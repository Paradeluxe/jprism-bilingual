# -*- coding: utf-8 -*-
"""Probe which columns the ezlmm anova table exposes (need Satterthwaite DenDF)."""
import os
import sys

os.environ.setdefault('R_HOME', r'C:\Program Files\R\R-4.4.1')

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ezlmm_pinned import PinnedLinearMixedModel, set_sum_contrasts  # noqa: E402

TAGS = ['qwen3-0.6b', 'qwen3-4b', 'qwen3-14b', 'qwen3.5-0.8b', 'qwen3.5-2b',
        'gemma4-e2b', 'gemma4-e4b', 'gemma4-12b']
LEVELS = ['en', 'zh', 'ru']
FAMILIES = ['P1', 'P3', 'P4']

set_sum_contrasts()
d = pd.read_csv(os.path.join(HERE, 'data', 'item_level_core.csv'))
d = d[d.tag.isin(TAGS)].copy()
d['prompt_lang'] = pd.Categorical(d.prompt_lang, categories=LEVELS)
d['lens_lang'] = pd.Categorical(d.lens_lang, categories=LEVELS)
d['item_type'] = pd.Categorical(d.item_type, categories=FAMILIES)
d['item'] = d.item_type.astype(str) + '_' + d.item_idx.astype(str)

sub = d[d.tag == 'qwen3-0.6b'].copy()
m = PinnedLinearMixedModel()
m.data = sub
m.dep_var = 'arcsin_en'
m.indep_var = ['prompt_lang', 'lens_lang', 'item_type']
m.random_var = ['item']
m.fit_pinned('arcsin_en ~ prompt_lang * lens_lang * item_type + (1 | item)')
an = m.anova
print('anova columns:', list(an.columns))
print(an.to_string())
print('converged:', m.converged())
