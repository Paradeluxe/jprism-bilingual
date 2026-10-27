"""all_models_bilingual_html.py — one page, every model that has BOTH an English and a Chinese
measurement, with a model switcher and a per-layer top-N (default 10) side-by-side view of the
EN and ZH lenses. Each layer row also carries the v2 translation-aware Δ pair (Δ同形, Δ全),
computed on the top-10 of each side by bilingual_align.py (identical > translatable > no match,
position- and rank-weighted; dictionary = MUSE en-zh/zh-en + hand concept groups).

Reads raw JSONs written by measure_sicc.py:
    RESULT/MEASURE_SICC/MEAS_<tag>_<corpus>_raw.json
Any model missing one of the two corpora is skipped and listed in the footer, so the gap is
visible rather than silently absent.
"""
import glob
import html
import json
import os
import re
import sys

import bilingual_align as ALIGN

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "all_models_bilingual.html"
TOPN = int(sys.argv[3]) if len(sys.argv) > 3 else 5


rows_by_tag = {}
for path in glob.glob(os.path.join(ROOT, "MEAS_*_raw.json")):
    m = re.match(r"MEAS_(.+?)_(wikitext|zhwiki)_raw\.json$", os.path.basename(path))
    if not m:
        continue
    tag, corpus = m.group(1), m.group(2)
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        continue
    rows_by_tag.setdefault(tag, {})[corpus] = d

models, skipped = [], []
for tag in sorted(rows_by_tag):
    pair = rows_by_tag[tag]
    if "wikitext" in pair and "zhwiki" in pair:
        models.append((tag, pair["wikitext"], pair["zhwiki"]))
    else:
        have = "+".join(sorted(pair))
        skipped.append((tag, have))

if not models:
    sys.exit("no model has both an English and a Chinese raw report in " + ROOT)


def pick(d, pos=-1):
    for r in d["results"]:
        if r.get("pos") == pos:
            return r
    return d["results"][0] if d["results"] else None


def esc(s):
    return html.escape(str(s))


def layer_rows(en_d, zh_d, n):
    er, zr = pick(en_d), pick(zh_d)
    if er is None or zr is None:
        return "", [], []
    targets = [t.lower() for t in er["targets"]]
    zmap = {l["layer"]: l for l in zr["layers"]}

    def hitflags(lay):
        low = [w.lower() for w, _ in (lay.get("j_top5") or [])]
        return any(t in low for t in targets)

    def cell(lay):
        out = []
        for w, s in (lay.get("j_top5") or [])[:n]:
            cls = ""
            if w.lower() in targets:
                cls = " tgt" if (lay.get("j_hit5") or lay.get("j_hit10")) else " tgt-out"
            out.append(f'<span class="tok{cls}">{esc(w)}<i>{s:g}</i></span>')
        return "".join(out) or '<span class="tok none">—</span>'

    body, en_hits, zh_hits = [], [], []
    for lay in er["layers"]:
        z = zmap.get(lay["layer"])
        if z is None:
            continue
        eh, zh = hitflags(lay), hitflags(z)
        en_hits.append((lay["layer"], 1 if eh else 0))
        zh_hits.append((lay["layer"], 1 if zh else 0))
        body.append(
            f'<tr class="{"hit" if (eh or zh) else ""}">'
            f'<td class="lay">{lay["layer"]}{" EN" if eh else ""}{" ZH" if zh else ""}</td>'
            f'<td class="rank">{lay.get("j_rank") if lay.get("j_rank") is not None else "—"}</td>'
            f'<td>{cell(lay)}</td>'
            f'<td class="rank">{z.get("j_rank") if z.get("j_rank") is not None else "—"}</td>'
            f'<td>{cell(z)}</td></tr>')
    return "".join(body), en_hits, zh_hits


