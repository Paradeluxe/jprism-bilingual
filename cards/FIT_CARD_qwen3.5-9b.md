# FIT_CARD — qwen3.5-9b n1000 Lstep2 zhwiki

**When:** 2026-10-02 21:52 UTC
**Where:** um-h800-02 (SICC)
**Status:** fit complete
**Model key:** 9B
**HF id:** Qwen/Qwen3.5-9B
**Loaded from:** `~/jspace/models/Qwen3.5-9B`
**n_layers:** 32
**d_model:** 4096
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
**target_layer:** final (31)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 4
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `zh_9b.log`
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/qwen3.5-9b/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3.5-9b/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 56281.1
**fit_hours:** 15.63
**vram_peak_gb:** 20.90526580810547
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** APPENDIX / not main Qwen3 scale table
