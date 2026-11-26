/**
 * Accessibility + dark-mode probe against the live preview page.
 * Usage: node a11y-check.mjs <cdp-port> <dark-out.png>
 */
const port = process.argv[2] || '9334'
const out = process.argv[3] || 'dark.png'
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
await new Promise(resolve => setTimeout(resolve, 2600))

const probe = await send('Runtime.evaluate', {
  expression: `(() => {
    const zones = [...document.querySelectorAll('.fig-zone')]
    const chips = [...document.querySelectorAll('button[aria-pressed]')]
    const ranges = [...document.querySelectorAll('.fig-range')]
    return {
      zones: zones.length,
      zonesFocusable: zones.filter(z => z.tabIndex === 0).length,
      chips: chips.length,
      chipsPressed: chips.filter(c => c.getAttribute('aria-pressed') === 'true').length,
      ranges: ranges.length,
      valueText: ranges[0] && ranges[0].getAttribute('aria-valuetext'),
      headings: [...document.querySelectorAll('h1,h2,h3')].map(h => h.tagName + ':' + h.textContent.trim().slice(0, 24)),
      region: document.querySelector('[role="region"]') ? document.querySelector('[role="region"]').getAttribute('aria-label') : null,
    }
  })()`,
  returnByValue: true,
})
const info = probe.result.value

await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 })
await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab', windowsVirtualKeyCode: 9 })
await new Promise(resolve => setTimeout(resolve, 150))

const focus = await send('Runtime.evaluate', {
  expression: `(() => {
    const el = document.activeElement
    if (!el) return null
    const style = getComputedStyle(el)
    return { tag: el.tagName, label: el.getAttribute('aria-label') || el.textContent.trim().slice(0, 20), outline: style.outlineStyle + ' ' + style.outlineWidth + ' ' + style.outlineColor }
  })()`,
  returnByValue: true,
})
info.firstTabFocus = focus.result.value

await send('Emulation.setEmulatedMedia', {
  features: [{ name: 'prefers-color-scheme', value: 'dark' }],
})
await new Promise(resolve => setTimeout(resolve, 300))
const shot = await send('Page.captureScreenshot', { format: 'png' })
fs.writeFileSync(out, Buffer.from(shot.data, 'base64'))
console.log(JSON.stringify({ ok: true, info, out }, null, 2))
ws.close()
