"""Per-window token lengths of the fit corpora under each Gemma-4 tokenizer.

Why: fit_corpus/*_n1000_L128.jsonl was cut into exactly 128 tokens with the
Qwen3-0.6B tokenizer. Each model family re-tokenizes the decoded prompt text with
its OWN tokenizer, so the effective window length differs per family. Fit
truncates to max_seq_len=128 and drops rows < 18 tokens (skip_first=16), so the
distribution under the Gemma-4 tokenizer is what matters for the gemma rungs.

Gemma-4's tokenizer_config sets add_bos_token=true, so a default tokenizer call
prepends <bos>: the content budget is 127 tokens, not 128. Both columns are
reported and both id lists are kept.

Writes RESULT/TOK_WINDOW_LEN_gemma4.{json,md} plus one per-window CSV per corpus.
Reads only local files; no network.
"""
import csv
import hashlib
import json
import statistics
import sys
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent
CORPORA = [
    ("wikitext", ROOT / "fit_corpus" / "wikitext_n1000_L128.jsonl"),
    ("zhwiki", ROOT / "fit_corpus" / "zhwiki_n1000_L128.jsonl"),
]
QWEN_TOK = Path("E:/huggingface_cache/hub/models--Qwen--Qwen3-0.6B")
GEMMA_TOKS = {
    "gemma4-e2b": ROOT / "tok" / "gemma4-e2b" / "tokenizer.json",
    "gemma4-e4b": ROOT / "tok" / "gemma4-e4b" / "tokenizer.json",
    "gemma4-12b": ROOT / "tok" / "gemma4-12b" / "tokenizer.json",
}
BUDGET = 128          # run_fit_sicc.MAX_SEQ_LEN
SKIP_MIN = 18         # re-encode < 18 dropped (skip_first=16 needs seq_len > 17)
BOS = 1               # gemma-4 tokenizer_config: add_bos_token = true
BIN_EDGES = [0, 90, 100, 110, 118, 122, 126, 128, 130, 135, 140, 150, 10 ** 6]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_qwen_tokenizer() -> Path:
    direct = QWEN_TOK / "tokenizer.json"
    if direct.exists():
        return direct
    hits = sorted(QWEN_TOK.glob("snapshots/*/tokenizer.json"))
    if not hits:
        sys.exit(f"Qwen3-0.6B tokenizer.json not found under {QWEN_TOK}")
    return hits[0]


def lengths(tok: Tokenizer, texts):
    return [len(tok.encode(t, add_special_tokens=False).ids) for t in texts]


def pct(xs, q):
    s = sorted(xs)
    return s[min(len(s) - 1, int(q * len(s)))]


def summarise(name, xs, recorded):
    hist = {}
    for lo, hi in zip(BIN_EDGES, BIN_EDGES[1:]):
        label = f"[{lo},{hi})" if hi < 10 ** 6 else f"[{lo},inf)"
        hist[label] = sum(1 for v in xs if lo <= v < hi)
    over_content = [i for i, v in enumerate(xs) if v > BUDGET]
    over_bos = [i for i, v in enumerate(xs) if v + BOS > BUDGET]
    loss = [v + BOS - BUDGET for v in xs if v + BOS > BUDGET]
    return {
        "corpus": name,
        "n_windows": len(xs),
        "min": min(xs),
        "p05": pct(xs, 0.05),
        "median": int(statistics.median(xs)),
        "mean": round(statistics.fmean(xs), 2),
        "p95": pct(xs, 0.95),
        "max": max(xs),
        "n_over_budget_128_content": len(over_content),
        "over_budget_ids_content": over_content,
        "n_over_budget_128_with_bos": len(over_bos),
        "over_budget_ids_with_bos": over_bos,
        "tokens_lost_at_fit_mean": round(statistics.fmean(loss), 2) if loss else 0.0,
        "tokens_lost_at_fit_max": max(loss) if loss else 0,
        "tokens_lost_at_fit_total": sum(loss),
        "n_under_skip_min_18": sum(1 for v in xs if v < SKIP_MIN),
        "hist": hist,
        "reencode_mismatch_vs_recorded": sum(1 for a, b in zip(xs, recorded) if a != b),
    }


