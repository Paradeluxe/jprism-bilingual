# -*- coding: utf-8 -*-
"""Preliminary pinned mixed-model fits on the PROBE300 long table.

Fits, for one model tag:
  * 5 band DVs (arcsine-sqrt share) with a pinned LMM random structure
  * the blackout DV with a pinned binomial GLMM
and writes tidy tables (Type III tests + emmeans cell means back-transformed to %).

Run with the stats venv:
  set R_HOME=C:\\Program Files\\R\\R-4.4.1
  set PATH=C:\\Program Files\\R\\R-4.4.1\\bin\\x64;%PATH%
  .venv-stats\\Scripts\\python.exe stats_mixed\\run_prelim.py qwen3.5-0.8b
"""
import os
import sys
import time

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import rpy2.robjects as ro

from ezlmm.utils import _get_r_packages, r2p
from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)

BANDS = ["en", "zh", "ru", "other", "non"]


def _anova_rows(anova, tag, dv, model_class, secs, singular):
    rows = []
    for effect, r in anova.iterrows():
        rec = dict(tag=tag, dv=dv, model=model_class, secs=round(secs, 1), singular=singular,
                   effect=str(effect))
        for c in ("Sum Sq", "Mean Sq", "NumDF", "DenDF", "F value", "Pr(>F)",
                  "Chisq", "Df", "Pr(>Chisq)"):
            if c in anova.columns:
                rec[c.replace(">", "gt").replace("<", "lt").replace("(", "_").replace(")", "")] = \
                    r.get(c)
        rows.append(rec)
    return rows


def emmeans_cell_means(model, response=False):
    """emmeans cell means over lens x prompt; `response=True` regrids a GLMM to probability."""
    r = _get_r_packages()
    specs = ro.r["as.formula"]("~ lens_lang * prompt_lang")
    em = r["emmeans"].emmeans(model, specs)
    if response:
        em = r["emmeans"].regrid(em, "response")
    s = ro.r["summary"](em)
    df = pd.DataFrame(r2p(ro.r["as.data.frame"](s)))
    return df


def main(tag):
    src = os.path.join(HERE, "data", "real_check", tag + "_long.csv")
    d = pd.read_csv(src)
    d = d[d.layer != 0].copy()
    d["prompt_lang"] = pd.Categorical(d.prompt_lang, categories=["en", "zh", "ru"])
    d["lens_lang"] = pd.Categorical(d.lens_lang, categories=["en", "zh", "ru"])
    d["item"] = d["item"].astype(str)
    d["layer"] = d["layer"].astype(str)
    print("%s: %d pools, %d items, %d layers" % (
        tag, len(d), d.item.nunique(), d.layer.nunique()), flush=True)

    set_sum_contrasts()
    out_dir = os.path.join(HERE, "results")
    os.makedirs(out_dir, exist_ok=True)
    anova_rows, means = [], []

    for b in BANDS:
        dv = "arcsin_" + b
        m = PinnedLinearMixedModel()
        m.data = d.copy()
        m.dep_var, m.indep_var, m.random_var = dv, ["prompt_lang", "lens_lang"], ["item", "layer"]
        f = ("%s ~ prompt_lang * lens_lang + (1 + prompt_lang + lens_lang | item) + (1 | layer)" % dv)
        t0 = time.time()
        m.fit_pinned(f)
        secs = time.time() - t0
        sing = not m.converged()
        desc = "; ".join("%s F=%.1f p=%.2g" % (i, r["F value"], r["Pr(>F)"])
                         for i, r in m.anova.iterrows())
        print("  %-12s %6.1fs singular=%s | %s" % (dv, secs, sing, desc), flush=True)
        anova_rows += _anova_rows(m.anova, tag, b, "LMM-arcsine", secs, sing)
        try:
            cm = emmeans_cell_means(m.model_r)
            cm["share_pct"] = 100.0 * np.sin(cm["emmean"].astype(float)) ** 2
            cm["lo_pct"] = 100.0 * np.sin(cm["asymp.LCL"].astype(float)) ** 2
            cm["hi_pct"] = 100.0 * np.sin(cm["asymp.UCL"].astype(float)) ** 2
            cm["band"], cm["tag"] = b, tag
            means.append(cm)
        except Exception as e:
            print("    emmeans failed for %s: %s" % (dv, e), flush=True)
        m.model_r = None

    # blackout GLMM: maximal-by-theory is too slow at this n; item slopes for prompt only
    g = PinnedGeneralizedLinearMixedModel()
    g.data = d.copy()
    g.dep_var, g.indep_var, g.random_var = "blackout", ["prompt_lang", "lens_lang"], ["item", "layer"]
    f = "blackout ~ prompt_lang * lens_lang + (1 + prompt_lang | item) + (1 | layer)"
    t0 = time.time()
    g.fit_pinned(f, family="binomial")
    secs = time.time() - t0
    desc = "; ".join("%s X2=%.2f p=%.2g" % (i, r["Chisq"], r["Pr(>Chisq)"])
                     for i, r in g.anova.iterrows())
    print("  %-12s %6.1fs | %s" % ("blackout", secs, desc), flush=True)
    anova_rows += _anova_rows(g.anova, tag, "blackout", "GLMM-binomial", secs, not g.converged())
    try:
        cm = emmeans_cell_means(g.model_r, response=True)
        cm["band"], cm["tag"] = "blackout", tag
        means.append(cm)
    except Exception as e:
        print("    emmeans failed for blackout: %s" % e, flush=True)

    pd.DataFrame(anova_rows).to_csv(
        os.path.join(out_dir, "prelim_anova_%s.csv" % tag), index=False)
    if means:
        pd.concat(means, ignore_index=True).to_csv(
            os.path.join(out_dir, "prelim_cellmeans_%s.csv" % tag), index=False)
    print("wrote results/prelim_*_%s.csv" % tag, flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "qwen3.5-0.8b")
