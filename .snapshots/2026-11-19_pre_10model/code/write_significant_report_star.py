# -*- coding: utf-8 -*-
"""Summary of the saturated models prompt * lens * probe family."""
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
TERMS = [('prompt_lang', 'prompt'), ('lens_lang', 'lens'), ('item_type', 'family'),
         ('prompt_lang:lens_lang', 'prompt x lens'),
         ('prompt_lang:item_type', 'prompt x family'),
         ('lens_lang:item_type', 'lens x family'),
         ('prompt_lang:lens_lang:item_type', 'prompt x lens x family')]
DVS = ['share_en', 'share_zh', 'share_ru', 'share_other', 'blackout_pool',
       'm1', 'm2', 'm3', 'm4']
out = []


def w(s=''):
    out.append(s)


T = pd.read_csv('results/star_tests.csv')
J = pd.read_csv('results/star_joint.csv')
P = pd.read_csv('results/star_pair.csv')
C = pd.read_csv('results/full_cells.csv')
T, J, P, C = [x[x.tag.isin(B)] for x in (T, J, P, C)]

w('# Saturated models: prompt * lens * probe family')
w()
w('```')
w('arcsin(share)   ~ PromptLanguage * LensLanguage * ProbeFamily + (1 | Probe)')
w('BlackoutRate    ~ PromptLanguage * LensLanguage * ProbeFamily + (1 | Probe)')
w('SemanticOverlap ~ PromptLanguage * ProbeFamily + (1 | Probe)')
w('```')
w()

w('## 1. Type III tests (n/8 models significant)')
w()
w('| DV | ' + ' | '.join(n for _, n in TERMS) + ' |')
w('| --- |' + ' --- |' * len(TERMS))
for dv in DVS:
    s = T[T.dv == dv]
    cells = []
    for e, _ in TERMS:
        g = s[s.effect == e]
        cells.append('-' if g.empty else '%d/8' % int((g.p < .05).sum()))
    w('| %s | %s |' % (dv, ' | '.join(cells)))
w()

w('## 2. Language shares: cell means (%) and simple effects')
w()
for dv in ['share_en', 'share_zh', 'share_ru']:
    cm = C[C.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
    w('### %s' % dv)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % cm.loc[lens, p] for p in LV)))
    w()
    for by, term, nm in [('lens_lang', 'prompt_lang', 'prompt | lens'),
                         ('prompt_lang', 'lens_lang', 'lens | prompt'),
                         ('item_type', 'prompt_lang', 'prompt | family')]:
        sub = J[(J.dv == dv) & (J['by'] == by) & (J.term == term)]
        w('- %s: %s' % (nm, '; '.join('%s %d/8' % (lv, int((g.p < .05).sum()))
                                      for lv, g in sub.groupby('level'))))
    sub = P[P.dv == dv]
    for lv in LV:
        g = sub[sub.level == lv]
        if len(g):
            w('- pairwise within %s lens: %s' % (LAB[lv], '; '.join(
                '%s %d/8' % (c, int((x.p < .05).sum())) for c, x in g.groupby('contrast'))))
    w()

w('## 3. Pool blackout')
w()
cm = C[C.dv == 'blackout_pool'].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
w('| lens \\ prompt | EN | ZH | RU |')
w('| --- | --- | --- | --- |')
for lens in LV:
    w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % cm.loc[lens, p] for p in LV)))
w()
for by, term, nm in [('lens_lang', 'prompt_lang', 'prompt | lens'),
                     ('prompt_lang', 'lens_lang', 'lens | prompt'),
                     ('item_type', 'prompt_lang', 'prompt | family')]:
    sub = J[(J.dv == 'blackout_pool') & (J['by'] == by) & (J.term == term)]
    w('- %s: %s' % (nm, '; '.join('%s %d/8' % (lv, int((g.p < .05).sum()))
                                  for lv, g in sub.groupby('level'))))
w()
w('*Caveat*: the saturated blackout model has lens x prompt cells with zero blackout '
  'layers in every model (4-9 of the 9 cells), so the pooled lower-order terms are '
  'poorly estimated (separation); the family-interaction terms remain significant in '
  '6/8 models.')
w()

w('## 4. Three-way overlap')
w()
cm = C[C.dv.isin(['m1', 'm2', 'm3', 'm4'])].groupby(['dv', 'prompt_lang'])['mean'].mean().unstack() * 100
w('| measure | EN prompt | ZH prompt | RU prompt |')
w('| --- | --- | --- | --- |')
for m in ['m1', 'm2', 'm3', 'm4']:
    w('| %s | %s |' % (m, ' | '.join('%.1f' % cm.loc[m, p] for p in LV)))
w()
for m in ['m1', 'm2', 'm3', 'm4']:
    sub = P[P.dv == m]
    w('- %s pairwise: %s' % (m, '; '.join('%s %d/8' % (c, int((g.p < .05).sum()))
                                         for c, g in sub.groupby('contrast'))))

open('results/significant_summary_star_models.md', 'w', encoding='utf-8',
     newline='\n').write('\n'.join(out) + '\n')
print('wrote results/significant_summary_star_models.md')
