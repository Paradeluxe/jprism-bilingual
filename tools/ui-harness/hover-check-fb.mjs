/**
 * Hover a gap and report what the browser thinks is under the pointer.
 * Usage: node hover-check.mjs <cdp-port> <out.png>
 */
const port = process.argv[2] || '9335'
const out = process.argv[3] || 'hover2.png'
const fs = await import('node:fs')

const targets = await (await fetch('http://127.0.0.1:' + port + '/json/list')).json()
const page = targets.find(t => t.type === 'page' && t.url.includes('live-fallback.html'))
if (!page) throw new Error('page target not found')

const ws = new WebSocket(page.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve, { once: true })
  ws.addEventListener('error', reject, { once: true })
})

let id = 0
const pending = new Map()
ws.addEventListener('message', event => {
  const message = JSON.parse(event.data)
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id)
    pending.delete(message.id)
    if (message.error) reject(new Error(message.error.message))
    else resolve(message.result)
  }
})
function send(method, params = {}) {
  const current = ++id
  return new Promise((resolve, reject) => {
    pending.set(current, { resolve, reject })
    ws.send(JSON.stringify({ id: current, method, params }))
  })
}

await send('Page.enable')
const waitForImage = async () => {
  for (let attempt = 0; attempt < 30; attempt += 1) {
    const ready = (await send('Runtime.evaluate', {
      expression: "(() => { const img = document.querySelector('img[alt]'); return !!img && img.complete && img.naturalWidth > 0 })()",
      returnByValue: true,
    })).result.value
    if (ready) return
    await new Promise(resolve => setTimeout(resolve, 500))
  }
}
await waitForImage()
await new Promise(resolve => setTimeout(resolve, 800))

const rect = (await send('Runtime.evaluate', {
  expression: `(() => {
    const zone = [...document.querySelectorAll('.fig-zone')].find(z => z.title === 'Checkpoint gaps')
    if (!zone) return null
    const r = zone.getBoundingClientRect()
    for (let y = r.top + 6; y < r.bottom - 6; y += 8) {
      const hit = document.elementFromPoint(r.left + r.width / 2, y)
      if (hit === zone || zone.contains(hit)) {
        return { x: r.left + r.width / 2, y, w: r.width, h: r.height }
      }
    }
    return null
  })()`,
  returnByValue: true,
})).result.value
if (!rect) throw new Error('no zone')

await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: rect.x, y: rect.y })
await new Promise(resolve => setTimeout(resolve, 350))

const info = (await send('Runtime.evaluate', {
  expression: `(() => {
    const zone = [...document.querySelectorAll('.fig-zone')].find(z => z.title === 'Checkpoint gaps')
    const hit = document.elementFromPoint(${rect.x}, ${rect.y})
    const style = getComputedStyle(zone)
    return {
      hoverMatch: zone.matches(':hover'),
      linked: document.querySelectorAll('.fig-zone.is-linked').length,
      selected: document.querySelectorAll('.fig-zone.is-selected').length,
      border: style.borderColor,
      background: style.backgroundColor,
      pointer: style.pointerEvents,
      hit: hit ? hit.tagName + '.' + hit.className + ':' + (hit.title || '') : null,
      pageHasFocus: document.hasFocus(),
    }
  })()`,
  returnByValue: true,
})).result.value

const shot = await send('Page.captureScreenshot', { format: 'png' })
fs.writeFileSync(out, Buffer.from(shot.data, 'base64'))
console.log(JSON.stringify({ ok: true, rect, info, out }, null, 2))
ws.close()
