# jspace-bilingual-lens

Code and analyses for a controlled comparison of Jacobian lenses fitted on
English versus Chinese corpora, applied to the same models and the same
probes.

This repository contains the analyses. It is **not** the J-lens implementation —
it depends on [anthropics/jacobian-lens](https://github.com/anthropics/jacobian-lens)
(Apache-2.0; see Gurnee et al., 2026, *Verbalizable Representations Form a
Global Workspace in Language Models*) — and it is **not** the paper full text
(manuscript in preparation).

Code and analyses: Zhengyuan Liu; full author list in the accompanying paper.

## What is here

| path | contents |
|------|----------|
| `src/measure/` | the fit entry point + model registry (`run_fit_sicc.py`), the measurement engine (`measure_sicc.py`), and the single source of truth for probes and scoring (`pilot_core.py`) |
| `src/fit/` | local (single-GPU) fit drivers |
| `src/audit/` | four-state audits (`full_audit.py`, `matrix_audit.py`, `nan_audit.py`), results-page generator (`build_results.py`), comparability audit |
| `src/analysis/` | corpus builders, tokenizer/window audits, bilingual alignment and candidate-pool analyses, HTML viewers, intervention experiments |
| `corpora/` | the two fitting corpora — the only thing that differs between the two lenses of a pair (see `docs/CORPORA.md`) |
| `cards/` | per-lens fit record cards (FIT_CARD): lens path, layer list, corpus hash, dtype, VRAM, wallclock, skip rate |
| `docs/` | the locked measurement protocol and corpus provenance |

## Reproduce (outline)

Paths inside the scripts assume the original project layout; a tidy-up pass is
welcome but not done yet.

1. Install the upstream lens library:
   `pip install -e git+https://github.com/anthropics/jacobian-lens#egg=jlens`
2. Fit a pair (one per corpus): `python src/measure/run_fit_sicc.py --model qwen3-0.6b`
3. Measure: `python src/measure/measure_sicc.py --only qwen3-0.6b`
4. Audit the matrix: `python src/audit/full_audit.py lenses/local RESULT/MEASURE_SICC`

Lenses and raw readout JSONs are not in this repository (multi-GB); the
FIT_CARDs in `cards/` record where each one was produced.

## License

Apache-2.0 for everything in this repository. The upstream Jacobian-lens
library is Anthropic's, also Apache-2.0, and is a declared dependency — the
lens algorithm itself is not this repository's contribution.
