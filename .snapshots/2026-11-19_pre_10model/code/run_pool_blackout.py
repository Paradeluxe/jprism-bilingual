# -*- coding: utf-8 -*-
"""Re-run the item-level blackout model with the paper's original criterion:

    per layer:  top-10 candidates ALL non-language (no letter)
                AND non-language share of the TOP-100 pool >= 50%

This criterion does not mention any language, so the three "language blackouts" collapse to
one DV by construction.  DV at item level = (# layers meeting it) / n_layers.
Model: binomial GLMM on cbind(k, n_layers - k) ~ prompt_lang * lens_lang + (1 | item).

Also computes simple effects (joint tests + Bonferroni pairwise) and cell means.
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


def load():
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_q.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item'] = d.item_type + '_' + d.item_idx.astype(str)
    # per-item integer counts for the binomial response
    d['n_boQ'] = np.rint(d.pool_blackout * d.n_layers).astype(int)
    d['rest_Q'] = d.n_layers - d.n_boQ
    return d


def main():
    set_sum_contrasts()
    d = load()
    print('items: %d, mean layer-blackout rate: %.4f' % (len(d), d.pool_blackout.mean()))
    cells = d.groupby(['lens_lang', 'prompt_lang'], observed=True).apply(
        lambda t: t.n_boQ.sum() / t.n_layers.sum(), include_groups=False)
    print('\nper-layer blackout rate (lens x prompt, pooled over 9 models):')
    print((100 * cells.unstack().reindex(index=LEVELS, columns=LEVELS)).round(1).to_string())

    r = _get_r_packages()
    tests, joint, pair, meancells = [], [], [], []
    for tag in TAGS:
        sub = d[d.tag == tag].copy()
        g = PinnedGeneralizedLinearMixedModel()
        g.data = sub
        g.dep_var = 'cbind(n_boQ, rest_Q)'
        g.indep_var = ['prompt_lang', 'lens_lang']
        g.random_var = ['item']
        g.fit_pinned('cbind(n_boQ, rest_Q) ~ prompt_lang * lens_lang + (1 | item)',
                     family='binomial')
        for effect, row in g.anova.iterrows():
            if str(effect).startswith('(Intercept)'):
                continue
            tests.append(dict(tag=tag, effect=str(effect), Chisq=float(row['Chisq']),
                              df=float(row['Df']), p=float(row['Pr(>Chisq)']),
                              converged=g.converged()))
        for (lens, prompt), v in sub.groupby(['lens_lang', 'prompt_lang'],
                                             observed=True).n_boQ.apply(
                lambda s: s.sum() / sub.loc[s.index, 'n_layers'].sum()).items():
            meancells.append(dict(tag=tag, lens_lang=lens, prompt_lang=prompt, rate=v))
        # simple effects
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
        print('fitted', tag, flush=True)

    T = pd.DataFrame(tests)
    J = pd.DataFrame(joint)
    P = pd.DataFrame(pair)
    C = pd.DataFrame(meancells)
    for name, df in [('pool_blackout_tests', T), ('pool_blackout_joint', J),
                     ('pool_blackout_pair', P), ('pool_blackout_cells', C)]:
        df.to_csv(os.path.join(HERE, 'results', name + '.csv'), index=False)

    print('\n=== Type III tests per model ===')
    for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']:
        s = T[T.effect == e]
        print('%-24s significant in %d/9 models;  p per model: %s' % (
            e, int((s.p < .05).sum()), ', '.join('%.1e' % v for v in s.p)))
    print('\n=== joint simple effects: N models p<.05 ===')
    for by in ['lens_lang', 'prompt_lang']:
        line = []
        for lev in LEVELS:
            s = J[(J['by'] == by) & (J.level == lev)]
            line.append('%s:%d/9' % (lev, int((s.p < .05).sum())))
        print('%-28s %s' % ('prompt@lens' if by == 'lens_lang' else 'lens@prompt',
                            '  '.join(line)))
    print('\n=== pairwise: significant models / 9 ===')
    for by in ['lens_lang', 'prompt_lang']:
        for lev in LEVELS:
            s = P[(P['by'] == by) & (P.level == lev)]
            parts = ['%s %d/9' % (str(c).replace(' - ', '>'), int((g.p < .05).sum()))
                     for c, g in s.groupby('contrast')]
            print('%-6s@%-3s %s' % ('prompt' if by == 'lens_lang' else 'lens', lev,
                                    '; '.join(parts)))
    print('\n=== model-averaged cell means (%) ===')
    mm = C.groupby(['lens_lang', 'prompt_lang'], observed=True).rate.mean().unstack()
    print((100 * mm.reindex(index=LEVELS, columns=LEVELS)).round(1).to_string())
    for lens in LEVELS:
        print('  lens=%-2s prompt order: %s' % (
            lens, ' > '.join(mm.loc[lens].sort_values(ascending=False).index)))
    for prompt in LEVELS:
        print('  prompt=%-2s lens order: %s' % (
            prompt, ' > '.join(mm[prompt].sort_values(ascending=False).index)))


if __name__ == '__main__':
    main()

