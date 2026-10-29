## J-Prism: Language Models Think Semantically, with Preferred Languages

With the exact same **prompt**, **model**, and **layer**, Qwen and Gemma models were probed with **Chinese** J-lenses and **English** J-lenses.

The results could indicate:

| Interpretation | Evidence |
| --- | --- |
| The lens has a preference for languages | Each lens usually gives the larger share to the language it was fitted on. |
| The model has a preference for languages | The lens fitted on the model's own language usually reads a purer share of it than the other lens does. |
| The thinking has a preference for languages | A blackout usually falls on one lens while the other still reads. |
| The thinking is semantic | The two pools overlap in meaning across the two fitted languages and a small minority of other languages. |

![Figure 1](figures/fig1_composition.png)

**Figure 1.** Language composition of the candidate pools of both lenses. Currency probe at the last position, top-100 candidates; the four bands sum to one at every layer.

![Figure 2](figures/fig2_overlap.png)

**Figure 2.** Overlap between the candidate lists of the two lenses. Four measures per model on the currency probe at the last position, top-100 candidates.

![Figure 3](figures/fig3_blackouts.png)

**Figure 3.** Blackouts in five (model, probe) cells over three consecutive measured layers. Each bar gives the composition of that lens's top-100 pool; the ten highest-ranked candidates stand beside it.

## Materials

Two lenses per checkpoint, one per corpus. The matrix behind the figures is 23 checkpoints (46 lenses); the repository also fits the small-model quantized variants as separate rungs, for 38 rungs and 76 lenses in total.

| Corpus | Source | Config | Windows | sha256 |
| --- | --- | --- | --- | --- |
| English | [`Salesforce/wikitext`](https://huggingface.co/datasets/Salesforce/wikitext) | `wikitext-103-raw-v1`, train | 1,000 × 128 | `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee` |
| Chinese | [`wikimedia/wikipedia`](https://huggingface.co/datasets/wikimedia/wikipedia) | `20231101.zh` | 1,000 × 128 | `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792` |

Both corpora are cut in stream order with the Qwen3-0.6B tokenizer. The Chinese build adds Han-ratio guards, and both drop any window that contains a probe string or a listed answer paraphrase. Each model re-tokenizes the decoded windows with its own tokenizer at fit time. The built files ship in [`corpora/`](corpora/), and both sources are Wikipedia-derived under CC BY-SA 3.0 and GFDL.

| Family | Checkpoints | Layers | Precision |
| --- | --- | --- | --- |
| Qwen3, dense | 0.6B, 1.7B, 4B, 8B, 14B, 32B | 28, 28, 36, 36, 40, 64 | bf16, 32B as FP8 |
| Qwen3.5 | 0.8B, 2B, 9B | 24, 24, 32 | bf16 |
| Qwen3.6, Qwen3.8 | 27B each | 64 | bf16, hybrid attention |
| Gemma-4 | E2B, E4B, 12B | 35, 42, 48 | bf16 |

| Probe | Prompt | Rank targets |
| --- | --- | --- |
| P1 | `Fact: The currency used in the country shaped like a boot is` | euro, eur |
| P2 | `The number of legs on the animal that spins webs is` | 8, eight |
| P3 | `The capital of France is` | paris |
| P4 | `Think of a sport: people kick a round ball into a net. The sport is` | football, soccer |

## Measurement

Each lens is read at the last position of the four probes on every scored layer, and the top-100 candidates of each pool are stored per (probe, layer) cell with the answer rank, scanned to depth 500. Probes and ranks are fixed in `src/measure/pilot_core.py`.

| Reading | Definition |
| --- | --- |
| Hit@5, Hit@10 | Share of cells whose best rank for an answer-family token is at most 5 or 10. |
| Language composition | Share of the pool in four bands: English, Chinese, other language, non-language. Han script counts as Chinese; Latin script counts as English unless the hub table marks the token a foreign word; other scripts count as other language; digits and symbols as non-language. |
| Blackout | A top-5 pool with no language token in any slot. |
| Overlap | Four measures between the two lenses at the same layer. Without order, the share of one list's tokens that find a partner on the other, taking the better of the two lists: cross-language counts identical or translated partners, within-language identical partners only. With order, the share of same-rank pairs that are identical (within-language) or identical or translated (cross-language). |

The overlap score uses a bilingual lexicon: [`MUSE`](https://dl.fbaipublicfiles.com/arrival/dictionaries) dictionaries for ten languages in both directions, an English-hub table for two-hop pairs, a frozen Qwen3.5-0.8B translation hub for Chinese tokens outside MUSE, and a morphological strip so that a function word glued to a dictionary word still matches. Traditional and simplified forms are folded with [`opencc`](https://github.com/BYVoid/OpenCC). The tables are local and not in git; `src/analysis/bilingual_align.py` loads them.

## Pipeline

Two lenses per model, one per corpus, measured on the same probes and audited per cell. The code is in `src/`; per-lens provenance is in `cards/`.

1. **Corpora.** Two corpora of 1,000 non-overlapping 128-token windows, cut in stream order with the Qwen3-0.6B tokenizer: English WikiText-103 and Chinese Wikipedia (`20231101.zh`). The Chinese build adds Han-ratio guards, and both drop any window that contains a probe string or a listed answer paraphrase.
2. **Fit.** One lens per corpus per model, the Jacobian of the final-layer output with respect to an earlier residual stream, averaged over the 1,000 fitting windows in fp32 with every second source layer sampled. A prompt with a non-finite Jacobian is skipped, and a lens above 2% skips is refused. Entry point `src/measure/run_fit_sicc.py`; the registry in that file covers five families from 0.6B to 32B, with quantized variants as separate rungs.
3. **Measure.** Each lens is applied to the same four English probes at the last position of every scored layer, and the top-100 candidates are stored per cell with the answer rank. Entry point `src/measure/measure_sicc.py`; probes and ranks are fixed in `src/measure/pilot_core.py`.
4. **Score.** Hit@5 and Hit@10 per cell; the language composition of each pool (English, Chinese, other language, non-language); blackouts, a top-5 pool with no language token; and cross-language overlap, with and without order, over a bilingual lexicon (`src/analysis/bilingual_align.py`).
5. **Audit.** `src/audit/full_audit.py` joins four states per (model, corpus): lens file, measurement, prompt compliance, and fit card. A rung counts only when all four hold.

The fitted lenses and raw measurements are local (about 31 GB) and not in git; the code reproduces them from the corpora.

## Reproduce

```bash
pip install -e "git+https://github.com/anthropics/jacobian-lens#egg=jlens"
python src/measure/run_fit_sicc.py --model qwen3-0.6b
python src/measure/measure_sicc.py --only qwen3-0.6b
python src/audit/full_audit.py experiment/lenses/local experiment/RESULT/MEASURE_SICC
```

The quoted `pip` line matters: an unquoted `#egg=jlens` is a shell comment.

## References

Gurnee, W., et al. (2026). *Verbalizable Representations Form a Global Workspace in Language Models.* Jacobian-lens library: <https://github.com/anthropics/jacobian-lens>, Apache-2.0.

Merity, S., Xiong, C., Bradbury, J., and Socher, R. (2017). *Pointer Sentinel Mixture Models.* WikiText-103, used here as `Salesforce/wikitext`, config `wikitext-103-raw-v1`, train split.

Wikimedia Foundation. Chinese Wikipedia dump `wikimedia/wikipedia`, config `20231101.zh`.
