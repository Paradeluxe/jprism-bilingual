# -*- coding: utf-8 -*-
"""Robustness: refit the 4 share DVs with simpler random structures (the maximal
(1+prompt+lens|item) is singular at 2700 item-level rows) and compare significance."""
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
STRUCTS = {'max': '(1 + prompt_lang + lens_lang | item)',
           'slope_p': '(1 + prompt_lang | item)',
           'int': '(1 | item)'}


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
            for name, rnd in STRUCTS.items():
                m = PinnedLinearMixedModel()
                m.data = d.copy()
                m.dep_var = 'arcsin_' + b
                m.indep_var = ['prompt_lang', 'lens_lang']
                m.random_var = ['item']
                m.fit_pinned('%s ~ prompt_lang * lens_lang + %s' % (m.dep_var, rnd))
                for effect, r in m.anova.iterrows():
                    rows.append(dict(tag=tag, dv='share_' + b, struct=name,
                                     effect=str(effect), p=float(r['Pr(>F)']),
                                     converged=m.converged()))
                m.model_r = None
        print('done', tag, flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, 'results', 'share_struct_robustness.csv'), index=False)
    print('\nsignificance counts (p<.05) by structure:')
    print(df.groupby(['struct', 'dv']).p.apply(lambda s: int((s < .05).sum())).to_string())
    print('\nmax |log10 p| change vs max structure:')
    piv = df.pivot_table(index=['tag', 'dv', 'effect'], columns='struct', values='p')
    for name in ['slope_p', 'int']:
        d = (piv['max'].apply(lambda p: -99 if p <= 0 else __import__('numpy').log10(p))
             - piv[name].apply(lambda p: -99 if p <= 0 else __import__('numpy').log10(p)))
        print('  %-8s max shift %.1f dex' % (name, d.abs().max()))
    print('wrote results/share_struct_robustness.csv')


if __name__ == '__main__':
    main()
