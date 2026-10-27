# FIT_CARD — qwen3-8b-gptq4 n2 Lstep2 wikitext

**When:** 2026-09-30 13:11 UTC
**Where:** um-a100-02 (SICC)
**Status:** fit complete
**Model key:** Q8B-GPTQ4
**HF id:** JunHowie/Qwen3-8B-GPTQ-Int4
**Loaded from:** `~/jspace/models/qwen3-8b-gptq4`
**n_layers:** 36
**d_model:** 4096
**source_layers (every 2):** [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34]
**target_layer:** final (35)
**max_seq_len:** 128
**skip_first:** 16
**dim_batch:** 2
**N prompts used:** 2
**seed:** 20260913
**corpus:** `~/jspace/jspace/fit_corpus/wikitext_n1000_L128.jsonl`
**corpus_sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**lens:** `~/jspace/jspace/lenses/local/qwen3-8b-gptq4/jlens_n2_Lstep2_wikitext.smoke.pt`
**checkpoint:** `~/jspace/jspace/fit_ckpt/qwen3-8b-gptq4/fit_ckpt_n2_Lstep2_wikitext.smoke.pt`
**fit_sec:** 809.5
**fit_hours:** 0.22
**vram_peak_gb:** 19.748577117919922
**dtype:** bf16
**protocol:** LOCKED_DECISIONS / SOP_LOCAL_FIT (NP not in main table)
**track:** main Qwen3 scale table (0.6/1.7/4B)
