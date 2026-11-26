# -*- coding: utf-8 -*-
"""Per-DV direction report for the unified arcsine-LMM analyses."""
import pandas as pd

B = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
     'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LV = ['en', 'zh', 'ru']
FA = ['P1', 'P3', 'P4']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
out = []


def w(s=''):
    out.append(s)


def sig(df, dv, **kw):
    d = df[df.dv == dv]
    for k, v in kw.items():
        if k in d.columns:
            d = d[d[k] == v]
    return d


def pct(x):
    return 100.0 * x


# ---------------- data sources ----------------
C = pd.read_csv('results/full_cells.csv')          # shares: lens x prompt means
C = C[C.tag.isin(B)]
BO = pd.concat([pd.read_csv('results/pool_bo_lmm_cells.csv'),
                pd.read_csv('results/single_bo_lmm_cells.csv')])
BO = BO[BO.tag.isin(B)]
OV = pd.read_csv('results/overlap_cells.csv')
OV = OV[OV.tag.isin(B)]

STAR_T = pd.read_csv('results/star_tests.csv')     # shares (LMM saturated)
STAR_T = STAR_T[STAR_T.tag.isin(B)]
STAR_J = pd.read_csv('results/star_joint.csv')
STAR_J = STAR_J[STAR_J.tag.isin(B)]
STAR_P = pd.read_csv('results/star_pair.csv')
STAR_P = STAR_P[STAR_P.tag.isin(B)]

BO_T = pd.concat([pd.read_csv('results/pool_bo_lmm_tests.csv'),
                  pd.read_csv('results/single_bo_lmm_tests.csv')])
BO_T = BO_T[(BO_T.tag.isin(B)) & (BO_T.spec == 'saturated')]
BO_J = pd.concat([pd.read_csv('results/pool_bo_lmm_joint.csv'),
                  pd.read_csv('results/single_bo_lmm_joint.csv')])
BO_J = BO_J[(BO_J.tag.isin(B)) & (BO_J.spec == 'saturated')]
BO_P = pd.concat([pd.read_csv('results/pool_bo_lmm_pair.csv'),
                  pd.read_csv('results/single_bo_lmm_pair.csv')])
BO_P = BO_P[(BO_P.tag.isin(B)) & (BO_P.spec == 'saturated')]

OV_T = pd.read_csv('results/overlap_lmm_tests.csv')
OV_T = OV_T[OV_T.tag.isin(B)]
OV_J = pd.read_csv('results/overlap_lmm_joint.csv')
OV_J = OV_J[OV_J.tag.isin(B)]
OV_P = pd.read_csv('results/overlap_lmm_pair.csv')
OV_P = OV_P[OV_P.tag.isin(B)]

IT = pd.read_csv('data/item_level_core.csv')
IT = IT[IT.tag.isin(B)]
EX = pd.read_csv('data/blackout_exclusive.csv')
EX = EX[EX.tag.isin(B)]
OI = pd.read_csv('data/overlap_item.csv')
OI = OI[OI.tag.isin(B)]

NAMES = {'share_en': 'English share', 'share_zh': 'Chinese share',
         'share_ru': 'Russian share', 'share_other': 'Other-language share',
         'blackout_pool': 'Pool blackout', 'blackout_excl': 'Single blackout',
         'blackout_alive': 'Single survivor', 'm1': 'Overlap m1',
         'm2': 'Overlap m2', 'm3': 'Overlap m3', 'm4': 'Overlap m4'}

w('# Direction of every significant effect, per dependent variable')
w()

