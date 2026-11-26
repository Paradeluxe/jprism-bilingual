tid = current_tab()['target_id']
expr = r"""JSON.stringify({title:document.title, text:(document.body.innerText||'').replace(/\s+/g,' ').slice(0,1500)})"""
print(js(expr, target_id=tid))
