# FIT_CARD — qwen3-32b-fp8 n2 Lstep2 wikitext

**When:** 2026-10-12 09:29 UTC
**Where:** um-h800-01 (SICC)
**Status:** fit complete
**Model key:** Q32B-FP8
**HF id:** Qwen/Qwen3-32B-FP8
**Loaded from:** `~/jspace/models/Qwen3-32B-FP8`
**n_layers:** 64
**d_model:** 5120
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 50, 52, 54, 56, 58, 60, 62]
**target_layer:** final (63)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 2
**N prompts used:** 2
**seed:** 20260913
**corpus:** `~/jspace/jspace/fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**lens:** `~/jspace/jspace/lenses/local/qwen3-32b-fp8/jlens_n2_Lstep2_wikitext.smoke.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3-32b-fp8/fit_ckpt_n2_Lstep2_wikitext.smoke.pt`
**fit_sec:** 377.1
**fit_hours:** 0.10
**vram_peak_gb:** 65.3959755897522
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
