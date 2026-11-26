# Supplementary tables

Tidy result files behind the manuscript. Everything lives under `supplementary/` in the
[J-Prism repository](https://github.com/Paradeluxe/jprism-bilingual).

## Where to look

| the manuscript says | open this |
| --- | --- |
| "the complete contrast tables" | `tables/contrast-tables.csv` |
| "the cell means" | `tables/cell-means.csv` |
| "the omnibus terms" | `tables/omnibus-terms.csv` |
| "the post-training comparison" | `tables/post-training-lens-balanced.csv`, `tables/post-training-by-lens.csv` |
| "Figures A1 through A63" | `figures/` (gallery in `figures/FIGURES.md`) |

## Models

Thirteen checkpoints enter every table: gemma4-e2b, gemma4-e4b, gemma4-12b, qwen3-0.6b,
qwen3-4b, qwen3-8b, qwen3-14b, qwen3.5-0.8b, qwen3.5-2b, qwen3.5-9b, qwen3.6-27b,
qwen3.8-27b, arete-27b.

## Files

### `tables/contrast-tables.csv`

One row per model × outcome × contrast, from the per-outcome linear mixed models.

| column | meaning |
| --- | --- |
| `tag` | model checkpoint |
| `dv` | outcome: `share_en`, `share_zh`, `share_ru`, `share_other`, `share_non`, `blackout_pool`, `blackout_excl`, `blackout_alive`, `overlap` |
| `focus` | the factor the contrast tests (`lens_lang`, `prompt_lang`, `item_type`, `sem_type`, `prompt`, `family`) |
| `by`, `by_level` | the cell at which the contrast is evaluated (`all`, one factor level, or `level|level` for cell-level simple effects) |
| `contrast` | `a - b` in the factor's own labels: `en`/`ru`/`zh`; `P1`/`P3`/`P4`; `cross`/`cross_ordered`/`identical`/`identical_ordered` |
| `estimate`, `SE`, `df`, `t`, `p` | model estimate and test statistics |

### `tables/cell-means.csv`

Cell means on the arcsine scale (`mean_asin`) and back-transformed percentage points
(`mean_pct`), one row per model × outcome × cell.

| column | meaning |
| --- | --- |
| `tag`, `dv` | model checkpoint, outcome |
| `prompt_lang`, `lens_lang` | factor levels (`en`/`zh`/`ru`) |
| `item_type` | probe family (`P1` country–capital, `P3` definitional, `P4` category–clue) |
| `sem_type` | overlap type (`cross`, `cross_ordered`, `identical`, `identical_ordered`) |
| `prompt`, `family` | the overlap model's prompt and family labels |
| `mean_asin`, `mean_pct` | cell mean on the arcsine scale and in percentage points |

### `tables/omnibus-terms.csv`

Type III omnibus tests, one row per model × outcome × term.

| column | meaning |
| --- | --- |
| `tag`, `dv`, `effect` | model checkpoint, outcome, model term |
| `F`, `df1`, `df2`, `p` | test statistics |

### `tables/post-training-lens-balanced.csv`

Lens-balanced Arete-27B minus Qwen3.8-27B posterior differences, for the five composition
bands and the four ILR coordinates.

| column | meaning |
| --- | --- |
| `scale`, `component`, `comparison` | band/ILR scale, component, `Arete - Qwen3.8` |
| `median`, `l95`, `u95` | posterior median and 95% credible interval |
| `mean`, `sd`, `p_gt0`, `p_lt0`, `pd`, `n_draws` | posterior summary |

### `tables/post-training-by-lens.csv`

The same difference computed separately under each fitted lens; the extra `lens_lang`
column takes `en`, `zh` or `ru`.

## Reproducing the tables quoted in the appendix

- **Lens simple effects** (lens language within each prompt language × probe family):
  `contrast-tables.csv` with `by = "cell"` and `focus = "lens_lang"`. The difference in
  percentage points is the difference of `mean_pct` between the two lens levels in
  `cell-means.csv`; report the range over models, the |t| range, and the largest p.
- **Overlap-type simple effects**: `dv = "overlap"`, `by = "cell"`, `focus = "sem_type"`.
- **Prompt simple effects**: `by = "cell"`, `focus = "prompt_lang"`.
- **Two-way simple effects**: `by = "prompt_lang"`, `"lens_lang"` or `"item_type"` (and the
  overlap analogues), one row per moderator level.
- **Omnibus tests**: `omnibus-terms.csv`.

## Figures

`figures/` holds the 63 appendix figures (A1–A63) as PNG, with the gallery and captions in
`figures/FIGURES.md`.

## License

The data files follow the repository license in `../LICENSE`.
