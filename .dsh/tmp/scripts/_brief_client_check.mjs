// Throwaway verification of the brief-mode browser half: module shape, slot
// registration, the injected toggle, and the rendered control's attributes.
import { readFileSync } from 'node:fs'

const assert = (condition, message) => {
  if (!condition) throw new Error('FAIL: ' + message)
  console.log('ok  ' + message)
}

// --- minimal React stand-in -------------------------------------------------
const Fragment = Symbol('Fragment')
const callComponent = (type, props) => type(props)
const React = {
  Fragment,
  createElement: (type, props, ...children) => (
    typeof type === 'function' && type !== Fragment
      ? callComponent(type, props ?? {})
      : { type, props: props ?? {}, children: children.flat() }
  ),
  useState: (initial) => [typeof initial === 'function' ? initial() : initial, () => {}],
  useRef: (initial) => ({ current: initial }),
  useEffect: () => {},
}

// --- load the browser module through its own loader hook --------------------
let loaded
const source = readFileSync('E:/hermes_playground/jspace-repo/plugins/brief-mode/client.js', 'utf8')
new Function('window', 'require', source)(
  { __ModuleLoader__: { load: (definition) => { loaded = definition } } },
  (specifier) => { if (specifier !== 'react') throw new Error('unexpected require: ' + specifier); return React },
)
assert(loaded !== undefined, 'the module registers itself with the page module loader')
assert(loaded.id === '@local/dsh-brief-mode', 'the module id equals the bundle package name (it must match)')

// --- plugin shape and registrations ----------------------------------------
const plugin = loaded.factory((specifier) => React)
assert(typeof plugin.apply === 'function', 'the factory returns a plugin with apply()')
assert(plugin.inject.includes('slots') && plugin.inject.includes('remote.commands'), 'it injects slots and the commands remote')

const registered = []
const localeCalls = []
const executed = []
const mockCtx = {
  effect: (factory) => { factory(); return () => {} },
  locale: { register: (...args) => { localeCalls.push(args); return () => {} } },
  slots: {
    inject: (key, callback) => {
      assert(key === 'conversation.input.left', 'it injects the composer tool-row slot')
      callback()
      return () => {}
    },
    register: (options, component) => { registered.push({ options, component }); return () => {} },
  },
  remote: { commands: { execute: async (...args) => { executed.push(args); return { ok: true, value: { commandId: 'c1', result: { kind: 'success' } } } } } },
}
plugin.apply(mockCtx)

assert(localeCalls.length === 1 && localeCalls[0][0] === 'briefMode', 'it registers one locale namespace')
assert(localeCalls[0][1].zh['chip.label'] === '简短回答' && localeCalls[0][1].en['chip.label'] === 'Brief replies', 'both dictionaries are complete')

assert(registered.length === 1, 'it contributes exactly one tool-row switch')
const { options, component } = registered[0]
assert(options.name === 'conversation.input.left' && options.id === 'brief-mode', 'the entry names the tool-row slot and a stable id')
assert(options.locale === 'briefMode', 'the component resolves copy from the plugin namespace')
assert(typeof options.inject === 'function', 'the entry injects a session-scoped face')

const face = options.inject('session-1')
assert(typeof face.toggleBrief === 'function', 'the injected face exposes toggleBrief')

// --- the injected toggle drives the command ---------------------------------
const failureOnSuccess = await face.toggleBrief(true)
assert(failureOnSuccess === null, 'a successful toggle reports no failure')
assert(executed[0][0] === 'session-1' && executed[0][1] === '/brief on' && Array.isArray(executed[0][2]), 'it runs /brief on against that Session')
await face.toggleBrief(false)
assert(executed[1][1] === '/brief off', 'it runs /brief off when switching the other way')

const errorCtx = { ...mockCtx, remote: { commands: { execute: async () => ({ ok: true, value: { commandId: 'c2', result: { kind: 'error', text: 'boom' } } }) } } }
const errorRegistered = []
errorCtx.slots = { ...mockCtx.slots, register: (opts) => { if (typeof opts.inject === 'function') errorRegistered.push(opts.inject('s').toggleBrief); return () => {} } }
plugin.apply(errorCtx)
assert(await errorRegistered[0](true) === 'boom', 'a handler error surfaces as the failure line')

const missingCtx = { ...mockCtx, remote: { commands: { execute: async () => ({ ok: true, value: undefined }) } } }
const missingRegistered = []
missingCtx.slots = { ...mockCtx.slots, register: (opts) => { typeof opts.inject === 'function' ? missingRegistered.push(opts.inject('s').toggleBrief) : undefined; return () => {} } }
plugin.apply(missingCtx)
assert((await missingRegistered[0](true)).includes('not a registered command'), 'an unregistered command surfaces as a failure line')

