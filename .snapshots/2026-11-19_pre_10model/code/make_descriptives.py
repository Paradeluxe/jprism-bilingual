# -*- coding: utf-8 -*-
"""Descriptive tables for the 3x3 design (per tag x lens x prompt).

Outputs (stats_mixed/tables/):
  band_cell_means.csv     mean share of each band per cell, with SE and 95% CI
  blackout_cells.csv      blackout count / pool count and Wilson 95% CI per cell
  own_lens_share.csv      share of the band equal to the lens language, per cell

Uses the long table only; no model is fitted.  Layer 0 excluded by default (--keep-l0 to
include it); see PLAN.md §1.
"""
import argparse
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
BANDS = ["en", "zh", "ru", "other", "non"]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, max(0.0, centre - half), min(1.0, centre + half)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--long", default=os.path.join(HERE, "data", "long.parquet"))
    ap.add_argument("--out-dir", default=os.path.join(HERE, "tables"))
    ap.add_argument("--keep-l0", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    df = pd.read_parquet(args.long)
    if not args.keep_l0:
        df = df[df.layer != 0]
    df = df.copy()
    for b in BANDS:
        df["share_" + b] = df["band_" + b] / 100.0

    # ---- band shares per cell (mean over pools; SE across pools) ----
    rows = []
    for (tag, lens, prompt), d in df.groupby(["tag", "lens_lang", "prompt_lang"]):
        for b in BANDS:
            x = d["share_" + b].to_numpy()
            n = len(x)
            se = x.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
            rows.append(dict(tag=tag, lens_lang=lens, prompt_lang=prompt, band=b,
                             n_pools=n, mean_share=x.mean(), se=se,
                             lo=x.mean() - 1.96 * se, hi=x.mean() + 1.96 * se,
                             zeros=int((x == 0).sum()), ones=int((x == 1).sum())))
    band_tab = pd.DataFrame(rows)
    band_tab.to_csv(os.path.join(args.out_dir, "band_cell_means.csv"), index=False)

    # ---- blackout per cell, with Wilson CI on the pool-level binary ----
    rows = []
    for (tag, lens, prompt), d in df.groupby(["tag", "lens_lang", "prompt_lang"]):
        k, n = int(d.blackout.sum()), len(d)
        p, lo, hi = wilson(k, n)
        rows.append(dict(tag=tag, lens_lang=lens, prompt_lang=prompt,
                         blackouts=k, pools=n, rate=p, lo=lo, hi=hi))
    bo = pd.DataFrame(rows)
    bo.to_csv(os.path.join(args.out_dir, "blackout_cells.csv"), index=False)

    # ---- own-lens-language share per cell ----
    rows = []
    for (tag, lens, prompt), d in df.groupby(["tag", "lens_lang", "prompt_lang"]):
        x = d["share_" + lens].to_numpy()
        se = x.std(ddof=1) / np.sqrt(len(x))
        rows.append(dict(tag=tag, lens_lang=lens, prompt_lang=prompt,
                         n_pools=len(x), own_share_mean=x.mean(), se=se))
    own = pd.DataFrame(rows)
    own.to_csv(os.path.join(args.out_dir, "own_lens_share.csv"), index=False)

    print("rows: long=%d, cells=%d" % (len(df), band_tab.tag.nunique() * 9))
    print("\nblackout rate, mean over tags (lens x prompt):")
    print(bo.pivot_table(index="lens_lang", columns="prompt_lang", values="rate").round(3).to_string())
    print("\nowned-lens share, mean over tags (lens x prompt):")
    print(own.pivot_table(index="lens_lang", columns="prompt_lang",
                          values="own_share_mean").round(3).to_string())
    print("\nwrote", args.out_dir)


if __name__ == "__main__":
    main()
