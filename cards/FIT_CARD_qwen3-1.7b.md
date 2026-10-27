# FIT_CARD — qwen3-1.7b (dense, NOT quantized) n1000 Lstep2 wikitext

> **NP-NOT-IN-MAIN-TABLE.** This rung is excluded from the paper's main table by the
> protocol locked on 2026-09-15 (`LOCKED_DECISIONS / SOP_LOCAL_FIT`, "NP not in main table").
> It is retained as an early local run, not as a citable cell. Do not cite it.

**When:** 2026-09-15 10:47
**Status:** fit complete — with a known defect, see "Known defect" below
**Where:** LOCAL (this machine, not SICC)
**Model key:** 1.7B
**HF id:** Qwen/Qwen3-1.7B
**Loaded from:** `E:\huggingface_cache\manual\Qwen3-1.7B`
**n_layers:** 28
**d_model:** 2048
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
**target_layer:** final (27)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 4
**N prompts used:** 1000
**dtype:** float16
**fit_sec:** 90066.5
**fit_hours:** 25.02
**vram_peak_gb:** 4.570281505584717
**lens:** `lenses/local/qwen3-1.7b/jlens_n1000_Lstep2_wikitext.pt`
**checkpoint:** `fit_ckpt/qwen3-1.7b/fit_ckpt_n1000_Lstep2_wikitext.pt`
**corpus:** `fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d9064e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**seed:** 20260913
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)

## Why this card exists

A 2026-10-18 audit of the local mirror found `lenses/local/qwen3-1.7b/…wikitext.pt` with no
report and no cluster counterpart, which reads as a stray artifact. It is not: this is a
legitimate 2026-09-15 local fit of the **dense** 1.7B, made before the program moved that size
onto the cluster. The cluster registry has no `Q17` dense entry — only the quantized rungs
(`q2k`, `q3km`, `q4km`, `bnb4`) — so there is no cluster copy to reconcile against.

Its absence from `SCALE_SUMMARY.md` is by protocol, not by oversight: both copies of that table
list only `qwen3-1.7b-bnb4 / -q2k / -q3km / -q4km`. No measurement report anywhere references
this lens.

## Known defect (measured 2026-10-18, torch.isfinite over every layer)

| layer | non-finite entries | share of 2048x2048 |
|---|---|---|
| 0  | 6144 | 0.1465% |
| 2  | 6144 | 0.1465% |
| 4 and above (12 layers) | 0 | 0% |

The non-finite entries are **whole rows**, not scattered values: 3 rows spanning indices
1683–1999, each row fully NaN across all 2048 columns. That shape means a few prompts overflowed
to NaN in the shallowest layers and were accumulated into the Jacobian; layers 4+ are clean, so
the overflow is confined to the early activation path. `float16` (the narrowest dynamic range)
is the plausible cause.

## Why it was not re-fitted

The NaN remediation built on 2026-10-08 (`nanfit_keeper.sh`) targeted `qwen3.5-2b` only. This
lens predates that machinery, lives on the local machine rather than on the cluster, and is
excluded from the main table — so re-fitting would cost 25 GPU-hours to repair a cell that is
never reported.

## How to treat it

- Citing it: not permitted. It is NP.
- Deleting it: not required. It is the only record of that early local run.
- If the dense 1.7B cell is ever needed for the paper, it must be re-fitted under the current
  cluster protocol with bf16 or fp32 and a recorded skip_rate, not resurrected from this file.
