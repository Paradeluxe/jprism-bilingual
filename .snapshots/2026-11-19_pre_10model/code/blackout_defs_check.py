# -*- coding: utf-8 -*-
"""Prevalence of three candidate per-language blackout definitions.

A (mirror of the paper's pool-level definition):
    blackout_X = (no top-10 candidate in language X) AND (share_X < 0.50)
B (strict): no top-10 candidate in X AND share_X == 0
C (band empty): share_X == 0 anywhere in the pool

Reports per tag x lens x prompt the rate for X in {en, zh, ru}, so we can see which
definition has usable variation (not all-0 / all-1 cells -> separation risk).
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))   # experiment/ for bilingual_align
import bilingual_align as A  # noqa: E402

P300 = os.path.join(os.path.dirname(HERE), 'RESULT', 'PROBE300')
nrm, is_lang, lang_of = A.nrm, A._is_language, A._lang

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
LANGS = ['en', 'zh', 'ru']


def rows_for(tag):
    import json
    import glob
    out = []
    for f in sorted(glob.glob(os.path.join(P300, 'PROBE300_%s_*_raw.json' % tag))):
        d = json.load(open(f, encoding='utf-8'))
        m = d['meta']
        for r in d['results']:
            for lay in r['layers']:
                if lay['L'] == 0:
                    continue
                top = lay['j_top100']
                if len(top) != 100:
                    continue
                toks = [nrm(t) for t in top]
                cnt = {'en': 0, 'zh': 0, 'ru': 0}
                for t in toks:
                    if is_lang(t):
                        L = lang_of(t)
                        if L in cnt:
                            cnt[L] += 1
                rec = {'tag': tag, 'lens': m['lens'], 'prompt': m['lang']}
                for x in LANGS:
                    top10_x = any(is_lang(t) and lang_of(t) == x for t in toks[:10])
                    sh = cnt[x] / 100.0
                    rec['A_' + x] = (0 if top10_x else 1) * (1 if sh < 0.5 else 0)
                    rec['B_' + x] = (0 if top10_x else 1) * (1 if cnt[x] == 0 else 0)
                    rec['C_' + x] = 1 if cnt[x] == 0 else 0
                out.append(rec)
    return pd.DataFrame(out)


def main():
    frames = [rows_for(t) for t in TAGS]
    df = pd.concat(frames, ignore_index=True)
    print('pools:', len(df), 'tags:', df.tag.nunique())
    for x in LANGS:
        for defn in ['A', 'B', 'C']:
            col = '%s_%s' % (defn, x)
            t = df.pivot_table(index='lens', columns='prompt', values=col,
                               aggfunc='mean')
            t = t.reindex(index=['wikitext', 'zhwiki', 'ruwiki'], columns=['en', 'zh', 'ru'])
            print('\n=== definition %s, language %s (rate; row=lens, col=prompt) ===' % (defn, x))
            print((100 * t).round(1).to_string())
    # per-tag detail for the chosen candidates
    for defn in ['A', 'B', 'C']:
        for x in LANGS:
            col = '%s_%s' % (defn, x)
            g = df.groupby('tag')[col].agg(['min', 'max', 'mean'])
            print('\n[%s_%s] per-tag range: min=%.3f max=%.3f mean=%.3f' % (
                defn, x, g['min'].min(), g['max'].max(), df[col].mean()))


if __name__ == '__main__':
    main()
