"""bilingual_top100_rbo_html.py — 中英双镜逐层对照页（每侧取 top-k，取自 top-100）+ 三分数。

用法: python bilingual_top100_rbo_html.py <EN_raw.json> <ZH_raw.json> <out.html> [k]

背景：镜片重测版（TOPK_STORE=100）在每层存满 100 个候选。本页把同一模型的两枚镜片
（EN 语料 fit / ZH 语料 fit）逐层并排，并给出每层的三个分数（bilingual_align.py，无关顺序）：

  语言bias：(EN榜英文token数 + ZH榜中文token数) ÷ 2x —— jlens 结果的语言 bias
  语义overlap：两榜各自合并成概念集合，交集概念数 ÷ 较小概念集大小（1=全覆盖，0=零共享）
  严格一致：完全相同的词的多重集交集对数 ÷ x（恒有 严格 ≤ 语义）
"""
import datetime
import html
import json
import os
import sys

import bilingual_align as ALIGN

EN, ZH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
K = int(sys.argv[4]) if len(sys.argv) > 4 else 10


en = json.load(open(EN, encoding="utf-8"))
zh = json.load(open(ZH, encoding="utf-8"))
en_res = {r["key"]: r for r in en["results"] if r.get("pos") in (-1, None)}
zh_res = {r["key"]: r for r in zh["results"] if r.get("pos") in (-1, None)}
keys = [k for k in en_res if k in zh_res]

metrics = {}
sections = []


def tokcell(words, targets, kk):
    out_ = []
    for w, s in words[:kk]:
        cls = " tgt" if w.lower() in targets else ""
        out_.append(f'<span class="tok{cls}">{html.escape(w)}<i>{s:g}</i></span>')
    return "".join(out_) or '<span class="tok none">—</span>'


