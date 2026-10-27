#!/usr/bin/env python3
"""matrix_audit.py —「还有活吗／能收工吗」的矩阵对账探针（在集群 ~/jspace 下运行）。

回答「宣布没活了之前的唯一问题」：镜片与测量是否逐个 (tag, corpus) 对得上，
还有多少产物停在旧 k / 旧尺寸档。

三件输出：
  A. 有镜片但完全无测量（真缺口，按四状态第 2 栏处理）
  B. 有测量但仍是旧尺寸档（<400K；升级批的清单）
  C. 有测量但无镜片（孤儿，先查注册表/命名再看要不要清）

反坑（实测踩过）：re.match 拿「全路径模式」去 match os.path.basename 会静默 0 命中，
把「全齐」读成「全缺」。所以本脚本对测量集合做两路独立计数（glob 与 listdir）并要求
相等，不等就直接退出——先复核样例，别采信任何结论。

用法：python3 matrix_audit.py [~/jspace]
注：宣布「没活了」前还要 `squeue -s -j <票>` 数别家 step 名（别的 orchestrator 也是活），
并检查最近日志 mtime。
"""
import glob
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
OLD_K_BYTES = 400_000

lens = {}
for p in glob.glob(os.path.join(root, "lenses/local", "*", "jlens_n1000_Lstep2_*.pt")):
    m = re.search(r"jlens_n1000_Lstep2_(wikitext|zhwiki)\.pt$", p)
    if m:
        lens[(os.path.basename(os.path.dirname(p)), m.group(1))] = p

meas_dir = os.path.join(root, "RESULT", "MEASURE_SICC")
meas = {}
for p in glob.glob(os.path.join(meas_dir, "MEAS_*_raw.json")):
    m = re.match(r"MEAS_(.+?)_(wikitext|zhwiki)_raw\.json$", os.path.basename(p))
    if m:
        meas[(m.group(1), m.group(2))] = p

ARCHIVE_MARKERS = (".bak", ".archived", "recheck", ".hold", ".canon", ".smoke")


def _is_archive(name: str) -> bool:
    return any(k in name for k in ARCHIVE_MARKERS)


n_dir = 0
skipped = []
if os.path.isdir(meas_dir):
    for f in os.listdir(meas_dir):
        if not f.endswith("_raw.json"):
            continue
        if _is_archive(f):
            skipped.append(f)
            continue
        n_dir += 1

print(f"镜片 {len(lens)} 组；测量 {len(meas)} 份（目录计数 {n_dir} 份 canonical，跳过归档 {len(skipped)} 份）")
if skipped:
    print("   归档（不计入对账）：" + ", ".join(sorted(skipped)[:6])
          + (" …" if len(skipped) > 6 else ""))
if len(meas) != n_dir:
    print("!! 两路计数不一致——先复核样例，别采信 !!")
    sys.exit(2)

a = sorted(k for k in lens if k not in meas)
print(f"\nA. 有镜片但完全无测量（{len(a)}）:")
for t, c in a:
    print(f"   {t} {c}")

b = sorted(k for k in meas if k in lens and os.path.getsize(meas[k]) < OLD_K_BYTES)
print(f"\nB. 有测量但仍是旧尺寸档 <{OLD_K_BYTES}B（{len(b)}）:")
for t, c in b:
    print(f"   {t:30s} {c:9s} {os.path.getsize(meas[t, c]):>9d}B")

c_ = sorted(k for k in meas if k not in lens)
print(f"\nC. 有测量但无镜片（{len(c_)}）:")
for t, c in c_:
    print(f"   {t} {c}")

print("\n判读：A 空 + B 空 = 矩阵口径闭合；再做 squeue -s -j <票> 的别家 step 检查后才可宣布收工。")
