# Supplementary package

Inventory and folder layout for the material that accompanies the manuscript.
Generated 2026-11-26 18:18.

**File count:** 72 — 5 tables, 63 figures, 2 documents, and 2 manifest files
(`MANIFEST.md`, `MANIFEST.csv`).

## Tree

```
supplementary/
├── README.md                             # codebook: where to look, columns, filters
├── MANIFEST.md                           # this file
├── MANIFEST.csv                          # machine-readable inventory
├── tables/                               # 5 CSV files
│   ├── contrast-tables.csv
│   ├── cell-means.csv
│   ├── omnibus-terms.csv
│   ├── post-training-lens-balanced.csv
│   └── post-training-by-lens.csv
└── figures/                              # 63 PNG files + gallery
    ├── FIGURES.md                        # Appendix Figures A1–A63 with captions
    └── figure-a01.png … figure-a63.png
```

## Tables

| file | data rows | bytes | sha256 (first 16) |
| --- | ---: | ---: | --- |
| `tables/cell-means.csv` | 3,033 | 266,769 | `38eb87b1b93461ac…` |
| `tables/contrast-tables.csv` | 12,996 | 2,015,786 | `e95c106615ee187f…` |
| `tables/omnibus-terms.csv` | 819 | 80,219 | `29469e744033bfe1…` |
| `tables/post-training-by-lens.csv` | 27 | 4,569 | `bc0ba95c77ef437a…` |
| `tables/post-training-lens-balanced.csv` | 9 | 1,525 | `0d638537c34d1512…` |

## Where the manuscript points

| the manuscript says | file |
| --- | --- |
| "the complete contrast tables" | `tables/contrast-tables.csv` |
| "the cell means" | `tables/cell-means.csv` |
| "the omnibus terms" | `tables/omnibus-terms.csv` |
| "the post-training comparison" | `tables/post-training-lens-balanced.csv`, `tables/post-training-by-lens.csv` |
| "Figures A1 through A63" | `figures/` (gallery in `figures/FIGURES.md`) |

## Figures

`figures/` holds the 63 appendix figures (A1–A63) as PNG, with the gallery and captions in
`figures/FIGURES.md`.

## Provenance

The five tables were copied from the analysis outputs on 2026-11-25; the exact source path
and timestamp for each file are in `MANIFEST.csv`. The 63 figures are the manuscript's
appendix figures, rendered at 1800 px wide.

**Caveat.** The statistical batch predates the ongoing float32 lens refit (4 of 16 lenses
refit as of 2026-11-26 17:52). The tables will be regenerated from the refit analysis
before submission.
