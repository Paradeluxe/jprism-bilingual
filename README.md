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

### Model matrix

One English lens and one Chinese lens per row: the figures use 23 checkpoints (46 lenses), and the repository fits 38 rungs (76 lenses).

| Family | Checkpoint | Params | Layers | d_model | Attention | Weights |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3 | Qwen3-0.6B | 0.6B | 28 | 1024 | full | bf16 |
| | Qwen3-0.6B-FP8 | 0.6B | 28 | 1024 | full | FP8 |
| | Qwen3-0.6B-Q8_0 | 0.6B | 28 | 1024 | full | GGUF Q8_0 |
| | Qwen3-0.6B-Q6_K | 0.6B | 28 | 1024 | full | GGUF Q6_K |
| | Qwen3-0.6B-Q5_K_M | 0.6B | 28 | 1024 | full | GGUF Q5_K_M |
| | Qwen3-0.6B-Q4_K_M | 0.6B | 28 | 1024 | full | GGUF Q4_K_M |
| | Qwen3-0.6B-Q3_K_M | 0.6B | 28 | 1024 | full | GGUF Q3_K_M |
| | Qwen3-0.6B-Q2_K | 0.6B | 28 | 1024 | full | GGUF Q2_K |
| | Qwen3-1.7B-BNB4 | 1.7B | 28 | 2048 | full | bitsandbytes 4-bit |
| | Qwen3-1.7B-Q4_K_M | 1.7B | 28 | 2048 | full | GGUF Q4_K_M |
| | Qwen3-1.7B-Q3_K_M | 1.7B | 28 | 2048 | full | GGUF Q3_K_M |
| | Qwen3-1.7B-Q2_K | 1.7B | 28 | 2048 | full | GGUF Q2_K |
| | Qwen3-4B | 4B | 36 | 2560 | full | bf16 |
| | Qwen3-4B-AWQ | 4B | 36 | 2560 | full | AWQ |
| | Qwen3-8B | 8B | 36 | 4096 | full | bf16 |
| | Qwen3-8B-GPTQ-Int4 | 8B | 36 | 4096 | full | GPTQ-Int4 |
| | Qwen3-14B | 14B | 40 | 5120 | full | bf16 |
| | Qwen3-32B-FP8 | 32B | 64 | 5120 | full | FP8 |
| Qwen3.5 | Qwen3.5-0.8B | 0.8B | 24 | 1024 | linear | bf16 |
| | Qwen3.5-0.8B-FP8 | 0.8B | 24 | 1024 | linear | FP8 |
| | Qwen3.5-0.8B-Q8_0 | 0.8B | 24 | 1024 | linear | GGUF Q8_0 |
| | Qwen3.5-0.8B-Q6_K | 0.8B | 24 | 1024 | linear | GGUF Q6_K |
| | Qwen3.5-0.8B-Q5_K_M | 0.8B | 24 | 1024 | linear | GGUF Q5_K_M |
| | Qwen3.5-0.8B-Q4_K_M | 0.8B | 24 | 1024 | linear | GGUF Q4_K_M |
| | Qwen3.5-0.8B-Q4_K_S | 0.8B | 24 | 1024 | linear | GGUF Q4_K_S |
| | Qwen3.5-0.8B-Q3_K_M | 0.8B | 24 | 1024 | linear | GGUF Q3_K_M |
| | Qwen3.5-0.8B-Q2_K | 0.8B | 24 | 1024 | linear | GGUF Q2_K |
| | Qwen3.5-2B | 2B | 24 | 2048 | linear | bf16 |
| | Qwen3.5-2B-Q4_K_S | 2B | 24 | 2048 | linear | GGUF Q4_K_S |
| | Qwen3.5-2B-Q4_K_M | 2B | 24 | 2048 | linear | GGUF Q4_K_M |
| | Qwen3.5-2B-Q3_K_M | 2B | 24 | 2048 | linear | GGUF Q3_K_M |
| | Qwen3.5-2B-Q2_K | 2B | 24 | 2048 | linear | GGUF Q2_K |
| | Qwen3.5-9B | 9B | 32 | 4096 | linear | bf16 |
| Qwen3.6 | Qwen3.6-27B | 27B | 64 | 5120 | hybrid 3:1 | bf16 |
| Qwen3.8 | Qwen3.8-27B | 27B | 64 | 5120 | hybrid 3:1 | bf16 |
| Gemma-4 | Gemma-4-E2B | E2B | 35 | 1536 | — | bf16 |
| | Gemma-4-E4B | E4B | 42 | 2560 | — | bf16 |
| | Gemma-4-12B | 12B | 48 | 3840 | — | bf16 |

### Corpora

