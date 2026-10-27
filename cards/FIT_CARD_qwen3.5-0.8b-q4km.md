# FIT_CARD — qwen3.5-0.8b-q4km n1000 Lstep2 zhwiki

**When:** 2026-10-08 16:52 UTC
**Where:** um-h800-03 (SICC)
**Status:** fit complete
**Model key:** X08-Q4
**HF id:** unsloth/Qwen3.5-0.8B-GGUF
**Loaded from:** `~/jspace/models/gguf/qwen3.5-0.8b-q4km`
**n_layers:** 24
**d_model:** 1024
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
**target_layer:** final (23)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `zhq_fit_qwen3.5-0.8b-q4km.log`
**seed:** 20260913
**corpus:** `fit_corpus/zhwiki_n1000_L128.jsonl`
**corpus_sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**lens:** `~/jspace/jspace/lenses/local/qwen3.5-0.8b-q4km/jlens_n1000_Lstep2_zhwiki.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3.5-0.8b-q4km/fit_ckpt_n1000_Lstep2_zhwiki.pt`
**fit_sec:** 4726.4
**fit_hours:** 1.31
**vram_peak_gb:** 3.5728158950805664
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
