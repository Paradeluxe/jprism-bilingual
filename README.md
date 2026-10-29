## J-Prism: Language Models Think Semantically, with Preferred Languages

With the exact same **prompt**, **model**, and **layer**, Qwen and Gemma models were probed with **Chinese** J-lenses and **English** J-lenses.

The results could indicate:

| Interpretation | Evidence |
| --- | --- |
| The lens has a preference for languages | Each lens usually gives the larger share to the language it was fitted on. |
| The model has a preference for languages | The lens fitted on the model's own language usually reads a purer share of it than the other lens does. |
| The thinking has a preference for languages | A blackout usually falls on one lens while the other still reads. |
| The thinking is semantic | The two pools overlap in meaning across the two fitted languages and a small minority of other languages. |

## Figures

![Figure 1](figures/fig1_composition.png)

**Figure 1.** Language composition of the candidate pools of both lenses. Currency probe at the last position, top-100 candidates; the four bands sum to one at every layer.

![Figure 2](figures/fig2_overlap.png)

**Figure 2.** Overlap between the candidate lists of the two lenses. Four measures per model on the currency probe at the last position, top-100 candidates.

![Figure 3](figures/fig3_blackouts.png)

**Figure 3.** Blackouts in five (model, probe) cells over three consecutive measured layers. Each bar gives the composition of that lens's top-100 pool; the ten highest-ranked candidates stand beside it.

## 1. Question

The global-workspace claim says that a language model maintains a late representation that can be read out as words. If that space were only a property of the weights, two lenses of the same model would verbalize the same probes in the same way. If the space also carries the language it was estimated on, the English-fitted lens and the Chinese-fitted lens will disagree: in which language the top of the readout sits, and in whether the answer token is near the top at all.

| Held fixed                                       | Allowed to vary                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| Model weights                                    | Fitting corpus (English or Chinese)                                      |
| Window budget: 1,000 × 128 tokens                | <br />                                                                   |
| Tokenizer used to *cut* the windows (Qwen3-0.6B) | Each model re-tokenizes those windows with its own tokenizer at fit time |
| Probe strings and answer families                | <br />                                                                   |
| Layer schedule, dtype, skip rule, scoring code   | <br />                                                                   |

The corpus is the only intended difference between the two lenses of a pair. [`docs/CORPORA.md`](docs/CORPORA.md) and [`docs/PROTOCOL.md`](docs/PROTOCOL.md) record that claim. `src/measure/pilot_core.py` defines the probes and the ranks. Measurement scripts import it and do not reimplement it.

## 2. The lens

One lens is the Jacobian of the final-layer output with respect to an earlier residual stream, taken up to the second-to-last block ($J_{\ell \to L-1}$), and averaged over the fitting corpus. Accumulation is fp32. Weights are loaded in bf16. Source layers are every second layer from layer 0 up to, and not including, the final layer. The primary measurement never scores layer 0: it requests layers $2, 4, \ldots$ and keeps only those the lens actually contains.

A prompt whose per-layer Jacobian contains a non-finite value is skipped. Summing that prompt would corrupt the average. The skip rate is a field on the fit card. A skip rate above 2% is refused, because the kept prompts would be a biased subset and the lens would no longer match the rest of the table. A Qwen3-4B-AWQ fit at 0.3% was kept. A Qwen3-8B-AWQ fit at 24% was refused.

The first 16 token positions of each window are skipped (`skip_first=16`), so a window must re-encode to more than 17 tokens. Sequence length is capped at 128.

## 3. Corpora

Both corpora live in [`corpora/`](corpora/). Build cards: [`corpora/CORPUS_CARD.md`](corpora/CORPUS_CARD.md), [`corpora/CORPUS_CARD_zhwiki.md`](corpora/CORPUS_CARD_zhwiki.md).

