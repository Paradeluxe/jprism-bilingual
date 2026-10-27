#!/usr/bin/env python3
"""measure_sicc.py — batch measurement of every n1000 lens on the cluster.

Run on the SICC login node (no GPU needed: a lens apply over 4 prompts x ~12 layers is
seconds). Deployed 2026-10-01 after the local pass measured 5 of 27 lenses; the other 22
had never been measured at all, and the local machine simply does not hold those weights.

Reuses the locked scoring core by importing the reference engine's helper functions; the
protocol string and the pos=-1 primary read are carried through unchanged so cluster and
local numbers are the same measurement.
"""
from __future__ import annotations

import argparse
import contextlib
import gc
import importlib.util
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

PROJECT = Path(os.path.expanduser("~/jspace"))
OUT_DIR = PROJECT / "RESULT" / "MEASURE"
CLUSTER_OUT = PROJECT / "RESULT" / "MEASURE_SICC"

# How many ranked candidates to KEEP per (prompt, layer) in the raw JSON. The reported Hit@5 /
# Hit@10 cell-rates come from j_rank (an exact rank), so they are independent of this; this only
# sets how much of the ranking is preserved for inspection. 100 was chosen on 2026-10-07 so the
# artifact answers "what occupies rank 47" and "what displaced the answer at rank 6", not just
# the head of the list. Cost: ~1.3 MB per report at 32 layers x 4 prompts x 2 positions.
TOPK_STORE = 100

# Scoring core, imported from the locked reference so the two never drift. The reference file
# (run_pilot_0.6b_n1000.py) exists only on the local machine, so pilot_core.py here is a
# verbatim copy of its CLASSIC / honest_cues / rank_targets / topk_pairs — do not edit it.
import pilot_core as pilot  # noqa: E402
CLASSIC, POSITIONS = pilot.CLASSIC, pilot.POSITIONS
honest_cues, rank_targets, topk_pairs = pilot.honest_cues, pilot.rank_targets, pilot.topk_pairs


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M HKT", time.localtime())


def resolve_model_path(p: Path) -> str | None:
    if (p / "config.json").is_file():
        return str(p)
    return None


def gguf_file(p: Path) -> str | None:
    if not p.is_dir():
        return None
    for f in sorted(p.glob("*.gguf")):
        return f.name
    return None


def find_lenses() -> list[tuple[str, Path, str]]:
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


def load_registry():
    spec = importlib.util.spec_from_file_location("m", PROJECT / "run_fit_sicc.py")
    m = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]
    try:
        spec.loader.exec_module(m)
    except SystemExit:
        pass
    by_tag = {}
    for v in m.MODELS.values():
        by_tag[v["tag"]] = v
    return by_tag


