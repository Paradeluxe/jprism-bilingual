# -*- coding: utf-8 -*-
import pandas as pd

t = pd.read_csv('experiment/stats_mixed/results/barr_terms_selected.csv')
TAGS = ['gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-0.6b', 'qwen3-4b',
        'qwen3-8b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b', 'qwen3.5-9b',
        'qwen3.6-27b']
t = t[t.tag.isin(TAGS)]
OUT = [('share_en', 'English share'), ('share_zh', 'Chinese share'),
       ('share_ru', 'Russian share'), ('share_non', 'Non-language share'),
       ('blackout_pool', 'Pool blackout'), ('overlap', 'Semantic overlap')]
TERMS = [('lens_lang', 'Lens language'), ('prompt_lang', 'Prompt language'),
         ('item_type', 'Probe family'), ('prompt_lang:lens_lang', 'Lens \u00d7 prompt'),
         ('lens_lang:item_type', 'Lens \u00d7 probe family'),
         ('prompt_lang:item_type', 'Prompt \u00d7 probe family')]
OVER = [('sem_type', 'Overlap type'), ('prompt', 'Prompt language'), ('family', 'Probe family'),
        ('sem_type:prompt', 'Overlap type \u00d7 prompt'),
        ('sem_type:family', 'Overlap type \u00d7 probe family'),
        ('prompt:family', 'Prompt \u00d7 probe family')]


def fnum(x):
    return '{:,.0f}'.format(x)


def df2txt(lo, hi):
    return '%d' % lo if abs(hi - lo) < 1 else '%d\u2013%d' % (lo, hi)


def ptext(p):
    if p < .001:
        return '< .001'
    s = '%.3g' % p
    return '\u2264 ' + (s[1:] if s.startswith('0.') else s)


rows = []
for dv, out in OUT:
    terms = OVER if dv == 'overlap' else TERMS
    for eff, lab in terms:
        g = t[(t.dv == dv) & (t.effect == eff)]
        rows.append([out, lab, '%s\u2013%s' % (fnum(g.F.min()), fnum(g.F.max())),
                     '%d' % int(g.df1.iloc[0]), df2txt(g.df2.min(), g.df2.max()),
                     ptext(g.p.max()), '%d/11' % int((g.p < .05).sum())])
print(len(rows))
for r in rows[:8]:
    print(r)