| File                        | Source                                              | Windows     | sha256                                                             |
| --------------------------- | --------------------------------------------------- | ----------- | ------------------------------------------------------------------ |
| `wikitext_n1000_L128.jsonl` | `Salesforce/wikitext`, `wikitext-103-raw-v1`, train | 1,000 × 128 | `dacf54ddf125c2d906e0b5634cfc95972decc75a0843933d1fb2aad2795a21ee` |
| `zhwiki_n1000_L128.jsonl`   | `wikimedia/wikipedia`, `20231101.zh`                | 1,000 × 128 | `f1b108c43abbabb1acc5c44ae18633b1daebe657b9f44aa393548974cbbd2792` |

Shared build rules:

- Non-overlapping 128-token windows, cut in stream order with the Qwen3-0.6B tokenizer (`add_special_tokens=False`). No shuffle. Seed `20260913` is recorded; the slice does not use it to permute.
- No padding. The English slice re-encodes at exactly 128 tokens on all 1,000 rows.
- Windows whose decoded text contains a probe string, or a listed paraphrase of a probe answer, are dropped before the slice is closed.
- The same filename is never rebuilt on another machine. Move the file, or finish that arm where it was built.

The Chinese arm adds a Han-ratio guard: a line below 0.5, or a window below 0.4, is dropped, which removes code, URLs, and boilerplate. On the selected 1,000 windows the Han ratio has minimum 0.41 and mean 0.84; characters per window run from 128 to 307, mean 184. One Chinese row re-encodes at 127 tokens; the rest re-encode at 128.

At fit time each model tokenizes the decoded string with its own tokenizer, with the transformers default of adding special tokens, then truncates to 128. The content budget is therefore `128` minus however many special tokens that tokenizer inserts. Gemma-4's BOS leaves 127 content tokens. `src/analysis/tokenizer_consistency.py` and `src/analysis/tok_window_len_all.py` measure that shift per family. Qwen3.5, Qwen3.6, and the Gemma-4 sizes each share tokenizer bytes inside the family; Qwen3.8-27B uses a separate 248k vocabulary.

## 4. Model matrix

The registry is `MODELS` in `src/measure/run_fit_sicc.py`. Per-lens provenance (path, layer list, corpus hash, dtype, VRAM, wall clock, skip rate) is a fit card in [`cards/`](cards/). Smoke cards (`*.smoke.md`) are short runs used to check a ladder rung; `src/audit/full_audit.py` does not count a `.smoke` file as a lens.

The groups in this section follow the registry comments and [`cards/FIT_CARD_qwen3-32b-fp8.NOTE.md`](cards/FIT_CARD_qwen3-32b-fp8.NOTE.md). Several fit cards repeat a template track line. Where that line disagrees with the registry or the note, use those two sources.

Dense Qwen3. Qwen3-0.6B (28 layers, $d=1024$), 1.7B, 4B, 8B (36 layers), 14B (40 layers), and the 32B cell (64 layers). The 14B English lens is a merge of disjoint prompt ranges through `JacobianLens.merge`, still over 1,000 kept prompts. The bf16 Qwen3-32B checkpoint is 65.5 GB and cannot run the fit's backward pass on an 80 GB card: bf16 at `dim_batch=2`, the same run with gradient checkpointing, and checkpointing at `dim_batch=1` all OOM, the last with 142 MiB free of 79.18 GiB. The official FP8 checkpoint (`Qwen/Qwen3-32B-FP8`, tag `qwen3-32b-fp8`) fills that cell. It has the same 64-layer dense layout and the same 32.76B parameters. Keep it off the GGUF bit-width ladder and out of the bf16 rows. A dense-versus-hybrid comparison that uses it changes architecture and weight precision together. A bf16 32B cell needs a multi-GPU allocation. The backward pass runs through the unembedding and has not been checked across devices here.

