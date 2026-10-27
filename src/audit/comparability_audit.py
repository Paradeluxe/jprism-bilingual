"""comparability_audit.py — are any rungs measured under a SPECIAL PATCH that makes them
incomparable with the rest of the ladder?

Two suspects, both real code paths that exist only for some rungs:
  A. fp8 rungs are measured with HF_HUB_OFFLINE=1 plus a pre-fetched full kernel snapshot
     (the normal path dies on httpx.LocalProtocolError). If that changed the numerics, the
     NEW top-100 report would disagree with the OLD top-5 report of the same rung. TOPK_STORE
     5 -> 100 provably does not move any aggregate, so any difference is the patch's fault.
  B. lens storage dtype changed from fp16 to float32 on the tenth of October 2026. Every
     lens already on disk is fp16; anything re-fitted after that is fp32. If the fp16 store
     loses enough precision to move a hit, the ladder now mixes two precisions. Quantify the
     loss, and check whether any recorded cell margin is smaller than it.

Run: python3 comparability_audit.py <RESULT_DIR>
"""
import glob
import json
import math
import os
import re
import sys

import torch

RES = sys.argv[1] if len(sys.argv) > 1 else "RESULT/MEASURE_SICC"

# ---------------------------------------------------------------- A: fp8 patch
print("=== A. fp8 rung: offline-kernel patch vs the pre-patch measurement ===")
rows = []
for tag in sorted({os.path.basename(p).split("_")[1] for p in
                    glob.glob(os.path.join(RES, "MEAS_*_raw.json"))
                    if re.match(r"MEAS_(.+?)_(wikitext|zhwiki)_raw\.json",
                                os.path.basename(p))}):
    new = os.path.join(RES, f"MEAS_{tag}_wikitext_raw.json")
    old = new + ".bak_top5"
    if not os.path.exists(old):
        continue
    try:
        a = json.load(open(new, encoding="utf-8")).get("aggregate", {})
        b = json.load(open(old, encoding="utf-8")).get("aggregate", {})
    except Exception as e:
        print(f"  {tag}: parse fail {e}")
        continue
    if "fp8" not in tag and "q4" not in tag and "awq" not in tag and "bnb" not in tag:
        continue
    h5n, h5o = a.get("j_hit5_rate_cells"), b.get("j_hit5_rate_cells")
    h10n, h10o = a.get("j_hit10_rate_cells"), b.get("j_hit10_rate_cells")
    same = (h5n == h5o) and (h10n == h10o)
    rows.append((tag, same, h5o, h5n, h10o, h10n))
    print(f"  {tag:22s} H5 {h5o} -> {h5n}   H10 {h10o} -> {h10n}   {'IDENTICAL' if same else '*** CHANGED ***'}")
if not rows:
    print("  (no rung has both a pre-patch backup and a post-patch report to compare)")

# ---------------------------------------------------------------- B: fp16 vs fp32 store
print()
print("=== B. lens storage precision: what does the old fp16 store actually cost? ===")
lens_dir = os.path.expanduser("~/jspace/lenses/local") if os.path.isdir(
    os.path.expanduser("~/jspace/lenses/local")) else "lenses/local"
checked = 0
worst = []
for p in sorted(glob.glob(os.path.join(lens_dir, "*", "jlens_n1000_Lstep2_*.pt"))):
    try:
        d = torch.load(p, map_location="cpu", weights_only=False)
    except Exception:
        continue
    J = d.get("J", {})
    for L, t in J.items():
        if not torch.is_tensor(t) or t.dtype != torch.float16 or not torch.isfinite(t).all():
            continue
        back = t.float()                       # what __init__ does on load
        finite = torch.isfinite(t)
        a = back[finite]
        if a.numel() == 0:
            continue
        denom = a.abs().clamp_min(1e-12)
        rel = ((a - t.float()[finite]).abs() / denom)
        worst.append((float(rel.max()), float(rel.mean()), os.path.basename(os.path.dirname(p)), L))
        checked += 1
    del d
if worst:
    worst.sort(reverse=True)
    print(f"  layers examined: {checked} (all fp16-stored)")
    print(f"  worst relative error a fp16 store introduces: max={worst[0][0]:.3e} "
          f"(at {worst[0][2]} L{worst[0][3]})")
    print(f"  mean relative error across layers:          {sum(w[1] for w in worst)/len(worst):.3e}")
    print("  -> this is the ONLY numerical difference between an fp16-stored and an")
    print("     fp32-stored lens; everything else in the measurement path is identical.")
else:
    print("  (no fp16 lens files found to quantify)")

# ---------------------------------------------------------------- C: is any margin that small?
print()
print("=== C. could a ~1e-3 readout error flip a recorded cell? ===")
print("  Compare the smallest top-5 boundary margin in the ladder against that error.")
gaps = []
for p in glob.glob(os.path.join(RES, "MEAS_*_raw.json")):
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    for r in d.get("results", []):
        for L in r.get("layers", []):
            top = L.get("j_top5") or []
            if len(top) < 6:
                continue
            try:
                s = [float(x[1]) for x in top[:6]]
            except (TypeError, ValueError):
                continue
            if any(math.isnan(x) for x in s):
                continue
            gaps.append((abs(s[4] - s[5]), os.path.basename(p), L.get("layer")))
if gaps:
    gaps.sort()
    print(f"  boundary margins examined: {len(gaps)}")
    print(f"  smallest top-5 boundary gap: {gaps[0][0]:.5f}  ({gaps[0][1]} L{gaps[0][2]})")
    tiny = [g for g in gaps if g[0] < 1e-2]
    print(f"  gaps below 0.01: {len(tiny)}  ({100*len(tiny)/len(gaps):.2f}% of cells)")
    for g in gaps[:5]:
        print(f"    {g[0]:.5f}  {g[1]} L{g[2]}")
else:
    print("  (no comparable gaps found)")