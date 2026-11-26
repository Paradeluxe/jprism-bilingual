# Appendix

### Probe evidence

Each table records the dual-lens readout of every model on every layer in which the answer is visible, for one probe at the last probe position. In each table, for every model and for every layer at which the answer family reaches the top-5 of at least one lens, the best answer-family rank and the top-5 candidates of both lenses are given. Layers are listed verbatim as measured, and degenerate fragment tokens (underscore runs, empty strings) are preserved as they appear.

Table A1. Boot-currency probe, last position. For each model, the layers at which the answer family reaches the top-5 of at least one lens are shown with the rank and top-5 candidates of both lenses, following the convention described above. Under Gemma-4’s exact logit ties (Section 2.4), the stored top-5 shows one arbitrary order of the tied block.

| Model | Layer | EN rank | EN top-5 | ZH rank | ZH top-5 |
| --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | 30 | 21 | termed,  currency,  Pounds,  Euros,  not | 1 | worthless,  not, currency,  Bitcoin,  Euros |
|  | 32 | 10 | nothing,  dollars,  commonly,  known,  referred | 3 | coin, called,  coined,  dubbed,  one |
| Gemma-4-E4B | 34 | 5 | called,  denominated,  known,  chamado,  llamado | 12 | called,  named,  known, called,  the |
|  | 36 | 3 | called,  denominated,  euros,  pesos,  euro | 13 | called,  known, called,  named,  the |
| Gemma-4-12B | 30 | 3 | euros,  Euros,  Eurovision,  slang,  yummy | 48 | called, Argentina,  nickname,  country, 欧元 |
|  | 36 | 5 | called, 叫做,  denominated, 欧元,  euros | 11 | called,  currency, called, 叫做,  llamada |
|  | 38 | 2 | итальян, 欧元, イタリア,  イタリア,  euros | 10 | dollar,  moeda,  Italy,  italiano, イタリア |
|  | 40 | 2 | EURO,  یورو,  Euro, Euro, euro | 2 | 欧元,  евро, euro,  यूरो,  یورو |
|  | 42 | 1 | euros,  EURO,  евро,  euro, 欧元 | 1 | euro,  euros,  EUR,  Euro, 欧元 |
|  | 44 | 1 | Euros,  Euro,  EURO,  euros,  euro | 1 | called,  EURO,  euro,  euros,  EUR |
|  | 46 | 2 | s,  euros,  Euros,  called,  Euro | 2 | called,  euro,  euros,  dollars,  the |
| Qwen3-0.6B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-FP8 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q8_0 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q6_K | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q5_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q4_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q3_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-1.7B-BNB4 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-1.7B-Q4_K_M | 24 | 5 | dollars,  dollar,  Dollar,  USD,  euro | 12 | the,  called,  dollars,  USD, 英镑 |
| Qwen3-4B | 28 | 5 | 欧元, 意大利,  Italy,  Italian,  euros | 6 | 欧元, 意大利, 英镑,  Italian, 人民币 |
|  | 30 | 3 | 欧元, 意大利,  euros,  euro,  Italian | 2 | 欧元,  euros,  euro, 意大利,  currency |
|  | 32 | 2 | 欧元,  euro,  euros,  Euro,  Euros | 2 | 欧元,  euro,  euros,  Euro,  Euros |
|  | 34 | 3 | the, 欧元,  Euro,  euro,  called | 3 | the, 欧元,  Euro,  euro,  called |
| Qwen3-4B-AWQ | 26 | 5 | Italy, 意大利, 欧元, 英镑,  Euros | 8 | 欧元, 英镑, 货币, 人民币,  currency |
|  | 28 | 5 | 欧元, 意大利,  Italy, 英镑,  Euros | 6 | 欧元, 英镑, 人民币,  currency, 货币 |
|  | 30 | 2 | 欧元,  euros,  currency, 货币,  Euros | 5 | 欧元,  currency, 货币, 人民币,  euros |
|  | 32 | 2 | 欧元,  Euros,  euro,  euros,  EUR | 2 | 欧元,  euro,  euros,  currency,  Euros |
|  | 34 | 5 | the,  called, 欧元, ? ,  Euro | 6 | the,  called,  known,  not, 欧元 |
| Qwen3-8B | 28 | 5 | 欧元,  Italian, 意大利,  Italy,  euros | 8 | 欧元, 人民币,  Italian,  currency, 意大利 |
|  | 30 | 3 | 欧元,  Italian,  euro,  euros,  Euros | 2 | 欧元,  euro, 人民币,  Italian,  euros |
|  | 32 | 2 | 欧元,  euro,  Euro,  euros,  Euros | 2 | 欧元,  euro,  euros,  Euro,  Euros |
|  | 34 | 1 | Euro,  euro,  the, 欧元,  called | 2 | the,  Euro, 欧元,  euro,  called |
| Qwen3-8B-GPTQ4 | 30 | 6 | Italy,  Italian, 欧元, 意大利, Italy | 5 | 欧元,  Italian,  Italy, 意大利,  euro |
|  | 32 | 2 | Italy,  euro, 欧元,  Euro,  Italian | 3 | 欧元,  Italy,  euro,  Italian,  Euro |
|  | 34 | 1 | Euro,  euro,  the, 欧元,  EUR | 2 | the,  Euro, 欧元,  euro,  called |
| Qwen3-14B | 32 | 7 | 欧元, 意大利,  currency, currency, 货币 | 5 | 欧元,  called,  currency, 币,  euro |
|  | 34 | 2 | 欧元,  euro,  Euro, Euro,  euros | 2 | 欧元,  euro,  Euro,  euros, Euro |
|  | 36 | 1 | euro, 欧元,  Euro,  euros, Euro | 2 | 欧元,  euro,  Euro, Euro,  euros |
|  | 38 | 3 | the,  called,  euro,  Euro,  euros | 3 | called,  the,  Euro,  euro,  known |
| Qwen3-32B-FP8 | 56 | 3 | 意大利, 欧元,  euros,  Euros, 人民币 | 3 | 欧元,  currency,  euro,  euros, 意大利 |
|  | 58 | 2 | 欧元,  euro,  Euro,  Euros,  euros | 2 | 欧元,  euro,  Euro, Euro,  euros |
| Qwen3.5-0.8B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.5-2B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.5-9B | 22 | 2 | 欧元,  euros,  Currency,  currency,  euro | 16 | 欧元,  currency, 人民币, currency, Currency |
|  | 24 | 1 | euros, 欧元,  euro,  Euros,  Currency | 7 | 欧元, 人民币, 英镑,  currency, 钞票 |
|  | 26 | 1 | euro,  euros,  Euro, 欧元,  Euros | 2 | 欧元,  euro,  Euro,  euros, Euro |
|  | 28 | 1 | euro,  euros,  Euro,  Euros, 欧元 | 2 | 欧元,  euro,  euros,  Euro, Euro |
|  | 30 | 1 | Euro,  Euros,  the,  euros,  EUR | 4 | the, 欧元,  called,  euros,  Euro |
| Qwen3.6-27B | 54 | 2 | Dollar,  euro,  dollar, 欧元,  Italian | 15 | 欧元, 人民币, 美元, 货币,  currency |
|  | 56 | 2 | Italian,  called,  euro, 欧元,  Euros | 18 | 欧元,  called, 叫做, 意大利, 叫 |
|  | 58 | 1 | euro,  Euro, 欧元,  euros,  Euros | 2 | 欧元,  euro,  Euro, Euro,  called |
| Qwen3.8-27B | 54 | 1 | euro,  euros, 欧元,  Euros,  Currency | 12 | 欧元,  called, 叫做, 人民币, 叫什么 |
|  | 56 | 2 | called,  euro,  euros, 欧元,  Euros | 11 | called, 叫做, 欧元, 叫, called |
|  | 58 | 1 | euro,  Euro,  euros,  Euros, 欧元 | 2 | 欧元,  euro,  called,  Euro,  euros |

