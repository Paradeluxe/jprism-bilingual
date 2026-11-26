# -*- coding: utf-8 -*-
"""Simple-effects analysis for the final item-level 7-DV model, aggregated over 9 models.

For every model x DV:
  * joint simple-effect tests: prompt effect at each lens level; lens effect at each prompt
  * Bonferroni pairwise contrasts within each by-level
Then aggregate over models: how many models show each simple effect / pairwise, and the
model-averaged cell means and ordering (response scale: share % for bands, blackout % for
the three blackout DVs).

All share DVs are TOP-100 pool shares, layer-averaged per item.
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
SHARES = ['en', 'zh', 'ru', 'other']
BB = ['en', 'zh', 'ru']
LEVELS = ['en', 'zh', 'ru']


def load():
    d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
    b = pd.read_csv(os.path.join(HERE, 'data', 'blackoutP.csv'))
    keys = ['tag', 'lens_lang', 'prompt_lang', 'item_type', 'item_idx']
    b = b[keys + ['boP_en', 'boP_zh', 'boP_ru', 'n_boP_en', 'n_boP_zh', 'n_boP_ru',
                  'n_layers']].rename(columns={'n_layers': 'n_layers_b'})
    d = d.merge(b, on=keys, how='left')
    d = d[d.tag.isin(TAGS)].copy()
    d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
    d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
    d['item'] = d['item_type'] + '_' + d['item_idx'].astype(str)
    for x in BB:
        d['rest_' + x] = d['n_layers'] - d['n_boP_' + x]
    return d


def edf(em):
    return pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](em))))


def main():
    set_sum_contrasts()
    r = _get_r_packages()
    d_all = load()

    joint_rows, pair_rows, cell_rows = [], [], []
    for tag in TAGS:
        d = d_all[d_all.tag == tag].copy()
        models = {}
        for b in SHARES:
            m = PinnedLinearMixedModel()
            m.data = d.copy()
            m.dep_var = 'arcsin_' + b
            m.indep_var = ['prompt_lang', 'lens_lang']
            m.random_var = ['item']
            m.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % m.dep_var)
            models['share_' + b] = m
        for x in BB:
            g = PinnedGeneralizedLinearMixedModel()
            g.data = d.copy()
            g.dep_var = 'cbind(n_boP_%s, rest_%s)' % (x, x)
            g.indep_var = ['prompt_lang', 'lens_lang']
            g.random_var = ['item']
            g.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % g.dep_var,
                         family='binomial')
            models['boP_' + x] = g
        print('fitted', tag, flush=True)

        # cell means on the observed scale (model-averaged later)
        for dv in models:
            if dv.startswith('share_'):
                b = dv.split('_')[1]
                tab = d.groupby(['lens_lang', 'prompt_lang'])['sh_' + b].mean()
            else:
                x = dv.split('_')[1]
                tab = d.groupby(['lens_lang', 'prompt_lang'])['boP_' + x].mean()
            for (lens, prompt), v in tab.items():
                cell_rows.append(dict(tag=tag, dv=dv, lens_lang=lens,
                                      prompt_lang=prompt, mean=float(v)))

        for dv, m in models.items():
            # joint simple effects
            for by, focus in [('lens_lang', 'prompt'), ('prompt_lang', 'lens')]:
                jt = r['emmeans'].joint_tests(m.model_r, by=by)
                dfj = pd.DataFrame(r2p(ro.r['as.data.frame'](jt)))
                for _, row in dfj.iterrows():
                    lev = row[by]
                    joint_rows.append(dict(tag=tag, dv=dv, by=by, level=lev,
                                           focus=focus, F=float(row['F.ratio']),
                                           p=float(row['p.value'])))
            # pairwise within each level
            for by, focus in [('lens_lang', 'prompt_lang'), ('prompt_lang', 'lens_lang')]:
                specs = ro.r['as.formula']('~ %s | %s' % (focus, by))
                em = r['emmeans'].emmeans(m.model_r, specs)
                ct = r['emmeans'].contrast(em, 'pairwise', adjust='bonferroni')
                dfp = pd.DataFrame(r2p(ro.r['as.data.frame'](ro.r['summary'](ct))))
                for _, row in dfp.iterrows():
                    pair_rows.append(dict(tag=tag, dv=dv, by=by, level=row[by],
                                          contrast=str(row['contrast']),
                                          estimate=float(row['estimate']),
                                          p=float(row['p.value'])))
            m.model_r = None

    joint = pd.DataFrame(joint_rows)
    pair = pd.DataFrame(pair_rows)
    cells = pd.DataFrame(cell_rows)
    for name, df in [('simple_joint_item', joint), ('simple_pair_item', pair),
                     ('cell_means_item', cells)]:
        df.to_csv(os.path.join(HERE, 'results', name + '.csv'), index=False)

    # ---------- aggregation ----------
    dvs = ['share_en', 'share_zh', 'share_ru', 'share_other', 'boP_en', 'boP_zh', 'boP_ru']
    print('\n## joint simple effects: N models with p<.05 (out of 9)')
    for dv in dvs:
        print('--', dv)
        for by in ['lens_lang', 'prompt_lang']:
            sub = joint[(joint.dv == dv) & (joint['by'] == by)]
            line = []
            for lev in LEVELS:
                s = sub[sub.level == lev]
                line.append('%s:%d/%d' % (lev, int((s.p < .05).sum()), len(s)))
            print('   %s -> %s' % ('prompt@lens' if by == 'lens_lang' else 'lens@prompt',
                                  '  '.join(line)))

    print('\n## model-averaged cell means and ordering')
    for dv in dvs:
        sub = cells[cells.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean()
        mat = sub.unstack().reindex(index=LEVELS, columns=LEVELS)
        scale = 100.0
        print('\n--', dv, '(%)')
        print((mat * scale).round(1).to_string())
        for lens in LEVELS:
            order = mat.loc[lens].sort_values(ascending=False).index.tolist()
            print('   lens=%-2s prompt order: %s' % (lens, ' > '.join(order)))
        for prompt in LEVELS:
            order = mat[prompt].sort_values(ascending=False).index.tolist()
            print('   prompt=%-2s lens order: %s' % (prompt, ' > '.join(order)))

    print('\n## pairwise: fraction of models significant (p<.05, bonferroni)')
    for dv in dvs:
        sub = pair[pair.dv == dv]
        print('\n--', dv)
        for by, focus in [('lens_lang', 'prompt'), ('prompt_lang', 'lens')]:
            for lev in LEVELS:
                s = sub[(sub['by'] == by) & (sub.level == lev)]
                if len(s) == 0:
                    continue
                parts = []
                for c, g in s.groupby('contrast'):
                    parts.append('%s %d/9' % (c.replace(' - ', '>'), int((g.p < .05).sum())))
                print('   %s@%-2s: %s' % (focus, lev, '; '.join(parts)))


if __name__ == '__main__':
    main()
