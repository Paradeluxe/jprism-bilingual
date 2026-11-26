# 2. Method

## 2.1 The Jacobian lens

The Jacobian lens was implemented following the original formulation and reference code (Gurnee et al., 2026). A transformer maps an input sequence to hidden states at each layer and position. Reading a hidden state as a vocabulary distribution requires a map from the hidden space to the output space. The Jacobian lens constructs this map from the model’s own first-order behavior: for a source layer l, the lens is the average, over a fitting corpus of natural text, of the Jacobian of the model’s final residual stream with respect to the hidden state at layer l. A hidden state at layer l is read out by applying the lens and projecting the result through the model’s unembedding matrix, which yields a distribution over the vocabulary. First, the lens is corpus-averaged: it trades exactness on any one prompt for a fixed, context-independent map. What the corpus contributes is the text over which the model’s local transfer behavior is sampled. Second, the lens file contains only the linear map. The vocabulary and the unembedding come from the model itself. Therefore, the lens does not contain a separate dictionary or lexicon. For a given model, all three fitted lenses use the same vocabulary and unembedding matrix and therefore have access to the same set of output tokens. They differ in the corpus-averaged linear map that determines which tokens receive high readout scores.

Following the reference implementation, the lens was fitted with the first 16 positions of each sequence skipped, since early positions act as attention sinks and have atypical residual statistics (Xiao et al., 2024), and with the final layer as the readout target. Source layers were sampled at every second layer below the final layer. The grid stores 12 to 24 layers per model and halves the fitting and storage cost of the per-layer maps. It was fixed before fitting and follows the original work, which reports all of its measurements on 25 evenly spaced layers per model (Gurnee et al., 2026).

The fitting protocol was held fixed across all lenses in the present study. We performed all lens fitting, application, and candidate decoding with the reference implementation of the Jacobian lens released with the original work (Gurnee et al., 2026), following its default estimator. That estimator averages the model’s input-output Jacobian over the fitting corpus for each source layer. It is computed by injecting a one-hot cotangent at every valid target position and summing the resulting gradients at each source position. The three lenses of a model differ only in their fitting corpus. The estimator is deterministic given its corpus, and all three lenses were fitted with the same sequence count under the same protocol, so the fitting procedure is the same for all three.  The original study reported only modest improvements beyond the first several dozen fitting prompts (Gurnee et al., 2026). We therefore used the maximum corpus size included in that analysis, 1,000 sequences per fitting corpus.

## 2.2 Fitting corpora

We built three corpora, one per language (Table 1). Each corpus contains 1,000 text windows of 128 tokens, cut as non-overlapping windows from the train split of a Wikipedia-derived source and packed deterministically in stream order without shuffling. The English corpus was cut from WikiText-103 (Merity et al., 2016), which is already a curated Wikipedia corpus; the English windows were used as released, with no additional language filter. The Chinese corpus was cut from the Chinese Wikipedia dump of November 2023 and screened with line-level and window-level Han-ratio guards (line at least 0.5, window at least 0.4) to exclude code, URLs, and boilerplate. The Russian corpus was cut from the Russian Wikipedia dump of November 2023 and screened with the analogous Cyrillic-ratio guards (line at least 0.5, window at least 0.4). All three corpora were cut with a single fixed tokenizer, that of Qwen3-0.6B, which is the common yardstick for the three languages, and built to the same target length, so that the number of windows, the window length, and the packing rule are identical. Preprocessing differs: the Han-ratio guards are specific to the Chinese corpus and the Cyrillic-ratio guards to the Russian corpus. Any window containing a banned evaluation substring (Section 2.4) was dropped at build time. These three corpus files were shared by every fit: each model read the windows through its own tokenizer, with sequences truncated to a common cap of 128 tokens and never padded. Windows whose retokenized length fell below 18 tokens were dropped, since the fitting rule skips the first 16 positions; no window fell below this threshold in any fit.

**Table 1. Fitting corpora. All three corpora hold 1,000 windows of 128 tokens, cut with the same tokenizer and packed in the same stream order. They differ in the text, and so in language, script and lexical content.**

| Property | English corpus | Chinese corpus | Russian corpus |
| --- | --- | --- | --- |
| Source | WikiText-103 train split | Chinese Wikipedia, 2023-11 dump | Russian Wikipedia, 2023-11 dump |
| Sequences | 1,000 | 1,000 | 1,000 |
| Window length | 128 tokens | 128 tokens | 128 tokens |
| Packing | non-overlapping, deterministic | non-overlapping, deterministic | non-overlapping, deterministic |
| Tokenizer | Qwen3-0.6B | Qwen3-0.6B (same) | Qwen3-0.6B (same) |
| CJK character share | 0.01% | 83.41% | 0.00% |
| Cyrillic character share | 0.00% | 0.00% | 79.89% |
| Latin character share | 75.9% | 2.77% | 0.51% |
| sha256 | dacf54dd...5a21ee | f1b108c4...bbd2792 | a173cae3...25cee4 |

