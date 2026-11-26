# Results digest, ten models

Models: gemma4-e2b, gemma4-e4b, gemma4-12b, qwen3-0.6b, qwen3-4b, qwen3-14b, qwen3-8b, qwen3.5-0.8b, qwen3.5-2b, qwen3.5-9b

## Language shares (% of top-100 pool)

**en band**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 50.1 | 23.0 | 28.7 |
| ZH | 26.9 | 9.2 | 13.4 |
| RU | 33.1 | 15.1 | 14.8 |

**zh band**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 5.0 | 25.9 | 6.5 |
| ZH | 46.3 | 68.5 | 48.8 |
| RU | 4.4 | 22.6 | 5.1 |

**ru band**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 1.0 | 1.2 | 15.0 |
| ZH | 0.6 | 1.4 | 10.2 |
| RU | 24.9 | 18.1 | 37.0 |

**other band**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 2.3 | 3.1 | 5.1 |
| ZH | 4.1 | 4.4 | 5.9 |
| RU | 5.0 | 4.3 | 6.8 |

**non band**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 41.6 | 46.8 | 44.7 |
| ZH | 22.1 | 16.5 | 21.7 |
| RU | 32.5 | 39.9 | 36.3 |

Family means of the English band: P1 27.0%, P3 19.4%, P4 25.0%
Family means of the other-language band: P1 6.0%, P3 3.8%, P4 3.9%

## Semantic overlap (% of positions / ranks)
m1: overall 42.61% | prompt EN 44.0 ZH 44.3 RU 39.5 | family P1 49.0 P3 40.5 P4 38.3
m2: overall 10.35% | prompt EN 11.1 ZH 12.3 RU 7.7 | family P1 12.3 P3 9.3 P4 9.4
m3: overall 11.37% | prompt EN 10.7 ZH 12.3 RU 11.2 | family P1 14.9 P3 8.7 P4 10.5
m4: overall 0.08% | prompt EN 0.1 ZH 0.1 RU 0.1 | family P1 0.1 P3 0.1 P4 0.1
m1/m3 = 3.7 ; m2/m1 = 0.243 ; m4/m3 = 0.007

## Blackout rates (proportion of measured layers)

**Pool blackout**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 0.267 | 0.245 | 0.267 |
| ZH | 0.102 | 0.018 | 0.078 |
| RU | 0.204 | 0.189 | 0.214 |

**single blackout**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 0.117 | 0.126 | 0.121 |
| ZH | 0.018 | 0.004 | 0.018 |
| RU | 0.062 | 0.071 | 0.073 |

**single survivor**
| lens \ prompt | EN | ZH | RU |
| --- | --- | --- | --- |
| EN | 0.011 | 0.002 | 0.007 |
| ZH | 0.077 | 0.107 | 0.093 |
| RU | 0.019 | 0.002 | 0.012 |

## Answer recovery (Hit@k over measured cells)
hit5: min 0.005 max 0.097 mean 0.040
hit10: min 0.009 max 0.130 mean 0.053
hit100: min 0.039 max 0.322 mean 0.125
Hit@100 by family: P1 0.135, P3 0.095, P4 0.145

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
- share_en: en - ru est -0.260..+0.489 |t| 0.1-123.5 df 2376 sig 28/30 ; en - zh est -0.011..+0.584 |t| 2.5-147.4 df 2376 sig 30/30 ; ru - zh est -0.195..+0.276 |t| 1.2-65.3 df 2376 sig 27/30
- share_zh: en - ru est -0.082..+0.162 |t| 1.3-37.7 df 2376 sig 29/30 ; en - zh est -0.769..-0.218 |t| 55.6-222.7 df 2376 sig 30/30 ; ru - zh est -0.779..-0.189 |t| 58.5-211.4 df 2376 sig 30/30
- share_ru: en - ru est -0.722..-0.054 |t| 17.5-243.0 df 2376 sig 30/30 ; en - zh est -0.057..+0.196 |t| 0.5-60.2 df 2376 sig 23/30 ; ru - zh est +0.061..+0.677 |t| 19.6-228.0 df 2376 sig 30/30
- m3: en - ru est -0.073..+0.049 |t| 2.0-22.1 df 594 sig 9/10 ; en - zh est -0.068..+0.060 |t| 7.2-27.1 df 594 sig 10/10 ; ru - zh est -0.099..+0.074 |t| 0.4-35.1 df 594 sig 9/10
- blackout_pool: en - ru est -0.205..+0.465 |t| 0.7-61.6 df 2376 sig 27/30 ; en - zh est -0.007..+0.617 |t| 0.6-74.7 df 2376 sig 29/30 ; ru - zh est -0.120..+0.655 |t| 0.0-79.2 df 2376 sig 27/30

## Joint simple effects (shares: prompt within each lens level)
- share_en within-prompt: F 29.6-12778.4 p_max 4.6e-14 sig 180/180
- share_en within-lens: F 23.8-12385.9 p_max 2.7e-19 sig 90/90
- share_zh within-prompt: F 0.3-30219.6 p_max 7.4e-01 sig 178/180
- share_zh within-lens: F 1.0-30752.8 p_max 3.9e-01 sig 88/90
- share_ru within-prompt: F 1.9-32005.0 p_max 1.5e-01 sig 179/180
- share_ru within-lens: F 2.2-37080.5 p_max 1.1e-01 sig 89/90
