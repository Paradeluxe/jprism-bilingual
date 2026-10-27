# FIT_CARD — qwen3-32b-fp8 n1000 Lstep2 zhwiki

**When:** 2026-10-17 03:59 UTC
**Where:** um-h800-02 (SICC)
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
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `zhwave_q32b.log`
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/qwen3-32b-fp8/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3-32b-fp8/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 88647.9
**fit_hours:** 24.62
**vram_peak_gb:** 65.3949990272522
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
