tid = current_tab()['target_id']
expr = r"""JSON.stringify((()=>{const as=[...document.querySelectorAll('h3.gs_rt a')];return as.slice(0,10).map(a=>({t:a.innerText,u:a.href}));})())"""
print(js(expr, target_id=tid))
