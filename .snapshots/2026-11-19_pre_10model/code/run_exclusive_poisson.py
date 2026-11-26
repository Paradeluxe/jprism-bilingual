# -*- coding: utf-8 -*-
"""Robustness model for the exclusive blackout DV: Poisson GLMM on counts with offset.

The binomial cbind model did not converge in 7/9 models (rare events -> separation).
Poisson handles zero counts naturally:  n_excl ~ offset(log(n_layers)) + prompt*lens + (1|item)
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedGeneralizedLinearMixedModel, set_sum_contrasts

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
LEVELS = ['en', 'zh', 'ru']


def main():
    set_sum_contrasts()
    d = pd.read_csv(os.path.join(HERE, 'data', 'blackout_exclusive.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item'] = d.item_type + '_' + d.item_idx.astype(str)
    d['log_layers'] = np.log(d.n_layers)

    rows = []
    for tag in TAGS:
        sub = d[d.tag == tag].copy()
        g = PinnedGeneralizedLinearMixedModel()
        g.data = sub
        g.dep_var = 'n_excl'
        g.indep_var = ['prompt_lang', 'lens_lang']
        g.random_var = ['item']
        # offset handled by adding log_layers as a fixed term with fixed coefficient
        g.fit_pinned('n_excl ~ prompt_lang * lens_lang + offset(log_layers) + (1 | item)',
                     family='poisson')
        conv = g.converged()
        for effect, row in g.anova.iterrows():
            if str(effect).startswith('(Intercept)'):
                continue
            rows.append(dict(tag=tag, effect=str(effect), Chisq=float(row['Chisq']),
                             df=float(row['Df']), p=float(row['Pr(>Chisq)']),
                             converged=conv))
        print('fitted', tag, 'converged=%s' % conv, flush=True)
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(HERE, 'results', 'exclusive_poisson_tests.csv'), index=False)
    print('\n=== Poisson GLMM, Type III ===')
    for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']:
        s = T[T.effect == e]
        print('%-24s %d/9 significant; p: %s' % (
            e, int((s.p < .05).sum()), ', '.join('%.1e' % v for v in s.p)))
    print('non-converged:', T[T.converged == False].tag.unique().tolist())


if __name__ == '__main__':
    main()
