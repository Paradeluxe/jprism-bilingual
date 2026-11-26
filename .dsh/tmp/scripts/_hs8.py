import time

url = "https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1553708/full"
tid = new_tab(url)
time.sleep(4)
expr = r"""JSON.stringify((()=>{const t=(document.body.innerText||'').replace(/\s+/g,' ');const out=[];let i=0;while((i=t.indexOf('simple two-way',i))>=0&&out.length<4){out.push(t.slice(Math.max(0,i-500),i+900));i+=15;}return {len:t.length,out};})())"""
print(js(expr, target_id=tid))
