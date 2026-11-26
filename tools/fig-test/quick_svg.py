# -*- coding: utf-8 -*-
"""Fast SVG preview of Figure 1.

Reads preview_data.json once per call (the full matplotlib render is far too
slow for live editing). Given token overrides, lays out the plate with the same
geometry rules as make_family_grids and emits an SVG plus the gap zones.

Usage: python quick_svg.py request.json

request.json: {"tokens": {"MGAP": 56, ...}}
stdout: {"svg": "...", "zones": [...], "W": ..., "H": ...}
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "out", "preview_data.json")


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build(tokens, model):
    P = dict(model["tokens"])
    P.update(tokens or {})
    bw = model["bwBar"]
    layers = model["layers"]
    prompts = model["prompts"]
    rows = model["rows"]

    def panel_w(tag):
        return layers[tag] * bw

    rows_meta = []
    for row in rows:
        block_row = []
        for family in row:
            models = [{"tag": m["tag"], "label": m["label"], "w": panel_w(m["tag"])}
                      for m in family["models"]]
            w = P["LENSW"] + sum(m["w"] for m in models) + P["MGAP"] * (len(models) - 1)
            block_row.append({"family": family["family"], "models": models, "w": w})
        rows_meta.append(block_row)

    row_w = [sum(f["w"] for f in row) + P["FGAP"] * (len(row) - 1) for row in rows_meta]
    max_row_w = max(row_w)
    legend_w = sum(P["MGAP"] + len(n) * 8.5 + P["LABH"] for n in model["palette"]["bandNames"])
    W = max(P["MX"] + P["PLAB"] + max_row_w, legend_w) + 2 * P["MX"]

    nrow = len(prompts)
    cell_h = 3 * P["PH"] + 2 * P["LENS_GAP"] + P["TICKROW"]
    block_h = P["HEAD_GAP"] + P["LABH"] + nrow * cell_h + (nrow - 1) * P["CELLGAP"] + 18
    content_h = len(rows_meta) * block_h + (len(rows_meta) - 1) * P["ROWGAP"]
    legend_y = P["RULE_Y"] + content_h + P["LEGEND_GAP"]
    H = legend_y + P["TAILPAD"]

    zones = []

    def zone(kind, box):
        zones.append({"kind": kind, "box": [round(v, 1) for v in box]})

    body = []
    palette = model["palette"]
    bands = palette["bands"]
    band_names = palette["bandNames"]

    def text(x, y, s, size, fill=None, anchor="start", weight=None, rotate=None):
        attrs = [
            'x="%.1f"' % x, 'y="%.1f"' % y,
            'font-size="%.1f"' % size,
            'fill="%s"' % (fill or palette["ink"]),
            'font-family="Segoe UI, DejaVu Sans, sans-serif"',
        ]
        if anchor != "start":
            attrs.append('text-anchor="%s"' % anchor)
        if weight:
            attrs.append('font-weight="%s"' % weight)
        if rotate:
            attrs.append('transform="rotate(%s %.1f %.1f)"' % (rotate, x, y))
        body.append("<text %s>%s</text>" % (" ".join(attrs), esc(s)))

    def rect(x, y, w, h, fill, opacity=None):
        attrs = ['x="%.1f"' % x, 'y="%.1f"' % y, 'width="%.1f"' % w,
                 'height="%.1f"' % h, 'fill="%s"' % fill]
        if opacity is not None:
            attrs.append('opacity="%s"' % opacity)
        body.append("<rect %s/>" % " ".join(attrs))

    def line(x1, y1, x2, y2, stroke, width=1.0):
        body.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"/>'
                    % (x1, y1, x2, y2, stroke, width))

    y0 = P["RULE_Y"]
    for ri, row in enumerate(rows_meta):
        y = y0 + ri * (block_h + P["ROWGAP"])
        x = P["MX"] + P["PLAB"]
        for family in row:
            grid_top = y + P["HEAD_GAP"]
            cell_tops = [grid_top + P["LABH"] + i * (cell_h + P["CELLGAP"]) for i in range(nrow)]
            text(x, y - P["TITLE_GAP"], family["family"] + " family", 20, weight="600")
            line(x, y, x + family["w"], y, palette["rule"], 0.9)
            zone("title-gap", (x, y - P["TITLE_GAP"] + 8, family["w"], max(8, P["TITLE_GAP"] - 8)))
            zone("head-gap", (x, y + 2, family["w"], max(8, P["HEAD_GAP"] - 2)))

            bx = x
            for j, entry in enumerate(family["models"]):
                mx = bx + (P["LENSW"] if j == 0 else 0)
                text(mx + entry["w"] / 2, grid_top + P["LABEL_GAP"], entry["label"], 16, anchor="middle")
                right = mx + entry["w"]
                if j + 1 < len(family["models"]):
                    zone("panel-gap", (right, grid_top + P["LABH"], P["MGAP"],
                                       nrow * cell_h + (nrow - 1) * P["CELLGAP"]))
                bx = right + P["MGAP"]

                for i, prompt in enumerate(prompts):
                    cell_top = cell_tops[i]
                    if i > 0:
                        zone("prompt-gap", (mx, cell_tops[i - 1] + cell_h, entry["w"], P["CELLGAP"]))
                    if j == 0:
                        text(P["MX"] + P["MGAP"], cell_top + (3 * P["PH"] + 2 * P["LENS_GAP"]) / 2,
                             model["promptLabels"][prompt], 14, anchor="middle", rotate="-90")
                    for k, lens in enumerate(("en", "zh", "ru")):
                        top = cell_top + k * (P["PH"] + P["LENS_GAP"])
                        bot = top + P["PH"]
                        if k > 0:
                            zone("lens-gap", (mx, top - P["LENS_GAP"], entry["w"], P["LENS_GAP"]))
                        for gv in (0.25, 0.5, 0.75, 1.0):
                            line(mx, bot - gv * P["PH"], mx + entry["w"], bot - gv * P["PH"],
                                 palette["grid"], 0.5)
                        line(mx, bot, mx + entry["w"], bot, palette["rule"], 0.8)
                        line(mx, top, mx, bot, palette["rule"], 0.8)
                        if j == 0:
                            text(mx - 8, top + P["PH"] / 2 + 4, lens.upper(), 14,
                                 palette["muted"], anchor="end")
                            for gv in (0, 0.5, 1):
                                label = "0" if gv == 0 else ("0.5" if gv == 0.5 else "1")
                                text(mx - 2, bot - gv * P["PH"] + 4, label, 12,
                                     palette["muted"], anchor="end")

                        layers_map = model["data"].get(prompt, {}).get(entry["tag"], {})
                        for layer_key, lenses in layers_map.items():
                            shares = lenses.get(lens) or []
                            layer = float(layer_key)
                            yb = bot
                            for bi, value in enumerate(shares):
                                hgt = value * P["PH"]
                                if hgt > 0:
                                    rect(mx + layer * bw + bw * 0.06, yb - hgt, bw * 0.88, hgt,
                                         bands[bi], 0.95)
                                yb -= hgt

                        if k == 2:
                            n = layers[entry["tag"]]
                            for tv in range(0, n, 8):
                                if n - tv < 8:
                                    continue
                                text(mx + tv * bw + bw / 2, bot + 8, str(tv), 11,
                                     palette["muted"], anchor="middle")

            if family is not row[-1]:
                zone("family-gap", (x + family["w"], y, P["FGAP"], block_h))
            x += family["w"] + P["FGAP"]
        if ri + 1 < len(rows_meta):
            zone("row-gap", (P["MX"], y + block_h, row_w[ri], P["ROWGAP"]))

    # legend
    widths = [P["MGAP"] + len(name) * 8.5 + P["LABH"] for name in band_names]
    lx = (W - sum(widths)) / 2
    for index, name in enumerate(band_names):
        rect(lx, legend_y - 12, 24, 12, bands[index])
        text(lx + P["MGAP"] + 20, legend_y + 4, name, 16)
        lx += widths[index]

    zone("page-margin", (0, 0, P["MX"], H))
    zone("page-margin", (W - P["MX"], 0, P["MX"], H))
    zone("page-margin", (0, 0, W, max(8, P["RULE_Y"] - P["TITLE_GAP"] - 34)))
    zone("page-margin", (0, legend_y + 28, W, max(8, H - legend_y - 28)))
    zone("legend-gap", (P["MX"], P["RULE_Y"] + content_h, W - 2 * P["MX"],
                        max(8, P["LEGEND_GAP"])))

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.1f %.1f" '
           'width="100%%" height="100%%" style="display:block" preserveAspectRatio="xMidYMid meet" '
           '>'
           '<rect x="0" y="0" width="%.1f" height="%.1f" fill="#ffffff"/>%s</svg>'
           % (W, H, W, H, "".join(body)))
    return {"svg": svg, "zones": zones, "W": round(W, 1), "H": round(H, 1), "tokens": P}


def main():
    request = {}
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        with open(sys.argv[1], encoding="utf-8-sig") as fh:
            request = json.load(fh)
    with open(DATA, encoding="utf-8") as fh:
        model = json.load(fh)
    out = build(request.get("tokens") or {}, model)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
