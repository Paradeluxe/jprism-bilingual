import json

tid = current_tab()
expr = r"""JSON.stringify({title:document.title, text:(document.body.innerText||'').replace(/\s+/g,' ').slice(0,1200)})"""
print(js(expr, target_id=tid))
