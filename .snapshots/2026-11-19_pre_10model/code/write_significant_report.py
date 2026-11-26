# -*- coding: utf-8 -*-
"""Write the significant-results summary (8 non-quantized models) to markdown."""
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
out = []


def w(s=''):
    out.append(s)


F = pd.read_csv('results/final_7dv_stats.csv')
F8 = F[F.tag.isin(B) & F.dv.str.startswith('share_')]
T = pd.read_csv('results/pool_blackout_tests.csv')
T8 = T[T.tag.isin(B)]
O = pd.read_csv('results/overlap_tests.csv')
O8 = O[O.tag.isin(B) & (O.variant == 'stw') & (O.model == 'GLMM')]
C = pd.read_csv('results/cell_means_item.csv')
C8 = C[C.tag.isin(B)]
P = pd.read_csv('results/simple_pair_item.csv')
P8 = P[P.tag.isin(B)]
Cb = pd.read_csv('results/pool_blackout_cells.csv')
Cb8 = Cb[Cb.tag.isin(B)]
Gb = pd.read_csv('results/pool_blackout_pair.csv')
Gb8 = Gb[Gb.tag.isin(B)]
Co = pd.read_csv('results/overlap_cells.csv')
Co8 = Co[Co.tag.isin(B)]
Po = pd.read_csv('results/overlap_pair.csv')
Po8 = Po[Po.tag.isin(B) & (Po.variant == 'stw')]

w('# Significant results (eight non-quantized models)')
w()
w('Models: Qwen3-0.6B, Qwen3-4B, Qwen3-14B, Qwen3.5-0.8B, Qwen3.5-2B, '
  'Gemma-4-E2B, Gemma-4-E4B, Gemma-4-12B.')
w()
w('## 1. Which effects were significant')
w()
w('| DV | prompt | lens | prompt x lens |')
w('| --- | --- | --- | --- |')
for dv in ['share_en', 'share_zh', 'share_ru', 'share_other']:
    s = F8[F8.dv == dv]
    cells = []
    for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']:
        g = s[s.effect == e]
        cells.append('%d/8' % int((g.p < .05).sum()))
    w('| %s | %s |' % (dv, ' | '.join(cells)))

for e, nm in [('prompt_lang', 'pool blackout: prompt'),
              ('lens_lang', 'pool blackout: lens'),
              ('prompt_lang:lens_lang', 'pool blackout: interaction')]:
    g = T8[T8.effect == e]
    ns = g[g.p >= .05].tag.tolist()
    w('| %s | %d/8%s | | |' % (nm, int((g.p < .05).sum()),
                               '' if not ns else ' (ns: %s)' % ', '.join(ns)))
for m in ['m1', 'm2', 'm3', 'm4']:
    g = O8[O8.measure == m]
    ns = g[g.p >= .05].tag.tolist()
    w('| overlap %s | %d/8%s | - | - |' % (m, int((g.p < .05).sum()),
                                          '' if not ns else ' (ns: %s)' % ', '.join(ns)))

w()
w('## 2. Simple effects: language shares (mean cell value, % of top-100)')
w()
for dv in ['share_en', 'share_zh', 'share_ru', 'share_other']:
    cm = C8[C8.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
    cm = cm.reindex(LV)[['en', 'zh', 'ru']].round(1)
    w('### %s' % dv)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % cm.loc[lens, p] for p in LV)))
    w()
    s = P8[P8.dv == dv]
    for by, nm in [('lens_lang', 'within lens'), ('prompt_lang', 'within prompt')]:
        for lv in LV:
            sub = s[(s['by'] == by) & (s.level == lv)]
            if sub.empty:
                continue
            parts = []
            for c in ['en - zh', 'en - ru', 'ru - zh']:
                g = sub[sub.contrast == c]
                parts.append('%s %d/8' % (c, int((g.p < .05).sum())))
            w('- %s=%s: %s' % (nm, LAB[lv], '; '.join(parts)))
    w()

w('## 3. Simple effects: pool blackout (mean rate, % of measured layers)')
w()
cm = Cb8.groupby(['lens_lang', 'prompt_lang'])['rate'].mean().unstack() * 100
cm = cm.reindex(LV)[['en', 'zh', 'ru']].round(1)
w('| lens \\ prompt | EN | ZH | RU |')
w('| --- | --- | --- | --- |')
for lens in LV:
    w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % cm.loc[lens, p] for p in LV)))
w()
for by, nm in [('lens_lang', 'within lens'), ('prompt_lang', 'within prompt')]:
    for lv in LV:
        sub = Gb8[(Gb8['by'] == by) & (Gb8.level == lv)]
        if sub.empty:
            continue
        parts = []
        for c in ['en - zh', 'en - ru', 'ru - zh']:
            g = sub[sub.contrast == c]
            parts.append('%s %d/8' % (c, int((g.p < .05).sum())))
        w('- %s=%s: %s' % (nm, LAB[lv], '; '.join(parts)))
w()
w('### Pool blackout per model (%)')
w()
pm = Cb8.pivot_table(index='tag', columns=['lens_lang', 'prompt_lang'],
                     values='rate') * 100
w('| model | EN lens | | | ZH lens | | | RU lens | | |')
w('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
w('| | ENp | ZHp | RUp | ENp | ZHp | RUp | ENp | ZHp | RUp |')
for tag in B:
    row = pm.loc[tag]
    vals = ['%.1f' % row[(lens, pr)] for lens in LV for pr in LV]
    w('| %s | %s |' % (tag, ' | '.join(vals)))
w()

w('## 4. Three-way overlap: means (%) and prompt contrasts')
w()
cm = Co8.groupby(['measure', 'prompt_lang'])['rate_stw'].mean().unstack() * 100
w('| measure | EN prompt | ZH prompt | RU prompt |')
w('| --- | --- | --- | --- |')
for m in ['m1', 'm2', 'm3', 'm4']:
    w('| %s | %s |' % (m, ' | '.join('%.1f' % cm.loc[m, p] for p in LV)))
w()
for m in ['m1', 'm2', 'm3', 'm4']:
    sub = Po8[Po8.measure == m]
    parts = []
    for c in ['en - zh', 'en - ru', 'ru - zh']:
        g = sub[sub.contrast == c]
        parts.append('%s %d/8' % (c, int((g.p < .05).sum())))
    w('- %s: %s' % (m, '; '.join(parts)))

w()
w('## 5. Not reported')
w()
w('- Single blackout and single survivor: the binomial GLMMs failed to converge '
  'for most models, so these measures are descriptive only.')
w('- The older per-language blackout DVs (boP_en / boP_zh / boP_ru) are superseded '
  'by the pool-level blackout.')

open('results/significant_summary_8models.md', 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(out) + '\n')
print('wrote results/significant_summary_8models.md')
