# -*- coding: utf-8 -*-
"""README figures 1/2/4/5 rebuilt with the ORIGINAL subplot geometry.

The original README plates are cropped rasters of the manuscript figures produced
by manuscript/fig/fig31/gen_fig31.py (composition) and
manuscript/fig/fig33/gen_fig33.py (overlap).  Those generators lay the figure out
in SVG user units (1 unit = 1 px of the pre-raster canvas); this script draws the
same layout with matplotlib on a pixel coordinate system, keeping every constant:

  composition : PH = 108 per lens row, BW_BAR = 8 per layer slot, LENSW = 66,
                MGAP = 40, FGAP = 54, LABH = 40, TICKROW = 30, LENS_GAP = 20,
                LEGEND_GAP = 84, TAILPAD = 30, RULE_Y = 30, HEAD_GAP = 26, MX = 24
  overlap     : PANW = 300, PH = 172, LENSW = 40, MGAP = 34, FSEG_GAP = 60,
                LABH = 33, TICKROW = 52, MODEL_GAP = 54, HEAD_GAP = 24,
                LEGEND_GAP = 92, TAILPAD = 26, RULE_Y = 29, MX = 24

The canvas is drawn at 1 unit = 1 px and rasterised at 2x (as the original
plates were), then cropped to content with a 24 px pad, exactly like
experiment/notes/crop_figs.py.  So every subplot keeps its original pixel size.

Content changes only: eight non-quantized models, three lenses (EN/ZH/RU), and
the three-way overlap measures.

Outputs (figures/):
  fig1_composition_3lens.png            English prompts
  fig2_overlap_3lens.png                English prompts
  fig4_composition_zhprompt_3lens.png   Chinese prompts
  fig5_overlap_zhprompt_3lens.png       Chinese prompts
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
REPO = os.path.dirname(EXP)
LONG = os.path.join(EXP, "stats_mixed", "data", "long.parquet")
CACHE = os.path.join(EXP, "stats_mixed", "data", "overlap_by_layer_3lens_v2.json")
OUT = os.path.join(REPO, "figures")
P300 = os.path.join(EXP, "RESULT", "PROBE300")
LENS_FILE = {"en": "wikitext", "zh": "zhwiki", "ru": "ruwiki"}

ROWS = [
    ("Gemma-4", [("gemma4-e2b", "Gemma-4-E2B"),
                 ("gemma4-e4b", "Gemma-4-E4B"),
                 ("gemma4-12b", "Gemma-4-12B")]),
    ("Qwen3", [("qwen3-0.6b", "Qwen3-0.6B"),
               ("qwen3-4b", "Qwen3-4B"),
               ("qwen3-14b", "Qwen3-14B")]),
    ("Qwen3.5", [("qwen3.5-0.8b", "Qwen3.5-0.8B"),
                 ("qwen3.5-2b", "Qwen3.5-2B")]),
]

INK, MUTED, GRID, RULE = "#222222", "#5f6b76", "#e8ecef", "#aab4bd"
C_EN, C_ZH, C_RU, C_OTH, C_NON = "#4C86A8", "#D55E00", "#00B37E", "#262626", "#C6C6C6"
BANDS = [C_EN, C_ZH, C_RU, C_OTH, C_NON]
BAND_NAMES = ["English", "Chinese", "Russian", "Other language", "Non-language"]

TICK = "#333333"
GRID_H, GRID_V, AXIS = "#EFEFEF", "#F5F5F5", "#888888"
C_ALL, C_IL, C_SEM, C_STR = "#0B3D63", "#7FA8C9", "#2E6E9E", "#A9B7C4"
SERIES = [("m4", C_STR, True), ("m2", C_SEM, False),
          ("m3", C_IL, True), ("m1", C_ALL, False)]
SERIES_LEGEND = [("m1", False, "cross-language overlap (no order)"),
                 ("m3", True, "within-language overlap (no order)"),
                 ("m2", False, "cross-language overlap (ordered)"),
                 ("m4", True, "within-language overlap (ordered)")]
SERIES_COLOR = {"m1": C_ALL, "m3": C_IL, "m2": C_SEM, "m4": C_STR}

# 1 SVG unit = 1 px on the pre-raster canvas; the figure is rasterised at 2x.
PT = 0.72           # point size per px (72/100)
FAM = ["Segoe UI", "DejaVu Sans"]
plt.rcParams["font.family"] = FAM
plt.rcParams["font.weight"] = "normal"
plt.rcParams["pdf.fonttype"] = 42


# ---------------------------------------------------------------- data

def load_composition(prompt):
    """{tag: {layer: {lens: [5 band shares]}}}"""
    d = pd.read_parquet(LONG)
    d = d[d.prompt_lang == prompt].copy()
    d["other"] = d["band_other"] / d.pool_size
    out = {}
    for tag, sub in d.groupby("tag"):
        out[tag] = {}
        for layer, lay in sub.groupby("layer"):
            out[tag][int(layer)] = {}
            for lens in ("en", "zh", "ru"):
                s = lay[lay.lens_lang == lens]
                if s.empty:
                    continue
                out[tag][int(layer)][lens] = [
                    s["band_en"].mean() / 100.0,
                    s["band_zh"].mean() / 100.0,
                    s["band_ru"].mean() / 100.0,
                    s["other"].mean(),
                    s["band_non"].mean() / 100.0,
                ]
    return out


def load_composition_probes(prompt, item_type="P1"):
    """{tag: {layer: {lens: [5 band shares]}}} averaged over one probe family."""
    d = pd.read_parquet(LONG)
    d = d[(d.prompt_lang == prompt) & (d.item_type == item_type)].copy()
    d["other"] = d["band_other"] / d.pool_size
    out = {}
    for tag, sub in d.groupby("tag"):
        out[tag] = {}
        for layer, lay in sub.groupby("layer"):
            out[tag][int(layer)] = {}
            for lens in ("en", "zh", "ru"):
                s = lay[lay.lens_lang == lens]
                if s.empty:
                    continue
                out[tag][int(layer)][lens] = [
                    s["band_en"].mean() / 100.0,
                    s["band_zh"].mean() / 100.0,
                    s["band_ru"].mean() / 100.0,
                    s["other"].mean(),
                    s["band_non"].mean() / 100.0,
                ]
    return out


def load_overlap():
    if os.path.isfile(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    sys.path.insert(0, EXP)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "ovl", os.path.join(EXP, "stats_mixed", "overlap", "build_overlap.py"))
    ovl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ovl)
    tags = [t for _, ms in ROWS for t, _ in ms]
    vocab, raw = set(), {}
    for tag in tags:
        for lens in ("en", "zh", "ru"):
            for prompt in ("en", "zh", "ru"):
                path = os.path.join(P300, "PROBE300_%s_%s_%s_raw.json"
                                    % (tag, LENS_FILE[lens], prompt))
                blob = json.load(open(path, encoding="utf-8"))
                cells = {}
                for r in blob["results"]:
                    for lay in r["layers"]:
                        cells[(r["key"], lay["L"])] = [ovl.nrm(t) for t in lay["j_top100"]]
                raw[(tag, lens, prompt)] = cells
                for v in cells.values():
                    vocab.update(v)
    cid = ovl.build_concept_map(vocab)
    out = {}
    for tag in tags:
        out[tag] = {}
        for prompt in ("en", "zh", "ru"):
            acc = {}
            cells = {l: raw[(tag, l, prompt)] for l in ("en", "zh", "ru")}
            keys = set(cells["en"]) & set(cells["zh"]) & set(cells["ru"])
            for (item, layer) in keys:
                toks = [cells[l][(item, layer)] for l in ("en", "zh", "ru")]
                c, o, s, so, _ = ovl.triple_measures(toks, cid, True)
                rec = acc.setdefault(layer, [0, 0, 0, 0, 0])
                rec[0] += c
                rec[1] += o
                rec[2] += s
                rec[3] += so
                rec[4] += 1
            out[tag][prompt] = {}
            for layer, (c, o, s, so, n) in acc.items():
                out[tag][prompt][str(layer)] = {
                    "m1": c / (300.0 * n), "m2": o / (100.0 * n),
                    "m3": s / (100.0 * n), "m4": so / (100.0 * n)}
        print("overlap", tag, flush=True)
    json.dump(out, open(CACHE, "w", encoding="utf-8"))
    return out


def text_width(s, size):
    """Width of a label in canvas units (1 unit = 1 px at dpi 100)."""
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    fp = FontProperties(family=FAM)
    tp = TextPath((0, 0), s, size=size * PT, prop=fp)
    return tp.get_extents().width * 100.0 / 72.0


# ---------------------------------------------------------------- canvas

class Cv:
    """Draw on a pixel canvas: 1 unit = 1 px of the pre-raster layout."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(H, 0)
        self.ax.set_axis_off()
        self.ax.set_facecolor("white")
        self.fig.patch.set_facecolor("white")

    def rect(self, x, y, w, h, fill, alpha=1.0):
        self.ax.add_patch(Rectangle((x, y), w, h, facecolor=fill,
                                    edgecolor="none", alpha=alpha, zorder=2))

    def line(self, x1, y1, x2, y2, stroke, width=1.0, z=1):
        self.ax.plot([x1, x2], [y1, y2], color=stroke, lw=width * PT,
                     solid_capstyle="butt", zorder=z)

    def text(self, x, y, s, size=11.5, fill=INK, anchor="start", weight=False):
        ha = {"start": "left", "middle": "center", "end": "right"}[anchor]
        self.ax.text(x, y, s, fontsize=size * PT, color=fill, ha=ha,
                     va="baseline", zorder=5, fontfamily=FAM,
                     fontweight="bold" if weight else "normal")

    def curve(self, pts, colour, dashed):
        if len(pts) < 2:
            return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        lw = 2.1
        ls = (0, (4 * PT / lw, 2.5 * PT / lw)) if dashed else "-"
        self.ax.plot(xs, ys, color=colour, lw=lw * PT, ls=ls,
                     solid_joinstyle="round", zorder=3)

    def markers(self, pts, colour):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        self.ax.plot(xs, ys, ls="none", marker="o", ms=2.6 * 2 * PT,
                     mfc="white", mec=colour, mew=1.9 * PT, zorder=4)

    def measure(self, s, size):
        """Width of the string in canvas units (1 unit = 1 px at dpi 100)."""
        t = self.ax.text(0, 0, s, fontsize=size * PT, fontfamily=FAM)
        self.fig.canvas.draw()
        bb = t.get_window_extent(renderer=self.fig.canvas.get_renderer())
        t.remove()
        return bb.width

    def save_svg_png(self, name, scale=2.0, pad=24):
        png = os.path.join(OUT, "_tmp.png")
        self.fig.savefig(png, dpi=100 * scale, facecolor="white")
        plt.close(self.fig)
        a = np.asarray(Image.open(png).convert("RGB"))
        nz = a.min(axis=2) < 245
        rows = np.where(nz.any(axis=1))[0]
        cols = np.where(nz.any(axis=0))[0]
        y0 = max(0, rows[0] - pad)
        y1 = min(a.shape[0], rows[-1] + pad + 1)
        x0 = max(0, cols[0] - pad)
        x1 = min(a.shape[1], cols[-1] + pad + 1)
        img = a[y0:y1, x0:x1]
        Image.fromarray(img).save(os.path.join(OUT, name), optimize=True)
        os.remove(png)
        print("saved %-44s %5d x %-5d" % (name, img.shape[1], img.shape[0]))


