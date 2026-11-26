# -*- coding: utf-8 -*-
"""Run the 3x3 mixed-model screen for every core model tag.

For each tag and dependent variable:
  * band DVs (arcsine-sqrt share)  -> pinned LMM, Type III Satterthwaite F
  * blackout (0/1)                -> pinned binomial GLMM, Type III Wald chi-square
and writes one long table of tests plus a Holm-corrected significance view.

The random structures here are the *screening* structures (item slope for prompt, layer
intercept).  The maximal-by-theory structure is what PLAN.md pre-specifies for the final
analysis; measured on qwen3.5-0.8b the LMM interaction F changes <1.5% between them, so the
screen is faithful for "is this effect there", which is what this run answers.

Run with the stats venv (R_HOME and PATH must be set first):
  .venv-stats\\Scripts\\python.exe -u stats_mixed\\run_all_models.py
"""
import os
import sys
import time

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)
from ezlmm.utils import _get_r_packages  # noqa: F401  (warms the R session once)

TAGS = ["qwen3-0.6b", "qwen3-4b", "qwen3-14b", "qwen3.5-0.8b", "qwen3.5-2b",
        "gemma4-e2b", "gemma4-e4b", "gemma4-12b", "qwen3-1.7b-bnb4"]
BANDS = ["en", "zh", "ru", "other", "non"]
LMM_RANDOM = "(1 + prompt_lang | item) + (1 | layer)"
GLMM_RANDOM = "(1 + prompt_lang | item) + (1 | layer)"
OUT = os.path.join(HERE, "results", "all_models_tests.csv")


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, "data", "real_check", tag + "_long.csv"))
    d = d[d.layer != 0].copy()          # PLAN.md: layer 0 excluded
    d["prompt_lang"] = pd.Categorical(d.prompt_lang, categories=["en", "zh", "ru"])
    d["lens_lang"] = pd.Categorical(d.lens_lang, categories=["en", "zh", "ru"])
    d["item"] = d["item"].astype(str)
    d["layer"] = d["layer"].astype(str)
    return d


def rows_from_anova(tag, dv, kind, anova, secs, converged):
    out = []
    for effect, r in anova.iterrows():
        if str(effect) == "(Intercept)":
            continue
        rec = dict(tag=tag, dv=dv, family=kind, secs=round(secs, 1),
                   converged=converged, effect=str(effect))
        if "F value" in anova.columns:
            rec.update(stat="F", value=float(r["F value"]),
                       df1=float(r["NumDF"]), df2=float(r["DenDF"]),
                       p=float(r["Pr(>F)"]))
        else:
            rec.update(stat="Chisq", value=float(r["Chisq"]),
                       df1=float(r["Df"]), df2=float("nan"),
                       p=float(r["Pr(>Chisq)"]))
        out.append(rec)
    return out


def main():
    set_sum_contrasts()
    all_rows = []
    for tag in TAGS:
        d = prep(tag)
        print("\n### %s  (%d pools, %d items, %d layers)" % (
            tag, len(d), d.item.nunique(), d.layer.nunique()), flush=True)

        for b in BANDS:
            dv = "arcsin_" + b
            m = PinnedLinearMixedModel()
            m.data = d.copy()
            m.dep_var, m.indep_var, m.random_var = dv, ["prompt_lang", "lens_lang"], ["item", "layer"]
            t0 = time.time()
            m.fit_pinned("%s ~ prompt_lang * lens_lang + %s" % (dv, LMM_RANDOM))
            secs = time.time() - t0
            conv = m.converged()
            all_rows += rows_from_anova(tag, b, "LMM-arcsine", m.anova, secs, conv)
            print("  %-11s %5.1fs conv=%s | %s" % (
                dv, secs, conv, "; ".join(
                    "%s p=%.2g" % (i, r["Pr(>F)"]) for i, r in m.anova.iterrows())), flush=True)
            m.model_r = None

        g = PinnedGeneralizedLinearMixedModel()
        g.data = d.copy()
        g.dep_var, g.indep_var, g.random_var = "blackout", ["prompt_lang", "lens_lang"], ["item", "layer"]
        t0 = time.time()
        g.fit_pinned("blackout ~ prompt_lang * lens_lang + %s" % GLMM_RANDOM, family="binomial")
        secs = time.time() - t0
        conv = g.converged()
        all_rows += rows_from_anova(tag, "blackout", "GLMM-binomial", g.anova, secs, conv)
        print("  %-11s %5.1fs conv=%s | %s" % (
            "blackout", secs, conv, "; ".join(
                "%s p=%.2g" % (i, r["Pr(>Chisq)"]) for i, r in g.anova.iterrows())), flush=True)

    df = pd.DataFrame(all_rows)
    # Holm within (tag, dv) across the three effects
    df["p_holm"] = float("nan")
    for (tag, dv), idx in df.groupby(["tag", "dv"]).groups.items():
        sub = df.loc[idx].sort_values("p")
        m = len(sub)
        running = 0.0
        for rank, (i, row) in enumerate(sub.iterrows(), start=1):
            running = max(running, min(1.0, (m - rank + 1) * row["p"]))
            df.loc[i, "p_holm"] = running
    df["sig_raw"] = df.p < 0.05
    df["sig_holm"] = df.p_holm < 0.05
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False)
    print("\nwrote %s  (%d tests)" % (OUT, len(df)), flush=True)


if __name__ == "__main__":
    main()
