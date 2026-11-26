# -*- coding: utf-8 -*-
"""Exclusive language blackout: at a layer, lens X's pool is the ONLY one blacked out.

Per-layer pool-level blackout (the criterion just adopted):
    top-10 candidates all non-language (no letter) AND non-language share of the TOP-100
    pool >= 50%

For each (tag, prompt language, item, layer) the three lens pools (wikitext=EN, zhwiki=ZH,
ruwiki=RU) are read at the same layer.  Then, for lens X:
    exclusive_X(layer) = blackout_X(layer) AND NOT blackout_Y(layer) AND NOT blackout_Z(layer)
Item-level DV: exclusive_X = (# such layers) / (# layers), and the denominator n_layers is
also stored with the count n_excl so a binomial GLMM can use cbind(n_excl, n_layers - n_excl).

Output: data/blackout_exclusive.csv
        columns: tag, lens_lang, prompt_lang, item_type, item_idx, n_layers, n_excl,
                 rate, n_blackout_lenses_mean (descriptive)
"""
import glob
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, EXP)
import bilingual_align as A  # noqa: E402

nrm, is_lang = A.nrm, A._is_language
P300 = os.path.join(EXP, 'RESULT', 'PROBE300')
TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b', 'qwen3-1.7b-bnb4']
LENS = {'wikitext': 'en', 'zhwiki': 'zh', 'ruwiki': 'ru'}
PROMPTS = ['en', 'zh', 'ru']
_cache = {}


def is_letter(tok):
    c = _cache.get(tok)
    if c is None:
        c = is_lang(tok)
        _cache[tok] = c
    return c


def pool_blackout(top):
    letters = [is_letter(nrm(t)) for t in top]
    dark10 = not any(letters[:10])
    non_share = sum(1 for x in letters if not x) / len(letters)
    return 1 if (dark10 and non_share >= 0.5) else 0


def load_cell(tag, lens, prompt):
    """{(item_key, layer): blackout flag} for one (tag, lens, prompt) cell."""
    path = os.path.join(P300, 'PROBE300_%s_%s_%s_raw.json' % (tag, lens, prompt))
    d = json.load(open(path, encoding='utf-8'))
    out = {}
    for r in d['results']:
        for lay in r['layers']:
            if lay['L'] == 0:
                continue
            out[(r['key'], lay['L'])] = pool_blackout(lay['j_top100'])
    return out


def main():
    rows = []
    for tag in TAGS:
        cells = {(lg, pr): load_cell(tag, lg, pr) for lg in LENS for pr in PROMPTS}
        for prompt in PROMPTS:
            keys = set(cells[('wikitext', prompt)])
            for (item_key, layer) in sorted(keys):
                flags = {}
                for lg, ll in LENS.items():
                    flags[ll] = cells[(lg, prompt)].get((item_key, layer), 0)
                nb = sum(flags.values())
                for ll in ['en', 'zh', 'ru']:
                    others = [flags[k] for k in flags if k != ll]
                    excl = 1 if (flags[ll] == 1 and sum(others) == 0) else 0
                    alive = 1 if (flags[ll] == 0 and sum(others) == 2) else 0
                    rows.append(dict(tag=tag, lens_lang=ll, prompt_lang=prompt,
                                     item_key=item_key, layer=layer,
                                     blackout=flags[ll], exclusive=excl,
                                     only_alive=alive,
                                     n_blackout_lenses=nb))
        print('built', tag, flush=True)

    df = pd.DataFrame(rows)
    # aggregate to item level per (tag, lens, prompt, item)
    g = df.groupby(['tag', 'lens_lang', 'prompt_lang', 'item_key'], observed=True).agg(
        n_layers=('layer', 'size'), n_excl=('exclusive', 'sum'),
        n_alive=('only_alive', 'sum'),
        n_blackout=('blackout', 'sum'), mean_nb=('n_blackout_lenses', 'mean')).reset_index()
    g['rate'] = g.n_excl / g.n_layers
    g['rate_alive'] = g.n_alive / g.n_layers
    g['blackout_rate'] = g.n_blackout / g.n_layers
    # split item key into type/idx for the random-effect item id
    g['item_type'] = g.item_key.str.split('#').str[0]
    g['item_idx'] = g.item_key.str.split('#').str[1]
    g.to_csv(os.path.join(HERE, 'data', 'blackout_exclusive.csv'), index=False)
    print('\nitem rows: %d  tags: %d' % (len(g), g.tag.nunique()))
    print('mean exclusive rate: %.4f' % g.rate.mean())
    print('mean blackout rate (per lens): %.4f' % g.blackout_rate.mean())
    print('\npooled exclusive rate (lens x prompt, %):')
    t = g.groupby(['lens_lang', 'prompt_lang'], observed=True)[['n_excl', 'n_layers']].sum()
    t = 100 * t.n_excl / t.n_layers
    print(t.unstack().reindex(index=['en', 'zh', 'ru'], columns=PROMPTS).round(1).to_string())
    print('\npooled blackout rate (lens x prompt, %):')
    t2 = g.groupby(['lens_lang', 'prompt_lang'], observed=True)[['n_blackout', 'n_layers']].sum()
    t2 = 100 * t2.n_blackout / t2.n_layers
    print(t2.unstack().reindex(index=['en', 'zh', 'ru'], columns=PROMPTS).round(1).to_string())
    print('\npooled only-alive rate (lens x prompt, %): only this lens reads, other two black')
    ta = g.groupby(['lens_lang', 'prompt_lang'], observed=True)[['n_alive', 'n_layers']].sum()
    ta = 100 * ta.n_alive / ta.n_layers
    print(ta.unstack().reindex(index=['en', 'zh', 'ru'], columns=PROMPTS).round(2).to_string())
    print('\nlayers by number of blacked-out lenses (all tags/prompts):')
    print((df.n_blackout_lenses.value_counts(normalize=True).sort_index() * 100).round(2).to_string())
    print('\nP(exclusive | lens blacked out), %:')
    sub = g[g.n_blackout > 0]
    t3 = 100 * sub.groupby(['lens_lang', 'prompt_lang'], observed=True)[['n_excl', 'n_blackout']].sum()
    print((t3.n_excl / t3.n_blackout).unstack().reindex(index=['en', 'zh', 'ru'],
                                                       columns=PROMPTS).round(1).to_string())
    print('\nwrote data/blackout_exclusive.csv')


if __name__ == '__main__':
    main()
