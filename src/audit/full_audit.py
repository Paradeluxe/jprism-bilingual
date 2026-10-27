#!/usr/bin/env python3
"""full_audit.py — the four-state audit, done properly and re-runnable.

Every earlier count in this project was produced by tag extraction like
`basename.split("_")[1]`, which silently mis-parses any tag containing an underscore
(`qwen3-0.6b_q8_0` -> `qwen3`) and therefore reported both phantom gaps and phantom
completeness. Here the (tag, corpus) pair is taken from the FILENAME by regex, and the
lens/measurement/card states are joined per cell rather than per file prefix.

Four states, never collapsed:
  1 lens   the lens file exists (a .smoke / .nan_quarantine / .dirty-* file does not count)
  2 meas   a measurement raw of the right size exists for that lens
  3 record a FIT_CARD naming that tag and corpus
  4 usable the lens is not quarantined and the measurement has no non-finite scores

Run:  python3 full_audit.py [lenses_dir] [measure_dir]
"""
import glob
import json
import math
import os
import re
import sys

LENS = sys.argv[1] if len(sys.argv) > 1 else "lenses/local"
MEAS = sys.argv[2] if len(sys.argv) > 2 else "RESULT/MEASURE_SICC"

LENS_RE = re.compile(r"lenses/local/([^/]+)/jlens_n1000_Lstep2_(wikitext|zhwiki)\.pt$")
MEAS_RE = re.compile(r"MEAS_(.+?)_(wikitext|zhwiki)_raw\.json$")
CORPORA = ("wikitext", "zhwiki")


def norm(p):
    return p.replace("\\", "/")


def load_lenses():
    out = {}
    for p in glob.glob(os.path.join(LENS, "*", "jlens_n1000_Lstep2_*.pt")):
        m = LENS_RE.search(norm(p))
        if m:
            out[(m.group(1), m.group(2))] = norm(p)
    return out


def load_measurements():
    out, bad_nan, small = {}, {}, []
    for p in glob.glob(os.path.join(MEAS, "MEAS_*_raw*.json")):
        b = os.path.basename(p)
        if re.search(r"\.(bak|h800|h80001|h800b|a100|recheck|hold|pre_gm|canon)", b):
            continue                      # archived/superseded copies are not the canonical
        m = MEAS_RE.search(b)
        if not m:
            continue
        key = (m.group(1), m.group(2))
        sz = os.path.getsize(p)
        if sz < 400000:
            small.append((b, sz))
            continue
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        nan = 0
        for r in d.get("results", []):
            for L in r.get("layers", []):
                for pair in L.get("j_top5", []):
                    if isinstance(pair, list) and len(pair) == 2:
                        v = pair[1]
                        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                            nan += 1
        out[key] = (p, nan)
        if nan:
            bad_nan[key] = nan
    return out, bad_nan, small


def cards():
    have = set()
    for p in glob.glob("FIT_CARD*.md") + glob.glob("RESULT/**/FIT_CARD*.md", recursive=True):
        b = os.path.basename(p)
        m = re.match(r"FIT_CARD_(.+?)(?:\.(wikitext|zhwiki))?\.md$", b)
        if not m:
            continue
        tag = m.group(1)
        corp = m.group(2) or "any"
        have.add((tag, corp))
    return have


def main():
    lenses = load_lenses()
    meas, bad_nan, small = load_measurements()
    have_cards = cards()

    tags = sorted({t for t, c in lenses} | {t for t, c in meas})
    print(f"lenses (canonical): {len(lenses)}   measurements: {len(meas)}   tags: {len(tags)}")
    if small:
        print(f"  NOTE: {len(small)} measurement file(s) below 400K were treated as NOT measured")
        for b, s in small[:6]:
            print(f"    {b}  {s}B")
    print()
    hdr = f"{'tag':<26}{'corpus':<9}{'lens':>6}{'meas':>6}{'card':>6}{'status':>10}"
    print(hdr)
    print("-" * len(hdr))
    gaps = []
    for t in tags:
        for c in CORPORA:
            has_l = (t, c) in lenses
            has_m = (t, c) in meas
            has_c = (t, c) in have_cards or (t, "any") in have_cards
            if not has_l and not has_m:
                continue
            if has_l and has_m:
                status = "OK"
            elif has_l and not has_m:
                status = "NEEDS-MEAS"
                gaps.append((t, c, "lens without measurement"))
            elif has_m and not has_l:
                status = "ORPHAN-MEAS"
                gaps.append((t, c, "measurement without lens"))
            else:
                status = "?"
            print(f"{t:<26}{c:<9}{'Y' if has_l else '-':>6}{'Y' if has_m else '-':>6}"
                  f"{'Y' if has_c else '-':>6}{status:>10}")
    print()
    if bad_nan:
        print(f"NON-FINITE SCORES FOUND in {len(bad_nan)} measurement(s):")
        for (t, c), n in bad_nan.items():
            print(f"  {t} {c}: {n} non-finite scores")
    else:
        print("no non-finite scores in any canonical measurement")
    quarantined = sorted(glob.glob(os.path.join(LENS, "*", "*.nan_quarantine")))
    if quarantined:
        print(f"quarantined lenses (kept as evidence): {len(quarantined)}")
        for q in quarantined:
            print(f"  {norm(q)}")
    print()
    if gaps:
        print(f"GAPS: {len(gaps)}")
        for t, c, why in gaps:
            print(f"  {t} {c}: {why}")
    else:
        print("GAPS: none — every canonical lens has a measurement of the right size")

    # RUNG-level verdict. This is the check that was missing when a report called a rung
    # done because its English lens existed: a rung is COMPLETE only when BOTH corpora are OK,
    # and PARTIAL otherwise, naming the missing side. Reporting per-cell OK rows and then
    # calling the rung done is how a one-language rung gets reported as a finished one.
    print()
    print("=== RUNG-LEVEL VERDICT (both corpora required) ===")
    states = {}
    for t in tags:
        per = {}
        for c in CORPORA:
            if (t, c) in lenses and (t, c) in meas:
                per[c] = "OK"
            elif (t, c) in lenses:
                per[c] = "LENS-ONLY"
            elif (t, c) in meas:
                per[c] = "MEAS-ONLY"
            else:
                per[c] = "NONE"
        states[t] = per
    full = [t for t, p in states.items() if all(v == "OK" for v in p.values())]
    part = {t: p for t, p in states.items() if not all(v == "OK" for v in p.values())}
    print(f"  COMPLETE (both corpora measured): {len(full)} rungs")
    for t in sorted(full):
        print(f"     {t}")
    print(f"  PARTIAL: {len(part)} rungs")
    for t in sorted(part):
        missing = [c for c, v in states[t].items() if v != "OK"]
        print(f"     {t}: missing {', '.join(missing)} ({states[t][missing[0]]})")


if __name__ == "__main__":
    main()