for k in keys:
    er, zr = en_res[k], zh_res[k]
    et = [t.lower() for t in er["targets"]]
    zt = [t.lower() for t in zr["targets"]]
    zmap = {l["layer"]: l for l in zr["layers"]}
    mrows = {}
    body = []
    for lay in er["layers"]:
        z = zmap.get(lay["layer"])
        if z is None:
            continue
        en_words = lay.get("j_top5") or []
        zh_words = z.get("j_top5") or []
        bv4 = ALIGN.bias_scores(en_words, zh_words, k=K)
        if bv4 is None:                 # 两侧都只有非语言 token → 不比较，显示 -
            mrows[lay["layer"]] = {"en_en": None, "zh_en": None, "zh_zh": None, "en_zh": None,
                                   "semantic": None, "strict": None, "seq_strict": None,
                                   "seq_semantic": None}
            c1 = c2 = c3 = c4 = sem_cell = stc_cell = q1_cell = q2_cell = "-"
        else:
            sem = ALIGN.semantic_pairs(en_words, zh_words, k=K)[0]
            stc = ALIGN.strict_score(en_words, zh_words, k=K)
            mrows[lay["layer"]] = {"en_en": round(bv4[0], 4), "zh_en": round(bv4[1], 4),
                                   "zh_zh": round(bv4[2], 4), "en_zh": round(bv4[3], 4),
                                   "semantic": round(sem, 4), "strict": round(stc, 4),
                                   "seq_strict": round(ALIGN.seq_strict(en_words, zh_words, k=K), 4),
                                   "seq_semantic": round(ALIGN.seq_semantic(en_words, zh_words, k=K), 4)}
            c1 = f"{bv4[0]:.2f}"        # EN榜英文
            c2 = f"{bv4[1]:.2f}"        # EN榜中文
            c3 = f"{bv4[2]:.2f}"        # ZH榜中文
            c4 = f"{bv4[3]:.2f}"        # ZH榜英文
            sem_cell = f"{sem:.2f}"
            stc_cell = f"{stc:.2f}"
            q1_cell = f"{ALIGN.seq_strict(en_words, zh_words, k=K):.2f}"
            q2_cell = f"{ALIGN.seq_semantic(en_words, zh_words, k=K):.2f}"
        body.append(
            f'<tr><td class="lay">{lay["layer"]}</td>'
            f'<td class="rank">{lay.get("j_rank") if lay.get("j_rank") is not None else "—"}</td>'
            f'<td class="en">{tokcell(en_words, et, K)}</td>'
            f'<td class="rank">{z.get("j_rank") if z.get("j_rank") is not None else "—"}</td>'
            f'<td class="zh">{tokcell(zh_words, zt, K)}</td>'
            f'<td class="num">{c1}</td>'
            f'<td class="num">{c2}</td>'
            f'<td class="num">{c3}</td>'
            f'<td class="num">{c4}</td>'
            f'<td class="num">{sem_cell}</td>'
            f'<td class="num">{stc_cell}</td>'
            f'<td class="num">{q1_cell}</td>'
            f'<td class="num">{q2_cell}</td></tr>')
    metrics[k] = mrows
    sections.append(
        f'<section><h2>{html.escape(k)} <small>model rank {er["model_rank"]} · targets: '
        f'{html.escape(", ".join(er["targets"]))} / {html.escape(", ".join(zr["targets"]))}</small></h2>'
        f'<div class="q"><span class="qlab">probe</span><code>{html.escape(er.get("prompt", ""))}</code></div>'
            f'<table><thead><tr><th>layer</th><th>EN rk</th><th>EN top-{K}（取自 top-100）</th>'
            f'<th>ZH rk</th><th>ZH top-{K}（取自 top-100）</th>'
            f'<th>EN榜英<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">英文镜说英文</span></th>'
            f'<th>EN榜中<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">英文镜说中文</span></th>'
            f'<th>ZH榜中<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">中文镜说中文</span></th>'
            f'<th>ZH榜英<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">中文镜说英文</span></th>'
            f'<th>语义相关<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">x×x捉对覆盖率</span></th>'
            f'<th>严格一致<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">同形对数÷x</span></th>'
            f'<th>同序同形<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">同位同形÷x</span></th>'
            f'<th>同序语义<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">同位语义÷x</span></th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></section>')

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
title = f'{en["tag"]} 中英逐层 top-{K} 对比（取自 top-100）— 附三分数'
css = """
 :root { --bd:#d8dee9; --mut:#6b7280; --en:#1f6feb; --zh:#c2410c; }
 * { box-sizing:border-box }
 body { font:14px/1.5 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
        margin:0; padding:24px 28px; color:#1f2328; background:#fff }
 h1 { font-size:20px; margin:0 0 4px }
 .sub { color:var(--mut); margin-bottom:16px; font-size:13px; max-width:1080px }
 section { margin:26px 0 34px }
 h2 { font-size:15px; margin:0 0 8px; font-weight:600 }
 h2 small { font-weight:400; color:var(--mut); margin-left:8px; font-size:12px }
 table { border-collapse:collapse; width:100%; table-layout:fixed }
 th,td { border:1px solid var(--bd); padding:4px 8px; vertical-align:top; font-size:12.5px }
 th { background:#f6f8fa; text-align:left; position:sticky; top:0; z-index:2 }
 th:nth-child(1) { width:44px } th:nth-child(2),th:nth-child(4) { width:48px }
 th:nth-child(6),th:nth-child(7),th:nth-child(8),th:nth-child(9) { width:46px }
 th:nth-child(10),th:nth-child(11) { width:54px } th:nth-child(12),th:nth-child(13) { width:54px }
 td.lay { background:#f6f8fa; font-weight:600; color:var(--en); text-align:center }
 td.rank { text-align:center; color:var(--mut); font-variant-numeric:tabular-nums }
 td:nth-child(3) { border-left:2px solid var(--en) }
 td:nth-child(5) { border-left:2px solid var(--zh) }
 .tok { display:inline-block; margin:1px 5px 1px 0; white-space:nowrap;
        font-family:"Cascadia Mono",Consolas,monospace; font-size:12px }
 .tok i { color:var(--mut); font-style:normal; font-size:10.5px; margin-left:2px }
 .tok.tgt { background:#dcfce7; border:1px solid #16a34a; border-radius:3px; padding:0 3px }
 .tok.none { color:#bbb }
 .q { margin:3px 0 7px; font-size:12.5px; display:flex; gap:8px; align-items:baseline; flex-wrap:wrap }
 .q code { background:#f3f4f6; border:1px solid #e5e7eb; border-radius:3px;
           padding:1px 7px; font-family:"Cascadia Mono",Consolas,monospace }
 .qlab { color:var(--mut); font-size:11px; text-transform:uppercase; letter-spacing:.4px; min-width:44px }
 td.num { text-align:center; font-variant-numeric:tabular-nums; color:#374151; font-size:12px }
 .legend { margin:10px 0 0; font-size:12px; color:var(--mut) }
 .sw { display:inline-block; width:11px; height:11px; vertical-align:-1px; border-radius:2px; margin:0 4px 0 10px }
"""