Table A2. France-capital probe, last position. For each model, the layers at which the answer family reaches the top-5 of at least one lens are shown with the rank and top-5 candidates of both lenses, following the convention described above.

| Model | Layer | EN rank | EN top-5 | ZH rank | ZH top-5 |
| --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | 28 | 1 | Paris,  located, Paris,  Marseille,  experiencing | 2 | renowned,  Paris,  paris, 巴黎,  famous |
|  | 30 | 2 | Toulouse,  situated,  Paris,  Париж,  enjoying | 1 | Paris,  Paris,  France,  undergoing,  one |
|  | 32 | 5 | celebrating,  PARIS,  unquestionably,  notoriously,  adorned | 2 | surrounded,  Paris,  really,  renowned,  celebrated |
| Gemma-4-E4B | 12 | 1 | Paris,  France,  Constantinople,  Parisian,  Marseille | 79 | 意大利,  Tbilisi,  Nantes,  Strasbourg,  Reykjavik |
|  | 14 | 2 | Hauptstadt,  Paris,  Parisian,  city,  şehr | 64 | città,  cidade,  ciudades,  Hauptstadt,  villes |
|  | 16 | 4 | Hauptstadt,  city,  şehr,  Parisian,  cities | 79 | città,  Hauptstadt,  مدينة,  villes,  도시 |
|  | 36 | 1 | Paris,  known,  located,  famous,  bustling | 34 | one,  located,  surrounded,  undoubtedly,  known |
|  | 38 | 1 | Paris,  known,  located,  famous,  situated | 30 | known,  also,  synonymous,  one,  considered |
|  | 40 | 1 | Paris,  a,  one,  also,  known | 6 | also,  one,  the,  undoubtedly,  a |
| Gemma-4-12B | 38 | 5 | famous,  Париж,  renowned,  known, 巴黎 | 25 | một,  famous,  oraș,  terkenal, 一座 |
|  | 40 | 1 | Paris, Paris,  París,  Париж, 巴黎 | 1 | Paris, Paris,  famous,  paris,  PARIS |
|  | 42 | 1 | Paris,  Париж,  París, 巴黎, Paris | 1 | Paris,  famous, Paris,  París,  Париж |
|  | 44 | 1 | Paris,  famous,  Париж,  París, Paris | 1 | Paris, 性,  known,  famous,  París |
|  | 46 | 2 | s,  Paris,  famous,  known,  located | 6 | known,  located,  famous,  renowned,  one |
| Qwen3-0.6B | 22 | 1 | Paris,  France, Paris, 巴黎, France | 2 | France,  Paris,  city,  City,  cities |
|  | 24 | 1 | Paris, 巴黎, Paris,  France,  Brussels | 1 | Paris,  France,  city, 巴黎,  Brussels |
|  | 26 | 1 | Paris,  France, 巴黎, Paris,  Lyon | 1 | Paris,  France,  French,  Lyon,  Brussels |
| Qwen3-0.6B-FP8 | 20 | 5 | ____,  ______,  France,  ___,  Italy | 23 | ______,  ____,  ___, ____,  city |
|  | 22 | 1 | Paris,  France, Paris, 巴黎, France | 2 | France,  Paris,  city,  City,  cities |
|  | 24 | 1 | Paris, 巴黎,  France, Paris,  Brussels | 1 | Paris,  France,  city, 巴黎,  Brussels |
|  | 26 | 1 | Paris,  France, 巴黎, Paris,  Lyon | 1 | Paris,  France,  French,  Rome,  Lyon |
| Qwen3-0.6B-Q8_0 | 22 | 1 | Paris,  France, Paris, 巴黎, France | 2 | France,  Paris,  city,  City,  cities |
|  | 24 | 1 | Paris, 巴黎, Paris,  France,  Brussels | 1 | Paris,  France,  city, 巴黎,  Brussels |
|  | 26 | 1 | Paris,  France, 巴黎, Paris,  Lyon | 1 | Paris,  France,  French,  Lyon,  Brussels |
| Qwen3-0.6B-Q6_K | 22 | 1 | Paris,  France, Paris, 巴黎, France | 2 | France,  Paris,  city,  City,  cities |
|  | 24 | 1 | Paris, 巴黎,  France, Paris,  Brussels | 1 | Paris,  France,  city, 巴黎,  Brussels |
|  | 26 | 1 | Paris,  France, 巴黎, Paris,  Lyon | 1 | Paris,  France,  French,  Lyon,  Brussels |
| Qwen3-0.6B-Q5_K_M | 22 | 1 | Paris,  France, Paris, 巴黎, France | 1 | Paris,  France,  city,  ______,  City |
|  | 24 | 1 | Paris, 巴黎, Paris,  France,  Brussels | 1 | Paris,  city,  France, 巴黎,  Brussels |
|  | 26 | 1 | Paris,  France, 巴黎, Paris,  Lyon | 1 | Paris,  France,  French,  Lyon,  Brussels |
| Qwen3-0.6B-Q4_K_M | 20 | 4 | ____,  France,  ______,  Paris,  Rome | 15 | city,  ______,  France,  ____, ____ |
|  | 22 | 1 | Paris,  France, Paris, 巴黎, France | 1 | Paris,  France,  city,  City,  cities |
|  | 24 | 1 | Paris, 巴黎, Paris,  France,  Brussels | 1 | Paris, 巴黎,  France,  city,  Brussels |
|  | 26 | 1 | Paris,  France, 巴黎, Paris,  Lyon | 1 | Paris,  France,  French,  Lyon,  Brussels |
| Qwen3-0.6B-Q3_K_M | 20 | 4 | located,  France,  Rome,  Paris,  Italy | 18 | located,  city,  France,  Spain, 位于 |
|  | 22 | 1 | Paris,  France, 巴黎, Paris, France | 2 | France,  Paris,  located,  city,  Rome |
|  | 24 | 1 | Paris, 巴黎,  France, Paris,  Rome | 1 | Paris,  France,  located, 巴黎,  city |
|  | 26 | 1 | Paris,  France,  located, 巴黎,  Rome | 1 | Paris,  France,  located,  in,  the |
| Qwen3-1.7B-BNB4 | 22 | 1 | Paris, 巴黎, Paris,  France,  London | 1 | Paris, 巴黎,  France, Paris,  London |
|  | 24 | 1 | Paris, 巴黎, Paris,  France,  London | 1 | Paris, 巴黎, Paris,  France,  London |
|  | 26 | 1 | Paris, 巴黎,  ____, Paris,  ______ | 1 | Paris,  which,  the,  either,  both |
| Qwen3-1.7B-Q4_K_M | 22 | 1 | Paris, 巴黎, Paris,  France,  London | 1 | Paris, 巴黎,  France,  ____,  London |
|  | 24 | 1 | Paris, 巴黎, Paris,  France,  London | 1 | Paris, 巴黎, Paris,  France,  London |
|  | 26 | 1 | Paris, 巴黎, Paris,  ______,  ____ | 1 | Paris,  which,  the,  either,  located |
| Qwen3-4B | 28 | 2 | ____,  Paris, 巴黎, ？ ,  ____ | 2 | ____,  Paris,  ____,  __,  ______ |
|  | 30 | 1 | Paris, 巴黎, Paris,  London, 伦敦 | 1 | Paris, 巴黎, Paris,  paris, 伦敦 |
|  | 32 | 1 | Paris, 巴黎, Paris, ____,  __ | 1 | Paris, 巴黎, Paris, ____,  __ |
|  | 34 | 1 | Paris, 巴黎, Paris,  located,  ______ | 1 | Paris, 巴黎,  located, Paris,  in |
| Qwen3-4B-AWQ | 28 | 1 | Paris, 巴黎, ____, Paris,  ____ | 1 | Paris,  ____, ____,  __,  ______ |
|  | 30 | 1 | Paris, 巴黎, Paris,  London, 伦敦 | 1 | Paris, 巴黎, Paris,  paris,  London |
|  | 32 | 1 | Paris, 巴黎, Paris, ____,  __ | 1 | Paris, Paris, 巴黎,  __,  ____ |
|  | 34 | 1 | Paris, 巴黎, Paris,  ______,  ____ | 1 | Paris,  in, Paris,  __,  London |
| Qwen3-8B | 28 | 2 | ____,  Paris,  ______,  ___,  ____ | 6 | ____,  ____,  ______,  __,  ___ |
|  | 30 | 1 | Paris, 巴黎, Paris,  paris,  France | 1 | Paris, 巴黎, Paris,  paris, 法国 |
|  | 32 | 1 | Paris, 巴黎, Paris, ____,  ______ | 1 | Paris, 巴黎, Paris,  ____, ____ |
|  | 34 | 1 | Paris,  paris, 巴黎, Paris,  ______ | 1 | Paris,  paris,  the,  a,  par |
| Qwen3-8B-GPTQ4 | 30 | 1 | Paris, 巴黎, Paris,  paris, 长沙 | 1 | Paris, 巴黎, Paris,  paris,  ____ |
|  | 32 | 1 | Paris, 巴黎, ____,  ______, Paris | 1 | Paris,  ____, ____,  ______,  ___ |
|  | 34 | 1 | Paris,  ______,  ____,  paris, 巴黎 | 1 | Paris,  the,  a,  ______,  ____ |
| Qwen3-14B | 26 | 5 | ____,  ____,  France,  ______,  Paris | 66 | 哪个, 是什么, 什么, 在哪里,  __ |
|  | 28 | 1 | Paris, 巴黎,  France, Paris, ____ | 17 | 在哪里, 哪个, 是什么, 这座城市, 哪一个 |
|  | 30 | 1 | Paris, 巴黎,  France, Paris, ____ | 3 | ____,  ____,  Paris,  ______,  __ |
|  | 32 | 1 | Paris, 巴黎, Paris,  France, 法国 | 1 | Paris, 法国,  France, Paris, 巴黎 |
|  | 34 | 1 | Paris, 巴黎, Paris,  London,  France | 1 | Paris, 巴黎, Paris,  London, 伦敦 |
|  | 36 | 1 | Paris, 巴黎, Paris,  London,  Rome | 1 | Paris, 巴黎, Paris,  London,  Berlin |
|  | 38 | 1 | Paris,  Berlin,  London,  Rome, Paris | 1 | Paris,  Berlin,  London,  known,  not |
| Qwen3-32B-FP8 | 50 | 4 | ____,  ______,  France,  Paris, ________ | 53 | 是什么, 什么, 什么样的, 在哪里,  what |
|  | 52 | 1 | Paris, ____, Paris, 法国, 巴黎 | 11 | 法国, 什么样的, 位于, 这座城市, 在哪里 |
|  | 54 | 1 | Paris, 巴黎, Paris, ____,  France | 2 | ____,  Paris, 法国, 这座城市, 位于 |
|  | 56 | 2 | 巴黎,  Paris, Paris, 法国,  France | 1 | Paris, 法国,  France, 巴黎, Paris |
|  | 58 | 2 | 巴黎,  Paris, Paris, 法国,  paris | 1 | Paris, 巴黎, Paris, 法国,  France |
| Qwen3.5-0.8B | 18 | 2 | located,  Paris,  London,  Istanbul,  Brussels | 8 | 伦敦, 这座城市,  city,  London,  located |
|  | 20 | 1 | Paris,  France, Paris, 巴黎,  Brussels | 2 | 巴黎,  Paris, Paris, 法国,  France |
|  | 22 | 2 | located,  Paris,  situated,  ____,  ______ | 8 | located,  a,  in,  the,  not |
| Qwen3.5-2B | 4 | 2 | ,,  Paris,  is, .,  city | 24 | ,,  ,,  .,  ?,  ; |
|  | 6 | 3 | city,  cities,  Paris,  , ____ | 16 | ,,  \",  ,  ', , |
|  | 8 | 5 | ,  city, ____,  cities,  Paris | 42 | 城市的, 首都, 这座城市,  , 是国家 |
|  | 18 | 2 | ________,  Paris, ____,  ______,  __ | 9 | __,  ____,  ______,  ________,  ___ |
|  | 20 | 1 | Paris, 巴黎, Paris,  France,  paris | 2 | 巴黎,  Paris, Paris,  __,  ____ |
|  | 22 | 1 | Paris,  ______,  ___,  __,  ____ | 4 | a,  __,  ______,  Paris,  ____ |
| Qwen3.5-9B | 22 | 2 | London,  Paris,  Berlin,  Tokyo, ________ | 19 | __,  ______, 伦敦,  ___,  ____ |
|  | 24 | 1 | Paris, Paris, 巴黎,  France,  London | 1 | Paris, 巴黎, Paris, 伦敦,  __ |
|  | 26 | 1 | Paris, 巴黎, Paris,  París,  paris | 1 | Paris, 巴黎, Paris,  paris, 伦敦 |
|  | 28 | 1 | Paris, 巴黎, Paris,  paris,  London | 2 | 巴黎,  Paris, Paris,  __, 伦敦 |
|  | 30 | 1 | Paris,  __,  London,  ____,  ______ | 2 | __,  Paris,  ____,  ______,  ________ |
| Qwen3.6-27B | 50 | 4 | ____, ___,  ______,  ___,  Paris | 85 | ____,  ___, 叫什么,  ______,  __ |
|  | 54 | 1 | Paris, ___, ____,  ___,  London | 9 | ____,  ___,  __, ___,  ____ |
|  | 56 | 1 | Paris, Paris,  France, 巴黎,  Berlin | 2 | 巴黎,  Paris, Paris,  __, ____ |
|  | 58 | 1 | Paris, Paris, 巴黎,  paris,  PARIS | 2 | 巴黎,  Paris, Paris,  paris,  París |
| Qwen3.8-27B | 24 | 4 | city,  France,  cities,  Paris,  City | 100 | , 城市的, 国家的,  city, 城市 |
|  | 40 | 2 | Paris,  city,  cities,  London, city | 16 | city, 城市, 城市的, 这座城市, 的城市 |
|  | 42 | 1 | Paris,  city,  cities,  London,  France | 22 | 城市, 城市的,  city, 这座城市, 的城市 |
|  | 44 | 1 | Paris,  city,  cities,  London,  France | 19 | 城市的, 城市,  city, 这座城市, 的城市 |
|  | 46 | 1 | Paris,  city,  cities,  London, … | 27 | 城市的, 是哪个, 是全国, 城市, 是国家 |
|  | 48 | 1 | Paris,  city,  cities,  London,  France | 40 | 是什么, 城市的, 是哪个, 城市, 是国家 |
|  | 50 | 3 | ...,  Paris, __.,  ___,  ______ | 64 | 是哪个,  ___, 叫什么,  ____, 是什么 |
|  | 52 | 4 | ______,  ___, ____,  Paris,  ____ | 46 | ____,  ___, ____,  ______,  __ |
|  | 54 | 1 | Paris,  ___, ...\,  ______, ____ | 17 | ..., ……,  ___, ____,  ______ |
|  | 56 | 1 | Paris, Paris,  France, ...\,  Parigi | 2 | 巴黎,  Paris, ..., Paris,  ______ |
|  | 58 | 1 | Paris, Paris, 巴黎,  paris,  París | 1 | Paris, 巴黎, Paris,  paris, パリ |