def measure_one(tag, lens_path, corpus_tag, cfg, device, layers_wanted):
    import torch
    import transformers
    import jlens

    local = Path(cfg["local"])
    is_gguf = bool(cfg.get("loader") == "gguf")
    mp = resolve_model_path(local)
    gfile = gguf_file(local) if mp is None else None
    if mp is None and gfile is None:
        raise FileNotFoundError(f"no weights under {local}")

    # Tokenizer source. A GGUF checkpoint directory contains ONE .gguf blob and no tokenizer
    # files, so `AutoTokenizer.from_pretrained(gguf_dir, gguf_file=...)` cannot build a fast
    # tokenizer and raises "Couldn't instantiate the backend tokenizer" (measured 2026-10-02 on
    # every quantized rung). The vocab is identical to the dense sibling that produced the GGUF,
    # so take the tokenizer from there and load the WEIGHTS from the gguf. For GGUF rungs the
    # lens was fitted with exactly this tokenizer, so the token ids match by construction.
    tok_src = mp
    if mp is None and cfg.get("loader") == "gguf":
        # The tokenizer must come from the SAME model family as the gguf. Picking the first
        # dense sibling that happens to exist (measured 2026-10-03: Qwen3-0.6B for a Qwen3.5-0.8B
        # rung) loads fine and produces garbage — generation came back as "1. 2. 3. 4. 5." and
        # the model's own Hit@5 was 0.0, which looks exactly like a dead lens but is a wrong
        # vocabulary. Match on the model stem, then fall back to the registry's hf_name.
        stem = os.path.basename(str(local)).lower()      # e.g. qwen3.5-0.8b-q4km
        fam = re.match(r"(qwen3[.\-]?[0-9]*|gemma-?[0-9]*)([.\-]?[0-9]+b)?", stem)
        want = ""
        if fam:
            base = (fam.group(1) or "") + (fam.group(2) or "")
            base = base.replace("-", "").replace(".", "").lower()
            for d in sorted(Path(os.path.expanduser("~/models")).iterdir()):
                if not d.is_dir():
                    continue
                key = d.name.replace("-", "").replace(".", "").lower()
                if key.startswith(base) or key == base:
                    want = str(d)
                    break
        if not want:
            # last resort: the base-model name in the registry, minus any quant suffix
            base = cfg["hf_name"].split("/")[-1].lower()
            for d in sorted(Path(os.path.expanduser("~/models")).iterdir()):
                if d.is_dir() and d.name.lower() == base:
                    want = str(d)
                    break
        # A tokenizer-only mirror: unsloth's GGUF repos ship no tokenizer files at all, and the
        # dense 3.5 weights are not on disk either, so the vocabulary was fetched on its own
        # into ~/models/tok_<base> (22 MB, tokenizer.json + vocab.json + merges.txt).
        if (not want or not (Path(want) / "tokenizer.json").is_file()):
            b = re.sub(r"[^a-z0-9]", "", os.path.basename(str(local)).split("-q")[0].lower())
            for cand in sorted(Path(os.path.expanduser("~/models")).glob("tok_*")):
                key = re.sub(r"[^a-z0-9]", "", cand.name.replace("tok_", "").lower())
                if key.startswith(b[:8]) or b.startswith(key[:8]):
                    want = str(cand)
                    break
        tok_src = want if want and (Path(want) / "tokenizer.json").is_file() else None
    tok = transformers.AutoTokenizer.from_pretrained(
        str(tok_src), local_files_only=True) if tok_src else None
    if tok is None:
        raise FileNotFoundError(
            f"no tokenizer for {tag}: need the same-family dense model under ~/models "
            f"(gguf dir is {local}, stem {os.path.basename(str(local))})")
    dtype = torch.bfloat16
    # FP8 rungs pull their forward kernel from kernels-community/finegrained-fp8, and
    # transformers runs a publisher-trust check on it. The registry already carries
    # trust_remote_code=True for those keys (the FIT runner expands it), but the measurement
    # path never did — measured 2026-10-04: qwen3.5-0.8b-fp8 died with
    # "Kernel repository 'kernels-community/finegrained-fp8' could not verify publisher trust
    # status" on the very first lens.apply(). The switch is allow_all_kernels (NOT
    # trust_remote_code, which only covers model code and is silently ignored here).
    aak = bool(cfg.get("trust_remote_code"))
    # NOTE: _nullcontext must be bound BEFORE the branch (measured 2026-10-04): it used to be
    # assigned inside `if mp:` only, so the GGUF else-branch (mp is None) hit
    # UnboundLocalError on _nullcontext and every GGUF rung died with it — qwen3.5-2b-q4ks
    # wikitext and zhwiki both. The GGUF branch is exactly the one that never needed the
    # import, which is why it survived the refactor.
    _nullcontext = contextlib.nullcontext
    if mp:
        # The kernels-community trust check is a MODULE GLOBAL, not a from_pretrained kwarg.
        # The real switch is allow_all_hub_kernels() (flips ALLOW_ALL_KERNELS). It must wrap
        # the WHOLE measurement, not just from_pretrained: the fp8 hub kernel is loaded
        # LAZILY on the first forward call, so a context that exits after loading leaves the
        # global flipped back to False by the time the kernel is actually fetched
        # (measured 2026-10-04: with-only-load still raised the trust ValueError).
        from transformers.integrations.hub_kernels import allow_all_hub_kernels
        _kernel_ctx = allow_all_hub_kernels() if aak else _nullcontext()
        _kernel_ctx.__enter__()
        try:
            hf = transformers.AutoModelForCausalLM.from_pretrained(
                mp, dtype=dtype, local_files_only=True)
        except TypeError:
            hf = transformers.AutoModelForCausalLM.from_pretrained(
                mp, torch_dtype=dtype, local_files_only=True)
    else:
        # nullcontext().__enter__() returns None, so binding the *result* of __enter__ left
        # _kernel_ctx=None and the cleanup at the end raised
        # "AttributeError: 'NoneType' object has no attribute '__exit__'" AFTER all the
        # measurement work was done — the result was computed and then thrown away
        # (measured 2026-10-04, qwen3.5-2b-q4ks wikitext+zhwiki). Bind the context object
        # itself, exactly like the mp branch above, then enter it.
        _kernel_ctx = _nullcontext()
        _kernel_ctx.__enter__()
        hf = transformers.AutoModelForCausalLM.from_pretrained(
            str(local), gguf_file=gfile, dtype=dtype)

    if cfg.get("quantized_fit_fix"):
        sys.path.insert(0, str(PROJECT))
        import fix_awq_backend
        fix_awq_backend.force_gemm_autograd()
        if cfg.get("gptq_no_optimum"):
            fix_awq_backend.stub_optional_imports("pandas")
            fix_awq_backend.install_metadata_stubs()

    if cfg.get("loader") == "image_text":
        AutoIT = getattr(transformers, "AutoModelForImageTextToText", None)
        hf = (AutoIT or transformers.AutoModelForCausalLM).from_pretrained(
            str(mp), dtype=dtype, local_files_only=True)
    if cfg.get("device_map") is None and device == "cuda":
        hf = hf.cuda()
    elif device == "cuda":
        hf = hf.cuda()

    if cfg.get("quantized_fit_fix"):
        fix_awq_backend.swap_to_gemm(hf)
        hf.eval()
        probe = fix_awq_backend.assert_grad_works(hf, tok)
        if not probe.get("backward_ok"):
            raise RuntimeError(f"autograd probe failed: {probe}")

    model = jlens.from_hf(hf, tok)
    lens = jlens.JacobianLens.load(str(lens_path))
    have = set(lens.source_layers)
    layers = [L for L in layers_wanted if L in have] or sorted(have)
    lens_meta = repr(lens)

    results, hit5_j, hit10_j, total, model_hit5 = [], 0, 0, 0, 0
    for key, prompt, targets, _extra in CLASSIC:
        for pos in POSITIONS:
            lens_logits, model_logits, _ = lens.apply(
                model, prompt, layers=layers, positions=[pos], max_seq_len=128)
            model_top = topk_pairs(tok, model_logits[0], 5)
            model_cues = honest_cues(key, [t for t, _ in model_top])
            mr, mt = rank_targets(tok, model_logits[0], targets)
            rows = []
            for L in layers:
                # Store 100 candidates per layer, not 5. The published Hit@5/Hit@10 rates were
                # always computed from j_rank (an exact rank), so those numbers never depended
                # on k — but the raw JSON only kept the first five words, which made the top-10
                # rate unreproducible from the artifact and left no way to ask "what sits at
                # rank 47" or "which word displaced the answer at rank 6". k=100 costs ~1.3 MB
                # per report (the full ladder is ~13 MB) and is a pure top-k slice of the same
                # logit vector, so nothing numeric changes.
                jtop = topk_pairs(tok, lens_logits[L][0], TOPK_STORE)
                jcues = honest_cues(key, [t for t, _ in jtop])
                jr, jt = rank_targets(tok, lens_logits[L][0], targets)
                rows.append({"layer": L, "j_top5": jtop, "j_cues": jcues,
                             "j_rank": jr, "j_tok": jt,
                             "j_hit5": jr is not None and jr <= 5,
                             "j_hit10": jr is not None and jr <= 10,
                             "j_top5_head": jtop[:5]})
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
        gens.append({"key": key, "text": text,
                     "targets_present": [t for t in targets if t.lower() in text.lower()]})

    del model, hf, tok, lens
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    # exit the allow_all_hub_kernels scope entered at load (if it was entered)
    try:
        _kernel_ctx.__exit__(None, None, None)
    except NameError:
        pass

    return {"when": now(), "tag": tag, "lens": str(lens_path), "corpus": corpus_tag,
            "model": str(mp or local), "lens_meta": lens_meta, "layers": layers,
            "protocol": "measurement-protocol=v1-full-gurnee pilot-4", "device": device,
            "results": results, "generation": gens,
            "aggregate": {"j_hit5_rate_cells": hit5_j / total if total else None,
                          "j_hit10_rate_cells": hit10_j / total if total else None,
                          "n_cells": total,
                          "model_hit5_rate_prompts": model_hit5 / len(CLASSIC)}}


