# -*- coding: utf-8 -*-
"""Figure 1: one figure per family group.

Layout of a figure
  rows    = prompt language (English, Chinese, Russian probes)
  columns = the family's checkpoints ordered by size (smallest -> largest)
  cell    = the three lenses stacked (English-fitted, Chinese-fitted, Russian-fitted)

Gemma-4 has its own figure; Qwen3 and Qwen3.5 share one figure, their two family
blocks side by side.  Each family shows its smallest, middle and largest checkpoint (display rule,
figures only).

Subplot geometry is the manuscript constant one (gen_fig31.py): PH = 108 per lens
row, BW_BAR = 8 per layer slot, LENSW = 66, MGAP = 40, LABH = 40, TICKROW = 30,
LENS_GAP = 20, LEGEND_GAP = 84, TAILPAD = 30, RULE_Y = 30, HEAD_GAP = 26, MX = 24.
Rendered at 2x and cropped to content with a 24 px pad.

Data: P1 probes (country-capital), top-100 candidates, mean over the 100 probes.

Outputs (figures/):
  fig1a_gemma4_grid.png   Gemma-4 (E2B, E4B, 12B)
  fig1b_qwen_grid.png     Qwen3 (0.6B, 8B, 14B) and Qwen3.5 (0.8B, 2B, 9B) side by side
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

OUT = os.path.join(HERE, 'out')
_FS = float(os.environ.get('FIG_FS', '1.0'))
_SUFFIX = os.environ.get('FIG_SUFFIX', '')
_TS = float(os.environ.get('FIG_TICK_SIZE', '1.0'))
_YT = float(os.environ.get('FIG_YTICK_STEP', '0.25'))


def FS(x):
    return x * _FS


# spacing scale (canvas units, multiples of 4)
GAP_XS = 24
GAP_S = 16
GAP_M = 8
GAP_L = 32
GAP_XL = 48
GAP_XXL = 64
GAP_FAM = 96

MX = 64.0                  # page edge
PAD = 96                   # saved-image margin in raster px (2 x units)
PLAB = 128.0               # prompt-label column
LENSW = 64.0               # lens-label column
PH = 102.0                 # bar height per lens row (merged plate)
BW_BAR = 8.0 * float(os.environ.get('FIG_BW', '1.0'))       # width per measured layer
MGAP = 64.0                # between checkpoints of one family
FGAP = 144.0               # between family blocks, horizontally
ROWGAP = 192.0             # between the two block rows, vertically
LENS_GAP = 32.0            # between lens rows of one prompt
CELLGAP = 64.0             # between prompt groups
TICKROW = 32.0             # axis tick row
LABH = 60.0                # checkpoint title row
RULE_Y = 120.0             # family rule baseline
HEAD_GAP = 40.0            # rule to the checkpoint titles
LEGEND_GAP = 128.0         # before the legend
TAILPAD = 64.0             # bottom page edge
TITLE_GAP = 24           # family title above its rule
LABEL_GAP = 32.0           # checkpoint title above its panel
TICK_GAP = 12.0            # y tick label to the axis
SUBTICK_GAP = 72.0         # row label to the axis
LENSES = ("EN", "ZH", "RU")
PROMPTS = (("en", "EN prompt"), ("zh", "ZH prompt"), ("ru", "RU prompt"))

# Display subset: smallest, middle and largest checkpoint of each family
# (display_models.py). Statistics use every checkpoint in the manuscript set;
# Qwen3.6 is figure-only until it enters the analysis.
from display_models import load_selection  # noqa: E402

_SEL = load_selection()


def _family_block(family):
    return (family, [(m["tag"], m["label"]) for m in _SEL[family]])


FAM_ROWS = [
    [_family_block("Gemma-4"), _family_block("Qwen3")],
    [_family_block("Qwen3.5"), ("Qwen3.6", [("qwen3.6-27b", "Qwen3.6-27B")])],
]
MERGED_OUT = "fig1_merged_grid.png"


def draw_families(rows, item_type, outname):
    """Draw family blocks in one or more rows; each block is one family."""

    def nlayer(tag):
        # one fixed width per measured layer: panels widen with model depth
        return max(data["en"][tag]) + 1

    def block_meta(fam_name, models):
        metas = []
        for tag, label in models:
            panw = nlayer(tag) * BW_BAR
            metas.append((tag, label, panw))
        fam_w = LENSW + sum(panw for _, _, panw in metas) + MGAP * (len(metas) - 1)
        return fam_name, metas, fam_w

    rows_meta = []
    for row in rows:
        blocks = [block_meta(f, ms) for f, ms in row]
        row_w = sum(fw for _, _, fw in blocks) + FGAP * (len(blocks) - 1)
        rows_meta.append((blocks, row_w))

    nrow = len(PROMPTS)
    cell_h = 3 * PH + 2 * LENS_GAP + TICKROW
    block_h = HEAD_GAP + LABH + nrow * cell_h + (nrow - 1) * CELLGAP + 18

    max_row_w = max(rw for _, rw in rows_meta)
    legend_w = sum(GAP_M + text_width(n, 17) + GAP_L for n in BAND_NAMES)
    W = int(max(MX + PLAB + max_row_w, legend_w) + 2 * MX)

    content_h = len(rows_meta) * block_h + (len(rows_meta) - 1) * ROWGAP
    y0 = RULE_Y
    legend_y = y0 + content_h + LEGEND_GAP
    H = int(legend_y + TAILPAD)

    cv = Cv(W, H)
    cv.ax.add_patch(Rectangle((0, 0), W, H, facecolor="white", edgecolor="none",
                              zorder=0))

    zones = []

    def zone(kind, label, tokens, box):
        zones.append({"kind": kind, "label": label, "tokens": tokens, "box": box})

    def draw_block(fam_name, metas, fam_w, x0, y_rule):
        cv.text(x0, y_rule - TITLE_GAP, fam_name + " family", FS(20), INK, weight=True)
        cv.line(x0, y_rule, x0 + fam_w, y_rule, RULE)
        grid_top = y_rule + HEAD_GAP
        cell_tops = [grid_top + LABH + i * (cell_h + CELLGAP) for i in range(nrow)]
        # Only empty bands: the space under the title, under the rule.
        zone("title-gap", "Space under the family title", ["TITLE_GAP"],
             (x0, y_rule - TITLE_GAP + 8, fam_w, max(8, TITLE_GAP - 8)))
        zone("head-gap", "Space under the family rule", ["HEAD_GAP"],
             (x0, y_rule + 2, fam_w, max(8, HEAD_GAP - 2)))
        bx = x0
        for j, (tag, label, panw) in enumerate(metas):
            xp = bx + (LENSW if j == 0 else 0.0)
            cv.text(xp + panw / 2.0,
                    grid_top + LABEL_GAP, label, FS(16), INK, "middle")
            for i, (prompt, plabel) in enumerate(PROMPTS):
                prof = data[prompt][tag]
                layers = sorted(prof)
                cell_top = cell_tops[i]
                if j == 0:
                    cv.text(MX + GAP_M, cell_top + (3 * PH + 2 * LENS_GAP) / 2.0,
                            plabel, FS(14), INK, "middle", rotate=90)
                if i > 0:
                    zone("prompt-gap", "Between prompt groups", ["CELLGAP", "TICKROW"],
                         (xp, cell_tops[i - 1] + cell_h, panw, CELLGAP))
                for k, lens in enumerate(LENSES):
                    x0p = xp
                    yy = cell_top + k * (PH + LENS_GAP)
                    if k > 0:
                        zone("lens-gap", "Between lens rows", ["LENS_GAP", "PH"],
                             (x0p, yy - LENS_GAP, panw, LENS_GAP))
                    bot = yy + PH
                    if j == 0:
                        cv.text(x0p - SUBTICK_GAP, yy + PH / 2.0 + 4.0, lens, FS(14),
                                MUTED, "end")
                    cv.line(x0p, bot, x0p + panw, bot, RULE)
                    cv.line(x0p, yy, x0p, bot, RULE)
                    for gv in (0.25, 0.5, 0.75, 1.0):
                        yg = bot - gv * PH
                        cv.line(x0p, yg, x0p + panw, yg, GRID)
                    n_yt = int(round(1.0 / _YT))
                    if j == 0:
                        for gi in range(n_yt + 1):
                            gv = gi * _YT
                            cv.text(x0p - TICK_GAP, bot - gv * PH + 4.0, ("%g" % gv),
                                    FS(13) * _TS, MUTED, "end")
                    for L in layers:
                        sh = prof[L].get(lens.lower())
                        if sh is None:
                            continue
                        bxp = x0p + L * BW_BAR + BW_BAR * 0.06
                        yb = bot
                        for val, col in zip(sh, BANDS):
                            h = val * PH
                            if h > 0:
                                cv.rect(bxp, yb - h, BW_BAR * 0.88, h, col, 0.95)
                            yb -= h
                    if k == len(LENSES) - 1:
                        for tv in range(0, nlayer(tag), 8):
                            if nlayer(tag) - tv < 8:
                                continue
                            cv.text(x0p + tv * BW_BAR + BW_BAR / 2.0, bot + GAP_M,
                                    str(tv), FS(13) * _TS, MUTED, "middle")
            right = xp + panw
            if j + 1 < len(metas):
                zone("panel-gap", "Between checkpoints", ["MGAP"],
                     (right, grid_top + LABH, MGAP, nrow * cell_h + (nrow - 1) * CELLGAP))
            bx = right + MGAP
        cv.text(x0 + fam_w / 2.0,
                cell_tops[-1] + 3 * PH + 2 * LENS_GAP + TICKROW + GAP_XS,
                "Layer", FS(14), INK, "middle")

    y = y0
    for row_index, (blocks, row_w) in enumerate(rows_meta):
        x = MX + PLAB
        for bi, (fam_name, metas, fam_w) in enumerate(blocks):
            draw_block(fam_name, metas, fam_w, x, y)
            if bi + 1 < len(blocks):
                zone("family-gap", "Between families", ["FGAP"],
                     (x + fam_w, y, FGAP, block_h))
            x += fam_w + FGAP
        if row_index + 1 < len(rows_meta):
            zone("row-gap", "Between family rows", ["ROWGAP"],
                 (MX, y + block_h, row_w, ROWGAP))
        y += block_h + ROWGAP

    items = list(zip(BANDS, BAND_NAMES))
    widths = [GAP_L + cv.measure(n, FS(17)) + GAP_XL for _, n in items]
    lx = (W - sum(widths)) / 2.0
    for (col, name), wd in zip(items, widths):
        cv.rect(lx, legend_y - 12, 24, 12, col, 0.95)
        cv.text(lx + GAP_L, legend_y + 4.0, name, FS(17))
        lx += wd
    content_bottom = y0 + content_h
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"],
         (0, 0, MX, H))
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"], (W - MX, 0, MX, H))
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"],
         (0, 0, W, max(8, RULE_Y - TITLE_GAP - 34)))
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"],
         (0, legend_y + 28, W, max(8, H - legend_y - 28)))
    zone("legend-gap", "Space before the legend", ["LEGEND_GAP"],
         (MX, content_bottom, W - 2 * MX, max(8, legend_y - content_bottom)))

    cv.save_svg_png(outname.replace('.png', _SUFFIX + '.png'), pad=PAD, layout=zones)


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
    draw_families(FAM_ROWS, "P1", MERGED_OUT)


if __name__ == "__main__":
    main()
