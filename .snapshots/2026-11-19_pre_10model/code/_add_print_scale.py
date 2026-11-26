# -*- coding: utf-8 -*-
"""Add a print-scale mode to the family-grid generator and export print variants."""
import re

p = r'E:\hermes_playground\jspace-repo\experiment\figures\make_family_grids.py'
s = open(p, encoding='utf-8').read()

# 1. scale factors from the environment
anchor = 'MX, PLAB, LENSW, PH, BW_BAR = 24.0, 86.0, 66.0, 108.0, 8.0'
assert anchor in s
s = s.replace(anchor, '''_FS = float(os.environ.get('FIG_FS', '1.0'))
_SUFFIX = os.environ.get('FIG_SUFFIX', '')
_TS = float(os.environ.get('FIG_TICK_SIZE', '1.0'))


def FS(x):
    return x * _FS


MX = 24.0 * max(1.0, _FS * 0.8)
PLAB = 86.0 * _FS
LENSW = 66.0 * _FS
PH, BW_BAR = 108.0, 8.0''')

# 2. scale the remaining layout margins
s = s.replace('MGAP, FGAP, LENS_GAP, TICKROW = 40.0, 60.0, 20.0, 30.0',
              'MGAP, FGAP, LENS_GAP = 40.0, 60.0, 20.0')
s = s.replace('LABH, RULE_Y, HEAD_GAP, LEGEND_GAP, TAILPAD = 40.0, 30.0, 26.0, 84.0, 30.0',
              'TICKROW = 30.0 * max(1.0, _FS * 0.75)\n'
              'LABH = 40.0 * max(1.0, _FS * 0.85)\n'
              'RULE_Y = 30.0 * max(1.0, _FS * 0.9)\n'
              'HEAD_GAP = 26.0\n'
              'LEGEND_GAP = 84.0 * max(1.0, _FS * 0.8)\n'
              'TAILPAD = 30.0 * max(1.0, _FS * 0.8)')

# 3. scale every font size
s = s.replace("cv.text(sx, RULE_Y - 10, fam_name + \" family\", 20, INK, weight=True)",
              "cv.text(sx, RULE_Y - 10, fam_name + \" family\", FS(20), INK, weight=True)")
s = s.replace("cv.text(bx, grid_top + LABH - 20, label, 18, INK)",
              "cv.text(bx, grid_top + LABH - 20, label, FS(18), INK)")
s = s.replace("plabel, 14, INK)", "plabel, FS(14), INK)")
s = s.replace("cv.text(x0 - 34, yy + PH / 2.0 + 5.0, lens, 14, MUTED, \"end\")",
              "cv.text(x0 - 0.52 * LENSW, yy + PH / 2.0 + 5.0, lens, FS(14), MUTED, \"end\")")
s = s.replace("cv.text(x0 - 7, bot - gv * PH + 5.0, (\"%g\" % gv), 13,",
              "cv.text(x0 - 7, bot - gv * PH + 5.0, (\"%g\" % gv), FS(13) * _TS,")
s = s.replace("str(tv), 13, MUTED, \"middle\")", "str(tv), FS(13) * _TS, MUTED, \"middle\")")
s = s.replace("widths = [28 + cv.measure(n, 17) + 26 for _, n in items]",
              "widths = [28 + cv.measure(n, FS(17)) + 26 for _, n in items]")
s = s.replace("cv.text(lx + 28, legend_y + 2.0, name, 17)",
              "cv.text(lx + 28, legend_y + 2.0, name, FS(17))")

# 4. output suffix
s = s.replace("cv.save_svg_png(outname)",
              "cv.save_svg_png(outname.replace('.png', _SUFFIX + '.png'))")

open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('generator parameterised for print scale')
