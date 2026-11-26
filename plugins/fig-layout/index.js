// Host half of the figure-spacing plugin.
//
// The plate generators keep their spacing in named tokens on a 4-unit grid.
// This plugin reads those tokens, measures the margins the rendered PNG really
// has, patches the tokens in the source, re-renders with the project's own
// Python environment, and serves the same operations to the sidebar editor over
// a loopback HTTP service.

import fs from 'node:fs'
import os from 'node:os'
import http from 'node:http'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'



export const inject = ['tools']

const execFileAsync = promisify(execFile)

// The Host loader does not resolve @deepseek-ai/dsh-tools from this workspace
// package, so build registry-ready definitions from the same small schema
// surface the typed helper uses: name, description, parameters, output, execute.
function defineTool(options) {
  const properties = {}
  const required = []
  for (const [key, spec] of Object.entries(options.parameters || {})) {
    const property = spec.type === 'json' ? {} : { type: spec.type }
    if (spec.enum) property.enum = spec.enum
    if (spec.description) property.description = spec.description
    properties[key] = property
    if (spec.required) required.push(key)
  }
  return {
    name: options.name,
    description: options.description,
    parameters: {
      type: 'object',
      properties,
      ...(required.length ? { required } : {}),
      additionalProperties: false,
    },
    output: { schema: {}, render: options.output.render },
    async execute(args) {
      return options.execute(args)
    },
  }
}

const COMMON_TOKENS = [
  'PH', 'LENS_GAP', 'CELLGAP', 'MGAP', 'TITLE_GAP', 'HEAD_GAP', 'LABH',
  'LABEL_GAP', 'ROW_GAP', 'ROW_FAM_GAP', 'TICKROW', 'RULE_Y', 'MX',
  'LEGEND_GAP', 'TAILPAD', 'FGAP', 'PLAB', 'LENSW',
]

const FIGURES = {
  // Isolated working copy: the real figure in experiment/figures is left alone
  // until the test copy is approved.
  fig1: {
    label: 'Figure 1 - test copy',
    quick: 'tools/fig-test/quick_svg.py',
    file: 'tools/fig-test/make_family_grids.py',
    cwd: 'tools/fig-test',
    script: 'make_family_grids.py',
    png: 'tools/fig-test/out/fig1_merged_grid.png',
    env: {},
    scope: null,
    tokens: [...COMMON_TOKENS.slice(0, 12), 'MX', 'PAD', ...COMMON_TOKENS.slice(13)],
  },
  fig2: {
    label: 'Figure 2 - overlap plate',
    file: 'experiment/figures/make_readme_figs_svg.py',
    cwd: 'experiment/figures',
    script: 'make_readme_figs_svg.py',
    png: 'figures/fig2_overlap_3lens.png',
    env: { OV_FS: '1.45', OV_PANW: '0.75' },
    scope: ['def draw_overlap', '\n# ---------------------------------------------------------------- main'],
    tokens: COMMON_TOKENS,
  },
}

const NUM = '([0-9]+(?:\\.[0-9]+)?)'

function fail(code, message) {
  const error = new Error(message)
  error.code = code
  return error
}

function figureConfig(config, name) {
  const fig = FIGURES[name]
  if (!fig) throw fail('UNKNOWN_FIGURE', 'unknown figure: ' + String(name))
  const root = config.root || process.env.DSH_FIG_ROOT || process.cwd()
  return { fig, root: path.resolve(root) }
}

function scopeOf(text, fig) {
  if (!fig.scope) return { start: 0, end: text.length }
  const start = text.indexOf(fig.scope[0])
  if (start < 0) throw fail('SOURCE_SHAPE', 'missing function ' + fig.scope[0])
  const end = text.indexOf(fig.scope[1], start + 1)
  return { start, end: end < 0 ? text.length : end }
}

function readSource(root, fig) {
  const file = path.join(root, fig.file)
  if (!fs.existsSync(file)) throw fail('SOURCE_MISSING', 'source not found: ' + file)
  return { file, text: fs.readFileSync(file, 'utf8') }
}

function readTokens(fig, text) {
  const { start, end } = scopeOf(text, fig)
  const slice = text.slice(start, end)
  const out = {}
  for (const token of fig.tokens) {
    const match = new RegExp('^[ \\t]*' + token + '\\s*=\\s*' + NUM, 'm').exec(slice)
    if (match) out[token] = Number(match[1])
  }
  return out
}

