#!/usr/bin/env python3
"""tokenizer_consistency.py — re-encode the jspace fit corpora (windows cut at
exactly 128 tokens under the Qwen3-0.6B tokenizer) with each candidate model's
OWN tokenizer and report the token-count distribution.

Question it answers: when model X's tokenizer reads the same window text that was
cut to 128 tokens under Qwen3-0.6B, does it also see ~128 tokens? Or does the
fit's max_seq_len=128 truncation bite differently per model?

For each (tokenizer, corpus):
  full_special : len(tok(text))                       -> what jlens.fit sees pre-cap
  no_special   : len(tok(text, add_special_tokens=False)) -> windowing semantics
Stats: n, min, p25, median, p75, max, mean, ==128 count, >128 count, <128 count,
       <120 count, total/max overage beyond 128.

Usage:
  python tokenizer_consistency.py \
      --corpus fit_corpus/wikitext_n1000_L128.jsonl --corpus-tag wikitext \
      --tok qwen3-0.6b=E:/huggingface_cache/hub/models--Qwen--Qwen3-0.6B \
      --tok qwen3-8b=E:/huggingface_cache/hub/models--Qwen--Qwen3-8B \
      --out RESULT/TOKENIZER_CONSISTENCY/tok_consistency_local.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys


def load_texts(path: str) -> list:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line)["text"])
    return out


def resolve_dir(path: str) -> str:
    """Accept a flat model dir or a HF cache bucket dir (models--Org--Name)."""
    for probe in ("tokenizer_config.json", "tokenizer.json", "vocab.json", "config.json"):
        if os.path.isfile(os.path.join(path, probe)):
            return path
    snaps = os.path.join(path, "snapshots")
    if os.path.isdir(snaps):
        subs = sorted(os.listdir(snaps))
        if subs:
            return os.path.join(snaps, subs[-1])
    return path


def pct(vals, q):
    if not vals:
        return None
    s = sorted(vals)
    i = (len(s) - 1) * q
    lo = int(i)
    hi = min(lo + 1, len(s) - 1)
    fr = i - lo
    return round(s[lo] * (1 - fr) + s[hi] * fr, 2)


def describe(vals):
    return {
        "n": len(vals),
        "min": min(vals),
        "p25": pct(vals, 0.25),
        "median": statistics.median(vals),
        "p75": pct(vals, 0.75),
        "max": max(vals),
        "mean": round(sum(vals) / len(vals), 4),
        "eq_128": sum(1 for v in vals if v == 128),
        "gt_128": sum(1 for v in vals if v > 128),
        "lt_128": sum(1 for v in vals if v < 128),
        "lt_120": sum(1 for v in vals if v < 120),
        "total_overage": sum(max(0, v - 128) for v in vals),
        "max_overage": max([max(0, v - 128) for v in vals], default=0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--corpus-tag", default="")
    ap.add_argument("--tok", action="append", default=[], help="NAME=PATH (repeatable)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    import transformers
    print(f"transformers {transformers.__version__}", flush=True)
    texts = load_texts(args.corpus)
    print(f"corpus {args.corpus}: {len(texts)} windows (cut at 128 tokens under Qwen3-0.6B)", flush=True)

    results = {}
    for spec in args.tok:
        name, _, path = spec.partition("=")
        rpath = resolve_dir(path)
        try:
            tok = transformers.AutoTokenizer.from_pretrained(rpath, local_files_only=True)
        except Exception as e:
            print(f"[TOKFAIL] {name}: {type(e).__name__}: {e}", flush=True)
            results[name] = {"error": f"{type(e).__name__}: {e}", "path": path}
            continue
        full = []
        nospec = []
        for t in texts:
            full.append(len(tok(t)["input_ids"]))
            nospec.append(len(tok(t, add_special_tokens=False)["input_ids"]))
        d = {"path": path, "resolved": rpath, "full_special": describe(full), "no_special": describe(nospec)}
        results[name] = d
        fs = d["full_special"]
        ns = d["no_special"]
        print(
            f"{name:22s} full: min={fs['min']:4d} med={fs['median']:6.1f} max={fs['max']:4d} mean={fs['mean']:7.2f} "
            f"eq128={fs['eq_128']:4d} >128={fs['gt_128']:4d} <128={fs['lt_128']:4d} over={fs['total_overage']:5d} "
            f"| nospec: med={ns['median']:6.1f} max={ns['max']:4d} eq128={ns['eq_128']:4d}",
            flush=True,
        )

    out = {
        "corpus": args.corpus,
        "corpus_tag": args.corpus_tag,
        "n_windows": len(texts),
        "tokenizers": results,
    }
    if args.out:
        od = os.path.dirname(os.path.abspath(args.out))
        if od:
            os.makedirs(od, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("wrote", args.out, flush=True)

    fails = [k for k, v in results.items() if "error" in v]
    if fails:
        print("TOKFAILS:", ",".join(fails), flush=True)


if __name__ == "__main__":
    main()
