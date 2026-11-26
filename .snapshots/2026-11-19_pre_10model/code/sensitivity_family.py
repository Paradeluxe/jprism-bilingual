# -*- coding: utf-8 -*-
"""Probe-family sensitivity, two extra specifications (corrected dispatch).

R variant (family as random grouping):
  shares      (LMM)  := (1 | Probe) + (1 + PromptLanguage | ProbeFamily)
  binomial DVs (GLMM) := (1 | Probe) + (1 | ProbeFamily)
  (a three-level random *slope* in the binomial models was not estimable in practical
   time, so the GLMM version uses a random intercept for family.)

X variant (fixed moderation):
  (1 | Probe) + ProbeFamily + PromptLanguage x ProbeFamily   (fixed)

Output: results/sensitivity_family.csv + _raw.csv
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


def run(tag, block, spec, family, formula, data, dep, indep, rows):
    try:
        if family == 'LMM':
            m = PinnedLinearMixedModel()
            m.data = data
            m.dep_var, m.indep_var, m.random_var = dep, indep, ['item']
            m.fit_pinned(formula)
            conv, an, pcol, scol = m.converged(), m.anova, 'Pr(>F)', 'F value'
            m.model_r = None
        else:
            g = PinnedGeneralizedLinearMixedModel()
            g.data = data
            g.dep_var, g.indep_var, g.random_var = dep, indep, ['item']
            g.fit_pinned(formula, family='binomial')
            conv, an, pcol, scol = g.converged(), g.anova, 'Pr(>Chisq)', 'Chisq'
            g.model_r = None
        for effect, r in an.iterrows():
            rows.append(dict(tag=tag, block=block, spec=spec, effect=str(effect),
                             p=float(r[pcol]), stat=float(r[scol]), converged=conv))
    except Exception as e:
        rows.append(dict(tag=tag, block=block, spec=spec, effect='FIT_FAILED',
                         p=np.nan, stat=np.nan, converged=False))
        print('  FAILED', tag, block, spec, e, flush=True)


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
        print('###', tag, flush=True)

        for meas in MEAS:
            num = meas + '_stw'
            osub[num + '_rest'] = osub[num + '_den'] - osub[num]
            run(tag, meas, 'R', 'GLMM',
                'cbind(%s, %s_rest) ~ prompt_lang + (1 | item) + (1 | item_type)'
                % (num, num), osub, 'cbind(%s, %s_rest)' % (num, num), ['prompt_lang'], rows)
            run(tag, meas, 'X', 'GLMM',
                'cbind(%s, %s_rest) ~ prompt_lang + item_type'
                ' + prompt_lang:item_type + (1 | item)' % (num, num),
                osub, 'cbind(%s, %s_rest)' % (num, num),
                ['prompt_lang', 'item_type'], rows)

        for b in SHARES:
            dep = 'arcsin_' + b
            run(tag, 'share_' + b, 'R', 'LMM',
                '%s ~ prompt_lang * lens_lang + (1 | item)'
                ' + (1 + prompt_lang | item_type)' % dep,
                sub, dep, ['prompt_lang', 'lens_lang'], rows)
            run(tag, 'share_' + b, 'X', 'LMM',
                '%s ~ prompt_lang * lens_lang + item_type'
                ' + prompt_lang:item_type + (1 | item)' % dep,
                sub, dep, ['prompt_lang', 'lens_lang', 'item_type'], rows)

        run(tag, 'blackout_pool', 'R', 'GLMM',
            'cbind(n_boQ, rest_Q) ~ prompt_lang * lens_lang'
            ' + (1 | item) + (1 | item_type)',
            sub, 'cbind(n_boQ, rest_Q)', ['prompt_lang', 'lens_lang'], rows)
        run(tag, 'blackout_pool', 'X', 'GLMM',
            'cbind(n_boQ, rest_Q) ~ prompt_lang * lens_lang'
            ' + item_type + prompt_lang:item_type + (1 | item)',
            sub, 'cbind(n_boQ, rest_Q)',
            ['prompt_lang', 'lens_lang', 'item_type'], rows)

    S = pd.DataFrame(rows)
    S.to_csv(os.path.join(HERE, 'results', 'sensitivity_family_raw.csv'), index=False)

    main = []
    F = pd.read_csv(os.path.join(HERE, 'results', 'final_7dv_stats.csv'))
    F = F[F.dv.str.startswith('share_')]
    for _, r in F.iterrows():
        main.append(dict(tag=r.tag, block=r.dv, effect=r.effect, p_main=float(r.p)))
    B = pd.read_csv(os.path.join(HERE, 'results', 'pool_blackout_tests.csv'))
    for _, r in B.iterrows():
        main.append(dict(tag=r.tag, block='blackout_pool', effect=r.effect, p_main=float(r.p)))
    O = pd.read_csv(os.path.join(HERE, 'results', 'overlap_tests.csv'))
    O = O[(O.model == 'GLMM') & (O.variant == 'stw')]
    for _, r in O.iterrows():
        main.append(dict(tag=r.tag, block=r.measure, effect=r.effect, p_main=float(r.p)))
    M = pd.DataFrame(main)

    FOCAL = {'prompt_lang', 'lens_lang', 'prompt_lang:lens_lang'}
    J = S[S.effect.isin(FOCAL)].merge(M, on=['tag', 'block', 'effect'], how='inner')
    J = J.dropna(subset=['p'])
    for spec in ['R', 'X']:
        sub = J[J.spec == spec]
        print('\n=== spec %s: matched %d; main sig %d; spec sig %d; flips %d' % (
            spec, len(sub), int((sub.p_main < .05).sum()), int((sub.p < .05).sum()),
            int(((sub.p_main < .05) != (sub.p < .05)).sum())))
        print('  non-converged rows: %d' % int((sub.converged == False).sum()))
    X = S[(S.spec == 'X') & (S.effect == 'prompt_lang:item_type')]
    if len(X):
        print('\n=== X moderation (PromptLanguage x ProbeFamily)')
        for block in X.block.unique():
            s = X[X.block == block]
            print('  %-14s %d/%d significant' % (block, int((s.p < .05).sum()), len(s)))
    J.to_csv(os.path.join(HERE, 'results', 'sensitivity_family.csv'), index=False)
    print('\nwrote results/sensitivity_family.csv')


if __name__ == '__main__':
    main()
