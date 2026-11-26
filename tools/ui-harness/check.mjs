/**
 * Render the sidebar editor in jsdom against a mocked Host, then drive the real
 * interaction: a gap is clicked, the controls narrow to that spacing's tokens,
 * an edit is applied, and the request body is checked.
 */
import assert from 'node:assert/strict'
import { JSDOM } from 'jsdom'
import { pathToFileURL } from 'node:url'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const clientPath = path.join(here, '..', '..', 'plugins', 'fig-layout', 'client.js')

const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', {
  url: 'http://127.0.0.1:60647/',
  pretendToBeVisual: true,
})
globalThis.window = dom.window
globalThis.document = dom.window.document
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true })
globalThis.HTMLElement = dom.window.HTMLElement
globalThis.Event = dom.window.Event
globalThis.Node = dom.window.Node

const baseState = {
  figure: 'fig1',
  label: 'Figure 1 - composition plate',
  source: 'experiment/figures/make_family_grids.py',
  tokens: { PH: 102, LENS_GAP: 32, CELLGAP: 64, MGAP: 48, TITLE_GAP: 24, MX: 64, PAD: 96 },
  png: 'figures/fig1_merged_grid_print.png',
  pngExists: true,
  image: { width: 3478, height: 6749, printWidthCmAt22_1: 11.39 },
  stale: false,
}
const audit = { image: { width: 3478, height: 6749 }, marginPx: { top: 96, right: 96, bottom: 96, left: 96 } }
const layout = {
  image: { width: 3478, height: 6749 },
  zones: [
    { kind: 'family-title', label: 'Family title to rule', tokens: ['TITLE_GAP'], box: [323, 86, 1481, 100] },
    { kind: 'panel-gap', label: 'Between checkpoints', tokens: ['MGAP'], box: [639, 386, 96, 2668] },
    { kind: 'lens-gap', label: 'Between lens rows', tokens: ['LENS_GAP', 'PH'], box: [451, 590, 316, 64] },
    { kind: 'legend', label: 'Legend block', tokens: ['LEGEND_GAP', 'TAILPAD'], box: [0, 6500, 3478, 249] },
  ],
}

