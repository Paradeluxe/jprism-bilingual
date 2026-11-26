# -*- coding: utf-8 -*-
"""Which (tag, lens, prompt) cells sit at 0% or 100% for the candidate per-language
blackout definitions -> these are the separation-risk cells for a logistic GLMM."""
import glob
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bilingual_align as A  # noqa: E402

P300 = os.path.join(os.path.dirname(HERE), 'RESULT', 'PROBE300')
nrm, is_lang, lang_of = A.nrm, A._is_language, A._lang
TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']


def main():
    rows = []
    for tag in TAGS:
        for f in sorted(glob.glob(os.path.join(P300, 'PROBE300_%s_*_raw.json' % tag))):
            d = json.load(open(f, encoding='utf-8'))
            m = d['meta']
            cnt = {'en': 0, 'zh': 0, 'ru': 0}
            tot = {'A_en': 0, 'A_zh': 0, 'A_ru': 0, 'C_en': 0, 'C_zh': 0, 'C_ru': 0}
            n = 0
            for r in d['results']:
                for lay in r['layers']:
                    if lay['L'] == 0:
                        continue
                    top = lay['j_top100']
                    if len(top) != 100:
                        continue
                    toks = [nrm(t) for t in top]
                    c = {'en': 0, 'zh': 0, 'ru': 0}
                    for t in toks:
                        if is_lang(t):
                            L = lang_of(t)
                            if L in c:
                                c[L] += 1
                    n += 1
                    for x in ('en', 'zh', 'ru'):
                        top10 = any(is_lang(t) and lang_of(t) == x for t in toks[:10])
                        sh = c[x] / 100.0
                        tot['A_' + x] += 1 if ((not top10) and sh < 0.5) else 0
                        tot['C_' + x] += 1 if c[x] == 0 else 0
            rows.append(dict(tag=tag, lens=m['lens'], prompt=m['lang'], pools=n,
                             **{k: v / n for k, v in tot.items()}))
    df = pd.DataFrame(rows)
    for x in ('en', 'zh', 'ru'):
        for defn in ('A', 'C'):
            col = '%s_%s' % (defn, x)
            print('\n=== %s ===' % col)
            print('range %.3f - %.3f, mean %.3f' % (df[col].min(), df[col].max(), df[col].mean()))
            print('cells at 0%%: %d, at 100%%: %d' % ((df[col] == 0).sum(), (df[col] == 1).sum()))
            print('extreme cells:')
            print(df[(df[col] == 0) | (df[col] == 1)][['tag', 'lens', 'prompt', col]]
                  .to_string(index=False))
    df.to_csv(os.path.join(HERE, 'results', 'blackout_defs_cells.csv'), index=False)


if __name__ == '__main__':
    main()
