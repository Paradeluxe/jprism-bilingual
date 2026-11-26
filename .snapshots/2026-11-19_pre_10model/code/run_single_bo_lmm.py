# -*- coding: utf-8 -*-
"""Single blackout and single survivor modelled at the item level (proportion LMM).

Instead of treating the measured layers as independent binomial trials, each cell
contributes its item-level proportion (layers with the outcome / measured layers) and
that proportion is modelled with an arcsine-square-root linear mixed model, exactly as
the language shares are:

  arcsin(sqrt(rate)) ~ prompt_lang * lens_lang * item_type + (1 | item)

An additive specification (+ item_type) is fitted as well, for comparison.

Outputs (results/):
  single_bo_lmm_tests.csv, single_bo_lmm_joint.csv, single_bo_lmm_pair.csv,
  single_bo_lmm_cells.csv
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
DVS = {'blackout_excl': 'rate', 'blackout_alive': 'rate_alive'}


def load():
    d = pd.read_csv(os.path.join(HERE, 'data', 'blackout_exclusive.csv'))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
    d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)
    for dv, col in DVS.items():
        d['ang_' + dv] = np.arcsin(np.sqrt(np.clip(d[col], 0, 1)))
    return d


def as_df(x):
    return pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](x))))


def main():
    set_sum_contrasts()
    r = _get_r_packages()
    d_all = load()
    tests, joint, pair, cells = [], [], [], []

    for tag in TAGS:
        d = d_all[d_all.tag == tag].copy()
        for dv, col in DVS.items():
            for spec in ('additive', 'saturated'):
                term = 'prompt_lang * lens_lang' + (
                    ' + item_type' if spec == 'additive' else ' * item_type')
                m = PinnedLinearMixedModel()
                m.data = d.copy()
                m.dep_var = 'ang_' + dv
                m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
                m.random_var = ['item']
                m.fit_pinned('ang_%s ~ %s + (1 | item)' % (dv, term))
                for effect, row in m.anova.iterrows():
                    tests.append(dict(tag=tag, dv=dv, spec=spec, effect=str(effect),
                                      stat=float(row['F value']),
                                      p=float(row['Pr(>F)']),
                                      converged=m.converged()))
                for by, focus in [('lens_lang', 'prompt'), ('prompt_lang', 'lens'),
                                  ('item_type', 'prompt')]:
                    jt = r['emmeans'].joint_tests(m.model_r, by=by)
                    for _, row in pd.DataFrame(r2p(ro.r['as.data.frame'](jt))).iterrows():
                        joint.append(dict(tag=tag, dv=dv, spec=spec, by=by,
                                          level=row[by], focus=focus,
                                          term=str(row.get('model term', '')),
                                          F=float(row['F.ratio']),
                                          p=float(row['p.value'])))
                specs = ro.r['as.formula']('~ prompt_lang | lens_lang')
                em = r['emmeans'].emmeans(m.model_r, specs)
                ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
                for _, row in as_df(ct).iterrows():
                    pair.append(dict(tag=tag, dv=dv, spec=spec, level=row['lens_lang'],
                                     contrast=str(row['contrast']),
                                     estimate=float(row['estimate']),
                                     p=float(row['p.value'])))
                m.model_r = None
            tab = d.groupby(['lens_lang', 'prompt_lang'])[col].mean()
            for (lens, prompt), v in tab.items():
                cells.append(dict(tag=tag, dv=dv, lens_lang=lens,
                                  prompt_lang=prompt, mean=float(v)))
        print('fitted', tag, flush=True)

    out = os.path.join(HERE, 'results')
    T, J, P, C = pd.DataFrame(tests), pd.DataFrame(joint), pd.DataFrame(pair), pd.DataFrame(cells)
    T.to_csv(os.path.join(out, 'single_bo_lmm_tests.csv'), index=False)
    J.to_csv(os.path.join(out, 'single_bo_lmm_joint.csv'), index=False)
    P.to_csv(os.path.join(out, 'single_bo_lmm_pair.csv'), index=False)
    C.to_csv(os.path.join(out, 'single_bo_lmm_cells.csv'), index=False)

    print('\n=== item-level proportion LMM ===')
    for dv in DVS:
        for spec in ('additive', 'saturated'):
            s = T[(T.dv == dv) & (T.spec == spec)]
            row = {}
            for e in ['prompt_lang', 'lens_lang', 'item_type',
                      'prompt_lang:lens_lang', 'prompt_lang:item_type',
                      'lens_lang:item_type', 'prompt_lang:lens_lang:item_type']:
                g = s[s.effect == e]
                if not g.empty:
                    row[e] = '%d/8' % int((g.p < .05).sum())
            print('%-16s %-9s %s' % (dv, spec, row))
    print('\nwrote results/single_bo_lmm_*.csv')


if __name__ == '__main__':
    main()
