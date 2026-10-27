#!/usr/bin/env python3
"""build_results.py — generate ARCHIVE/RESULTS.md from the raw measurement JSON.

Why generated and not hand-written: RESULTS.md was hand-written once (2026-10-03) and a
transcription error shipped in it within minutes (a bf16 baseline was pasted into the
"quantized" column). Worse, six of its rows were invalidated hours later when a wrong
tokenizer was found — a summary written by hand cannot notice that its inputs moved.

This script reads ONLY the per-lens raw JSON that the measurement code produced, so the
summary is wrong only if the measurements themselves are wrong. Every claim in the generated
page is traceable to a file it names.

  usage:  python build_results.py            # read local ARCHIVE/measurements/raw
          python build_results.py --remote  # scp the cluster's raw json first
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

PROJ = Path(os.environ.get("JSPACE_ROOT", "."))
A = PROJ / "ARCHIVE"
RAW = A / "measurements" / "raw"
OUT = A / "RESULTS.md"
KEY = os.path.expanduser(os.environ.get("SICC_KEY", "~/.ssh/id_ed25519"))
HOST = os.environ.get("SICC_HOST", "user@host")  # set SICC_HOST=<user>@<ip> to pull from the cluster

# Non-full-protocol lenses: measured, but flagged wherever they appear.
N_MIN = 950          # below this a lens is a subset of the locked n=1000 corpus
EXCLUDE = {
    "qwen3-0.6b-q3km": "违反单调性（高于 Q4/Q5/Q6/Q8 四档）——产物可疑，不进表",
}


def pull_remote():
    RAW.mkdir(parents=True, exist_ok=True)
    subprocess.run(["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no",
                    "-o", "ConnectTimeout=25",
                    f"{HOST}:~/jspace/RESULT/MEASURE_SICC/*_raw.json", str(RAW)],
                   check=False, capture_output=True)
    for f in RAW.glob("*.md"):
        f.unlink()


def load():
    rows = []
    for f in sorted(RAW.glob("*_raw.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:                      # noqa: BLE001
            print(f"  skip {f.name}: {exc}")
            continue
        g = d.get("aggregate") or {}
        meta = d.get("lens_meta") or ""
        n = re.search(r"n_prompts=(\d+)", meta)
        rows.append(dict(
            tag=d.get("tag", "?"), corpus=d.get("corpus", "?"),
            device=d.get("device", "?"), layers=len(d.get("layers", [])),
            h5=g.get("j_hit5_rate_cells"), h10=g.get("j_hit10_rate_cells"),
            model=g.get("model_hit5_rate_prompts"),
            n=int(n.group(1)) if n else 0, src=f.name,
        ))
    return rows


def pct(v):
    return "—" if v is None else f"{v:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remote", action="store_true", help="scp the cluster raw json first")
    args = ap.parse_args()
    if args.remote:
        pull_remote()

    rows = [r for r in load() if r["h5"] is not None]
    en = sorted([r for r in rows if r["corpus"] == "wikitext"], key=lambda r: -r["h5"])
    zh = sorted([r for r in rows if r["corpus"] == "zhwiki"], key=lambda r: -r["h5"])
    usable = [r for r in en if r["tag"] not in EXCLUDE and r["n"] >= N_MIN]
    have = {r["tag"]: r for r in usable}

    L = []
    w = L.append
    w("# RESULTS — jspace 梯度测量汇总")
    w("")
    w("> **本文件由 `sicc/build_results.py` 从原始 JSON 自动生成，请勿手改。**")
    w("> 数据源：`ARCHIVE/measurements/raw/*_raw.json`（每份对应一个镜片的实测）。")
    w("> 手写过一次的版本在 minutes 内就混进了一个转录错误，且有六行在词表 bug 修复后失效——")
    w("> 汇总页不该由人抄数字。")
    w("")
    w(f"**实测 {len(rows)} 份**（英文 {len(en)} / 中文 {len(zh)}）"
      f"　**口径偏离 n=1000 的 {sum(1 for r in rows if r['n'] and r['n'] < N_MIN)} 份**"
      f"　**排除 {len(EXCLUDE)} 份**")
    w("")
    w("**口径:** Hit@5 / Hit@10 = prompt × layer **格子命中率**，主读位 pos=-1；"
      "模型 Hit@5 = 四道经典题的**题目命中率**。均直接取自测量代码的 `aggregate`，未改。")
    w("")

    w("## 一、全部实测（英文，按 Hit@5 降序）")
    w("")
    w("| 模型 | n | 层数 | Hit@5 | Hit@10 | 模型自己 | 设备 | 标记 |")
    w("|---|---|---|---|---|---|---|---|")
    for r in en:
        mark = ""
        if r["tag"] in EXCLUDE:
            mark = "**排除**"
        elif r["n"] and r["n"] < N_MIN:
            mark = f"**n={r['n']} 偏离**"
        w(f"| {r['tag']} | {r['n']} | {r['layers']} | {pct(r['h5'])} | {pct(r['h10'])} "
          f"| {pct(r['model'])} | {r['device']} | {mark} |")
    w("")

    # 规模曲线：bf16 / dense only, one lineage, full protocol
    # 规模曲线 —— grouped BY GENERATION, never merged. The hand-written version of this page
    # merged Qwen3 (0.6B/8B/14B) with Qwen3.5 (0.8B/2B) into one series and called it
    # "monotonically rising"; the merged sequence is 0.107 -> 0.104 -> 0.146 -> 0.191, i.e. it
    # DIPS at the join. A generation is a confound, not noise, so each lineage gets its own
    # table and its own monotonicity verdict.
    def gen(tag: str) -> str | None:
        m = re.match(r"qwen3\.(\d)", tag)
        if m:
            return f"Qwen3.{m.group(1)}"
        if tag.startswith("qwen3-"):
            return "Qwen3"
        return None

    def params(tag: str) -> float:
        m = re.search(r"(\d+(?:\.\d+)?)b", tag)
        return float(m.group(1)) if m else 0.0

    w("## 二、Qwen 规模曲线（bf16，按代际分组）")
    w("")
    # bf16 ONLY. A quantized rung at the same parameter count is a different model, not another
    # point on the scale curve — including them put 0.6B seven times in the same "lineage" and
    # produced a meaningless "sequence" of thirteen numbers with quantization noise in it.
    BF16 = re.compile(r"^qwen3(\.\d)?-\d+(\.\d+)?b$")
    lineages: dict[str, list] = {}
    for t, r in have.items():
        if not BF16.match(t):
            continue
        g = gen(t)
        if g:
            lineages.setdefault(g, []).append((t, r))
    for g in sorted(lineages):
        pts = sorted(lineages[g], key=lambda x: params(x[0]))
        if len(pts) < 2:
            continue
        seq = [r["h5"] for _, r in pts]
        w(f"### {g}")
        w("")
        w("| 模型 | 参数量 | n | Hit@5 | Hit@10 |")
        w("|---|---|---|---|---|")
        for t, r in pts:
            w(f"| {t} | {params(t):g}B | {r['n']} | {pct(r['h5'])} | {pct(r['h10'])} |")
        w("")
        w(f"序列：{' → '.join(f'{v:.3f}' for v in seq)}")
        w("")
        if all(b >= a for a, b in zip(seq, seq[1:])):
            w("**单调上升。**")
        else:
            dips = [f"{pts[i][0]} {seq[i]:.3f} → {pts[i+1][0]} {seq[i+1]:.3f}"
                    for i in range(len(seq) - 1) if seq[i + 1] < seq[i]]
            w(f"**非单调，下降段：** {'；'.join(dips)}。如实记录。")
        w("")
    w("⚠️ **代际不可合并**：Qwen3 与 Qwen3.5 是两个代际，混成一条会在接缝处出现假下降"
      "（3 代 0.6B=0.107 → 3.5 代 0.8B=0.104），看起来像噪声，其实是代际差。")
    w("⚠️ **Qwen3.8-27B 无法测量**：权重 2026-09-27 为配额所删，镜片尚在但无从测量。")
    w("")

    w("## 三、中文臂（⑩ 跨语）")
    w("")
    if zh:
        w("| 模型 | 英文 Hit@5 | 中文 Hit@5 | Δ |")
        w("|---|---|---|---|")
        pairs = 0
        for r in zh:
            base = next((e for e in en if e["tag"] == r["tag"] and e["tag"] not in EXCLUDE), None)
            if base:
                w(f"| {r['tag']} | {pct(base['h5'])} | {pct(r['h5'])} | {r['h5']-base['h5']:+.3f} |")
                pairs += 1
            else:
                w(f"| {r['tag']} | — | {pct(r['h5'])} | — |")
        w("")
        w(f"{pairs} 对有同模型英文对照。")
    w("")
    w("⚠️ **已知缺口**：中文镜片目前跑的是**英文经典四题**，不是中英同事实题集。"
      "⑩ 协议要求后者，因此本表只能说明「同一批英文题在中英镜片上的可读性差异」，"
      "不能作为严格的跨语言结论。")
    w("")

    w("## 四、量化臂")
    w("")
    groups: dict[str, list] = {}
    for r in usable:
        m = re.match(r"(.+)-(q\d\w*|fp8|awq|gptq\d?|bnb4)$", r["tag"])
        if m:
            groups.setdefault(m.group(1), []).append((m.group(2), r))
        else:
            groups.setdefault(r["tag"], [])

    w("### 4.1 量化档位 × 全部实测（同一基座内可比）")
    w("")
    for base, rungs in sorted(groups.items()):
        if not rungs:
            continue
        ref = have.get(base)
        w(f"**{base}**" + (f"　bf16 基准 Hit@5 = {pct(ref['h5'])}（n={ref['n']}）" if ref
                           else "　⚠️ 无 bf16 基准 —— 该基座的量化档无法与 dense 对照"))
        w("")
        w("| 档位 | n | 层数 | Hit@5 | Hit@10 | 模型自己 | vs bf16 |")
        w("|---|---|---|---|---|---|---|")
        if ref:
            w(f"| **bf16** | {ref['n']} | {ref['layers']} | **{pct(ref['h5'])}** | "
              f"**{pct(ref['h10'])}** | {pct(ref['model'])} | — |")
        for q, r in sorted(rungs, key=lambda x: x[0]):
            d = f"{r['h5']-ref['h5']:+.3f}" if ref else "—"
            w(f"| {q} | {r['n']} | {r['layers']} | {pct(r['h5'])} | {pct(r['h10'])} "
              f"| {pct(r['model'])} | {d} |")
        w("")

    w("### 4.2 跨代际的量化敏感性")
    w("")
    w("同一个量化档位在 3 代与 3.5 代上的表现差异（这正是「版本迭代 × 量化」的核心交叉项）")
    w("")
    w("| 档位 | Qwen3 系 | Qwen3.5 系 |")
    w("|---|---|---|")
    rungs_all = sorted({q for _, rs in groups.items() for q, _ in rs})
    for q in rungs_all:
        a = next((r["h5"] for b, rs in groups.items() if gen(b) == "Qwen3"
                  for qq, r in rs if qq == q), None)
        b_ = next((r["h5"] for b, rs in groups.items() if gen(b) == "Qwen3.5"
                   for qq, r in rs if qq == q), None)
        if a is not None and b_ is not None:
            w(f"| {q} | {pct(a)} | {pct(b_)} |")
    w("")
    w("⚠️ 可比性限制：同档位在两代的**基座模型不同**（0.6B vs 0.8B，1.7B vs 2B），"
      "因此这是「同档位跨代」的横向参照，不是同参量对照。")
    w("")

    w("## 五、口径偏离与排除")
    w("")
    off = [r for r in rows if r["n"] and r["n"] < N_MIN]
    if off:
        w("| 模型 | n | 偏离 | 处理 |")
        w("|---|---|---|---|")
        for r in off:
            short = 1000 - r["n"]
            w(f"| {r['tag']} | {r['n']} | 缺 {short} 条（{short/10:.1f}%） | "
              f"{'超 2% 阈值，标注后可用' if short/10 > 2 else '阈值内，可用'} |")
        w("")
    w("**排除:**")
    w("")
    for t, why in EXCLUDE.items():
        w(f"- `{t}` — {why}")
    w("")
    w("**其它不可用:**")
    w("")
    w("- `qwen3-1.7b` / `qwen3.8-27b` — 镜片在，权重已删，无法测量")
    w("- 中文臂 2B / 14B / 27B — 权重残缺，fit 未做")
    w("- 因果干预 ⑤（coordinate-swap / steer / ablate / J vs 非J）— **完全未做**")
    w("- 结构指标 ⑨（CKA / occupancy / 层带）— **完全未做**")
    w("")

    w("## 六、目录")
    w("")
    w("```")
    w("ARCHIVE/")
    w("  RESULTS.md              ← 本文件（自动生成）")
    w("  measurements/           实测报告 md")
    w("  measurements/raw/       实测原始 json（唯一数据源）")
    w("  failed_attempts/        真失败留证")
    w("  fit_cards/              FIT_CARD：dtype / 显存 / 速率 / 语料 sha256")
    w("  pilot_202609/           2026-09 老 pilot-4（口径不同）")
    w("  superseded/             n=100 试跑、12 层截断反例")
    w("  plans/                  PLAN / SOP / MEASUREMENTS / LOCKED_DECISIONS")
    w("lenses/local/             镜片本体 10 GB（本地为权威副本）")
    w("ARTIFACT_MANIFEST.md      镜片清单")
    w("```")
    w("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"  measured: {len(rows)} (en {len(en)} / zh {len(zh)})")
    print(f"  off-protocol: {len(off)}   excluded: {len(EXCLUDE)}")


if __name__ == "__main__":
    main()
