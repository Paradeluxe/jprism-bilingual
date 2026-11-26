# Manuscript refresh report

Generated after rebuilding the analysis for **10 models**.

## Models in the analysis

- **Gemma-4**: Gemma-4-E2B, Gemma-4-E4B, Gemma-4-12B
- **Qwen3**: Qwen3-0.6B, Qwen3-4B, Qwen3-8B, Qwen3-14B
- **Qwen3.5**: Qwen3.5-0.8B, Qwen3.5-2B, Qwen3.5-9B

## Figure inventory

- Figure 1 image: 10.2 x 20.6 cm
- Figure 2 image: 16.5 x 18.1 cm
- Figure 3 image: 14.5 x 20.4 cm
- Figure 4 image: 16.5 x 8.5 cm

## Paragraphs that quote model counts or statistics

Re-read each one; the numbers changed when the new models entered.

### paragraph 16 (model count)

> Bilinguals hold two languages in one mind: acquisition history sets a native preference, and the task at hand sets a working language. We ask whether a language model, like a bilingual, has a preferred language of its own, and whether that preference is present in its unverbalized reasoning. We used the Jacobian lens (J-lens): it decodes intermediate activations into a distribution over the vocabu

### paragraph 39 (statistic)

> The present study compares an English-fitted and a Chinese-fitted Jacobian lens to identify which properties of their readouts vary with the fitting corpus and which remain stable across lenses. For each of 23 models from five families, ranging from 0.6B to 32B parameters, we fitted one lens on English WikiText and another on Chinese Wikipedia. For each model, the two lenses followed the same fitt

### paragraph 61 (model count)

> We fitted twenty-four lenses, three per model (Table 2). The eight model instances are the non-quantized releases of three generations: Gemma-4-E2B, Gemma-4-E4B and Gemma-4-12B (Gemma Team, 2026); Qwen3-0.6B, Qwen3-4B and Qwen3-14B (Yang et al., 2025); and the later Qwen3.5-0.8B and Qwen3.5-2B, for which no separate technical reports exist and which are cited through the Qwen3 report. For each mod

### paragraph 72 (statistic)

> Measurement followed a fixed protocol, applied identically to the three lenses. Answer recovery was scored at the depth that the pool analyses use: Hit@100 is the share of measured (item, layer) cells in which the answer family appears among the top-100 decoded candidates of a lens at the last prompt position; it is computed separately for each prompt language. The answer family is matched as deco

### paragraph 90 (statistic)

> Each model was analysed separately. Every dependent variable is an item-level proportion: one of the four language shares of the top-100 pool, one of the three blackout rates (pool blackout, single blackout, single survivor), or one of the four three-lens overlap measures. Because these proportions include exact zeros and ones, each was arcsine-square-root transformed, y′ = asin(√y), before fittin

### paragraph 101 (model count, statistic)

> All tests are Type III tests with Satterthwaite denominator degrees of freedom. For English share (Figures 1 and 2), the main effect of lens language was significant in all ten models (F(2, 2376) = 2,245–31,047, all p < .001). Post-hoc comparisons on the lens main effect placed the English band above the Chinese band by 0.03–0.54 (|t(2376)| = 12.1–238.0, all p < .001), whereas the English-fitted l

### paragraph 103 (model count, statistic)

> For Chinese share, the same structure appeared with the bands reversed. Lens language was significant in all ten models (F(2, 2376) = 9,704–79,409, all p < .001), and post-hoc comparisons placed the Chinese-fitted lens above the English-fitted lens by 0.19–0.72 (|t(2376)| = 80.7–356.5) and above the Russian-fitted lens by 0.16–0.71 (|t(2376)| = 73.1–332.5), all p < .001. Prompt language was signif

### paragraph 105 (model count, statistic)

> For Russian share, lens language was significant in all ten models (F(2, 2376) = 3,958–79,698, all p < .001), and the Russian-fitted lens exceeded the English-fitted lens by 0.08–0.60 (|t(2376)| = 37.8–347.1) and the Chinese-fitted lens by 0.12–0.59 (|t(2376)| = 56.4–344.4), all p < .001. Prompt language was significant in all ten models (F(2, 2376) = 1,652–39,916, all p < .001), and the Russian b

### paragraph 108 (caption, statistic)

> Figure 1. Language composition of the Gemma-4 family. Rows are the prompt language (English, Chinese, Russian); columns are the three checkpoints ordered by size, smallest to largest; inside each cell the three lens rows are the English-fitted, Chinese-fitted and Russian-fitted readouts. Each bar is one measured layer, and the five bands (English, Chinese, Russian, other language, non-language) su

