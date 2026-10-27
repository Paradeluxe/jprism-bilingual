"""bilingual_top5_html.py — build a browsable side-by-side per-layer top-5 comparison from the
EN and ZH measurement raws of the same model. Standalone HTML, no server-side deps, no CDN:
open the file locally or serve the folder. Reads the raw JSONs written by measure_sicc.py.
"""
import html
import json
import os
import sys

en_path, zh_path = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else "bilingual_top5.html"

en = json.load(open(en_path, encoding="utf-8"))
zh = json.load(open(zh_path, encoding="utf-8"))
en_res = {r["key"]: r for r in en["results"] if r.get("pos") in (-1, None)}
zh_res = {r["key"]: r for r in zh["results"] if r.get("pos") in (-1, None)}

keys = [k for k in en_res if k in zh_res]
ea, za = en["aggregate"], zh["aggregate"]

# per-layer hit@5 across all prompts, for the strip charts. The per-prompt records live under
# results[].layers; the top-level "layers" key is just a flat list of layer indices, so this
# must walk results, not the top-level key (which raises 'int has no attribute get').
def hitmap(doc):
    m = {}
    for r in doc["results"]:
        if r.get("pos") not in (-1, None):
            continue
        for lay in r.get("layers") or []:
            if lay.get("j_hit5"):
                m[lay["layer"]] = m.get(lay["layer"], 0) + 1
    return m


rows_html = []
for k in keys:
    er, zr = en_res[k], zh_res[k]
    targets = [t.lower() for t in er["targets"]]
    zmap = {l["layer"]: l for l in zr["layers"]}
    body = []
    q = er.get("prompt", "")
    for lay in er["layers"]:
        z = zmap.get(lay["layer"])
        if z is None:
            continue
        en_hit = any(t in [w.lower() for w, _ in (lay.get("j_top5") or [])] for t in targets)
        zh_hit = any(t in [w.lower() for w, _ in (z.get("j_top5") or [])] for t in targets)

        def cell(tl):
            out_ = []
            for w, s in (tl.get("j_top5") or []):
                cls = ""
                if w.lower() in targets:
                    cls = " tgt" if (tl.get("j_hit5") or tl.get("j_hit10")) else " tgt-out"
                out_.append(f'<span class="tok{cls}">{html.escape(w)}<i>{s:g}</i></span>')
            return "".join(out_) or '<span class="tok none">—</span>'

        body.append(
            f'<tr class="{"hit" if (en_hit or zh_hit) else ""}">'
            f'<td class="lay">{lay["layer"]}'
            f'{" EN" if en_hit else ""}{" ZH" if zh_hit else ""}</td>'
            f'<td class="rank">{lay.get("j_rank") if lay.get("j_rank") is not None else "—"}</td>'
            f'<td>{cell(lay)}</td>'
            f'<td class="rank">{z.get("j_rank") if z.get("j_rank") is not None else "—"}</td>'
            f'<td>{cell(z)}</td></tr>')
    mt = ", ".join(f"`{w}`" for w, _ in (er.get("model_top5") or []))
    rows_html.append(
        f'<section><h2>{html.escape(k)} <small>model rank {er["model_rank"]}</small></h2>'
        f'<div class="q"><span class="qlab">probe</span>'
        f'<code>{html.escape(q)}</code></div>'
        f'<div class="q"><span class="qlab">answer</span>'
        f'<code class="ans">{html.escape(", ".join(er["targets"]))}</code>'
        f'<span class="qlab ml">model top-5</span><code>{mt}</code></div>'
        f'<table><thead><tr><th>layer</th><th>EN rank</th><th>EN top-5</th>'
        f'<th>ZH rank</th><th>ZH top-5</th></tr></thead><tbody>{"".join(body)}</tbody></table>'
        f'</section>')

strips = []
for label, doc, agg in (("EN", en, ea), ("ZH", zh, za)):
    hm = hitmap(doc)
    layers = sorted(hm) or sorted({l["layer"] for r in doc["results"] for l in (r.get("layers") or [])})
    peak = max(hm.values()) if hm else 1
    bars = []
    for lay in layers:
        n = hm.get(lay, 0)
        h = max(3, round(15 * n / peak)) if n else 3
        bars.append(f'<i class="on{n}" style="height:{h}px" title="L{lay}: {n} hits"></i>')
    strips.append(
        f'<div class="strip"><b>{label}</b> Hit@5 {agg["j_hit5_rate_cells"]:.4f} '
        f'({agg["n_cells"]} cells) <span class="bar">{"".join(bars)}</span></div>')

quiz = []
for k in keys:
    r = en_res[k]
    quiz.append(
        f'<li><code>{html.escape(r.get("prompt", ""))}</code> → '
        f'<b>{html.escape(", ".join(r["targets"]))}</b>'
        f'<span class="mr">model rank {r["model_rank"]}</span></li>')

