# -*- coding: utf-8 -*-
"""Build the ITEM-LEVEL table the analysis wants.

**All language shares in this table are computed over the TOP-100 candidate pool
(`j_top100`, 100 decoded candidates), NOT over top-5 or top-10.**  The top-10 is used only
inside the language-blackout criterion ("is the language readable at the depth a user would
consult"), never for the four share DVs.

Unit of observation = (tag, prompt_lang, lens_lang, item)  -> 300 items x 9 cells = 2700
rows per model.  Per item:

  share_en / share_zh / share_ru / share_other / share_non
        TOP-100 band share of each measured layer, averaged over the measured layers
        (layer 0 excluded by default; --keep-l0 to include)
  boA_en / boA_zh / boA_ru
        proportion of measured layers in which language X is "blacked out" under the
        mirrored paper criterion: no X token in the top-10 AND share_X < 0.50
  boP_en / boP_zh / boP_ru
        **the user's per-language criterion**: top-10 candidates are all non-language
        (no letter) AND language X's TOP-100 share < 50%
  boC_en / boC_zh / boC_ru
        proportion of layers where the X band is empty (share_X == 0)
  bo10_en / bo10_zh / bo10_ru
        proportion of layers where the top-10 has no X token (no share condition)
  pool_blackout
        proportion of layers meeting the original pool-level criterion
        (top-10 has no letters at all AND non-language share >= 0.50)
  n_layers
        denominator used above
  pool_topk
        constant 100: marks that every share was computed on the top-100 pool

Output: data/item_level.parquet (+ csv.gz fallback)
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, EXP)
import bilingual_align as A  # noqa: E402

nrm, is_lang, lang_of = A.nrm, A._is_language, A._lang
P300 = os.path.join(EXP, 'RESULT', 'PROBE300')
LANGS = ('en', 'zh', 'ru')

_cache = {}


def classify(tok):
    """(is_letter, language) for a normalised token, memoised (vocab repeats a lot)."""
    c = _cache.get(tok)
    if c is None:
        letter = is_lang(tok)
        c = (letter, lang_of(tok) if letter else None)
        _cache[tok] = c
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'data', 'item_level.parquet'))
    ap.add_argument('--keep-l0', action='store_true')
    args = ap.parse_args()

    rows = []
    files = sorted(glob.glob(os.path.join(P300, 'PROBE300_*_raw.json')))
    core_tags = None
    for fi, f in enumerate(files):
        base = os.path.basename(f)[len('PROBE300_'):-len('_raw.json')]
        tag, lens, prompt = base.rsplit('_', 2)
        if core_tags is None:
            core_tags = set()
        d = json.load(open(f, encoding='utf-8'))
        m = d['meta']
        for r in d['results']:
            per_item = []
            for lay in r['layers']:
                if lay['L'] == 0 and not args.keep_l0:
                    continue
                top = lay['j_top100']
                if len(top) != 100:
                    continue
                toks = [nrm(t) for t in top]
                cls = [classify(t) for t in toks]
                cnt = {'en': 0, 'zh': 0, 'ru': 0, 'other': 0, 'non': 0}
                for letter, lang in cls:
                    if not letter:
                        cnt['non'] += 1
                    elif lang in ('en', 'zh', 'ru'):
                        cnt[lang] += 1
                    else:
                        cnt['other'] += 1
                top10 = [c for c in cls[:10]]
                rec = {}
                for x in LANGS:
                    in_top10 = any(letter and lang == x for letter, lang in top10)
                    rec['bo10_' + x] = 0.0 if in_top10 else 1.0
                    rec['boA_' + x] = 1.0 if ((not in_top10) and cnt[x] / 100.0 < 0.5) else 0.0
                    rec['boC_' + x] = 1.0 if cnt[x] == 0 else 0.0
                dark10 = not any(letter for letter, _ in top10)
                rec['pool_blackout'] = 1.0 if (dark10 and cnt['non'] / 100.0 >= 0.5) else 0.0
                for k, v in cnt.items():
                    rec['sh_' + k] = v / 100.0
                rec['layer'] = lay['L']
                per_item.append(rec)
            if not per_item:
                continue
            df = pd.DataFrame(per_item)
            out = dict(tag=tag, lens_lang=lens, prompt_lang=prompt,
                       item_type=r['type'], item_idx=r['idx'],
                       item_key=r['key'], n_layers=len(df))
            for k in ['sh_en', 'sh_zh', 'sh_ru', 'sh_other', 'sh_non',
                      'bo10_en', 'bo10_zh', 'bo10_ru',
                      'boA_en', 'boA_zh', 'boA_ru',
                      'boC_en', 'boC_zh', 'boC_ru', 'pool_blackout']:
                out[k] = float(df[k].mean())
            for x in LANGS:
                out['n_boA_' + x] = int(round(out['boA_' + x] * len(df)))
                out['n_boC_' + x] = int(round(out['boC_' + x] * len(df)))
            rows.append(out)
        if fi % 20 == 0:
            print('  %d/%d files' % (fi + 1, len(files)), flush=True)

    item = pd.DataFrame(rows)
    item['lens_lang'] = item['lens_lang'].replace({'wikitext': 'en', 'zhwiki': 'zh', 'ruwiki': 'ru'})
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    try:
        item.to_parquet(args.out, index=False)
    except Exception:
        item.to_pickle(args.out.replace('.parquet', '.pkl'))
    print('rows: %d  tags: %d  cells/tag: %d  items/cell: %d' % (
        len(item), item.tag.nunique(),
        item.groupby('tag').apply(lambda d: d.groupby(['lens_lang', 'prompt_lang']).ngroups,
                                  include_groups=False).max(),
        item.groupby(['tag', 'lens_lang', 'prompt_lang']).size().max()))
    print('mean band shares:', item[['sh_en', 'sh_zh', 'sh_ru', 'sh_other', 'sh_non']].mean().round(3).to_dict())
    print('mean blackout A:', item[['boA_en', 'boA_zh', 'boA_ru']].mean().round(3).to_dict())
    print('mean blackout C:', item[['boC_en', 'boC_zh', 'boC_ru']].mean().round(3).to_dict())
    print('mechanism check (paper pool-level):', round(item.pool_blackout.mean(), 3))
    print('wrote', args.out)


if __name__ == '__main__':
    main()
