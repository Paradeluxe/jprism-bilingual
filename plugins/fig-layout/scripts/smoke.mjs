/**
 * Smoke test for the client half: load client.js with a stub module loader and
 * a stub Cordis context, then assert the sidebar registrations the plugin makes.
 * Run with: ELECTRON_RUN_AS_NODE=1 "<node>" scripts/smoke.mjs
 */
import assert from 'node:assert/strict'
import { pathToFileURL } from 'node:url'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const clientPath = path.join(here, '..', 'client.js')

const registrations = []
let factory = null

globalThis.window = {
  __ModuleLoader__: {
    load({ id, factory: make }) {
      factory = make
    },
  },
}

await import(pathToFileURL(clientPath).href)
assert.ok(factory, 'client.js must register a lazy factory')

const React = {
  createElement: (type, props, ...children) => ({ type, props, children }),
  Fragment: 'fragment',
  useState: value => [value, () => {}],
  useEffect: () => {},
  useRef: value => ({ current: value }),
  useCallback: fn => fn,
}

const disposers = []
const ctx = {
  locale: {
    bind: () => key => key,
    register: () => () => {},
  },
  slots: {
    inject: (_name, make) => make(),
    register: (options) => {
      registrations.push(options)
      return () => {}
    },
  },
  sidebarRightTabs: {
    register: (definition) => {
      registrations.push({ tabType: definition })
      return () => {}
    },
  },
  sidebarRight: {
    mounted: { getSnapshot: () => 'session-1', subscribe: () => () => {} },
    openTabs: { getSnapshot: () => [] },
    openTab: () => {},
    closeIn: () => {},
  },
  effect: (fn) => {
    const dispose = fn()
    if (typeof dispose === 'function') disposers.push(dispose)
  },
}

const plugin = factory(name => {
  if (name === 'react') return React
  throw new Error('unexpected require: ' + name)
})

assert.equal(plugin.name, '@local/dsh-fig-layout')
assert.deepEqual(plugin.inject.slice(0, 3), ['slots', 'locale', 'sidebarRight'])
plugin.apply(ctx)

const tabType = registrations.find(entry => entry.tabType)
assert.ok(tabType, 'must register a sidebar tab type')
assert.equal(tabType.tabType.kind, 'fig-layout')
assert.equal(tabType.tabType.guide.length, 1)
assert.ok(registrations.some(entry => entry.name === 'sidebar.right.pane.tab'))
assert.ok(registrations.some(entry => entry.name === 'sidebar.right.pane.tab.title'))

// The body must be a component factory, not a rendered element.
const body = registrations.find(entry => entry.name === 'sidebar.right.pane.tab')
assert.equal(typeof body, 'object')
assert.ok(factory, 'factory stays synchronous')

assert.equal(disposers.length >= 4, true, 'every effect must return a disposer')
console.log(JSON.stringify({
  ok: true,
  registrations: registrations.map(entry => entry.name || ('tabType:' + entry.tabType.kind)),
  disposers: disposers.length,
}, null, 2))