function patchTokens(fig, text, values) {
  const { start, end } = scopeOf(text, fig)
  let slice = text.slice(start, end)
  const changed = []
  for (const [token, value] of Object.entries(values)) {
    if (!fig.tokens.includes(token)) throw fail('UNKNOWN_TOKEN', 'unknown token: ' + token)
    const number = Number(value)
    if (!Number.isFinite(number) || number <= 0 || number > 10000) {
      throw fail('BAD_VALUE', token + ' must be a positive number')
    }
    const pattern = new RegExp('^(\\s*' + token + '\\s*=\\s*)' + NUM, 'm')
    if (!pattern.test(slice)) throw fail('TOKEN_MISSING', 'token not found in source: ' + token)
    const before = pattern.exec(slice)[2]
    if (Number(before) !== number) {
      slice = slice.replace(pattern, '$1' + String(number))
      changed.push({ token, from: Number(before), to: number })
    }
  }
  return { text: text.slice(0, start) + slice + text.slice(end), changed }
}

function pngSize(file) {
  const bytes = fs.readFileSync(file)
  return { width: bytes.readUInt32BE(16), height: bytes.readUInt32BE(20) }
}

function layoutPath(root, fig) {
  return path.join(root, fig.png + '.layout.json')
}

function readPreview(root, fig) {
  const file = path.join(root, path.dirname(fig.png), 'preview_data.json')
  if (!fs.existsSync(file)) return null
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'))
  } catch {
    return null
  }
}

function readLayout(root, fig) {
  const file = layoutPath(root, fig)
  if (!fs.existsSync(file)) return { image: null, zones: [] }
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8'))
    return {
      image: parsed.image || null,
      zones: Array.isArray(parsed.zones) ? parsed.zones : [],
    }
  } catch {
    return { image: null, zones: [] }
  }
}

function readState(figureName, config) {
  const { fig, root } = figureConfig(config, figureName)
  const { file, text } = readSource(root, fig)
  const pngPath = path.join(root, fig.png)
  const state = {
    figure: figureName,
    label: fig.label,
    source: fig.file,
    tokens: readTokens(fig, text),
    png: fig.png,
    pngExists: fs.existsSync(pngPath),
  }
  if (state.pngExists) {
    const size = pngSize(pngPath)
    const heightCm = 22.1
    state.image = {
      ...size,
      bytes: fs.statSync(pngPath).size,
      mtimeMs: Math.round(fs.statSync(pngPath).mtimeMs),
      printWidthCmAt22_1: Math.round((heightCm * size.width / size.height) * 100) / 100,
      cmPerUnit: Math.round((heightCm / (size.height / 2)) * 10000) / 10000,
    }
  }
  state.sourceMtimeMs = Math.round(fs.statSync(file).mtimeMs)
  state.stale = !state.pngExists ||
    (fs.statSync(file).mtimeMs > fs.statSync(pngPath).mtimeMs + 500)
  const layout = readLayout(root, fig)
  state.zones = layout.zones.length
  return { state, fig, root }
}

async function renderFigure(figureName, config) {
  const { fig, root } = figureConfig(config, figureName)
  const python = config.python || path.join(root, 'experiment', '.venv', 'Scripts', 'python.exe')
  if (!fs.existsSync(python)) throw fail('PYTHON_MISSING', 'python not found: ' + python)
  const cwd = path.join(root, fig.cwd)
  try {
    await execFileAsync(python, [fig.script], {
      cwd,
      env: { ...process.env, ...fig.env },
      timeout: 300000,
      maxBuffer: 8 * 1024 * 1024,
    })
  } catch (error) {
    throw fail('RENDER_FAILED', 'render failed: ' + (error.stderr || error.message))
  }
  return readState(figureName, config).state
}

