# -*- coding: utf-8 -*-
"""Significant results + simple effects, restricted to the eight non-quantized models."""
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
pd.set_option('display.width', 200)


def stars(p):
    return '***' if p < .001 else '**' if p < .01 else '*' if p < .05 else ''


print('=' * 100)
print('1. PER-MODEL SIGNIFICANCE (prompt / lens / interaction)')
print('=' * 100)
F = pd.read_csv('results/final_7dv_stats.csv')
F = F[F.tag.isin(B) & F.dv.str.startswith('share_')]
rows = []
for dv in ['share_en', 'share_zh', 'share_ru', 'share_other']:
    s = F[F.dv == dv]
    rows.append([dv] + ['%s%s' % ('%.0e' % g.p.values[0], stars(g.p.values[0]))
                        for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']
                        for g in [s[s.effect == e]]])
print(pd.DataFrame(rows, columns=['DV', 'prompt', 'lens', 'prompt x lens']).to_string(index=False))

T = pd.read_csv('results/pool_blackout_tests.csv')
T = T[T.tag.isin(B)]
agg = {}
for e in ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']:
    s = T[T.effect == e]
    agg[e] = '%d/8 sig (p %.1e-%.2g)' % (int((s.p < .05).sum()), s.p.min(), s.p.max())
print('\npool blackout:', agg)

O = pd.read_csv('results/overlap_tests.csv')
O = O[O.tag.isin(B) & (O.variant == 'stw') & (O.model == 'GLMM')]
for m in ['m1', 'm2', 'm3', 'm4']:
    s = O[O.measure == m]
    print('%-3s prompt %d/8 sig (chi2 %.0f-%.0f)' % (m, int((s.p < .05).sum()),
                                                     s.value.min(), s.value.max()))

print()
print('=' * 100)
print('2. SIMPLE EFFECTS: cell means (%) and pairwise prompt contrasts')
print('=' * 100)
C = pd.read_csv('results/cell_means_item.csv')
C = C[C.tag.isin(B)]
P = pd.read_csv('results/simple_pair_item.csv')
P = P[P.tag.isin(B)]
for dv in ['share_en', 'share_zh', 'share_ru']:
    cm = C[C.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
    print('\n## %s  (rows lens, columns prompt)' % dv)
    print(cm.reindex(LV)[['en', 'zh', 'ru']].round(1).to_string())
    s = P[P.dv == dv]
    for by, levels in (('lens_lang', LV), ('prompt_lang', LV)):
        for lv in levels:
            sub = s[(s['by'] == by) & (s.level == lv)]
            if sub.empty:
                continue
            out = []
            for c in ['en - zh', 'en - ru', 'zh - ru']:
                g = sub[sub.contrast == c]
                if g.empty:
                    continue
                out.append('%s: %d/8 sig, mean %+0.1f' % (c, int((g.p < .05).sum()),
                                                          g.estimate.mean()))
            print('   %s=%-2s  %s' % (by[:4], lv, ' | '.join(out)))

cm = C[C.dv == 'share_other'].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack() * 100
print('\n## share_other (rows lens, columns prompt)')
print(cm.reindex(LV)[['en', 'zh', 'ru']].round(1).to_string())

print()
print('=' * 100)
print('3. POOL BLACKOUT simple effects')
print('=' * 100)
Cb = pd.read_csv('results/pool_blackout_cells.csv')
Cb = Cb[Cb.tag.isin(B)]
cm = Cb.groupby(['lens_lang', 'prompt_lang'])['rate'].mean().unstack() * 100
print(cm.reindex(LV)[['en', 'zh', 'ru']].round(1).to_string())
Gb = pd.read_csv('results/pool_blackout_pair.csv')
Gb = Gb[Gb.tag.isin(B)]
for by in ['lens_lang', 'prompt_lang']:
    for lv in LV:
        sub = Gb[(Gb['by'] == by) & (Gb.level == lv)]
        if sub.empty:
            continue
        out = []
        for c in ['en - zh', 'en - ru', 'zh - ru']:
            g = sub[sub.contrast == c]
            if g.empty:
                continue
            out.append('%s: %d/8 sig' % (c, int((g.p < .05).sum())))
        print('   %s=%-2s  %s' % (by[:4], lv, ' | '.join(out)))

print()
print('=' * 100)
print('4. THREE-WAY OVERLAP: means and pairwise prompt contrasts')
print('=' * 100)
Co = pd.read_csv('results/overlap_cells.csv')
Co = Co[Co.tag.isin(B)]
cm = Co.groupby(['measure', 'prompt_lang'])['rate_stw'].mean().unstack() * 100
print(cm[['en', 'zh', 'ru']].round(1).to_string())
Po = pd.read_csv('results/overlap_pair.csv')
Po = Po[Po.tag.isin(B) & (Po.variant == 'stw')]
for m in ['m1', 'm2', 'm3', 'm4']:
    sub = Po[Po.measure == m]
    out = []
    for c in sub.contrast.unique():
        g = sub[sub.contrast == c]
        out.append('%s: %d/8 sig, mean %+0.3f' % (c, int((g.p < .05).sum()),
                                                  g.estimate.mean()))
    print('%-3s %s' % (m, ' | '.join(out)))
