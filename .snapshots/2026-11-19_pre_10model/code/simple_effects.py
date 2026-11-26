# -*- coding: utf-8 -*-
"""Significant terms + simple-effects analysis for one tag.

Three outputs per dependent variable:
  1. significant Type III terms only (p < .05, with Holm within DV)
  2. simple-effect JOINT tests (prompt effect at each lens level, and lens effect at each
     prompt level) via emmeans::joint_tests  -> the ANOVA definition of simple effects
  3. simple-effect PAIRWISE contrasts (bonferroni) for every by-level, via emmeans
plus ezlmm's own built-in simple-effect prose (report.write_simple_effect_lmm/glmm).

Models: same pinned structures as run_prelim.py (LMM maximal item slopes; blackout GLMM
intercept-only because the slope model is rank-deficient from complete separation).

Outputs (results/):
  sig_terms_<tag>.csv
  simple_joint_<tag>.csv
  simple_pairwise_<tag>.csv
  ezlmm_report_<tag>.txt

Usage: .venv-stats\\Scripts\\python.exe -u stats_mixed\\simple_effects.py qwen3.5-0.8b
"""
import os
import sys

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import numpy as np
import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)
from ezlmm.report import write_simple_effect_lmm, write_simple_effect_glmm
from ezlmm.utils import _get_r_packages, r2p

BANDS = ["en", "zh", "ru", "other", "non"]
TAG = sys.argv[1] if len(sys.argv) > 1 else "qwen3.5-0.8b"
OUT = os.path.join(HERE, "results")


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, "data", "real_check", tag + "_long.csv"))
    d = d[d.layer != 0].copy()
    d["prompt_lang"] = pd.Categorical(d.prompt_lang, categories=["en", "zh", "ru"])
    d["lens_lang"] = pd.Categorical(d.lens_lang, categories=["en", "zh", "ru"])
    d["item"] = d["item"].astype(str)
    d["layer"] = d["layer"].astype(str)
    return d


def em_df(em):
    return pd.DataFrame(r2p(ro.r["as.data.frame"](ro.r["summary"](em))))


def joint_tests(model, by, dv):
    """Simple-effect joint tests: the effect of the *other* factor at each level of `by`."""
    r = _get_r_packages()
    jt = r["emmeans"].joint_tests(model, by=by)
    df = pd.DataFrame(r2p(ro.r["as.data.frame"](jt)))
    df.insert(0, "dv", dv)
    df.insert(1, "by", by)
    return df


def pairwise(model, dv, by, focus, response=False):
    """Pairwise contrasts of `focus` within each level of `by`, bonferroni."""
    r = _get_r_packages()
    specs = ro.r["as.formula"]("~ %s | %s" % (focus, by))
    em = r["emmeans"].emmeans(model, specs)
    if response:
        em = r["emmeans"].regrid(em, "response")
    ct = r["emmeans"].contrast(em, "pairwise", adjust="bonferroni")
    df = pd.DataFrame(r2p(ro.r["as.data.frame"](ro.r["summary"](ct))))
    df.insert(0, "dv", dv)
    df.insert(1, "by", by)
    df.insert(2, "focus", focus)
    return df


