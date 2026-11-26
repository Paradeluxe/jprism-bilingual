# -*- coding: utf-8 -*-
"""Export clickable spacing zones from the Figure 1 plate.

The plate keeps its spacing in canvas units. This patch writes a sidecar JSON
next to the rendered PNG, with every zone as a pixel box, so the sidebar editor
can highlight the real gaps instead of guessing from proportions.

Usage: python scripts/_patch_layout_export.py
"""
import os

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FIGDIR = os.path.join(HERE, 'experiment', 'figures')
sv = os.path.join(FIGDIR, 'make_readme_figs_svg.py')
src = open(sv, encoding='utf-8').read()

old_save = '''    def save_svg_png(self, name, scale=2.0, pad=24):
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
'''
new_save = '''    def save_svg_png(self, name, scale=2.0, pad=24, layout=None):
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
        if layout is not None:
            zones = []
            for zone in layout:
                x, y, w, h = zone["box"]
                zones.append({
                    "kind": zone["kind"],
                    "label": zone["label"],
                    "tokens": zone["tokens"],
                    "box": [round(x * scale - x0, 1), round(y * scale - y0, 1),
                            round(w * scale, 1), round(h * scale, 1)],
                })
            meta = {"image": {"width": int(img.shape[1]), "height": int(img.shape[0])},
                    "pad": pad, "zones": zones}
            with open(os.path.join(OUT, name + ".layout.json"), "w", encoding="utf-8") as fh:
                json.dump(meta, fh, ensure_ascii=False, indent=1)
        print("saved %-44s %5d x %-5d" % (name, img.shape[1], img.shape[0]))
'''
assert old_save in src
src = src.replace(old_save, new_save, 1)
open(sv, 'w', encoding='utf-8', newline='\n').write(src)
print('save_svg_png can export layout zones')

fam = os.path.join(FIGDIR, 'make_family_grids.py')
src = open(fam, encoding='utf-8').read()

# zones collector
old_head = '''    cv = Cv(W, H)
    cv.ax.add_patch(Rectangle((0, 0), W, H, facecolor="white", edgecolor="none",
                              zorder=0))

    def draw_block(fam_name, metas, fam_w, x0, y_rule):
'''
new_head = '''    cv = Cv(W, H)
    cv.ax.add_patch(Rectangle((0, 0), W, H, facecolor="white", edgecolor="none",
                              zorder=0))

    zones = []

    def zone(kind, label, tokens, box):
        zones.append({"kind": kind, "label": label, "tokens": tokens, "box": box})

    def draw_block(fam_name, metas, fam_w, x0, y_rule):
'''
assert old_head in src
src = src.replace(old_head, new_head, 1)

# title and label zones after grid_top / cell_tops are known
old_geo = '''        grid_top = y_rule + HEAD_GAP
        cell_tops = [grid_top + LABH + i * (cell_h + CELLGAP) for i in range(nrow)]
        bx = x0
'''
new_geo = '''        grid_top = y_rule + HEAD_GAP
        cell_tops = [grid_top + LABH + i * (cell_h + CELLGAP) for i in range(nrow)]
        zone("family-title", "Family title to rule", ["TITLE_GAP"],
             (x0, y_rule - TITLE_GAP - 26, fam_w, TITLE_GAP + 26))
        zone("checkpoint-title", "Checkpoint title row", ["LABH", "LABEL_GAP"],
             (x0, grid_top, fam_w, LABH))
        zone("label-column", "Prompt label column", ["PLAB", "LENSW", "SUBTICK_GAP", "TICK_GAP"],
             (0, grid_top, MX + PLAB, LABH + nrow * cell_h + (nrow - 1) * CELLGAP))
        bx = x0
'''
assert old_geo in src
src = src.replace(old_geo, new_geo, 1)

# per-cell zones inside the checkpoint loop
old_cell = '''                for k, lens in enumerate(LENSES):
                    x0p = bx + (LENSW if j == 0 else 0.0)
                    yy = cell_top + k * (PH + LENS_GAP)
'''
new_cell = '''                if i > 0:
                    zone("prompt-gap", "Between prompt groups", ["CELLGAP", "TICKROW"],
                         (bx, cell_tops[i - 1] + cell_h, panw, CELLGAP))
                for k, lens in enumerate(LENSES):
                    x0p = bx + (LENSW if j == 0 else 0.0)
                    yy = cell_top + k * (PH + LENS_GAP)
                    if k > 0:
                        zone("lens-gap", "Between lens rows", ["LENS_GAP", "PH"],
                             (x0p, yy - LENS_GAP, panw, LENS_GAP))
'''
assert old_cell in src
src = src.replace(old_cell, new_cell, 1)

# panel gap after each checkpoint's cell loop (bx moves after)
old_tail = '''            bx = x0p + panw + MGAP
'''
new_tail = '''            zone("axis", "Tick row", ["TICKROW", "TICK_GAP"],
                 (bx, cell_tops[-1] + cell_h - TICKROW, panw, TICKROW))
            right = bx + panw
            if j + 1 < len(metas):
                zone("panel-gap", "Between checkpoints", ["MGAP"],
                     (right, grid_top + LABH, MGAP, nrow * cell_h + (nrow - 1) * CELLGAP))
            bx = right + MGAP
'''
assert old_tail in src
src = src.replace(old_tail, new_tail, 1)

# block loop: family gap and row gap
old_rows = '''    y = y0
    for blocks, row_w in rows_meta:
        x = MX + PLAB
        for fam_name, metas, fam_w in blocks:
            draw_block(fam_name, metas, fam_w, x, y)
            x += fam_w + FGAP
        y += block_h + ROWGAP
'''
new_rows = '''    y = y0
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
'''
assert old_rows in src
src = src.replace(old_rows, new_rows, 1)

# margins and legend after legend_y is known (before cv.save)
old_save_call = '''    cv.save_svg_png(outname.replace('.png', _SUFFIX + '.png'), pad=PAD)
'''
new_save_call = '''    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"],
         (0, 0, W, RULE_Y - TITLE_GAP - 30))
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"], (0, 0, MX, H))
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"], (W - MX, 0, MX, H))
    zone("page-margin", "Page edge", ["MX", "PAD", "TAILPAD"], (0, legend_y, W, H - legend_y))
    zone("legend", "Legend block", ["LEGEND_GAP", "TAILPAD"],
         (0, legend_y - LEGEND_GAP, W, LEGEND_GAP + TAILPAD))

    cv.save_svg_png(outname.replace('.png', _SUFFIX + '.png'), pad=PAD, layout=zones)
'''
assert old_save_call in src
src = src.replace(old_save_call, new_save_call, 1)
open(fam, 'w', encoding='utf-8', newline='\n').write(src)
print('figure 1 now exports spacing zones')
