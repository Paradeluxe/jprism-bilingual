"""bilingual_align.py — 中英双镜片 top-x 三分数（2026-10-07 终版，无关顺序）。

  1) 语言bias  bias_scores()  = (EN榜英文token数 + ZH榜中文token数) ÷ 2x
     —— 中文lens中文结果更多、英文lens英文结果更多则高（jlens 结果的语言 bias）。
  2) 语义相关  semantic_pairs() = 两榜 top-x 枚举 x×x 捉对，逐对判定语义相关
     （同形 或 词典可互译/英语枢纽两跳，含 morph 变体 euro/euros/Euro↔欧元；
     非语言 token 不参与）。头条读数 coverage =（有至少一个相关伙伴的 EN token
     数 + ZH token 数）/ 2x；密度 density = 相关对数 / x²。
     （另保留集合口径 semantic_overlap()：交集概念数 ÷ 较小概念集大小。）
  3) 严格一致  strict_score()  = 完全相同的词构成的多重集交集对数 ÷ x。
     （恒有 严格 ≤ 语义）
  4) 同序同形  seq_strict()    = 同位且同形的对数 ÷ x（顺序严格的 overlap 率）。
  5) 同序语义  seq_semantic()  = 同位且语义相关（同形或互译）的对数 ÷ x（⊇ 同序同形）。

x = 该档深度（min(两榜长度, k)）。语言判定：含汉字=zh；拉丁=en 或 x（已知外语词）；
其余（数字/符号等）=n。互译关系 = bilingual_lexicon.tsv（MUSE 10 语言双向 71 万对）
+ bilingual_hubs.tsv（英语枢纽两跳）+ 词素剥离（在意大利→意大利、这座城市→城市、的钱→钱；
核心须词典命中且不是虚词单字；剥离分支对侧须成词，挡 um/i 碎片碰撞）。
资源由 make_bilingual_lexicon.py 生成。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LEXICON = os.path.join(HERE, "bilingual_lexicon.tsv")
HUBS_TSV = os.path.join(HERE, "bilingual_hubs.tsv")

K_TOP = 10      # 默认取前 K 个候选（页面档位 top-5/10/100 会显式传 k）

_TRANS = {}
_HUBS = {}


def _load():
    if os.path.exists(LEXICON):
        with open(LEXICON, encoding="utf-8") as fh:
            for line in fh:
                a, _, b = line.rstrip("\n").partition("\t")
                if a and b:
                    _TRANS.setdefault(a, set()).add(b)
                    _TRANS.setdefault(b, set()).add(a)
    if os.path.exists(HUBS_TSV):
        with open(HUBS_TSV, encoding="utf-8") as fh:
            for line in fh:
                a, _, h = line.rstrip("\n").partition("\t")
                if a and h:
                    _HUBS.setdefault(a, set()).add(h)
    # MT 冻结表（make_mt_hub.py）：词典外中文 token 的英文译文，并入英语枢纽空间
    mt = os.path.join(HERE, "bilingual_mt_hub.tsv")
    if os.path.exists(mt):
        with open(mt, encoding="utf-8") as fh:
            for line in fh:
                a, _, h = line.rstrip("\n").partition("\t")
                if a and h and a != h:
                    _HUBS.setdefault(a, set()).add(h)
                    _HUBS.setdefault(h, set()).add(h)


_load()


def nrm(t):
    # strip + 去 BPE 记号 + casefold（保留内部标点，与已算数字一致）
    return t.strip().strip("▁Ġ").casefold()


def _is_language(t):
    """语言 token 判定：含任意 Unicode 字母（含西里尔/阿拉伯/假名等）→ True；
    纯数字/符号/下划线连串（___、\、"、…) → False，不参与三分数比较。"""
    import unicodedata
    return any(unicodedata.category(c).startswith("L") for c in t)


def _lang(t):
    # 粗粒度语言判定：含汉字=zh；含拉丁字母=en 或 x（已知外语词：在枢纽词典里
    # 只作为 外语→英语 的源词、无自映射，如 parigi/parís）；其余（数字/符号/
    # 西里尔/阿拉伯等）=n（对两块镜片都算"非正确语言"）。未收录的拉丁词默认 en。
    if any("\u4e00" <= c <= "\u9fff" for c in t):
        return "zh"
    if any("a" <= c <= "z" for c in t):
        h = _HUBS.get(t)
        if h and t not in h:
            return "x"
        return "en"
    return "n"


# --- 词素剥离：在X / 这座城市 / 在欧洲 这类"虚词前缀+核心"的复合 token ---
# 白名单只放开虚词；剥离出的核心必须能在词典/枢纽里解析（_forms 为空则整串不参与），
# 该"核心必须命中词典"即防假阳性的闸门。
_STRIP = set("在的是这那该本此个些种位名条只张们又还也就都很最更太被把对向从到和与或"
             "一二三四五六七八九十两几多少了着呢过之其为所"
             "座场部份期届双台辆艘架匹头封篇页项章节款类群批组"
             "叫有没不无未别请让使跟同"
             "我你他她它们谁什么吗吧呢啊呀嘛哦嗯")
