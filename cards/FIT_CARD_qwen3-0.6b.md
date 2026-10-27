# FIT_CARD — qwen3-0.6b n1000 Lstep2 wikitext

**When:** 2026-10-04 23:26 UTC
**Where:** um-h800-02 (SICC)
**Status:** fit complete
**Model key:** Q06
**HF id:** Qwen/Qwen3-0.6B
**Loaded from:** `~/jspace/models/Qwen3-0.6B`
**n_layers:** 28
**d_model:** 1024
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26]
**target_layer:** final (27)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `leg_q06_fit.log`
**seed:** 20260913
**corpus:** `fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**lens:** `~/jspace/jspace/lenses/local/qwen3-0.6b/jlens_n1000_Lstep2_wikitext.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3-0.6b/fit_ckpt_n1000_Lstep2_wikitext.pt`
**fit_sec:** 3274.9
**fit_hours:** 0.91
**vram_peak_gb:** 2.597111225128174
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
