# FIT_CARD — gemma4-e2b n1000 Lstep2 zhwiki

**When:** 2026-09-30 19:07 UTC
**Where:** um-a100-03 (SICC)
**Status:** fit complete
**Model key:** G4E2B
**HF id:** google/gemma-4-E2B
**Loaded from:** `~/jspace/models/gemma-4-E2B`
**n_layers:** 35
**d_model:** 1536
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]
**target_layer:** final (34)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `ticket_zh_fit.log`
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/gemma4-e2b/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/gemma4-e2b/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 14693.6
**fit_hours:** 4.08
**vram_peak_gb:** 13.362086296081543
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
