# -*- coding: utf-8 -*-
"""Dump the fitted-model summaries (fixed effects + VarCorr + fit info) for one tag.

This is the table ezlmm/lme4 calls .summary.  The structures are the ones used in
run_prelim.py, so the numbers match the prelim preview:
  LMM : (1 + prompt_lang + lens_lang | item) + (1 | layer)
  GLMM: (1 + prompt_lang | item) + (1 | layer)

Outputs (results/):
  summary_fixed_<tag>.csv    Estimate / SE / df / t|z / p per coefficient per DV
  summary_varcorr_<tag>.csv  variance / sd / n groups per random term per DV
  summary_text_<tag>.txt     the verbatim R summary() text for each fitted model

Usage (stats venv):
  .venv-stats\\Scripts\\python.exe -u stats_mixed\\dump_summary.py qwen3.5-0.8b
"""
import os
import sys

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)
from ezlmm.utils import _get_r_packages, r2p

BANDS = ["en", "zh", "ru", "other", "non"]


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, "data", "real_check", tag + "_long.csv"))
    d = d[d.layer != 0].copy()
    d["prompt_lang"] = pd.Categorical(d.prompt_lang, categories=["en", "zh", "ru"])
    d["lens_lang"] = pd.Categorical(d.lens_lang, categories=["en", "zh", "ru"])
    d["item"] = d["item"].astype(str)
    d["layer"] = d["layer"].astype(str)
    return d


def fixed_table(m, tag, dv, family):
    co = r2p(ro.r["coef"](ro.r["summary"](m.model_r)))
    co = pd.DataFrame(co)
    co = co.reset_index().rename(columns={"index": "term"})
    co.insert(0, "tag", tag)
    co.insert(1, "dv", dv)
    co.insert(2, "family", family)
    return co


def varcorr_table(m, tag, dv, family):
    r = _get_r_packages()
    vc = r["nlme"].VarCorr(m.model_r)
    df = r2p(ro.r["as.data.frame"](vc))
    df = pd.DataFrame(df)
    df.insert(0, "tag", tag)
    df.insert(1, "dv", dv)
    df.insert(2, "family", family)
    return df


def main(tag):
    set_sum_contrasts()
    d = prep(tag)
    r = _get_r_packages()
    fixed, vc, texts = [], [], []

    for b in BANDS:
        dv = "arcsin_" + b
        m = PinnedLinearMixedModel()
        m.data = d.copy()
        m.dep_var, m.indep_var, m.random_var = dv, ["prompt_lang", "lens_lang"], ["item", "layer"]
        f = "%s ~ prompt_lang * lens_lang + (1 + prompt_lang + lens_lang | item) + (1 | layer)" % dv
        m.fit_pinned(f)
        fixed.append(fixed_table(m, tag, b, "LMM"))
        vc.append(varcorr_table(m, tag, b, "LMM"))
        texts.append("### %s  (LMM)  singular=%s  n=%d\n%s\n" % (
            dv, not m.converged(), len(d),
            "\n".join(str(x) for x in ro.r["capture.output"](ro.r["summary"](m.model_r)))))
        print("fitted", dv, flush=True)

    g = PinnedGeneralizedLinearMixedModel()
    g.data = d.copy()
    g.dep_var, g.indep_var, g.random_var = "blackout", ["prompt_lang", "lens_lang"], ["item", "layer"]
    g.fit_pinned("blackout ~ prompt_lang * lens_lang + (1 + prompt_lang | item) + (1 | layer)",
                 family="binomial")
    fixed.append(fixed_table(g, tag, "blackout", "GLMM"))
    vc.append(varcorr_table(g, tag, "blackout", "GLMM"))
    texts.append("### blackout  (GLMM binomial)  n=%d\n%s\n" % (
        len(d), "\n".join(str(x) for x in ro.r["capture.output"](
            ro.r["summary"](g.model_r)))))
    print("fitted blackout", flush=True)

    out = os.path.join(HERE, "results")
    os.makedirs(out, exist_ok=True)
    pd.concat(fixed, ignore_index=True).to_csv(
        os.path.join(out, "summary_fixed_%s.csv" % tag), index=False)
    pd.concat(vc, ignore_index=True).to_csv(
        os.path.join(out, "summary_varcorr_%s.csv" % tag), index=False)
    with open(os.path.join(out, "summary_text_%s.txt" % tag), "w", encoding="utf-8") as fh:
        fh.write("\n".join(texts))
    print("wrote results/summary_*_%s" % tag, flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qwen3.5-0.8b")
