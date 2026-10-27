# FIT_CARD — gemma4-12b n1000 Lstep2 zhwiki

**When:** 2026-10-08 01:27 UTC
**Where:** um-h800-02 (SICC)
**Status:** fit complete
**Model key:** G4-12B
**HF id:** google/gemma-4-12B
**Loaded from:** `~/jspace/models/gemma-4-12B`
**n_layers:** 48
**d_model:** 3840
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46]
**target_layer:** final (47)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 4
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `zh12b_h800_fit.log`
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/gemma4-12b/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/gemma4-12b/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 26540.3
**fit_hours:** 7.37
**vram_peak_gb:** 27.62250804901123
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
