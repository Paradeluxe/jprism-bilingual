import pandas as pd

pd.set_option('display.width', 260)
t = pd.read_csv('results/item_models_tests.csv')
print('rows', len(t), 'tags', t.tag.nunique(), 'dvs', t.dv.nunique())
print(t.dv.unique())

# Holm within (tag, dv)
t['p_holm'] = float('nan')
for (tag, dv), idx in t.groupby(['tag', 'dv']).groups.items():
    sub = t.loc[idx].sort_values('p')
    m = len(sub)
    run = 0.0
    for rank, (i, row) in enumerate(sub.iterrows(), start=1):
        run = max(run, min(1.0, (m - rank + 1) * row.p))
        t.loc[i, 'p_holm'] = run

print('\n=== significance counts across the 9 models (p<.05 raw) ===')
cnt = t.groupby(['dv', 'effect']).agg(n_sig=('p', lambda s: int((s < .05).sum())),
                                      n=('p', 'size'))
print(cnt.unstack(0).to_string())

print('\n=== per-tag p table: share DVs (P=prompt, L=lens, PxL) ===')
for dv in ['share_en', 'share_zh', 'share_ru', 'share_other']:
    sub = t[t.dv == dv].pivot_table(index='tag', columns='effect', values='p')
    print('\n--', dv)
    print(sub.map(lambda v: '%.2g' % v if pd.notna(v) else '').to_string())

print('\n=== per-tag p table: blackout A (mirror criterion) ===')
for dv in ['boA_en', 'boA_zh', 'boA_ru']:
    sub = t[t.dv == dv].pivot_table(index='tag', columns='effect', values='p')
    print('\n--', dv)
    print(sub.map(lambda v: '%.2g' % v if pd.notna(v) else '').to_string())

print('\n=== per-tag p table: blackout C (band empty) ===')
for dv in ['boC_en', 'boC_zh', 'boC_ru']:
    sub = t[t.dv == dv].pivot_table(index='tag', columns='effect', values='p')
    print('\n--', dv)
    print(sub.map(lambda v: '%.2g' % v if pd.notna(v) else '').to_string())

print('\n=== convergence ===')
print(t.groupby('family').converged.value_counts().to_string())