Hybrid and Qwen3.5. Qwen3.5-0.8B and Qwen3.5-2B (24 layers) are the dense-tokenizer-family baselines the GGUF arms are compared with. Qwen3.5-4B and Qwen3.5-9B (32 layers) are appendix rungs. Qwen3.6-27B and Qwen3.8-27B (64 layers) share the 27B scale and a hybrid schedule of three linear-attention blocks per full-attention block, one generation apart, both in bf16. That pair holds scale and precision fixed and changes generation. Qwen3.6-27B is in the hybrid group.

Gemma-4 mirror. E2B (35 layers), E4B (42), 12B (48), with 31B registered on the same tokenizer. These are the foreign-architecture arm. Their hit rates are read with the softcap caveat in Section 8.

Quantization ladder. On the small models the bit-width series is GGUF `Q2_K`, `Q3_K_M`, `Q4_K_S`, `Q4_K_M`, `Q5_K_M`, `Q6_K`, and `Q8_0`, plus separate AWQ, GPTQ-Int4, bitsandbytes 4-bit, and official FP8 checkpoints. The GGUF series asks at which width the readout breaks, within one model. Official FP8 checkpoints are published weight sets, with their own tags, and are kept separate from that series.

## 5. Probes and scoring

Four probes, fixed in `CLASSIC` inside `src/measure/pilot_core.py`. The primary answer list is what `rank_targets` scans. `honest_cues` also records Italy on the boot probe. That cue is separate from the rank target.

| ID | Key              | Prompt                                                                | Rank targets     |
| -- | ---------------- | --------------------------------------------------------------------- | ---------------- |
| P1 | `boot_currency`  | `Fact: The currency used in the country shaped like a boot is`        | euro, eur        |
| P2 | `spider_legs`    | `The number of legs on the animal that spins webs is`                 | 8, eight         |
| P3 | `france_capital` | `The capital of France is`                                            | paris            |
| P4 | `sport`          | `Think of a sport: people kick a round ball into a net. The sport is` | football, soccer |

A match is a decoded token, stripped and lower-cased, equal to a target. The string `european` does not count as `euro`. Ranks are scanned to depth 500; past that the rank is missing.

The unit of the main table is a cell: one probe at one layer, read at the last position (`pos=-1`). `pos=-2` is stored and kept out of the aggregate. Hit\@5 / Hit\@10 is the fraction of cells whose best target rank is at most 5 or 10. `j_rank` is that rank in the full vocabulary order induced by the lens. Candidate strings are stored to depth 100; the JSON field is still named `j_top5`. Hit\@5 and Hit\@10 come from `j_rank`, so storing a longer candidate list does not change them.

`model_hit5` is the model's own final-layer Hit\@5 on the same four prompts. It does not depend on which lens is applied. A value of 0 means the tokenizer does not match. Each report also stores a 24-token greedy continuation. The continuation is excluded from the hit rate.

The measurement entry point is `src/measure/measure_sicc.py`. It joins each `jlens_n1000_Lstep2_{wikitext,zhwiki}.pt` to the registry, applies the lens on CPU or GPU, and writes `MEAS_<tag>_<corpus>_raw.json` plus a short markdown summary. Cluster and local numbers are the same measurement because both import `pilot_core`.

## 6. Comparing the two readouts

Hit rate records whether the answer token is near the top. `src/analysis/bilingual_align.py` scores the top-$x$ of a paired readout, which asks whether the English list and the Chinese list name the same things. $x$ is the depth of that comparison (5, 10, or 100), limited by the shorter list. Language tokens contain a letter; digits and symbols are left out of the comparison. A token with a Han character is Chinese. A Latin token is English unless the hub table marks it as a foreign word translated through English.

Five scores, all independent of which list is written first:

| Score                           | Definition                                                                                      |
| ------------------------------- | ----------------------------------------------------------------------------------------------- |
| Language bias                   | (English tokens on the English list + Chinese tokens on the Chinese list) / $2x$                |
| Semantic coverage               | Fraction of language tokens on either list that have at least one semantic partner on the other |
| Semantic density                | Number of semantic pairs / $x^2$                                                                |
| Strict overlap                  | Multiset of identical strings, divided by $x$                                                   |
| Same-position strict / semantic | Share of aligned ranks that are string-identical, or string-identical or translations           |