Table A3. Sport probe, last position. For each model, the layers at which the answer family reaches the top-5 of at least one lens are shown with the rank and top-5 candidates of both lenses, following the convention described above.

| Model | Layer | EN rank | EN top-5 | ZH rank | ZH top-5 |
| --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | 26 | 2 | fútbol,  football,  baseball,  basketball,  soccer | 4 | football,  sports,  Baseball,  baseball, called |
|  | 28 | 2 | basketball,  football,  badminton,  volleyball,  Soccer | 8 | softball, ball,  cricket,  calcio,  played |
|  | 30 | 4 | golf,  Badminton,  fútbol, soccer,  handball | 6 | racquet,  क्रिकेट,  футбол,  playing,  Sports |
|  | 32 | 3 | 足球,  Badminton,  Soccer,  كرة, サッカー | 10 | 足球,  football,  fútbol,  rugby, hockey |
| Gemma-4-E4B | 32 | 1 | soccer,  football,  basketball,  probably,  hockey | 3 | called,  probably,  football,  basketball,  likely |
|  | 34 | 1 | soccer,  fútbol,  Soccer,  futbol,  football | 4 | soccer,  football,  rugby,  basketball,  hockey |
|  | 36 | 1 | football,  soccer,  hockey,  basketball,  rugby | 1 | football,  soccer,  basketball, football, soccer |
|  | 38 | 1 | soccer,  football,  rugby,  hockey,  basketball | 1 | soccer,  football,  hockey,  basketball, soccer |
|  | 40 | 1 | soccer,  football,  hockey,  Soccer,  probably | 1 | soccer,  football,  probably,  called,  either |
| Gemma-4-12B | 36 | 6 | ⚽, ________,  ____________, …?,  ________ | 2 | ____,  football,  __________,  probably,  soccer |
|  | 38 | 4 | football, soccer,  футбо,  Fußball,  fútbol | 2 | soccer,  football,  fútbol, 足球,  Fußball |
|  | 40 | 2 | futebol,  Fußball,  soccer, football, soccer | 2 | 足球,  voetbal, ⚽, サッカー, soccer |
|  | 42 | 1 | soccer,  Soccer, soccer, 足球, ⚽ | 1 | football,  soccer,  Soccer, 足球, ⚽ |
|  | 44 | 1 | soccer,  football,  Soccer, 足球, サッカー | 1 | soccer,  football, soccer,  Soccer,  futbol |
|  | 46 | 1 | soccer, s,  football, soccer,  Soccer | 1 | soccer,  football,  most,  probably,  called |
| Qwen3-0.6B | 22 | 3 | called,  basketball,  football,  soccer, 叫做 | 5 | called, 称为, 叫做,  ______,  football |
|  | 24 | 2 | called,  football,  soccer,  basketball,  sports | 2 | called,  football,  sports,  sport,  basketball |
|  | 26 | 4 | called,  known,  football,  soccer,  named | 16 | called,  known,  on,  named,  the |
| Qwen3-0.6B-FP8 | 22 | 3 | called,  basketball,  football,  soccer,  hockey | 4 | called, 称为, 叫做,  football,  ______ |
|  | 24 | 2 | called,  football,  soccer,  basketball,  known | 2 | called,  football,  sports,  sport,  basketball |
|  | 26 | 3 | called,  known,  football,  soccer,  named | 13 | called,  known,  a,  named,  the |
| Qwen3-0.6B-Q8_0 | 22 | 3 | called,  basketball,  football,  soccer, 叫做 | 7 | called, 称为, 叫做,  ______, 被称为 |
|  | 24 | 2 | called,  football,  soccer,  basketball,  sports | 2 | called,  football,  sports,  sport,  played |
|  | 26 | 3 | called,  known,  football,  named,  soccer | 15 | called,  known,  on,  named,  the |
| Qwen3-0.6B-Q6_K | 22 | 2 | called,  football,  basketball,  soccer,  hockey | 3 | called, 称为,  football, 叫做,  sport |
|  | 24 | 2 | called,  football,  soccer,  basketball,  sports | 2 | called,  football,  sports,  sport,  played |
|  | 26 | 3 | called,  known,  football,  soccer,  named | 11 | called,  known,  on,  as,  the |
| Qwen3-0.6B-Q5_K_M | 22 | 3 | called,  basketball,  football,  soccer,  sports | 5 | called, 称为, 叫做,  football,  sport |
|  | 24 | 2 | called,  football,  soccer,  sports,  basketball | 2 | called,  football,  sports,  sport,  soccer |
|  | 26 | 3 | called,  known,  football,  soccer,  named | 11 | called,  known,  on,  named,  as |
| Qwen3-0.6B-Q4_K_M | 24 | 4 | called,  named,  known,  football,  soccer | 3 | called,  known,  football,  named,  played |
|  | 26 | 4 | called,  known,  named,  football,  soccer | 23 | called,  known,  named,  on,  now |
| Qwen3-0.6B-Q3_K_M | 20 | 5 | called,  basketball,  often,  usually,  football | 14 | called, 体育, 篮球,  usually,  sport |
|  | 22 | 2 | basketball,  football,  soccer,  called,  hockey | 2 | called,  football, 篮球,  basketball,  sports |
|  | 24 | 1 | football,  soccer,  basketball,  sports,  hockey | 1 | football,  sports,  called,  sport,  basketball |
|  | 26 | 2 | called,  football,  soccer,  basketball,  known | 4 | called,  the,  as,  football,  not |
| Qwen3-1.7B-BNB4 | 22 | 2 | basketball,  soccer,  volleyball,  football,  Basketball | 2 | basketball,  football, 网球,  soccer,  volleyball |
|  | 24 | 2 | basketball,  soccer,  volleyball,  football,  tennis | 2 | basketball,  football,  soccer, 网球,  volleyball |
|  | 26 | 2 | basketball,  called,  soccer,  football,  volleyball | 2 | called,  football,  known,  basketball,  volleyball |
| Qwen3-1.7B-Q4_K_M | 22 | 1 | soccer,  basketball,  football, 足球,  rugby | 1 | football,  soccer,  basketball, 足球, 网球 |
|  | 24 | 1 | soccer,  football,  basketball,  rugby,  volleyball | 1 | football,  soccer,  basketball, 足球, 篮球 |
|  | 26 | 1 | soccer,  football,  called,  basketball,  volleyball | 2 | called,  football,  known,  soccer,  which |
| Qwen3-4B | 28 | 1 | soccer,  football,  basketball, 足球,  rugby | 1 | football,  soccer,  basketball, 足球,  baseball |
|  | 30 | 1 | soccer,  football,  basketball, 足球,  rugby | 1 | football,  soccer,  basketball, 足球,  rugby |
|  | 32 | 1 | soccer,  football,  basketball, 足球,  rugby | 1 | soccer,  football,  basketball, 足球,  Soccer |
|  | 34 | 1 | soccer,  football,  called,  basketball,  ____ | 1 | soccer,  football,  called,  basketball,  known |
| Qwen3-4B-AWQ | 28 | 1 | soccer,  football, 足球,  rugby,  basketball | 1 | football,  soccer,  ____, 足球,  baseball |
|  | 30 | 1 | soccer,  football, 足球,  basketball,  rugby | 1 | football,  soccer, 足球,  basketball,  tennis |
|  | 32 | 1 | soccer,  football, 足球,  basketball,  rugby | 1 | soccer,  football, 足球,  basketball, football |
|  | 34 | 1 | soccer,  football,  called,  volleyball,  baseball | 1 | soccer,  football,  known,  called,  not |
| Qwen3-8B | 26 | 4 | ____, ____,  soccer,  ______, 足球 | 7 | __,  ____,  ______,  ___,  _____ |
|  | 28 | 1 | soccer, 足球,  football,  basketball, ____ | 4 | ____,  ______,  __,  football,  ___ |
|  | 30 | 1 | soccer,  football, 足球,  basketball,  Football | 1 | football, 足球,  soccer, football,  basketball |
|  | 32 | 1 | soccer,  football, 足球, football,  Football | 1 | soccer,  football, 足球, football,  Football |
|  | 34 | 1 | soccer,  football,  called,  played,  known | 1 | soccer,  football,  called,  known,  the |
| Qwen3-8B-GPTQ4 | 26 | 5 | ____,  ______, ____, 足球,  soccer | 4 | __,  ____,  ______,  football,  ___ |
|  | 28 | 1 | soccer, 足球,  football,  basketball,  hockey | 2 | football,  ____, 名为,  ______, 被称为 |
|  | 30 | 1 | soccer,  football, 足球,  hockey,  basketball | 1 | football,  soccer, 足球, football,  hockey |
|  | 32 | 1 | soccer,  football, 足球,  Soccer, football | 1 | soccer,  football, 足球, football,  Football |
|  | 34 | 1 | soccer,  called,  football,  known,  ______ | 2 | called,  soccer,  football,  known,  the |
| Qwen3-14B | 32 | 1 | soccer, 足球,  football,  ______,  ____ | 2 | 足球,  football,  soccer, ____,  ______ |
|  | 34 | 1 | soccer,  football, 足球,  Soccer,  Football | 1 | soccer, 足球,  football, football, Football |
|  | 36 | 1 | soccer,  football, 足球,  Soccer,  ______ | 1 | soccer, 足球,  football, football,  Football |
|  | 38 | 1 | soccer,  football,  called,  ______,  ____ | 1 | soccer,  called,  football,  most,  usually |
| Qwen3-32B-FP8 | 54 | 2 | ______,  soccer, ____,  ____,  called | 22 | 叫做, 名叫,  called, 被称为, 名为 |
|  | 56 | 1 | soccer,  football, 足球,  probably, occer | 2 | 足球,  soccer,  called,  football,  probably |
|  | 58 | 1 | soccer,  played,  football, 足球, 踢 | 1 | soccer, 足球, 踢,  football,  played |
| Qwen3.5-0.8B | 18 | 1 | football,  soccer,  basketball,  Football,  tennis | 8 | 网球,  tennis, 足球, 踢球, 打球 |
|  | 20 | 1 | soccer,  football,  tennis,  basketball,  volleyball | 5 | 网球, 踢球, 足球, 踢,  soccer |
| Qwen3.5-2B | 16 | 1 | soccer,  football,  basketball,  tennis,  Soccer | 40 | 叫做, 网球,  ____,  called, 篮球 |
|  | 18 | 1 | soccer,  football,  basketball,  Soccer,  baseball | 7 | 足球, 踢球, 篮球, 网球, 球的 |
|  | 20 | 1 | soccer,  football,  basketball,  tennis,  baseball | 4 | 足球, 踢球, 网球,  football, 篮球 |
|  | 22 | 1 | soccer,  called,  football,  tennis,  basketball | 6 | a,  ",  “,  called,  ' |
| Qwen3.5-9B | 24 | 1 | soccer,  football,  Football,  Soccer, 足球 | 2 | 足球,  football,  soccer, football,  Football |
|  | 26 | 1 | soccer,  football,  Soccer, 足球,  Football | 2 | 足球,  football,  soccer, football,  Soccer |
|  | 28 | 1 | soccer,  football,  Soccer,  Football, 足球 | 2 | 足球,  football,  soccer, ____, football |
|  | 30 | 1 | soccer,  football,  Soccer,  ____,  ______ | 4 | ____,  ______,  __,  soccer,  ________ |
| Qwen3.6-27B | 56 | 2 | called,  soccer, ____,  football,  ______ | 18 | called, 叫做, ____, 叫,  __ |
|  | 58 | 1 | soccer, ____,  ______,  __,  ____ | 11 | __, ____,  called,  ______,  ____ |
| Qwen3.8-27B | 56 | 1 | soccer,  called,  football,  Soccer,  Football | 7 | called, 叫做,   , 足球, 叫 |
|  | 58 | 1 | soccer,  football,  played,  __,  ___ | 5 | __, ____, 足球,  ______,  soccer |

