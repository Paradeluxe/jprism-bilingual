# -*- coding: utf-8 -*-
"""Pool blackout at the item level (proportion LMM), for symmetry with the other two.

  arcsin(sqrt(pool blackout rate)) ~ prompt_lang * lens_lang * item_type + (1 | item)
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedLinearMixedModel, set_sum_contrasts
from ezlmm.utils import _get_r_packages, r2p

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LEVELS = ['en', 'zh', 'ru']
FAMILIES = ['P1', 'P3', 'P4']


def as_df(x):
    return pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](x))))


def main():
    set_sum_contrasts()
    r = _get_r_packages()
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
    d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)
    d['ang_pool'] = np.arcsin(np.sqrt(np.clip(d.pool_blackout, 0, 1)))

    tests, joint, pair, cells = [], [], [], []
    for tag in TAGS:
        sub = d[d.tag == tag].copy()
        for spec, term in (('additive', 'prompt_lang * lens_lang + item_type'),
                           ('saturated', 'prompt_lang * lens_lang * item_type')):
            m = PinnedLinearMixedModel()
            m.data = sub.copy()
            m.dep_var = 'ang_pool'
            m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
            m.random_var = ['item']
            m.fit_pinned('ang_pool ~ %s + (1 | item)' % term)
            for effect, row in m.anova.iterrows():
                tests.append(dict(tag=tag, dv='blackout_pool', spec=spec,
                                  effect=str(effect), stat=float(row['F value']),
                                  p=float(row['Pr(>F)']), converged=m.converged()))
            for by, focus in [('lens_lang', 'prompt'), ('prompt_lang', 'lens'),
                              ('item_type', 'prompt')]:
                jt = r['emmeans'].joint_tests(m.model_r, by=by)
                for _, row in pd.DataFrame(r2p(ro.r['as.data.frame'](jt))).iterrows():
                    joint.append(dict(tag=tag, dv='blackout_pool', spec=spec, by=by,
                                      level=row[by], focus=focus,
                                      term=str(row.get('model term', '')),
                                      F=float(row['F.ratio']),
                                      p=float(row['p.value'])))
            specs = ro.r['as.formula']('~ prompt_lang | lens_lang')
            em = r['emmeans'].emmeans(m.model_r, specs)
            ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
            for _, row in as_df(ct).iterrows():
                pair.append(dict(tag=tag, dv='blackout_pool', spec=spec,
                                 level=row['lens_lang'], contrast=str(row['contrast']),
                                 estimate=float(row['estimate']),
                                 p=float(row['p.value'])))
            m.model_r = None
        tab = sub.groupby(['lens_lang', 'prompt_lang'])['pool_blackout'].mean()
        for (lens, prompt), v in tab.items():
            cells.append(dict(tag=tag, dv='blackout_pool', lens_lang=lens,
                              prompt_lang=prompt, mean=float(v)))
        print('fitted', tag, flush=True)

    out = os.path.join(HERE, 'results')
    pd.DataFrame(tests).to_csv(os.path.join(out, 'pool_bo_lmm_tests.csv'), index=False)
    pd.DataFrame(joint).to_csv(os.path.join(out, 'pool_bo_lmm_joint.csv'), index=False)
    pd.DataFrame(pair).to_csv(os.path.join(out, 'pool_bo_lmm_pair.csv'), index=False)
    pd.DataFrame(cells).to_csv(os.path.join(out, 'pool_bo_lmm_cells.csv'), index=False)

    T = pd.DataFrame(tests)
    print('\n=== pool blackout, item-level proportion LMM ===')
    for spec in ('additive', 'saturated'):
        s = T[T.spec == spec]
        row = {}
        for e in ['prompt_lang', 'lens_lang', 'item_type',
                  'prompt_lang:lens_lang', 'prompt_lang:item_type',
                  'lens_lang:item_type', 'prompt_lang:lens_lang:item_type']:
            g = s[s.effect == e]
            if not g.empty:
                row[e] = '%d/8' % int((g.p < .05).sum())
        print('blackout_pool  %-9s %s' % (spec, row))
    print('\nwrote results/pool_bo_lmm_*.csv')


if __name__ == '__main__':
    main()
