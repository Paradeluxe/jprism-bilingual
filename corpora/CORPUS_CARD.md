# CORPUS_CARD — wikitext_n1000_L128

**Built:** 2026-09-13 18:59 台北?准??
**File:** `E:\hermes_playground\jspace-qwen-exp\fit_corpus\wikitext_n1000_L128.jsonl`
**sha256:** `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee`
**N:** 1000
**Target length:** 128 tokens (Qwen3-0.6B tokenizer)
**Seed:** 20260913 (recorded; primary slice is deterministic train-order packing, no shuffle)
**Source id:** `Salesforce/wikitext:wikitext-103-raw-v1:train`
**Tokenizer:** `E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B` (local_files_only)

## Slice policy

1. Load WikiText train split (non-empty `text` lines only).
2. Encode lines with Qwen3-0.6B tokenizer (`add_special_tokens=False`).
3. Concatenate into a token buffer; cut **non-overlapping** windows of exactly **128** tokens.
4. Decode each window to a UTF-8 prompt string for `jlens.fit`.
5. Drop windows whose decoded text contains any banned classic eval prompt substring.
6. Keep the first **1000** accepted windows (deterministic).

## Truncation / padding

- **No padding.** Windows are exactly 128 tokens at cut time.
- Round-trip decode→encode may change length slightly; fit uses `max_seq_len=128` truncation.
- Rows with re-encode length < 18 were dropped (jlens `skip_first=16` needs seq_len > 17).

## Re-encode length stats (selected 1000)

- min=128 max=128 mean=128.0

## Banned eval prompts (must not appear as substrings)

- `Fact: The currency used in the country shaped like a boot is`
- `The number of legs on the animal that spins webs is`
- `The capital of France is`
- `Think of a sport: people kick a round ball into a net. The sport is`
- `The animal that spins webs has how many legs? The number is`

## JSONL schema

Each line: `{"id": int, "text": str, "n_tokens_window": 128, "n_tokens_reencode": int, "n_tokens_fit_budget": int}`
