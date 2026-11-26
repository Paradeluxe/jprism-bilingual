# -*- coding: utf-8 -*-
"""Figure 4: the three blackout outcomes for the eight models, three lenses, three prompts.

Three heat-map panels side by side: pool blackout, single blackout, single survivor.
Rows are models (grouped by family); the nine columns are the three lenses x three prompt
languages. Cell values are the model-averaged rate in percent of measured layers.

Print geometry: 16.5 cm wide, fonts sized for a manuscript page.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'stats_mixed', 'results')
OUT = os.path.join(HERE, '..', '..', 'figures', 'fig4_blackout_heatmap.png')

TAGS = [('gemma4-e2b', 'Gemma-4-E2B'), ('gemma4-e4b', 'Gemma-4-E4B'),
        ('gemma4-12b', 'Gemma-4-12B'),
        ('qwen3-0.6b', 'Qwen3-0.6B'), ('qwen3-4b', 'Qwen3-4B'), ('qwen3-14b', 'Qwen3-14B'),
        ('qwen3.5-0.8b', 'Qwen3.5-0.8B'), ('qwen3.5-2b', 'Qwen3.5-2B')]
LENSES = ['en', 'zh', 'ru']
PROMPTS = ['en', 'zh', 'ru']
LAB = {'en': 'EN', 'zh': 'ZH', 'ru': 'RU'}
PANELS = [('blackout_pool', 'Pool blackout'), ('blackout_excl', 'Single blackout'),
          ('blackout_alive', 'Single survivor')]

pool = pd.read_csv(os.path.join(RES, 'pool_bo_lmm_cells.csv'))
single = pd.read_csv(os.path.join(RES, 'single_bo_lmm_cells.csv'))
cells = pd.concat([pool, single], ignore_index=True)
cells = cells[cells.tag.isin([t for t, _ in TAGS])]

cmap = LinearSegmentedColormap.from_list('ink', ['#ffffff', '#9ecae1', '#2171b5', '#08306b'])
matplotlib.rcParams.update({'font.family': ['DejaVu Sans'], 'font.size': 7,
                            'axes.linewidth': 0.5})

fig, axes = plt.subplots(1, 3, figsize=(6.5, 3.35), dpi=300)
vmax = {'blackout_pool': 0.55, 'blackout_excl': 0.27, 'blackout_alive': 0.24}

for k, (ax, (dv, title)) in enumerate(zip(axes, PANELS)):
    mat = np.full((len(TAGS), 9), np.nan)
    for i, (tag, _) in enumerate(TAGS):
        sub = cells[(cells.dv == dv) & (cells.tag == tag)]
        for j, lens in enumerate(LENSES):
            for m, prompt in enumerate(PROMPTS):
                v = sub[(sub.lens_lang == lens) & (sub.prompt_lang == prompt)]['mean']
                if len(v):
                    mat[i, j * 3 + m] = v.iloc[0]
    im = ax.imshow(mat, cmap=cmap, vmin=0, vmax=vmax[dv], aspect='auto')
    ax.set_title(title, fontsize=9, pad=21)
    ax.set_xticks(range(9))
    ax.set_xticklabels([LAB[p] for p in PROMPTS] * 3, fontsize=6.5)
    ax.set_yticks(range(len(TAGS)))
    if k == 0:
        ax.set_yticklabels([m for _, m in TAGS], fontsize=7)
    else:
        ax.set_yticklabels([])
    ax.tick_params(length=0, pad=2.5)
    for j in (2.5, 5.5):
        ax.axvline(j, color='white', lw=1.5)
    for j, lens in enumerate(LENSES):
        ax.text(j * 3 + 1, -1.0, LAB[lens] + ' lens', ha='center', va='bottom',
                fontsize=6.5, color='#333333')
    for i in (2.5, 5.5):
        ax.axhline(i, color='white', lw=1.5)
    for i in range(len(TAGS)):
        for j in range(9):
            v = mat[i, j]
            if np.isnan(v):
                continue
            ax.text(j, i, '%.2f' % v, ha='center', va='center', fontsize=5.0,
                    color='white' if v > 0.55 * vmax[dv] else '#222222')
    for sp in ax.spines.values():
        sp.set_visible(False)

fig.subplots_adjust(left=0.14, right=0.995, top=0.83, bottom=0.10, wspace=0.045)
fig.savefig(OUT, dpi=300, facecolor='white')
print('saved', OUT, 'size:', os.path.getsize(OUT))
