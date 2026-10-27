# FIT_CARD — qwen3.5-0.8b-fp8 n2 Lstep2 zhwiki

**When:** 2026-10-09 22:49 UTC
**Where:** um-a100-03 (SICC)
**Status:** fit complete
**Model key:** X08-FP8
**HF id:** surogate/Qwen3.5-0.8B-FP8
**Loaded from:** `~/jspace/models/qwen3.5-0.8b-fp8`
**n_layers:** 24
**d_model:** 1024
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
**target_layer:** final (23)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 2
**seed:** 20260913
**corpus:** `~/jspace/jspace/fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**lens:** `~/jspace/jspace/lenses/local/qwen3.5-0.8b-fp8/jlens_n2_Lstep2_zhwiki.smoke.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3.5-0.8b-fp8/fit_ckpt_n2_Lstep2_zhwiki.smoke.pt`
**fit_sec:** 15.6
**fit_hours:** 0.00
**vram_peak_gb:** 3.4858126640319824
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
