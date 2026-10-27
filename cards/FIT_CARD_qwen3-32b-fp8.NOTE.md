# Qwen3-32B-FP8 — what this rung is and is not

## What it is
The official FP8 weight set of Qwen3-32B: same 64-layer dense architecture, same 32.76B
parameters, weight precision FP8 instead of BF16. Fitted and measured under the same
protocol as every other rung (n=1000 prompts, 128 tokens, bf16 forward, fp32 lens storage,
pos=-1 primary, Hit@5/Hit@10 from exact `j_rank`).

## Why this precision
The BF16 checkpoint is 65.5 GB and cannot perform the fit's backward pass on this cluster's
80 GB cards. Measured, not estimated:

| configuration | result |
|---|---|
| BF16 weights, dim_batch=2 | OOM, 142 MiB free of 79.18 GiB |
| BF16 + gradient checkpointing | OOM |
| BF16 + gradient checkpointing + dim_batch=1 | OOM |

The weights alone are the constraint, not activation memory. Qwen3-27B (55.6 GB) fits in
62,369 MiB on the same card, so the extra ~10 GB of weights is exactly what the backward
pass needed. Every ticket in this account exposes a single GPU, so sharding is unavailable.

## What it is NOT
- NOT a rung on the GGUF bit-width ladder. That ladder (Q2_K_M, Q3_K_M, Q4_K_M, Q5_K_M, Q6_K,
  Q8_0) varies bit width within one model and answers "at which width does the readout
  break". FP8 is a separately published weight set, not a rung on that ladder, and must never
  be placed on it or counted as one of its points.
- NOT pooled with the BF16 rows. It has its own tag (`qwen3-32b-fp8`), its own lens, its own
  reports, and the precision appears in its label in every table.
- NOT a clean substitute for a BF16 32B rung in a controlled architecture comparison. The
  comparison this rung was added to enable -- dense versus linear-attention attention at
  comparable scale -- therefore differs in TWO variables (architecture AND weight precision).
  Any write-up must state that, rather than reading the gap as purely architectural.

## Comparisons that need no caveat
- `qwen3.8-27b` vs `qwen3.6-27b`: 27B scale, BF16 precision, one generation apart. Clean.
- The dense family (Qwen3: 0.6B / 4B / 8B / 14B / 32B-fp8) versus the linear-attention
  family (Qwen3.5: 0.8B / 2B / 9B, plus 27B / 3.6-27B) remains a descriptive grouping; the
  FP8 rung narrows but does not close the scale confound.

## To fill the BF16 32B cell
Requires a multi-GPU allocation (tensor or pipeline sharding). The fit's backward pass spans
the unembed, so it has never been validated across devices in this project; a sharded run
would need a small-scale correctness check first.