### paragraph 110 (caption, statistic)

> Figure 2. Language composition of the Qwen3 and Qwen3.5 families, in the layout of Figure 1. Qwen3 contributes four checkpoints and Qwen3.5 three, so the two families are shown side by side under their own headings. Each bar is one measured layer, and the five bands (English, Chinese, Russian, other language, non-language) sum to one. Data are the P1 country-capital probes (100 items), top-100 can

### paragraph 112 (model count, statistic)

> The remaining mass split between the other-language and the non-language band. Both bands varied with lens language and with prompt language in all ten models (all p < .001), and the other-language band stayed below 7% in every cell (2.3–6.8%). Probe family entered every model significantly (F(2, 297) = 193–1,062 for the English band, 34–998 for the Chinese band and 27–1,190 for the Russian band, 

### paragraph 114 (statistic)

> The composition results describe the structure of the candidate pool rather than the identity of the answer. Hit@100, the share of measured cells in which the answer family appeared among the top-100 decoded candidates, spanned 0.039–0.322 across the 90 model × lens × prompt-language combinations (mean 0.125; P4 0.145, P1 0.135, P3 0.095).

### paragraph 117 (model count)

> For three-way overlap (Figure 3), cross-language overlap without order was far above identical-string overlap without order at every depth: across the ten models, 39.5–44.3% of positions carried a translated counterpart in each of the other two lists (m1), against 10.7–12.3% carrying the same string (m3), a ratio of about 3.7.

### paragraph 121 (model count, statistic)

> Prompt language moved the overlap in all ten models (m1: F(2, 594) = 8.9–1,763; m2: F(2, 594) = 47–3,231; m3: F(2, 594) = 85–642; all p ≤ .0013). Cross-language overlap without order was highest under English (44.0%) and Chinese (44.3%) prompts and lowest under Russian prompts (39.5%), and the ordered cross-language measure followed the same order (11.1%, 12.3% and 7.7%). Identical-string overlap 

### paragraph 123 (model count, statistic)

> Probe family moved the overlap as well (m1: F(2, 297) = 10.6–851; m3: F(2, 297) = 27.5–1,454; all p < .001), and the family × prompt interaction was significant in all ten models (F(4, 594) = 109–679 for m1 and 90–1,278 for m3, all p < .001). The country-capital family gave the highest cross-language and identical-string overlap (m1 49.0%, m3 14.9%), the category-clue family the lowest cross-langu

### paragraph 125 (statistic)

> The ordered identical-string measure sat at the floor in every cell (mean 0.1%). Its prompt effect was significant (F(2, 594–891) = 5.1–78.5, p ≤ .006), but its family effect was not significant in every model (F(2, 297) = 0.8–149.5, p up to .43), so m4 is reported as a descriptive bound rather than as a tested quantity.

### paragraph 131 (caption, statistic)

> Figure 3. Three-way overlap between the three lenses by layer. Columns are the family’s checkpoints, ordered by size; rows are the prompt language; curves are the four overlap measures across the measured layers: cross-language overlap without order, within-language overlap without order, cross-language overlap with order and within-language overlap with order. The cross-language unordered curve i

### paragraph 134 (model count, statistic)

> For pool blackout (Figure 4), lens language was the strongest factor in every model (F(2, 2376) = 199–10,610, all p < .001). Pools went dark most often under the English-fitted lens (0.267, 0.245 and 0.267 under English, Chinese and Russian prompts), less often under the Russian-fitted lens (0.204, 0.189 and 0.214) and least often under the Chinese-fitted lens (0.102, 0.018 and 0.078). Prompt lang

### paragraph 135 (model count, statistic)

> The same ordering held when the pool was not wholly dark (Figure 4). On layers where exactly one lens was dark and the other two read, the dark lens was the English-fitted one in 0.117–0.126 of layers, the Russian-fitted one in 0.062–0.073 and the Chinese-fitted one in 0.004–0.018. Lens language (F(2, 2376–2673) = 115–7,861), prompt language (F = 17–530) and their interaction (F(4, 2376–2673) = 26

### paragraph 136 (model count, statistic)

> The mirror image appeared for survival (Figure 4). On layers where exactly one lens read and the other two were dark, the survivor was the Chinese-fitted lens in 0.077–0.107 of layers, the Russian-fitted lens in 0.002–0.019 and the English-fitted lens in 0.002–0.011. Lens language (F(2, 2376–2673) = 8.8–7,335), prompt language (F = 6.2–488) and the prompt × lens interaction (F(4, 2376–2673) = 34–6

### paragraph 141 (caption, model count, statistic)

> Figure 4. Blackout rates for the ten models, the three lenses and the three prompt languages. Each panel is one outcome: pool blackout (a pool is dark when its top 10 candidates carry no letter-bearing token and at least half of its top-100 slots are non-language), single blackout (exactly one lens dark, the other two reading) and single survivor (exactly one lens reading, the other two dark). Row

### paragraph 144 (model count)

> In the present study, we examined where the language of a Jacobian-lens readout comes from: the corpus the lens was fitted on, the model the lens is pointed at, or the two jointly. Each of twenty-three models, spanning five families (Qwen3, Qwen3.5, Qwen3.6, Qwen3.8, and Gemma-4) and a 53-fold range of scale, received two lenses fitted under one protocol, one on English WikiText and one on Chinese

### paragraph 157 (model count)

> The second candidate is the output vocabulary. The readout is projected through the model’s own unembedding, so a skew in that matrix, learned from the same training mixture, would also appear in the readout. The design separates the lens from the model, not the model’s parts, and nothing here rules that account out. Two observations leave room for the intermediate state as well: the composition o

### paragraph 257 (caption, statistic)

> Table A5. Aggregate readout accuracy over (probe, layer) cells at the last probe position. The two arms of each model differ only in the fitting corpus of the lens. A cell counts as a hit when the answer token reaches rank k or better under that lens: Hit@5 and Hit@10 match the candidate depths used elsewhere in the paper, and Hit@100 uses the full stored candidate list. The model’s own final-laye

### paragraph 260 (statistic)

> Both arms of Gemma-4-E2B and Gemma-4-E4B were re-measured on two further compute nodes. Every pool-composition and overlap statistic reported in the paper moved by less than 0.02, and aggregate Hit@5 moved by at most 0.047 (Gemma-4-E2B, English arm). Gemma hit rates are read with that margin in mind, and no claim rests on a Gemma hit-rate difference smaller than it.

### paragraph 263 (model count)

> Table A7. Visibility of language tokens in the top-5 of the two lenses, over all (probe, layer) cells of the twenty-three models. “EN only” and “ZH only” count cells dark under one lens whose other lens carries at least one language token.

### paragraph 268 (statistic)

> Figures A1 through A20 give the per-layer trajectory of the candidate pool for every (model family, probe) pair, computed on the top-100 candidates of each lens at every measured layer. Within each figure the rows are the models of one family and the columns are four panels. The first two give the language composition of the English-fit and Chinese-fit candidate pools as stacked bars that sum to o


## New statistics

See `RESULTS_DIGEST_10MODEL.md` for every mean, F, df and t range.

```
## Type III tests (F, df, p) across the ten models
- share_en: item_type F(2, 297-297)=193.2-1061.6 p_max=1.8e-54 | lens_lang F(2, 2376-2376)=2245.3-31047.0 p_max=0.0e+00 | lens_lang:item_type F(4, 2376-2376)=59.5-952.1 p_max=6.4e-48 | prompt_lang F(2, 2376-2376)=641.0-23347.7 p_max=2.4e-223 | prompt_lang:item_type F(4, 2376-2376)=35.4-2932.7 p_max=9.1e-29 | prompt_lang:lens_lang F(4, 2376-2376)=22.1-1413.9 p_max=5.9e-18 | prompt_lang:lens_lang:item_type F(8, 2376-2376)=58.5-637.2 p_max=2.1e-87
- share_zh: item_type F(2, 297-297)=34.1-997.7 p_max=4.7e-14 | lens_lang F(2, 2376-2376)=9704.3-79408.9 p_max=0.0e+00 | lens_lang:item_type F(4, 2376-2376)=110.5-567.0 p_max=1.7e-86 | prompt_lang F(2, 2376-2376)=4686.7-29856.5 p_max=0.0e+00 | prompt_lang:item_type F(4, 2376-2376)=59.0-1591.0 p_max=1.6e-47 | prompt_lang:lens_lang F(4, 2376-2376)=19.1-1338.8 p_max=1.9e-15 | prompt_lang:lens_lang:item_type F(8, 2376-2376)=125.8-1293.4 p_max=4.2e-176
- share_ru: item_type F(2, 297-297)=26.7-1190.3 p_max=2.2e-11 | lens_lang F(2, 2376-2376)=3957.5-79697.7 p_max=0.0e+00 | lens_lang:item_type F(4, 2376-2376)=7.3-484.3 p_max=8.3e-06 | prompt_lang F(2, 2376-2376)=1651.7-39915.6 p_max=0.0e+00 | prompt_lang:item_type F(4, 2376-2376)=190.2-735.0 p_max=1.3e-141 | prompt_lang:lens_lang F(4, 2376-2376)=54.5-2626.0 p_max=4.9e-44 | prompt_lang:lens_lang:item_type F(8, 2376-2376)=120.3-366.7 p_max=2.3e-169
- share_other: item_type F(2, 297-297)=24.5-1420.5 p_max=1.4e-10 | lens_lang F(2, 2376-2376)=423.7-9382.5 p_max=4.2e-158 | lens_lang:item_type F(4, 2376-2376)=35.5-430.2 p_max=7.8e-29 | prompt_lang F(2, 2376-2376)=55.0-9647.8 p_max=4.6e-24 | prompt_lang:item_type F(4, 2376-2376)=333.7-2944.0 p_max=3.8e-228 | prompt_lang:lens_lang F(4, 2376-2376)=160.3-1972.9 p_max=1.5e-121 | prompt_lang:lens_lang:item_type F(8, 2376-2376)=31.9-277.4 p_max=5.8e-48
- blackout_pool: item_type F(2, 297-297)=15.8-450.5 p_max=2.9e-07 | lens_lang F(2, 2376-2376)=198.9-10610.1 p_max=1.4e-80 | lens_lang:item_type F(4, 2376-2376)=30.5-253.3 p_max=9.5e-25 | prompt_lang F(2, 2376-2376)=125.0-1379.5 p_max=2.4e-52 | prompt_lang:item_type F(4, 2376-2376)=93.5-812.5 p_max=6.4e-74 | prompt_lang:lens_lang F(4, 2376-2376)=51.2-428.5 p_max=2.1e-41 | prompt_lang:lens_lang:item_type F(8, 2376-2376)=41.8-558.5 p_max=7.0e-63
- blackout_excl: item_type F(2, 297-2673)=8.2-294.0 p_max=2.9e-04 | lens_lang F(2, 2376-2673)=115.4-7860.8 p_max=1.4e-48 | lens_lang:item_type F(4, 2376-2673)=36.8-632.6 p_max=6.6e-30 | prompt_lang F(2, 2376-2673)=17.0-529.9 p_max=4.5e-08 | prompt_lang:item_type F(4, 2376-2673)=25.5-200.7 p_max=1.0e-20 | prompt_lang:lens_lang F(4, 2376-2673)=26.2-687.9 p_max=2.5e-21 | prompt_lang:lens_lang:item_type F(8, 2376-2673)=41.1-289.6 p_max=7.0e-62
- blackout_alive: item_type F(2, 297-2673)=29.8-246.5 p_max=1.6e-12 | lens_lang F(2, 2376-2673)=8.8-7335.1 p_max=1.6e-04 | lens_lang:item_type F(4, 2376-2673)=15.6-361.4 p_max=1.3e-12 | prompt_lang F(2, 2376-2673)=6.2-487.7 p_max=2.1e-03 | prompt_lang:item_type F(4, 2376-2673)=41.5-291.5 p_max=1.1e-33 | prompt_lang:lens_lang F(4, 2376-2673)=33.7-657.1 p_max=2.0e-27 | prompt_lang:lens_lang:item_type F(8, 2376-2673)=26.5-626.0 p_max=1.4e-39
- m1: item_type F(2, 297-297)=10.6-851.2 p_max=3.5e-05 | prompt_lang F(2, 594-594)=8.9-1763.4 p_max=1.6e-04 | prompt_lang:item_type F(4, 594-594)=108.5-679.0 p_max=2.4e-69
- m2: item_type F(2, 297-297)=10.3-715.1 p_max=4.9e-05 | prompt_lang F(2, 594-594)=46.9-3231.2 p_max=1.2e-19 | prompt_lang:item_type F(4, 594-594)=74.9-397.5 p_max=2.0e-51
- m3: item_type F(2, 297-297)=27.5-1454.3 p_max=1.1e-11 | prompt_lang F(2, 594-594)=84.9-641.9 p_max=3.6e-33 | prompt_lang:item_type F(4, 594-594)=89.7-1277.7 p_max=1.2e-59
- m4: item_type F(2, 297-891)=0.8-149.5 p_max=4.3e-01 | prompt_lang F(2, 594-891)=5.1-78.5 p_max=6.1e-03 | prompt_lang:item_type F(4, 594-891)=5.2-44.3 p_max=4.2e-04

## Post-hoc contrasts (|t|, df, p)
- share_en: en - ru est -0.260..+0.489 |t| 0.1-123.5 df 2376 sig 28/30 ; en - zh est -0.011..+0
```
