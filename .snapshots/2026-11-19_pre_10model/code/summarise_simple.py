import pandas as pd

pd.set_option('display.width', 260)
p = pd.read_csv('results/simple_pairwise_qwen3.5-0.8b.csv')
j = pd.read_csv('results/simple_joint_qwen3.5-0.8b.csv')
s = pd.read_csv('results/sig_terms_qwen3.5-0.8b.csv')

BANDS = ['en', 'zh', 'ru', 'other', 'non']


def level_col(row, by):
    return row['lens_lang'] if by == 'lens_lang' else row['prompt_lang']


def ordering(sub):
    """Return a string like 'en > ru > zh' using significant pairwise contrasts."""
    est = {}
    wins = {}
    for _, r in sub.iterrows():
        a, b = [x.strip() for x in str(r.contrast).split('-')]
        e = float(r.estimate)
        if e > 0:
            wins.setdefault(a, set()).add(b)
            wins.setdefault(b, set())
        else:
            wins.setdefault(b, set()).add(a)
            wins.setdefault(a, set())
        est[a] = est.get(a, 0.0)
        est[b] = est.get(b, 0.0)
    levels = sorted(wins, key=lambda k: -len(wins[k]) + 0.0)
    # stable order: sort by number of significant wins then alphabetically
    levels = sorted(wins, key=lambda k: (-len(wins[k]), k))
    ns = []
    for _, r in sub.iterrows():
        if float(r['p.value']) >= 0.05:
            ns.append('%s=%s(p=%.2f)' % (str(r.contrast).split(' - ')[0].strip(),
                                         str(r.contrast).split(' - ')[1].strip(),
                                         float(r['p.value'])))
    txt = ' > '.join(levels)
    if ns:
        txt += '  [ns: ' + '; '.join(ns) + ']'
    return txt


print('=' * 100)
print('SIGNIFICANT TERMS (raw p<.05; Holm within DV)')
print('=' * 100)
print(s[['dv', 'effect', 'stat', 'df1', 'df2', 'p', 'p_holm']].to_string(index=False))

print()
print('=' * 100)
print('SIMPLE-EFFECT JOINT TESTS  (F, df1; all models df2=Inf)')
print('=' * 100)
for dv in BANDS + ['blackout']:
    sub = j[j.dv == dv]
    parts = []
    for _, r in sub.iterrows():
        lev = r['lens_lang'] if pd.notna(r['lens_lang']) else r['prompt_lang']
        tested = 'prompt' if r['by'] == 'lens_lang' else 'lens'
        parts.append('%s|%s: F=%.1f p=%.1g' % (tested, lev, r['F.ratio'], r['p.value']))
    print('-' * 4, dv)
    for x in parts:
        print('   ', x)

print()
print('=' * 100)
print('PAIRWISE SIMPLE EFFECTS -> level ordering per cell (bonferroni; ns pairs marked)')
print('=' * 100)
for dv in BANDS + ['blackout']:
    print('\n--', dv)
    for by in ['lens_lang', 'prompt_lang']:
        sub = p[(p.dv == dv) & (p['by'] == by)]
        for lev, g in sub.groupby('lens_lang' if by == 'lens_lang' else 'prompt_lang'):
            focus = 'prompt' if by == 'lens_lang' else 'lens'
            print('   %s = %-3s : %s' % (focus, lev, ordering(g)))

print()
print('=' * 100)
print('BLACKOUT pairwise (logit scale)')
print('=' * 100)
b = p[p.dv == 'blackout']
print(b[['by', 'lens_lang', 'prompt_lang', 'contrast', 'estimate', 'SE', 'z.ratio', 'p.value']]
      .to_string(index=False))
