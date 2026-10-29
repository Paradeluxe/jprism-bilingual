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

One English lens and one Chinese lens per checkpoint. The figures use 23 checkpoints (46 lenses); the repository fits the small-model quantized variants as extra rungs, 38 in total (76 lenses).

| Corpus | Source | Config | Windows | sha256 |
| --- | --- | --- | --- | --- |
| English | [`Salesforce/wikitext`](https://huggingface.co/datasets/Salesforce/wikitext) | `wikitext-103-raw-v1`, train | 1,000 × 128 | `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee` |
| Chinese | [`wikimedia/wikipedia`](https://huggingface.co/datasets/wikimedia/wikipedia) | `20231101.zh` | 1,000 × 128 | `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792` |

Both sources are Wikipedia-derived, CC BY-SA 3.0 and GFDL. The built files ship in [`corpora/`](corpora/); each model re-tokenizes the decoded windows at fit time.

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

Each lens is read at the last position of the four probes on every scored layer. The top-100 candidates of each pool are stored per (probe, layer) cell with the answer rank, scanned to depth 500; `src/measure/pilot_core.py` fixes probes and ranks.

| Reading | Definition |
| --- | --- |
| Hit@5, Hit@10 | Share of cells whose best answer rank is at most 5 or 10. |
| Language composition | Share of the pool in four bands: English, Chinese, other language, non-language. Han is Chinese; Latin is English unless the hub table marks a foreign word; other scripts are other language; digits and symbols are non-language. |
| Blackout | A top-5 pool with no language token. |
| Overlap | Four measures at the same layer. Without order, the better list's share of tokens that have a partner at depth x, counting identical or translated pairs (cross-language) or identical pairs only (within-language). With order, the share of same-rank pairs that are identical (within-language) or identical or translated (cross-language). |

The overlap uses [`MUSE`](https://dl.fbaipublicfiles.com/arrival/dictionaries) dictionaries for ten languages both ways, an English-hub table for two-hop pairs, a frozen Qwen3.5-0.8B hub for Chinese tokens outside MUSE, and a morphological strip; [`opencc`](https://github.com/BYVoid/OpenCC) folds traditional and simplified forms. The tables are local, not in git; `src/analysis/bilingual_align.py` loads them.

## Pipeline

One English lens and one Chinese lens per model, measured on the same probes and audited per cell. Code in `src/`; per-lens provenance in `cards/`.

1. **Corpora.** 1,000 non-overlapping 128-token windows per corpus, cut in stream order with the Qwen3-0.6B tokenizer; the Chinese build adds Han-ratio guards, and both drop windows that contain a probe or a listed answer paraphrase.
2. **Fit.** One lens per corpus per model, the Jacobian of the final-layer output with respect to an earlier residual stream, averaged over the 1,000 windows in fp32, sampling every second source layer. Prompts with a non-finite Jacobian are skipped; a lens above 2% skips is refused. Registry: `src/measure/run_fit_sicc.py`.
3. **Measure.** Both lenses applied to the four probes at the last position of every scored layer; the readout is defined under Measurement. `src/measure/measure_sicc.py`.
4. **Score.** Hit rates, language composition, blackouts and overlap, as defined under Measurement. `src/analysis/bilingual_align.py`.
5. **Audit.** Four states per (model, corpus), joined by `src/audit/full_audit.py`: lens file, measurement, prompt compliance, fit card. A rung counts when all four hold.

Fitted lenses and raw measurements are local (about 31 GB) and not in git; the code rebuilds them from the corpora.

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
