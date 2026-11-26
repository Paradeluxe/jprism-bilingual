// Throwaway verification of the brief-mode projection fold (not part of the bundle).
import { briefModeProjection as unit } from 'file:///E:/hermes_playground/jspace-repo/plugins/brief-mode/index.js'

const viewOf = state => unit.wire.view(state)

const assert = (condition, message) => {
  if (!condition) throw new Error('FAIL: ' + message)
  console.log('ok  ' + message)
}

const run = (commandId, args) => ({ type: 'command/run', data: { commandId, name: 'brief', args } })
const done = (commandId, kind) => ({ type: 'command/done', data: { commandId, kind, text: '' } })
const other = { type: 'user/message', data: {} }

let state = unit.init({}, 0)
assert(state.on === false && viewOf(state).on === false, 'a fresh Session starts off')

const before = state
state = unit.apply(state, other)
assert(state === before, 'an unrelated event returns the same state reference')

state = unit.apply(state, run('c1', ''))
assert(state.on === false && state.running.next === true, 'a bare /brief records the intent to toggle on')
state = unit.apply(state, done('c1', 'success'))
assert(state.on === true && viewOf(state).on === true, '/brief commits on after its paired done')

const onView = viewOf(state)
state = unit.apply(state, run('c2', ' on\n'))
assert(state === unit.apply(state, run('c3', 'on')), 'repeating the current state records no intent')
assert(viewOf(state) === onView, 'an unchanged switch keeps the view reference (no frame)')
state = unit.apply(state, done('c2', 'success'))
assert(state.on === true, 'a failed or dropped intent cannot flip the switch')

state = unit.apply(state, run('c4', 'off'))
state = unit.apply(state, done('c4', 'error'))
assert(state.on === true && state.running === null, 'an errored invocation leaves the switch untouched')

state = unit.apply(state, run('c5', 'off'))
state = unit.apply(state, done('c5', 'success'))
assert(state.on === false, '/brief off commits off')

state = unit.apply(state, run('c6', 'maybe'))
assert(state.running === null, 'an unknown verb records nothing; the handler reports the usage error')

const beforeOther = state
state = unit.apply(state, { type: 'command/run', data: { commandId: 'x', name: 'plan', args: 'off' } })
assert(state === beforeOther, 'another command name is ignored')

assert(unit.key === 'briefMode' && unit.stateVersion === 1, 'the projection identity is stable')
assert(unit.wire.summary === undefined, 'the switch stays in Session summaries')

// Two invocations before the first settles must not fight: both read the
// pending-aware state, so the second one wins and the first one's done is stale.
let raced = unit.apply(unit.init({}, 0), run('a1', 'on'))
assert(raced.running.next === true, 'the first invocation records its intent')
raced = unit.apply(raced, run('a2', 'off'))
assert(raced.running.commandId === 'a2' && raced.running.next === false, 'a later opposite invocation replaces the pending intent')
raced = unit.apply(raced, done('a1', 'success'))
assert(raced.on === false && raced.running.commandId === 'a2', 'the superseded invocation cannot commit')
raced = unit.apply(raced, done('a2', 'success'))
assert(raced.on === false && raced.running === null, 'the surviving invocation commits off')

let agreed = unit.apply(unit.init({}, 0), run('b1', 'on'))
agreed = unit.apply(agreed, run('b2', 'on'))
assert(agreed.running.commandId === 'b1', 'a repeat of the pending target keeps the original intent')
agreed = unit.apply(agreed, done('b1', 'success'))
assert(agreed.on === true, 'the original invocation still commits on')
console.log('\nall projection checks passed')
