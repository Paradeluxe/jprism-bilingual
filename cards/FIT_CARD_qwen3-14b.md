# FIT_CARD — qwen3-14b n1000 Lstep2 wikitext (4-way sliced fit, merged)

**When:** 2026-10-04 22:03
**Where:** SICC (a100_batch, 4x A100 40GB, 2 jobs) + resume partial
**Status:** fit complete (sliced: merge of disjoint prompt ranges; n-weighted via JacobianLens.merge)
**Model key:** 14B
**HF id:** Qwen/Qwen3-14B
**n_layers:** 40
**d_model:** 5120
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38]
**target_layer:** final (39)
**max_seq_len:** 128
**skip_first:** 16
**N prompts used:** 1000 (expected 1000)
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `zh12b_h800_fit.log (sliced merge; per-slice logs also 0.00%)`
**seed:** 20260913
**corpus:** `fit_corpus/wikitext_n1000_L128.jsonl`
**lens:** `lenses/local/qwen3-14b/jlens_n1000_Lstep2_wikitext.pt`
**fragments:**
  - `fit_ckpt/qwen3-14b/fit_ckpt_n1000_slice0-250_Lstep2_zhwiki.zh.pt`
  - `fit_ckpt/qwen3-14b/fit_ckpt_n1000_slice250-500_Lstep2_zhwiki.zh.pt`
  - `fit_ckpt/qwen3-14b/fit_ckpt_n1000_slice500-1000_Lstep2_zhwiki.zh.pt`
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (sliced-fit merge variant; verified against single-run refs on 8B n3/n4)
