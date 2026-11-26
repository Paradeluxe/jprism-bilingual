# -*- coding: utf-8 -*-
"""Three-way overlap as item-level proportions (arcsine LMM).

The four overlap measures are proportions of covered positions or matching ranks
(denominator 300 for the unordered cross-language measure, 100 for the other three),
so they are modelled exactly like the shares and the blackout rates:

  arcsin(sqrt(OverlapRate)) ~ PromptLanguage * ProbeFamily + (1 | Probe)

Outputs (results/):
  overlap_lmm_tests.csv, overlap_lmm_joint.csv, overlap_lmm_pair.csv
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
MEAS = ['m1', 'm2', 'm3', 'm4']


def as_df(x):
    return pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](x))))


def main():
    set_sum_contrasts()
    r = _get_r_packages()
    d = pd.read_csv(os.path.join(HERE, 'data', 'overlap_item.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
    d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)
    for m in MEAS:
        d['ang_' + m] = np.arcsin(np.sqrt(np.clip(d[m + '_stw_rate'], 0, 1)))

    tests, joint, pair = [], [], []
    for tag in TAGS:
        sub = d[d.tag == tag].copy()
        for m in MEAS:
            mod = PinnedLinearMixedModel()
            mod.data = sub.copy()
            mod.dep_var = 'ang_' + m
            mod.indep_var = ['prompt_lang', 'item_type']
            mod.random_var = ['item']
            mod.fit_pinned('ang_%s ~ prompt_lang * item_type + (1 | item)' % m)
            for effect, row in mod.anova.iterrows():
                tests.append(dict(tag=tag, dv=m, effect=str(effect),
                                  stat=float(row['F value']), p=float(row['Pr(>F)']),
                                  converged=mod.converged()))
            jt = r['emmeans'].joint_tests(mod.model_r, by='item_type')
            for _, row in pd.DataFrame(r2p(ro.r['as.data.frame'](jt))).iterrows():
                joint.append(dict(tag=tag, dv=m, by='item_type', level=row['item_type'],
                                  term=str(row.get('model term', '')),
                                  F=float(row['F.ratio']), p=float(row['p.value'])))
            em = r['emmeans'].emmeans(mod.model_r, ro.r['as.formula']('~ prompt_lang'))
            ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
            for _, row in as_df(ct).iterrows():
                pair.append(dict(tag=tag, dv=m, contrast=str(row['contrast']),
                                 estimate=float(row['estimate']),
                                 p=float(row['p.value'])))
            mod.model_r = None
        print('fitted', tag, flush=True)

    out = os.path.join(HERE, 'results')
    T, J, P = pd.DataFrame(tests), pd.DataFrame(joint), pd.DataFrame(pair)
    T.to_csv(os.path.join(out, 'overlap_lmm_tests.csv'), index=False)
    J.to_csv(os.path.join(out, 'overlap_lmm_joint.csv'), index=False)
    P.to_csv(os.path.join(out, 'overlap_lmm_pair.csv'), index=False)

    print('\n=== three-way overlap, item-level proportion LMM ===')
    for m in MEAS:
        s = T[T.dv == m]
        row = {}
        for e in ['prompt_lang', 'item_type', 'prompt_lang:item_type']:
            g = s[s.effect == e]
            if not g.empty:
                row[e] = '%d/8' % int((g.p < .05).sum())
        pm = d[d.tag.isin(TAGS)].groupby('prompt_lang')[m + '_stw_rate'].mean() * 100
        print('%-3s %s | means EN %.1f ZH %.1f RU %.1f | conv %d/8' % (
            m, row, pm.get('en', np.nan), pm.get('zh', np.nan), pm.get('ru', np.nan),
            int(s.converged.sum() / 3)))
    for m in MEAS:
        s = P[P.dv == m]
        print('%-3s pairwise: %s' % (m, '; '.join(
            '%s %d/8' % (c, int((g.p < .05).sum())) for c, g in s.groupby('contrast'))))
    print('\nwrote results/overlap_lmm_*.csv')


if __name__ == '__main__':
    main()
