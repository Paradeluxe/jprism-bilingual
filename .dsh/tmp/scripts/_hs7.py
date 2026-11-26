import time

q = "%22simple+two-way+interactions%22+%22simple+main+effects%22+%22three-way+interaction%22"
url = "https://scholar.google.com/scholar?hl=en&q=" + q
tid = new_tab(url)
time.sleep(2)
expr = r"""JSON.stringify((()=>{const rows=[...document.querySelectorAll('div.gs_r.gs_or.gs_scl')];return rows.slice(0,10).map(r=>{const a=r.querySelector('h3.gs_rt a');const m=r.querySelector('div.gs_a');const s=r.querySelector('div.gs_rs');return {title:a?a.innerText:'',url:a?a.href:'',meta:m?m.innerText:'',snip:s?s.innerText.slice(0,320):''};});})())"""
print(js(expr, target_id=tid))