_MAX_STRIP = 3     # 每端最多剥几个字
_MIN_CORE = 1      # 核心最短（单字核心如 的腿→腿 允许，靠词典命中兜底）


def _has_cjk(t):
    return any("一" <= c <= "鿿" for c in t)


def _raw_known(t):
    return bool(t in _TRANS or t in _HUBS)


def _core_variants(t):
    """t 的剥离变体（由短到长）：从左/右/两端逐字剥，每个被剥字须在 _STRIP 白名单。"""
    out, n = [], len(t)
    a_max = 0
    for a in range(1, _MAX_STRIP + 1):
        if n - a < _MIN_CORE or t[a - 1] not in _STRIP:
            break
        a_max = a
        out.append(t[a:])
    b_run = []
    for b in range(1, _MAX_STRIP + 1):
        if n - b < _MIN_CORE or t[n - b] not in _STRIP:
            break
        b_run.append(t[:n - b])
    out.extend(b_run)
    for a in range(1, a_max + 1):
        for b in range(1, _MAX_STRIP + 1):
            if n - a - b < _MIN_CORE or t[n - b] not in _STRIP:
                break
            out.append(t[a:n - b])
    return out


from functools import lru_cache


@lru_cache(maxsize=200000)
def _core_forms(t):
    """t 剥离后的可解析核心（不含自身）；核心不能是虚词单字（钱/门/球 这类内容字允许）。"""
    if not _has_cjk(t):
        return ()
    return tuple(v for v in _core_variants(t) if _raw_known(v) and v not in _STRIP)


def _ok_other(t):
    """剥离分支的对侧要求"成词"：含汉字，或拉丁串 >=3 字符（挡 um/i 这类碎片的交叉词碰撞）。"""
    return _has_cjk(t) or len(t) >= 3


def _rel_raw(a, b):
    if b in _TRANS.get(a, ()):
        return True
    ha, hb = _HUBS.get(a), _HUBS.get(b)
    return bool(ha and hb and not ha.isdisjoint(hb))


def translates(a, b):
    if _rel_raw(a, b):
        return True
    ca, cb = _core_forms(a), _core_forms(b)
    if ca and _ok_other(b) and any(_rel_raw(x, b) for x in ca):
        return True
    if cb and _ok_other(a) and any(_rel_raw(a, y) for y in cb):
        return True
    if ca and cb and any(_rel_raw(x, y) for x in ca for y in cb):
        return True
    return False


# --- 三分数（2026-10-07，无关顺序）------------------------------------------------

def bias_scores(en_words, zh_words, k=K_TOP):
    """1) 语言分布（四个读数，计数口径，无关顺序）：
       (EN镜片榜里英文占比, EN镜片榜里中文占比, ZH镜片榜里中文占比, ZH镜片榜里英文占比)。
    英文镜说英文/ZH镜说中文 = 语言 bias 强；EN榜全英 + ZH榜也全英（EN榜中=0 且 ZH榜英=1）= 与镜片语料无关。
    两侧都只有非语言 token → None。"""
    E = [nrm(w) for w, _ in en_words][:k]
    Z = [nrm(w) for w, _ in zh_words][:k]
    Ee = [t for t in E if _is_language(t)]
    Zz = [t for t in Z if _is_language(t)]
    if not Ee and not Zz:
        return None                       # 两侧都只有非语言 token → 不比较
    den_e = len(E) or 1
    den_z = len(Z) or 1
    en_en = sum(1 for t in Ee if _lang(t) == "en") / den_e
    zh_en = sum(1 for t in Ee if _lang(t) == "zh") / den_e
    zh_zh = sum(1 for t in Zz if _lang(t) == "zh") / den_z
    en_zh = sum(1 for t in Zz if _lang(t) == "en") / den_z
    return en_en, zh_en, zh_zh, en_zh


