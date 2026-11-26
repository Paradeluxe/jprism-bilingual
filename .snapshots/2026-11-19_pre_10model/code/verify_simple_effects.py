# -*- coding: utf-8 -*-
"""Independent check of the simple effects.

Two independent routes for the same simple effect:
  (a) emmeans::joint_tests(model, by=level)                <- what was reported
  (b) refit the model on the subset of that level, with only the other factor as fixed
      effect (classic "simple effect" = test of the factor in the subset model)

If (a) and (b) agree, the reported simple effects are not an artefact of joint_tests().
Also dumps the raw blackout counts per cell so a tiny-but-significant effect can be judged.
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
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
LEVELS = ['en', 'zh', 'ru']


def load():
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    b = pd.read_csv(os.path.join(HERE, 'data', 'blackoutP.csv'))
    keys = ['tag', 'lens_lang', 'prompt_lang', 'item_type', 'item_idx']
    b = b[keys + ['boP_en', 'boP_zh', 'boP_ru', 'n_boP_en', 'n_boP_zh', 'n_boP_ru',
                  'n_layers']].rename(columns={'n_layers': 'n_layers_b'})
    d = d.merge(b, on=keys, how='left')
    assert len(d) == len(pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv')))
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item'] = d['item_type'] + '_' + d['item_idx'].astype(str)
    for x in ['en', 'zh', 'ru']:
        d['rest_' + x] = d['n_layers'] - d['n_boP_' + x]
    return d


def joint_p(m, by):
    r = _get_r_packages()
    jt = r['emmeans'].joint_tests(m.model_r, by=by)
    df = pd.DataFrame(r2p(ro.r['as.data.frame'](jt)))
    return df


def main():
    set_sum_contrasts()
    d_all = load()
    cases = [
        ('share_en', 'lens_lang', 'en', 'arcsin_en', 'prompt_lang'),
        ('share_zh', 'prompt_lang', 'zh', 'arcsin_zh', 'lens_lang'),
        ('share_ru', 'lens_lang', 'ru', 'arcsin_ru', 'prompt_lang'),
        ('boP_en', 'lens_lang', 'en', 'cbind(n_boP_en, rest_en)', 'prompt_lang'),
        ('boP_zh', 'lens_lang', 'zh', 'cbind(n_boP_zh, rest_zh)', 'prompt_lang'),
        ('boP_ru', 'lens_lang', 'ru', 'cbind(n_boP_ru, rest_ru)', 'prompt_lang'),
    ]
    out = []
    for tag in TAGS:
        d = d_all[d_all.tag == tag].copy()
        for dv, by, lev, resp, focus in cases:
            sub = d[d[by] == lev].copy()
            if dv.startswith('share'):
                m = PinnedLinearMixedModel()
                m.data = sub
                m.dep_var, m.indep_var, m.random_var = resp, [focus], ['item']
                m.fit_pinned('%s ~ %s + (1 | item)' % (resp, focus))
                an = m.anova
                Fs = float(an['F value'].iloc[0])
                p_sub = float(an['Pr(>F)'].iloc[0])
                m.model_r = None
            else:
                g = PinnedGeneralizedLinearMixedModel()
                g.data = sub
                g.dep_var = resp
                g.indep_var = [focus]
                g.random_var = ['item']
                g.fit_pinned('%s ~ %s + (1 | item)' % (resp, focus), family='binomial')
                Fs = float(g.anova['Chisq'].iloc[0])
                p_sub = float(g.anova['Pr(>Chisq)'].iloc[0])
                g.model_r = None
            # full model joint test at this level
            full = PinnedLinearMixedModel() if dv.startswith('share') else PinnedGeneralizedLinearMixedModel()
            full.data = d
            full.dep_var, full.indep_var, full.random_var = resp, ['prompt_lang', 'lens_lang'], ['item']
            if dv.startswith('share'):
                full.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % resp)
            else:
                full.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % resp, family='binomial')
            jt = joint_p(full, by)
            row = jt[jt[by] == lev]
            p_jt = float(row['p.value'].iloc[0]) if len(row) else float('nan')
            F_jt = float(row['F.ratio'].iloc[0]) if len(row) else float('nan')
            out.append(dict(tag=tag, dv=dv, by=by, level=lev,
                            subset_F=round(Fs, 1), subset_p=p_sub,
                            joint_F=round(F_jt, 1), joint_p=p_jt,
                            agree=(p_sub < .05) == (p_jt < .05)))
            full.model_r = None
        print('checked', tag, flush=True)

    res = pd.DataFrame(out)
    res.to_csv(os.path.join(HERE, 'results', 'simple_effects_verify.csv'), index=False)
    print('\nagreement between subset-model and joint_tests:',
          '%d/%d' % (int(res.agree.sum()), len(res)))
    bad = res[~res.agree]
    print('\ndisagreements:' if len(bad) else '\nno disagreements')
    if len(bad):
        print(bad.to_string(index=False))
    print('\nper dv, N significant: joint vs subset')
    print(res.groupby('dv').agg(joint=('joint_p', lambda s: int((s < .05).sum())),
                                subset=('subset_p', lambda s: int((s < .05).sum())),
                                n=('joint_p', 'size')).to_string())

    # raw blackout counts per cell (model-averaged), to judge the tiny EN-lens prompt effect
    print('\nraw blackout counts, EN lens only (layers blacked / layers total, pooled):')
    for x in ['en', 'zh', 'ru']:
        sub = d_all[d_all.lens_lang == 'en']
        g = sub.groupby('prompt_lang', observed=True).apply(
            lambda t: pd.Series({'black': t['n_boP_' + x].sum(),
                                 'layers': t['n_layers'].sum()}), include_groups=False)
        g['rate_pct'] = 100 * g.black / g.layers
        print('boP_' + x)
        print(g.round(3).to_string())


if __name__ == '__main__':
    main()
