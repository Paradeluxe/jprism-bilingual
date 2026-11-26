import pandas as pd

pd.set_option('display.width', 220)
tag = 'qwen3.5-0.8b'

b = pd.read_csv('tables/band_cell_means.csv')
b = b[b.tag == tag]
for band in ['en', 'zh', 'ru', 'other', 'non']:
    t = b[b.band == band].pivot_table(index='lens_lang', columns='prompt_lang',
                                      values='mean_share')
    t = t.reindex(index=['en', 'zh', 'ru'], columns=['en', 'zh', 'ru'])
    print('\n[%s] observed mean share (row=lens, col=prompt)' % band)
    print((100 * t).round(1).to_string())

bo = pd.read_csv('tables/blackout_cells.csv')
bo = bo[bo.tag == tag].pivot_table(index='lens_lang', columns='prompt_lang',
                                   values=['rate', 'blackouts', 'pools'])
print('\n[blackout] rate (row=lens, col=prompt)')
print((100 * bo['rate'].reindex(index=['en', 'zh', 'ru'],
                                columns=['en', 'zh', 'ru'])).round(2).to_string())
print('\n[blackout] raw counts (blackouts / pools)')
cnt = bo['blackouts'].reindex(index=['en', 'zh', 'ru'], columns=['en', 'zh', 'ru'])
n = bo['pools'].reindex(index=['en', 'zh', 'ru'], columns=['en', 'zh', 'ru'])
print(cnt.astype(int).to_string(), '\n/', n.astype(int).iloc[0, 0], 'pools per cell')

own = pd.read_csv('tables/own_lens_share.csv')
own = own[own.tag == tag].pivot_table(index='lens_lang', columns='prompt_lang',
                                      values='own_share_mean')
print('\n[own-language share] row=lens, col=prompt')
print((100 * own.reindex(index=['en', 'zh', 'ru'], columns=['en', 'zh', 'ru'])).round(1).to_string())

a = pd.read_csv('results/prelim_anova_qwen3.5-0.8b.csv')
print('\n[tests]')
print(a[['dv', 'effect', 'NumDF', 'DenDF', 'F value', 'Pr_gtF', 'Chisq', 'Df', 'Pr_gtChisq']]
      .to_string(index=False, max_colwidth=16))