Table A4. Spider-legs probe, last position. For each model, the layers at which the answer family reaches the top-5 of at least one lens are shown with the rank and top-5 candidates of both lenses, following the convention described above.

| Model | Layer | EN rank | EN top-5 | ZH rank | ZH top-5 |
| --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Gemma-4-E4B | 34 | 8 | spiders,  infinite,  usually,  zero,  eight | 1 | four,  eight,  three,  usually,  zero |
|  | 36 | 2 | eight,  zero,  usually,  unknown,  six | 2 | eight,  four,  usually,  three,  one |
|  | 38 | 1 | eight,  zero,  typically,  spiders,  six | 1 | eight,  four,  usually,  called,  three |
|  | 40 | 3 | , :,  eight,  usually,  six | 2 | four,  eight,  the,  two,  one |
| Gemma-4-12B | 38 | 316 | равна,  ________,  __________,  計算,  ______ | 1 | eight,  four,  twice,  determined,  zero |
|  | 40 | 50 | ________,  ____,  __________,  ______,  _____ | 1 | eight,  four,  ________,  _____,  ______ |
|  | 42 | 49 | calculated,  determined,  negligible,  proportional,  equal | 2 | four,  eight,  twice,  determined,  six |
|  | 44 | 22 | calculated,  determined,  ________,  equal,  ____ | 3 | 性,  four,  eight,  calculated, 性的 |
|  | 46 | 20 | s, ed, :,  determined,  calculated | 2 | four,  calculated,  eight,  three,  equal |
| Qwen3-0.6B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-FP8 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q8_0 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q6_K | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q5_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q4_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-0.6B-Q3_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-1.7B-BNB4 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-1.7B-Q4_K_M | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-4B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-4B-AWQ | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-8B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-8B-GPTQ4 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-14B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3-32B-FP8 | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.5-0.8B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.5-2B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.5-9B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.6-27B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |
| Qwen3.8-27B | – | – | (no top-5 hit at any layer) | – | (no top-5 hit at any layer) |