async function quickFigure(figureName, tokens, config) {
  const { fig, root } = figureConfig(config, figureName)
  if (!fig.quick) throw fail('NO_QUICK', 'no live preview for ' + figureName)
  const script = path.join(root, fig.quick)
  if (!fs.existsSync(script)) throw fail('NO_QUICK_SCRIPT', 'missing ' + script)
  const python = config.python || path.join(root, 'experiment', '.venv', 'Scripts', 'python.exe')
  const request = path.join(os.tmpdir(), 'fig-quick-' + process.pid + '-' + Date.now() + '.json')
  fs.writeFileSync(request, JSON.stringify({ tokens: tokens || {} }), 'utf8')
  try {
    const { stdout } = await execFileAsync(python, [script, request], {
      timeout: 60000,
      maxBuffer: 32 * 1024 * 1024,
    })
    return JSON.parse(stdout)
  } finally {
    try { fs.unlinkSync(request) } catch { /* best effort */ }
  }
}

async function auditFigure(figureName, config) {
  const { fig, root } = figureConfig(config, figureName)
  const pngPath = path.join(root, fig.png)
  if (!fs.existsSync(pngPath)) throw fail('PNG_MISSING', 'render first: ' + fig.png)
  const python = config.python || path.join(root, 'experiment', '.venv', 'Scripts', 'python.exe')
  const script = path.join(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')), 'audit.py')
  try {
    const { stdout } = await execFileAsync(python, [script, pngPath], { timeout: 120000 })
    return JSON.parse(stdout)
  } catch (error) {
    throw fail('AUDIT_FAILED', 'audit failed: ' + (error.stderr || error.message))
  }
}

function openStream(url, req, res) {
  if (!fs.existsSync(url)) {
    res.writeHead(404, { 'content-type': 'application/json' })
    res.end(JSON.stringify({ error: 'PNG_MISSING' }))
    return
  }
  res.writeHead(200, {
    'content-type': 'image/png',
    'cache-control': 'no-store',
    'access-control-allow-origin': req.headers.origin || '*',
    vary: 'origin',
  })
  fs.createReadStream(url).pipe(res)
}

function sendJson(req, res, status, value) {
  const body = JSON.stringify(value)
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'access-control-allow-origin': req.headers.origin || '*',
    'access-control-allow-methods': 'GET,POST,OPTIONS',
    'access-control-allow-headers': 'content-type',
    vary: 'origin',
  })
  res.end(body)
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0
    const chunks = []
    req.on('data', (chunk) => {
      size += chunk.length
      if (size > 1024 * 1024) {
        reject(fail('BODY_TOO_LARGE', 'request body too large'))
        req.destroy()
        return
      }
      chunks.push(chunk)
    })
    req.on('end', () => {
      if (!chunks.length) return resolve({})
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')))
      } catch {
        reject(fail('BAD_JSON', 'request body is not valid JSON'))
      }
    })
    req.on('error', reject)
  })
}

function createServer(config) {
  return http.createServer(async (req, res) => {
    try {
      if (req.method === 'OPTIONS') {
        res.writeHead(204, {
          'access-control-allow-origin': req.headers.origin || '*',
          'access-control-allow-methods': 'GET,POST,OPTIONS',
          'access-control-allow-headers': 'content-type',
          'access-control-max-age': '600',
          vary: 'origin',
        })
        res.end()
        return
      }
      const url = new URL(req.url || '/', 'http://127.0.0.1')
      const figureName = url.searchParams.get('figure') || 'fig1'

      if (req.method === 'GET' && url.pathname === '/') {
        sendJson(req, res, 200, {
          plugin: '@local/dsh-fig-layout',
          figures: Object.fromEntries(Object.entries(FIGURES).map(([k, v]) => [k, v.label])),
          routes: ['GET /state?figure=', 'GET /figure.png?figure=', 'GET /audit?figure=', 'GET /layout?figure=', 'POST /quick', 'POST /apply', 'POST /render'],
        })
        return
      }
      if (req.method === 'GET' && url.pathname === '/state') {
        sendJson(req, res, 200, readState(figureName, config).state)
        return
      }
      if (req.method === 'GET' && url.pathname === '/figure.png') {
        openStream(path.join(figureConfig(config, figureName).root, FIGURES[figureName].png), req, res)
        return
      }
      if (req.method === 'POST' && url.pathname === '/quick') {
        const body = await readBody(req)
        sendJson(req, res, 200, await quickFigure(body.figure || figureName, body.tokens, config))
        return
      }
      if (req.method === 'GET' && url.pathname === '/preview') {
        const { fig, root } = figureConfig(config, figureName)
        const preview = readPreview(root, fig)
        if (!preview) {
          sendJson(req, res, 404, { error: 'NO_PREVIEW_DATA' })
          return
        }
        sendJson(req, res, 200, preview)
        return
      }
      if (req.method === 'GET' && url.pathname === '/layout') {
        const { fig, root } = figureConfig(config, figureName)
        sendJson(req, res, 200, readLayout(root, fig))
        return
      }
      if (req.method === 'GET' && url.pathname === '/audit') {
        sendJson(req, res, 200, await auditFigure(figureName, config))
        return
      }
      if (req.method === 'POST' && (url.pathname === '/apply' || url.pathname === '/render')) {
        const body = await readBody(req)
        const name = body.figure || figureName
        if (url.pathname === '/render') {
          sendJson(req, res, 200, { ok: true, state: await renderFigure(name, config) })
          return
        }
        const { fig, root } = figureConfig(config, name)
        const { file, text } = readSource(root, fig)
        const { text: next, changed } = patchTokens(fig, text, body.tokens || {})
        if (changed.length) fs.writeFileSync(file, next, 'utf8')
        const state = body.render === false ? readState(name, config).state : await renderFigure(name, config)
        sendJson(req, res, 200, { ok: true, changed, rendered: body.render !== false, state })
        return
      }
      sendJson(req, res, 404, { error: 'NOT_FOUND' })
    } catch (error) {
      sendJson(req, res, 400, { ok: false, code: error.code || 'ERROR', error: error.message })
    }
  })
}

