# -*- coding: utf-8 -*-
"""Final directional summary: means and significant contrasts with their direction.

Shares and overlap: saturated models (prompt * lens * family).
Blackout family: item-level proportion LMM, saturated.
"""
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
out = []


def w(s=''):
    out.append(s)


def cell_means(cells, dv, lens_col='lens_lang'):
    return cells[cells.dv == dv].groupby([lens_col, 'prompt_lang'])['mean'].mean().unstack() * 100


def prompt_lines(pair, cells, dv):
    lines = []
    for lens in LV:
        m = pair.dv == dv
        if 'by' in pair.columns:
            m &= pair['by'] == 'lens_lang'
        sub = pair[m & (pair.level == lens)]
        if sub.empty:
            continue
        bits = []
        for c in ['en - zh', 'en - ru', 'ru - zh']:
            g = sub[sub.contrast == c]
            if g.empty:
                continue
            a, b = [x.strip() for x in c.split('-')]
            ca = cells[(cells.dv == dv) & (cells.lens_lang == lens)
                       & (cells.prompt_lang == a)]['mean'].mean() * 100
            cb = cells[(cells.dv == dv) & (cells.lens_lang == lens)
                       & (cells.prompt_lang == b)]['mean'].mean() * 100
            bits.append('%s %+0.1f pp (%d/8)' % (LAB[a] + '>' + LAB[b], ca - cb,
                                                 int((g.p < .05).sum())))
        lines.append('- %s lens: %s' % (LAB[lens], '; '.join(bits)))
    return lines


C = pd.read_csv('results/full_cells.csv'); C = C[C.tag.isin(B)]
PS = pd.read_csv('results/star_pair.csv'); PS = PS[PS.tag.isin(B)]
BO = pd.concat([pd.read_csv('results/pool_bo_lmm_cells.csv'),
                pd.read_csv('results/single_bo_lmm_cells.csv')])
BO = BO[BO.tag.isin(B)]
BP = pd.concat([pd.read_csv('results/pool_bo_lmm_pair.csv'),
                pd.read_csv('results/single_bo_lmm_pair.csv')])
BP = BP[(BP.tag.isin(B)) & (BP.spec == 'saturated')]
O = pd.read_csv('results/overlap_cells.csv'); O = O[O.tag.isin(B)]
PO = pd.read_csv('results/star_pair.csv'); PO = PO[PO.tag.isin(B)]

w('# Direction of the significant results (model-averaged, eight non-quantized models)')
w()

w('## 1. Language shares (saturated models)')
w()
for dv, name in [('share_en', 'English share'), ('share_zh', 'Chinese share'),
                 ('share_ru', 'Russian share'), ('share_other', 'Other-language share')]:
    pm = cell_means(C, dv)
    w('### %s' % name)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % pm.loc[lens, p] for p in LV)))
    w()
    for line in prompt_lines(PS, C, dv):
        w(line)
    w()

w('## 2. Blackout family (item-level proportion LMM, saturated)')
w()
for dv, name in [('blackout_pool', 'Pool blackout'),
                 ('blackout_excl', 'Single blackout'),
                 ('blackout_alive', 'Single survivor')]:
    pm = cell_means(BO, dv)
    w('### %s' % name)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % pm.loc[lens, p] for p in LV)))
    w()
    for line in prompt_lines(BP, BO, dv):
        w(line)
    w()

w('## 3. Three-way overlap')
w()
pm = O.groupby(['measure', 'prompt_lang'])['rate_stw'].mean().unstack() * 100
w('| measure | EN prompt | ZH prompt | RU prompt |')
w('| --- | --- | --- | --- |')
for m in ['m1', 'm2', 'm3', 'm4']:
    w('| %s | %s |' % (m, ' | '.join('%.1f' % pm.loc[m, p] for p in LV)))
w()
for m in ['m1', 'm2', 'm3', 'm4']:
    sub = PO[PO.dv == m]
    bits = []
    for c in ['en - zh', 'en - ru', 'ru - zh']:
        g = sub[sub.contrast == c]
        a, b = [x.strip() for x in c.split('-')]
        ca = O[(O.measure == m) & (O.prompt_lang == a)].rate_stw.mean() * 100
        cb = O[(O.measure == m) & (O.prompt_lang == b)].rate_stw.mean() * 100
        bits.append('%s %+0.1f pp (%d/8)' % (LAB[a] + '>' + LAB[b], ca - cb,
                                             int((g.p < .05).sum())))
    w('- %s: %s' % (m, '; '.join(bits)))

open('results/direction_summary_final.md', 'w', encoding='utf-8',
     newline='\n').write('\n'.join(out) + '\n')
print('\n'.join(out))
