# -*- coding: utf-8 -*-
"""Fit the 3x3 item-level model for the EXCLUSIVE blackout DV.

DV: per (tag, prompt, lens, item) = (# layers where that lens is the only blacked-out one)
    / (# layers).  Response: cbind(n_excl, n_layers - n_excl), binomial GLMM,
    fixed prompt*lens, random (1|item).
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedGeneralizedLinearMixedModel, set_sum_contrasts
from ezlmm.utils import _get_r_packages, r2p

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
    d['rest'] = d.n_layers - d.n_excl
    print('rows %d, mean exclusive rate %.4f' % (len(d), d.rate.mean()))

    r = _get_r_packages()
    tests, joint, pair, cells = [], [], [], []
    for tag in TAGS:
        sub = d[d.tag == tag].copy()
        g = PinnedGeneralizedLinearMixedModel()
        g.data = sub
        g.dep_var = 'cbind(n_excl, rest)'
        g.indep_var = ['prompt_lang', 'lens_lang']
        g.random_var = ['item']
        g.fit_pinned('cbind(n_excl, rest) ~ prompt_lang * lens_lang + (1 | item)',
                     family='binomial')
        conv = g.converged()
        for effect, row in g.anova.iterrows():
            if str(effect).startswith('(Intercept)'):
                continue
            tests.append(dict(tag=tag, effect=str(effect), Chisq=float(row['Chisq']),
                              df=float(row['Df']), p=float(row['Pr(>Chisq)']), converged=conv))
        for (lens, prompt), s in sub.groupby(['lens_lang', 'prompt_lang'], observed=True):
            cells.append(dict(tag=tag, lens_lang=lens, prompt_lang=prompt,
                              rate=s.n_excl.sum() / s.n_layers.sum()))
        for by in ['lens_lang', 'prompt_lang']:
            jt = pd.DataFrame(r2p(ro.r['as.data.frame'](
                r['emmeans'].joint_tests(g.model_r, by=by))))
            for _, row in jt.iterrows():
                joint.append(dict(tag=tag, by=by, level=row[by], F=float(row['F.ratio']),
                                  p=float(row['p.value'])))
        for by, focus in [('lens_lang', 'prompt_lang'), ('prompt_lang', 'lens_lang')]:
            specs = ro.r['as.formula']('~ %s | %s' % (focus, by))
            em = r['emmeans'].emmeans(g.model_r, specs)
            ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
            dfp = pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](ct))))
            for _, row in dfp.iterrows():
                pair.append(dict(tag=tag, by=by, level=row[by],
                                 contrast=str(row['contrast']),
                                 estimate=float(row['estimate']), p=float(row['p.value'])))
        g.model_r = None
        print('fitted', tag, 'converged=%s' % conv, flush=True)

    T = pd.DataFrame(tests)
    C = pd.DataFrame(cells)
    J = pd.DataFrame(joint)
    P = pd.DataFrame(pair)
    for name, df in [('exclusive_tests', T), ('exclusive_cells', C),
                     ('exclusive_joint', J), ('exclusive_pair', P)]:
        df.to_csv(os.path.join(HERE, 'results', name + '.csv'), index=False)

    print('\n=== Type III tests ===')
    for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']:
        s = T[T.effect == e]
        print('%-24s %d/9 significant; p: %s' % (
            e, int((s.p < .05).sum()), ', '.join('%.1e' % v for v in s.p)))
    print('\n=== joint simple effects (N models p<.05) ===')
    for by in ['lens_lang', 'prompt_lang']:
        line = []
        for lev in LEVELS:
            s = J[(J['by'] == by) & (J.level == lev)]
            line.append('%s:%d/9' % (lev, int((s.p < .05).sum())))
        print('%-12s %s' % ('prompt@lens' if by == 'lens_lang' else 'lens@prompt',
                            '  '.join(line)))
    print('\n=== pairwise (sig models/9) ===')
    for by in ['lens_lang', 'prompt_lang']:
        for lev in LEVELS:
            s = P[(P['by'] == by) & (P.level == lev)]
            parts = ['%s %d/9' % (str(c).replace(' - ', '>'), int((g.p < .05).sum()))
                     for c, g in s.groupby('contrast')]
            print('%-6s@%-3s %s' % ('prompt' if by == 'lens_lang' else 'lens', lev,
                                    '; '.join(parts)))
    print('\n=== model-averaged cell means (exclusive rate %) ===')
    mm = C.groupby(['lens_lang', 'prompt_lang'], observed=True).rate.mean().unstack()
    print((100 * mm.reindex(index=LEVELS, columns=LEVELS)).round(2).to_string())
    for lens in LEVELS:
        print('  lens=%-2s prompt order: %s' % (
            lens, ' > '.join(mm.loc[lens].sort_values(ascending=False).index)))
    for prompt in LEVELS:
        print('  prompt=%-2s lens order: %s' % (
            prompt, ' > '.join(mm[prompt].sort_values(ascending=False).index)))
    print('\nnon-converged:', T[T.converged == False].tag.unique().tolist())


if __name__ == '__main__':
    main()