Semantic partners are string-identical after normalization, or translations. Translations come from a MUSE bilingual lexicon, an English-hub table of two-hop links, a frozen machine-translation hub for Chinese tokens outside the lexicon, and a small morphological strip (so that a function word glued to a dictionary word can still match). Strict overlap is always at most the semantic score. The resources are built by `make_bilingual_lexicon.py` and `make_mt_hub.py`.

`bilingual_top5_html.py`, `bilingual_top100_rbo_html.py`, and `all_models_bilingual_html.py` render the paired top-$k$ for every model that has both corpora. A model missing one corpus is listed as missing.

`src/analysis/intervene.py` edits one residual stream during the forward pass (`add`, `proj_out`, `scale`, or `swap`) and records the model top-$k$, the lens readout, and an optional greedy continuation. The hit-rate protocol does not use it.

## 7. When a rung counts

A rung has four states. The four are separate. A ladder that reports 100% by collapsing them has not reported the rung.

1. Lens file. `jlens_n1000_Lstep2_<corpus>.pt` exists.
2. Measurement. A Hit\@5 / Hit\@10 report exists for that lens.
3. Compliance. The number of prompts actually used meets the protocol ($N=1000$, skip rate at most 2%).
4. Record. A fit card names the path, corpus sha256, dtype, VRAM, wall clock, and skips.

`src/audit/full_audit.py` joins these per `(tag, corpus)`. The pair is parsed from the filename with a regular expression. Splitting on underscores mis-parses tags such as `qwen3-0.6b-q8_0` and has previously produced both phantom gaps and phantom completeness. The checker ignores `.smoke`, quarantine, and dirty lens files, and it flags a measurement that contains a non-finite score. `matrix_audit.py` is the set-difference view of the same matrix. `nan_audit.py` quarantines non-finite lens and measurement files. `build_results.py` renders the markdown results page from the raw JSON. `comparability_audit.py` checks two known ways a rung can leave the protocol: the offline kernel snapshot used for FP8 measurement, and the switch of lens storage from fp16 to fp32 on 10 October 2026. Lenses already on disk before that date are fp16.

## 8. Precision caveats

Gemma-4 softcap. Gemma-4 applies a final-logit softcap, $30 \tanh(x/30)$. In bf16, saturated logits collapse to exact ties, and membership inside a tie block is arbitrary. Gemma hit rates are read with the margin reported in the paper. Qwen families in this protocol show no cross-node rank flips of that kind.

FP8 32B. Until a bf16 32B lens exists, a dense-versus-hybrid comparison at this scale also changes weight precision. See Section 4.

Retokenization. Windows are equal in the Qwen3-0.6B token count. They are equal in another family's token count only to the extent `tok_window_len_all.py` measures. A family that spends a token on BOS, or that retokenizes Chinese much more densely, is fitting a different effective body of text.

Fit-card track line. Use Section 4, the registry, and `FIT_CARD_qwen3-32b-fp8.NOTE.md` when a card's track line disagrees with them.

## 9. Local layout

On this machine the code, the experiment, and the manuscript sit in one working tree. Git tracks the code and this report. `experiment/` and `manuscript/` are on disk and listed in `.gitignore`.

| Part                                        | Path                                                   | In git |
| ------------------------------------------- | ------------------------------------------------------ | ------ |
| Code and this report                        | repository root, `src/`, `cards/`, `corpora/`, `docs/` | yes    |
| Lenses, measurements, lexicons, lab scripts | [`experiment/`](experiment/)                           | no     |
| Manuscript, figures, reviews                | [`manuscript/`](manuscript/)                           | no     |

