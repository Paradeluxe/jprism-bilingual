"""Build WikiText fixed slice: 1000 sequences x 128 tokens (Qwen3-0.6B tokenizer).

Policy (documented in CORPUS_CARD.md):
- Source: Salesforce/wikitext, config wikitext-103-raw-v1, split=train (fallback wikitext-2-raw-v1)
- Seed: 20260913 for any shuffle / selection
- Tokenize with Qwen3-0.6B tokenizer (local cache)
- Pack non-empty lines into non-overlapping windows of exactly TARGET_LEN tokens
- Decode each window back to text (the prompt string passed to jlens.fit)
- Drop windows whose decoded text contains any banned eval-prompt substring
- Keep first N=1000 accepted windows after packing (deterministic order after seed)
- Truncation: windows are exactly TARGET_LEN tokens by construction (no pad)
- jlens.fit will re-encode and truncate to max_seq_len=128 (same budget)

Never clears HF cache. Writes into project fit_corpus/ only.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

os.environ.setdefault("HF_HOME", r"E:\huggingface_cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_DATASETS_CACHE", r"E:\huggingface_cache\datasets")
os.environ.setdefault("TRANSFORMERS_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

PROJECT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(PROJECT, "fit_corpus")
OUT_JSONL = os.path.join(OUT_DIR, "wikitext_n1000_L128.jsonl")
OUT_CARD = os.path.join(OUT_DIR, "CORPUS_CARD.md")
MODEL_ID = r"E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B"

N = 1000
TARGET_LEN = 128
SEED = 20260913
MIN_VALID = 16 + 2  # skip_first=16 needs seq_len > 17

BANNED = [
    "Fact: The currency used in the country shaped like a boot is",
    "The number of legs on the animal that spins webs is",
    "The capital of France is",
    "Think of a sport: people kick a round ball into a net. The sport is",
    # older spider phrasing from n100 tests
    "The animal that spins webs has how many legs? The number is",
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_wikitext_texts():
    from datasets import load_dataset

    last_err = None
    for config in ("wikitext-103-raw-v1", "wikitext-2-raw-v1"):
        try:
            print(f"loading Salesforce/wikitext config={config} split=train ...", flush=True)
            ds = load_dataset(
                "Salesforce/wikitext",
                config,
                split="train",
                cache_dir=r"E:\huggingface_cache\datasets",
            )
            texts = [t for t in ds["text"] if t and t.strip()]
            print(f"  got {len(texts)} non-empty lines", flush=True)
            return texts, f"Salesforce/wikitext:{config}:train"
        except Exception as e:
            last_err = e
            print(f"  failed {config}: {e}", flush=True)
    raise RuntimeError(f"WikiText download/load failed: {last_err}")


def is_banned(text: str) -> bool:
    return any(b in text for b in BANNED)


def build_windows(texts, tok):
    """Pack lines into a token stream; emit non-overlapping TARGET_LEN windows."""
    buf_ids: list[int] = []
    windows: list[dict] = []
    line_i = 0
    while line_i < len(texts) and len(windows) < N * 3:
        # oversample a bit so bans / short decodes still leave N
        ids = tok.encode(texts[line_i], add_special_tokens=False)
        line_i += 1
        if not ids:
            continue
        buf_ids.extend(ids)
        while len(buf_ids) >= TARGET_LEN and len(windows) < N * 3:
            chunk = buf_ids[:TARGET_LEN]
            buf_ids = buf_ids[TARGET_LEN:]
            text = tok.decode(chunk, skip_special_tokens=True)
            if not text.strip():
                continue
            if is_banned(text):
                print(f"  banned window skipped at index candidate {len(windows)}", flush=True)
                continue
            # verify re-encode length is usable
            re_ids = tok.encode(text, add_special_tokens=False)
            if len(re_ids) < MIN_VALID:
                continue
            # Prefer near-128 after roundtrip; truncate note if longer
            n_tok = min(len(re_ids), TARGET_LEN)
            windows.append(
                {
                    "id": len(windows),
                    "text": text,
                    "n_tokens_window": TARGET_LEN,
                    "n_tokens_reencode": len(re_ids),
                    "n_tokens_fit_budget": n_tok,
                }
            )
    return windows


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    import transformers

    print(f"tokenizer from {MODEL_ID}", flush=True)
    tok = transformers.AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)

    texts, source_id = load_wikitext_texts()
    # Deterministic order: datasets train order is fixed; we do not shuffle lines.
    # Seed recorded for future selection variants.
    windows = build_windows(texts, tok)
    if len(windows) < N:
        raise RuntimeError(f"only built {len(windows)} windows, need {N}")
    selected = windows[:N]
    # reindex
    for i, w in enumerate(selected):
        w["id"] = i

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for w in selected:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")

    digest = sha256_file(OUT_JSONL)
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    n_tok_stats = [w["n_tokens_reencode"] for w in selected]
    card = f"""# CORPUS_CARD — wikitext_n1000_L128

**Built:** {now}
**File:** `{OUT_JSONL}`
**sha256:** `{digest}`
**N:** {N}
**Target length:** {TARGET_LEN} tokens (Qwen3-0.6B tokenizer)
**Seed:** {SEED} (recorded; primary slice is deterministic train-order packing, no shuffle)
**Source id:** `{source_id}`
**Tokenizer:** `{MODEL_ID}` (local_files_only)

## Slice policy

1. Load WikiText train split (non-empty `text` lines only).
2. Encode lines with Qwen3-0.6B tokenizer (`add_special_tokens=False`).
3. Concatenate into a token buffer; cut **non-overlapping** windows of exactly **{TARGET_LEN}** tokens.
4. Decode each window to a UTF-8 prompt string for `jlens.fit`.
5. Drop windows whose decoded text contains any banned classic eval prompt substring.
6. Keep the first **{N}** accepted windows (deterministic).

## Truncation / padding

- **No padding.** Windows are exactly {TARGET_LEN} tokens at cut time.
- Round-trip decode→encode may change length slightly; fit uses `max_seq_len={TARGET_LEN}` truncation.
- Rows with re-encode length < {MIN_VALID} were dropped (jlens `skip_first=16` needs seq_len > 17).

## Re-encode length stats (selected {N})

- min={min(n_tok_stats)} max={max(n_tok_stats)} mean={sum(n_tok_stats)/len(n_tok_stats):.1f}

## Banned eval prompts (must not appear as substrings)

{chr(10).join('- `' + b + '`' for b in BANNED)}

## JSONL schema

Each line: `{{"id": int, "text": str, "n_tokens_window": 128, "n_tokens_reencode": int, "n_tokens_fit_budget": int}}`
"""
    with open(OUT_CARD, "w", encoding="utf-8") as f:
        f.write(card)
    print(f"wrote {OUT_JSONL}", flush=True)
    print(f"sha256={digest}", flush=True)
    print(f"wrote {OUT_CARD}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
