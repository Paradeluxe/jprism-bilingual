# -*- coding: utf-8 -*-
"""Export everything the browser needs to draw the plate instantly.

The full matplotlib render costs ~13 s, far too slow for a live preview. This
dumps the composition data, the model rows, the palette and the default spacing
tokens once, so the sidebar can redraw the plate on every slider move in the
browser.

Run from tools/fig-test: python export_preview.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import make_readme_figs_svg as m
import make_family_grids as g

PROMPTS = [p for p, _ in g.PROMPTS]
PROMPT_LABELS = {p: label for p, label in g.PROMPTS}


def main():
    data = {p: m.load_composition_probes(p, "P1") for p in PROMPTS}
    layers = {}
    payload_data = {}
    for prompt in PROMPTS:
        payload_data[prompt] = {}
        for tag, prof in data[prompt].items():
            layers[tag] = max(max(int(k) for k in prof) + 1, layers.get(tag, 0))
            payload_data[prompt][tag] = {}
            for layer, lenses in prof.items():
                payload_data[prompt][tag][str(layer)] = {
                    lens: [float(v) for v in lenses.get(lens, [])]
                    for lens in ("en", "zh", "ru")
                }

    rows = []
    for row in g.FAM_ROWS:
        out_row = []
        for family, models in row:
            out_row.append({
                "family": family,
                "models": [{"tag": tag, "label": label} for tag, label in models],
            })
        rows.append(out_row)

    tokens = {
        "MX": g.MX, "PAD": g.PAD, "PLAB": g.PLAB, "LENSW": g.LENSW,
        "PH": g.PH, "MGAP": g.MGAP, "FGAP": g.FGAP, "ROWGAP": g.ROWGAP,
        "LENS_GAP": g.LENS_GAP, "CELLGAP": g.CELLGAP, "TICKROW": g.TICKROW,
        "LABH": g.LABH, "RULE_Y": g.RULE_Y, "HEAD_GAP": g.HEAD_GAP,
        "LEGEND_GAP": g.LEGEND_GAP, "TAILPAD": g.TAILPAD,
        "TITLE_GAP": g.TITLE_GAP, "LABEL_GAP": g.LABEL_GAP,
    }

    payload = {
        "image": {"width": 0, "height": 0},
        "bwBar": g.BW_BAR,
        "prompts": PROMPTS,
        "promptLabels": PROMPT_LABELS,
        "rows": rows,
        "layers": layers,
        "tokens": tokens,
        "data": payload_data,
        "palette": {
            "bands": m.BANDS,
            "bandNames": m.BAND_NAMES,
            "ink": m.INK,
            "muted": m.MUTED,
            "grid": m.GRID,
            "rule": m.RULE,
        },
    }
    out = os.path.join(HERE, "out", "preview_data.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))


if __name__ == "__main__":
    main()