The English corpus contained 6 windows with Japanese-script characters, 82 characters in total (26 ideographs and 56 kana), residual Japanese titles inside Wikipedia entries, amounting to 0.01% of characters. The Chinese corpus contained 2.77% Latin characters. The Russian corpus contained 0.51% Latin characters and no Han characters. These residues sit at least an order of magnitude below the corpus-level contrast and do not affect the comparison at the scale reported here.

The corpora differ in script class. The Latin alphabet carries dozens of living languages, so a window in Latin script fits any of them, while Han script identifies Chinese and Cyrillic script identifies Russian, each to within the small residues counted above. A token in the readout therefore maps to a set of languages when the lens was fitted on English text, and to a single language when the lens was fitted on Chinese or Russian text.

## 2.3 Models and lenses

We fitted twenty-four lenses, three per model (Table 2). The eight model instances are the non-quantized releases of three generations: Gemma-4-E2B, Gemma-4-E4B and Gemma-4-12B (Gemma Team, 2026); Qwen3-0.6B, Qwen3-4B and Qwen3-14B (Yang et al., 2025); and the later Qwen3.5-0.8B and Qwen3.5-2B, for which no separate technical reports exist and which are cited through the Qwen3 report. For each model, one lens was fitted on the English corpus, one on the Chinese corpus and one on the Russian corpus, under the identical protocol of Section 2.2: 1,000 fitting sequences, the same skip rule, the same source-layer sampling, and bfloat16 precision. The three lenses of a model share one vocabulary and one unembedding matrix and differ only in their fitting corpus. Source layers differ in absolute index across models of different depth but follow the same relative rule, and the three lenses of a model share its exact layer set.

**Table 2. Models and fitted lenses. Each model contributes one English (EN)-fit, one Chinese (ZH)-fit and one Russian (RU)-fit lens, fitted under the same protocol. Source layers are sampled at every second layer below the final layer, as in Section 2.3. Layers is the transformer depth of the model; measured layers counts the stored layers that enter the analysis and excludes layer 0.**

| Model | Family | Layers | d_model | Measured layers | Lenses |
| --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | Gemma-4 | 34 | 1536 | 16 | EN, ZH, RU |
| Gemma-4-E4B | Gemma-4 | 42 | 2560 | 20 | EN, ZH, RU |
| Gemma-4-12B | Gemma-4 | 48 | 3840 | 23 | EN, ZH, RU |
| Qwen3-0.6B | Qwen3 | 28 | 1024 | 13 | EN, ZH, RU |
| Qwen3-4B | Qwen3 | 36 | 2560 | 17 | EN, ZH, RU |
| Qwen3-14B | Qwen3 | 40 | 5120 | 19 | EN, ZH, RU |
| Qwen3.5-0.8B | Qwen3.5 | 24 | 1024 | 11 | EN, ZH, RU |
| Qwen3.5-2B | Qwen3.5 | 24 | 2048 | 11 | EN, ZH, RU |

## 2.4 Probes and measurement protocol

Readout was measured on 300 probes, 100 in each of three families (Table 3). Each item exists in an English, a Chinese and a Russian version, and all 900 prompts were run under all three lenses of a model, at the same measured layers and at the last position of the prompt. Layer 0 is excluded from measurement, so every lens is scored on the same interior layer set. A comparison cell is therefore an (item, prompt language, layer) triple whose input, position and layer are held fixed and whose only difference is the fitted lens. The three families clone the classic probes of Gurnee et al. (2026): country-capital facts (P1, from france_capital), definitional facts (P3, from spider_legs) and category clues (P4, from sport); the currency probe did not yield 100 items and was not used.

**Table 3. Probe families. Each family holds 100 items, and every item is asked in English, Chinese and Russian; the three versions of an item denote the same concept and share the same answer family. The examples show the first item of each family.**

| Family | Design | English version | Chinese version | Russian version | Items |
| --- | --- | --- | --- | --- | --- |
| P1 | country to capital | The capital of France is | 法国的首都是 | Столица Франции — это | 100 |
| P3 | definitional fact | The number of legs on the animal that spins webs is | 会织网的动物身上的腿的数量是 | Количество ног у животного, которое плетёт сети — это | 100 |
| P4 | category clue | Think of a sport: people kick a round ball into a net. The sport is | 想一项运动：人们把一个圆球踢进网里。这项运动是 | Подумайте о виде спорта: люди пинают круглый мяч в ворота. Этот вид спорта — | 100 |

All probes are excluded from all three fitting corpora by a banned-substring list that includes every probe text in its English, Chinese and Russian versions, so no lens was fitted on the probe strings themselves.

Measurement followed a fixed protocol, applied identically to the three lenses. Answer recovery was scored at the depth that the pool analyses use: Hit@100 is the share of measured (item, layer) cells in which the answer family appears among the top-100 decoded candidates of a lens at the last prompt position; it is computed separately for each prompt language. The answer family is matched as decoded strings rather than as fixed token IDs, so that one rule serves the eight tokenizers. Every item has an English, a Chinese and a Russian answer family, and a candidate matches when its decoded string, stripped of surrounding whitespace and compared case-insensitively, equals one of those forms; multi-token spellings are not counted, so Hit@100 is a lower bound on answer recovery. Across the 72 (model, lens, prompt-language) combinations Hit@100 runs 0.043-0.241, with a mean of 0.124.