`experiment/` is the former `jspace-qwen-exp` tree: `lenses/local` (about 31 GB of `.pt` files), `RESULT/MEASURE_SICC` (the raw Hit\@5 / Hit\@10 JSON), `fit_corpus/`, the bilingual lexicons, and the lab scripts. `manuscript/` is the former `paper-writing/projects/jspace-bilingual` tree, including `draft.md`, the October 2026 docx, `fig/`, and `refs/`.

The old paths are directory junctions, so existing absolute paths keep resolving:

- `E:\hermes_playground\jspace-qwen-exp` → `experiment/`
- `E:\hermes_playground\paper-writing\projects\jspace-bilingual` → `manuscript/`

The Jacobian-lens implementation is still [anthropics/jacobian-lens](https://github.com/anthropics/jacobian-lens). Paths inside the scripts still assume the original project layout (`~/jspace` on the cluster, local Hugging Face caches on the workstation). Those paths have not been rewritten.

`paper-writing` was once synced to another machine by a Syncthing client running under WSL. That client has been removed from this machine. While it ran it recorded the junction as a zero-byte symlink entry, so the manuscript was never uploaded a second time.

## 10. Reproduce

1. Install the upstream library:
   ```bash
   pip install -e "git+https://github.com/anthropics/jacobian-lens#egg=jlens"
   ```
2. Fit one pair (one lens per corpus):
   ```bash
   python src/measure/run_fit_sicc.py --model qwen3-0.6b
   ```
3. Measure:
   ```bash
   python src/measure/measure_sicc.py --only qwen3-0.6b
   ```
4. Audit the four states:
   ```bash
   python src/audit/full_audit.py lenses/local RESULT/MEASURE_SICC
   ```

The quoted `pip` line matters: an unquoted `#egg=jlens` is a shell comment.

## 11. Repository map

| Path                                   | Role                                                                                                                    |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| [`src/measure/`](src/measure/)         | Fit entry point and model registry (`run_fit_sicc.py`), measurement (`measure_sicc.py`), scoring lock (`pilot_core.py`) |
| [`src/fit/`](src/fit/)                 | Single-GPU fit drivers                                                                                                  |
| [`src/audit/`](src/audit/)             | Four-state audit, matrix diff, NaN quarantine, results page, comparability audit                                        |
| [`src/analysis/`](src/analysis/)       | Corpus builders, tokenizer-window audits, bilingual alignment and HTML viewers, intervention                            |
| [`corpora/`](corpora/)                 | The two fitting corpora                                                                                                 |
| [`cards/`](cards/)                     | One fit card per lens                                                                                                   |
| [`docs/PROTOCOL.md`](docs/PROTOCOL.md) | Locked measurement protocol                                                                                             |
| [`docs/CORPORA.md`](docs/CORPORA.md)   | Corpus provenance                                                                                                       |
| [`experiment/`](experiment/)           | Local lenses, measurements, lexicons, and lab scripts (not in git)                                                      |
| [`manuscript/`](manuscript/)           | Local manuscript, figures, and reviews (not in git)                                                                     |

## References

Gurnee, W., et al. (2026). *Verbalizable Representations Form a Global Workspace in Language Models.* Jacobian-lens library: <https://github.com/anthropics/jacobian-lens>, Apache-2.0.

Merity, S., Xiong, C., Bradbury, J., and Socher, R. (2017). *Pointer Sentinel Mixture Models.* WikiText-103, used here as `Salesforce/wikitext`, config `wikitext-103-raw-v1`, train split.

Wikimedia Foundation. Chinese Wikipedia dump `wikimedia/wikipedia`, config `20231101.zh`.

## License

Apache-2.0 covers everything in this repository. The upstream Jacobian-lens library is Anthropic's, also Apache-2.0, and is a declared dependency. The lens algorithm stays in that library.

If you use the code, cite `CITATION.cff`.

## Author

Code and analyses: Zhengyuan Liu. The full author list is in the accompanying paper.
