# -*- coding: utf-8 -*-
"""Figure 1: one figure per family group.

Layout of a figure
  rows    = prompt language (English, Chinese, Russian probes)
  columns = the family's checkpoints ordered by size (smallest -> largest)
  cell    = the three lenses stacked (English-fitted, Chinese-fitted, Russian-fitted)

Gemma-4 has its own figure; Qwen3 and Qwen3.5 share one figure, their two family
blocks side by side.  Qwen3.5 contributes two checkpoints, so it has two columns.

Subplot geometry is the manuscript constant one (gen_fig31.py): PH = 108 per lens
row, BW_BAR = 8 per layer slot, LENSW = 66, MGAP = 40, LABH = 40, TICKROW = 30,
LENS_GAP = 20, LEGEND_GAP = 84, TAILPAD = 30, RULE_Y = 30, HEAD_GAP = 26, MX = 24.
Rendered at 2x and cropped to content with a 24 px pad.

Data: P1 probes (country-capital), top-100 candidates, mean over the 100 probes.

Outputs (figures/):
  fig1a_gemma4_grid.png   Gemma-4 (E2B, E4B, 12B)
  fig1b_qwen_grid.png     Qwen3 (0.6B, 4B, 14B) and Qwen3.5 (0.8B, 2B) side by side
"""
import os
import sys

from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from make_readme_figs_svg import (  # noqa: E402
    Cv, OUT, BANDS, BAND_NAMES, INK, MUTED, GRID, RULE,
    load_composition_probes,
)

_FS = float(os.environ.get('FIG_FS', '1.0'))
_SUFFIX = os.environ.get('FIG_SUFFIX', '')
_TS = float(os.environ.get('FIG_TICK_SIZE', '1.0'))
_YT = float(os.environ.get('FIG_YTICK_STEP', '0.25'))


def FS(x):
    return x * _FS


MX = 24.0 * max(1.0, _FS * 0.8)
PLAB = 86.0 * _FS
LENSW = 66.0 * _FS
PH = 108.0 * float(os.environ.get('FIG_PH', '1.0'))
BW_BAR = 8.0
MGAP, FGAP = 40.0, 60.0
LENS_GAP = 20.0 * float(os.environ.get('FIG_LENS_GAP', '1.0'))
CELLGAP = 48.0 * float(os.environ.get('FIG_CELL_GAP', '1.0'))
TICKROW = 30.0 * max(1.0, _FS * 0.75)
LABH = 40.0 * max(1.0, _FS * 0.85)
RULE_Y = 30.0 * max(1.0, _FS * 0.9)
HEAD_GAP = 26.0
LEGEND_GAP = 84.0 * max(1.0, _FS * 0.8)
TAILPAD = 30.0 * max(1.0, _FS * 0.8)
LENSES = ("EN", "ZH", "RU")
PROMPTS = (("en", "EN prompt"), ("zh", "ZH prompt"), ("ru", "RU prompt"))

GEMMA = [("Gemma-4", [("gemma4-e2b", "Gemma-4-E2B"),
                      ("gemma4-e4b", "Gemma-4-E4B"),
                      ("gemma4-12b", "Gemma-4-12B")])]
QWEN = [("Qwen3", [("qwen3-0.6b", "Qwen3-0.6B"),
                   ("qwen3-4b", "Qwen3-4B"),
                   ("qwen3-14b", "Qwen3-14B")]),
        ("Qwen3.5", [("qwen3.5-0.8b", "Qwen3.5-0.8B"),
                     ("qwen3.5-2b", "Qwen3.5-2B")])]

FAM_GROUPS = [
    (GEMMA, "fig1a_gemma4_grid.png"),
    (QWEN, "fig1b_qwen_grid.png"),
]