doc = (f'<!doctype html><html lang="zh"><meta charset="utf-8"><title>{html.escape(title)}</title>'
       f'<style>{css}</style>'
       f'<h1>{html.escape(title)}</h1>'
       f'<div class="sub">同一模型、同一套四道英文探针，唯一差别是镜片在哪种语言的语料上 fit'
       f'（EN 镜片=wikitext，ZH 镜片=zhwiki）。<b>左边 EN 列＝英文镜片的读数，右边 ZH 列＝中文镜片的读数；两边的输入完全相同（同一模型、同一题、同一层、同一个句末向量）。</b>每层从该镜片的 top-100 候选里取前 {K} 个并排展示；'
       f'右侧四列是逐层分数（无关顺序，x = 该档深度 {K}）：'
       f'<b>EN纯</b> = EN镜片榜里英文 token 占比；<b>ZH纯</b> = ZH镜片榜里中文 token 占比（两个都高=各自说自家话；两个都低=两榜说对方的语言；都≈同值=与语料无关）；'
       f'<b>语义相关</b> = 两榜 top-x 枚举 x×x 捉对，逐对判定：同形或词典互译（含 morph 变体与复合词素剥离，如 在意大利→意大利）→ 相关；覆盖率 =（有相关伙伴的 EN token 数 + ZH token 数）÷ 2x；'
       f'只计两边都出现的概念、每个概念按<b>多的一方</b>计数，Σ ÷ x；'
       f'<b>严格一致</b> = 完全相同的词的多重集交集对数 ÷ x（恒有 严格 ≤ 语义）。'
       f'<b>同序同形</b> = 同位且同形的对数 ÷ x；<b>同序语义</b> = 同位且语义相关的对数 ÷ x。'
       f'非语言 token（___、数字、符号）不参与比较；两侧都只剩非语言 token 的层显示 -。'
       f'绿色框=该题目标词。'
       f'EN 文件: {html.escape(os.path.basename(EN))} · ZH 文件: {html.escape(os.path.basename(ZH))} · '
       f'生成于 {now}。（pos=-1 句末读数）</div>'
       f'<p class="legend"><span class="sw" style="background:#dcfce7;border:1px solid #16a34a"></span>目标词'
       f'　左边蓝线=英文镜片，右边橙线=中文镜片</p>'
       + "".join(sections) + '</html>')

open(OUT, "w", encoding="utf-8").write(doc)
with open(os.path.splitext(OUT)[0] + "_rbo.json", "w", encoding="utf-8") as fh:
    json.dump(metrics, fh, ensure_ascii=False, indent=1)
print(f"wrote {OUT}  ({os.path.getsize(OUT) // 1024} KB)")

print()
for k in keys:
    ms = metrics[k]
    ok = [L for L in ms if ms[L]["semantic"] is not None]
    if not ok:
        print(f"{k}: 全部层无可比较语言 token（-）")
        continue
    mean_q1 = sum(ms[L]["seq_strict"] for L in ok) / len(ok)
    mean_q2 = sum(ms[L]["seq_semantic"] for L in ok) / len(ok)
    m_ee = sum(ms[L]["en_en"] for L in ok) / len(ok)
    m_ze = sum(ms[L]["zh_en"] for L in ok) / len(ok)
    m_zz = sum(ms[L]["zh_zh"] for L in ok) / len(ok)
    m_ez = sum(ms[L]["en_zh"] for L in ok) / len(ok)
    mean_sem = sum(ms[L]["semantic"] for L in ok) / len(ok)
    mean_stc = sum(ms[L]["strict"] for L in ok) / len(ok)
    mxg = max(ok, key=lambda L: ms[L]["semantic"])
    print(f"{k}: mean EN榜英{m_ee:.2f}/中{m_ze:.2f} ZH榜中{m_zz:.2f}/英{m_ez:.2f}  语义={mean_sem:.3f} 严格={mean_stc:.3f}  同序同形/语义={mean_q1:.3f}/{mean_q2:.3f}  n={len(ok)}")

print()
print("boot_currency per-layer:")
for L in sorted(metrics["boot_currency"]):
    m = metrics["boot_currency"][L]
    if m["en_en"] is None:
        print(f"  L{L:02d}  -")
    else:
        print(f"  L{L:02d}  EN榜英{m['en_en']:.2f}/中{m['zh_en']:.2f}  ZH榜中{m['zh_zh']:.2f}/英{m['en_zh']:.2f}  语义={m['semantic']:.2f}  严格={m['strict']:.2f}")

print()
print("spotlights (top-8 both sides):")
if "boot_currency" in en_res:
    emap = {l["layer"]: l for l in en_res["boot_currency"]["layers"]}
    zmap2 = {l["layer"]: l for l in zh_res["boot_currency"]["layers"]}
    for L in (28, 44, 54):
        if L in emap and L in zmap2:
            print(f"L{L} EN:", [w for w, _ in emap[L]["j_top5"][:8]])
            print(f"L{L} ZH:", [w for w, _ in zmap2[L]["j_top5"][:8]])
