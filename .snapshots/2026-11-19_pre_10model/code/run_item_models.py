# -*- coding: utf-8 -*-
"""Fit the corrected ITEM-LEVEL models for every core tag.

Unit of observation = item x cell (2700 rows/model).  This is the design the user asked for:
  * 4 share DVs  = mean over layers of the per-layer top-100 band share (arcsine LMM)
  * blackout DVs = (# layers blacked out) / (# layers), per language, fitted as a binomial
    GLMM on cbind(n_blackout_layers, n_layers - n_blackout_layers)

Two per-language blackout criteria are fitted side by side:
  A: no X token in the top-10 AND share_X < 0.50   (mirror of the paper's pool criterion)
  C: share_X == 0 (the X band is empty)
so the user can pick one.

Output: results/item_models_tests.csv  (one row per tag x DV x effect)
"""
import os
import sys
import time

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
SHARES = ['en', 'zh', 'ru', 'other']
LANGS = ['en', 'zh', 'ru']
LMM_RANDOM = "(1 + prompt_lang + lens_lang | item)"


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    d = d[d.tag == tag].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=['en', 'zh', 'ru'])
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=['en', 'zh', 'ru'])
    d['item'] = d['item_type'] + '_' + d['item_idx'].astype(str)
    return d


def rows(tag, dv, kind, anova, secs, conv):
    out = []
    for effect, r in anova.iterrows():
        if str(effect).startswith('(Intercept)'):
            continue
        rec = dict(tag=tag, dv=dv, family=kind, secs=round(secs, 1), converged=conv,
                   effect=str(effect))
        if 'F value' in anova.columns:
            rec.update(stat='F', value=float(r['F value']), df1=float(r['NumDF']),
                       df2=float(r['DenDF']), p=float(r['Pr(>F)']))
        else:
            rec.update(stat='Chisq', value=float(r['Chisq']), df1=float(r['Df']),
                       df2=np.nan, p=float(r['Pr(>Chisq)']))
        out.append(rec)
    return out


def main():
    set_sum_contrasts()
    all_rows = []
    for tag in TAGS:
        d = prep(tag)
        print('\n### %s  %d items x cells' % (tag, len(d)), flush=True)

        for b in SHARES:
            dv = 'arcsin_' + b
            m = PinnedLinearMixedModel()
            m.data = d.copy()
            m.dep_var, m.indep_var, m.random_var = dv, ['prompt_lang', 'lens_lang'], ['item']
            t0 = time.time()
            m.fit_pinned('%s ~ prompt_lang * lens_lang + %s' % (dv, LMM_RANDOM))
            secs = time.time() - t0
            all_rows += rows(tag, 'share_' + b, 'LMM-arcsine', m.anova, secs, m.converged())
            print('  %-10s %5.1fs conv=%-5s' % (dv, secs, m.converged()), flush=True)
            m.model_r = None

        for crit in ['A', 'C']:
            for x in LANGS:
                n = 'n_bo%s_%s' % (crit, x)
                rest = 'rest_%s_%s' % (crit, x)
                dv = 'cbind(%s, %s)' % (n, rest)
                g = PinnedGeneralizedLinearMixedModel()
                g.data = d.copy()
                g.dep_var = dv
                g.indep_var = ['prompt_lang', 'lens_lang']
                g.random_var = ['item']
                t0 = time.time()
                try:
                    g.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % dv,
                                 family='binomial')
                    secs = time.time() - t0
                    all_rows += rows(tag, 'bo%s_%s' % (crit, x), 'GLMM-binomial',
                                     g.anova, secs, g.converged())
                    print('  %-12s %5.1fs conv=%s' % ('bo%s_%s' % (crit, x), secs,
                                                      g.converged()), flush=True)
                except Exception as e:
                    print('  FAILED', dv, e, flush=True)
                g.model_r = None

    df = pd.DataFrame(all_rows)
    out = os.path.join(HERE, 'results', 'item_models_tests.csv')
    df.to_csv(out, index=False)
    print('\nwrote %s (%d tests)' % (out, len(df)))


if __name__ == '__main__':
    main()
