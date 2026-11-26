# -*- coding: utf-8 -*-
"""Itemised listing of the significant blackout simple effects (one cell at a time)."""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results', 'blackout_simple_list.txt')

TAGS = ['gemma4-12b', 'gemma4-e2b', 'gemma4-e4b', 'qwen3-0.6b',
        'qwen3-1.7b-bnb4', 'qwen3-14b', 'qwen3-4b', 'qwen3.5-0.8b', 'qwen3.5-2b']
SHORT = {'gemma4-12b': 'gm12', 'gemma4-e2b': 'gmE2', 'gemma4-e4b': 'gmE4',
         'qwen3-0.6b': 'q0.6', 'qwen3-1.7b-bnb4': 'q1.7', 'qwen3-14b': 'q14',
         'qwen3-4b': 'q4', 'qwen3.5-0.8b': 'q0.8', 'qwen3.5-2b': 'q2'}
LEVELS = ['en', 'zh', 'ru']
DVS = ['boP_en', 'boP_zh', 'boP_ru']


def cell_label(by, level):
    return ('prompt@lens=' + level) if by == 'lens_lang' else ('lens@prompt=' + level)


def main():
    j = pd.read_csv(os.path.join(HERE, 'results', 'simple_joint_item.csv'))
    p = pd.read_csv(os.path.join(HERE, 'results', 'simple_pair_item.csv'))
    bo = pd.read_csv(os.path.join(HERE, 'data', 'blackoutP.csv'))
    lines = []

    for dv in DVS:
        x = dv.split('_')[1]
        lines.append('\n' + '=' * 110)
        lines.append('# %s   criterion: top-10 all non-language AND %s top-100 share < 50%%'
                     % (dv, x.upper()))
        lines.append('=' * 110)
        for by in ['lens_lang', 'prompt_lang']:
            for level in LEVELS:
                sub = j[(j.dv == dv) & (j['by'] == by) & (j.level == level)]
                lab = cell_label(by, level)
                n_sig = int((sub.p < .05).sum())
                lines.append('\n-- %s   [significant in %d/%d models]' % (lab, n_sig, len(sub)))
                ps = p[(p.dv == dv) & (p['by'] == by) & (p.level == level)]
                pparts = []
                for c, g in ps.groupby('contrast'):
                    pparts.append('%s %d/9' % (str(c).replace(' - ', '>'),
                                               int((g.p < .05).sum())))
                lines.append('   pairwise (sig models/9): ' + '; '.join(pparts))
                for tag in TAGS:
                    r = sub[sub.tag == tag]
                    if len(r) == 0:
                        continue
                    r = r.iloc[0]
                    s = bo[bo.tag == tag]
                    if by == 'lens_lang':
                        s = s[s.lens_lang == level]
                        rates = s.groupby('prompt_lang').apply(
                            lambda t: 100 * t['n_boP_' + x].sum() / t['n_layers'].sum(),
                            include_groups=False)
                    else:
                        s = s[s.prompt_lang == level]
                        rates = s.groupby('lens_lang').apply(
                            lambda t: 100 * t['n_boP_' + x].sum() / t['n_layers'].sum(),
                            include_groups=False)
                    rr = '/'.join('%.1f' % rates.get(k, float('nan')) for k in LEVELS)
                    flag = 'SIG ' if r.p < .05 else 'n.s.'
                    lines.append('   %-5s %s F=%7.2f  p=%-9.3g  rates en/zh/ru = %s%%'
                                 % (SHORT[tag], flag, r.F, r.p, rr))
    text = '\n'.join(lines)
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(text + '\n')
    print(text)
    print('\nwrote', OUT)


if __name__ == '__main__':
    main()
