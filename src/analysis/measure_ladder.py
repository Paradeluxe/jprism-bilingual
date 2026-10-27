# -*- coding: utf-8 -*-
"""measure_ladder.py — run the locked pilot-4 measurement over every lens we have.

Why this file exists: 27 English + 2 Chinese n1000 lenses were fitted between 2026-09-25 and
2026-10-01, and NOT ONE of them had ever been measured. MEASUREMENTS.md locks the protocol
(v1-full-gurnee: Hit@5 / Hit@10 over prompt x layer cells, primary read pos=-1, top-k readout,
european!=euro guard); the four pilot reports that DO exist cover 0.6B / 1.7B / 3.5-0.8B /
3.5-2B only. A lens without a hit-rate is a file, not a result.

This does NOT re-implement the measurement. run_pilot_0.6b_n1000.py is the reference engine and
its scoring is subtle (rank_targets' euro/european exclusion, honest_cues, the pos=-1 primary
convention), so this file imports that logic verbatim and only adds: a model/lens registry, a
device switch, a batch loop, and a cross-model summary table.

Device: the user's 3050 stays free by default. --device cpu is the default here because a
lens apply on 4 prompts x ~12 layers is seconds of work and the desktop GPU is spoken for.

Usage:
  python measure_ladder.py                      # every lens with local weights, on CPU
  python measure_ladder.py --only qwen3-0.6b    # one
  python measure_ladder.py --device cuda        # use the local GPU
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("HF_HOME", r"E:\huggingface_cache")
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", r"E:\huggingface_cache\hub")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

PROJECT = Path(r"E:\hermes_playground\jspace-qwen-exp")
OUT_DIR = PROJECT / "RESULT" / "MEASURE"
HUB = Path(r"E:\huggingface_cache\hub")

# lens tag -> (local model dir under the HF hub, label). Only entries whose weights are present
# can be measured here; anything larger lives on SICC and is reported as such, not faked.
MODELS = {
    "qwen3-0.6b":       (HUB / "models--Qwen--Qwen3-0.6B",  "Qwen3-0.6B"),
    "qwen3.5-0.8b":     (HUB / "models--Qwen--Qwen3.5-0.8B", "Qwen3.5-0.8B"),
    "qwen3.5-2b":       (HUB / "models--Qwen--Qwen3.5-2B",  "Qwen3.5-2B"),
    "qwen3.5-4b":       (HUB / "models--Qwen--Qwen3.5-4B",  "Qwen3.5-4B"),
    "qwen3-4b":         (HUB / "models--Qwen--Qwen3-4B",    "Qwen3-4B"),
    "qwen3-8b":         (HUB / "models--Qwen--Qwen3-8B",    "Qwen3-8B"),
    "qwen3-1.7b":       (HUB / "models--Qwen--Qwen3-1.7B",  "Qwen3-1.7B"),
}

# The scoring core, imported from the reference engine so the two can never drift.
# The reference module ends with `sys.exit(main())` under `if __name__ == "__main__"`, and
# importlib sets __name__ to the alias, so the guard does not fire — but its module-level
# side effects (printing "START pilot ...") do, and in the 0.6B file `raise SystemExit` in
# the except branch would kill THIS script. Load it in an isolated namespace and swallow
# SystemExit so a failing reference import cannot take the batch down with it.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "pilot06", PROJECT / "run_pilot_0.6b_n1000.py")
pilot = importlib.util.module_from_spec(_spec)
try:
    _spec.loader.exec_module(pilot)
except SystemExit:
    print("note: reference engine exited during import; using whatever it defined", flush=True)
CLASSIC = pilot.CLASSIC
POSITIONS = pilot.POSITIONS
honest_cues = pilot.honest_cues
rank_targets = pilot.rank_targets
topk_pairs = pilot.topk_pairs

CORPUS_TAGS = {"wikitext": "wikitext", "zhwiki": "zhwiki"}


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M HKT", time.localtime())


def resolve_model_path(p: Path) -> str | None:
    if (p / "config.json").is_file():
        return str(p)
    snap = p / "snapshots"
    if snap.is_dir():
        for d in sorted(snap.iterdir()):
            if (d / "config.json").is_file():
                return str(d)
    return None


def find_lenses() -> list[tuple[str, Path, str]]:
    """(tag, path, corpus_tag) for every n1000 lens on disk."""
    out = []
    root = PROJECT / "lenses" / "local"
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        for f in sorted(d.glob("jlens_n1000_Lstep2_*.pt")):
            m = re.match(r"jlens_n1000_Lstep2_(wikitext|zhwiki)\.pt$", f.name)
            if m:
                out.append((d.name, f, m.group(1)))
    return out


def measure_one(tag: str, lens_path: Path, corpus_tag: str, model_dir: Path,
                device: str, layers_wanted: list[int]) -> dict:
    import torch
    import transformers
    import jlens

    mp = resolve_model_path(model_dir)
    if mp is None:
        raise FileNotFoundError(f"no config.json under {model_dir}")

    tok = transformers.AutoTokenizer.from_pretrained(mp, local_files_only=True)
    dtype = torch.bfloat16 if device == "cpu" else torch.float16
    try:
        hf = transformers.AutoModelForCausalLM.from_pretrained(
            mp, dtype=dtype, local_files_only=True)
    except TypeError:
        hf = transformers.AutoModelForCausalLM.from_pretrained(
            mp, torch_dtype=dtype, local_files_only=True)
    if device == "cuda":
        hf = hf.cuda()
    model = jlens.from_hf(hf, tok)
    lens = jlens.JacobianLens.load(str(lens_path))

    have = set(lens.source_layers)
    layers = [L for L in layers_wanted if L in have] or sorted(have)

    results, hit5_j, hit10_j, total = [], 0, 0, 0
    model_hit5 = 0
    for key, prompt, targets, _extra in CLASSIC:
        for pos in POSITIONS:
            lens_logits, model_logits, _ = lens.apply(
                model, prompt, layers=layers, positions=[pos], max_seq_len=128)
            model_top = topk_pairs(tok, model_logits[0], 5)
            model_cues = honest_cues(key, [t for t, _ in model_top])
            mr, mt = rank_targets(tok, model_logits[0], targets)
            rows = []
            for L in layers:
                jtop = topk_pairs(tok, lens_logits[L][0], 5)
                jcues = honest_cues(key, [t for t, _ in jtop])
                jr, jt = rank_targets(tok, lens_logits[L][0], targets)
                rows.append({"layer": L, "j_top5": jtop, "j_cues": jcues,
                             "j_rank": jr, "j_tok": jt,
                             "j_hit5": jr is not None and jr <= 5,
                             "j_hit10": jr is not None and jr <= 10})
                if pos == -1:
                    total += 1
                    hit5_j += int(jr is not None and jr <= 5)
                    hit10_j += int(jr is not None and jr <= 10)
            if pos == -1:
                model_hit5 += int(mr is not None and mr <= 5)
            results.append({"key": key, "prompt": prompt, "pos": pos, "targets": targets,
                            "model_top5": model_top, "model_cues": model_cues,
                            "model_rank": mr, "model_tok": mt, "layers": rows})

    gens = []
    for key, prompt, targets, _ in CLASSIC:
        ids = tok(prompt, return_tensors="pt").to(hf.device)
        with torch.no_grad():
            out = hf.generate(**ids, max_new_tokens=24, do_sample=False)
        text = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
        present = [t for t in targets if t.lower() in text.lower()]
        gens.append({"key": key, "text": text, "targets_present": present})

    # Capture the repr BEFORE the `del` below: `del model, hf, tok, lens` frees the name
    # `lens` for the rest of the function, so any later reference to it (including inside the
    # returned dict) raises UnboundLocalError.
    lens_meta = repr(lens)

    del model, hf, tok, lens
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

    return {
        "when": now(), "tag": tag, "lens": str(lens_path), "corpus": corpus_tag,
        "model": str(mp), "lens_meta": lens_meta, "layers": layers,
        "protocol": "measurement-protocol=v1-full-gurnee pilot-4",
        "device": device,
        "results": results, "generation": gens,
        "aggregate": {
            "j_hit5_rate_cells": hit5_j / total if total else None,
            "j_hit10_rate_cells": hit10_j / total if total else None,
            "n_cells": total,
            "model_hit5_rate_prompts": model_hit5 / len(CLASSIC),
        },
    }


def write_md(p: dict) -> Path:
    tag, corpus = p["tag"], p["corpus"]
    name = f"MEAS_{tag}_{corpus}.md"
    out = OUT_DIR / name
    agg = p["aggregate"]
    L = []
    L.append(f"# Measurement — {tag} ({corpus})")
    L.append("")
    L.append(f"**When:** {p['when']}")
    L.append(f"**Lens:** `{p['lens']}`")
    L.append(f"**Lens meta:** {p['lens_meta']}")
    L.append(f"**Model:** `{p['model']}`")
    L.append(f"**Layers:** {p['layers']}")
    L.append(f"**Device:** {p['device']}")
    L.append(f"**Protocol:** {p['protocol']}")
    L.append("")
    L.append("## Aggregate (pos=-1, cell = prompt x layer)")
    L.append("")
    L.append(f"- J Hit@5 cell-rate: **{agg['j_hit5_rate_cells']}** ({agg['n_cells']} cells)")
    L.append(f"- J Hit@10 cell-rate: **{agg['j_hit10_rate_cells']}**")
    L.append(f"- Model final Hit@5 prompt-rate: **{agg['model_hit5_rate_prompts']}**")
    L.append("")
    L.append("## Per-prompt (pos=-1)")
    L.append("")
    L.append("| prompt | model rank | J best rank | J best layer | Hit@5 layers |")
    L.append("|---|---|---|---|---|")
    for b in p["results"]:
        if b["pos"] != -1:
            continue
        ranks = [(r["j_rank"], r["layer"]) for r in b["layers"] if r["j_rank"] is not None]
        best = min(ranks) if ranks else (None, None)
        h5 = [r["layer"] for r in b["layers"] if r["j_hit5"]]
        L.append(f"| {b['key']} | {b['model_rank']} | {best[0]} | {best[1]} | {h5} |")
    L.append("")
    L.append("## Generation (greedy, 24 new tokens)")
    L.append("")
    for g in p["generation"]:
        L.append(f"- **{g['key']}**: {g['targets_present'] or ['NO']}; `{g['text'][:160]}`")
    L.append("")
    out.write_text("\n".join(L), encoding="utf-8")
    (OUT_DIR / f"MEAS_{tag}_{corpus}_raw.json").write_text(
        json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def write_summary(rows: list[dict]) -> Path:
    out = OUT_DIR / "SCALE_SUMMARY.md"
    L = ["# Measured scale table — pilot-4, protocol v1-full-gurnee", "",
         "| model | corpus | layers | J Hit@5 (cells) | J Hit@10 | model Hit@5 (prompts) |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        a = r["aggregate"]
        h5 = a["j_hit5_rate_cells"]
        h10 = a["j_hit10_rate_cells"]
        L.append(
            f"| {r['tag']} | {r['corpus']} | {len(r['layers'])} | "
            f"{'—' if h5 is None else f'{h5:.3f}'} | "
            f"{'—' if h10 is None else f'{h10:.3f}'} | "
            f"{a['model_hit5_rate_prompts']:.3f} |")
    L.append("")
    L.append("Hit@5/Hit@10 are cell-rates over prompt x layer at pos=-1 (the locked primary read).")
    L.append("model Hit@5 is a prompt-rate over the 4 classic prompts. Both are the reference")
    L.append("engine's own definitions, unchanged.")
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=None)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--limit", type=int, default=4, help="how many source layers to read")
    ap.add_argument("--dry", action="store_true", help="list what would run")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lenses = find_lenses()
    todo = []
    for tag, path, corpus in lenses:
        if args.only and tag not in args.only:
            continue
        if tag not in MODELS:
            todo.append((tag, path, corpus, None, "no local weights in MODELS"))
            continue
        md = MODELS[tag][0]
        if resolve_model_path(md) is None:
            todo.append((tag, path, corpus, None, f"weights incomplete: {md.name}"))
            continue
        todo.append((tag, path, corpus, md, "ok"))

    print(f"lenses found: {len(lenses)}   runnable: "
          f"{sum(1 for t in todo if t[4] == 'ok')}", flush=True)
    for tag, path, corpus, _md, why in todo:
        print(f"  {tag:24} {corpus:9} {why}", flush=True)
    if args.dry:
        return 0

    # Read EVERY source layer the lens was fitted with. This used to be capped at 12, which
    # silently truncated the late layers: qwen3-8b has 18 source layers and scored Hit@5=0.0
    # locally vs 0.191 on the cluster with all 18 — the answer-bearing layers were cut off.
    # A cell-rate over a truncated layer set is not comparable to one over the full set.
    layers_wanted = list(range(0, 64, 2))
    rows = []
    for tag, path, corpus, md, why in todo:
        if why != "ok":
            continue
        print(f"\n=== {tag} ({corpus}) ===", flush=True)
        t0 = time.perf_counter()
        try:
            p = measure_one(tag, path, corpus, md, args.device, layers_wanted)
            p["elapsed_sec"] = time.perf_counter() - t0
            w = write_md(p)
            rows.append(p)
            a = p["aggregate"]
            print(f"  Hit@5={a['j_hit5_rate_cells']} Hit@10={a['j_hit10_rate_cells']} "
                  f"({p['elapsed_sec']:.0f}s) -> {w.name}", flush=True)
        except Exception:
            print(traceback.format_exc(), flush=True)
            (OUT_DIR / f"MEAS_{tag}_{corpus}.FAILED.md").write_text(
                f"# FAILED {tag} ({corpus})\n\n```\n{traceback.format_exc()}\n```\n",
                encoding="utf-8")

    if rows:
        s = write_summary(rows)
        print(f"\nwrote {s}", flush=True)
    return 0


if __name__ == "__main__":
    # Was `sys.exit(0)` — which made every run a silent no-op with exit code 0, so the batch
    # looked like it "ran" and produced nothing. Always call main() and propagate its code.
    sys.exit(main())
