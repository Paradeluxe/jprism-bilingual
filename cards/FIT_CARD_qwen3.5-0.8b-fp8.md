# FIT_CARD — qwen3.5-0.8b-fp8 n1000 Lstep2 zhwiki

**When:** 2026-10-10 00:54 UTC
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
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `fp8_zhwiki_fit_15692.log`
**seed:** 20260913
**corpus:** `~/jspace/jspace/fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/qwen3.5-0.8b-fp8/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3.5-0.8b-fp8/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 7432.0
**fit_hours:** 2.06
**vram_peak_gb:** 3.5264596939086914
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