MODEL_HTML = []
KS = (1, 5, 10, 100)   # 页面可切换的深度档位
# pre-pass: per-model gap aggregates at each depth K (mean Δ同形 / Δ全 over all layer cells)
GAPSTATS, STORED = {}, {}
for tag, en_d, zh_d in models:
    per_k = {K: [0.0] * 8 + [0] for K in KS}  # ΣEN英,ΣEN中,ΣZH中,ΣZH英,Σ语义,Σ严格,Σ同序同形,Σ同序语义,n
    depth = 0
    for r in en_d["results"]:
        if r.get("pos") != -1:
            continue
        zmap2 = {l["layer"]: l for l in
                 next((x for x in zh_d["results"]
                       if x["key"] == r["key"] and x.get("pos") == -1), {"layers": []})["layers"]}
        for lay in r["layers"]:
            depth = max(depth, len(lay.get("j_top5") or []))
            z = zmap2.get(lay["layer"])
            if z is None:
                continue
            ew, zw = lay.get("j_top5") or [], z.get("j_top5") or []
            for K in KS:
                bv3 = ALIGN.bias_scores(ew, zw, k=K)
                if bv3 is None:          # 两侧都只有非语言 token → 不比较、不计入均值
                    continue
                per_k[K][0] += bv3[0]    # EN榜英文
                per_k[K][1] += bv3[1]    # EN榜中文
                per_k[K][2] += bv3[2]    # ZH榜中文
                per_k[K][3] += bv3[3]    # ZH榜英文
                per_k[K][4] += ALIGN.semantic_pairs(ew, zw, k=K)[0]
                per_k[K][5] += ALIGN.strict_score(ew, zw, k=K)
                per_k[K][6] += ALIGN.seq_strict(ew, zw, k=K) or 0.0
                per_k[K][7] += ALIGN.seq_semantic(ew, zw, k=K) or 0.0
                per_k[K][8] += 1
    GAPSTATS[tag] = {K: tuple(v[i] / v[8] for i in range(8)) + (v[8],)
                     if v[8] else (0.0,) * 8 + (0,) for K, v in per_k.items()}
    STORED[tag] = depth

for tag, en_d, zh_d in models:
    ea, za = en_d["aggregate"], zh_d["aggregate"]
    er = pick(en_d)
    q = er.get("prompt", "") if er else ""
    tgt = ", ".join(er["targets"]) if er else ""
    body, en_hits, zh_hits = layer_rows(en_d, zh_d, 5)
    p1, p2, sp, sq = [], [], [], []
    for K in KS:
        e_en, e_zh, z_zh, z_en, ms, mt, sqs, sqm, ncells = GAPSTATS[tag][K]
        if ncells:
            p1.append(f'<b class="t{K}">英 {e_en:.2f} / 中 {e_zh:.2f}</b>')
            p2.append(f'<b class="t{K}">中 {z_zh:.2f} / 英 {z_en:.2f}</b>')
            sp.append(f'<b class="t{K}">{ms:.2f}·{mt:.2f}</b>')
            sq.append(f'<b class="t{K}">{sqs:.2f}/{sqm:.2f}</b>')
        else:
            p1.append(f'<b class="t{K}">-</b>')
            p2.append(f'<b class="t{K}">-</b>')
            sp.append(f'<b class="t{K}">-</b>')
            sq.append(f'<b class="t{K}">-</b>')
    dep_badge = ('<span class="pill warn need10">仅存 top-5 候选，10/100 档数值同 top-5</span>'
                 if STORED[tag] < 100 else '<span class="pill plain">已存 top-100 候选</span>')
    body, en_hits, zh_hits = layer_rows(en_d, zh_d, 5)
    layers = [l for l, _ in en_hits]
    peak_e = max([v for _, v in en_hits] or [1]) or 1
    peak_z = max([v for _, v in zh_hits] or [1]) or 1
    strip_e = "".join(
        f'<i class="on{max(1,v)}" style="height:{max(3, round(15*v/peak_e))}px" '
        f'title="L{l}: {v}"></i>' for l, v in en_hits)
    strip_z = "".join(
        f'<i class="on{max(1,v)}" style="height:{max(3, round(15*v/peak_z))}px" '
        f'title="L{l}: {v}"></i>' for l, v in zh_hits)
    quiz = "".join(
        f'<li><code>{esc(pick(en_d)["prompt"])}</code></li>'
        for _ in [0]) if er else ""
    prompts = "".join(
        f'<li><code>{esc(r.get("prompt",""))}</code> → <b>{esc(", ".join(r["targets"]))}</b>'
        f'<span class="mr">model rank {r.get("model_rank")}</span></li>'
        for r in en_d["results"] if r.get("pos") == -1)

    MODEL_HTML.append(f"""
<section class="model" id="m_{esc(tag)}" hidden>
  <div class="mhead">
    <h2>{esc(tag)}</h2>
    <div class="nums">
      <span class="pill en">EN Hit@5 <b>{ea["j_hit5_rate_cells"]:.4f}</b>
        <i>Hit@10 {ea["j_hit10_rate_cells"]:.4f}</i></span>
      <span class="pill zh">ZH Hit@5 <b>{za["j_hit5_rate_cells"]:.4f}</b>
        <i>Hit@10 {za["j_hit10_rate_cells"]:.4f}</i></span>
      <span class="pill plain">model 自身 Hit@5
        <b>{ea["model_hit5_rate_prompts"]:.2f} / {za["model_hit5_rate_prompts"]:.2f}</b>
        <i>EN / ZH</i></span>
      <span class="pill plain">{esc(en_d["lens_meta"].split("d_model=")[1].split(",")[0])} dim ·
        {len(layers)} layers · {ea["n_cells"]} cells</span>
      <span class="pill plain">EN镜片 {"".join(p1)}</span>
      <span class="pill plain">ZH镜片 {"".join(p2)}</span>
      <span class="pill plain">语义·严格 {"".join(sp)}</span>
      <span class="pill plain">同序 同形/语义 {"".join(sq)}</span>
      {dep_badge}
    </div>
  </div>
  <div class="strip"><b>EN</b><span class="bar">{strip_e}</span></div>
  <div class="strip"><b>ZH</b><span class="bar">{strip_z}</span></div>
  <details class="quiz" open><summary>四道探针题（中英镜片用同一套英文题）</summary>
    <ol>{prompts}</ol></details>
  <div id="tables_{esc(tag)}"></div>
</section>""")

