# GPU sizing — what fits where (measured, not estimated)

Every row below was run on this project. "OK" means the measurement completed and wrote a
report; "OOM" means CUDA ran out; "torch" means the card is unusable for another reason.

## The table

| weight on disk | size | card | outcome | note |
|---|---|---|---|---|
| 0.6B bf16 | 1.5 G | RTX 3050 8G | OK | local machine, gguf variants too |
| 0.8B bf16 | 1.7 G | RTX 3050 8G | OK | |
| 2B bf16 | 4–5 G | RTX 3050 8G | OK | |
| Gemma-4-E4B (4B) | 14.9 G | **A100 40G** | OK | loads 2076 tensors, measures in ~70 s/corpus |
| Gemma-4-E4B (4B) | 14.9 G | RTX 2080 Ti 11G | **OOM** | 9.08 GiB held, then "Tried to allocate 5.25 GiB" |
| Gemma-4-E4B (4B) | 14.9 G | Tesla V100 16G | **torch** | loads to 14.8 GiB then `torch 2.14+cu130 does not include kernels for this GPU` |
| Gemma-4-E4B (4B) | 14.9 G | RTX 4070 12G | untested | needs ~13 GiB, i.e. borderline; 14.9 G transfer was also unstable |
| Qwen3.5-9B | 19 G | A100 40G | OK | |
| Gemma-4-12B | 23 G | A100 40G | OK | peak 23.5 GiB during load |
| Qwen3-14B | 28 G | A100 40G | OK | |
| Qwen3.6-27B / 3.8-27B | 53 G | **80G (h800)** | — | 54 G bf16 does not fit on 40 G, do not try |
| Qwen3-32B-FP8 | 33 G | A100 40G | historical OOM | re-test once weights are back on disk |

## The rule of thumb

    required VRAM ≈ weight size × 1.5–1.7     (weights + activations, batch 1)

so a 40 GB card is safe up to ~24 G of weights (12B bf16). Beyond that, go to the h800.

## Two traps that are not about VRAM

1. **Volta is dead to this torch.** V100-16G has enough memory for a 4B model but the installed
   torch 2.14.0+cu130 ships no SM 7.0 kernels. `gpu_batch` on this cluster is RTX 2080 Ti 11G,
   `v100_batch` is Tesla V100-16G — neither can run anything above 2B, so do not queue there.

2. **Directory names must match the registry verbatim.** The downloader creates
   `~/models/<tag>` (e.g. `gemma4-e4b`, `qwen3.5-9b`), while `run_fit_sicc.py` points at
   `~/models/gemma-4-E4B`, `~/models/Qwen3.5-9B`. One missing hyphen or a case difference gives
   `weights missing` from the dry-run and `no file named model.safetensors` from the loader.
   Fix with a symlink, but **`ls -ld` first** — deleting what looks like a broken link when it is
   actually a real directory destroys the only copy.

## Quota arithmetic (150 G account)

- models + jspace together count. Keep a running `du -sh ~/models ~/jspace`.
- At 150 G the HF downloader fails with `OSError: [Errno 122] Disk quota exceeded` on
  `os.makedirs` — the message points at the directory, not the quota, so read the errno.
- The big-dense chain is therefore strictly one rung at a time: download → measure → delete the
  `*.safetensors` blobs (keep config/tokenizer) → next rung.

## Transfer speed beats download speed

    cluster → HuggingFace (anonymous)     4.5 MB/s   (xet high-performance: 4 MB/s, hf-mirror: 2 MB/s)
    this machine → cluster (SFTP)         50 MB/s
    cluster → this machine (SFTP)         92 MB/s    (14.9 G in ~2.5 min)

So moving a model between machines is cheap; fetching it from HF is not. If a rung is needed on
both sides, download once and push.

## Card inventory on SICC

    a100_batch   A100-SXM4-40GB   3 nodes   the workhorse
    h800_batch   H800 80GB        3 nodes   only place 27B bf16 fits
    gpu_batch    RTX 2080 Ti 11G  4 nodes   <= 2B only
    v100_batch   Tesla V100-16G   3 nodes   unusable (torch has no Volta kernels)