### Aggregate statistics

The tables below carry the aggregate readouts on which Sections 3.1 and 3.3 rest. The per-probe layer tables are given above.

Table A5. Aggregate readout accuracy over (probe, layer) cells at the last probe position. The two arms of each model differ only in the fitting corpus of the lens. A cell counts as a hit when the answer token reaches rank k or better under that lens: Hit@5 and Hit@10 match the candidate depths used elsewhere in the paper, and Hit@100 uses the full stored candidate list. The model’s own final-layer hit rate is identical across arms and is given as a reference. Gemma-4 rows carry the tie caveat of Section 2.4.

| Model | Cells | EN-fit Hit@5 | EN-fit Hit@10 | EN-fit Hit@100 | ZH-fit Hit@5 | ZH-fit Hit@10 | ZH-fit Hit@100 | ΔHit@5 | Model final Hit@5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | 64 | 0.125 | 0.141 | 0.312 | 0.125 | 0.172 | 0.297 | 0.000 | 0.50 |
| Gemma-4-E4B | 80 | 0.200 | 0.237 | 0.350 | 0.113 | 0.125 | 0.350 | 0.088 | 0.75 |
| Gemma-4-12B | 92 | 0.196 | 0.217 | 0.402 | 0.207 | 0.239 | 0.391 | -0.011 | 0.75 |
| Qwen3-0.6B | 52 | 0.115 | 0.135 | 0.250 | 0.096 | 0.096 | 0.231 | 0.019 | 0.50 |
| Qwen3-0.6B-FP8 | 52 | 0.115 | 0.154 | 0.250 | 0.096 | 0.096 | 0.231 | 0.019 | 0.50 |
| Qwen3-0.6B-Q8_0 | 52 | 0.115 | 0.135 | 0.250 | 0.077 | 0.096 | 0.212 | 0.038 | 0.50 |
| Qwen3-0.6B-Q6_K | 52 | 0.115 | 0.154 | 0.250 | 0.096 | 0.096 | 0.231 | 0.019 | 0.50 |
| Qwen3-0.6B-Q5_K_M | 52 | 0.115 | 0.154 | 0.250 | 0.096 | 0.096 | 0.231 | 0.019 | 0.50 |
| Qwen3-0.6B-Q4_K_M | 52 | 0.115 | 0.135 | 0.250 | 0.077 | 0.077 | 0.212 | 0.038 | 0.50 |
| Qwen3-0.6B-Q3_K_M | 52 | 0.154 | 0.154 | 0.288 | 0.115 | 0.115 | 0.250 | 0.038 | 0.50 |
| Qwen3-1.7B-BNB4 | 52 | 0.135 | 0.173 | 0.423 | 0.115 | 0.173 | 0.365 | 0.019 | 0.50 |
| Qwen3-1.7B-Q4_K_M | 52 | 0.154 | 0.154 | 0.442 | 0.135 | 0.212 | 0.365 | 0.019 | 0.50 |
| Qwen3-4B | 68 | 0.206 | 0.235 | 0.294 | 0.206 | 0.235 | 0.382 | 0.000 | 0.75 |
| Qwen3-4B-AWQ | 68 | 0.191 | 0.235 | 0.324 | 0.206 | 0.221 | 0.397 | -0.015 | 0.75 |
| Qwen3-8B | 68 | 0.206 | 0.235 | 0.309 | 0.191 | 0.235 | 0.324 | 0.015 | 0.75 |
| Qwen3-8B-GPTQ4 | 68 | 0.176 | 0.206 | 0.353 | 0.206 | 0.221 | 0.324 | -0.029 | 0.75 |
| Qwen3-14B | 76 | 0.237 | 0.263 | 0.408 | 0.211 | 0.211 | 0.303 | 0.026 | 0.75 |
| Qwen3-32B-FP8 | 116 | 0.103 | 0.103 | 0.190 | 0.078 | 0.095 | 0.129 | 0.026 | 0.75 |
| Qwen3.5-0.8B | 44 | 0.114 | 0.136 | 0.432 | 0.114 | 0.205 | 0.250 | 0.000 | 0.25 |
| Qwen3.5-2B | 44 | 0.227 | 0.295 | 0.409 | 0.114 | 0.205 | 0.386 | 0.114 | 0.50 |
| Qwen3.5-9B | 60 | 0.233 | 0.267 | 0.400 | 0.233 | 0.250 | 0.400 | 0.000 | 0.75 |
| Qwen3.6-27B | 116 | 0.078 | 0.078 | 0.276 | 0.052 | 0.103 | 0.259 | 0.026 | 0.75 |
| Qwen3.8-27B | 116 | 0.138 | 0.164 | 0.405 | 0.069 | 0.121 | 0.276 | 0.069 | 0.75 |