def main():
    set_sum_contrasts()
    d = prep(TAG)
    r = _get_r_packages()
    sig, jts, pair, texts = [], [], [], []

    for b in BANDS:
        dv = "arcsin_" + b
        m = PinnedLinearMixedModel()
        m.data = d.copy()
        m.dep_var, m.indep_var, m.random_var = dv, ["prompt_lang", "lens_lang"], ["item", "layer"]
        f = "%s ~ prompt_lang * lens_lang + (1 + prompt_lang + lens_lang | item) + (1 | layer)" % dv
        m.fit_pinned(f)
        print("fitted", dv, flush=True)

        # ---- 1. significant terms (raw + Holm within DV)
        a = m.anova.copy().reset_index().rename(columns={"index": "effect"})
        statcol, pcol = "F value", "Pr(>F)"
        a = a[["effect", statcol, "NumDF", "DenDF", pcol]].copy()
        a.columns = ["effect", "stat", "df1", "df2", "p"]
        ps = sorted(a.p)
        holm = {}
        running = 0.0
        for rank, p in enumerate(ps, 1):
            running = max(running, min(1.0, (len(ps) - rank + 1) * p))
            holm[p] = running
        a["p_holm"] = a.p.map(holm)
        a.insert(0, "dv", b)
        a.insert(1, "family", "LMM-arcsine")
        sig.append(a[a.p < 0.05])

        # ---- 2. simple-effect joint tests
        try:
            j1 = joint_tests(m.model_r, "lens_lang", b)
            j1.insert(2, "tests", "prompt within lens")
            j2 = joint_tests(m.model_r, "prompt_lang", b)
            j2.insert(2, "tests", "lens within prompt")
            jts += [j1, j2]
        except Exception as e:
            print("  joint_tests failed for %s: %s" % (b, e), flush=True)

        # ---- 3. pairwise simple effects (both directions)
        try:
            pair.append(pairwise(m.model_r, b, "lens_lang", "prompt_lang"))
            pair.append(pairwise(m.model_r, b, "prompt_lang", "lens_lang"))
        except Exception as e:
            print("  pairwise failed for %s: %s" % (b, e), flush=True)

        # ---- 4. ezlmm built-in simple-effect prose
        try:
            texts.append("### %s\n%s\n" % (b, write_simple_effect_lmm(
                dv, {}, f, m.anova, m.model_r, data=d)))
        except Exception as e:
            texts.append("### %s\n[report failed: %s]\n" % (b, e))
        m.model_r = None

    # ---- blackout: intercept-only structure (complete separation makes slopes rank-deficient)
    g = PinnedGeneralizedLinearMixedModel()
    g.data = d.copy()
    g.dep_var, g.indep_var, g.random_var = "blackout", ["prompt_lang", "lens_lang"], ["item", "layer"]
    f = "blackout ~ prompt_lang * lens_lang + (1 | item) + (1 | layer)"
    g.fit_pinned(f, family="binomial")
    print("fitted blackout", flush=True)
    a = g.anova.copy().reset_index().rename(columns={"index": "effect"})
    a = a[a.effect != "(Intercept)"][["effect", "Chisq", "Df", "Pr(>Chisq)"]].copy()
    a.columns = ["effect", "stat", "df1", "p"]
    a["df2"] = np.nan
    a.insert(0, "dv", "blackout")
    a.insert(1, "family", "GLMM-binomial intercept-only")
    sig.append(a[a.p < 0.05])
    try:
        jts.append(joint_tests(g.model_r, "lens_lang", "blackout").assign(tests="prompt within lens"))
        jts.append(joint_tests(g.model_r, "prompt_lang", "blackout").assign(tests="lens within prompt"))
    except Exception as e:
        print("joint_tests blackout failed:", e, flush=True)
    try:
        pair.append(pairwise(g.model_r, "blackout", "lens_lang", "prompt_lang", response=True))
        pair.append(pairwise(g.model_r, "blackout", "prompt_lang", "lens_lang", response=True))
    except Exception as e:
        print("pairwise blackout failed:", e, flush=True)
    texts.append("### blackout (GLMM)\n%s\n" % write_simple_effect_glmm(
        "blackout", {}, f, g.anova, g.model_r, data=d))

    os.makedirs(OUT, exist_ok=True)
    pd.concat(sig, ignore_index=True).to_csv(os.path.join(OUT, "sig_terms_%s.csv" % TAG), index=False)
    pd.concat(jts, ignore_index=True).to_csv(os.path.join(OUT, "simple_joint_%s.csv" % TAG), index=False)
    if pair:
        pd.concat(pair, ignore_index=True).to_csv(
            os.path.join(OUT, "simple_pairwise_%s.csv" % TAG), index=False)
    with open(os.path.join(OUT, "ezlmm_report_%s.txt" % TAG), "w", encoding="utf-8") as fh:
        fh.write("\n".join(texts))
    print("\nwrote results/sig_terms_* simple_joint_* simple_pairwise_* ezlmm_report_*", flush=True)


if __name__ == "__main__":
    main()
