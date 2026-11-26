# -*- coding: utf-8 -*-
"""Refit the item-level proportion LMMs and record Satterthwaite numerator/denominator df.

The anova table of the pinned lmerTest fit already carries NumDF and DenDF, so this script
only re-fits the saturated models used in the Results section and writes one compact table:

  results/term_df.csv   tag, dv, effect, F, df1, df2, p, converged
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedLinearMixedModel, set_sum_contrasts  # noqa: E402

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LEVELS = ['en', 'zh', 'ru']
FAMILIES = ['P1', 'P3', 'P4']
MEAS = ['m1', 'm2', 'm3', 'm4']


def prep(d):
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    if 'lens_lang' in d.columns:
        d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
    d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)
    return d


def fit(sub, dep, formula, indep=None):
    m = PinnedLinearMixedModel()
    m.data = sub
    m.dep_var = dep
    m.indep_var = indep or ['prompt_lang', 'lens_lang', 'item_type']
    m.random_var = ['item']
    m.fit_pinned(formula)
    an = m.anova
    rows = []
    for effect, row in an.iterrows():
        rows.append(dict(F=float(row['F value']), df1=float(row['NumDF']),
                         df2=float(row['DenDF']), p=float(row['Pr(>F)'])))
    conv = bool(m.converged())
    m.model_r = None
    return rows, conv


def main():
    set_sum_contrasts()
    out = []
    items = prep(pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv')))
    items['ang_pool'] = np.arcsin(np.sqrt(np.clip(items.pool_blackout, 0, 1)))

    for tag in TAGS:
        sub = items[items.tag == tag].copy()
        for b in ['en', 'zh', 'ru', 'other']:
            rows, conv = fit(sub, 'arcsin_' + b,
                             'arcsin_%s ~ prompt_lang * lens_lang * item_type + (1 | item)' % b)
            for ef, r in zip(['prompt_lang', 'lens_lang', 'item_type',
                              'prompt_lang:lens_lang', 'prompt_lang:item_type',
                              'lens_lang:item_type', 'prompt_lang:lens_lang:item_type'], rows):
                out.append(dict(tag=tag, dv='share_' + b, effect=ef, converged=conv, **r))
        rows, conv = fit(sub, 'ang_pool',
                         'ang_pool ~ prompt_lang * lens_lang * item_type + (1 | item)')
        for ef, r in zip(['prompt_lang', 'lens_lang', 'item_type',
                          'prompt_lang:lens_lang', 'prompt_lang:item_type',
                          'lens_lang:item_type', 'prompt_lang:lens_lang:item_type'], rows):
            out.append(dict(tag=tag, dv='blackout_pool', effect=ef, converged=conv, **r))
        print('shares + pool', tag, flush=True)

    exc = prep(pd.read_csv(os.path.join(HERE, 'data', 'blackout_exclusive.csv')))
    for dv, col in (('blackout_excl', 'rate'), ('blackout_alive', 'rate_alive')):
        exc['ang_' + dv] = np.arcsin(np.sqrt(np.clip(exc[col], 0, 1)))
    for tag in TAGS:
        sub = exc[exc.tag == tag].copy()
        for dv in ('blackout_excl', 'blackout_alive'):
            rows, conv = fit(sub, 'ang_' + dv,
                             'ang_%s ~ prompt_lang * lens_lang * item_type + (1 | item)' % dv)
            for ef, r in zip(['prompt_lang', 'lens_lang', 'item_type',
                              'prompt_lang:lens_lang', 'prompt_lang:item_type',
                              'lens_lang:item_type', 'prompt_lang:lens_lang:item_type'], rows):
                out.append(dict(tag=tag, dv=dv, effect=ef, converged=conv, **r))
        print('single blackout', tag, flush=True)

    ov = prep(pd.read_csv(os.path.join(HERE, 'data', 'overlap_item.csv')))
    for m in MEAS:
        ov['ang_' + m] = np.arcsin(np.sqrt(np.clip(ov[m + '_stw_rate'], 0, 1)))
    for tag in TAGS:
        sub = ov[ov.tag == tag].copy()
        for m in MEAS:
            rows, conv = fit(sub, 'ang_' + m, 'ang_%s ~ prompt_lang * item_type + (1 | item)' % m,
                             indep=['prompt_lang', 'item_type'])
            for ef, r in zip(['prompt_lang', 'item_type', 'prompt_lang:item_type'], rows):
                out.append(dict(tag=tag, dv=m, effect=ef, converged=conv, **r))
        print('overlap', tag, flush=True)

    T = pd.DataFrame(out)
    path = os.path.join(HERE, 'results', 'term_df.csv')
    T.to_csv(path, index=False)
    print('\nwrote', path, T.shape)
    for dv in ['share_en', 'share_zh', 'share_ru', 'share_other', 'blackout_pool',
               'blackout_excl', 'blackout_alive', 'm1', 'm2', 'm3', 'm4']:
        s = T[T.dv == dv]
        print('%-14s' % dv, ' | '.join(
            '%s df1=%g df2=%.0f-%.0f F=%.1f-%.1f' % (
                e, g.df1.iloc[0], g.df2.min(), g.df2.max(), g.F.min(), g.F.max())
            for e, g in s.groupby('effect')))


if __name__ == '__main__':
    main()
