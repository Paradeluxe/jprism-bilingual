#!/usr/bin/env python3
"""build_zh_corpus.py — build a Chinese fit corpus with EXACTLY the same protocol as
build_fit_corpus.py (English WikiText side), so the two are comparable: only the text
changes, never the statistics.

Protocol held identical to the English corpus (see fit_corpus/CORPUS_CARD.md):
  1000 windows x exactly 128 tokens (Qwen3-0.6B tokenizer) -> decode to a UTF-8 prompt
  -> drop banned eval substrings -> drop re-encode < MIN_VALID -> keep first 1000.
  No shuffle, no padding, seed recorded.

What changes vs English: the SOURCE, and the banned-substring list, which must be the
Chinese equivalents of the classic eval prompts (banning only the English strings would
let Chinese eval prompts leak into the corpus).

Usage:
  python build_zh_corpus.py --source wikipedia    # -> zhwiki_n1000_L128.jsonl
  python build_zh_corpus.py --source fineweb_edu # -> zhfinewebedu_n1000_L128.jsonl
  python build_zh_corpus.py --source <label> --out-dir fit_corpus --tag zhwiki
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
from datetime import datetime, timezone

os.environ.setdefault("HF_HOME", r"E:\huggingface_cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_DATASETS_CACHE", r"E:\huggingface_cache\datasets")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

PROJECT = os.path.dirname(os.path.abspath(__file__))
MODEL_ID = r"E:\huggingface_cache\hub\models--Qwen--Qwen3-0.6B"

N = 1000
TARGET_LEN = 128
SEED = 20260913  # same recorded seed as the English corpus (selection is deterministic anyway)
MIN_VALID = 16 + 2  # skip_first=16 needs seq_len > 17

# Chinese equivalents of the English banned classic eval prompts + the ones this project
# actually uses in PROMPTS/measurements. Substring match, same rule as the English side.
BANNED_ZH = [
    "法国的首都是",
    "法国的首都为",
    "意大利的首都",
    "澳大利亚的首都是",
    "日本的首都",
    "有四条腿、会织网的动物",
    "形似靴子的国家使用的货币",
    "印 shaped 橄榄球",
    "把球踢进网的运动",
    "The capital of France is",
    "The number of legs on the animal that spins webs is",
    "Think of a sport: people kick a round ball into a net.",
]

# --- sources: label -> (repo_id, config, text_field, streaming_ok)
SOURCES = {
    "wikipedia": ("wikimedia/wikipedia", "20231101.zh", "text", True),
    "wikipedia_alt": ("pleisto/wikipedia-cn-20230720", None, "text", True),
    "fineweb_edu": ("opencsg/chinese-fineweb-edu", None, "text", True),
    "fineweb": ("opencsg/chinese-fineweb", None, "text", True),
    "industry_wiki": ("BAAI/IndustryCorpus2", "wikipedia", "text", True),
    "cci_high": ("BAAI/CCI-High", None, "content", True),
    "cluec": ("CLUEC/CLUECCorpusSmall", None, "text", True),
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_banned(text: str) -> bool:
    return any(b in text for b in BANNED_ZH)


def han_ratio(text: str) -> float:
    """Guard against a 'Chinese' corpus that is mostly ASCII (code/URLs/boilerplate)."""
    if not text:
        return 0.0
    han = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return han / len(text)


def load_texts(label: str, *, min_han_ratio: float, max_lines: int, verbose: bool = True):
    from datasets import load_dataset

    if label not in SOURCES:
        raise SystemExit(f"unknown source {label!r}; known: {sorted(SOURCES)}")
    repo, config, field, streaming = SOURCES[label]
    kw = {"name": config} if config else {}
    if verbose:
        print(f"streaming {repo}" + (f" / {config}" if config else "") + f" field={field}", flush=True)
    ds = load_dataset(repo, split="train", streaming=streaming, **kw)
    texts: list[str] = []
    rejected_han = 0
    for row in ds:
        t = row.get(field)
        if not t or not t.strip():
            continue
        if han_ratio(t) < min_han_ratio:
            rejected_han += 1
            continue
        texts.append(t)
        if len(texts) >= max_lines:
            break
    if verbose:
        print(f"  kept {len(texts)} lines (rejected {rejected_han} for han_ratio<{min_han_ratio})", flush=True)
    return texts, f"{repo}" + (f":{config}" if config else "")


def build_windows(texts, tok, *, oversample: int = 3):
    buf_ids: list[int] = []
    windows: list[dict] = []
    line_i = 0
    while line_i < len(texts) and len(windows) < N * oversample:
        ids = tok.encode(texts[line_i], add_special_tokens=False)
        line_i += 1
        if not ids:
            continue
        buf_ids.extend(ids)
        while len(buf_ids) >= TARGET_LEN and len(windows) < N * oversample:
            chunk = buf_ids[:TARGET_LEN]
            buf_ids = buf_ids[TARGET_LEN:]
            text = tok.decode(chunk, skip_special_tokens=True)
            if not text.strip() or is_banned(text):
                continue
            if han_ratio(text) < 0.4:  # a window that is mostly non-Han is not our corpus
                continue
            re_ids = tok.encode(text, add_special_tokens=False)
            if len(re_ids) < MIN_VALID:
                continue
            windows.append({
                "id": len(windows),
                "text": text,
                "n_tokens_window": TARGET_LEN,
                "n_tokens_reencode": len(re_ids),
                "n_tokens_fit_budget": min(len(re_ids), TARGET_LEN),
            })
    return windows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="wikipedia", choices=sorted(SOURCES) + ["custom"])
    ap.add_argument("--repo", default=None, help="for --source custom")
    ap.add_argument("--config", default=None)
    ap.add_argument("--field", default="text")
    ap.add_argument("--tag", default="zhwiki", help="filename prefix: <tag>_n1000_L128")
    ap.add_argument("--out-dir", default=os.path.join(PROJECT, "fit_corpus"))
    ap.add_argument("--min-han-ratio", type=float, default=0.5)
    ap.add_argument("--window-min-han", type=float, default=0.4)
    ap.add_argument("--max-lines", type=int, default=20000)
    ap.add_argument("--dry-run", action="store_true", help="build, print stats, write nothing")
    args = ap.parse_args()

    if args.source == "custom":
        if not args.repo:
            raise SystemExit("--source custom needs --repo")
        SOURCES["custom"] = (args.repo, args.config, args.field, True)

    import transformers

    print(f"tokenizer: {MODEL_ID}", flush=True)
    tok = transformers.AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)

    texts, source_id = load_texts(
        args.source, min_han_ratio=args.min_han_ratio, max_lines=args.max_lines)
    windows = build_windows(texts, tok)
    # apply the window-level Han guard with the caller-provided threshold
    windows = [w for w in windows if han_ratio(w["text"]) >= args.window_min_han]
    if len(windows) < N:
        raise RuntimeError(
            f"only built {len(windows)} windows (need {N}); lower --min-han-ratio or "
            f"--window-min-han, or raise --max-lines")

    selected = windows[:N]
    for i, w in enumerate(selected):
        w["id"] = i

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    out_jsonl = os.path.join(out_dir, f"{args.tag}_n1000_L128.jsonl")
    out_card = os.path.join(out_dir, f"CORPUS_CARD_{args.tag}.md")

    stats = [w["n_tokens_reencode"] for w in selected]
    chars = [len(w["text"]) for w in selected]
    han = [han_ratio(w["text"]) for w in selected]

    if not args.dry_run:
        with open(out_jsonl, "w", encoding="utf-8") as f:
            for w in selected:
                f.write(json.dumps(w, ensure_ascii=False) + "\n")
    digest = sha256_file(out_jsonl) if not args.dry_run else "(dry-run, not written)"
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")

    print(f"\nSOURCE       {source_id}")
    print(f"N            {len(selected)} windows x {TARGET_LEN} tokens")
    print(f"tokens       min={min(stats)} max={max(stats)} mean={sum(stats)/len(stats):.1f}")
    print(f"chars/window min={min(chars)} max={max(chars)} mean={sum(chars)//len(chars)}")
    print(f"han_ratio    min={min(han):.2f} mean={sum(han)/len(han):.2f}")
    print(f"sha256       {digest}")
    print(f"\nsample[0]: {selected[0]['text'][:120]}")
    print(f"sample[1]: {selected[1]['text'][:120]}")
    if args.dry_run:
        print("\n(dry-run: nothing written)")
        return 0

    card = f"""# CORPUS_CARD — {args.tag}_n1000_L128

