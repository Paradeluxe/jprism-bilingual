"""Local jlens fit N=1000, max_seq_len=128, source_layers every 2.

Loads fit_corpus/wikitext_n1000_L128.jsonl, fits Qwen3-0.6B by default,
saves under lenses/local/... + FIT_CARD. Resumable via fit_ckpt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import time
import traceback
from datetime import datetime, timezone

os.environ.setdefault("HF_HOME", r"E:\huggingface_cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_DATASETS_CACHE", r"E:\huggingface_cache\datasets")
os.environ.setdefault("TRANSFORMERS_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
# Online allowed for missing models; prefer local. Do NOT set OFFLINE=1 globally.

import torch
import transformers
import jlens

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_local_fit_n1000")

PROJECT = os.path.dirname(os.path.abspath(__file__))
CORPUS_PATH = os.path.join(PROJECT, "fit_corpus", "wikitext_n1000_L128.jsonl")
CORPUS_CARD = os.path.join(PROJECT, "fit_corpus", "CORPUS_CARD.md")

MODELS = {
    "0.6B": {
        "hf_name": "Qwen/Qwen3-0.6B",
        "local": r"E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B",
        "tag": "qwen3-0.6b",
        "device_map": None,  # full GPU
    },
    "1.7B": {
        "hf_name": "Qwen/Qwen3-1.7B",
        "local": r"E:\huggingface_cache\manual\Qwen3-1.7B",
        "tag": "qwen3-1.7b",
        "device_map": None,
    },
    "4B": {
        "hf_name": "Qwen/Qwen3-4B",
        "local": r"E:\huggingface_cache\hub\models--Qwen--Qwen3-4B",
        "tag": "qwen3-4b",
        "device_map": "auto",
    },
    # APPENDIX track (Qwen3.5 hybrid DeltaNet+Attention) — NOT main Qwen3 scale table
    "3.5-0.8B": {
        "hf_name": "Qwen/Qwen3.5-0.8B",
        "local": r"E:\huggingface_cache\hub\models--Qwen--Qwen3.5-0.8B",
        "tag": "qwen3.5-0.8b",
        "device_map": None,
        "loader": "image_text",  # Qwen3_5ForConditionalGeneration
        "appendix": True,
    },
    "3.5-2B": {
        "hf_name": "Qwen/Qwen3.5-2B",
        "local": r"E:\huggingface_cache\hub\models--Qwen--Qwen3.5-2B",
        "tag": "qwen3.5-2b",
        "device_map": None,
        "loader": "image_text",
        "appendix": True,
    },
}

MAX_SEQ_LEN = 128
SKIP_FIRST = 16  # jlens default
N_TARGET = 1000
DIM_BATCH = 8  # 0.6B VRAM headroom; prior n100 used 4
LAYER_STEP = 2
SEED = 20260913


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_corpus(path: str) -> list[str]:
    prompts: list[str] = []
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


def every_2_source_layers(n_layers: int) -> list[int]:
    """Every 2 layers strictly below final layer (target = n_layers-1)."""
    target = n_layers - 1
    return list(range(0, target, LAYER_STEP))


def resolve_model_path(cfg: dict) -> str:
    local = cfg["local"]
    if os.path.isdir(local) and os.path.isfile(os.path.join(local, "config.json")):
        return local
    # hub snapshot layout fallback
    snap_root = os.path.join(local, "snapshots")
    if os.path.isdir(snap_root):
        snaps = [
            os.path.join(snap_root, d)
            for d in os.listdir(snap_root)
            if os.path.isdir(os.path.join(snap_root, d))
        ]
        for s in snaps:
            if os.path.isfile(os.path.join(s, "config.json")):
                return s
    return cfg["hf_name"]


def write_fit_card(
    path: str,
    *,
    model_key: str,
    cfg: dict,
    model_path: str,
    n_layers: int,
    d_model: int,
    source_layers: list[int],
    lens_path: str,
    ckpt_path: str,
    corpus_hash: str,
    fit_sec: float,
    n_prompts: int,
    vram_peak_gb: float | None,
    dim_batch: int,
) -> None:
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    body = f"""# FIT_CARD — {cfg["tag"]} n{N_TARGET} Lstep{LAYER_STEP} wikitext

