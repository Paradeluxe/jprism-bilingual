# -*- coding: utf-8 -*-
"""Direction tables: mean difference in percentage points and how often it is significant."""
import itertools
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
out = []


def w(s=''):
    out.append(s)


C = pd.read_csv('results/full_cells.csv')
C = C[C.tag.isin(B)]
S = pd.read_csv('results/single_bo_cells.csv')
S = S[S.tag.isin(B)]
P = pd.read_csv('results/full_pair.csv')
P = P[P.tag.isin(B)]
Ps = pd.read_csv('results/single_bo_pair.csv')
Ps = Ps[(Ps.tag.isin(B)) & (Ps.spec == 'additive')]
O = pd.read_csv('results/overlap_cells.csv')
O = O[O.tag.isin(B)]
Po = pd.read_csv('results/overlap_pair.csv')
Po = Po[Po.tag.isin(B) & (Po.variant == 'stw')]

w('# Direction of the significant contrasts (eight non-quantized models)')
w()
w('Each row: mean cell value (%), the contrast that is significant, the mean difference in '
  'percentage points, and in how many of the eight models the contrast reaches p < .05 with '
  'that sign.')
w()


def pct_table(src, dv, by, level):
    sub = src[(src.dv == dv)]
    t = sub.groupby([by, 'prompt_lang' if by == 'lens_lang' else 'lens_lang'])['mean'].mean() * 100
    return t


def contrast_line(pr, cells, dv, by, level, axis_other):
    sub = pr[(pr.dv == dv) & (pr['by'] == by) & (pr.level == level)]
    if sub.empty:
        return None
    out_bits = []
    for c in ['en - zh', 'en - ru', 'ru - zh']:
        g = sub[sub.contrast == c]
        if g.empty:
            continue
        a, b = [x.strip() for x in c.split('-')]
        ca = cells[(cells[by] == level) & (cells[axis_other] == a)]['mean'].mean() * 100
        cb = cells[(cells[by] == level) & (cells[axis_other] == b)]['mean'].mean() * 100
        out_bits.append('%s %+0.1f pp (%d/8 sig)' % (
            c.replace('-', '>'), ca - cb, int((g.p < .05).sum())))
    return '; '.join(out_bits)


w('## 1. Language shares: prompt contrasts within each lens')
w()
for dv in ['share_en', 'share_zh', 'share_ru']:
    w('### %s' % dv)
    w()
    cells = C[C.dv == dv]
    for lens in LV:
        line = contrast_line(P, cells, dv, 'lens_lang', lens, 'prompt_lang')
        if line:
            w('- %s lens: %s' % (LAB[lens], line))
    w()

w('## 2. Blackout family: prompt contrasts within each lens')
w()
for dv, src_cells, src_pair in [('blackout_pool', C, P),
                                ('blackout_excl', S, Ps),
                                ('blackout_alive', S, Ps)]:
    w('### %s' % dv)
    w()
    cells = src_cells[src_cells.dv == dv]
    for lens in LV:
        line = contrast_line(src_pair, cells, dv, 'lens_lang', lens, 'prompt_lang')
        if line:
            w('- %s lens: %s' % (LAB[lens], line))
    w()

w('## 3. Three-way overlap: prompt contrasts')
w()
cells = O[O.measure.isin(['m1', 'm2', 'm3', 'm4'])]
for m in ['m1', 'm2', 'm3', 'm4']:
    sub = Po[Po.dv == m]
    bits = []
    for c in ['en - zh', 'en - ru', 'ru - zh']:
        g = sub[sub.contrast == c]
        a, b = [x.strip() for x in c.split('-')]
        ca = cells[(cells.measure == m) & (cells.prompt_lang == a)].rate_stw.mean() * 100
        cb = cells[(cells.measure == m) & (cells.prompt_lang == b)].rate_stw.mean() * 100
        bits.append('%s %+0.1f pp (%d/8 sig)' % (c.replace('-', '>'), ca - cb,
                                                 int((g.p < .05).sum())))
    w('- %s: %s' % (m, '; '.join(bits)))
w()

open('results/direction_table.md', 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(out) + '\n')
print('\n'.join(out))
