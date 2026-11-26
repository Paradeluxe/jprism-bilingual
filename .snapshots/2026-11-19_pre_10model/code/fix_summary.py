# -*- coding: utf-8 -*-
"""Rebuild readable summary tables for qwen3.5-0.8b and produce a *valid* blackout fit.

Background: the blackout GLMM with item slopes failed to converge (negative Hessian
eigenvalue) and its coefficient table is degenerate (SE ~ 79 on every term).  The
intercept-only structure converges; it is the version to quote, with the separation
caveat documented in PLAN.md §4.2.

Outputs (results/):
  summary_fixed_named_<tag>.csv   named coefficient tables (LMM from the existing fits)
  summary_blackout_<tag>.csv      named coefficient table of the convergent blackout GLMM
"""
import os
import sys

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import numpy as np
import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ezlmm_pinned import PinnedGeneralizedLinearMixedModel, set_sum_contrasts
from ezlmm.utils import r2p

TAG = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5-0.8b"
TERMS = ["(Intercept)",
         "prompt_lang1 [en vs mean]", "prompt_lang2 [ru vs mean]",
         "lens_lang1 [en lens vs mean]", "lens_lang2 [ru lens vs mean]",
         "prompt1:lens1", "prompt2:lens1", "prompt1:lens2", "prompt2:lens2"]


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, "data", "real_check", tag + "_long.csv"))
    d = d[d.layer != 0].copy()
    d["prompt_lang"] = pd.Categorical(d.prompt_lang, categories=["en", "zh", "ru"])
    d["lens_lang"] = pd.Categorical(d.lens_lang, categories=["en", "zh", "ru"])
    d["item"] = d["item"].astype(str)
    d["layer"] = d["layer"].astype(str)
    return d


def name_lmm():
    f = pd.read_csv(os.path.join(HERE, "results", "summary_fixed_%s.csv" % TAG))
    out = []
    for dv, sub in f.groupby("dv"):
        sub = sub.reset_index(drop=True)
        if len(sub) != 9:
            continue
        out.append(pd.DataFrame({
            "tag": TAG, "dv": dv, "family": "LMM",
            "term": TERMS,
            "Estimate": sub["0"].astype(float).values,
            "SE": sub["1"].astype(float).values,
            "df": sub["2"].astype(float).values,
            "t_or_z": sub["3"].astype(float).values,
            "p": sub["4"].astype(float).values,
        }))
    out = pd.concat(out, ignore_index=True)
    out.to_csv(os.path.join(HERE, "results", "summary_fixed_named_%s.csv" % TAG), index=False)
    return out


def refit_blackout():
    set_sum_contrasts()
    d = prep(TAG)
    g = PinnedGeneralizedLinearMixedModel()
    g.data = d.copy()
    g.dep_var, g.indep_var, g.random_var = "blackout", ["prompt_lang", "lens_lang"], ["item", "layer"]
    g.fit_pinned("blackout ~ prompt_lang * lens_lang + (1 | item) + (1 | layer)",
                 family="binomial")
    sm = ro.r["summary"](g.model_r)
    co = sm.rx2("coefficients")
    vals = np.asarray(r2p(co), dtype=float)
    terms = [str(x) for x in ro.r["rownames"](co)]
    cols = [str(x) for x in ro.r["colnames"](co)]
    df = pd.DataFrame(vals, columns=cols)
    df.insert(0, "term", terms)
    df.insert(0, "family", "GLMM-binomial intercept-only")
    df.insert(0, "dv", "blackout")
    df.insert(0, "tag", TAG)
    df.to_csv(os.path.join(HERE, "results", "summary_blackout_%s.csv" % TAG), index=False)
    print("[blackout GLMM, (1|item)+(1|layer), converged=%s]" % g.converged())
    print(df.to_string(index=False))
    print("\nanova:")
    print(g.anova.round(4).to_string())
    return df


if __name__ == "__main__":
    lmm = name_lmm()
    print("[LMM coefficients, named]")
    for dv in ["en", "zh", "ru", "other", "non"]:
        sub = lmm[lmm.dv == dv]
        if len(sub):
            print("\n--", dv)
            print(sub[["term", "Estimate", "SE", "df", "t_or_z", "p"]].to_string(index=False))
    print("\n")
    refit_blackout()