**When:** {now}
**Status:** fit complete
**Model key:** {model_key}
**HF id:** {cfg["hf_name"]}
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
**dtype:** float16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** {"APPENDIX / not main Qwen3 scale table" if cfg.get("appendix") else "main Qwen3 scale table (0.6/1.7/4B)"}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="0.6B",
        choices=list(MODELS.keys()),
        help="Which model to fit: 0.6B/1.7B/4B (main) or 3.5-0.8B/3.5-2B (appendix)",
    )
    parser.add_argument("--dim-batch", type=int, default=DIM_BATCH)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force local_files_only / HF offline env",
    )
    args = parser.parse_args()

    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

    cfg = MODELS[args.model]
    tag = cfg["tag"]
    lens_dir = os.path.join(PROJECT, "lenses", "local", tag)
    ckpt_dir = os.path.join(PROJECT, "fit_ckpt", tag)
    os.makedirs(lens_dir, exist_ok=True)
    os.makedirs(ckpt_dir, exist_ok=True)
    lens_path = os.path.join(
        lens_dir, f"jlens_n{N_TARGET}_Lstep{LAYER_STEP}_wikitext.pt"
    )
    ckpt_path = os.path.join(
        ckpt_dir, f"fit_ckpt_n{N_TARGET}_Lstep{LAYER_STEP}_wikitext.pt"
    )
    card_path = os.path.join(PROJECT, f"FIT_CARD_{tag}.md")

    if not os.path.isfile(CORPUS_PATH):
        raise FileNotFoundError(
            f"corpus missing: {CORPUS_PATH}; run build_fit_corpus.py first"
        )

    corpus_hash = sha256_file(CORPUS_PATH)
    prompts = load_corpus(CORPUS_PATH)
    logger.info("corpus %s sha256=%s n=%d", CORPUS_PATH, corpus_hash, len(prompts))

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model_path = resolve_model_path(cfg)
    local_only = os.path.isdir(model_path)
    logger.info(
        "model=%s path=%s local_only=%s dim_batch=%d",
        cfg["hf_name"],
        model_path,
        local_only,
        args.dim_batch,
    )

    dtype = torch.float16
    t0 = time.perf_counter()
    tok = transformers.AutoTokenizer.from_pretrained(
        model_path, local_files_only=local_only
    )
    load_kwargs = {
        "local_files_only": local_only,
        "dtype": dtype,
    }
    if cfg["device_map"] is not None:
        load_kwargs["device_map"] = cfg["device_map"]
    else:
        load_kwargs["device_map"] = None

    loader = cfg.get("loader", "causal")
    if loader == "image_text":
        # Qwen3.5 hub ships Qwen3_5ForConditionalGeneration (multimodal wrapper).
        AutoIT = getattr(transformers, "AutoModelForImageTextToText", None)
        if AutoIT is not None:
            hf = AutoIT.from_pretrained(model_path, **load_kwargs)
        else:
            hf = transformers.Qwen3_5ForConditionalGeneration.from_pretrained(
                model_path, **load_kwargs
            )
    else:
        try:
            hf = transformers.AutoModelForCausalLM.from_pretrained(
                model_path, **load_kwargs
            )
        except TypeError:
            # older transformers: dtype kw unsupported
            load_kwargs.pop("dtype", None)
            load_kwargs["torch_dtype"] = dtype
            hf = transformers.AutoModelForCausalLM.from_pretrained(
                model_path, **load_kwargs
            )

    if cfg["device_map"] is None and torch.cuda.is_available():
        hf = hf.cuda()

    logger.info("load_sec=%.1f", time.perf_counter() - t0)
    model = jlens.from_hf(hf, tok)
    n_layers, d_model = model.n_layers, model.d_model
    source_layers = every_2_source_layers(n_layers)
    logger.info(
        "n_layers=%d d_model=%d source_layers(%d)=%s",
        n_layers,
        d_model,
        len(source_layers),
        source_layers,
    )

    if os.path.isfile(lens_path):
        logger.info("lens already exists at %s — skip fit (delete to refit)", lens_path)
        return

    t1 = time.perf_counter()
    lens = jlens.fit(
        model,
        prompts=prompts,
        source_layers=source_layers,
        dim_batch=args.dim_batch,
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

    vram_peak = None
    if torch.cuda.is_available():
        vram_peak = torch.cuda.max_memory_allocated() / 1024**3
        logger.info("vram_peak_gb=%.2f", vram_peak)

    write_fit_card(
        card_path,
        model_key=args.model,
        cfg=cfg,
        model_path=model_path,
        n_layers=n_layers,
        d_model=d_model,
        source_layers=source_layers,
        lens_path=lens_path,
        ckpt_path=ckpt_path,
        corpus_hash=corpus_hash,
        fit_sec=fit_sec,
        n_prompts=lens.n_prompts,
        vram_peak_gb=vram_peak,
        dim_batch=args.dim_batch,
    )

    # Appendix models: also park FIT_CARD next to the lens
    if cfg.get("appendix"):
        lens_card = os.path.join(lens_dir, f"FIT_CARD_{tag}.md")
        write_fit_card(
            lens_card,
            model_key=args.model,
            cfg=cfg,
            model_path=model_path,
            n_layers=n_layers,
            d_model=d_model,
            source_layers=source_layers,
            lens_path=lens_path,
            ckpt_path=ckpt_path,
            corpus_hash=corpus_hash,
            fit_sec=fit_sec,
            n_prompts=lens.n_prompts,
            vram_peak_gb=vram_peak,
            dim_batch=args.dim_batch,
        )
        logger.info("wrote appendix lens FIT_CARD %s", lens_card)

    logger.info("wrote %s", card_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