const rejectedCtx = { ...mockCtx, remote: { commands: { execute: async () => ({ ok: false, error: { message: 'nope', code: 'E_DENIED' } }) } } }
const rejectedRegistered = []
rejectedCtx.slots = { ...mockCtx.slots, register: (opts) => { typeof opts.inject === 'function' ? rejectedRegistered.push(opts.inject('s').toggleBrief) : undefined; return () => {} } }
plugin.apply(rejectedCtx)
assert((await rejectedRegistered[0](true)).includes('E_DENIED'), 'a rejected remote call surfaces its code')

// --- the rendered control ---------------------------------------------------
const find = (node, type) => {
  if (node === null || node === undefined || typeof node !== 'object') return undefined
  if (node.type === type) return node
  for (const child of node.children ?? []) {
    const hit = find(child, type)
    if (hit !== undefined) return hit
  }
  return undefined
}
const t = (key, params) => (params === undefined ? key : key + JSON.stringify(params))
const off = component({ useProjection: () => ({ on: false }), t, toggleBrief: async () => null })
const button = find(off, 'button')
assert(button !== undefined, 'the control renders a real button element')
assert(button.props.type === 'button' && button.props['aria-pressed'] === false, 'it is a real off button with aria-pressed=false')
assert(button.props.disabled === undefined, 'it stays focusable: pending is not expressed by disabling')
assert(button.props['aria-busy'] === undefined, 'an idle control is not announced as busy')
assert(button.props.title.startsWith('chip.title.off'), 'the tooltip explains the off state')
assert(String(button.props['aria-label']).startsWith('chip.aria'), 'the accessible name states the current state')
assert(button.props['data-state'] === 'off', 'the off state carries its own state marker')
assert(typeof button.props.onMouseDown === 'function', 'pressing the tool keeps the draft focused')
const prevented = []
button.props.onMouseDown({ preventDefault: () => prevented.push(true) })
assert(prevented.length === 1, 'the mouse-down default is suppressed so the caret stays in the composer')
const style = find(off, 'style')
assert(style !== undefined && style.children.join('').includes('--dsw-alias-'), 'the component ships its own token-based styles')
const glyph = find(off, 'svg')
assert(glyph !== undefined, 'the control carries a line glyph like its neighbours')
assert(glyph.props.width === 14 && glyph.props.height === 14 && glyph.props.strokeWidth === 1.5, 'the glyph is 14px at 1.5 stroke')
assert(glyph.props.stroke === 'currentColor', 'the glyph takes its color from the control state')
assert(glyph.children.length === 2, 'the glyph is a frame plus one short line')
const findByClass = (node, name) => {
  if (node === null || node === undefined || typeof node !== 'object') return undefined
  if (node.props !== undefined && node.props.className === name) return node
  for (const child of node.children ?? []) {
    const hit = findByClass(child, name)
    if (hit !== undefined) return hit
  }
  return undefined
}
const labelSpan = findByClass(off, 'dshb-label')
assert(labelSpan !== undefined && labelSpan.children[0] === 'chip.label', 'the visible label is one word, with no state suffix in the row')

const on = component({ useProjection: () => ({ on: true }), t, toggleBrief: async () => null })
const onButton = find(on, 'button')
assert(onButton.props['data-state'] === 'on' && onButton.props['aria-pressed'] === true, 'the on state is announced and marked for styling')
assert(onButton.props.title.startsWith('chip.title.on'), 'the tooltip explains the on state')

const unknown = component({ useProjection: () => undefined, t, toggleBrief: async () => null })
assert(find(unknown, 'button').props['aria-pressed'] === false, 'an absent projection falls back to off instead of hiding the control')
assert(find(unknown, 'button').props['data-state'] === 'unread', 'an absent projection renders the third, unread marker')
assert(find(unknown, 'button').props['aria-label'] === 'chip.aria.unknown', 'an absent projection says the state was not read, not that it is off')
assert(find(unknown, 'button').props.title === 'chip.title.unknown', 'the unread tooltip does not claim the switch is off')

const zhKeys = Object.keys(localeCalls[0][1].zh).sort()
const enKeys = Object.keys(localeCalls[0][1].en).sort()
assert(JSON.stringify(zhKeys) === JSON.stringify(enKeys), 'the two dictionaries carry the same keys')
for (const key of ['chip.aria', 'chip.aria.unknown', 'chip.title.on', 'chip.title.off', 'chip.title.unknown', 'chip.busy']) {
  assert(zhKeys.includes(key), 'locale defines ' + key)
}

console.log('\nall browser-half checks passed')
