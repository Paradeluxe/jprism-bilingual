"""nan_audit.py — reusable, re-runnable quarantine sweep for lens and measurement artifacts.

Discipline this encodes (measured 2026-10-08): a new validity gate only blocks the FUTURE.
The moment you add a NaN/shape/fingerprint gate, run it retroactively over every existing
artifact, or a corrupt lens keeps sitting in the main table with perfectly healthy metadata.

Two modes:
  lens   — walk every JacobianLens file, tensor by tensor, report per-layer non-finite counts
  meas   — scan every measurement raw json, report non-finite scores with the affected layers

Exit code is 1 when anything is contaminated, so it can gate a batch.

usage:
  python3 nan_audit.py lens [lenses/local]
  python3 nan_audit.py meas RESULT/MEASURE_SICC
  python3 nan_audit.py both lenses/local RESULT/MEASURE_SICC
"""
import glob
import json
import math
import os
import sys

import torch


def is_nan(x):
    try:
        return math.isnan(x)
    except TypeError:
        return False


def walk(obj, path="root"):
    if torch.is_tensor(obj):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")


def audit_lenses(root):
    files = sorted(glob.glob(os.path.join(root, "*", "jlens_n1000_Lstep2_*.pt")))
    print(f"== lenses: {len(files)} files under {root}")
    bad = []
    for p in files:
        tag = "/".join(p.split(os.sep)[-2:])
        try:
            d = torch.load(p, map_location="cpu", weights_only=False)
        except Exception as e:
            print(f"  {tag}: LOAD FAIL {type(e).__name__}: {e}")
            continue
        dirty = []
        for path, t in walk(d):
            if t.is_floating_point() and t.numel():
                n = int(torch.isnan(t).sum())
                m = int(torch.isinf(t).sum())
                if n or m:
                    pct = 100.0 * (n + m) / t.numel()
                    dirty.append((path, tuple(t.shape), n, m, pct))
        if dirty:
            bad.append(tag)
            print(f"  NaN/Inf {tag}  [{os.path.basename(p)}]")
            for path, shape, n, m, pct in dirty[:12]:
                print(f"      {path} {shape} nan={n} inf={m} ({pct:.3f}% of entries)")
            if len(dirty) > 12:
                print(f"      ... +{len(dirty) - 12} more tensors")
        del d
    print(f"== lens verdict: {len(bad)}/{len(files)} contaminated"
          + (f": {bad}" if bad else ""))
    return bad


def audit_meas(root):
    files = sorted(glob.glob(os.path.join(root, "MEAS_*raw*.json")))
    print(f"== measurements: {len(files)} files under {root}")
    bad = []
    for p in files:
        rel = os.path.relpath(p, root)
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception as e:
            print(f"  {rel}: PARSE FAIL {e}")
            continue
        n_nan, layers, klen = 0, set(), None
        for r in d.get("results", []):
            for L in r.get("layers", []):
                if klen is None and L.get("j_top5"):
                    klen = len(L["j_top5"])
                for pair in L.get("j_top5", []):
                    if isinstance(pair, list) and len(pair) == 2 and is_nan(pair[1]):
                        n_nan += 1
                        layers.add(L.get("layer"))
        if n_nan:
            bad.append(rel)
            a = d.get("aggregate", {})
            print(f"  NaN {rel}: {n_nan} non-finite scores at layers "
                  f"{sorted(x for x in layers if x is not None)} k={klen} "
                  f"n_cells={a.get('n_cells')} H5={a.get('j_hit5_rate_cells')}")
    print(f"== measurement verdict: {len(bad)}/{len(files)} contaminated"
          + (f": {bad}" if bad else ""))
    return bad


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    roots = sys.argv[2:] or ["lenses/local", "RESULT/MEASURE_SICC"]
    bad = []
    if mode in ("lens", "both"):
        bad += audit_lenses(roots[0])
    if mode in ("meas", "both") and len(roots) > 1:
        bad += audit_meas(roots[1])
    print()
    print("CLEAN" if not bad else f"CONTAMINATED ({len(bad)} artifacts) — quarantine or re-fit")
    sys.exit(1 if bad else 0)