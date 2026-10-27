# The two fitting corpora

One corpus per language; identical on every axis except the text itself.

| file | source | windows | sha256 |
|------|--------|---------|--------|
| `wikitext_n1000_L128.jsonl` | WikiText-103 train split | 1,000 × 128 tok | `dacf54dd…95a21ee` |
| `zhwiki_n1000_L128.jsonl` | Chinese Wikipedia dump (Nov 2023) | 1,000 × 128 tok | `f1b108c4…4cbbd2792` |

Full hashes:

```
dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee  wikitext_n1000_L128.jsonl
f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792  zhwiki_n1000_L128.jsonl
```

Build rules (both arms):

- Non-overlapping 128-token windows cut in stream order, packed
  deterministically, no shuffling.
- Cut with a **single fixed tokenizer** (Qwen3-0.6B) so the two corpora share
  one yardstick; each model re-tokenizes the same windows through its own
  family tokenizer at fit time (so the effective body budget differs by family,
  e.g. Gemma's BOS leaves 127).
- The Chinese arm adds line-level and window-level Han-ratio guards (line ≥ 0.5,
  window ≥ 0.4) to exclude code, URLs, and boilerplate.
- Any window containing a banned evaluation substring (probe answers) was
  dropped at build time.

The corpus is the only thing that differs between the two lenses of a pair.
Never rebuild a corpus under the same name on another machine — either move the
file or finish that arm where it was built.
