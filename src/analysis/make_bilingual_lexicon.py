"""make_bilingual_lexicon.py — build the translation resources for bilingual_align.py v2.1:

  bilingual_lexicon.tsv  direct translation pairs, one "a<TAB>b" per line (symmetric)
  bilingual_hubs.tsv     "token<TAB>english_hub" per line; two tokens are translation-
                         equivalent (two-hop) if their hub sets intersect

Sources: MUSE bilingual dictionaries (dl.fbaipublicfiles.com/arrival/dictionaries),
both directions, for every language seen in lens token lists (zh ru ja ko ar es it fr de pt).
zh side is duplicated traditional+simplified (opencc). The hand concept groups from the
report scripts are kept on top (covers € / 8 / -boot style entries MUSE lacks).

Run:  .venv/Scripts/python make_bilingual_lexicon.py
Needs opencc-python-reimplemented (only here, not in the report scripts).
"""
import os
import urllib.request

from opencc import OpenCC

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PAIRS = os.path.join(HERE, "bilingual_lexicon.tsv")
OUT_HUBS = os.path.join(HERE, "bilingual_hubs.tsv")
LANGS = ["zh", "ru", "ja", "ko", "ar", "es", "it", "fr", "de", "pt"]

# hand DICT v1.1 (concept -> surface forms); same content as the report scripts
HAND = {
    "EUR": ["euro", "euros", "欧元", "евро", "eur", "€"],
    "EURADJ": ["european", "europe"],
    "IT": ["italy", "italian", "italians", "意大利", "イタリア"],
    "BOOT": ["boot", "boots", "-boot", "靴"],
    "SHOE": ["shoe", "shoes", "鞋", "鞋子"],
    "HEEL": ["heel", "heels"],
    "CUR": ["currency", "currencies", "货币"],
    "CNY": ["人民币", "rmb"],
    "GBP": ["英镑", "pound", "pounds"],
    "CASH": ["钞票", "cash"],
    "USD": ["美元", "dollar", "dollars", "usd"],
    "MONEY": ["money", "钱"],
    "COIN": ["coin", "coins", "硬币"],
    "FR": ["france", "french", "法国", "法國", "法兰西"],
    "PARIS": ["paris", "巴黎"],
    "CAP": ["capital", "capitals", "首都", "首府"],
    "SPIDER": ["spider", "spiders", "蜘蛛"],
    "LEG": ["leg", "legs", "腿"],
    "EIGHT": ["eight", "8", "八"],
    "NUM": ["number", "numbers", "数字", "数量", "数目"],
    "SPORT": ["sport", "sports", "运动", "体育"],
    "SOC": ["soccer", "football", "足球"],
    "KICK": ["kick", "kicks", "踢"],
    "BALL": ["ball", "balls", "球"],
}

cc = OpenCC("t2s")


def nrm(t):
    return t.strip().casefold()


def zh_variants(w):
    return {w, cc.convert(w)}


pairs = set()   # direct translation edges
strong = set()  # MUSE / 手工来源（高置信）
hubs = {}       # token -> set of english hub words
for lg in LANGS:
    for name in (f"en-{lg}", f"{lg}-en"):
        url = f"https://dl.fbaipublicfiles.com/arrival/dictionaries/{name}.txt"
        local = os.path.join(HERE, "_" + name + ".txt")
        if not os.path.exists(local):
            print("downloading", url)
            urllib.request.urlretrieve(url, local)
        n = 0
        for line in open(local, encoding="utf-8"):
            # maxsplit=1: one side may be a multi-word phrase ("in order to 按"…)
            parts = line.rstrip("\n").split(None, 1)
            if len(parts) != 2:
                continue
            w1, w2 = nrm(parts[0]), nrm(parts[1])
            if not w1 or not w2 or w1 == w2:
                continue
            pairs.add((w1, w2))
            strong.add((w1, w2))
            if name == f"{lg}-en":       # col1=foreign  col2=english hub
                for v in zh_variants(w1) if lg == "zh" else {w1}:
                    hubs.setdefault(v, set()).add(w2)
                hubs.setdefault(w2, set()).add(w2)   # hub maps to itself
            else:                         # en-XX: col1=english hub col2=foreign
                for v in zh_variants(w2) if lg == "zh" else {w2}:
                    hubs.setdefault(v, set()).add(w1)
                hubs.setdefault(w1, set()).add(w1)
            n += 1
        print(f"{name}.txt: {n} raw pairs")

# --- CC-CEDICT：补 MUSE 缺失的中文复合词/常用动词（叫、叫做、被称为、称为…）---
# 格式: 傳統 传统 [pinyin] /gloss1/gloss2/.../    gloss 是英文释义短语
CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
CEDICT_LOCAL = os.path.join(HERE, "_cedict.txt.gz")
STOP = {"to", "be", "a", "an", "the", "of", "in", "on", "at", "as", "is", "are", "was",
        "were", "been", "being", "or", "and", "by", "for", "with", "that", "this", "it",
        "its", "so", "etc", "s", "one", "ones", "up", "out", "off", "from", "into",
        "used", "using", "use"}   # 注意：called/known/call 等必须保留
if not os.path.exists(CEDICT_LOCAL):
    print("downloading", CEDICT_URL)
    urllib.request.urlretrieve(CEDICT_URL, CEDICT_LOCAL)
import gzip
import re as _re
n_ced = 0
with gzip.open(CEDICT_LOCAL, "rt", encoding="utf-8") as fh:
    for line in fh:
        if line.startswith("#"):
            continue
        m = _re.match(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.+)/\s*$", line)
        if not m:
            continue
        trad, simp, glosses = m.group(1), m.group(2), m.group(4)
        zh_forms = {simp, trad, cc.convert(trad)}
        for i, gloss in enumerate(glosses.split("/")):
            if i >= 6:                      # 每词条最多取 6 个义项，控制噪声
                break
            gloss = _re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", gloss)   # 去括注
            for w in _re.split(r"[\s,;]+", gloss.lower()):
                w = w.strip("'\"-")
                if len(w) < 2 or w in STOP or not _re.match(r"^[a-z][a-z'-]*$", w):
                    continue
                for zh in zh_forms:
                    if zh and zh != w:
                        pairs.add((zh, w))
                n_ced += 1
print(f"cedict: {n_ced} raw gloss-word pairs")

for group in HAND.values():
    ws = [nrm(w) for w in group]
    for i in range(len(ws)):
        for j in range(i + 1, len(ws)):
            if ws[i] != ws[j]:
                pairs.add((ws[i], ws[j]))
                strong.add((ws[i], ws[j]))

with open(OUT_PAIRS, "w", encoding="utf-8") as fh:
    for a, b in sorted(pairs):
        fh.write(f"{a}\t{b}\n")
soft = pairs - strong
with open(os.path.join(HERE, "bilingual_lexicon_soft.tsv"), "w", encoding="utf-8") as fh:
    for a, b in sorted(soft):
        fh.write(f"{a}\t{b}\n")
print(f"soft (CEDICT-only) pairs: {len(soft)}  |  strong pairs: {len(strong)}")

with open(OUT_HUBS, "w", encoding="utf-8") as fh:
    for a in sorted(hubs):
        for h in sorted(hubs[a]):
            fh.write(f"{a}\t{h}\n")
print(f"wrote {OUT_PAIRS}  ({len(pairs)} unique pairs)")
print(f"wrote {OUT_HUBS}  ({len(hubs)} tokens with hubs)")
