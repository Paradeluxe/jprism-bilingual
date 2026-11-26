# -*- coding: utf-8 -*-
"""Fit the top-10-only language blackout variant, then build the final significance matrix.

blackout_X at a layer:
  A  : no X token in top-10  AND  share_X < 0.50      (mirror of the paper's pool criterion)
  C  : share_X == 0                                   (X band empty)
  T  : no X token in top-10                           (readout depth only)

Item-level DV = (# layers meeting the criterion) / n_layers.
Model: binomial GLMM on cbind(n_blackout, n_layers - n_blackout) ~ prompt*lens + (1|item).
"""
import os
import sys
import time

os.environ.setdefault("R_HOME", r"C:\Program Files\R\R-4.4.1")

import numpy as np
import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from ezlmm_pinned import (PinnedGeneralizedLinearMixedModel, set_sum_contrasts)

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
LANGS = ['en', 'zh', 'ru']


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    d = d[d.tag == tag].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=['en', 'zh', 'ru'])
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=['en', 'zh', 'ru'])
    d['item'] = d['item_type'] + '_' + d['item_idx'].astype(str)
    for x in LANGS:
        d['n_boT_' + x] = np.rint(d['bo10_' + x] * d['n_layers']).astype(int)
        d['rest_T_' + x] = d['n_layers'] - d['n_boT_' + x]
    return d


def main():
    set_sum_contrasts()
    out = []
    for tag in TAGS:
        d = prep(tag)
        for x in LANGS:
            g = PinnedGeneralizedLinearMixedModel()
            g.data = d.copy()
            g.dep_var = 'cbind(n_boT_%s, rest_T_%s)' % (x, x)
            g.indep_var = ['prompt_lang', 'lens_lang']
            g.random_var = ['item']
            g.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % g.dep_var,
                         family='binomial')
            for effect, r in g.anova.iterrows():
                if str(effect).startswith('(Intercept)'):
                    continue
                out.append(dict(tag=tag, dv='boT_' + x, effect=str(effect),
                                stat='Chisq', value=float(r['Chisq']),
                                df1=float(r['Df']), p=float(r['Pr(>Chisq)'])))
            print('fitted', tag, 'boT_' + x, flush=True)
    df = pd.DataFrame(out)
    df.to_csv(os.path.join(HERE, 'results', 'item_models_boT.csv'), index=False)
    print('wrote results/item_models_boT.csv (%d tests)' % len(df))


if __name__ == '__main__':
    main()
