"""SICC jlens fit — Qwen3-8B / Qwen3.5-9B / Qwen3-14B / Qwen3.8-27B, N=1000, L=128, every-2 layers.

Adapted from run_local_fit_n1000.py for the SICC cluster (A100-40GB; fp16 default,
bf16 where configured). Model weights: ~/models/<name> (hf CLI --local-dir layout);
corpus ships alongside under fit_corpus/. Resumable via fit_ckpt (checkpoint per prompt).

NaN gate: after fitting, the lens is scanned for NaN/Inf; a corrupt fit saves the
artifact (for debugging) and exits 3 so the chain marks it failed instead of
quietly burning hours on garbage.

Usage:
    python3 run_fit_sicc.py --model 27B [--dim-batch 4] [--limit N]   # --limit => .smoke artifacts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import socket
import sys
import contextlib
import time
import traceback
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
os.environ.setdefault("HF_HOME", os.path.join(HOME, ".cache", "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

import torch
import transformers
import jlens

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_fit_sicc")

PROJECT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.join(PROJECT, "fit_corpus", "wikitext_n1000_L128.jsonl")
CORPUS_PATH = DEFAULT_CORPUS   # overridable: --corpus
CORPUS_TAG = "wikitext"        # overridable: --corpus-tag (命名标识：镜片/存档/卡片)

# A prompt whose per-prompt Jacobian contains non-finite entries is skipped by jlens (its
# own regression test documents that summing such a prompt "permanently poison[s] the whole
# lens"). A small fraction is that guard doing its job. A large fraction means the kept
# prompts are a biased subset and the lens stops being comparable with the rest of the
# table — so we refuse to write it. Observed 2026-09-28: 4B-AWQ 0.3% (fine),
# 8B-AWQ 24% (would have shipped corrupt).
SKIP_RATE_MAX = 0.02

MODELS = {
    "8B": {
        "hf_name": "Qwen/Qwen3-8B",
        "local": os.path.join(HOME, "models", "Qwen3-8B"),
        "tag": "qwen3-8b",
        "device_map": None,
        "dim_batch": 4,
        "dtype": "bf16",
    },
    "9B": {
        "hf_name": "Qwen/Qwen3.5-9B",
        "local": os.path.join(HOME, "models", "Qwen3.5-9B"),
        "tag": "qwen3.5-9b",
        "device_map": None,
        "dim_batch": 4,
        "loader": "image_text",
        "appendix": True,
        "dtype": "bf16",
    },
    "14B": {
        "hf_name": "Qwen/Qwen3-14B",
        "local": os.path.join(HOME, "models", "Qwen3-14B"),
        "tag": "qwen3-14b",
        "device_map": None,
        "dim_batch": 2,
        "dtype": "bf16",
    },
    "27B": {
        "hf_name": "Qwen/Qwen3.8-27B",
        "local": os.path.join(HOME, "models", "Qwen3.8-27B"),
        "tag": "qwen3.8-27b",
        "device_map": "auto",
        "dim_batch": 4,
        "dtype": "bf16",
    },
    # --- new rungs (2026-10-10): second generation at 27B, and pure-dense controls ---
    # Qwen3.6-27B shares the 27B scale and the hybrid linear:full=3:1 family with
    # qwen3.8-27b, one generation apart, so it isolates generation from scale and
    # architecture. It is NOT dense; it belongs in the linear-hybrid group.
    "X36-27": {
        "hf_name": "Qwen/Qwen3.6-27B",
        "local": os.path.join(HOME, "models", "Qwen3.6-27B"),
        "tag": "qwen3.6-27b",
        "device_map": "auto",
        "dim_batch": 4,
        "dtype": "bf16",
    },
    # The only large PURE dense official rung. Comparing it with the linear 27B at the
    # same scale is what turns "wider EN-ZH gap under hybrid attention" from a
    # correlation into a causal claim.
    "Q3-32B": {
        "hf_name": "Qwen/Qwen3-32B",
        "local": os.path.join(HOME, "models", "Qwen3-32B"),
        "tag": "qwen3-32b",
        "device_map": "auto",
        "dim_batch": 2,
        "dtype": "bf16",
    },
    # Fills the dense ladder between 0.6B and 8B.
    # Official FP8 checkpoint of Qwen3-32B. Same 64-layer dense architecture and the same
    # 32.76B parameters as the bf16 rung; only the weight precision differs, and quantization
    # is already an axis of this program. The bf16 checkpoint cannot do a backward pass on an
    # 80 GB card (measured OOM with 142 MiB free; gradient checkpointing does not help),
    # so this rung is how the dense 32B cell gets filled.
    # trust_remote_code is required: the fp8 forward kernel comes from
    # kernels-community and the measurement path must pass the allow_all_hub_kernels global.
    "Q32B-FP8": {
        "hf_name": "Qwen/Qwen3-32B-FP8",
        "local": os.path.join(HOME, "models", "Qwen3-32B-FP8"),
        "tag": "qwen3-32b-fp8",
        "device_map": "auto",
        "dim_batch": 2,
        "dtype": "bf16",
        "trust_remote_code": True,
    },
    "Q3-4B": {
        "hf_name": "Qwen/Qwen3-4B",
        "local": os.path.join(HOME, "models", "Qwen3-4B"),
        "tag": "qwen3-4b",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
    },
    # --- Gemma 4 dense (foreign mirror arm, 2026-09-26) ---
    "G4E2B": {
        "hf_name": "google/gemma-4-E2B",
        "local": os.path.join(HOME, "models", "gemma-4-E2B"),
        "tag": "gemma4-e2b",
        "device_map": None,
        "dim_batch": 8,
        "loader": "image_text",
        "dtype": "bf16",
    },
    "G4E4B": {
        "hf_name": "google/gemma-4-E4B",
        "local": os.path.join(HOME, "models", "gemma-4-E4B"),
        "tag": "gemma4-e4b",
        "device_map": None,
        "dim_batch": 8,
        "loader": "image_text",
        "dtype": "bf16",
    },
    "G4-12B": {
        "hf_name": "google/gemma-4-12B",
        "local": os.path.join(HOME, "models", "gemma-4-12B"),
        "tag": "gemma4-12b",
        "device_map": None,
        "dim_batch": 4,
        "loader": "image_text",
        "dtype": "bf16",
    },
    # Dense Qwen3.5 baselines. These two lenses were fitted on 2026-10-03 and have been sitting
    # unmeasured ever since, because measure_sicc.py builds its tag→config map out of THIS
    # registry and skipped them as "tag not in registry" — a missing entry, not a missing lens.
    # They are the dense points the GGUF quant arms (q4km/q4ks/q5km/q6k/q8_0) are compared
    # against, so a quant ladder without them has no baseline in its own family.
    # Weights are NOT on disk yet; Q4KS/X2* fit the lens from the GGUF + the same-family
    # tokenizer mirror, but the measurement path needs the real dense checkpoint.
    "X08": {
        "hf_name": "Qwen/Qwen3.5-0.8B",
        "local": os.path.join(HOME, "models", "Qwen3.5-0.8B"),
        "tag": "qwen3.5-0.8b",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
    },
    "X2": {
        "hf_name": "Qwen/Qwen3.5-2B",
        "local": os.path.join(HOME, "models", "Qwen3.5-2B"),
        "tag": "qwen3.5-2b",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
    },
    "G4-31B": {
        "hf_name": "google/gemma-4-31B",
        "local": os.path.join(HOME, "models", "gemma-4-31B"),
        "tag": "gemma4-31b",
        "device_map": "auto",
        "dim_batch": 2,
        "loader": "image_text",
        "dtype": "bf16",
    },
    # --- Quant arm battery #1/#2 (2026-09-27; H800 13085; smoke->full chained) ---
# NOTE (09-27 21:15): the smoke leg MUST NOT gate the full leg with '&&'. A stale smoke
# checkpoint makes the smoke leg exit 1, and '&&' then skips the full fit entirely.
    "Q06": {
        "hf_name": "Qwen/Qwen3-0.6B",
        "local": os.path.join(HOME, "models", "Qwen3-0.6B"),
        "tag": "qwen3-0.6b",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
    },
    "Q06-Q4": {
        "hf_name": "unsloth/Qwen3-0.6B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q4km"),
        "tag": "qwen3-0.6b-q4km",
        "gguf_file": "Qwen3-0.6B-Q4_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q06-Q2": {
        "hf_name": "unsloth/Qwen3-0.6B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q2k"),
        "tag": "qwen3-0.6b-q2k",
        "gguf_file": "Qwen3-0.6B-Q2_K.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q06-Q3": {
        "hf_name": "unsloth/Qwen3-0.6B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q3km"),
        "tag": "qwen3-0.6b-q3km",
        "gguf_file": "Qwen3-0.6B-Q3_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q3": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q3km"),
        "tag": "qwen3.5-0.8b-q3km",
        "gguf_file": "Qwen3.5-0.8B-Q3_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X2-Q3": {
        "hf_name": "unsloth/Qwen3.5-2B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-2b-q3km"),
        "tag": "qwen3.5-2b-q3km",
        "gguf_file": "Qwen3.5-2B-Q3_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q06-Q5": {
        "hf_name": "unsloth/Qwen3-0.6B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q5km"),
        "tag": "qwen3-0.6b-q5km",
        "gguf_file": "Qwen3-0.6B-Q5_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q06-Q6": {
        "hf_name": "unsloth/Qwen3-0.6B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q6k"),
        "tag": "qwen3-0.6b-q6k",
        "gguf_file": "Qwen3-0.6B-Q6_K.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q06-Q8": {
        "hf_name": "unsloth/Qwen3-0.6B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-0.6b-q8_0"),
        "tag": "qwen3-0.6b-q8_0",
        "gguf_file": "Qwen3-0.6B-Q8_0.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q5": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q5km"),
        "tag": "qwen3.5-0.8b-q5km",
        "gguf_file": "Qwen3.5-0.8B-Q5_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q6": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q6k"),
        "tag": "qwen3.5-0.8b-q6k",
        "gguf_file": "Qwen3.5-0.8B-Q6_K.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q8": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q8_0"),
        "tag": "qwen3.5-0.8b-q8_0",
        "gguf_file": "Qwen3.5-0.8B-Q8_0.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q06-FP8": {
        "hf_name": "Qwen/Qwen3-0.6B-FP8",
        "local": os.path.join(HOME, "models", "qwen3-0.6b-fp8"),
        "tag": "qwen3-0.6b-fp8",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
        "trust_remote_code": True,
    },
    "Q17-Q4": {
        "hf_name": "unsloth/Qwen3-1.7B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-1.7b-q4km"),
        "tag": "qwen3-1.7b-q4km",
        "gguf_file": "Qwen3-1.7B-Q4_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q17-Q2": {
        "hf_name": "unsloth/Qwen3-1.7B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-1.7b-q2k"),
        "tag": "qwen3-1.7b-q2k",
        "gguf_file": "Qwen3-1.7B-Q2_K.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "Q17-Q3": {
        "hf_name": "unsloth/Qwen3-1.7B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3-1.7b-q3km"),
        "tag": "qwen3-1.7b-q3km",
        "gguf_file": "Qwen3-1.7B-Q3_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q4KS": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q4ks"),
        "tag": "qwen3.5-0.8b-q4ks",
        "gguf_file": "Qwen3.5-0.8B-Q4_K_S.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q4": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q4km"),
        "tag": "qwen3.5-0.8b-q4km",
        "gguf_file": "Qwen3.5-0.8B-Q4_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X08-Q2": {
        "hf_name": "unsloth/Qwen3.5-0.8B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-0.8b-q2k"),
        "tag": "qwen3.5-0.8b-q2k",
        "gguf_file": "Qwen3.5-0.8B-UD-Q2_K_XL.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X2-Q4KS": {
        "hf_name": "unsloth/Qwen3.5-2B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-2b-q4ks"),
        "tag": "qwen3.5-2b-q4ks",
        "gguf_file": "Qwen3.5-2B-Q4_K_S.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X2-Q4": {
        "hf_name": "unsloth/Qwen3.5-2B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-2b-q4km"),
        "tag": "qwen3.5-2b-q4km",
        "gguf_file": "Qwen3.5-2B-Q4_K_M.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X2-Q2": {
        "hf_name": "unsloth/Qwen3.5-2B-GGUF",
        "local": os.path.join(HOME, "models", "gguf", "qwen3.5-2b-q2k"),
        "tag": "qwen3.5-2b-q2k",
        "gguf_file": "Qwen3.5-2B-UD-Q2_K_XL.gguf",
        "device_map": None,
        "dim_batch": 8,
        "loader": "gguf",
        "dtype": "bf16",
    },
    "X2-AWQ": {
        "hf_name": "QuantTrio/Qwen3.5-2B-AWQ",
        # Measured 2026-10-03: cyankiwi/Qwen3.5-2B-AWQ-4bit is packed as
        # compressed-tensors/pack-quantized, where quantized_forward reads self.weight while the
        # data lives in weight_packed — swap_to_gemm reports "0 replaced" and no AWQ kernel path
        # can rescue it. QuantTrio ships plain quant_method=awq 4-bit g128, the same layout as the
        # Q4-AWQ rung that fitted cleanly (252 replaced). atalsharma/cyankiwi both compressed-tensors.
        "local": os.path.join(HOME, "models", "qwen3.5-2b-awq"),
        "tag": "qwen3.5-2b-awq",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
        # Pre-quantized AWQ needs the autograd-capable GEMM kernel. Measured 2026-10-03: with
        # fix=None this rung produced non-finite Jacobians concentrated in layer 0 (4 of the
        # first 6 prompts) — the AWQ inference kernels declare SUPPORTS_TRAINING=False, so the
        # backward silently produces wrong numbers. Q4-AWQ escaped this only because it is a
        # self-trained compressed-tensors checkpoint whose lm_head is dense.
        "quantized_fit_fix": "gemm",
    },
    "Q17-BNB": {
        "hf_name": "unsloth/Qwen3-1.7B-unsloth-bnb-4bit",
        "local": os.path.join(HOME, "models", "qwen3-1.7b-bnb4"),
        "tag": "qwen3-1.7b-bnb4",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
    },
    "X08-FP8": {
        "hf_name": "surogate/Qwen3.5-0.8B-FP8",
        "local": os.path.join(HOME, "models", "qwen3.5-0.8b-fp8"),
        "tag": "qwen3.5-0.8b-fp8",
        "device_map": None,
        "dim_batch": 8,
        "dtype": "bf16",
        "trust_remote_code": True,
    },
    "Q4-AWQ": {
        "hf_name": "Qwen/Qwen3-4B-AWQ",
        "local": os.path.join(HOME, "models", "qwen3-4b-awq"),
        "tag": "qwen3-4b-awq",
        "device_map": None,
        "dim_batch": 4,
        "dtype": "bf16",
    },
    "Q8B-AWQ": {
        "hf_name": "Qwen/Qwen3-8B-AWQ",
        "local": os.path.join(HOME, "models", "qwen3-8b-awq"),
        "tag": "qwen3-8b-awq",
        "device_map": None,
        "dim_batch": 2,
        "dtype": "bf16",
        # Same reason as X2-AWQ: pre-quantized AWQ needs the autograd-capable kernel.
        # Measured 2026-10-05 00:06 on 13884 (h800-02): BOTH kernel choices fail here —
        # gemm and force_torch_aten both land on TorchAtenAwqLinear, and gptqmodel's AWQ JIT
        # extension fails to build on this node ("failed to build torch.ops JIT extension:
        # Error building extension 'gptqmodel_awq_ops'", 3 ValueErrors per layer), so the
        # autograd gate reports backward_ok=False/grad_abs_sum=nan and exits 5. This is a
        # toolchain blocker, not a knob: the rung is unrunnable until the extension builds.
        "quantized_fit_fix": "gemm",
    },
    # 8B 4-bit replacement. gptqmodel's AWQ GPU kernels (Marlin/Machete/ExllamaV2) all set
    # SUPPORTS_TRAINING = False, so a jacobian fit backprops through a non-differentiable op
    # and 24-28% of prompts come out non-finite. The 4-bit-weight GPTQ/AutoRound family has the
    # opposite profile (autograd-capable CUDA GEMM kernel, conservative 16-bit activations).
    "Q8B-GPTQ": {
        "hf_name": "RedHatAI/Qwen3-8B-quantized.w4a16",
        "local": os.path.join(HOME, "models", "qwen3-8b-gptq"),
        "tag": "qwen3-8b-gptq",
        "device_map": None,
        "dim_batch": 2,
        "dtype": "bf16",
        "quantized_fit_fix": "gemm",
    },
    # Native GPTQ-Int4 (goes through gptqmodel, which has autograd-capable CUDA GEMM kernels
    # and leaves lm_head dense). The compressed-tensors "pack-quantized" checkpoints fail with
    # "AttributeError: 'Linear' object has no attribute 'weight'" because their
    # quantized_forward reads self.weight while the data lives in weight_packed.
    "Q8B-GPTQ4": {
        "hf_name": "JunHowie/Qwen3-8B-GPTQ-Int4",
        "local": os.path.join(HOME, "models", "qwen3-8b-gptq4"),
        "tag": "qwen3-8b-gptq4",
        "device_map": None,
        "dim_batch": 2,
        "dtype": "bf16",
        "quantized_fit_fix": "gemm",
        "gptq_no_optimum": True,
    },
}

MAX_SEQ_LEN = 128
SKIP_FIRST = 16
N_TARGET = 1000
LAYER_STEP = 2
SEED = 20260913


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_corpus(path: str) -> list:
    prompts = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            prompts.append(obj["text"])
    if len(prompts) != N_TARGET:
        logger.warning("corpus has %d prompts, expected %d", len(prompts), N_TARGET)
    return prompts


def every_2_source_layers(n_layers: int) -> list:
    target = n_layers - 1
    return list(range(0, target, LAYER_STEP))


def resolve_model_path(cfg: dict) -> str:
    local = cfg["local"]
    if os.path.isdir(local):
        if os.path.isfile(os.path.join(local, "config.json")):
            return local
        if any(f.endswith(".gguf") for f in os.listdir(local)):
            return local
    return cfg["hf_name"]


def write_fit_card(path, *, model_key, cfg, model_path, n_layers, d_model,
                   source_layers, lens_path, ckpt_path, corpus_hash, fit_sec,
                   n_prompts, vram_peak_gb, dim_batch, host, dtype_name):
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    track = "APPENDIX / not main Qwen3 scale table" if cfg.get("appendix") else "main Qwen3 scale table (0.6/1.7/4B)"
    body = f"""# FIT_CARD — {cfg['tag']} n{n_prompts} Lstep{LAYER_STEP} {CORPUS_TAG}

