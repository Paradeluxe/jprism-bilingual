# -*- coding: utf-8 -*-
"""Export the long table to per-tag R-ready CSVs (long format + DV transforms).

The stats venv deliberately has no pyarrow, so this step runs with the project venv
(which has pandas + pyarrow).  Output: data/real_check/<tag>_long.csv

Usage:
  .venv\\Scripts\\python.exe stats_mixed\\export_for_R.py
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TAGS = ["qwen3-0.6b", "qwen3-4b", "qwen3-14b", "qwen3.5-0.8b", "qwen3.5-2b",
        "gemma4-e2b", "gemma4-e4b", "gemma4-12b", "qwen3-1.7b-bnb4"]
KEEP = ["tag", "prompt_lang", "lens_lang", "item_type", "item_idx", "layer",
        "band_en", "band_zh", "band_ru", "band_other", "band_non", "blackout", "hit10"]


def main():
    df = pd.read_parquet(os.path.join(HERE, "data", "long.parquet"))
    out = os.path.join(HERE, "data", "real_check")
    os.makedirs(out, exist_ok=True)
    for tag in TAGS:
        d = df[df.tag == tag][KEEP].copy()
        d["item"] = d["item_type"] + "_" + d["item_idx"].astype(str)
        for b in ("en", "zh", "ru", "other", "non"):
            s = d["band_" + b] / 100.0
            d["arcsin_" + b] = np.arcsin(np.sqrt(s))
            d["logit_" + b] = np.log((s + 0.005) / (1 - s + 0.005))
        path = os.path.join(out, tag + "_long.csv")
        d.to_csv(path, index=False)
        print("%-18s %7d rows -> %s" % (tag, len(d), os.path.basename(path)))


if __name__ == "__main__":
    main()
