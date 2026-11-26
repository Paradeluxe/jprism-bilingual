# -*- coding: utf-8 -*-
"""Final stats table for the 7 DVs x 9 models, with the converged random structure.

shares: LMM arcsine, intercept-only random structure (the maximal structure is singular at
        2700 item-level rows; significance decisions are identical, checked separately)
blackout: binomial GLMM cbind, (1|item)   [from blackoutP_tests.csv]
"""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedLinearMixedModel, set_sum_contrasts

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
SHARES = ['en', 'zh', 'ru', 'other']
EFFECTS = ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']


def prep(tag):
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    d = d[d.tag == tag].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=['en', 'zh', 'ru'])
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=['en', 'zh', 'ru'])
    d['item'] = d['item_type'] + '_' + d['item_idx'].astype(str)
    return d


def main():
    set_sum_contrasts()
    rows = []
    for tag in TAGS:
        d = prep(tag)
        for b in SHARES:
            m = PinnedLinearMixedModel()
            m.data = d.copy()
            m.dep_var = 'arcsin_' + b
            m.indep_var = ['prompt_lang', 'lens_lang']
            m.random_var = ['item']
            m.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % m.dep_var)
            for effect, r in m.anova.iterrows():
                if str(effect).startswith('(Intercept)'):
                    continue
                rows.append(dict(tag=tag, dv='share_' + b, effect=str(effect),
                                 stat='F', value=float(r['F value']),
                                 df1=float(r['NumDF']), df2=float(r['DenDF']),
                                 p=float(r['Pr(>F)']), converged=m.converged()))
            m.model_r = None
        print('done', tag, flush=True)

    sh = pd.DataFrame(rows)
    bo = pd.read_csv(os.path.join(HERE, 'results', 'blackoutP_tests.csv'))
    bo = bo[['tag', 'dv', 'effect', 'stat', 'value', 'df', 'p', 'converged']].copy()
    bo['df1'] = bo['df']
    bo['df2'] = float('nan')
    out = pd.concat([sh, bo], ignore_index=True)
    out.to_csv(os.path.join(HERE, 'results', 'final_7dv_stats.csv'), index=False)

    # pretty print
    order_tags = ['gemma4-12b', 'gemma4-e2b', 'gemma4-e4b', 'qwen3-0.6b',
                  'qwen3-1.7b-bnb4', 'qwen3-14b', 'qwen3-4b', 'qwen3.5-0.8b', 'qwen3.5-2b']
    dvs = ['share_en', 'share_zh', 'share_ru', 'share_other',
           'boP_en', 'boP_zh', 'boP_ru']
    for dv in dvs:
        sub = out[out.dv == dv]
        print('\n### ' + dv)
        print('%-18s %-26s %-26s %-26s' % ('model', 'prompt', 'lens', 'prompt x lens'))
        for tag in order_tags:
            cells = []
            for e in EFFECTS:
                r = sub[(sub.tag == tag) & (sub.effect == e)]
                if len(r) == 0:
                    cells.append('-')
                    continue
                r = r.iloc[0]
                fmt = 'F(%.0f,%.0f)=%.1f' % (r.df1, r.df2, r.value) if r.stat == 'F' \
                    else 'X2(%d)=%.1f' % (int(r.df1), r.value)
                cells.append('%s p=%s' % (fmt, '%.1e' % r.p if r.p < 1e-3 else '%.3f' % r.p))
            print('%-18s %-26s %-26s %-26s' % (tag, cells[0], cells[1], cells[2]))
    print('\nconverged:', out.groupby('stat').converged.agg(['sum', 'size']).to_dict())
    print('wrote results/final_7dv_stats.csv')


if __name__ == '__main__':
    main()
