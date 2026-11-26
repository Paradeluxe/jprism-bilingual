import json

url = "https://scholar.google.com/scholar?hl=en&q=%22decomposing+three-way+interactions%22"
tid = new_tab(url)
print("TAB", tid)
print(page_info())
expr = r"""JSON.stringify((()=>{const rows=[...document.querySelectorAll('div.gs_r.gs_or.gs_scl')];return rows.slice(0,10).map(r=>{const a=r.querySelector('h3.gs_rt a');const m=r.querySelector('div.gs_a');const s=r.querySelector('div.gs_rs');return {title:a?a.innerText:'',url:a?a.href:'',meta:m?m.innerText:'',snip:s?s.innerText.slice(0,280):''};});})())"""
print(js(expr, target_id=tid))
