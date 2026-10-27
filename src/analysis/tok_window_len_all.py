"""Per-window tokenizer lengths of the fit corpora, for every family in the matrix.

Why: fit_corpus/*_n1000_L128.jsonl was cut into exactly 128 tokens with the
Qwen3-0.6B tokenizer. Each model re-tokenizes the decoded prompt text with its own
tokenizer at fit time, so the effective window length is family-dependent. Fit
truncates to max_seq_len=128 (run_fit_sicc.MAX_SEQ_LEN) and drops rows < 18 tokens
(skip_first=16).

BOS is measured, not assumed: bos_delta = len(encode(add_special_tokens=True)) -
len(encode(add_special_tokens=False)) on a probe string. The fit path
(jlens/hf.py:157-160) calls tokenizer(text, truncation=True, max_length=128) with
no add_special_tokens argument, i.e. the transformers default True, so the
content budget is 128 - bos_delta.

Writes RESULT/TOK_WINDOW_LEN_all.{json,md} + one CSV per (tokenizer, corpus).
Reads only local files; no network.
"""
import csv
import hashlib
import json
import statistics
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent
CORPORA = [
    ("wikitext", ROOT / "fit_corpus" / "wikitext_n1000_L128.jsonl"),
    ("zhwiki", ROOT / "fit_corpus" / "zhwiki_n1000_L128.jsonl"),
]
BASELINE = "qwen3-0.6b"
MODELS = [
    # tag, tokenizer.json, what it covers / note
    ("qwen3-0.6b", Path("E:/huggingface_cache/hub/models--Qwen--Qwen3-0.6B/tokenizer.json"),
     "Qwen3 family (the tokenizer that cut the corpora)"),
    ("qwen3.5-0.8b", ROOT / "tok" / "qwen3.5-0.8b" / "tokenizer.json",
     "Qwen3.5 family; 0.8B is byte-identical to 2B/9B mirrors"),
    ("qwen3.6-27b", ROOT / "tok" / "3-6-27b" / "tokenizer.json",
     "Qwen3.6-27B; byte-identical to the Qwen3.5 tokenizer"),
    ("qwen3.8-27b", ROOT / "tok" / "3-8-27b" / "tokenizer.json",
     "Qwen3.8-27B; new 248k vocab, not shared with 3.5/3.6"),
    ("gemma4-e2b", ROOT / "tok" / "gemma4-e2b" / "tokenizer.json",
     "Gemma-4; E2B/E4B/12B ship the same tokenizer.json bytes"),
    ("gemma4-e4b", ROOT / "tok" / "gemma4-e4b" / "tokenizer.json",
     "Gemma-4 (same bytes as E2B)"),
    ("gemma4-12b", ROOT / "tok" / "gemma4-12b" / "tokenizer.json",
     "Gemma-4 (same bytes as E2B; tokenizer_config omits add_bos_token but the "
     "template post-processor still adds <bos>)"),
    ("gemma4-31b", ROOT / "tok" / "gemma4-31b" / "tokenizer.json",
     "Gemma-4 31B (same bytes as E2B)"),
]
BUDGET = 128
SKIP_MIN = 18
BIN_EDGES = [0, 100, 110, 118, 122, 126, 128, 130, 135, 140, 150, 10 ** 6]
PROBE = "数学是研究数量、结构以及空间等概念的学科。"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lengths(tok: Tokenizer, texts, special=False):
    return [len(tok.encode(t, add_special_tokens=special).ids) for t in texts]


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def main():
    out = {
        "budget": BUDGET,
        "skip_min": SKIP_MIN,
        "bos_measured_by": "encode(probe, add_special_tokens=True) - encode(probe, add_special_tokens=False)",
        "fit_path": "jlens/hf.py:157-160 (SICC): tokenizer(text, return_tensors='pt', truncation=True, max_length=128), add_special_tokens default True",
        "models": {},
        "corpora_sha256": {},
        "rows": [],
    }
    dst = ROOT / "RESULT"
    dst.mkdir(exist_ok=True)

    corpora = {}
    for name, path in CORPORA:
        rows = [json.loads(line) for line in path.open(encoding="utf-8")]
        corpora[name] = rows
        out["corpora_sha256"][name] = sha256(path)

    for tag, tok_path, note in MODELS:
        tok = Tokenizer.from_file(str(tok_path))
        bos = len(tok.encode(PROBE, add_special_tokens=True).ids) - len(
            tok.encode(PROBE, add_special_tokens=False).ids)
        meta = {
            "tokenizer_json": str(tok_path),
            "sha256": sha256(tok_path),
            "vocab_size": tok.get_vocab_size(),
            "bos_tokens": bos,
            "content_budget": BUDGET - bos,
            "note": note,
        }
        out["models"][tag] = meta

        for name, rows in corpora.items():
            texts = [r["text"] for r in rows]
            g = lengths(tok, texts)
            base = [r["n_tokens_reencode"] for r in rows]
            over = [i for i, v in enumerate(g) if v + bos > BUDGET]
            loss = [v + bos - BUDGET for v in g if v + bos > BUDGET]
            hist = {}
            for lo, hi in zip(BIN_EDGES, BIN_EDGES[1:]):
                label = f"[{lo},{hi})" if hi < 10 ** 6 else f"[{lo},inf)"
                hist[label] = sum(1 for v in g if lo <= v < hi)
            row = {
                "model": tag,
                "corpus": name,
                "bos_tokens": bos,
                "content_budget": BUDGET - bos,
                "n_windows": len(g),
                "min": min(g),
                "p05": pct(g, 0.05),
                "median": int(statistics.median(g)),
                "mean": round(statistics.fmean(g), 2),
                "p95": pct(g, 0.95),
                "max": max(g),
                "n_truncated_at_fit": len(over),
                "truncated_ids": over,
                "tokens_lost_mean": round(statistics.fmean(loss), 2) if loss else 0.0,
                "tokens_lost_max": max(loss) if loss else 0,
                "tokens_lost_total": sum(loss),
                "n_under_skip_min": sum(1 for v in g if v < SKIP_MIN),
                "delta_vs_qwen3_min": min(a - b for a, b in zip(g, base)),
                "delta_vs_qwen3_max": max(a - b for a, b in zip(g, base)),
                "delta_vs_qwen3_median": int(statistics.median([a - b for a, b in zip(g, base)])),
                "hist": hist,
            }
            out["rows"].append(row)

            csv_path = dst / f"TOK_WINDOW_LEN_{tag}_{name}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["model", "corpus", "id", "chars", "content_tokens",
                            "tokens_with_special", "delta_vs_qwen3_baseline",
                            "truncated_at_fit"])
                for i, r in enumerate(rows):
                    w.writerow([tag, name, r["id"], len(r["text"]), g[i], g[i] + bos,
                                g[i] - base[i], int(g[i] + bos > BUDGET)])
            row["csv"] = str(csv_path)

    # Segmentation identity: different tokenizer.json bytes can still segment plain text
    # identically (e.g. a version that only adds special tokens). Compare token ids across
    # every pair of distinct tokenizers over both corpora, so equal tables are provably real.
    uniq = {}
    for tag, m in out["models"].items():
        uniq.setdefault(m["sha256"], tag)
    ids_cache = {}
    texts_all = [(name, r["text"]) for name, rows in corpora.items() for r in rows]
    for sha, tag in uniq.items():
        tok = Tokenizer.from_file(out["models"][tag]["tokenizer_json"])
        ids_cache[tag] = [tok.encode(t, add_special_tokens=False).ids for _, t in texts_all]
    pair_checks = []
    tags = list(ids_cache)
    for i in range(len(tags)):
        for j in range(i + 1, len(tags)):
            a, b = ids_cache[tags[i]], ids_cache[tags[j]]
            eq = sum(1 for x, y in zip(a, b) if x == y)
            pair_checks.append({"a": tags[i], "b": tags[j], "windows": len(a),
                                "identical_ids": eq, "differing_ids": len(a) - eq})
    out["segmentation_identity"] = pair_checks

    (dst / "TOK_WINDOW_LEN_all.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    # Dedupe rows for the reader: one table line per distinct tokenizer byte-set.
    by_sha = {}
    for tag, m in out["models"].items():
        by_sha.setdefault(m["sha256"], []).append(tag)

    L = ["# Per-window tokenizer lengths of the fit corpora\n"]
    L.append(
        "Both corpora were cut as exactly 128 tokens with the Qwen3-0.6B tokenizer "
        f"(`{out['models'][BASELINE]['sha256'][:8]}`) and are re-tokenized per family at fit "
        "time. Fit truncates to `max_seq_len=128` and drops rows < 18 tokens (skip_first=16); "
        "the fit path is `jlens/hf.py:157-160`, which does not pass `add_special_tokens`, so any "
        "tokenizer that prepends a BOS token eats one of the 128. BOS counts below are measured "
        "per tokenizer, not assumed.\n"
    )
    L.append("## Tokenizer identity\n")
    L.append("| tokenizer | sha256 | vocab | BOS | content budget | covers |")
    L.append("|---|---|---|---|---|---|")
    for sha, tags in by_sha.items():
        m = out["models"][tags[0]]
        L.append(
            f"| {tags[0]} | `{sha[:12]}` | {m['vocab_size']:,} | {m['bos_tokens']} | "
            f"{m['content_budget']} | {', '.join(tags)} |"
        )
    L.append(
        "\nByte-identical tokenizers produce byte-identical length tables, so the per-window "
        "numbers below are listed once per distinct tokenizer.\n"
    )
    L.append("## Per-window length distribution (content tokens)\n")
    L.append("| tokenizer | corpus | n | min | p05 | median | mean | p95 | max | truncated at fit | mean lost | max lost |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    seen = set()
    for r in out["rows"]:
        key = (out["models"][r["model"]]["sha256"], r["corpus"])
        if key in seen:
            continue
        seen.add(key)
        L.append(
            f"| {r['model']} | {r['corpus']} | {r['n_windows']} | {r['min']} | {r['p05']} | "
            f"{r['median']} | {r['mean']} | {r['p95']} | {r['max']} | "
            f"{r['n_truncated_at_fit']} | {r['tokens_lost_mean']} | {r['tokens_lost_max']} |"
        )
    L.append("\n## Truncation exposure\n")
    seen = set()
    for r in out["rows"]:
        key = (out["models"][r["model"]]["sha256"], r["corpus"])
        if key in seen:
            continue
        seen.add(key)
        L.append(
            f"- {r['model']} / {r['corpus']}: {r['n_truncated_at_fit']}/{r['n_windows']} windows "
            f"exceed the {r['content_budget']}-token content budget "
            f"({r['tokens_lost_total']} tokens lost in total, max {r['tokens_lost_max']} per "
            f"window); {r['n_under_skip_min']} windows fall under the {SKIP_MIN}-token skip floor."
        )
    L.append("\n## Shift against the cutting tokenizer (Qwen3-0.6B)\n")
    L.append("| tokenizer | corpus | min delta | median delta | max delta |")
    L.append("|---|---|---|---|---|")
    seen = set()
    for r in out["rows"]:
        key = (out["models"][r["model"]]["sha256"], r["corpus"])
        if key in seen:
            continue
        seen.add(key)
        L.append(
            f"| {r['model']} | {r['corpus']} | {r['delta_vs_qwen3_min']} | "
            f"{r['delta_vs_qwen3_median']} | {r['delta_vs_qwen3_max']} |"
        )
    L.append("\n## Segmentation identity (different bytes, same plain-text split?)\n")
    L.append("| tokenizer A | tokenizer B | windows | identical token ids | differing |")
    L.append("|---|---|---|---|---|")
    for c in out["segmentation_identity"]:
        L.append(f"| {c['a']} | {c['b']} | {c['windows']} | {c['identical_ids']} | {c['differing_ids']} |")
    L.append(
        "\nEqual rows for two tokenizers with different sha256 are therefore not a copy bug: "
        "3.8-27B's tokenizer is the 3.5/3.6 vocabulary plus 7 special tokens "
        "(`<tts_pad>`, `<|audio_start|>`, …), and it segments every corpus window to identical ids."
    )
    L.append("\n## Histogram (windows, content tokens)\n")
    labels = list(out["rows"][0]["hist"].keys())
    L.append("| tokenizer | corpus | " + " | ".join(labels) + " |")
    L.append("|---|---|" + "---|" * len(labels))
    seen = set()
    for r in out["rows"]:
        key = (out["models"][r["model"]]["sha256"], r["corpus"])
        if key in seen:
            continue
        seen.add(key)
        L.append(f"| {r['model']} | {r['corpus']} | " +
                 " | ".join(str(r["hist"][k]) for k in labels) + " |")
    L.append("\n## Per-window tables\n")
    for tag in out["models"]:
        for name, _ in CORPORA:
            L.append(f"- {tag} / {name}: `{dst / f'TOK_WINDOW_LEN_{tag}_{name}.csv'}`")
    (dst / "TOK_WINDOW_LEN_all.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    for tag in out["models"]:
        m = out["models"][tag]
        print(f"{tag:<14} sha={m['sha256'][:12]} vocab={m['vocab_size']:>7,} "
              f"bos={m['bos_tokens']} budget={m['content_budget']}")
    print()
    for r in out["rows"]:
        print(f"{r['model']:<14} {r['corpus']:<9} n={r['n_windows']} "
              f"min={r['min']:<3} med={r['median']:<3} mean={r['mean']:<6} max={r['max']:<3} "
              f"trunc={r['n_truncated_at_fit']:<4} lost_mean={r['tokens_lost_mean']:<5} "
              f"lost_max={r['tokens_lost_max']}")
    print("\nwrote", dst / "TOK_WINDOW_LEN_all.json", "and .md")


if __name__ == "__main__":
    main()