### Gemma tie sensitivity

Both arms of Gemma-4-E2B and Gemma-4-E4B were re-measured on two further compute nodes. Every pool-composition and overlap statistic reported in the paper moved by less than 0.02, and aggregate Hit@5 moved by at most 0.047 (Gemma-4-E2B, English arm). Gemma hit rates are read with that margin in mind, and no claim rests on a Gemma hit-rate difference smaller than it.

Table A6. Boot-currency probe, last position, at the deepest layer where the answer family reaches the top-5 of both lenses, or, for models without such a layer, the deepest layer at which it reaches the top-5 of at least one lens, and for models on which it never does, the deepest layer at which the answer is visible within the 500-token scan. Ranks are full-vocabulary ranks recorded at measurement. Under Gemma-4’s exact logit ties the stored top-5 shows one arbitrary order of the tied block (Section 2.4). Answer-family tokens and their Chinese translations are listed for each probe in Table 3.

| Model | Layer | EN rank | EN top-5 | ZH rank | ZH top-5 |
| --- | --- | --- | --- | --- | --- |
| Gemma-4-E2B | 32 | 10 | nothing,  dollars,  commonly,  known,  referred | 3 | coin, called,  coined,  dubbed,  one |
| Gemma-4-E4B | 36 | 3 | called,  denominated,  euros,  pesos,  euro | 13 | called,  known, called,  named,  the |
| Gemma-4-12B | 46 | 2 | s,  euros,  Euros,  called,  Euro | 2 | called,  euro,  euros,  dollars,  the |
| Qwen3-0.6B | 26 | 23 | called,  currency,  the,  known,  coin | 40 | the,  called,  in,  a,  not |
| Qwen3-0.6B-FP8 | 26 | 17 | currency,  called,  the,  coin,  coins | 23 | the,  called,  in,  currency,  a |
| Qwen3-0.6B-Q8_0 | 26 | 24 | called,  currency,  the,  money,  coin | 41 | the,  called,  in,  a,  currency |
| Qwen3-0.6B-Q6_K | 26 | 22 | called,  currency,  the,  money,  coin | 33 | the,  called,  in,  currency,  a |
| Qwen3-0.6B-Q5_K_M | 26 | 19 | called,  currency,  the,  money,  dollars | 26 | the,  called,  currency,  in,  money |
| Qwen3-0.6B-Q4_K_M | 26 | 26 | called,  currency,  the,  coin,  known | 27 | called,  the,  not,  a,  currency |
| Qwen3-0.6B-Q3_K_M | 26 | 35 | called,  the,  currency,  known,  named | 45 | called,  the,  in,  a,  known |
| Qwen3-1.7B-BNB4 | 26 | 25 | called,  the,  known,  named,  divided | 140 | the,  called,  known,  specifically,  either |
| Qwen3-1.7B-Q4_K_M | 24 | 5 | dollars,  dollar,  Dollar,  USD,  euro | 12 | the,  called,  dollars,  USD, 英镑 |
| Qwen3-4B | 34 | 3 | the, 欧元,  Euro,  euro,  called | 3 | the, 欧元,  Euro,  euro,  called |
| Qwen3-4B-AWQ | 32 | 2 | 欧元,  Euros,  euro,  euros,  EUR | 2 | 欧元,  euro,  euros,  currency,  Euros |
| Qwen3-8B | 34 | 1 | Euro,  euro,  the, 欧元,  called | 2 | the,  Euro, 欧元,  euro,  called |
| Qwen3-8B-GPTQ4 | 34 | 1 | Euro,  euro,  the, 欧元,  EUR | 2 | the,  Euro, 欧元,  euro,  called |
| Qwen3-14B | 38 | 3 | the,  called,  euro,  Euro,  euros | 3 | called,  the,  Euro,  euro,  known |
| Qwen3-32B-FP8 | 58 | 2 | 欧元,  euro,  Euro,  Euros,  euros | 2 | 欧元,  euro,  Euro, Euro,  euros |
| Qwen3.5-0.8B | 22 | 14 | currency,  called,  USD,  Currency,  coin | 19 | currency,  a,  the, 人民币,  USD |
| Qwen3.5-2B | 22 | 6 | USD,  currency,  called,  dollar,  dollars | 55 | the, 美元, 人民币,  USD,  U |
| Qwen3.5-9B | 30 | 1 | Euro,  Euros,  the,  euros,  EUR | 4 | the, 欧元,  called,  euros,  Euro |
| Qwen3.6-27B | 58 | 1 | euro,  Euro, 欧元,  euros,  Euros | 2 | 欧元,  euro,  Euro, Euro,  called |
| Qwen3.8-27B | 58 | 1 | euro,  Euro,  euros,  Euros, 欧元 | 2 | 欧元,  euro,  called,  Euro,  euros |

