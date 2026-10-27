# Measurement protocol (v1-full-gurnee)

This is the locked protocol every lens pair in `cards/` was produced under. It is
reproduced here so the FIT_CARDs are interpretable without the original lab wiki.

## Fitting

- One lens = the Jacobian of the final-layer output (up to the second-to-last
  block, i.e. J_{l→L-1}) averaged over a fitting corpus of **1,000 sequences of
  128 tokens**, accumulated in fp32, weights loaded in bf16.
- Source layers are sampled every 2 layers from layer 2 (layer 0 never scored).
- Skip rule: a prompt whose per-layer Jacobian contains non-finite entries is
  skipped and recorded (skip rate is a FIT_CARD field).
- Two corpora, one per language (`corpora/`), built with a single fixed
  tokenizer (Qwen3-0.6B) so both arms are identical on every axis except text.

## Probes (fixed battery)

| ID | Probe | Answer-family targets |
|----|-------|-----------------------|
| P1 | `Fact: The currency used in the country shaped like a boot is` | euro, Euro, Italy, Italian, european |
| P2 | spider legs (classic) | 8, eight |
| P3 | France capital (classic) | Paris, 巴黎 |
| P4 | kick-ball sport (classic) | football, soccer |

The scoring core (`rank_targets` / `honest_cues`, incl. the european≠euro
exclusion) lives in one place only: `src/measure/pilot_core.py`. All measurement
scripts import it; nothing re-implements it.

## Readout and scoring

- Hit@5 / Hit@10 are computed over **(probe × layer) cells** at the last
  position (`pos=-1`) of each probe; `pos=-2` and content positions are stored
  but never mixed into the main table.
- A cell counts as a hit when the best answer-family token appears in the
  lens's top-5 / top-10 readout at that layer.
- `j_rank` is the rank of the answer token in the **full vocabulary** ordering
  induced by the lens readout, scanned to depth 500 (beyond 500 → None).
- The model's own final-layer hit rate over the same probes is recorded as
  `model_hit5` — a property of the model alone, identical across the two arms;
  it doubles as a vocabulary-alignment self-check (a tokenizer mismatch makes
  it 0.0).
- Candidate lists are stored to depth 100 (`j_top5` field name is historical).

## The four states of a rung (never collapse them)

1. **fit 出片** — the lens `.pt` exists
2. **测量有数** — a Hit@5/Hit@10 report exists
3. **合规** — actual n_prompts meets the protocol
4. **有记录** — a FIT_CARD exists (path, corpus sha256, dtype, VRAM, wallclock, skips)

A ladder that reports 100% while collapsing these is reporting nothing.
`src/audit/full_audit.py` checks all four per (tag, corpus); `src/audit/
matrix_audit.py` is the set-difference view.

## Known precision caveat (Gemma-4)

Gemma-4 applies final-logit softcapping (30·tanh(x/30)); under bf16 the
saturated logits collapse to exact ties and top-5 membership inside a tie block
is arbitrary. Gemma hit rates are therefore read with the margin stated in the
paper; Qwen families show zero cross-node rank flips.
