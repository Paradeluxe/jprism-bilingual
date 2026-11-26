# -*- coding: utf-8 -*-
"""Sensitivity: add probe family (P1/P3/P4) as a fixed covariate to the main models.

Compares the focal p values with the stored main results:
  shares      -> results/final_7dv_stats.csv
  pool black  -> results/pool_blackout_tests.csv
  overlap     -> results/overlap_tests.csv (stw, GLMM)
Output: results/sensitivity_itemtype.csv
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
SHARES = ['en', 'zh', 'ru', 'other']
MEAS = ['m1', 'm2', 'm3', 'm4']
LEVELS = ['en', 'zh', 'ru']


def main():
    set_sum_contrasts()
    item = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    item = item[item.tag.isin(TAGS)].copy()
    item['prompt_lang'] = pd.Categorical(item.prompt_lang, categories=LEVELS)
    item['lens_lang'] = pd.Categorical(item.lens_lang, categories=LEVELS)
    item['item_type'] = pd.Categorical(item.item_type, categories=['P1', 'P3', 'P4'])
    item['item'] = item.item_type.astype(str) + '_' + item.item_idx.astype(str)
    item['n_boQ'] = np.rint(item.pool_blackout * item.n_layers).astype(int)
    item['rest_Q'] = item.n_layers - item.n_boQ

    ov = pd.read_csv(os.path.join(HERE, 'data', 'overlap_item.csv'))
    ov = ov[ov.tag.isin(TAGS)].copy()
    ov['prompt_lang'] = pd.Categorical(ov.prompt_lang, categories=LEVELS)
    ov['item_type'] = pd.Categorical(ov.item_type, categories=['P1', 'P3', 'P4'])
    ov['item'] = ov.item_type.astype(str) + '_' + ov.item_idx.astype(str)

    rows = []
    for tag in TAGS:
        sub = item[item.tag == tag].copy()
        osub = ov[ov.tag == tag].copy()
        # shares
        for b in SHARES:
            m = PinnedLinearMixedModel()
            m.data = sub
            m.dep_var = 'arcsin_' + b
            m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
            m.random_var = ['item']
            m.fit_pinned('arcsin_%s ~ prompt_lang * lens_lang + item_type + (1 | item)' % b)
            for effect, r in m.anova.iterrows():
                rows.append(dict(tag=tag, block='share_' + b, effect=str(effect),
                                 p_sens=float(r['Pr(>F)'])))
            m.model_r = None
        # pool blackout
        g = PinnedGeneralizedLinearMixedModel()
        g.data = sub
        g.dep_var = 'cbind(n_boQ, rest_Q)'
        g.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
        g.random_var = ['item']
        g.fit_pinned('cbind(n_boQ, rest_Q) ~ prompt_lang * lens_lang + item_type + (1 | item)',
                     family='binomial')
        for effect, r in g.anova.iterrows():
            rows.append(dict(tag=tag, block='blackout_pool', effect=str(effect),
                             p_sens=float(r['Pr(>Chisq)'])))
        g.model_r = None
        # overlap
        for meas in MEAS:
            num = meas + '_stw'
            osub[num + '_rest'] = osub[num + '_den'] - osub[num]
            gg = PinnedGeneralizedLinearMixedModel()
            gg.data = osub
            gg.dep_var = 'cbind(%s, %s_rest)' % (num, num)
            gg.indep_var = ['prompt_lang', 'item_type']
            gg.random_var = ['item']
            gg.fit_pinned('%s ~ prompt_lang + item_type + (1 | item)' % gg.dep_var,
                          family='binomial')
            for effect, r in gg.anova.iterrows():
                rows.append(dict(tag=tag, block=meas, effect=str(effect),
                                 p_sens=float(r['Pr(>Chisq)'])))
            gg.model_r = None
        print('done', tag, flush=True)

    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(HERE, 'results', 'sensitivity_itemtype_raw.csv'), index=False)
    # stored main p values
    main = []
    F = pd.read_csv(os.path.join(HERE, 'results', 'final_7dv_stats.csv'))
    F = F[F.dv.str.startswith('share_')]
    for _, r in F.iterrows():
        main.append(dict(tag=r.tag, block=r.dv, effect=r.effect, p_main=float(r.p)))
    B = pd.read_csv(os.path.join(HERE, 'results', 'pool_blackout_tests.csv'))
    for _, r in B.iterrows():
        main.append(dict(tag=r.tag, block='blackout_pool', effect=r.effect,
                         p_main=float(r.p)))
    O = pd.read_csv(os.path.join(HERE, 'results', 'overlap_tests.csv'))
    O = O[(O.model == 'GLMM') & (O.variant == 'stw')]
    for _, r in O.iterrows():
        main.append(dict(tag=r.tag, block=r.measure, effect=r.effect, p_main=float(r.p)))
    M = pd.DataFrame(main)
    J = S.merge(M, on=['tag', 'block', 'effect'], how='inner')
    J = J[~J.effect.str.startswith('(Intercept)')]
    J.to_csv(os.path.join(HERE, 'results', 'sensitivity_itemtype.csv'), index=False)
    print('\nmatched tests:', len(J))
    print('significant: main %d, with item_type %d' % (
        int((J.p_main < .05).sum()), int((J.p_sens < .05).sum())))
    flip = J[((J.p_main < .05) != (J.p_sens < .05))]
    print('decision flips:', len(flip))
    if len(flip):
        print(flip.to_string(index=False))


if __name__ == '__main__':
    main()