const QUICK_FAIL = process.env.QUICK_FAIL === '1'
const requests = []
globalThis.fetch = async (url, options = {}) => {
  const body = options.body ? JSON.parse(options.body) : null
  const address = String(url)
  requests.push({ url: address, method: options.method || 'GET', body })
  let payload = {}
  if (address.includes('/state')) payload = baseState
  else if (address.includes('/layout')) payload = layout
  else if (address.includes('/quick')) {
    if (QUICK_FAIL) return { ok: false, status: 500, json: async () => ({ error: 'quick unavailable' }) }
    payload = { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>', zones: layout.zones, W: 10, H: 10 }
  }
  else if (address.includes('/audit')) payload = audit
  else if (address.includes('/apply')) {
    const tokens = { ...baseState.tokens, ...(body && body.tokens) }
    payload = { ok: true, changed: [{ token: 'MGAP', from: 48, to: 56 }], rendered: true, state: { ...baseState, tokens } }
  } else if (address.includes('/render')) payload = { ok: true, state: baseState }
  return { ok: true, status: 200, json: async () => payload }
}

let factory = null
globalThis.window.__ModuleLoader__ = {
  load({ id, factory: make }) { factory = make },
}
await import(pathToFileURL(clientPath).href + '?t=' + Date.now())
assert.ok(factory, 'client factory registered')

const React = (await import('react')).default
const { createRoot } = await import('react-dom/client')

const registrations = []
const ctx = {
  locale: { bind: () => key => key, register: () => () => {} },
  slots: {
    inject: (_name, make) => make(),
    register: (options, component) => {
      registrations.push({ options, component })
      return () => {}
    },
  },
  sidebarRightTabs: { register: definition => { registrations.push({ definition }); return () => {} } },
  sidebarRight: {
    mounted: { getSnapshot: () => 'session-preview', subscribe: () => () => {} },
    openTabs: { getSnapshot: () => [] },
    openTab: () => {},
    closeIn: () => {},
  },
  effect: fn => { fn() },
}
const plugin = factory(name => {
  if (name === 'react') return React
  throw new Error('unexpected require: ' + name)
})
plugin.apply(ctx)

const body = registrations.find(entry => entry.options && entry.options.name === 'sidebar.right.pane.tab')
assert.ok(body, 'tab body registered')

const T = {
  'figure.label': 'Plate', 'figure.fig1': 'Figure 1', 'figure.fig2': 'Figure 2',
  'status.saved': 'Saved', 'status.edited': 'edited', 'status.applied': 'Applied', 'status.rendered': 'Rendered',
  'meta.size': 'Size', 'meta.print': 'Print', 'meta.printValue': '22.1 cm high \u2192 {width} cm',
  'meta.margins': 'Margins', 'meta.unit': 'px', 'meta.open': 'Open PNG',
  'group.page': 'Page margins and labels', 'group.panels': 'Panels and rows',
  'group.unit': 'canvas units, 4-unit grid',
  'action.apply': 'Apply', 'action.render': 'Re-render', 'action.reset': 'Reset', 'action.all': 'All tokens',
  'hint.pick': 'Click a gap in the plate to filter the controls',
  'kind.family-title': 'Family title', 'kind.checkpoint-title': 'Checkpoint titles',
  'kind.label-column': 'Label columns', 'kind.panel-gap': 'Checkpoint gaps',
  'kind.prompt-gap': 'Prompt-group gaps', 'kind.lens-gap': 'Lens gaps', 'kind.axis': 'Tick rows',
  'kind.family-gap': 'Space between families', 'kind.row-gap': 'Row gaps',
  'kind.page-margin': 'Page edge', 'kind.legend': 'Legend block',
  'kind.places': 'places', 'kind.tokens': 'tokens', 'kind.token': 'token',
  'status.loading': 'Reading plate', 'status.offline': 'Service on 8829 is not running',
  'error.prefix': 'Failed',
}

const container = dom.window.document.getElementById('root')
const root = createRoot(container)
root.render(React.createElement(body.component, { t: key => T[key] ?? key }))

const wait = ms => new Promise(resolve => setTimeout(resolve, ms))
await wait(450)

assert.match(container.textContent, /Margins/, 'measured margins render')
if (QUICK_FAIL) {
  assert.ok(container.querySelector('img[alt]'), 'static preview renders when /quick is unavailable')
  assert.equal(container.querySelector('[role="img"] svg'), null, 'no SVG in the fallback')
} else {
  assert.ok(container.querySelector('[role="img"] svg'), 'live SVG preview renders')
}
const zoneButton = [...container.querySelectorAll('.fig-zone')].find(zone => zone.title === 'Checkpoint gaps')
assert.ok(zoneButton, 'zone buttons render over the plate')

// Click the panel gap: every panel gap is selected and the controls narrow to MGAP.
zoneButton.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true }))
await wait(80)
assert.ok(container.textContent.includes('Checkpoint gaps'), 'selected kind is named')
assert.ok(container.querySelector('input[aria-label="MGAP value"]'), 'MGAP row survives the filter')
assert.equal(container.querySelector('input[aria-label="PH value"]'), null, 'unrelated tokens are hidden')
assert.match(container.textContent, /places/, 'zone count is reported')

// Back to every token.
const allButton = [...container.querySelectorAll('button')].find(button => /All tokens/.test(button.textContent))
assert.ok(allButton, 'All tokens control exists')
allButton.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true }))
await wait(60)
assert.ok(container.querySelector('input[aria-label="MGAP value"]'), 'gap rows return')
assert.equal(container.querySelector('input[aria-label="PH value"]'), null, 'content tokens stay hidden')

// Edit MGAP and apply.
const valueInput = container.querySelector('input[aria-label="MGAP value"]')
const setValue = Object.getOwnPropertyDescriptor(dom.window.HTMLInputElement.prototype, 'value').set
setValue.call(valueInput, '56')
valueInput.dispatchEvent(new dom.window.Event('input', { bubbles: true }))
await wait(60)

const applyButton = [...container.querySelectorAll('button')].find(button => /^Apply$/.test(button.textContent.trim()))
assert.ok(applyButton, 'apply button exists')
assert.equal(applyButton.disabled, false, 'apply enables after an edit')
applyButton.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true }))
await wait(150)

const applyRequest = requests.find(request => request.url.includes('/apply'))
assert.ok(applyRequest, 'apply reached the Host')
assert.deepEqual(applyRequest.body.tokens, { MGAP: 56 })
assert.match(container.textContent, /Applied/, 'apply result is reported')

console.log(JSON.stringify({
  ok: true,
  requests: requests.map(request => request.method + ' ' + request.url.replace('http://127.0.0.1:8829', '')),
  appliedTokens: applyRequest.body.tokens,
  filteredTo: ['MGAP'],
}, null, 2))
root.unmount()
