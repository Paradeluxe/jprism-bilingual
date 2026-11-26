"""Measure the outer margins of a rendered figure plate.

Usage: python audit.py <png>
Prints JSON: image size, margins in pixels and in canvas units (the plates are
rasterized at 2x), and the content bounding box.
"""
import json
import sys

from PIL import Image
import numpy as np


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: audit.py <png>"}))
        return 1
    path = sys.argv[1]
    image = Image.open(path).convert("RGB")
    pixels = np.asarray(image)
    ink = pixels.min(axis=2) < 245
    height, width = ink.shape
    rows = np.where(ink.any(axis=1))[0]
    cols = np.where(ink.any(axis=0))[0]
    if not len(rows) or not len(cols):
        print(json.dumps({"error": "blank image", "width": width, "height": height}))
        return 0
    margin = {
        "top": int(rows[0]),
        "bottom": int(height - 1 - rows[-1]),
        "left": int(cols[0]),
        "right": int(width - 1 - cols[-1]),
    }
    result = {
        "image": {"width": width, "height": height},
        "marginPx": margin,
        "marginUnits": {k: round(v / 2.0, 1) for k, v in margin.items()},
        "content": {
            "left": int(cols[0]),
            "top": int(rows[0]),
            "right": int(cols[-1]),
            "bottom": int(rows[-1]),
            "width": int(cols[-1] - cols[0] + 1),
            "height": int(rows[-1] - rows[0] + 1),
        },
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