The rank of an answer is its position in the ordering induced by the lens readout at that cell, recorded for candidates found within the top 500 entries of that ordering; a candidate outside that depth was recorded as unranked and counts as a miss. The scan depth of 500 exceeds the 100-candidate depth stored for the pool analyses, so every stored candidate carries a recorded rank. Ties were broken by the order the implementation returned.

One measurement caveat concerns Gemma-4. Those models apply final-logit softcapping (30·tanh(x/30)), and the lens readout passes through the same unembedding, so the readout is ranked on post-softcap values. The softcap is monotone, so the order it induces matches the pre-softcap order in exact arithmetic; under bfloat16, the saturated logits collapse to exactly equal floating-point values, and a top-k boundary can cut through a block of exact ties; single-cell membership then follows the arbitrary order within the block, and the size of that margin was measured on two further compute nodes (Appendix, Gemma tie sensitivity).

## 2.5 Candidate-pool measures

A cell is an (item, prompt language, layer) triple whose top-100 readout under all three lenses is retained; each readout enters the analysis as the ordered list of its decoded candidates from rank 1 to rank 100. Each decoded string is normalized by stripping surrounding whitespace and tokenizer boundary markers and by casefolding. A string that contains a Han character is labelled Chinese, a string that contains a Cyrillic character is labelled Russian, a string that contains a Latin letter is labelled English unless the translation lexicon lists it as a word of another language, in which case it is labelled other natural language, and a string that contains no letter is labelled non-language.

Composition is the share of a pool’s slots carrying each label, so the five shares of a cell sum to one.

Two candidates correspond when their strings are identical or when the translation lexicon links them, directly or through an English pivot, a relation that covers morphological variants (euro, euros) and a morpheme attached to a function word (在意大利, 意大利). Non-language strings take no part in correspondence.

Four overlap measures follow, each requiring agreement among all three lenses and each computed on content words only; stopwords do not count as matches but keep their positions, so the denominators stay fixed. Cross-language overlap without order (m1) is the share of the 300 positions that have at least one corresponding candidate in each of the other two lists. Cross-language overlap with order (m2) is the count of ranks, divided by the pool depth of 100, at which the three lists hold corresponding candidates. Within-language overlap without order (m3) is the multiset intersection of identical content strings across the three lists, divided by 100. Within-language overlap with order (m4) is the count of ranks, divided by 100, at which the three lists hold the same string.

A cell is dark for a lens when its top 10 candidates carry no letter-bearing token and at least half of its top-100 pool is non-language. Pool blackout is the share of measured layers on which a lens is dark. Single blackout is the share on which exactly one lens is dark and the other two read. Single survivor is the share on which exactly one lens reads and the other two are dark.

## 2.6 Statistical analysis

Each model was analysed separately. Every dependent variable is an item-level proportion: one of the four language shares of the top-100 pool, one of the three blackout rates (pool blackout, single blackout, single survivor), or one of the four three-lens overlap measures. Because these proportions include exact zeros and ones, each was arcsine-square-root transformed, $y' = \arcsin(\sqrt{y})$, before fitting; the transformation is defined at both boundaries, where a logit is not.

The generic models were (the asterisk denotes a full model, i.e. both main effects and their interaction; (1 | Probe) is a random intercept for the 300 probes):

$$
\text{LanguageShare} \sim \text{PromptLanguage} \ast \text{LensLanguage} \ast \text{ProbeFamily} + (1 \mid \text{Probe})
$$

$$
\text{BlackoutRate} \sim \text{PromptLanguage} \ast \text{LensLanguage} \ast \text{ProbeFamily} + (1 \mid \text{Probe})
$$

$$
\text{SemanticOverlap} \sim \text{PromptLanguage} \ast \text{ProbeFamily} + (1 \mid \text{Probe})
$$

LanguageShare is the top-100 language share, BlackoutRate the share of measured layers meeting a blackout criterion, and SemanticOverlap the share of positions or ranks (of 300 or 100) carrying a three-lens match. Prompt language, lens language and probe family were sum-to-zero coded fixed factors; the overlap model contains prompt language and probe family as the only fixed factors because the three lenses are combined by construction. Interaction terms test whether the effect of one factor changes across the levels of another, and Type III tests used Satterthwaite denominator degrees of freedom (lmerTest).

Simple effects were evaluated with joint tests of prompt language within each level of lens language, of lens language within each level of prompt language, and of prompt language within each probe family, followed by Bonferroni-corrected pairwise contrasts computed with emmeans. Within each model and dependent variable, Holm correction across the tested terms changed no inference, and raw p values are reported.

Models were fitted in R 4.4.1 with lme4 2.0-1 and lmerTest 3.2-1; Type III tests and contrasts used car 3.1-2 and emmeans 1.10-1, called from Python through rpy2.
