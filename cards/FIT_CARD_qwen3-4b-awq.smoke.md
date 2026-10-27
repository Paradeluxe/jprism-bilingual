# FIT_CARD — qwen3-4b-awq n2 Lstep2 wikitext

**When:** 2026-09-27 06:46 UTC
**Where:** um-a100-01 (SICC)
**Status:** fit complete
**Model key:** Q4-AWQ
**HF id:** Qwen/Qwen3-4B-AWQ
**Loaded from:** `~/jspace/models/qwen3-4b-awq`
**n_layers:** 36
**d_model:** 2560
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34]
**target_layer:** final (35)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 4
**N prompts used:** 2
**seed:** 20260913
**corpus:** `~/jspace/jspace/fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**lens:** `~/jspace/jspace/lenses/local/qwen3-4b-awq/jlens_n2_Lstep2_wikitext.smoke.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3-4b-awq/fit_ckpt_n2_Lstep2_wikitext.smoke.pt`
**fit_sec:** 137.0
**fit_hours:** 0.04
**vram_peak_gb:** 11.376319408416748
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
