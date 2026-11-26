# -*- coding: utf-8 -*-
"""Pinned random-structure fitting for ezlmm.

Why this exists
---------------
ezlmm's own ``fit()`` starts from the maximal random structure and *prunes* it whenever a
fit emits a warning or a random-effect correlation >= .9.  Maximal structures for a 3x3
within-item design are frequently singular, so the search almost always collapses to
``(1|item) + (1|layer)``.  That is a defensible model, but it is not the model we want to
claim: with a 3-level factor the variance components differ, and for binary/GLMM data the
collapse changes the fixed-effect tests materially (measured on qwen3.5-0.8b blackout:
prompt main effect chi2 = 10.3 with item slopes vs 97.6 with intercepts only).

This module keeps ezlmm's data handling, R-call plumbing and result parsing, but pins the
random structure to a formula supplied by the analyst (no search).  It is a drop-in
replacement for ``fit()``: after ``fit_pinned()`` the object has the same attributes
(``model_r``, ``summary_r``, ``summary``, ``anova``, ``formula``) that ezlmm's reports use.

Usage
-----
    from ezlmm_pinned import PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel
    m = PinnedLinearMixedModel()
    m.read_data("long.csv")
    m.dep_var = "arcsin_en"
    m.indep_var = ["prompt_lang", "lens_lang"]
    m.random_var = ["item", "layer"]
    m.fit_pinned("arcsin_en ~ prompt_lang * lens_lang"
                 " + (1 + prompt_lang + lens_lang | item) + (1 | layer)")
    print(m.anova)

Notes
-----
* Sum contrasts must be set once per R session for Type III tests to be contrast-invariant:
  ``ro.r('options(contrasts = c("contr.sum", "contr.poly"))')`` (``set_sum_contrasts()``).
* For a binomial proportion use ``dep_var = "cbind(k, n_minus_k)"`` (literal string) and
  ``family="binomial"``; the data frame must contain columns ``k`` and ``n_minus_k``.
* ``anova``: LMM -> ``lmerTest`` Type III F (Satterthwaite by default); GLMM ->
  ``car::Anova(type=3, test="Chisq")``.  Kendall-Roger ddf is disabled above 3000 rows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ezlmm import LinearMixedModel, GeneralizedLinearMixedModel
from ezlmm.utils import _get_r_packages, r_object, r2p, p2r


def set_sum_contrasts() -> None:
    """Type III tests are only interpretable for factorial designs with sum contrasts."""
    ro = _get_r_packages()["ro"]
    ro.r('options(contrasts = c("contr.sum", "contr.poly"))')


def _format_factors(data: pd.DataFrame, factors) -> pd.DataFrame:
    """Make sure the factor columns are R factors with a stable level order.

    R's model.frame would coerce character columns, but the level order then depends on the
    data order, which changes the meaning of the sum contrasts.  An explicit pandas
    ``category`` with the declared order keeps the model matrix reproducible.
    """
    data = data.copy()
    for f in factors:
        data[f] = pd.Categorical(data[f], categories=sorted(data[f].astype(str).unique()))
    return data


class _PinnedMixin:
    """Shared pinned-fit implementation (works for both LMM and GLMM subclasses)."""

    def fit_pinned(self, formula: str, family: str | None = None,
                   optimizer: str | None = "bobyqa", maxfun: float = 2e5) -> None:
        r = _get_r_packages()
        data = _format_factors(self.data, getattr(self, "indep_var", []))
        r_data = p2r(data)
        formula_str = formula.replace("\n", " ")

        control = None
        if optimizer:
            if family is None:
                control = r["lme4"].lmerControl(
                    optimizer=optimizer, optCtrl=r["ro"].ListVector([("maxfun", maxfun)]))
            else:
                control = r["lme4"].glmerControl(
                    optimizer=optimizer, optCtrl=r["ro"].ListVector([("maxfun", maxfun)]))

        if family is None:
            if control is not None:
                model = r["lmerTest"].lmer(r["Formula"](formula_str), REML=True,
                                           data=r_data, control=control)
            else:
                model = r["lmerTest"].lmer(r["Formula"](formula_str), REML=True, data=r_data)
            summary_r = r["Matrix"].summary(model)
            self.anova = r2p(r["stats"].anova(model, type=3))
        else:
            if control is not None:
                model = r["lme4"].glmer(r["Formula"](formula_str), family=family,
                                        data=r_data, control=control)
            else:
                model = r["lme4"].glmer(r["Formula"](formula_str), family=family, data=r_data)
            summary_r = r["Matrix"].summary(model)
            self.anova = r2p(r["car"].Anova(model, type=3, test="Chisq"))

        self.model_r = model
        self.summary_r = summary_r
        self.summary = r_object(summary_r)
        self.formula = formula_str
        self.family = family

    def converged(self) -> bool:
        """True when lme4 reported no convergence message (singular fits are still 'converged')."""
        try:
            msg = self.summary["optinfo"]["conv"]["lme4"]["messages"]
        except Exception:
            return True
        return not bool(msg)


class PinnedLinearMixedModel(_PinnedMixin, LinearMixedModel):
    """Linear mixed model whose random structure is fixed by the caller."""


class PinnedGeneralizedLinearMixedModel(_PinnedMixin, GeneralizedLinearMixedModel):
    """GLMM whose random structure is fixed by the caller (family='binomial'|'poisson')."""