**When:** {now}
**Where:** {host} (SICC)
**Status:** fit complete
**Model key:** {model_key}
**HF id:** {cfg['hf_name']}
**Loaded from:** `{model_path}`
**n_layers:** {n_layers}
**d_model:** {d_model}
**source_layers (every {LAYER_STEP}):** {source_layers}
**target_layer:** final ({n_layers - 1})
**max_seq_len:** {MAX_SEQ_LEN}
**skip_first:** {SKIP_FIRST}
**dim_batch:** {dim_batch}
**N prompts used:** {n_prompts}
**seed:** {SEED}
**corpus:** `{CORPUS_PATH}`
**corpus_sha256:** `{corpus_hash}`
**lens:** `{lens_path}`
**checkpoint:** `{ckpt_path}`
**fit_sec:** {fit_sec:.1f}
**fit_hours:** {fit_sec / 3600:.2f}
**vram_peak_gb:** {vram_peak_gb if vram_peak_gb is not None else "n/a"}
**dtype:** {dtype_name}
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** {track}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="8B", choices=list(MODELS.keys()))
    parser.add_argument("--dim-batch", type=int, default=None)
    parser.add_argument("--limit", type=int, default=0,
                        help="use only first N prompts and write *.smoke artifacts")
    parser.add_argument("--corpus", default=None,
                        help="corpus jsonl path (default: fit_corpus/wikitext_n1000_L128.jsonl)")
    parser.add_argument("--corpus-tag", default="wikitext",
                        help="corpus tag used in lens/ckpt filenames + card title")
    parser.add_argument("--source-layers", default=None,
                        help="comma-separated override of the fitted source "
                             "layers (default: every 2 from layer 0). Used "
                             "to re-fit only the layers damaged by the old "
                             "fp16 lens store (Qwen3.5 shallow layers).")
    args = parser.parse_args()

    global CORPUS_PATH, CORPUS_TAG
    if args.corpus:
        CORPUS_PATH = args.corpus
    if args.corpus_tag:
        CORPUS_TAG = args.corpus_tag

    cfg = MODELS[args.model]
    tag = cfg["tag"]
    suffix = ".smoke" if args.limit else ""
    dim_batch = args.dim_batch if args.dim_batch else cfg["dim_batch"]
    dtype_name = cfg.get("dtype", "fp16")
    dtype = torch.bfloat16 if dtype_name == "bf16" else torch.float16

    lens_dir = os.path.join(PROJECT, "lenses", "local", tag)
    ckpt_dir = os.path.join(PROJECT, "fit_ckpt", tag)
    os.makedirs(lens_dir, exist_ok=True)
    os.makedirs(ckpt_dir, exist_ok=True)

    if not os.path.isfile(CORPUS_PATH):
        raise FileNotFoundError("corpus missing: %s" % CORPUS_PATH)

    corpus_hash = sha256_file(CORPUS_PATH)
    prompts = load_corpus(CORPUS_PATH)
    if args.limit:
        prompts = prompts[: args.limit]
    n_use = len(prompts)
    logger.info("corpus %s sha256=%s n_use=%d dim_batch=%d dtype=%s",
                CORPUS_PATH, corpus_hash, n_use, dim_batch, dtype_name)

    lens_path = os.path.join(lens_dir, "jlens_n%d_Lstep%d_%s%s.pt" % (n_use, LAYER_STEP, CORPUS_TAG, suffix))
    ckpt_path = os.path.join(ckpt_dir, "fit_ckpt_n%d_Lstep%d_%s%s.pt" % (n_use, LAYER_STEP, CORPUS_TAG, suffix))
    card_path = os.path.join(PROJECT, "FIT_CARD_%s%s.md" % (tag, suffix))

    if os.path.isfile(lens_path):
        logger.info("lens already exists at %s — skip fit (delete to refit)", lens_path)
        return

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model_path = resolve_model_path(cfg)
    local_only = os.path.isdir(model_path)
    logger.info("model=%s path=%s local_only=%s", cfg["hf_name"], model_path, local_only)

    t0 = time.perf_counter()
    tok_kwargs = {"local_files_only": local_only}
    if cfg.get("loader") == "gguf":
        tok_kwargs["gguf_file"] = cfg["gguf_file"]
    tok = transformers.AutoTokenizer.from_pretrained(model_path, **tok_kwargs)
    load_kwargs = {"local_files_only": local_only, "dtype": dtype}
    load_kwargs["device_map"] = cfg["device_map"]

    loader = cfg.get("loader", "causal")
    if cfg.get("trust_remote_code"):
        # FP8 checkpoints load their GPU kernels from kernels-community/finegrained-fp8.
        # transformers gates that behind a hub-kernel trust check, and the gate is NOT
        # `trust_remote_code` (that one is for modeling code): without allow_all_kernels=True
        # EVERY prompt is skipped with "skipping prompt N: ... could not verify publisher
        # trust status" and the fit dies as "no prompts were long enough to fit on"
        # (exactly how Q06-FP8 / X08-FP8 failed on 2026-09-27).
        load_kwargs["allow_all_kernels"] = True
        load_kwargs["trust_remote_code"] = True
        logger.info("FP8 path: allow_all_kernels=True (hub-kernel trust gate opened)")
    if cfg.get("quantized_fit_fix"):
        # Compressed-tensor / AWQ / GPTQ checkpoints expose lm_head as a quant linear with no
        # `.weight`, which jlens' unembed reads directly (jlens/hf.py) ->
        # "AttributeError: 'Linear' object has no attribute 'weight'". fix_awq_backend also
        # forces an autograd-capable kernel where one exists (the AWQ GPU kernels all declare
        # SUPPORTS_TRAINING=False, which silently corrupts a fit's gradients).
        sys.path.insert(0, PROJECT)
        import fix_awq_backend
        fix_awq_backend.force_gemm_autograd()
        if cfg.get("force_torch_aten"):
            fix_awq_backend.force_torch_aten()
        # A native GPTQ checkpoint makes transformers reach for `optimum`, which imports
        # `datasets` -> `pandas`, and pandas cannot coexist with the numpy pin gptqmodel
        # requires ("numpy.dtype size changed" / "requires numpy==2.2.6"). We never use
        # optimum's own loading path — gptqmodel is the backend that actually runs — so stub the
        # optional import rather than fight the dependency.
        if cfg.get("gptq_no_optimum"):
            fix_awq_backend.stub_optional_imports("pandas")
            fix_awq_backend.install_metadata_stubs()
        logger.info("quantized_fit_fix: %s", cfg.get("quantized_fit_fix"))
    if loader == "image_text":
        AutoIT = getattr(transformers, "AutoModelForImageTextToText", None)
        if AutoIT is not None:
            hf = AutoIT.from_pretrained(model_path, **load_kwargs)
        else:
            hf = transformers.Qwen3_5ForConditionalGeneration.from_pretrained(model_path, **load_kwargs)
    elif loader == "gguf":
        hf = transformers.AutoModelForCausalLM.from_pretrained(
            model_path, gguf_file=cfg["gguf_file"], **load_kwargs)
    else:
        try:
            hf = transformers.AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)
        except TypeError:
            load_kwargs.pop("dtype", None)
            load_kwargs["torch_dtype"] = dtype
            hf = transformers.AutoModelForCausalLM.from_pretrained(model_path, **load_kwargs)

    if cfg["device_map"] is None and torch.cuda.is_available():
        hf = hf.cuda()
    if cfg.get("quantized_fit_fix"):
        # After the move: restore lm_head as a plain Linear (jlens reads lm_head.weight) and
        # verify the residual stream can actually be backpropagated before we spend hours on it.
        fix_awq_backend.swap_to_gemm(hf)
        hf.eval()
        probe = fix_awq_backend.assert_grad_works(hf, tok)
        logger.info("quantized_fit_fix applied: kernels=%s autograd=%s",
                    fix_awq_backend.assert_no_marlin(hf), probe)
        if not probe.get("backward_ok"):
            logger.error("quantized_fit_fix: autograd check FAILED (%s) — the kernel cannot be "
                         "backpropagated, so a fit would silently produce wrong gradients; "
                         "exiting 5", probe)
            sys.exit(5)

    logger.info("load_sec=%.1f", time.perf_counter() - t0)
    model = jlens.from_hf(hf, tok)
    n_layers, d_model = model.n_layers, model.d_model
    if args.source_layers:
        source_layers = [int(x) for x in args.source_layers.split(",") if x.strip() != ""]
        logger.warning("SOURCE_LAYERS_OVERRIDE: fitting only %s (of %d default); "
                       "this lens is PARTIAL and covers fewer layers than the "
                       "ladder protocol.", source_layers)
    else:
        source_layers = every_2_source_layers(n_layers)
    logger.info("n_layers=%d d_model=%d source_layers(%d)=%s",
                n_layers, d_model, len(source_layers), source_layers)

    t1 = time.perf_counter()
    # FP8 hub kernels are fetched LAZILY on the first forward pass (inside jlens.fit), not during
    # from_pretrained: the allow_all_kernels load kwarg only opens the gate around model init and
    # ALLOW_ALL_KERNELS is reset to False right after. Without this context every prompt is skipped
    # with "could not verify publisher trust status" and the run dies as "no prompts were long
    # enough to fit on" (observed on Qwen3-32B-FP8 smoke, 2026-10-12, and earlier on Q06/X08-FP8).
    if cfg.get("trust_remote_code"):
        from transformers.integrations.hub_kernels import allow_all_hub_kernels
        fit_ctx = allow_all_hub_kernels()
    else:
        fit_ctx = contextlib.nullcontext()
    with fit_ctx:
        lens = jlens.fit(
            model,
            prompts=prompts,
            source_layers=source_layers,
            dim_batch=dim_batch,
            max_seq_len=MAX_SEQ_LEN,
            skip_first=SKIP_FIRST,
            checkpoint_path=ckpt_path,
            checkpoint_every=1,
            resume=True,
        )
    fit_sec = time.perf_counter() - t1
    lens.save(lens_path)
    logger.info("saved_lens=%s fit_sec=%.1f fit_hours=%.2f", lens_path, fit_sec, fit_sec / 3600)
    logger.info("lens=%s", lens)

    bad = [l for l in lens.source_layers
           if torch.isnan(lens.jacobians[l]).any() or torch.isinf(lens.jacobians[l]).any()]
    if bad:
        logger.error("NAN_IN_LENS layers=%s (of %d) — fit is corrupt; exiting 3",
                     bad[:8], len(lens.source_layers))
        sys.exit(3)

    # --- skip-rate gate (added 2026-09-28) ---------------------------------------
    # jlens skips a prompt whose per-prompt Jacobian has non-finite entries. A few skips
    # is a designed-in guard (see jlens tests/test_fitting.py::test_fit_skips_nonfinite
    # _jacobian); a LARGE fraction means the remaining prompts are a biased subset and the
    # lens is not comparable with the rest of the table. Q8B-AWQ in bf16 skipped 243/1000
    # (24%, all at layer 0) — that lens would have shipped as silently-corrupt data.
    # Reference practice: schani/j-space fits in float32 for exactly this reason.
    skip_rate = 1.0 - (lens.n_prompts / n_use) if n_use else 0.0
    if skip_rate > SKIP_RATE_MAX:
        logger.error(
            "SKIP_RATE_GATE: %d/%d prompts skipped (%.1f%%) > %.1f%% — the surviving "
            "prompts are a biased subset, so this lens is NOT comparable with the table. "
            "Refusing to write it. Fix the numerics (fit in float32) or lower n_use.",
            n_use - lens.n_prompts, n_use, 100 * skip_rate, 100 * SKIP_RATE_MAX)
        sys.exit(4)
    logger.info("skip_rate=%.2f%% (%d/%d prompts kept)", 100 * skip_rate,
                lens.n_prompts, n_use)

    vram_peak = None
    if torch.cuda.is_available():
        vram_peak = torch.cuda.max_memory_allocated() / 1024**3
        logger.info("vram_peak_gb=%.2f", vram_peak)

    host = socket.gethostname()
    write_fit_card(card_path, model_key=args.model, cfg=cfg, model_path=model_path,
                   n_layers=n_layers, d_model=d_model, source_layers=source_layers,
                   lens_path=lens_path, ckpt_path=ckpt_path, corpus_hash=corpus_hash,
                   fit_sec=fit_sec, n_prompts=lens.n_prompts, vram_peak_gb=vram_peak,
                   dim_batch=dim_batch, host=host, dtype_name=dtype_name)
    if cfg.get("appendix"):
        write_fit_card(os.path.join(lens_dir, "FIT_CARD_%s%s.md" % (tag, suffix)),
                       model_key=args.model, cfg=cfg, model_path=model_path,
                       n_layers=n_layers, d_model=d_model, source_layers=source_layers,
                       lens_path=lens_path, ckpt_path=ckpt_path, corpus_hash=corpus_hash,
                       fit_sec=fit_sec, n_prompts=lens.n_prompts, vram_peak_gb=vram_peak,
                       dim_batch=dim_batch, host=host, dtype_name=dtype_name)
    logger.info("wrote %s", card_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