# per-model tables built lazily is overkill; embed all, JS shows one
TABLE_HTML = []
for tag, en_d, zh_d in models:
    er = pick(en_d)
    if er is None:
        continue
    zr = pick(zh_d)
    zmap = {l["layer"]: l for l in zr["layers"]}
    targets = [t.lower() for t in er["targets"]]
    secs = []
    for r in en_d["results"]:
        if r.get("pos") != -1:
            continue
        tg = [t.lower() for t in r["targets"]]
        zr_layers = {l["layer"]: l for l in
                     next((x for x in zh_d["results"]
                           if x["key"] == r["key"] and x.get("pos") == -1), {"layers": []})["layers"]}
        body = []
        for lay in r["layers"]:
            z = zr_layers.get(lay["layer"])
            if z is None:
                continue

            def cell(l, tlist):
                o = []
                for p, (w, s) in enumerate(l.get("j_top5") or [], 1):
                    c = (" tgt" if (l.get("j_hit5") or l.get("j_hit10")) else " tgt-out") \
                        if w.lower() in tlist else ""
                    kc = "" if p == 1 else (" k5" if p <= 5 else (" k10" if p <= 10 else " k100"))
                    o.append(f'<span class="tok{c}{kc}">{esc(w)}<i>{s:g}</i></span>')
                return "".join(o) or '<span class="tok none">—</span>'

            def hit(l, tlist):
                return any(w.lower() in tlist for w, _ in (l.get("j_top5") or [])[:10])

            eh, zh = hit(lay, tg), hit(z, tg)
            c1, c2, c3, c4, sms, sts, q1, q2 = [], [], [], [], [], [], [], []
            for K in KS:
                ew, zw = lay.get("j_top5") or [], z.get("j_top5") or []
                bv4 = ALIGN.bias_scores(ew, zw, k=K)
                if bv4 is None:          # 两侧都只有非语言 token（___、数字、符号）→ 显示 -
                    c1.append("-"); c2.append("-"); c3.append("-"); c4.append("-")
                    sms.append("-"); sts.append("-"); q1.append("-"); q2.append("-")
                    continue
                c1.append(f"{bv4[0]:.2f}")   # EN榜英文
                c2.append(f"{bv4[1]:.2f}")   # EN榜中文
                c3.append(f"{bv4[2]:.2f}")   # ZH榜中文
                c4.append(f"{bv4[3]:.2f}")   # ZH榜英文
                sms.append(f"{ALIGN.semantic_pairs(ew, zw, k=K)[0]:.2f}")
                sts.append(f"{ALIGN.strict_score(ew, zw, k=K):.2f}")
                q1.append(f"{ALIGN.seq_strict(ew, zw, k=K):.2f}")
                q2.append(f"{ALIGN.seq_semantic(ew, zw, k=K):.2f}")

            def seq(name, vals):
                return "".join(f' {name}{K}="{v}"' for K, v in zip(KS, vals))

            body.append(
                f'<tr class="{"hit" if (eh or zh) else ""}">'
                f'<td class="lay">{lay["layer"]}{" EN" if eh else ""}{" ZH" if zh else ""}</td>'
                f'<td class="rank">{lay.get("j_rank") if lay.get("j_rank") is not None else "—"}</td>'
                f'<td>{cell(lay, tg)}</td>'
                f'<td class="rank">{z.get("j_rank") if z.get("j_rank") is not None else "—"}</td>'
                f'<td>{cell(z, tg)}</td>'
                f'<td class="rbo"{seq("data-v", c1)}>{c1[0]}</td>'
                f'<td class="rbo"{seq("data-v", c2)}>{c2[0]}</td>'
                f'<td class="rbo"{seq("data-v", c3)}>{c3[0]}</td>'
                f'<td class="rbo"{seq("data-v", c4)}>{c4[0]}</td>'
                f'<td class="rbo"{seq("data-v", sms)}>{sms[0]}</td>'
                f'<td class="rbo"{seq("data-v", sts)}>{sts[0]}</td>'
                f'<td class="rbo"{seq("data-v", q1)}>{q1[0]}</td>'
                f'<td class="rbo"{seq("data-v", q2)}>{q2[0]}</td></tr>')
        mt = ", ".join(f"`{w}`" for w, _ in (r.get("model_top5") or []))
        secs.append(
            f'<h3>{esc(r["key"])} <small>model rank {r.get("model_rank")}</small></h3>'
            f'<div class="q"><span class="qlab">probe</span><code>{esc(r.get("prompt",""))}</code></div>'
            f'<div class="q"><span class="qlab">answer</span>'
            f'<code class="ans">{esc(", ".join(r["targets"]))}</code>'
            f'<span class="qlab ml">model top-{len(r.get("model_top5") or [])}</span>'
            f'<code>{esc(mt)}</code></div>'
            f'<table><thead><tr><th>layer</th><th>EN rank</th>'
            f'<th>EN top-<span class="t1">1</span><span class="t5">5</span>'
            f'<span class="t10">10</span><span class="t100">100</span></th>'
            f'<th>ZH rank</th><th>ZH top-<span class="t1">1</span><span class="t5">5</span>'
            f'<span class="t10">10</span><span class="t100">100</span></th>'
            f'<th>EN榜英<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">英文镜说英文</span></th>'
            f'<th>EN榜中<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">英文镜说中文</span></th>'
            f'<th>ZH榜中<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">中文镜说中文</span></th>'
            f'<th>ZH榜英<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">中文镜说英文</span></th>'
            f'<th>语义相关<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">x×x捉对覆盖率</span></th>'
            f'<th>严格一致<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">同形对数÷x</span></th>'
            f'<th>同序同形<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">同位同形÷x</span></th>'
            f'<th>同序语义<span style="display:block;font-weight:400;color:#6b7280;font-size:9.5px">同位语义÷x</span></th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table>')
    TABLE_HTML.append(f'<div class="tables" id="t_{esc(tag)}" hidden>{"".join(secs)}</div>')

