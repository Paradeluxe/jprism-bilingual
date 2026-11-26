// Throwaway verification of the brief-mode Host half against a mock Cordis context.
import { apply, inject, CONTEXT_KIND, OFF_TEXT, DEFAULT_INSTRUCTION } from 'file:///E:/hermes_playground/jspace-repo/plugins/brief-mode/index.js'

const assert = (condition, message) => {
  if (!condition) throw new Error('FAIL: ' + message)
  console.log('ok  ' + message)
}

const registrations = []
const commands = []
const listeners = {}
const appends = []

let switchOn = false
let seq = 0
const log = new Map()
const nodes = []

const session = {
  get surface () { return { nodes } },
  eventAt: at => log.get(at),
  append: (type, data, opts) => {
    const event = { type, seq: seq++, data }
    log.set(event.seq, event)
    appends.push({ type, data, opts, seq: event.seq })
    if (opts !== undefined && opts.surfaceOp === 'append') nodes.push(event.seq)
    else if (opts !== undefined && typeof opts.surfaceOp === 'object') {
      const index = nodes.indexOf(opts.surfaceOp.startSeq)
      if (index === -1) throw new Error('replace target is not in the surface')
      nodes[index] = event.seq
    }
    return event
  },
}
const fakeAgent = { session }

const ctx = {
  logger: { error: (...args) => console.error('[logger]', ...args), warn: (...args) => console.error('[warn]', ...args) },
  sessionProjections: {
    register: (definition) => {
      registrations.push(definition)
      const handle = { stateOf: () => ({ on: switchOn, running: null }) }
      const dispose = () => Promise.resolve()
      return Object.assign(dispose, { then: (onOk, onErr) => Promise.resolve(handle).then(onOk, onErr) })
    },
  },
  on: (event, handler, options) => { listeners[event] = { handler, options }; return () => {} },
  inject: (deps, callback) => {
    assert(Array.isArray(deps) && deps[0] === 'commands', 'the command registry is optional (ctx.inject)')
    callback({ commands: { register: (definition) => { commands.push(definition); return () => {} } } })
  },
}

apply(ctx, { instruction: DEFAULT_INSTRUCTION })
await new Promise(resolve => setTimeout(resolve, 0))

assert(JSON.stringify(inject) === '["sessionProjections"]', 'it needs the projection registry only')
assert(registrations.length === 1 && registrations[0].key === 'briefMode', 'one briefMode projection is registered')
assert(ctx.systemPrompt === undefined, 'it does not register a system-prompt contribution')
assert(commands.length === 1 && commands[0].name === 'brief', 'the /brief command is registered')

const entry = listeners['agent/pre-step']
assert(entry !== undefined && entry.options.prepend === true, 'it prepends an agent/pre-step listener')

const decision = Object.freeze({ kind: 'accept', messages: [], startsRequestSeries: false })
const next = async () => decision
const step = () => entry.handler({ agent: fakeAgent, turn: 1, step: 1, signal: { aborted: false } }, next)

let out = await step()
assert(appends.length === 0, 'an off switch writes no row')

switchOn = true
out = await step()
assert(out === decision, 'the decision is returned untouched: the row rides the surface, not the message list')
assert(appends.length === 1, 'turning the switch on appends exactly one row')
const first = appends[0]
assert(first.type === 'user/message', 'the row is an ordinary user message (the context row renders it)')
assert(first.opts.surfaceOp === 'append', 'the first row enters the surface as an append')
assert(first.data.role === 'user', 'it is a user-role context message')
assert(first.data.source.kind === CONTEXT_KIND, 'its source kind is the row label (brief-mode)')
assert(first.data.source.form === 'snapshot', 'it declares snapshot form, which supersedes an earlier snapshot')
assert(first.data.source.sections[0].text === DEFAULT_INSTRUCTION, 'the section carries the instruction')
assert(first.data.content[0].text === DEFAULT_INSTRUCTION, 'the model-facing text is the instruction')
assert(nodes.length === 1, 'the session surface holds one row')

out = await step()
assert(appends.length === 1, 'an unchanged state writes nothing on the next step')

switchOn = false
out = await step()
assert(appends.length === 2, 'turning the switch off rewrites the row')
const second = appends[1]
assert(typeof second.opts.surfaceOp === 'object' && second.opts.surfaceOp.op === 'replace', 'it replaces the previous row instead of appending')
assert(second.opts.surfaceOp.startSeq === first.seq && second.opts.surfaceOp.endSeq === first.seq, 'the replacement targets exactly the old row')
assert(JSON.stringify(second.opts.sourceEventSeqs) === JSON.stringify([first.seq]), 'the replaced event is cited')
assert(second.data.content[0].text === OFF_TEXT, 'the off text tells the model to stop applying it')
assert(nodes.length === 1, 'the transcript still holds exactly one row')
assert(nodes[0] === second.seq, 'the surface now points at the new row')

out = await step()
assert(appends.length === 2, 'the off state is not rewritten again')

switchOn = true
out = await step()
assert(appends.length === 3 && appends[2].opts.surfaceOp.op === 'replace', 'turning it back on replaces the same row')
assert(nodes.length === 1 && log.get(nodes[0]).data.content[0].text === DEFAULT_INSTRUCTION, 'the single row carries the instruction again')

assert(commands[0].input.hint === '[on|off]', 'the command advertises its verbs')
switchOn = false
assert(commands[0].handler({ agent: fakeAgent, rawInput: '' }).text.includes('已开启'), 'a bare /brief predicts turning on')
assert(commands[0].handler({ agent: fakeAgent, rawInput: ' OFF ' }).text.includes('已关闭'), 'verb matching is case- and space-insensitive')
const usage = commands[0].handler({ agent: fakeAgent, rawInput: 'maybe' })
assert(usage.kind === 'error' && usage.text.startsWith('用法'), 'an unknown verb reports usage instead of switching')
switchOn = true
assert(commands[0].handler({ agent: fakeAgent, rawInput: 'on' }).text.includes('已开启'), '/brief on reports the wanted state')
assert(commands[0].handler({ agent: fakeAgent, rawInput: '' }).text.includes('已关闭'), 'a bare /brief toggles from on to off')

console.log('\nall host checks passed')