# ---------------------------------------------------------------- figure 1 / 4

def draw_composition(data):
    MX, LENSW, PH, BW_BAR = 24.0, 66.0, 108.0, 8.0
    MGAP, FGAP = 40.0, 54.0
    LENS_GAP, LEGEND_GAP, TAILPAD = 20.0, 84.0, 30.0
    LABH, TICKROW, RULE_Y, HEAD_GAP = 40.0, 30.0, 30.0, 26.0
    LENSES = ("EN", "ZH", "RU")
    BLOCK = LABH + len(LENSES) * PH + (len(LENSES) - 1) * LENS_GAP + TICKROW

    def slots(tag):
        return ((max(data[tag]) // 4) + 1) * 4 + 1

    def seg_width(models):
        return sum(LENSW + slots(t) * BW_BAR + MGAP for t, _ in models) - MGAP

    W = int(max(seg_width(ms) for _, ms in ROWS) + 2 * MX)
    tops = []
    for i in range(len(ROWS)):
        tops.append(RULE_Y + HEAD_GAP if i == 0 else tops[-1] + BLOCK + FGAP)
    legend_y = tops[-1] + BLOCK + LEGEND_GAP
    H = int(legend_y + TAILPAD)

    cv = Cv(W, H)
    cv.ax.add_patch(Rectangle((0, 0), W, H, facecolor="white", edgecolor="none",
                              zorder=0))

    for i, (fam, models) in enumerate(ROWS):
        fy = tops[i] - HEAD_GAP
        fx = MX
        cv.text(fx, fy - 10, fam + " family", 20, INK, weight=True)
        cv.line(fx, fy, fx + seg_width(models), fy, RULE)
        bx = fx
        for tag, label in models:
            prof = data[tag]
            layers = sorted(prof)
            xmax = ((max(layers) // 4) + 1) * 4
            PANW = (xmax + 1) * BW_BAR
            y = tops[i]
            cv.text(bx, y + LABH - 20, label, 18, INK)
            y += LABH
            for k, lens in enumerate(LENSES):
                x0 = bx + LENSW
                bot = y + PH
                cv.text(x0 - 34, y + PH / 2.0 + 5.0, lens, 14, MUTED, "end")
                cv.line(x0, bot, x0 + PANW, bot, RULE)
                cv.line(x0, y, x0, bot, RULE)
                for gv in (0.25, 0.5, 0.75, 1.0):
                    yy = bot - gv * PH
                    cv.line(x0, yy, x0 + PANW, yy,
                            GRID if gv in (0.5, 1.0) else "#f2f5f7")
                for gv in (0.0, 0.25, 0.5, 0.75, 1.0):
                    cv.text(x0 - 7, bot - gv * PH + 5.0, ("%g" % gv), 13,
                            MUTED, "end")
                for L in layers:
                    s = prof[L].get(lens.lower())
                    if s is None:
                        continue
                    bxp = x0 + L * BW_BAR + BW_BAR * 0.06
                    yy = bot
                    for val, col in zip(s, BANDS):
                        h = val * PH
                        if h > 0:
                            cv.rect(bxp, yy - h, BW_BAR * 0.88, h, col, 0.95)
                        yy -= h
                if k == len(LENSES) - 1:
                    for tv in range(0, xmax + 1, 8):
                        cv.text(x0 + tv * BW_BAR + BW_BAR / 2.0, bot + 17,
                                str(tv), 13, MUTED, "middle")
                    y += PH + TICKROW
                else:
                    y += PH + LENS_GAP
            bx += LENSW + PANW + MGAP

    items = list(zip(BANDS, BAND_NAMES))
    widths = [28 + cv.measure(n, 17) + 26 for _, n in items]
    lx = (W - sum(widths)) / 2.0
    for (col, name), wd in zip(items, widths):
        cv.rect(lx, legend_y - 11, 22, 13, col, 0.95)
        cv.text(lx + 28, legend_y + 2.0, name, 17)
        lx += wd
    return cv


# ---------------------------------------------------------------- figure 2 / 5

def draw_overlap(data):
    """Three-way overlap: one block per family, three prompt rows, models across.

    Geometry follows gen_fig33.py: PANW = 300, PH = 172, LENSW = 40, MGAP = 34,
    MX = 24; labels and ticks as in the manuscript plate.
    """
    _OFS = float(os.environ.get('OV_FS', '1.0'))
    _OPW = float(os.environ.get('OV_PANW', '1.0'))

    def _fs(v):
        return v * _OFS

    MX, LENSW = 24.0, 104.0 * max(1.0, _OFS * 0.95)
    PANW, PH = 300.0 * _OPW, 172.0
    MGAP = 34.0 * float(os.environ.get('OV_MGAP', '1.0'))
    HEAD_GAP = 16.0
    ROW_GAP = 26.0 * float(os.environ.get('OV_ROW_GAP', '1.0'))
    FGAP = 56.0 * float(os.environ.get('OV_FGAP', '1.0'))
    LABH, TICKROW, RULE_Y = 24.0, 52.0, 29.0
    LEGEND_GAP, TAILPAD = 92.0, 26.0
    PROMPTS = (("en", "EN prompt"), ("zh", "ZH prompt"), ("ru", "RU prompt"))
    nrow = len(PROMPTS)

    fam_w = [(LENSW + PANW + MGAP) * len(ms) - MGAP for _, ms in ROWS]
    LS, SW, SWGAP, ITEMGAP = _fs(14), 30.0, 8.0, 30.0
    legend_w = (sum(SW + SWGAP + text_width(lbl, LS) for _, _, lbl in SERIES_LEGEND)
                + ITEMGAP * (len(SERIES_LEGEND) - 1))
    W = int(max(max(fam_w), legend_w) + 2 * MX)

    blocks = []
    y = RULE_Y
    for k, (fam, models) in enumerate(ROWS):
        rule_y = y
        y += HEAD_GAP
        rows = []
        for i, (prompt, plabel) in enumerate(PROMPTS):
            panel_top = y + (LABH if i == 0 else 0)
            rows.append((prompt, plabel, panel_top))
            y = panel_top + PH + (TICKROW if i == nrow - 1 else ROW_GAP)
        blocks.append((fam, models, rule_y, rows))
        y += FGAP
    legend_y = y - FGAP + LEGEND_GAP
    H = int(legend_y + TAILPAD)

    cv = Cv(W, H)
    cv.ax.add_patch(Rectangle((0, 0), W, H, facecolor="white", edgecolor="none",
                              zorder=0))

    for fam, models, rule_y, rows in blocks:
        sege = (LENSW + PANW + MGAP) * len(models) - MGAP
        cv.text(MX, rule_y - 7, fam + " family", _fs(16), INK, weight=True)
        cv.line(MX, rule_y, MX + sege, rule_y, RULE)
        for i, (prompt, plabel, panel_top) in enumerate(rows):
            cy = panel_top + PH / 2.0
            cv.text(MX, cy, plabel, _fs(13), INK)
            for j, (tag, label) in enumerate(models):
                x0 = MX + LENSW + j * (PANW + MGAP)
                rowsd = data[tag][prompt]
                layers = sorted(int(k) for k in rowsd)
                xmax = max(layers)
                XU = (PANW - 6.0) / float(xmax)
                bot = panel_top + PH
                if i == 0:
                    cv.text(x0, panel_top - 6, label, _fs(13), INK)
                cv.rect(x0, panel_top, PANW, PH, "white")
                for gv in (0.0, 0.25, 0.5, 0.75, 1.0):
                    yy = bot - gv * PH
                    cv.line(x0, yy, x0 + PANW, yy, GRID_H)
                    if j == 0:
                        cv.text(x0 - 7, yy + 4.6, ("%g" % gv), _fs(13), TICK, "end")
                step = 8 if xmax <= 40 else 12
                for tv in range(0, xmax + 1, step):
                    xx = x0 + tv * XU
                    if i == nrow - 1:
                        cv.text(xx, bot + 17, str(tv), _fs(12), TICK, "middle")
                cv.line(x0, panel_top, x0, bot, AXIS)
                cv.line(x0, bot, x0 + PANW, bot, AXIS)
                for key, colour, dashed in SERIES:
                    pts = [(x0 + L * XU, bot - rowsd[str(L)][key] * PH)
                           for L in layers]
                    cv.curve(pts, colour, dashed)
                    cv.markers(pts, colour)
        # one axis title per family, centred under the block
        cv.text(MX + sege / 2.0,
                rows[-1][2] + PH + 17 + _fs(20), "Layer", _fs(13), INK, "middle")

    lx = (W - legend_w) / 2.0
    for j, (key, dashed, lbl) in enumerate(SERIES_LEGEND):
        colour = SERIES_COLOR[key]
        yl = legend_y - 4
        cv.line(lx, yl, lx + SW, yl, colour, 1.8)
        if dashed:
            cv.ax.plot([lx, lx + SW], [yl, yl], color="white", lw=3.2, zorder=6,
                       solid_capstyle="butt")
            cv.curve([(lx, yl), (lx + SW, yl)], colour, True)
        cv.ax.plot([lx + SW / 2.0], [yl], ls="none", marker="o", ms=2.2 * 2 * PT,
                   mfc="white", mec=colour, mew=1.7 * PT, zorder=7)
        cv.text(lx + SW + SWGAP, legend_y, lbl, LS, INK)
        lx += SW + SWGAP + text_width(lbl, LS) + (
            ITEMGAP if j < len(SERIES_LEGEND) - 1 else 0.0)
    return cv


# ---------------------------------------------------------------- main

def main():
    os.makedirs(OUT, exist_ok=True)
    ov = load_overlap()
    draw_overlap(ov).save_svg_png("fig2_overlap_3lens.png")


if __name__ == "__main__":
    main()