tabs = "".join(
    f'<button data-tag="{esc(tag)}" class="{"on" if i == 0 else ""}">{esc(tag)}</button>'
    for i, (tag, _, _) in enumerate(models))
skip_html = ""
if skipped:
    skip_html = ("<p class='skip'>只有单语结果（未进入本页）："
                 + "、".join(f"{esc(t)}（{esc(h)}）" for t, h in skipped) + "</p>")

doc = f"""<!doctype html><html lang="zh"><meta charset="utf-8">
<title>J-lens 中英逐层 top-5/10/100 对比 — 全模型</title>
<style>
 :root {{ --bd:#dde3ea; --mut:#6b7280; --en:#1f6feb; --zh:#c2410c }}
 * {{ box-sizing:border-box }}
 body {{ font:14px/1.5 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif; margin:0;
        padding:20px 24px 60px; color:#1f2328; background:#fff }}
 h1 {{ font-size:19px; margin:0 0 3px }}
 .sub {{ color:var(--mut); font-size:12.5px; margin-bottom:14px }}
 .tabs {{ display:flex; flex-wrap:wrap; gap:6px; margin:0 0 18px; position:sticky;
          top:0; background:#fff; padding:8px 0; border-bottom:1px solid var(--bd); z-index:9 }}
 .tabs button {{ font:inherit; font-size:12.5px; padding:4px 12px; cursor:pointer;
                 border:1px solid var(--bd); border-radius:14px; background:#fff; color:#374151 }}
 .tabs button.on {{ background:#111827; color:#fff; border-color:#111827 }}
 .tabs button:hover:not(.on) {{ background:#f3f4f6 }}
 .depths {{ display:flex; gap:6px; align-items:center; margin:0 0 16px; position:sticky;
           top:44px; background:#fff; padding:6px 0; border-bottom:1px solid var(--bd); z-index:8 }}
 .depths .lab {{ color:var(--mut); font-size:12px }}
 .depths button {{ font:inherit; font-size:12.5px; padding:3px 12px; cursor:pointer;
                  border:1px solid var(--bd); border-radius:12px; background:#fff; color:#374151 }}
 .depths button.on {{ background:#1d4ed8; color:#fff; border-color:#1d4ed8 }}
 body[data-k="1"] .k5, body[data-k="1"] .k10, body[data-k="1"] .k100,
 body[data-k="5"] .k10, body[data-k="5"] .k100,
 body[data-k="10"] .k100 {{ display:none }}
 body[data-k="1"] .t5, body[data-k="1"] .t10, body[data-k="1"] .t100,
 body[data-k="5"] .t1, body[data-k="5"] .t10, body[data-k="5"] .t100,
 body[data-k="10"] .t1, body[data-k="10"] .t5, body[data-k="10"] .t100,
 body[data-k="100"] .t1, body[data-k="100"] .t5, body[data-k="100"] .t10 {{ display:none }}
 body[data-k="1"] .need10, body[data-k="5"] .need10 {{ display:none }}
 .pill.warn {{ border-color:#d97706; color:#92400e; background:#fffbeb }}
 .mhead h2 {{ font-size:16px; margin:0 0 6px }}
 .nums {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px }}
 .pill {{ font-size:11.5px; border:1px solid var(--bd); border-radius:5px; padding:2px 8px;
          background:#fafbfc }}
 .pill b {{ font-size:13px; margin:0 3px }}
 .pill i {{ color:var(--mut); font-style:normal }}
 .pill.en b {{ color:var(--en) }} .pill.zh b {{ color:var(--zh) }}
 .strip {{ display:flex; align-items:center; gap:8px; margin:3px 0 }}
 .strip b {{ width:22px; color:var(--mut); font-size:11.5px }}
 .bar {{ display:inline-flex; gap:2px; align-items:flex-end; height:16px; flex-wrap:wrap }}
 .bar i {{ width:7px; height:3px; background:#e5e7eb; border-radius:1px }}
 .bar i[class*="on"] {{ background:#86efac }}
 .bar i.on2 {{ background:#4ade80 }} .bar i.on3 {{ background:#22c55e }}
 .bar i.on4 {{ background:#15803d }}
 .quiz {{ margin:10px 0 14px; border:1px solid var(--bd); border-radius:5px;
          padding:7px 12px; background:#fcfcfd }}
 .quiz summary {{ cursor:pointer; font-size:12px; color:var(--mut); font-weight:600 }}
 .quiz ol {{ margin:7px 0 1px; padding-left:20px }}
 .quiz li {{ margin:2px 0; font-size:12.5px }}
 .quiz code, .q code {{ background:#f3f4f6; border:1px solid #e5e7eb; border-radius:3px;
          padding:1px 6px; font-family:"Cascadia Mono",Consolas,monospace }}
 .quiz b {{ color:#15803d }} .mr {{ color:var(--mut); font-size:11px; margin-left:9px }}
 h3 {{ font-size:14px; margin:20px 0 5px }}
 h3 small {{ font-weight:400; color:var(--mut); font-size:11.5px; margin-left:7px }}
 .q {{ margin:2px 0 5px; font-size:12.5px; display:flex; gap:7px; align-items:baseline;
       flex-wrap:wrap }}
 .q code.ans {{ background:#dcfce7; border-color:#16a34a; font-weight:600 }}
 .qlab {{ color:var(--mut); font-size:10.5px; text-transform:uppercase; letter-spacing:.4px;
          min-width:42px }}
 .qlab.ml {{ margin-left:12px }}
 table {{ border-collapse:collapse; width:100%; table-layout:fixed; margin-bottom:6px }}
 th,td {{ border:1px solid var(--bd); padding:3px 7px; vertical-align:top; font-size:12px }}
 th {{ background:#f6f8fa; text-align:left; position:sticky; top:44px }}
 th:nth-child(1),th:nth-child(2),th:nth-child(4) {{ width:54px }}
 th:nth-child(6),th:nth-child(7),th:nth-child(8),th:nth-child(9) {{ width:50px }}
 th:nth-child(10),th:nth-child(11) {{ width:54px }}
 th:nth-child(12),th:nth-child(13) {{ width:54px }}
 td.lay {{ background:#f6f8fa; font-weight:600; color:var(--en); text-align:center }}
 td.rank {{ text-align:center; color:var(--mut); font-variant-numeric:tabular-nums }}
 tr.hit td.lay {{ color:#15803d }} tr.hit {{ background:#f2fdf5 }}
 td:nth-child(3) {{ border-left:2px solid var(--en) }}
 td:nth-child(5) {{ border-left:2px solid var(--zh) }}
 td.rbo {{ text-align:center; color:#374151; font-variant-numeric:tabular-nums; font-size:11.5px }}
 .tok {{ display:inline-block; margin:1px 4px 1px 0; white-space:nowrap;
        font-family:"Cascadia Mono",Consolas,monospace; font-size:11.5px }}
 .tok i {{ color:var(--mut); font-style:normal; font-size:10px; margin-left:2px }}
 .tok.tgt {{ background:#dcfce7; border:1px solid #16a34a; border-radius:3px; padding:0 2px }}
 .tok.tgt-out {{ background:#fef3c7; border:1px dashed #d97706; border-radius:3px; padding:0 2px }}
 .tok.none {{ color:#bbb }}
 .skip {{ color:var(--mut); font-size:12px; margin-top:26px; border-top:1px solid var(--bd);
          padding-top:10px }}
 .legend {{ font-size:12px; color:var(--mut); margin:6px 0 0 }}
 .sw {{ display:inline-block; width:11px; height:11px; vertical-align:-1px; border-radius:2px;
       margin:0 4px 0 10px }}
</style>
<body data-k="5">
<h1>J-lens 中英镜片逐层对比 · 全模型（top-5/10/100 可切换）</h1>
<div class="sub">每个模型的两块镜片在各自语料上 fit，用<strong>同一套四道英文题</strong>探测。
左列 = 英文镜片读数，右列 = 中文镜片读数；两边输入完全相同（同一模型、同一题、同一层、同一个句末向量）。
model 自身能力两语相同，所以 Hit@5 的差距只来自镜片。绿底行 = 至少一边命中 top-10；
层号后 EN/ZH = 该层命中。</div>
<div class="tabs">{tabs}</div>
<div class="depths"><span class="lab">分数深度</span>
 <button data-k="1">top-1</button>
 <button data-k="5" class="on">top-5</button>
 <button data-k="10">top-10</button>
 <button data-k="100">top-100</button>
 <span class="lab" style="margin-left:10px">候选不足的模型按已存深度计算（橙标提示）</span></div>
<p class="legend"><span class="sw" style="background:#dcfce7;border:1px solid #16a34a"></span>答案在 top-5
 <span class="sw" style="background:#fef3c7;border:1px dashed #d97706"></span>答案在 top-10 但不在 top-5
 左蓝线=英文镜片，右橙线=中文镜片<br>
 <b>三分数（无关顺序，x = 该档深度，深度随上方 top-1/5/10/100 档位统一截断）</b>：
 <b>四读数</b>（每榜两语占比）：EN榜英/EN榜中/ZH榜中/ZH榜英——EN榜英与ZH榜中高 = 各自说自家语料语言（语言 bias 强）；
 <b>无 bias 签名：两榜同说一种语言</b>（如两榜全英时 EN榜英=1、EN榜中=0、ZH榜中=0、ZH榜英=1）；ZH榜英高 = 中文镜片漏英文，EN榜中高 = 英文镜片漏中文；
 <b>语义相关</b> = 两榜 top-x 枚举 <b>x×x 捉对</b>，逐对判定：同形 或 词典可互译/英语枢纽两跳（含 morph 变体 euro/euros/Euro↔欧元）→ 相关；
 覆盖率 = （有至少一个相关伙伴的 EN token 数 + ZH token 数）÷ 2x（1=两侧每个 token 都找到语义伙伴）；
 复合词素剥离：在意大利→意大利、这座城市→城市、的钱→钱 也算相关（核心须词典命中）；字典=MUSE 多语 {len(ALIGN._TRANS)} 对+英语枢纽 {len(ALIGN._HUBS)} 词；
 <b>严格一致</b> = 完全相同的词构成的多重集交集对数 ÷ x。恒有 严格 ≤ 语义。
 <b>同序同形</b> = 同位（同一排名）且完全同形的对数 ÷ x（顺序严格的 overlap 率）；
 <b>同序语义</b> = 同位且语义相关（同形或互译）的对数 ÷ x（⊇ 同序同形）。
 <b>非语言 token（___、数字、符号）不参与任何比较</b>；两侧都只剩非语言 token 的层不做比较，三列显示 <b>-</b> 且不计入均值。
 K 敏感性与补测状态见 bilingual_depth_pending.html。</p>
{"".join(MODEL_HTML)}
{"".join(TABLE_HTML)}
{skip_html}
<script>
const tabs=[...document.querySelectorAll('.tabs button')];
function show(tag){{
  tabs.forEach(b=>b.classList.toggle('on',b.dataset.tag===tag));
  document.querySelectorAll('section.model').forEach(s=>
    s.hidden=(s.id!=='m_'+tag));
  document.querySelectorAll('.tables').forEach(t=>
    t.hidden=(t.id!=='t_'+tag));
  window.scrollTo({{top:0}});
}}
tabs.forEach(b=>b.onclick=()=>show(b.dataset.tag));
show(tabs[0].dataset.tag);
const dbtns=[...document.querySelectorAll('.depths button')];
function setK(k){{
  document.body.dataset.k=k;
  dbtns.forEach(b=>b.classList.toggle('on',b.dataset.k===k));
  document.querySelectorAll('td[data-v5]').forEach(td=>
    td.textContent=td.getAttribute('data-v'+k));
  document.querySelectorAll('td[data-g5]').forEach(td=>{{
    td.textContent=td.getAttribute('data-g'+k);
    td.classList.toggle('hot',td.getAttribute('data-h'+k)==='1');
  }});
}}
dbtns.forEach(b=>b.onclick=()=>setK(b.dataset.k));
setK('5');
</script>
"""
open(OUT, "w", encoding="utf-8").write(doc)
print(f"wrote {OUT}  ({os.path.getsize(OUT)/1024:.0f} KB, {len(models)} models, "
      f"三分数深度可切换 1/5/10/100, 默认 5)")
print("models:", ", ".join(t for t, _, _ in models))
if skipped:
    print("skipped (single language only):", ", ".join(f"{t}[{h}]" for t, h in skipped))
