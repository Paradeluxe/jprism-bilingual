// Usage: node _search_asar.js <literal-or-regex-pattern> <subdir> [maxHits] [maxLinesPerFile]
// Searches files under node_modules/@deepseek-ai/<subdir> inside app.asar via the Electron runtime.
const fs = require('node:fs')
const path = require('node:path')
const base = 'D:/Software/DSH_desktop/resources/app.asar/dsh/node_modules/@deepseek-ai'
const pattern = process.argv[2]
const sub = process.argv[3] || ''
const maxHits = Number(process.argv[4] || 60)
const maxLinesPerFile = Number(process.argv[5] || 6)
const re = new RegExp(pattern)
const TEXT = new Set(['.ts', '.tsx', '.js', '.mjs', '.json', '.md', '.yml', '.yaml', '.css'])
let hits = 0
function walk (dir) {
  let entries = []
  try { entries = fs.readdirSync(dir, { withFileTypes: true }) } catch { return }
  for (const e of entries) {
    if (e.name.startsWith('.') || e.name === 'node_modules') continue
    const p = path.join(dir, e.name)
    if (e.isDirectory()) { if (hits < maxHits) walk(p); continue }
    if (!TEXT.has(path.extname(e.name))) continue
    let st = null
    try { st = fs.statSync(p) } catch { continue }
    if (st.size > 2 * 1024 * 1024) continue
    let text = ''
    try { text = fs.readFileSync(p, 'utf8') } catch { continue }
    if (!re.test(text)) continue
    const lines = text.split(/\r?\n/)
    let printed = 0
    for (let i = 0; i < lines.length; i++) {
      if (!re.test(lines[i])) continue
      if (printed === 0) { console.log(p.slice(base.length + 1)); }
      if (printed < maxLinesPerFile) console.log('  ' + (i + 1) + ': ' + lines[i].trim().slice(0, 220))
      printed++
      hits++
      if (hits >= maxHits) return
    }
    if (printed > maxLinesPerFile) console.log('  ... ' + (printed - maxLinesPerFile) + ' more lines in file')
  }
}
walk(sub ? path.join(base, sub) : base)
if (hits === 0) console.log('no matches')
