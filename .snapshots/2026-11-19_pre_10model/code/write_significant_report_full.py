# -*- coding: utf-8 -*-
"""Significant-results summary for the FULL models (probe family in the fixed part).

Reads results/full_tests.csv, full_joint.csv, full_pair.csv, full_cells.csv and
writes results/significant_summary_full_models.md.
"""
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
DVS = ['share_en', 'share_zh', 'share_ru', 'share_other', 'blackout_pool',
       'm1', 'm2', 'm3', 'm4']
out = []


def w(s=''):
    out.append(s)


T = pd.read_csv('results/full_tests.csv')
J = pd.read_csv('results/full_joint.csv')
P = pd.read_csv('results/full_pair.csv')
C = pd.read_csv('results/full_cells.csv')
T, J, P, C = [x[x.tag.isin(B)] for x in (T, J, P, C)]

w('# Significant results, full models (probe family in the fixed part)')
w()
w('Models: Qwen3-0.6B, Qwen3-4B, Qwen3-14B, Qwen3.5-0.8B, Qwen3.5-2B, '
  'Gemma-4-E2B, Gemma-4-E4B, Gemma-4-12B.')
w()
w('Model formulas:')
w()
w('```')
w('arcsin(share)  ~ PromptLanguage * LensLanguage + ProbeFamily + (1 | Probe)')
w('BlackoutRate   ~ PromptLanguage * LensLanguage + ProbeFamily + (1 | Probe)   [binomial]')
w('SemanticOverlap~ PromptLanguage + ProbeFamily + (1 | Probe)                  [binomial]')
w('```')
w()

w('## 1. Type III tests')
w()
w('| DV | prompt | lens | prompt x lens | probe family |')
w('| --- | --- | --- | --- | --- |')
for dv in DVS:
    s = T[T.dv == dv]
    cells = []
    for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang', 'item_type']:
        g = s[s.effect == e]
        cells.append('-' if g.empty else '%d/8' % int((g.p < .05).sum()))
    w('| %s | %s |' % (dv, ' | '.join(cells)))
w()
for dv in DVS:
    s = T[(T.dv == dv)]
    ns = {}
    for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang', 'item_type']:
        g = s[(s.effect == e) & (s.p >= .05)]
        if len(g):
            ns[e] = ', '.join(g.tag)
    if ns:
        w('- %s non-significant: %s' % (dv, '; '.join('%s (%s)' % (k, v)
                                                      for k, v in ns.items())))
w()

w('## 2. Simple effects, language shares (mean cell value, % of top-100)')
w()
for dv in ['share_en', 'share_zh', 'share_ru', 'share_other']:
    cm = C[C.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
    cm = cm.reindex(LV)[['en', 'zh', 'ru']].round(1)
    w('### %s' % dv)
    w()
    w('| lens \\ prompt | EN | ZH | RU |')
    w('| --- | --- | --- | --- |')
    for lens in LV:
        w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % cm.loc[lens, p] for p in LV)))
    w()
    jsp = J[(J.dv == dv) & (J['by'] == 'lens_lang') & (J.term == 'prompt_lang')]
    jsl = J[(J.dv == dv) & (J['by'] == 'prompt_lang') & (J.term == 'lens_lang')]
    w('- prompt effect within lens: ' + '; '.join(
        '%s %d/8' % (LAB[lv], int((g.p < .05).sum())) for lv, g in jsp.groupby('level')))
    w('- lens effect within prompt: ' + '; '.join(
        '%s %d/8' % (LAB[lv], int((g.p < .05).sum())) for lv, g in jsl.groupby('level')))
    s = P[P.dv == dv]
    for by, nm in [('lens_lang', 'within lens'), ('prompt_lang', 'within prompt')]:
        for lv in LV:
            sub = s[(s['by'] == by) & (s.level == lv)]
            if sub.empty:
                continue
            w('- %s=%s: %s' % (nm, LAB[lv], '; '.join(
                '%s %d/8' % (c, int((g.p < .05).sum()))
                for c, g in sub.groupby('contrast'))))
    w()

w('## 3. Simple effects, pool blackout (mean rate, % of measured layers)')
w()
cm = C[C.dv == 'blackout_pool'].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
cm = cm.reindex(LV)[['en', 'zh', 'ru']].round(1)
w('| lens \\ prompt | EN | ZH | RU |')
w('| --- | --- | --- | --- |')
for lens in LV:
    w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % cm.loc[lens, p] for p in LV)))
w()
jsp = J[(J.dv == 'blackout_pool') & (J['by'] == 'lens_lang') & (J.term == 'prompt_lang')]
jsl = J[(J.dv == 'blackout_pool') & (J['by'] == 'prompt_lang') & (J.term == 'lens_lang')]
w('- prompt effect within lens: ' + '; '.join(
    '%s %d/8' % (LAB[lv], int((g.p < .05).sum())) for lv, g in jsp.groupby('level')))
w('- lens effect within prompt: ' + '; '.join(
    '%s %d/8' % (LAB[lv], int((g.p < .05).sum())) for lv, g in jsl.groupby('level')))
s = P[P.dv == 'blackout_pool']
for by, nm in [('lens_lang', 'within lens'), ('prompt_lang', 'within prompt')]:
    for lv in LV:
        sub = s[(s['by'] == by) & (s.level == lv)]
        if sub.empty:
            continue
        w('- %s=%s: %s' % (nm, LAB[lv], '; '.join(
            '%s %d/8' % (c, int((g.p < .05).sum()))
            for c, g in sub.groupby('contrast'))))
w()

w('## 4. Three-way overlap (probe family in the fixed part)')
w()
cm = C[C.dv.isin(['m1', 'm2', 'm3', 'm4'])].groupby(['dv', 'prompt_lang'])['mean'].mean().unstack() * 100
w('| measure | EN prompt | ZH prompt | RU prompt |')
w('| --- | --- | --- | --- |')
for m in ['m1', 'm2', 'm3', 'm4']:
    w('| %s | %s |' % (m, ' | '.join('%.1f' % cm.loc[m, p] for p in LV)))
w()
for m in ['m1', 'm2', 'm3', 'm4']:
    sub = P[P.dv == m]
    w('- %s: %s' % (m, '; '.join('%s %d/8' % (c, int((g.p < .05).sum()))
                                 for c, g in sub.groupby('contrast'))))

open('results/significant_summary_full_models.md', 'w', encoding='utf-8',
     newline='\n').write('\n'.join(out) + '\n')
print('wrote results/significant_summary_full_models.md')