| Corpus | Source | Config | Windows | sha256 |
| --- | --- | --- | --- | --- |
| English | [`Salesforce/wikitext`](https://huggingface.co/datasets/Salesforce/wikitext) | `wikitext-103-raw-v1`, train | 1,000 × 128 | `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee` |
| Chinese | [`wikimedia/wikipedia`](https://huggingface.co/datasets/wikimedia/wikipedia) | `20231101.zh` | 1,000 × 128 | `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792` |

Both sources are released under CC BY-SA 3.0 and GFDL. The built files ship in [`corpora/`](corpora/), and the sha256 column is their digest. Each model re-tokenizes the decoded windows at fit time.

### Probes

| Probe | Prompt | Rank targets |
| --- | --- | --- |
| P1 | `Fact: The currency used in the country shaped like a boot is` | euro, eur |
| P2 | `The number of legs on the animal that spins webs is` | 8, eight |
| P3 | `The capital of France is` | paris |
| P4 | `Think of a sport: people kick a round ball into a net. The sport is` | football, soccer |

## Measurement

Every row of the results table rests on the same cells: one probe at one layer, read at the last position of both lenses, top-100 candidates.

| Reading | Supports | Definition |
| --- | --- | --- |
| Language shares | the lens and model rows | Share of a pool in four bands: English, Chinese, other language, non-language. Han is Chinese; Latin is English unless the hub table marks a foreign word; other scripts are other language; digits and symbols are non-language. |
| Blackout | the blackout row | A top-5 pool with no language token. |
| Overlap | the semantic row | Four measures at one layer. Without order, the better list's share of tokens that have a partner at depth x, counting identical or translated pairs (cross-language) or identical pairs only (within-language). With order, the share of same-rank pairs that are identical (within-language) or identical or translated (cross-language). |

Only language tokens are compared for overlap, and x is limited by the shorter list. Partners come from [`MUSE`](https://dl.fbaipublicfiles.com/arrival/dictionaries) dictionaries for ten languages both ways, an English-hub table for two-hop pairs, a frozen Qwen3.5-0.8B hub for Chinese tokens outside MUSE, and a morphological strip; [`opencc`](https://github.com/BYVoid/OpenCC) folds traditional and simplified forms. Strict matches are a subset of the semantic ones. The tables are local, not in git; `src/analysis/bilingual_align.py` loads them.

## Pipeline

The corpora ship in [`corpora/`](corpora/), and probes and ranks are fixed in `src/measure/pilot_core.py`. Five stages take them to audited numbers. Commands run from the repository root and write into `--root` (default `src/measure/`, the scripts' own directory).

### Environment

Python 3.10+ with a CUDA build of PyTorch:

```bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu124   # match your driver
pip install -e "git+https://github.com/anthropics/jacobian-lens#egg=jlens"
```

The quoted `pip` line matters: an unquoted `#egg=jlens` is a shell comment.

### Weights

`MODELS` in `src/measure/run_fit_sicc.py` maps each checkpoint to `~/models/<Name>`. Download what you need there with the Hugging Face CLI; Gemma checkpoints need the licence accepted on the Hub first.

```bash
pip install "huggingface_hub[cli]"
hf download Qwen/Qwen3-8B --local-dir ~/models/Qwen3-8B
```

Quantized variants follow the same layout, with GGUF files under `~/models/gguf/`; edit the `local` entry in `MODELS` if you keep weights elsewhere.

### Fit

One lens per corpus per model, one CUDA GPU per fit; our runs used an H800 80 GB or an A100 40 GB.

```bash
python src/measure/run_fit_sicc.py --model 8B --root data \
    --corpus corpora/wikitext_n1000_L128.jsonl --corpus-tag wikitext
python src/measure/run_fit_sicc.py --model 8B --root data \
    --corpus corpora/zhwiki_n1000_L128.jsonl --corpus-tag zhwiki
```

This writes `data/lenses/local/qwen3-8b/jlens_n1000_Lstep2_{wikitext,zhwiki}.pt` and a fit card beside them; the cards for the full matrix are in [`cards/`](cards/). Prompts with a non-finite Jacobian are skipped; a fit above 2% skips is refused. Fits resume from `data/fit_ckpt/`. Add `--limit 20` for a quick `.smoke` fit, and repeat per checkpoint in `MODELS`.

### Measure

```bash
python src/measure/measure_sicc.py --root data --only qwen3-8b --device cuda
```

Writes `data/RESULT/MEASURE_SICC/MEAS_<tag>_<corpus>_raw.json` plus a markdown summary. The cell, depth and match rules are the ones under Measurement.

### Audit and readings

```bash
python src/audit/full_audit.py data/lenses/local data/RESULT/MEASURE_SICC
python src/analysis/all_models_bilingual_html.py data/RESULT/MEASURE_SICC page.html
```

The first joins the four states per (model, corpus) and lists gaps; the second renders the paired readouts and the readings computed by `src/analysis/bilingual_align.py`. Both read only the raw JSON. The bilingual tables are not in git: `make_bilingual_lexicon.py` downloads the MUSE pairs, and `make_mt_hub.py` fills Chinese terms outside them from a local Qwen3.5-0.8B (set `MODEL_DIR` in that script).

Fitted lenses and raw measurements are not in git; the full matrix is about 31 GB and is rebuilt from the shipped corpora.

## References

Gurnee, W., et al. (2026). *Verbalizable Representations Form a Global Workspace in Language Models.* Jacobian-lens library: <https://github.com/anthropics/jacobian-lens>, Apache-2.0.

Merity, S., Xiong, C., Bradbury, J., and Socher, R. (2017). *Pointer Sentinel Mixture Models.* WikiText-103, used here as `Salesforce/wikitext`, config `wikitext-103-raw-v1`, train split.

Wikimedia Foundation. Chinese Wikipedia dump `wikimedia/wikipedia`, config `20231101.zh`.

## Acknowledgement

This work was performed in part at SICC which is supported by IOTSC of the University of Macau.