Table A7. Visibility of language tokens in the top-5 of the two lenses, over all (probe, layer) cells of the twenty-three models. “EN only” and “ZH only” count cells dark under one lens whose other lens carries at least one language token.

| Family | Both see | EN only | ZH only | Neither | Cells |
| --- | --- | --- | --- | --- | --- |
| Gemma-4 | 173 | 3 | 55 | 5 | 236 |
| Qwen3 | 510 | 4 | 322 | 96 | 932 |
| Qwen3.5 | 84 | 9 | 29 | 26 | 148 |
| Qwen3.6 | 29 | 1 | 58 | 28 | 116 |
| Qwen3.8 | 65 | 1 | 37 | 13 | 116 |
| All families | 861 | 18 | 501 | 168 | 1548 |

Table A8. Tokenization and truncation statistics at fit time. Windows were cut at exactly 128 tokens with the Qwen3-0.6B tokenizer and retokenized per model. Lengths are content tokens; the effective budget is 128 tokens for the Qwen tokenizers and 127 for Gemma-4, which prepends a beginning-of-sequence token.

| Model family | Tokenizer | Retokenized length | Windows truncated | Tokens lost | Valid positions |
| --- | --- | --- | --- | --- | --- |
| Qwen3 (15 models) | Qwen3-0.6B (shared) | EN 128 (all); ZH 127–128 (mean 128.0) | 0 / 0 | 0 / 0 | EN 111; ZH 110–111 (mean 111.0) |
| Qwen3.5 / 3.6 / 3.8 (5 models) | Qwen3.5 (shared) | EN 115–134 (median 128, mean 127.3); ZH 90–129 (median 115, mean 114.2) | EN 3 / ZH 1 | EN 12 / ZH 1 | EN 98–111 (mean 110.3); ZH 73–111 (mean 97.2) |
| Gemma-4 (3 models) | Gemma-4 (shared) | EN 112–140 (median 126, mean 125.1); ZH 96–152 (median 127, mean 127.5) | EN 243 / ZH 458 | EN 481 / ZH 3,302 | EN 96–111 (mean 108.7); ZH 80–111 (mean 108.2) |