for dv in ['share_en', 'share_zh', 'share_ru', 'share_other',
           'blackout_pool', 'blackout_excl', 'blackout_alive',
           'm1', 'm2', 'm3', 'm4']:
    w('## %s (`%s`)' % (NAMES[dv], dv))
    w()
    if dv.startswith('share') or dv.startswith('blackout'):
        cells = C if dv.startswith('share') else BO
        pm = cells[cells.dv == dv].groupby(['lens_lang', 'prompt_lang'])['mean'].mean().unstack()
        w('Cells (%):')
        w()
        w('| lens \\ prompt | EN | ZH | RU |')
        w('| --- | --- | --- | --- |')
        for lens in LV:
            w('| %s | %s |' % (LAB[lens], ' | '.join('%.1f' % pct(pm.loc[lens, p]) for p in LV)))
        w()
        if dv.startswith('share'):
            b = dv.split('_')[1]
            fam = IT.groupby('item_type')['sh_' + b].mean()
            T, J, P = STAR_T, STAR_J, STAR_P
        else:
            col = {'blackout_pool': 'blackout_rate', 'blackout_excl': 'rate',
                   'blackout_alive': 'rate_alive'}[dv]
            fam = EX.groupby('item_type')[col].mean()
            T, J, P = BO_T, BO_J, BO_P
        w('- family means: %s' % ', '.join('%s %.1f' % (k, pct(fam[k])) for k in FA))
        terms = sig(T, dv)
        w('- significant terms: %s' % ', '.join(
            '%s %d/8' % (e, int((g.p < .05).sum()))
            for e, g in terms.groupby('effect')
            if e in ('prompt_lang', 'lens_lang', 'item_type',
                     'prompt_lang:lens_lang', 'prompt_lang:item_type',
                     'lens_lang:item_type', 'prompt_lang:lens_lang:item_type')))
        for by, term, nm in [('lens_lang', 'prompt_lang', 'prompt | lens'),
                             ('prompt_lang', 'lens_lang', 'lens | prompt'),
                             ('item_type', 'prompt_lang', 'prompt | family')]:
            sub = J[(J.dv == dv) & (J['by'] == by) & (J.term == term)]
            if len(sub):
                w('- %s: %s' % (nm, '; '.join('%s %d/8' % (LAB.get(lv, lv),
                                                          int((g.p < .05).sum()))
                                              for lv, g in sub.groupby('level'))))
        for lens in LV:
            sub = P[(P.dv == dv) & (P.level == lens)]
            if not len(sub):
                continue
            bits = []
            for c in ['en - zh', 'en - ru', 'ru - zh']:
                g = sub[sub.contrast == c]
                if g.empty:
                    continue
                a, b2 = [x.strip() for x in c.split('-')]
                d = pct(pm.loc[lens, a] - pm.loc[lens, b2])
                bits.append('%s %+0.1f pp (%d/8)' % (
                    LAB[a] + (' > ' if d > 0 else ' < ') + LAB[b2], abs(d),
                    int((g.p < .05).sum())))
            w('- within %s lens: %s' % (LAB[lens], '; '.join(bits)))
    else:
        pm = OV[OV.measure == dv].groupby('prompt_lang')['rate_stw'].mean()
        w('- prompt means: %s' % ', '.join('%s %.1f' % (LAB[p], pct(pm[p])) for p in LV))
        fam = OI.groupby('item_type')[dv + '_stw_rate'].mean()
        w('- family means: %s' % ', '.join('%s %.1f' % (k, pct(fam[k])) for k in FA))
        terms = sig(OV_T, dv)
        w('- significant terms: %s' % ', '.join(
            '%s %d/8' % (e, int((g.p < .05).sum()))
            for e, g in terms.groupby('effect')
            if e in ('prompt_lang', 'item_type', 'prompt_lang:item_type')))
        sub = OV_J[(OV_J.dv == dv) & (OV_J.term == 'prompt_lang')]
        if len(sub):
            w('- prompt | family: %s' % '; '.join(
                '%s %d/8' % (lv, int((g.p < .05).sum())) for lv, g in sub.groupby('level')))
        bits = []
        for c in ['en - zh', 'en - ru', 'ru - zh']:
            g = OV_P[(OV_P.dv == dv) & (OV_P.contrast == c)]
            if g.empty:
                continue
            a, b2 = [x.strip() for x in c.split('-')]
            d = pct(pm[a] - pm[b2])
            bits.append('%s %+0.1f pp (%d/8)' % (
                LAB[a] + (' > ' if d > 0 else ' < ') + LAB[b2], abs(d),
                int((g.p < .05).sum())))
        w('- pairwise: %s' % '; '.join(bits))
    w()

open('results/direction_by_dv.md', 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(out) + '\n')
print('\n'.join(out))