export function apply(ctx, config = {}) {
  const port = Number(config.port || 8829)
  const server = createServer(config)
  ctx.effect(() => {
    let active = port
    let attempts = 0
    const listen = () => {
      server.listen(active, '127.0.0.1', () => {
        console.log('[fig-layout] listening on http://127.0.0.1:' + active)
      })
    }
    server.on('error', (error) => {
      if (error && error.code === 'EADDRINUSE' && attempts < 5) {
        attempts += 1
        active += 1
        setTimeout(listen, 150)
        return
      }
      console.error('[fig-layout] server error:', error && error.message)
    })
    listen()
    return () => server.close()
  })

  const tools = [
    defineTool({
      name: 'fig_spacing_read',
      description: 'Read the spacing tokens, rendered PNG size, print scale, clickable gap zones and whether the source is newer than the saved render of a J-Prism plate (fig1 = composition, fig2 = overlap).',
      parameters: {
        figure: { type: 'string', enum: ['fig1', 'fig2'], required: true, description: 'Which plate to read.' },
      },
      output: {
        schema: { type: 'json' },
        render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
      },
      async execute(args) {
        return readState(args.figure, config).state
      },
    }),
    defineTool({
      name: 'fig_spacing_apply',
      description: 'Patch spacing tokens in the figure source and re-render it. Returns the changed tokens and the new render state. Values are canvas units on a 4-unit grid; tokens are listed by fig_spacing_read.',
      parameters: {
        figure: { type: 'string', enum: ['fig1', 'fig2'], required: true },
        tokens: { type: 'json', required: true, description: 'Object of token name to positive number, e.g. {"MGAP": 48, "TITLE_GAP": 24}.' },
        render: { type: 'boolean', description: 'Re-render after patching; defaults to true.' },
      },
      output: {
        schema: { type: 'json' },
        render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
      },
      async execute(args) {
        const { fig, root } = figureConfig(config, args.figure)
        const { file, text } = readSource(root, fig)
        const { text: next, changed } = patchTokens(fig, text, args.tokens || {})
        if (changed.length) fs.writeFileSync(file, next, 'utf8')
        const state = args.render === false ? readState(args.figure, config).state : await renderFigure(args.figure, config)
        return { ok: true, changed, rendered: args.render !== false, state }
      },
    }),
    defineTool({
      name: 'fig_spacing_audit',
      description: 'Measure the actual outer margins of a rendered plate and report its pixel size, so a nominal margin token can be compared with what the PNG really shows.',
      parameters: {
        figure: { type: 'string', enum: ['fig1', 'fig2'], required: true },
      },
      output: {
        schema: { type: 'json' },
        render: (_args, value) => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
      },
      async execute(args) {
        return auditFigure(args.figure, config)
      },
    }),
  ]

  for (const tool of tools) ctx.effect(() => ctx.tools.register(tool))
}