def _concept_partition(toks):
    """把 token 列表按 翻译等价（同串或词典互译，含英文形态变体）做并查集划分。"""
    parent = list(range(len(toks)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            if toks[i] == toks[j] or translates(toks[i], toks[j]):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri
    return [find(i) for i in range(len(toks))]


OVERLAP_MODE = "coef"   # 语义 overlap 归一化："coef" = |交集| / min(|C_EN|,|C_ZH|)；
                        # "divx" = |交集| / x（保留原 ÷x 惯例，可一行切换）


def semantic_overlap(en_words, zh_words, k=K_TOP):
    """2) 语义存在 overlap：两榜 top-x 的 token 各自按翻译等价类合并成概念集合
    （英文 morph 变体 euro/euros/Euro 同一概念；非语言 token 已剔除，无关顺序），
    求交集 O = C_EN ∩ C_ZH（两边都存在的概念），每个概念只计一次：
      coef 口径（默认）：|O| / min(|C_EN|, |C_ZH|) —— 较小概念集被覆盖的比例，1=全覆盖、0=零共享；
      divx 口径：|O| / x —— 除以该档深度。
    两侧都只有非语言 token → None；一侧无概念（另一侧有）→ 0.0（无共享）。"""
    E = [nrm(w) for w, _ in en_words][:k]
    Z = [nrm(w) for w, _ in zh_words][:k]
    Ee = [t for t in E if _is_language(t)]
    Zz = [t for t in Z if _is_language(t)]
    if not Ee and not Zz:
        return None                       # 两侧都只有非语言 token → 不比较
    roots = _concept_partition(Ee + Zz)
    ce = {r for r in roots[:len(Ee)]}
    cz = {r for r in roots[len(Ee):]}
    inter = len(ce & cz)
    if OVERLAP_MODE == "divx":
        x = min(len(E), len(Z), k)
        return inter / x if x else 0.0
    denom = min(len(ce), len(cz))
    return inter / denom if denom else 0.0


def semantic_pairs(en_words, zh_words, k=K_TOP):
    """2') 语义相关（捉对口径）：两榜 top-x 枚举 x×x 对，逐对判定是否语义相关——
    同形，或词典可互译/英语枢纽两跳（含 morph 变体 euro/euros/Euro↔欧元）；
    非语言 token（___、数字、符号）不参与。返回 (coverage, density)：
      coverage = (有至少一个相关伙伴的 EN token 数 + ZH token 数) / (2x)   ← 头条读数
      density  = 相关对数 / (x*x)                                        ← 细节
    两侧都只有非语言 token → None；一侧无语言 token（另一侧有）→ (0.0, 0.0)。"""
    E = [nrm(w) for w, _ in en_words][:k]
    Z = [nrm(w) for w, _ in zh_words][:k]
    Ee = [t for t in E if _is_language(t)]
    Zz = [t for t in Z if _is_language(t)]
    if not Ee and not Zz:
        return None                       # 两侧都只有非语言 token → 不比较
    x = min(len(E), len(Z), k)
    if not x:
        return 0.0, 0.0
    hit_e, hit_z, pairs = set(), set(), 0
    for i, a in enumerate(Ee):
        for j, b in enumerate(Zz):
            if a == b or translates(a, b):
                pairs += 1
                hit_e.add(i)
                hit_z.add(j)
    cov = (len(hit_e) + len(hit_z)) / (2.0 * x)
    return cov, pairs / (x * x)


def seq_strict(en_words, zh_words, k=K_TOP):
    """顺序严格的 overlap 率：同位（同一排名）且完全同形的对数 ÷ x（非语言 token 不参与）。"""
    E = [nrm(w) for w, _ in en_words][:k]
    Z = [nrm(w) for w, _ in zh_words][:k]
    if not any(_is_language(t) for t in E) and not any(_is_language(t) for t in Z):
        return None
    x = min(len(E), len(Z), k)
    if not x:
        return 0.0
    cnt = sum(1 for i in range(x)
              if E[i] == Z[i] and _is_language(E[i]) and _is_language(Z[i]))
    return cnt / x


def seq_semantic(en_words, zh_words, k=K_TOP):
    """顺序严格且语义严格：同位且语义相关（同形或词典互译/枢纽/MT/剥离）的对数 ÷ x。"""
    E = [nrm(w) for w, _ in en_words][:k]
    Z = [nrm(w) for w, _ in zh_words][:k]
    if not any(_is_language(t) for t in E) and not any(_is_language(t) for t in Z):
        return None
    x = min(len(E), len(Z), k)
    if not x:
        return 0.0
    cnt = 0
    for i in range(x):
        if not _is_language(E[i]) or not _is_language(Z[i]):
            continue
        if E[i] == Z[i] or translates(E[i], Z[i]):
            cnt += 1
    return cnt / x


def strict_score(en_words, zh_words, k=K_TOP):
    """3) 严格一致性：两榜 top-x 完全相同 token 的多重集交集对数 ÷ x（无关顺序）。"""
    from collections import Counter
    E = [nrm(w) for w, _ in en_words][:k]
    Z = [nrm(w) for w, _ in zh_words][:k]
    Ee = Counter(t for t in E if _is_language(t))
    Zz = Counter(t for t in Z if _is_language(t))
    if not Ee and not Zz:
        return None                       # 两侧都只有非语言 token → 不比较
    inter = sum((Ee & Zz).values())
    x = min(len(E), len(Z), k)
    return inter / x if x else 0.0
