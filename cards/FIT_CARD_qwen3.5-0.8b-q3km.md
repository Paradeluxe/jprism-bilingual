# FIT_CARD — qwen3.5-0.8b-q3km n1000 Lstep2 wikitext

**When:** 2026-10-09 16:30 UTC
**Where:** um-a100-03 (SICC)
**Status:** fit complete
**Model key:** X08-Q3
**HF id:** unsloth/Qwen3.5-0.8B-GGUF
**Loaded from:** `~/jspace/models/gguf/qwen3.5-0.8b-q3km`
**n_layers:** 24
**d_model:** 1024
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
**target_layer:** final (23)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 8
**N prompts used:** 1000
**skip_rate:** 0.00% (1000/1000 prompts kept)  
**skip_rate source:** cluster fit log `q3k_smoke_519_15692.log`
**seed:** 20260913
**corpus:** `fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**lens:** `~/jspace/jspace/lenses/local/qwen3.5-0.8b-q3km/jlens_n1000_Lstep2_wikitext.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3.5-0.8b-q3km/fit_ckpt_n1000_Lstep2_wikitext.pt`
**fit_sec:** 7032.9
**fit_hours:** 1.95
**vram_peak_gb:** 3.5182504653930664
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
