# -*- coding: utf-8 -*-
import docx
import pandas as pd

D = 'manuscript/JSpace_Liu_Nov18_2026.docx'
c = pd.read_csv('experiment/stats_mixed/results/barr_contrasts.csv')
m = pd.read_csv('experiment/stats_mixed/results/barr_cell_means.csv')
DV = {'English share': 'share_en', 'Chinese share': 'share_zh', 'Russian share': 'share_ru',
      'Non-language share': 'share_non', 'Pool blackout': 'blackout_pool', 'Semantic overlap': 'overlap'}
LAN = {'English': 'en', 'Chinese': 'zh', 'Russian': 'ru'}
FAM = {'Country–capital': 'P1', 'Definitional': 'P3', 'Category–clue': 'P4'}
TYPE = {'Cross-language unordered': 'cross', 'Cross-language ordered': 'cross_ordered',
        'Identical-string unordered': 'identical', 'Identical-string ordered': 'identical_ordered'}
LENS = {'English lens': 'en', 'Chinese lens': 'zh', 'Russian lens': 'ru'}


def con_key(s):
    a, b = [x.strip() for x in s.split(' − ')]
    return LAN.get(a, TYPE.get(a, a)) + ' - ' + LAN.get(b, TYPE.get(b, b))


def delta_range(dv, by_level, a, b, mode):
    g = m[m.dv == dv]
    p, f = by_level.split('|')
    if mode == 'lens':
        g = g[(g.prompt_lang == p) & (g.item_type == f)]
        col = 'lens_lang'
    elif mode == 'type':
        g = g[(g.prompt == p) & (g.family == f)]
        col = 'sem_type'
    elif mode == 'prompt_share':
        g = g[(g.lens_lang == p) & (g.item_type == f)]
        col = 'prompt_lang'
    else:
        g = g[(g.sem_type == p) & (g.family == f)]
        col = 'prompt'
    ds = []
    for _, h in g.groupby('tag'):
        v = h.groupby(col).mean_pct.mean()
        if a in v.index and b in v.index:
            ds.append(v[a] - v[b])
    return min(ds), max(ds)


def update_row(row, start, dv, by_level, contrast, focus, mode):
    key = con_key(contrast)
    h = c[(c.dv == dv) & (c.focus == focus) & (c.by == 'cell') &
          (c.by_level == by_level) & (c.contrast == key)]
    if len(h) == 0:
        return False
    a, b = [x.strip() for x in key.split(' - ')]
    lo, hi = delta_range(dv, by_level, a, b, mode)
    row.cells[start].text = '%.1f to %.1f' % (lo, hi)
    row.cells[start + 1].text = '%.1f–%.1f' % (h.t.abs().min(), h.t.abs().max())
    p = h.p.max()
    row.cells[start + 2].text = '< .001' if p < .001 else ('%.3g' % p)
    row.cells[start + 3].text = '%d/12' % int((h.p < .05).sum())
    return True


d = docx.Document(D)
t = d.tables[11]
for row in t.rows[1:]:
    out, prompt, fam, con = [x.text.strip() for x in row.cells[:4]]
    if not update_row(row, 4, DV[out], LAN[prompt] + '|' + FAM[fam], con, 'lens_lang', 'lens'):
        print('A9 unmapped', out, prompt, fam, con)

t = d.tables[12]
for row in t.rows[1:]:
    prompt, fam, con = [x.text.strip() for x in row.cells[:3]]
    if not update_row(row, 3, 'overlap', LAN[prompt] + '|' + FAM[fam], con, 'sem_type', 'type'):
        print('A10 unmapped', prompt, fam, con)

t = d.tables[16]
for row in t.rows[1:]:
    out, lev, fam, con = [x.text.strip() for x in row.cells[:4]]
    if out == 'Semantic overlap':
        ok = update_row(row, 4, 'overlap', TYPE[lev] + '|' + FAM[fam], con, 'prompt', 'prompt_overlap')
    else:
        ok = update_row(row, 4, DV[out], LENS[lev] + '|' + FAM[fam], con, 'prompt_lang', 'prompt_share')
    if not ok:
        print('A14 unmapped', out, lev, fam, con)
d.save(D)
print('A9/A10/A14 updated')
