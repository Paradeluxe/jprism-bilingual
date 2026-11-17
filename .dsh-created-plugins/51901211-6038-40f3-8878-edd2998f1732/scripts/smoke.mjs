/**
 * Local build check for the jspace dashboard bundle.
 *
 * Runs without a browser and without installing anything: it validates the
 * manifest and patch, loads the Client half in a browser-like sandbox, drives
 * the tab registration, the resident-tab follow logic, the body's three
 * display states, the probe cadence, and the teardown contract.
 *
 * Run: node scripts/smoke.mjs
 */
import { readFileSync, readdirSync, statSync, lstatSync, existsSync } from 'node:fs'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import vm from 'node:vm'

const here = dirname(fileURLToPath(import.meta.url))
const root = resolve(here, '..')
const failures = []
let checks = 0

/** Record one assertion. */
function ok(condition, message) {
  checks += 1
  if (!condition) failures.push(message)
}

/** Record equality. */
function equal(actual, expected, message) {
  ok(Object.is(actual, expected), `${message} (expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)})`)
}

const read = name => readFileSync(join(root, name), 'utf8')
const PACKAGE_NAME = '@dsh-local/view-51901211-6038-40f3-8878-edd2998f1732'
const KIND = 'jspace-dashboard'
const PAGE_URL = 'http://127.0.0.1:8904/'

// ---------------------------------------------------------------- manifest --
const pkg = JSON.parse(read('package.json'))
equal(pkg.name, PACKAGE_NAME, 'package name is the reserved name')
ok(/^\d+\.\d+\.\d+$/.test(pkg.version), 'package version is semver')
equal(pkg.dsh?.bundle?.patch, './cordis.patch.yml', 'bundle patch path')
equal(pkg.dsh?.client?.platform, 'web', 'client platform is web')
ok(Array.isArray(pkg.dsh?.client?.inject) && pkg.dsh.client.inject.includes('@deepseek-ai/dsh-client-ui-sidebar-right'), 'client injects the right Sidebar package')
for (const exportName of ['.', './client', './locale/*.json', './icon']) {
  ok(exportName in (pkg.exports ?? {}), `exports ${exportName}`)
}
equal(pkg.exports['.'], './index.js', 'root export')
equal(pkg.exports['./client'], './client.js', 'client export')
equal(pkg.icon, './icon.svg', 'manifest icon')
ok(!('scripts' in pkg) || JSON.stringify(pkg.scripts) === '{}', 'no install/build scripts')

// Every runtime file exists.
for (const name of ['index.js', 'client.js', 'cordis.patch.yml', 'icon.svg', 'locale/en.json', 'locale/zh.json']) {
  ok(existsSync(join(root, name)), `runtime file ${name} exists`)
}
// No symlinks escape the package; none exist at all.
function walkFiles(dir) {
  const out = []
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.name === '.git' || entry.name === '.ref' || entry.name === 'node_modules' || entry.name.startsWith('.tmp')) continue
    const full = join(dir, entry.name)
    if (entry.isSymbolicLink()) failures.push(`symlink found at ${full}`)
    else if (entry.isDirectory()) out.push(...walkFiles(full))
    else out.push(full)
  }
  return out
}
const files = walkFiles(root)

