"""make_mt_hub.py — 把中文 token 翻译成英文、冻结成静态枢纽表（bilingual_mt_hub.tsv）。

用户方案落地：数据里未被词典/枢纽/词素剥离覆盖的中文 token（约 582 个）用本地
Qwen3.5-0.8B 一次性翻译成英文（贪心解码），清洗后写成 `zh<TAB>english` 枢纽行；
bilingual_align 加载后并入 _HUBS —— 匹配仍是"翻译到英文空间后求交"的确定性查表。

用法:
  python make_mt_hub.py                                   # 全量 OOV 翻译
  python make_mt_hub.py --limit 20                        # 只翻前 20 个高频（试跑）
  python make_mt_hub.py --meas data/RESULT/MEASURE_SICC   # 指到 measure_sicc.py 的输出目录
  python make_mt_hub.py --model-dir ~/models/Qwen3.5-0.8B --device cpu
"""
import glob
import json
import os
import re
import sys
from collections import Counter

import bilingual_align as A

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "bilingual_mt_hub.tsv")


def _arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


LIMIT = int(_arg("--limit", 0)) or None

# Where measure_sicc.py wrote MEAS_*_raw.json. The documented flow uses
# `--root data`, so try that first, then the older HERE/RESULT layout.
DEFAULT_MEAS = (
    os.path.join(REPO, "data", "RESULT", "MEASURE_SICC"),
    os.path.join(HERE, "RESULT", "MEASURE_SICC"),
)
MEAS_DIR = _arg("--meas") or next(
    (p for p in DEFAULT_MEAS if os.path.isdir(p)), DEFAULT_MEAS[0])

# Local path or Hub id of the small dense model used for the translation pass.
MODEL_DIR = _arg("--model-dir") or os.environ.get(
    "MT_HUB_MODEL", os.path.expanduser(os.path.join("~", "models", "Qwen3.5-0.8B")))
DEVICE = _arg("--device", "auto")

if any(a in ("-h", "--help") for a in sys.argv):
    print(__doc__)
    sys.exit(0)


def collect_oov():
    """数据里出现过的全部中文 token，取当前无覆盖（词典/枢纽/剥离都不中）的。"""
    zh = Counter()
    paths = sorted(glob.glob(os.path.join(MEAS_DIR, "MEAS_*_raw.json")))
    if not paths:
        sys.exit(f"ERROR: no MEAS_*_raw.json under {MEAS_DIR}\n"
                 f"pass --meas <dir>, or run measure_sicc.py --root data first")
    for path in paths:
        m = re.match(r"MEAS_(.+?)_(wikitext|zhwiki)_raw\.json$", os.path.basename(path))
        if not m:
            continue
        d = json.load(open(path, encoding="utf-8"))
        for r in d["results"]:
            if r.get("pos") not in (-1, None):
                continue
            seen = set()
            for lay in r["layers"]:
                for w, _ in (lay.get("j_top5") or []):
                    t = A.nrm(w)
                    if t not in seen and any("\u4e00" <= c <= "\u9fff" for c in t):
                        seen.add(t)
                        zh[t] += 1
    oov = [(t, n) for t, n in zh.most_common()
           if not (t in A._HUBS or t in A._TRANS or A._core_forms(t))]
    return oov


STOP_EN = {"a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
           "it", "its", "this", "that", "these", "those", "also", "too", "not", "no",
           "yes", "you", "we", "i", "he", "she", "they", "them", "his", "her",
           "their", "our", "your", "and", "or", "but", "so", "if", "of", "in", "on",
           "at", "to", "from", "for", "with", "as", "by", "will", "can", "could",
           "would", "should", "may", "might", "must", "do", "does", "did", "have",
           "has", "had", "what", "which", "who", "there", "here", "then", "than"}


def _all_stop(e):
    return all(w in STOP_EN for w in e.split())


def clean_en(s):
    s = s.split("\n")[0].strip().strip('."\'"').lower()
    s = re.sub(r"\(.*?\)|\[.*?\]", " ", s)
    parts = re.split(r"[,;/、或]| or ", s)
    out = []
    for p in parts:
        p = p.strip().strip(".'\"")
        p = re.sub(r"^(to|a|an|the|be|is|are|it is)\s+", "", p)
        if re.fullmatch(r"[a-z][a-z' -]{0,40}", p) and len(p) >= 2:
            out.append(p)
    return out


def main():
    oov = collect_oov()
    print(f"OOV 中文 token: {len(oov)} 个（按频次降序）")
    if LIMIT:
        oov = oov[:LIMIT]
        print(f"试跑模式：只翻前 {len(oov)} 个")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch

    device = DEVICE
    if device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    dtype = (torch.bfloat16 if device == "cuda"
             else torch.float16 if device == "mps" else torch.float32)
    print(f"loading {MODEL_DIR} on {device}")
    tok = AutoTokenizer.from_pretrained(MODEL_DIR)
    try:
        model = AutoModelForCausalLM.from_pretrained(MODEL_DIR, dtype=dtype)
    except TypeError:  # older transformers
        model = AutoModelForCausalLM.from_pretrained(MODEL_DIR, torch_dtype=dtype)
    model = model.to(device)
    model.eval()

    rows, samples = [], []
    # 合并模式：保留旧表里的行（避免覆盖丢失已译 token，新数据增量扩展）
    if os.path.exists(OUT):
        for line in open(OUT, encoding="utf-8"):
            a, _, b = line.rstrip("\n").partition("\t")
            if a and b:
                rows.append((a, b))
        print(f"existing rows kept: {len(rows)}")
    with torch.no_grad():
        for i, (t, n) in enumerate(oov):
            msgs = [{"role": "user", "content":
                     f"Translate this Chinese word or phrase into English. "
                     f"Output only the English translation, up to 3 alternatives "
                     f"separated by commas. If it is a grammatical particle or has no "
                     f"English meaning, output NONE.\nChinese: {t}"}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            ids = tok(text, return_tensors="pt").to(device)
            out = model.generate(**ids, max_new_tokens=24, do_sample=False,
                                 pad_token_id=tok.eos_token_id)
            gen = tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)
            # 纯语气/结构助词（吗/的呢吧…）的译文不可信（模型会幻觉出 what/no），整体丢弃
            if all(c in "吗呢吧啊呀嘛哦嗯了的着过" for c in t):
                ens = []
            else:
                ens = [e for e in clean_en(gen) if not _all_stop(e)]
            if ens:
                for e in ens:
                    rows.append((t, e))
                if len(samples) < 30:
                    samples.append((t, n, ens[:3]))
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(oov)} …")

    with open(OUT, "w", encoding="utf-8") as fh:
        for t, e in sorted(set(rows)):
            fh.write(t + chr(9) + e + chr(10))
    print(f"wrote {OUT}: {len(rows)} 行（{len(set(t for t,_ in rows))} 个 token 有译文）")
    print("\n抽样（token, 频次, 译文前3）:")
    for s in samples:
        print("  ", s)


if __name__ == "__main__":
    main()
