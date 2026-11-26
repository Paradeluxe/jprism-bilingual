# -*- coding: utf-8 -*-
"""Full factorial models: prompt * lens * probe family (all interactions).

  shares      arcsin(share) ~ prompt_lang * lens_lang * item_type + (1 | item)
  blackout    cbind(k, n-k) ~ prompt_lang * lens_lang * item_type + (1 | item)
  overlap     cbind(k, den-k) ~ prompt_lang * item_type + (1 | item)

Outputs (results/):
  star_tests.csv   Type III tests for every term
  star_joint.csv   joint simple effects (prompt | lens, lens | prompt, prompt | family)
  star_pair.csv    Bonferroni pairwise prompt contrasts within each lens
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd
import rpy2.robjects as ro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import (PinnedLinearMixedModel, PinnedGeneralizedLinearMixedModel,
                          set_sum_contrasts)
from ezlmm.utils import _get_r_packages, r2p

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
SHARES = ['en', 'zh', 'ru', 'other']
MEAS = ['m1', 'm2', 'm3', 'm4']
LEVELS = ['en', 'zh', 'ru']
FAMILIES = ['P1', 'P3', 'P4']


def load_items():
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
    d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)
    d['n_boQ'] = np.rint(d.pool_blackout * d.n_layers).astype(int)
    d['rest_Q'] = d.n_layers - d.n_boQ
    return d


def load_overlap():
    d = pd.read_csv(os.path.join(HERE, 'data', 'overlap_item.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
    d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)
    for m in MEAS:
        d[m + '_rest'] = d[m + '_stw_den'] - d[m + '_stw']
    return d


def as_df(x):
    return pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](x))))


def main():
    set_sum_contrasts()
    r = _get_r_packages()
    items = load_items()
    overlap = load_overlap()

    tests, joint, pair = [], [], []

    for tag in TAGS:
        d = items[items.tag == tag].copy()
        o = overlap[overlap.tag == tag].copy()
        models = {}

        for b in SHARES:
            m = PinnedLinearMixedModel()
            m.data = d.copy()
            m.dep_var = 'arcsin_' + b
            m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
            m.random_var = ['item']
            m.fit_pinned('arcsin_%s ~ prompt_lang * lens_lang * item_type'
                         ' + (1 | item)' % b)
            models['share_' + b] = (m, 'LMM')

        g = PinnedGeneralizedLinearMixedModel()
        g.data = d.copy()
        g.dep_var = 'cbind(n_boQ, rest_Q)'
        g.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
        g.random_var = ['item']
        g.fit_pinned('cbind(n_boQ, rest_Q) ~ prompt_lang * lens_lang * item_type'
                     ' + (1 | item)', family='binomial')
        models['blackout_pool'] = (g, 'GLMM')

        for m in MEAS:
            gg = PinnedGeneralizedLinearMixedModel()
            gg.data = o.copy()
            gg.dep_var = 'cbind(%s_stw, %s_rest)' % (m, m)
            gg.indep_var = ['prompt_lang', 'item_type']
            gg.random_var = ['item']
            gg.fit_pinned('cbind(%s_stw, %s_rest) ~ prompt_lang * item_type'
                          ' + (1 | item)' % (m, m), family='binomial')
            models[m] = (gg, 'GLMM')

        print('fitted', tag, flush=True)

        for dv, (mod, kind) in models.items():
            an = mod.anova
            pcol = 'Pr(>F)' if kind == 'LMM' else 'Pr(>Chisq)'
            scol = 'F value' if kind == 'LMM' else 'Chisq'
            for effect, row in an.iterrows():
                tests.append(dict(tag=tag, dv=dv, effect=str(effect),
                                  stat=float(row[scol]), p=float(row[pcol]),
                                  converged=mod.converged()))
            if dv in MEAS:
                specs = ro.r['as.formula']('~ prompt_lang')
                em = r['emmeans'].emmeans(mod.model_r, specs)
                ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
                for _, row in as_df(ct).iterrows():
                    pair.append(dict(tag=tag, dv=dv, by='all', level='all',
                                     contrast=str(row['contrast']),
                                     estimate=float(row['estimate']),
                                     p=float(row['p.value'])))
            else:
                for by, focus in [('lens_lang', 'prompt'), ('prompt_lang', 'lens'),
                                  ('item_type', 'prompt')]:
                    jt = r['emmeans'].joint_tests(mod.model_r, by=by)
                    for _, row in pd.DataFrame(r2p(ro.r['as.data.frame'](jt))).iterrows():
                        joint.append(dict(tag=tag, dv=dv, by=by, level=row[by],
                                          focus=focus, term=str(row.get('model term', '')),
                                          F=float(row['F.ratio']), p=float(row['p.value'])))
                for by, focus in [('lens_lang', 'prompt_lang')]:
                    specs = ro.r['as.formula']('~ %s | %s' % (focus, by))
                    em = r['emmeans'].emmeans(mod.model_r, specs)
                    ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
                    for _, row in as_df(ct).iterrows():
                        pair.append(dict(tag=tag, dv=dv, by=by, level=row[by],
                                         contrast=str(row['contrast']),
                                         estimate=float(row['estimate']),
                                         p=float(row['p.value'])))
            mod.model_r = None

    T = pd.DataFrame(tests)
    J = pd.DataFrame(joint)
    P = pd.DataFrame(pair)
    out = os.path.join(HERE, 'results')
    T.to_csv(os.path.join(out, 'star_tests.csv'), index=False)
    J.to_csv(os.path.join(out, 'star_joint.csv'), index=False)
    P.to_csv(os.path.join(out, 'star_pair.csv'), index=False)

    print('\n=== Type III, prompt * lens * probe family ===')
    terms = ['prompt_lang', 'lens_lang', 'item_type',
             'prompt_lang:lens_lang', 'prompt_lang:item_type',
             'lens_lang:item_type', 'prompt_lang:lens_lang:item_type']
    for dv in ['share_en', 'share_zh', 'share_ru', 'share_other',
               'blackout_pool', 'm1', 'm2', 'm3', 'm4']:
        s = T[T.dv == dv]
        row = {}
        for e in terms:
            g = s[s.effect == e]
            if not g.empty:
                row[e] = '%d/8' % int((g.p < .05).sum())
        print('%-14s %s' % (dv, row))
    print('\nwrote results/star_{tests,joint,pair}.csv')


if __name__ == '__main__':
    main()
