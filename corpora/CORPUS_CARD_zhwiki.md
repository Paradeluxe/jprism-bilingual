# CORPUS_CARD — zhwiki_n1000_L128

**Built:** 2026-09-27 23:26 台北?准??
**File:** `E:\hermes_playground\jspace-qwen-exp\fit_corpus\zhwiki_n1000_L128.jsonl`
**sha256:** `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792`
**N:** 1000
**Target length:** 128 tokens (Qwen3-0.6B tokenizer)
**Seed:** 20260913 (recorded; deterministic train-order packing, no shuffle)
**Source id:** `wikimedia/wikipedia:20231101.zh`
**Tokenizer:** `E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B` (local_files_only)
**Language:** Chinese (Han-ratio guard: line >= 0.5, window >= 0.4)

## Comparability with the English corpus

Identical to `wikitext_n1000_L128.jsonl` on every axis except the text itself:
same N, same 128-token non-overlapping windows, same tokenizer, same
`skip_first`/dim_batch at fit time, same deterministic packing. Any English-vs-Chinese
lens difference is therefore attributable to language, not to protocol.

## Slice policy

1. Stream the source train split; keep non-empty lines.
2. Drop lines whose Han ratio < 0.5 (code/URL/boilerplate guard).
3. Encode with Qwen3-0.6B tokenizer (`add_special_tokens=False`).
4. Concatenate into a token buffer; cut **non-overlapping** **128**-token windows.
5. Decode each window to a UTF-8 prompt string; drop windows with Han ratio < 0.4.
6. Drop windows containing any banned eval substring (Chinese equivalents listed below).
7. Keep the first **1000** accepted windows (deterministic).

## Truncation / padding

- **No padding.** Windows are exactly 128 tokens at cut time.
- Round-trip decode->encode may change length; fit truncates to `max_seq_len=128`.
- Rows with re-encode < 18 dropped (jlens `skip_first=16` needs seq_len > 17).

## Stats (selected 1000)

- re-encode tokens: min=127 max=128 mean=128.0
- chars per window: min=128 max=307 mean=184
- Han ratio: min=0.41 mean=0.84

## Banned eval prompts (must not appear as substrings)

- `法国的首都是`
- `法国的首都为`
- `意大利的首都`
- `澳大利亚的首都是`
- `日本的首都`
- `有四条腿、会织网的动物`
- `形似靴子的国家使用的货币`
- `印 shaped 橄榄球`
- `把球踢进网的运动`
- `The capital of France is`
- `The number of legs on the animal that spins webs is`
- `Think of a sport: people kick a round ball into a net.`

## JSONL schema

Each line: `{"id": int, "text": str, "n_tokens_window": 128, "n_tokens_reencode": int, "n_tokens_fit_budget": int}`