Truncation removes tail tokens and leaves the window count unchanged. The two corpora are matched in window count and packing, but the number of positions a lens is fitted on depends on the tokenizer. For Qwen3.5, Qwen3.6 and Qwen3.8, Chinese windows retokenize shorter than English ones (median 115 against 128 content tokens), so the Chinese-fit lenses of these five models average 97 valid positions per window against 110 for the English-fit lenses. For Gemma-4, which prepends a beginning-of-sequence token, 243 English and 458 Chinese windows were truncated at fit, losing 0.4% and 2.6% of tokens. Neither difference reaches the language-share differences reported in Section 3, which run to 0.71 English against 0.15 Chinese under a Chinese-fitted lens. No window fell below the 18-token threshold in any fit.

### Candidate-pool overlap metrics by layer

Figures A1 through A20 give the per-layer trajectory of the candidate pool for every (model family, probe) pair, computed on the top-100 candidates of each lens at every measured layer. Within each figure the rows are the models of one family and the columns are four panels. The first two give the language composition of the English-fit and Chinese-fit candidate pools as stacked bars that sum to one at every layer, each band the share of one token class within that lens’s top-5: English, Chinese, other natural languages, and non-language tokens. The third is cross-language overlap without order, the larger of the two sides’ hit counts divided by the candidate depth, drawn twice. The solid curve counts a pair as related when the two tokens are identical or are translations of one another, and the dashed curve counts only identical tokens. The dashed is a strict subset of the solid by construction, so it can never rise above it. This nesting was checked on 951 layer samples spanning six models, three probes and three depths, with no violation. The fourth is overlap under order, the share of positions at which the two lists agree, again as a nested pair: cross-language in the solid curve, within-language in the dashed. Every model in the battery, including the six quantized variants of Qwen3-0.6B, carries both an English-fit and a Chinese-fit lens and is plotted here. Together with the aggregate Hit@5 of Table A5, these curves locate where in the depth axis the two lenses agree, on what kind of agreement they agree, and how the language mix of each candidate pool shifts with depth. The same trajectories at candidate depths 5 and 10, the depths at which the statistics quoted in the body are computed, are given in Figures A21 through A60, and every ordering reported in the body (cross-language above within-language at the same order, and unordered above ordered at the same language scope) holds at all three depths. Figures A61 through A63 repeat the four overlap measures of Figure 3 for the france-capital, sport, and spider-legs probes, on the top-100 pools at the last position.

### Candidate-pool metrics at top-5 and top-10

Figures A21 through A40 repeat Figures A1 through A20 with the candidate depth set to 5, and Figures A41 through A60 with the candidate depth set to 10. The statistics quoted in Sections 3.2 and 3.3 (the ordered-overlap rates and Table A7) are computed on the top-5 pools of Figures A21 through A40.

All sixty-three figures (A1–A63), with their captions, are available in the repository appendix: https://github.com/Paradeluxe/jprism-bilingual/blob/main/docs/APPENDIX_FIGURES.md.
