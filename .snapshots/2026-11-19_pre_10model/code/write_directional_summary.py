# -*- coding: utf-8 -*-
"""Direction checks: how often each ordering holds across the eight models."""
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
O = pd.read_csv('results/overlap_cells.csv')
O = O[O.tag.isin(B)]


def order_holds(df, dv, ordering, axis):
    """ordering: list of levels from high to low along `axis` ('lens_lang'/'prompt_lang')."""
    ok = 0
    for tag, g in df[df.dv == dv].groupby('tag'):
        t = g.groupby(axis)['mean'].mean()
        vals = [t.get(x) for x in ordering]
        if any(v is None for v in vals):
            continue
        if all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
            ok += 1
    return ok


def within_holds(df, dv, fixed_axis, fixed_level, ordering):
    """ordering along the other axis, inside one level of fixed_axis."""
    other = 'prompt_lang' if fixed_axis == 'lens_lang' else 'lens_lang'
    ok = 0
    for tag, g in df[df.dv == dv].groupby('tag'):
        sub = g[g[fixed_axis] == fixed_level]
        if sub.empty:
            continue
        t = sub.groupby(other)['mean'].mean()
        vals = [t.get(x) for x in ordering]
        if any(v is None for v in vals):
            continue
        if all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
            ok += 1
    return ok


w('# Direction of the significant effects (eight non-quantized models)')
w()
w('Values are the model-averaged cell means; the counts say in how many of the eight '
  'models the stated ordering holds strictly.')
w()

w('## 1. Language shares')
w()
for dv, name in [('share_en', 'English share'), ('share_zh', 'Chinese share'),
                 ('share_ru', 'Russian share'), ('share_other', 'Other-language share')]:
    pm = C[C.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
    w('### %s' % name)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % pm.loc[lens, p] for p in LV)))
    w()
    if dv == 'share_en':
        w('- lens order %s: %d/8 models' % ('EN > RU > ZH',
                                            order_holds(C, dv, ['en', 'ru', 'zh'], 'lens_lang')))
        for lens in LV:
            w('- prompt order inside %s lens, EN > RU > ZH: %d/8' % (
                LAB[lens], within_holds(C, dv, 'lens_lang', lens, ['en', 'ru', 'zh'])))
    if dv == 'share_zh':
        w('- lens order %s: %d/8 models' % ('ZH > EN > RU',
                                            order_holds(C, dv, ['zh', 'en', 'ru'], 'lens_lang')))
        w('- prompt order inside ZH lens, ZH > RU > EN: %d/8' % (
            within_holds(C, dv, 'lens_lang', 'zh', ['zh', 'ru', 'en'])))
    if dv == 'share_ru':
        w('- RU lens is the largest in %d/8 models for the EN prompt, %d/8 for ZH, %d/8 for RU'
          % (within_holds(C, dv, 'prompt_lang', 'en', ['ru', 'zh', 'en']),
             within_holds(C, dv, 'prompt_lang', 'zh', ['ru', 'zh', 'en']),
             within_holds(C, dv, 'prompt_lang', 'ru', ['ru', 'zh', 'en'])))
        w('- prompt order inside RU lens, RU > EN > ZH: %d/8' % (
            within_holds(C, dv, 'lens_lang', 'ru', ['ru', 'en', 'zh'])))
    if dv == 'share_other':
        w('- prompt order inside RU lens, RU > ZH > EN: %d/8' % (
            within_holds(C, dv, 'lens_lang', 'ru', ['ru', 'zh', 'en'])))
    w()

w('## 2. Blackout family')
w()
for dv, name in [('blackout_pool', 'Pool blackout'),
                 ('blackout_excl', 'Single blackout'),
                 ('blackout_alive', 'Single survivor')]:
    src = C if dv == 'blackout_pool' else S
    pm = src[src.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
    w('### %s' % name)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % pm.loc[lens, p] for p in LV)))
    w()
    if dv == 'blackout_alive':
        w('- lens order %s: %d/8 models' % ('ZH > RU > EN',
                                            order_holds(src, dv, ['zh', 'ru', 'en'], 'lens_lang')))
    else:
        w('- lens order %s: %d/8 models' % ('EN > RU > ZH',
                                            order_holds(src, dv, ['en', 'ru', 'zh'], 'lens_lang')))
    w()

w('## 3. Three-way overlap')
w()
pm = O.groupby(['measure', 'prompt_lang'])['rate_stw'].mean().unstack() * 100
w('| measure | EN prompt | ZH prompt | RU prompt |')
w('| --- | --- | --- | --- |')
for m in ['m1', 'm2', 'm3', 'm4']:
    w('| %s | %s |' % (m, ' | '.join('%.1f' % pm.loc[m, p] for p in LV)))
w()
for m, order in [('m1', ['en', 'zh', 'ru']), ('m2', ['zh', 'en', 'ru']),
                 ('m3', ['zh', 'en', 'ru'])]:
    tt = O[O.measure == m]
    ok = 0
    for tag, g in tt.groupby('tag'):
        t = g.groupby('prompt_lang')['rate_stw'].mean()
        vals = [t.get(x) for x in order]
        if all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)):
            ok += 1
    w('- %s prompt order %s: %d/8 models' % (m, ' > '.join(LAB[x] for x in order), ok))
w()
w('## 4. Probe family')
w()
it = pd.read_csv('data/item_level_core.csv')
it = it[it.tag.isin(B)]
for b, name in [('en', 'English'), ('zh', 'Chinese'), ('ru', 'Russian'), ('other', 'other')]:
    t = it.groupby('item_type')['sh_' + b].mean() * 100
    w('- %s share by family: %s' % (name, ', '.join('%s %.1f' % (k, v) for k, v in t.items())))
t = it.groupby('item_type')['pool_blackout'].mean() * 100
w('- pool blackout by family: %s' % ', '.join('%s %.1f' % (k, v) for k, v in t.items()))

open('results/directional_summary.md', 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(out) + '\n')
print('\n'.join(out))