def main():
    qpath = find_qwen_tokenizer()
    qwen = Tokenizer.from_file(str(qpath))
    gem = Tokenizer.from_file(str(GEMMA_TOKS["gemma4-e2b"]))
    gem_sha = {k: sha256(p) for k, p in GEMMA_TOKS.items()}
    identical = len(set(gem_sha.values())) == 1

    out = {
        "budget": BUDGET,
        "skip_min": SKIP_MIN,
        "bos_tokens_prepended_by_default": BOS,
        "gemma_tokenizer_sha256": gem_sha,
        "gemma_tokenizer_identical_across_rungs": identical,
        "qwen_tokenizer": str(qpath),
        "qwen_tokenizer_sha256": sha256(qpath),
        "gemma_vocab_size": gem.get_vocab_size(),
        "corpora_sha256": {},
        "rows": [],
    }

    dst = ROOT / "RESULT"
    dst.mkdir(exist_ok=True)

    for name, path in CORPORA:
        rows = [json.loads(line) for line in path.open(encoding="utf-8")]
        out["corpora_sha256"][name] = sha256(path)
        texts = [r["text"] for r in rows]
        g = lengths(gem, texts)
        rec = [r["n_tokens_reencode"] for r in rows]
        q = lengths(qwen, texts)
        row = summarise(name, g, rec)
        row["file"] = path.name
        row["qwen_reencode_matches_recorded"] = sum(1 for a, b in zip(q, rec) if a == b)
        out["rows"].append(row)

        csv_path = dst / f"TOK_WINDOW_LEN_gemma4_{name}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "corpus", "id", "chars", "qwen_window_tokens", "qwen_reencode_tokens",
                "gemma4_tokens_content", "gemma4_tokens_with_bos",
                "delta_gemma_minus_qwen", "truncated_at_128_content",
                "truncated_at_128_with_bos",
            ])
            for i, r in enumerate(rows):
                w.writerow([
                    name, r["id"], len(r["text"]), r["n_tokens_window"], rec[i], g[i],
                    g[i] + BOS, g[i] - rec[i], int(g[i] > BUDGET), int(g[i] + BOS > BUDGET),
                ])
        row["csv"] = str(csv_path)

    (dst / "TOK_WINDOW_LEN_gemma4.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    L = []
    L.append("# Gemma-4 fit-corpus per-window token lengths\n")
    L.append(
        "The fit corpora were cut as exactly 128 tokens with the Qwen3-0.6B tokenizer "
        f"(`{out['qwen_tokenizer_sha256'][:8]}`) and are re-tokenized per family at fit time. "
        "Gemma-4 E2B / E4B / 12B ship **byte-identical** tokenizers "
        f"(`{gem_sha['gemma4-e2b']}`, vocab {out['gemma_vocab_size']:,}), so one set of lengths "
        "covers all three rungs.\n"
    )
    L.append(
        f"Fit truncates to `max_seq_len={BUDGET}` and drops rows < {SKIP_MIN} tokens "
        f"(skip_first=16). The fit path is `jlens/hf.py:157-160` on SICC — "
        "`self.tokenizer(text, return_tensors=\"pt\", truncation=True, max_length=128)` with no "
        "`add_special_tokens` argument, i.e. the transformers default `True`. Gemma-4's "
        f"`tokenizer_config.json` sets `add_bos_token: true`, so one `<bos>` is prepended and the "
        f"effective content budget is **{BUDGET - BOS} tokens**. Lengths below are content tokens "
        "(`add_special_tokens=False`); the with-BOS columns are the operative ones.\n"
    )
    L.append("| corpus | n | min | p05 | median | mean | p95 | max | >128 content | >127 (+BOS) | <18 dropped |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in out["rows"]:
        L.append(
            f"| {r['corpus']} | {r['n_windows']} | {r['min']} | {r['p05']} | {r['median']} | "
            f"{r['mean']} | {r['p95']} | {r['max']} | {r['n_over_budget_128_content']} | "
            f"{r['n_over_budget_128_with_bos']} | {r['n_under_skip_min_18']} |"
        )
    L.append("\n## Histogram (windows, content tokens)\n")
    labels = list(out["rows"][0]["hist"].keys())
    L.append("| corpus | " + " | ".join(labels) + " |")
    L.append("|---|" + "---|" * len(labels))
    for r in out["rows"]:
        L.append(f"| {r['corpus']} | " + " | ".join(str(r["hist"][k]) for k in labels) + " |")
    L.append("\n## Round-trip checks\n")
    for r in out["rows"]:
        L.append(
            f"- {r['corpus']}: Qwen re-encode reproduces the recorded `n_tokens_reencode` on "
            f"{r['qwen_reencode_matches_recorded']}/{r['n_windows']} rows "
            f"(gemma-vs-recorded mismatches: {r['reencode_mismatch_vs_recorded']})."
        )
    L.append("\n## Per-window tables\n")
    for r in out["rows"]:
        L.append(f"- {r['corpus']}: `{r['csv']}`")
    L.append("\nTruncation exposure at fit:")
    for r in out["rows"]:
        L.append(
            f"- {r['corpus']}: {r['n_over_budget_128_content']} windows exceed 128 content tokens; "
            f"**{r['n_over_budget_128_with_bos']} exceed 127 and are truncated at fit** "
            f"(mean {r['tokens_lost_at_fit_mean']} tokens lost per affected window, max "
            f"{r['tokens_lost_at_fit_max']}, {r['tokens_lost_at_fit_total']} tokens total). "
            "Full id lists are in the JSON under `over_budget_ids_content` / "
            "`over_budget_ids_with_bos`."
        )
    L.append(
        "\nQwen3-0.6B sets `add_bos_token: false`, so the same fit path gives it the full 128 "
        "content tokens; only the Gemma rungs lose the tail. This is a per-family re-tokenization "
        "difference, not a corpus difference: both corpora were cut to exactly 128 Qwen tokens."
    )
    (dst / "TOK_WINDOW_LEN_gemma4.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(json.dumps({r["corpus"]: {k: r[k] for k in (
        "n_windows", "min", "p05", "median", "mean", "p95", "max",
        "n_over_budget_128_content", "n_over_budget_128_with_bos", "n_under_skip_min_18",
        "qwen_reencode_matches_recorded", "hist")} for r in out["rows"]},
        ensure_ascii=False, indent=2))
    print("gemma tokenizers identical across rungs:", identical,
          "| vocab:", out["gemma_vocab_size"], "| sha256:", gem_sha["gemma4-e2b"])
    for p in [dst / "TOK_WINDOW_LEN_gemma4.json", dst / "TOK_WINDOW_LEN_gemma4.md",
              *[Path(r["csv"]) for r in out["rows"]]]:
        print("wrote", p)


if __name__ == "__main__":
    main()