doc = f"""<!doctype html><html lang="zh"><meta charset="utf-8">
<title>{html.escape(en["tag"])} 中英逐层 top-5 对比</title>
<style>
 :root {{ --bd:#d8dee9; --mut:#6b7280; --en:#1f6feb; --zh:#c2410c; --tint:#fff8e6 }}
 * {{ box-sizing:border-box }}
 body {{ font:14px/1.5 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;
        margin:0; padding:24px 28px; color:#1f2328; background:#fff }}
 h1 {{ font-size:20px; margin:0 0 4px }}
 .sub {{ color:var(--mut); margin-bottom:16px; font-size:13px }}
 .strip {{ margin:6px 0; display:flex; align-items:center; gap:10px; font-size:12px }}
 .strip b {{ width:26px; color:var(--mut) }}
 .bar {{ display:inline-flex; gap:2px; align-items:flex-end; height:16px }}
 .bar i {{ width:7px; height:3px; background:#e5e7eb; border-radius:1px }}
 .bar i[class*="on"] {{ background:#86efac }}
 .bar i.on2 {{ background:#4ade80 }}
 .bar i.on3 {{ background:#22c55e }}
 .bar i.on4 {{ background:#15803d }}
 section {{ margin:26px 0 34px }}
 h2 {{ font-size:15px; margin:0 0 8px; font-weight:600 }}
 h2 small {{ font-weight:400; color:var(--mut); margin-left:8px; font-size:12px }}
 table {{ border-collapse:collapse; width:100%; table-layout:fixed }}
 th,td {{ border:1px solid var(--bd); padding:4px 8px; vertical-align:top; font-size:12.5px }}
 th {{ background:#f6f8fa; text-align:left; position:sticky; top:0 }}
 th:nth-child(1),th:nth-child(2),th:nth-child(4) {{ width:62px }}
 td.lay {{ background:#f6f8fa; font-weight:600; color:var(--en); text-align:center }}
 td.rank {{ text-align:center; color:var(--mut); font-variant-numeric:tabular-nums }}
 tr.hit td.lay {{ color:#15803d }}
 tr.hit {{ background:#f0fdf4 }}
 td:nth-child(3) {{ border-left:2px solid var(--en) }}
 td:nth-child(5) {{ border-left:2px solid var(--zh) }}
 .tok {{ display:inline-block; margin:1px 5px 1px 0; white-space:nowrap;
        font-family:"Cascadia Mono",Consolas,monospace; font-size:12px }}
 .tok i {{ color:var(--mut); font-style:normal; font-size:10.5px; margin-left:2px }}
 .tok.tgt {{ background:#dcfce7; border:1px solid #16a34a; border-radius:3px; padding:0 3px }}
 .tok.tgt-out {{ background:#fef3c7; border:1px dashed #d97706; border-radius:3px; padding:0 3px }}
 .tok.none {{ color:#bbb }}
 .q {{ margin:3px 0 7px; font-size:12.5px; display:flex; gap:8px; align-items:baseline;
       flex-wrap:wrap }}
 .q code {{ background:#f3f4f6; border:1px solid #e5e7eb; border-radius:3px;
            padding:1px 7px; font-family:"Cascadia Mono",Consolas,monospace }}
 .q code.ans {{ background:#dcfce7; border-color:#16a34a; font-weight:600 }}
 .qlab {{ color:var(--mut); font-size:11px; text-transform:uppercase; letter-spacing:.4px;
          min-width:44px }}
 .qlab.ml {{ margin-left:14px }}
 .quiz {{ margin:10px 0 14px; border:1px solid var(--bd); border-radius:5px;
         padding:8px 14px; background:#fcfcfd }}
 .quiz summary {{ cursor:pointer; font-size:12.5px; color:var(--mut);
                  font-weight:600; letter-spacing:.2px }}
 .quiz ol {{ margin:8px 0 2px; padding-left:22px }}
 .quiz li {{ margin:3px 0; font-size:12.5px }}
 .quiz code {{ background:#f3f4f6; border:1px solid #e5e7eb; border-radius:3px;
               padding:1px 6px; font-family:"Cascadia Mono",Consolas,monospace }}
 .quiz b {{ color:#15803d }}
 .mr {{ color:var(--mut); font-size:11px; margin-left:10px }}
 .legend {{ margin:10px 0 0; font-size:12px; color:var(--mut) }}
 .sw {{ display:inline-block; width:11px; height:11px; vertical-align:-1px;
       border-radius:2px; margin:0 4px 0 10px }}
</style>
<h1>{html.escape(en["tag"])} — 中英镜片逐层 top-5 对比</h1>
<div class="sub">同一模型、同一套四道英文题，唯一差别是镜片在哪种语言的语料上 fit。
model 自身能力两语相同（Hit@5 {ea["model_hit5_rate_prompts"]:.2f}），
所以差距只来自镜片。绿底行 = 至少一边命中 top-5。</div>
<details class="quiz" open><summary>四道探针题（英文，中英镜片用同一套）</summary>
<ol>{"".join(quiz)}</ol></details>
{"".join(strips)}
<p class="legend"><span class="sw" style="background:#dcfce7;border:1px solid #16a34a"></span>答案在 top-5
 <span class="sw" style="background:#fef3c7;border:1px dashed #d97706"></span>答案在 top-10 但不在 top-5
 左边蓝线=英文镜片，右边橙线=中文镜片。层号后的 EN/ZH 表示该层命中。</p>
{"".join(rows_html)}
"""
open(out, "w", encoding="utf-8").write(doc)
print(f"wrote {out}  ({os.path.getsize(out)/1024:.0f} KB, {len(keys)} prompts)")