**Built:** {now}
**File:** `{out_jsonl}`
**sha256:** `{digest}`
**N:** {len(selected)}
**Target length:** {TARGET_LEN} tokens (Qwen3-0.6B tokenizer)
**Seed:** {SEED} (recorded; deterministic train-order packing, no shuffle)
**Source id:** `{source_id}`
**Tokenizer:** `{MODEL_ID}` (local_files_only)
**Language:** Chinese (Han-ratio guard: line >= {args.min_han_ratio}, window >= {args.window_min_han})

## Comparability with the English corpus

Identical to `wikitext_n1000_L128.jsonl` on every axis except the text itself:
same N, same {TARGET_LEN}-token non-overlapping windows, same tokenizer, same
`skip_first`/dim_batch at fit time, same deterministic packing. Any English-vs-Chinese
lens difference is therefore attributable to language, not to protocol.

## Slice policy

1. Stream the source train split; keep non-empty lines.
2. Drop lines whose Han ratio < {args.min_han_ratio} (code/URL/boilerplate guard).
3. Encode with Qwen3-0.6B tokenizer (`add_special_tokens=False`).
4. Concatenate into a token buffer; cut **non-overlapping** **{TARGET_LEN}**-token windows.
5. Decode each window to a UTF-8 prompt string; drop windows with Han ratio < {args.window_min_han}.
6. Drop windows containing any banned eval substring (Chinese equivalents listed below).
7. Keep the first **{N}** accepted windows (deterministic).

## Truncation / padding

- **No padding.** Windows are exactly {TARGET_LEN} tokens at cut time.
- Round-trip decode->encode may change length; fit truncates to `max_seq_len={TARGET_LEN}`.
- Rows with re-encode < {MIN_VALID} dropped (jlens `skip_first=16` needs seq_len > 17).

## Stats (selected {len(selected)})

- re-encode tokens: min={min(stats)} max={max(stats)} mean={sum(stats)/len(stats):.1f}
- chars per window: min={min(chars)} max={max(chars)} mean={sum(chars)//len(chars)}
- Han ratio: min={min(han):.2f} mean={sum(han)/len(han):.2f}

## Banned eval prompts (must not appear as substrings)

{chr(10).join('- `' + b + '`' for b in BANNED_ZH)}

## JSONL schema

Each line: `{{"id": int, "text": str, "n_tokens_window": {TARGET_LEN}, "n_tokens_reencode": int, "n_tokens_fit_budget": int}}`
"""
    with open(out_card, "w", encoding="utf-8") as f:
        f.write(card)
    print(f"wrote {out_jsonl}")
    print(f"wrote {out_card}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        sys.exit(1)