def write_md(p):
    out = CLUSTER_OUT / f"MEAS_{p['tag']}_{p['corpus']}.md"
    a = p["aggregate"]
    L = [f"# Measurement — {p['tag']} ({p['corpus']})", "",
         f"**When:** {p['when']}",
         f"**Lens:** `{p['lens']}`",
         f"**Lens meta:** {p['lens_meta']}",
         f"**Model:** `{p['model']}`",
         f"**Layers:** {p['layers']}",
         f"**Device:** {p['device']}",
         f"**Protocol:** {p['protocol']}", "",
         "## Aggregate (pos=-1, cell = prompt x layer)", "",
         f"- J Hit@5 cell-rate: **{a['j_hit5_rate_cells']}** ({a['n_cells']} cells)",
         f"- J Hit@10 cell-rate: **{a['j_hit10_rate_cells']}**",
         f"- Model final Hit@5 prompt-rate: **{a['model_hit5_rate_prompts']}**", "",
         "## Per-prompt (pos=-1)", "",
         "| prompt | model rank | J best rank | J best layer | Hit@5 layers |",
         "|---|---|---|---|---|"]
    for b in p["results"]:
        if b["pos"] != -1:
            continue
        ranks = [(r["j_rank"], r["layer"]) for r in b["layers"] if r["j_rank"] is not None]
        best = min(ranks) if ranks else (None, None)
        h5 = [r["layer"] for r in b["layers"] if r["j_hit5"]]
        L.append(f"| {b['key']} | {b['model_rank']} | {best[0]} | {best[1]} | {h5} |")
    L += ["", "## Generation (greedy, 24 new tokens)", ""]
    for g in p["generation"]:
        L.append(f"- **{g['key']}**: {g['targets_present'] or ['NO']}; `{g['text'][:160]}`")
    out.write_text("\n".join(L), encoding="utf-8")
    (CLUSTER_OUT / f"MEAS_{p['tag']}_{p['corpus']}_raw.json").write_text(
        json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def write_summary(rows):
    """Rebuild SCALE_SUMMARY from every *_raw.json on disk, not just this pass's rows.

    A previous version built the table from the rows of the current invocation only, so
    measuring a single rung (--only ...) REPLACED the whole table with that one rung
    (measured 2026-10-04: re-measuring qwen3.5-2b-q4ks dropped the 27B row that the
    previous pass had just written). The raw json files are the per-rung record, so the
    summary must be the union of them.
    """
    by_key = {}
    for r in rows:
        by_key[(r["tag"], r["corpus"])] = r
    for jf in sorted(CLUSTER_OUT.glob("MEAS_*_raw.json")):
        try:
            p = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        k = (p.get("tag"), p.get("corpus"))
        if k[0] is None or k[1] is None:
            continue
        # this pass is authoritative for anything it just measured
        by_key.setdefault(k, p)

    out = CLUSTER_OUT / "SCALE_SUMMARY.md"
    L = ["# Measured scale table — pilot-4, protocol v1-full-gurnee (SICC)", "",
         "| model | corpus | layers | J Hit@5 (cells) | J Hit@10 | model Hit@5 (prompts) |",
         "|---|---|---|---|---|---|"]
    for k in sorted(by_key, key=lambda x: (x[1], x[0])):
        r = by_key[k]
        a = r["aggregate"]
        h5, h10 = a["j_hit5_rate_cells"], a["j_hit10_rate_cells"]
        L.append(f"| {r['tag']} | {r['corpus']} | {len(r['layers'])} | "
                 f"{'—' if h5 is None else f'{h5:.3f}'} | "
                 f"{'—' if h10 is None else f'{h10:.3f}'} | "
                 f"{a['model_hit5_rate_prompts']:.3f} |")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--only", action="append", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    CLUSTER_OUT.mkdir(parents=True, exist_ok=True)
    reg = load_registry()
    lenses = find_lenses()
    todo = []
    for tag, path, corpus in lenses:
        if args.only and tag not in args.only:
            continue
        cfg = reg.get(tag)
        if cfg is None:
            todo.append((tag, path, corpus, None, "tag not in registry"))
            continue
        if resolve_model_path(Path(cfg["local"])) is None and gguf_file(Path(cfg["local"])) is None:
            todo.append((tag, path, corpus, cfg, "weights missing"))
            continue
        todo.append((tag, path, corpus, cfg, "ok"))

    print(f"lenses {len(lenses)}  runnable {sum(1 for t in todo if t[4] == 'ok')}", flush=True)
    for tag, _p, corpus, _c, why in todo:
        print(f"  {tag:24} {corpus:9} {why}", flush=True)
    if args.dry:
        return 0

    layers_wanted = list(range(2, 60, 2))
    rows = []
    for tag, path, corpus, cfg, why in todo:
        if why != "ok":
            continue
        print(f"\n=== {tag} ({corpus}) ===", flush=True)
        t0 = time.perf_counter()
        try:
            p = measure_one(tag, path, corpus, cfg, args.device, layers_wanted)
            p["elapsed_sec"] = time.perf_counter() - t0
            write_md(p)
            rows.append(p)
            a = p["aggregate"]
            print(f"  Hit@5={a['j_hit5_rate_cells']} Hit@10={a['j_hit10_rate_cells']} "
                  f"({p['elapsed_sec']:.0f}s)", flush=True)
        except Exception:
            print(traceback.format_exc(), flush=True)
            (CLUSTER_OUT / f"MEAS_{tag}_{corpus}.FAILED.md").write_text(
                f"# FAILED {tag} ({corpus})\n\n```\n{traceback.format_exc()}\n```\n",
                encoding="utf-8")
    if rows:
        print(f"\nwrote {write_summary(rows)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
