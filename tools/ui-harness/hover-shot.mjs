/**
 * Hover a gap in a real browser and screenshot the result.
 * Usage: node hover-shot.mjs <cdp-port> <out.png>
 */
const port = process.argv[2] || '9333'
const out = process.argv[3] || 'hover.png'
const fs = await import('node:fs')

const targets = await (await fetch('http://127.0.0.1:' + port + '/json/list')).json()
const page = targets.find(t => t.type === 'page' && t.url.includes('live-wide.html'))
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
await new Promise(resolve => setTimeout(resolve, 2500))

const result = await send('Runtime.evaluate', {
  expression: `(() => {
    const zones = [...document.querySelectorAll('.fig-zone')]
    const zone = zones.find(z => z.getAttribute('aria-label') === 'Checkpoint gaps')
    if (!zone) return null
    const rect = zone.getBoundingClientRect()
    return { x: rect.left + rect.width / 2, y: rect.top + Math.min(rect.height / 2, 260), w: rect.width, h: rect.height }
  })()`,
  returnByValue: true,
})
const point = result.result.value
if (!point) throw new Error('no gap zone found')

await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: point.x, y: point.y })
await new Promise(resolve => setTimeout(resolve, 350))

const shot = await send('Page.captureScreenshot', { format: 'png' })
fs.writeFileSync(out, Buffer.from(shot.data, 'base64'))
console.log(JSON.stringify({ ok: true, point, out }))
ws.close()
