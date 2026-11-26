# -*- coding: utf-8 -*-
import pandas as pd

RES = 'experiment/stats_mixed/results/'
TAGS = ['gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-0.6b', 'qwen3-4b',
        'qwen3-8b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b', 'qwen3.5-9b',
        'qwen3.6-27b']
N = 11
S = pd.read_csv(RES + 'barr_simple_interactions.csv')
C = pd.read_csv(RES + 'barr_contrasts.csv')
M = pd.read_csv(RES + 'barr_cell_means.csv')
for d in (S, C, M):
    d.drop(d[~d.tag.isin(TAGS)].index, inplace=True)

FAM = {'P1': 'country–capital', 'P3': 'definitional', 'P4': 'category–clue'}
LENS = {'en': 'English lens', 'zh': 'Chinese lens', 'ru': 'Russian lens'}
TYPE = {'cross': 'Cross-language unordered', 'cross_ordered': 'Cross-language ordered',
        'identical': 'Identical-string unordered', 'identical_ordered': 'Identical-string ordered'}
PROMPT = {'en': 'English', 'zh': 'Chinese', 'ru': 'Russian'}


def fnum(x):
    return '{:,.0f}'.format(x)


print('== simple lens x prompt within family')
for dv in ['share_en', 'share_zh', 'share_ru', 'share_non', 'blackout_pool']:
    g = S[(S.dv == dv) & (S.by == 'item_type') & (S.term == 'prompt_lang:lens_lang')]
    for fam in ['P1', 'P3', 'P4']:
        h = g[g.by_level == fam]
        print(dv, fam, 'F %.0f-%.0f' % (h.F.min(), h.F.max()), 'df2 %d-%d' % (h.df2.min(), h.df2.max()),
              'pmax %.3g' % h.p.max(), 'k', int((h.p < .05).sum()))
g = S[(S.dv == 'overlap') & (S.by == 'family') & (S.term == 'sem_type:prompt')]
for fam in ['P1', 'P3', 'P4']:
    h = g[g.by_level == fam]
    print('overlap', fam, 'F %.0f-%.0f' % (h.F.min(), h.F.max()), 'df2 %d-%d' % (h.df2.min(), h.df2.max()),
          'pmax %.3g' % h.p.max(), 'k', int((h.p < .05).sum()))

print('\n== prompt contrasts within lens/family or type/family')
for dv, focus, con, cells in [
        ('share_en', 'prompt_lang', ['en - ru', 'en - zh', 'ru - zh'], None),
        ('share_zh', 'prompt_lang', ['en - ru', 'en - zh', 'ru - zh'], None),
        ('share_ru', 'prompt_lang', ['en - ru', 'en - zh', 'ru - zh'], None),
        ('share_non', 'prompt_lang', ['en - ru', 'en - zh', 'ru - zh'], None),
        ('blackout_pool', 'prompt_lang', ['en - ru', 'en - zh', 'ru - zh'], None),
        ('overlap', 'prompt', ['en - ru', 'en - zh', 'ru - zh'], None)]:
    print('==', dv)
    h = C[(C.dv == dv) & (C.focus == focus) & (C.by == 'cell')]
    levels = sorted(h.by_level.unique())
    print('levels', levels[:3], '... n', len(levels))
    for conx in con:
        r = h[h.contrast == conx]
        cnt = r.groupby('by_level').apply(lambda x: int((x.p < .05).sum()))
        full = [x for x in levels if cnt.get(x, 0) == N]
        exc = [x for x in levels if cnt.get(x, 0) < N]
        print(conx, 'full', len(full), '/', len(levels), 'exc', [(x, int(cnt[x])) for x in exc])
        print('  pmin/max', r.p.min(), r.p.max())
        for x in full[:3]:
            print('  full e.g.', x)
