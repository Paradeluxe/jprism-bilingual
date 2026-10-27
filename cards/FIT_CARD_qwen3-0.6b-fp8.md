# FIT_CARD — qwen3-0.6b-fp8 n1000 Lstep2 zhwiki

**When:** 2026-10-08 20:06 UTC
**Where:** um-a100-03 (SICC)
**Status:** fit complete
**Model key:** Q06-FP8
**HF id:** Qwen/Qwen3-0.6B-FP8
**Loaded from:** `~/jspace/models/qwen3-0.6b-fp8`
**n_layers:** 28
**d_model:** 1024
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
**target_layer:** final (27)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `zh_gap_retry.log`
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/qwen3-0.6b-fp8/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3-0.6b-fp8/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 6014.1
**fit_hours:** 1.67
**vram_peak_gb:** 2.550480365753174
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
