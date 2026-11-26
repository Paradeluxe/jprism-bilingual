# -*- coding: utf-8 -*-
"""Display rule for Figures 1 and 2 (figures only; inference uses every checkpoint).

Each model family is shown with three checkpoints: the smallest, the largest,
and the checkpoint whose parameter count is closest to the arithmetic midpoint
of the two, (min + max) / 2. Families with three or fewer checkpoints show all
of them. The rule keeps the panels comparable across families as models are
added, and it never changes which models enter the statistics.
"""
import json
import os
import re

ROOT = r'E:\hermes_playground\jspace-repo\experiment'
REGISTRY = os.path.join(ROOT, 'manuscript_models.json')


def params_billions(model):
    """Parameter count in billions; the registry field, or parsed from the label."""
    if 'params' in model:
        return float(model['params'])
    m = re.search(r'(\d+(?:\.\d+)?)\s*B', model['label'])
    if not m:
        raise ValueError('no parameter count for %s' % model.get('tag'))
    return float(m.group(1))


def select(models):
    """Return {family: [model, ...]} with the display subset, ordered by size."""
    by_family = {}
    for model in models:
        by_family.setdefault(model['family'], []).append(model)
    chosen = {}
    for family, members in by_family.items():
        members = sorted(members, key=params_billions)
        if len(members) <= 3:
            chosen[family] = members
            continue
        low, high = members[0], members[-1]
        target = (params_billions(low) + params_billions(high)) / 2.0
        middle = min(members[1:-1],
                     key=lambda m: (abs(params_billions(m) - target), params_billions(m)))
        chosen[family] = [low, middle, high]
    return chosen


def load_selection(path=REGISTRY):
    with open(path, encoding='utf-8') as fh:
        registry = json.load(fh)
    return select(registry['models'])
