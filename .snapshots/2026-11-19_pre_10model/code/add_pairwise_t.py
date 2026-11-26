# -*- coding: utf-8 -*-
"""Capture emmeans post-hoc contrasts with t ratios and Satterthwaite df.

Fits the same item-level proportion LMMs as add_term_df.py and, for every model, runs

  emmeans(model, ~ lens_lang)   -> pairwise lens contrasts
  emmeans(model, ~ prompt_lang) -> pairwise prompt contrasts

writing results/pairwise_t.csv with tag, dv, factor, contrast, estimate, SE, df, t, p.
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd  # noqa: E402
import rpy2.robjects as ro  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedLinearMixedModel, set_sum_contrasts  # noqa: E402
from ezlmm.utils import _get_r_packages, r2p  # noqa: E402

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


def contrasts(r, model, factor, by=None):
    spec = ro.r['as.formula']('~ ' + factor if by is None else '~ %s | %s' % (factor, by))
    em = r['emmeans'].emmeans(model, spec)
    ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
    df = pd.DataFrame(r2p(ro.r['as.data.frame'](ct)))
    return df


def main():
    set_sum_contrasts()
    r = _get_r_packages()
    out = []

    def record(tag, dv, factor, df, by=None, byname=None):
        for _, row in df.iterrows():
            out.append(dict(tag=tag, dv=dv, factor=factor, by=by or 'all',
                            level=(str(row[byname]) if byname else 'all'),
                            contrast=str(row['contrast']),
                            estimate=float(row['estimate']),
                            SE=float(row['SE']),
                            df=float(row['df']),
                            t=float(row['t.ratio']),
                            p=float(row['p.value'])))

    items = prep(pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv')))
    items['ang_pool'] = np.arcsin(np.sqrt(np.clip(items.pool_blackout, 0, 1)))
    specs = [('share_en', 'arcsin_en'), ('share_zh', 'arcsin_zh'),
             ('share_ru', 'arcsin_ru'), ('share_other', 'arcsin_other'),
             ('blackout_pool', 'ang_pool')]
    for tag in TAGS:
        sub = items[items.tag == tag].copy()
        for dv, dep in specs:
            m = PinnedLinearMixedModel()
            m.data = sub
            m.dep_var = dep
            m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
            m.random_var = ['item']
            m.fit_pinned('%s ~ prompt_lang * lens_lang * item_type + (1 | item)' % dep)
            record(tag, dv, 'lens_lang', contrasts(r, m.model_r, 'lens_lang'))
            record(tag, dv, 'prompt_lang', contrasts(r, m.model_r, 'prompt_lang'))
            record(tag, dv, 'lens_lang', contrasts(r, m.model_r, 'lens_lang', 'prompt_lang'),
                   by='prompt_lang', byname='prompt_lang')
            record(tag, dv, 'prompt_lang', contrasts(r, m.model_r, 'prompt_lang', 'lens_lang'),
                   by='lens_lang', byname='lens_lang')
            m.model_r = None
        print('shares', tag, flush=True)

    exc = prep(pd.read_csv(os.path.join(HERE, 'data', 'blackout_exclusive.csv')))
    for dv, col in (('blackout_excl', 'rate'), ('blackout_alive', 'rate_alive')):
        exc['ang_' + dv] = np.arcsin(np.sqrt(np.clip(exc[col], 0, 1)))
    for tag in TAGS:
        sub = exc[exc.tag == tag].copy()
        for dv in ('blackout_excl', 'blackout_alive'):
            m = PinnedLinearMixedModel()
            m.data = sub
            m.dep_var = 'ang_' + dv
            m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
            m.random_var = ['item']
            m.fit_pinned('ang_%s ~ prompt_lang * lens_lang * item_type + (1 | item)' % dv)
            record(tag, dv, 'lens_lang', contrasts(r, m.model_r, 'lens_lang'))
            record(tag, dv, 'prompt_lang', contrasts(r, m.model_r, 'prompt_lang'))
            record(tag, dv, 'lens_lang', contrasts(r, m.model_r, 'lens_lang', 'prompt_lang'),
                   by='prompt_lang', byname='prompt_lang')
            m.model_r = None
        print('single', tag, flush=True)

    ov = prep(pd.read_csv(os.path.join(HERE, 'data', 'overlap_item.csv')))
    for m in MEAS:
        ov['ang_' + m] = np.arcsin(np.sqrt(np.clip(ov[m + '_stw_rate'], 0, 1)))
    for tag in TAGS:
        sub = ov[ov.tag == tag].copy()
        for m in MEAS:
            mod = PinnedLinearMixedModel()
            mod.data = sub
            mod.dep_var = 'ang_' + m
            mod.indep_var = ['prompt_lang', 'item_type']
            mod.random_var = ['item']
            mod.fit_pinned('ang_%s ~ prompt_lang * item_type + (1 | item)' % m)
            record(tag, m, 'prompt_lang', contrasts(r, mod.model_r, 'prompt_lang'))
            record(tag, m, 'prompt_lang', contrasts(r, mod.model_r, 'prompt_lang', 'item_type'),
                   by='item_type', byname='item_type')
            mod.model_r = None
        print('overlap', tag, flush=True)

    T = pd.DataFrame(out)
    path = os.path.join(HERE, 'results', 'pairwise_t.csv')
    T.to_csv(path, index=False)
    print('\nwrote', path, T.shape)
    for dv in ['share_en', 'share_zh', 'share_ru', 'blackout_pool', 'blackout_excl',
               'blackout_alive', 'm1', 'm2', 'm3']:
        for factor in ('lens_lang', 'prompt_lang'):
            s = T[(T.dv == dv) & (T.factor == factor)]
            if s.empty:
                continue
            print('%-14s %-11s' % (dv, factor), ' | '.join(
                '%s t=%.1f..%.1f df=%.0f-%.0f' % (c, g.t.min(), g.t.max(), g.df.min(), g.df.max())
                for c, g in s.groupby('contrast')))


if __name__ == '__main__':
    main()