// ------------------------------------------------------------------- patch --
const patch = read('cordis.patch.yml')
ok(/^#.*\n/s.test(patch) || patch.trimStart().startsWith('-'), 'patch parses as a YAML list')
const patchBody = patch.split('\n').filter(line => !line.trimStart().startsWith('#'))
const topLevelOps = patchBody.filter(line => /^-\s/.test(line)).map(line => line.replace(/^-\s*/, '').replace(/:.*$/, '').trim())
equal(topLevelOps.join(','), 'insert', 'patch contains only an insert operation')
for (const forbidden of ['group', 'include', 'disabled', '!!js', '!!', '&', '*']) {
  ok(!patchBody.some(line => line.includes(forbidden)), `patch does not use ${forbidden}`)
}
const insertedId = (patchBody.find(line => /^\s+-\s+id:/.test(line)) ?? '').replace(/^\s+-\s+id:\s*/, '').replace(/^['"]|['"]$/g, '')
const insertedName = (patchBody.find(line => /^\s+name:/.test(line)) ?? '').replace(/^\s+name:\s*/, '').replace(/^['"]|['"]$/g, '')
ok(insertedId.startsWith(`${PACKAGE_NAME}:`), `inserted id starts with the package name plus a colon, got ${insertedId}`)
equal(insertedName, PACKAGE_NAME, 'inserted row loads this package')
equal(patchBody.filter(line => /^\s+-\s+id:/.test(line)).length, 1, 'exactly one row inserted')

// ------------------------------------------------------------- locale files --
for (const locale of ['en', 'zh']) {
  const meta = JSON.parse(read(`locale/${locale}.json`)).meta ?? {}
  ok(typeof meta.title === 'string' && meta.title.trim() !== '', `${locale} meta.title`)
  ok(typeof meta.description === 'string' && meta.description.trim() !== '', `${locale} meta.description`)
}
ok(/8904/.test(read('locale/zh.json')), 'zh metadata mentions port 8904')

// -------------------------------------------------------------------- icon --
const icon = read('icon.svg')
ok(icon.trimStart().startsWith('<svg') && icon.trimEnd().endsWith('</svg>'), 'icon is an SVG document')
ok(icon.length < 256 * 1024, 'icon is under the 256 KiB limit')
for (const forbidden of ['<script', '<foreignObject', '<image', '<style', 'onload=']) {
  ok(!icon.includes(forbidden), `icon omits ${forbidden}`)
}

// ------------------------------------------------------------------ Host ESM --
const hostHalf = await import(pathToFileURL(join(root, 'index.js')).href)
equal(typeof hostHalf.apply, 'function', 'Host half exports apply')

// ------------------------------------------------------- Client in a sandbox --
const clientSource = read('client.js')
let registration
const timers = new Map()
let timerSeed = 0
const scheduled = []
const sandbox = {
  window: { __ModuleLoader__: { load(config) { registration = config } } },
  console,
  AbortController,
  fetch: async () => ({ ok: true }),
  setTimeout(callback, delay) {
    timerSeed += 1
    timers.set(timerSeed, { callback, delay })
    scheduled.push(delay)
    return timerSeed
  },
  clearTimeout(id) { timers.delete(id) },
}
vm.createContext(sandbox)
vm.runInContext(clientSource, sandbox, { filename: 'client.js' })

ok(registration !== undefined, 'client registers through window.__ModuleLoader__')
equal(registration?.id, PACKAGE_NAME, 'browser module id is the package name')
equal(typeof registration?.factory, 'function', 'browser module factory exists')

// A React stand-in: element objects, swappable hooks, no DOM.
let state
let effects
let mounted
function makeReact() {
  return {
    Fragment: Symbol('Fragment'),
    createElement(type, props, ...children) {
      const flat = []
      for (const child of children) {
        if (Array.isArray(child)) flat.push(...child)
        else flat.push(child)
      }
      return { type, props: props ?? {}, children: flat }
    },
    useState() {
      return [state, updater => { state = typeof updater === 'function' ? updater(state) : updater }]
    },
    useEffect(callback) {
      if (!mounted) effects.push(callback)
    },
  }
}
const React = makeReact()
const plugin = registration.factory(specifier => {
  equal(specifier, 'react', 'factory requires only react')
  return React
})

equal(typeof plugin?.apply, 'function', 'Client half exports apply')
ok(Array.isArray(plugin.inject) && ['slots', 'locale', 'sidebarRight', 'sidebarRightTabs'].every(service => plugin.inject.includes(service)), 'Client half injects the required services')

// ------------------------------------------------------------ fake client ctx --
const dictionaries = {}
let lifecycle = []
let tabDefinition
const slotRegistrations = []
let mountedListener
let sessionId
let openTabs = []
const opened = []
const closed = []
const openBehavior = { fail: 0 }
const ctx = {
  effect(setup, label) {
    const produced = setup()
    const dispose = typeof produced === 'function' ? produced : () => {}
    lifecycle.push({ label, dispose })
    return () => dispose()
  },
  locale: {
    bind(namespace) {
      return key => dictionaries[namespace]?.zh?.[key] ?? dictionaries[namespace]?.en?.[key] ?? key
    },
    register(namespace, dicts) { dictionaries[namespace] = dicts; return () => {} },
  },
  slots: {
    inject(key, callback) {
      const dispose = callback()
      return () => dispose?.()
    },
    register(options, component) {
      slotRegistrations.push({ options, component })
      return () => {}
    },
  },
  sidebarRightTabs: {
    register(definition) { tabDefinition = definition; return () => {} },
  },
  sidebarRight: {
    mounted: {
      getSnapshot: () => sessionId,
      subscribe(listener) { mountedListener = listener; return () => { mountedListener = undefined } },
    },
    openTabs: { getSnapshot: () => openTabs },
    openTab(kind) {
      if (openBehavior.fail > 0) {
        openBehavior.fail -= 1
        throw new Error('no session surface is mounted')
      }
      opened.push(kind)
    },
    closeIn(id, tabId) { closed.push([id, tabId]) },
  },
}

plugin.apply(ctx)
const runTimer = (delay) => {
  const entry = [...timers.entries()].find(([, value]) => delay === undefined || value.delay === delay)
  if (entry === undefined) return false
  timers.delete(entry[0])
  entry[1].callback()
  return true
}
const flush = () => new Promise(resolve => setImmediate(resolve))

// -------------------------------------------------------------- registration --
ok(tabDefinition !== undefined, 'tab type registered')
equal(tabDefinition?.id, PACKAGE_NAME, 'tab type id is the package name')
equal(tabDefinition?.kind, KIND, 'tab kind')
equal(tabDefinition?.priority, 'extension', 'tab type priority band')
equal(typeof tabDefinition?.title, 'function', 'tab title is a thunk')
ok(Array.isArray(tabDefinition?.guide) && tabDefinition.guide.length === 1, 'one guide entry')
equal(typeof tabDefinition?.guide?.[0]?.icon, 'function', 'guide entry has an icon component')
ok(['tab.title', 'guide.title', 'guide.description'].every(key => key in (dictionaries.jspaceDashboard?.zh ?? {})), 'zh dictionary carries the visible copy')
equal(dictionaries.jspaceDashboard.zh['status.offline'], '8904 未运行', 'offline line is exactly 「8904 未运行」')
equal(typeof dictionaries.jspaceDashboard.en['status.offline'], 'string', 'en dictionary carries the offline line')
equal(tabDefinition.title(''), 'jspace', 'tab chip title')

const bodyEntry = slotRegistrations.find(entry => entry.options.name === 'sidebar.right.pane.tab')
const titleEntry = slotRegistrations.find(entry => entry.options.name === 'sidebar.right.pane.tab.title')
equal(bodyEntry?.options.key, PACKAGE_NAME, 'body registers under the type id')
equal(titleEntry?.options.key, PACKAGE_NAME, 'title registers under the type id')
equal(bodyEntry?.options.locale, 'jspaceDashboard', 'body declares the locale namespace')
equal(titleEntry?.options.locale, 'jspaceDashboard', 'title declares the locale namespace')
equal(titleEntry?.component({ t: ctx.locale.bind('jspaceDashboard') }).children[1], 'jspace', 'title renders the name')

// ------------------------------------------------------------- resident tab --
const OWNER = 'session-889466f5-5ec2-49e6-887f-2b1b54ac5089'
sessionId = undefined
runTimer(0) // initial schedule with no session on screen
equal(opened.length, 0, 'no tab opens while no session is on screen')

sessionId = 'session-other'
openTabs = []
mountedListener()
runTimer(0)
equal(opened.length, 0, 'another conversation does not get the dashboard tab')

sessionId = OWNER
openTabs = []
mountedListener()
runTimer(0)
equal(opened.join(','), KIND, 'the owning session gets the dashboard tab')

openTabs = [{ sessionId: OWNER, tabId: 'tab-1', kind: KIND, contentId: 'x' }]
mountedListener()
runTimer(0)
equal(opened.length, 1, 'an existing dashboard tab is not duplicated')

sessionId = 'session-other'
openTabs = []
mountedListener()
runTimer(0)
equal(opened.length, 1, 'switching to another conversation does not reopen it')

sessionId = OWNER
openBehavior.fail = 1
mountedListener()
runTimer(0)
equal(opened.length, 1, 'an open before the surface is adopted is retried, not forced')
runTimer(200)
equal(opened.length, 2, 'the retry opens the tab once the surface is adopted')

// ------------------------------------------------------------------- body UI --
const t = ctx.locale.bind('jspaceDashboard')
const renderBody = (view) => {
  state = view
  mounted = false
  effects = []
  return bodyEntry.component({ t })
}
const textOf = node => node === null || node === undefined ? ''
  : typeof node === 'string' ? node
    : (node.children ?? []).map(textOf).join('')
const typesOf = node => node === null || node === undefined ? []
  : typeof node === 'string' ? []
    : [node.type, ...(node.children ?? []).flatMap(typesOf)]

const checking = renderBody({ status: 'checking', epoch: 0 })
ok(!typesOf(checking).includes('iframe'), 'checking state shows no iframe')
equal(textOf(checking).trim(), '', 'checking state shows no status text')

const offline = renderBody({ status: 'offline', epoch: 0 })
ok(!typesOf(offline).includes('iframe'), 'offline state shows no iframe')
equal(textOf(offline).trim(), '8904 未运行', 'offline state shows exactly the one-line status')

const online = renderBody({ status: 'online', epoch: 1 })
ok(typesOf(online).includes('iframe'), 'online state mounts the iframe')
const frame = online.children.find(child => child.type === 'iframe')
equal(frame?.props.src, PAGE_URL, 'iframe embeds the dashboard URL')
equal(frame?.props.title, 'jspace 透镜实验仪表盘', 'iframe title is localized')
ok(typeof frame?.props.sandbox === 'string' && !frame.props.sandbox.includes('allow-top-navigation'), 'iframe sandbox blocks top navigation')

// ------------------------------------------------------------ probe behavior --
sandbox.fetch = async () => ({ status: 501 })
state = { status: 'checking', epoch: 0 }
mounted = false
effects = []
renderBody(state)
const cleanupProbe = effects[0]()
ok(timers.size > 0, 'a mounted body starts a probe')
await flush()
runTimer(3000) // no-op: the timeout timer was cleared when the probe answered
ok(state.status === 'online', 'a reachable service mounts the page')
ok(scheduled.includes(30000), 'an online body re-probes on the page refresh cadence')
cleanupProbe()
ok(timers.size === 0, 'unmounting clears the probe timers')

sandbox.fetch = async () => { throw new Error('connection refused') }
scheduled.length = 0
state = { status: 'checking', epoch: 0 }
mounted = false
effects = []
renderBody(state)
const cleanupProbe2 = effects[0]()
await flush()
ok(state.status === 'offline', 'an unreachable service shows the status line')
ok(scheduled.includes(10000), 'an offline body retries sooner')
cleanupProbe2()

// ---------------------------------------------------------------- teardown --
openTabs = [
  { sessionId: 'session-3', tabId: 'tab-3', kind: KIND, contentId: 'x' },
  { sessionId: 'session-3', tabId: 'tab-other', kind: 'guide', contentId: 'y' },
]
for (const entry of [...lifecycle].reverse()) {
  try { entry.dispose() } catch (error) { failures.push(`dispose ${entry.label} threw ${error}`) }
}
equal(closed.length, 1, 'teardown closes only its own tab')
equal(closed[0]?.join('|'), 'session-3|tab-3', 'the closed tab is the dashboard tab')
ok(mountedListener === undefined, 'teardown stops following the on-screen session')

// --------------------------------------------------------------- no leaks ----
const runtimeFiles = ['index.js', 'client.js', 'cordis.patch.yml', 'locale/en.json', 'locale/zh.json', 'icon.svg', 'README.md']
for (const name of runtimeFiles) {
  const text = read(name)
  ok(!/E:\\|\/home\/|file:\/\//.test(text), `${name} has no absolute machine path`)
}

// ------------------------------------------------------------------ report ---
if (failures.length > 0) {
  console.error(`smoke: ${failures.length} failure(s) after ${checks} checks`)
  for (const failure of failures) console.error(` - ${failure}`)
  process.exit(1)
}
console.log(`smoke: ${checks} checks passed`)
