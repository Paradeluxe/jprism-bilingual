# -*- coding: utf-8 -*-
"""Final significance matrix: 7 DVs per model (4 shares + 3 language blackouts) x 3 effects."""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
pd.set_option('display.width', 300)

SHARES = ['share_en', 'share_zh', 'share_ru', 'share_other']
BO = {'A': ['boA_en', 'boA_zh', 'boA_ru'],
      'C': ['boC_en', 'boC_zh', 'boC_ru']}
EFFECTS = ['prompt_lang', 'lens_lang', 'prompt_lang:lens_lang']


def load():
    a = pd.read_csv(os.path.join(HERE, 'results', 'item_models_tests.csv'))
    b = pd.read_csv(os.path.join(HERE, 'results', 'item_models_boT.csv'))
    a = a[['tag', 'dv', 'effect', 'stat', 'value', 'df1', 'p', 'converged']]
    b = b.assign(converged=True)
    return pd.concat([a, b], ignore_index=True)


def fmt_p(p):
    if p < 1e-16:
        return '<1e-16'
    if p < 0.001:
        return '%.0e' % p
    return '%.3f' % p


def main():
    t = load()
    # which items to show
    bo_choice = sys.argv[1] if len(sys.argv) > 1 else 'A'
    dvs = SHARES + BO[bo_choice]

    print('models:', t.tag.nunique(), '| tests:', len(t))
    print('\n### count of models with p<.05 per DV x effect (7 DVs, blackout criterion %s)' % bo_choice)
    tab = []
    for dv in dvs:
        row = {'dv': dv}
        for e in EFFECTS:
            s = t[(t.dv == dv) & (t.effect == e)].p
            row[e.split(':')[0] + ('_x' if ':' in e else '')] = '%d/%d' % (int((s < .05).sum()), len(s))
        tab.append(row)
    print(pd.DataFrame(tab).to_string(index=False))

    print('\n### per-model significance (raw p) for the 7 DVs [criterion %s]' % bo_choice)
    for dv in dvs:
        sub = t[t.dv == dv].pivot_table(index='tag', columns='effect', values='p')
        sub = sub.reindex(columns=EFFECTS)
        print('\n--', dv)
        print(sub.map(lambda v: ('%.1e' % v) if pd.notna(v) and v < 1e-3 else
                      ('%.3f' % v if pd.notna(v) else '')).to_string())

    print('\n### non-significant cells (p>=.05) in the 7-DV set')
    ns = t[(t.dv.isin(dvs)) & (t.p >= .05)][['tag', 'dv', 'effect', 'stat', 'value', 'p']]
    print(ns.to_string(index=False) if len(ns) else '  none')

    print('\n### blackout criterion comparison (model-level significance counts)')
    for crit, cols in BO.items():
        for dv in cols:
            s = t[(t.dv == dv) & (t.effect == 'prompt_lang:lens_lang')].p
            print('%-6s %-8s interaction significant in %d/9 models' % (crit, dv, int((s < .05).sum())))
    for lang in ['en', 'zh', 'ru']:
        s = t[(t.dv == 'boT_' + lang) & (t.effect == 'prompt_lang:lens_lang')].p
        print('%-6s %-8s interaction significant in %d/9 models' % ('T', 'boT_' + lang, int((s < .05).sum())))


if __name__ == '__main__':
    main()
