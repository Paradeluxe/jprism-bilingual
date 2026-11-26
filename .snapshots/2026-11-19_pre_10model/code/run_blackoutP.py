# -*- coding: utf-8 -*-
"""Per-language blackout with the user's per-layer criterion, then fit the three DVs.

Per-layer criterion (as specified):
    top-10 candidates are ALL non-language (no letter at all)
    AND  <share condition>

The literal second condition is the non-language share of the top-100 < 50%, but that is
language-agnostic (it yields ONE flag per layer, not three).  To get the three
language-specific DVs ("EN / CN / RUS 三种 blackout") the share condition is applied per
language band:  share_X(top-100) < 50%.

Both are computed so the difference is visible:
    boP_X : dark10 AND share_X   < 0.50      <- language-specific (primary)
    boN   : dark10 AND share_non < 0.50      <- literal, language-agnostic (one DV)

Item-level DV = (# layers meeting the criterion) / n_layers; fitted as binomial GLMM on
cbind(k, n_layers - k) ~ prompt_lang * lens_lang + (1 | item).

NOTE: every share used here is the TOP-100 pool share, not top-5 / top-10.  The top-10 is
used only for the "dark at the consulted depth" condition.
"""
import glob
import json
import os
import sys
import time

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, EXP)
sys.path.insert(0, HERE)
import bilingual_align as A  # noqa: E402

from ezlmm_pinned import PinnedGeneralizedLinearMixedModel, set_sum_contrasts  # noqa: E402

nrm, is_lang, lang_of = A.nrm, A._is_language, A._lang
P300 = os.path.join(EXP, 'RESULT', 'PROBE300')
TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
LANGS = ['en', 'zh', 'ru']
_cache = {}


def classify(tok):
    c = _cache.get(tok)
    if c is None:
        letter = is_lang(tok)
        c = (letter, lang_of(tok) if letter else None)
        _cache[tok] = c
    return c


def build():
    rows = []
    for tag in TAGS:
        for f in sorted(glob.glob(os.path.join(P300, 'PROBE300_%s_*_raw.json' % tag))):
            base = os.path.basename(f)[len('PROBE300_'):-len('_raw.json')]
            _, lens, prompt = base.rsplit('_', 2)
            d = json.load(open(f, encoding='utf-8'))
            for r in d['results']:
                cnt_layers = 0
                acc = {k: 0.0 for k in
                       ['boP_en', 'boP_zh', 'boP_ru', 'boN']}
                for lay in r['layers']:
                    if lay['L'] == 0:
                        continue
                    top = lay['j_top100']
                    if len(top) != 100:
                        continue
                    cnt_layers += 1
                    cls = [classify(nrm(t)) for t in top]
                    band = {'en': 0, 'zh': 0, 'ru': 0, 'non': 0}
                    for letter, lang in cls:
                        if not letter:
                            band['non'] += 1
                        elif lang in ('en', 'zh', 'ru'):
                            band[lang] += 1
                    dark10 = not any(letter for letter, _ in cls[:10])
                    if not dark10:
                        continue
                    for x in LANGS:
                        if band[x] / 100.0 < 0.5:
                            acc['boP_' + x] += 1
                    if band['non'] / 100.0 < 0.5:
                        acc['boN'] += 1
                if cnt_layers == 0:
                    continue
                rec = dict(tag=tag, lens_lang=lens, prompt_lang=prompt,
                           item_type=r['type'], item_idx=r['idx'],
                           item_key=r['key'], n_layers=cnt_layers)
                for k, v in acc.items():
                    rec[k] = v / cnt_layers
                    if k != 'boN':
                        rec['n_' + k] = int(v)
                rec['n_boN'] = int(acc['boN'])
                rows.append(rec)
    df = pd.DataFrame(rows)
    df['lens_lang'] = df['lens_lang'].replace({'wikitext': 'en', 'zhwiki': 'zh', 'ruwiki': 'ru'})
    df.to_csv(os.path.join(HERE, 'data', 'blackoutP.csv'), index=False)
    print('rows', len(df), 'tags', df.tag.nunique())
    print('mean boP:', df[['boP_en', 'boP_zh', 'boP_ru']].mean().round(3).to_dict())
    print('mean boN (literal, language-agnostic):', round(df.boN.mean(), 3))
    return df


def fit(df):
    set_sum_contrasts()
    tests = []
    for tag in TAGS:
        d = df[df.tag == tag].copy()
        d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=['en', 'zh', 'ru'])
        d['lens_lang'] = pd.Categorical(d.lens_lang, categories=['en', 'zh', 'ru'])
        d['item'] = d['item_type'] + '_' + d['item_idx'].astype(str)
        for x in LANGS:
            d['rest_' + x] = d['n_layers'] - d['n_boP_' + x]
            g = PinnedGeneralizedLinearMixedModel()
            g.data = d.copy()
            g.dep_var = 'cbind(n_boP_%s, rest_%s)' % (x, x)
            g.indep_var = ['prompt_lang', 'lens_lang']
            g.random_var = ['item']
            g.fit_pinned('%s ~ prompt_lang * lens_lang + (1 | item)' % g.dep_var,
                         family='binomial')
            for effect, r in g.anova.iterrows():
                if str(effect).startswith('(Intercept)'):
                    continue
                tests.append(dict(tag=tag, dv='boP_' + x, effect=str(effect),
                                  stat='Chisq', value=float(r['Chisq']),
                                  df=float(r['Df']), p=float(r['Pr(>Chisq)']),
                                  converged=g.converged()))
            g.model_r = None
        print('fitted', tag, flush=True)
    t = pd.DataFrame(tests)
    t.to_csv(os.path.join(HERE, 'results', 'blackoutP_tests.csv'), index=False)
    print('\n=== significance counts (p<.05) across 9 models ===')
    print(t.groupby(['dv', 'effect']).p.apply(lambda s: '%d/9' % int((s < .05).sum())).to_string())
    print('\n=== p per model ===')
    for x in LANGS:
        sub = t[t.dv == 'boP_' + x].pivot_table(index='tag', columns='effect', values='p')
        print('\n-- boP_' + x)
        print(sub.map(lambda v: '%.1e' % v if v < 1e-3 else '%.3f' % v).to_string())
    return t


if __name__ == '__main__':
    t0 = time.time()
    df = build()
    fit(df)
    print('\nelapsed %.0fs' % (time.time() - t0))