def draw_families(fams, item_type, outname):
    """Draw one or more family segments side by side in a single canvas."""

    def xmax(tag):
        return ((max(data["en"][tag]) // 4) + 1) * 4

    segs = []          # (fam_name, models, x_start, family_width, model_meta)
    x = MX + PLAB
    for fam_name, models in fams:
        metas = []
        for tag, label in models:
            panw = (xmax(tag) + 1) * BW_BAR
            metas.append((tag, label, panw))
        fam_w = sum(LENSW + panw + MGAP for _, _, panw in metas) - MGAP
        segs.append((fam_name, metas, x, fam_w))
        x += fam_w + FGAP

    nrow = len(PROMPTS)
    grid_top = RULE_Y + HEAD_GAP
    first_top = grid_top + LABH
    cell_hs = [3 * PH + 2 * LENS_GAP + TICKROW for i in range(nrow)]
    cell_tops = []
    y = first_top
    for h in cell_hs:
        cell_tops.append(y)
        y += h + CELLGAP
    content_end = cell_tops[-1] + cell_hs[-1]
    legend_y = content_end + LEGEND_GAP

    blocks_w = sum(seg[3] for seg in segs) + FGAP * (len(segs) - 1)
    legend_w = sum(28 + text_width(n, 17) + 26 for n in BAND_NAMES)
    W = int(max(MX + PLAB + blocks_w, legend_w) + 2 * MX)
    H = int(legend_y + TAILPAD)

    cv = Cv(W, H)
    cv.ax.add_patch(Rectangle((0, 0), W, H, facecolor="white", edgecolor="none",
                              zorder=0))
    for fam_name, metas, sx, fam_w in segs:
        cv.text(sx, RULE_Y - 10, fam_name + " family", FS(20), INK, weight=True)
        cv.line(sx, RULE_Y, sx + fam_w, RULE_Y, RULE)
        bx = sx
        for tag, label, panw in metas:
            cv.text(bx, grid_top + LABH - 20, label, FS(18), INK)
            for i, (prompt, plabel) in enumerate(PROMPTS):
                prof = data[prompt][tag]
                layers = sorted(prof)
                cell_top = cell_tops[i]
                if bx == sx:
                    cv.text(MX + 6, cell_top + (3 * PH + 2 * LENS_GAP) / 2.0,
                            plabel, FS(14), INK)
                for k, lens in enumerate(LENSES):
                    x0 = bx + LENSW
                    yy = cell_top + k * (PH + LENS_GAP)
                    bot = yy + PH
                    cv.text(x0 - 0.52 * LENSW, yy + PH / 2.0 + 5.0, lens, FS(14), MUTED, "end")
                    cv.line(x0, bot, x0 + panw, bot, RULE)
                    cv.line(x0, yy, x0, bot, RULE)
                    for gv in (0.25, 0.5, 0.75, 1.0):
                        yg = bot - gv * PH
                        cv.line(x0, yg, x0 + panw, yg, GRID)
                    n_yt = int(round(1.0 / _YT))
                    if bx == sx:
                        for gi in range(n_yt + 1):
                            gv = gi * _YT
                            cv.text(x0 - 7, bot - gv * PH + 5.0, ("%g" % gv),
                                    FS(13) * _TS, MUTED, "end")
                    for L in layers:
                        sh = prof[L].get(lens.lower())
                        if sh is None:
                            continue
                        bxp = x0 + L * BW_BAR + BW_BAR * 0.06
                        yb = bot
                        for val, col in zip(sh, BANDS):
                            h = val * PH
                            if h > 0:
                                cv.rect(bxp, yb - h, BW_BAR * 0.88, h, col, 0.95)
                            yb -= h
                    if k == len(LENSES) - 1:
                        for tv in range(0, xmax(tag) + 1, 8):
                            cv.text(x0 + tv * BW_BAR + BW_BAR / 2.0, bot + 17,
                                    str(tv), FS(13) * _TS, MUTED, "middle")
            bx += LENSW + panw + MGAP
        # one axis title per family, centred under the block
        cv.text(sx + fam_w / 2.0,
                cell_tops[-1] + 3 * PH + 2 * LENS_GAP + TICKROW + 2,
                "Layer", FS(14), INK, "middle")

    items = list(zip(BANDS, BAND_NAMES))
    widths = [28 + cv.measure(n, FS(17)) + 26 for _, n in items]
    lx = (W - sum(widths)) / 2.0
    for (col, name), wd in zip(items, widths):
        cv.rect(lx, legend_y - 11, 22, 13, col, 0.95)
        cv.text(lx + 28, legend_y + 2.0, name, FS(17))
        lx += wd
    cv.save_svg_png(outname.replace('.png', _SUFFIX + '.png'))


def text_width(s, size):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    from make_readme_figs_svg import FAM, PT
    tp = TextPath((0, 0), s, size=size * PT, prop=FontProperties(family=FAM))
    return tp.get_extents().width * 100.0 / 72.0


def main():
    os.makedirs(OUT, exist_ok=True)
    global data
    data = {p: load_composition_probes(p, "P1") for p, _ in PROMPTS}
    for fams, outname in FAM_GROUPS:
        draw_families(fams, "P1", outname)


if __name__ == "__main__":
    main()
