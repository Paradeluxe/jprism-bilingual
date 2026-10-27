# FIT_CARD — gemma4-e4b n2 Lstep2 zhwiki

**When:** 2026-09-30 19:10 UTC
**Where:** um-a100-03 (SICC)
**Status:** fit complete
**Model key:** G4E4B
**HF id:** google/gemma-4-E4B
**Loaded from:** `~/jspace/models/gemma-4-E4B`
**n_layers:** 42
**d_model:** 2560
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
**target_layer:** final (41)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 2
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/gemma4-e4b/jlens_n2_Lstep2_zhwiki.smoke.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/gemma4-e4b/fit_ckpt_n2_Lstep2_zhwiki.smoke.pt`
**fit_sec:** 77.0
**fit_hours:** 0.02
**vram_peak_gb:** 20.54458236694336
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
