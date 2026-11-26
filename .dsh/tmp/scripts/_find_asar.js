const fs = require('node:fs')
const path = require('node:path')
const base = 'D:/Software/DSH_desktop/resources/app.asar/dsh/node_modules/@deepseek-ai'
const root = (process.argv[2] && process.argv[2] !== 'all') ? path.join(base, process.argv[2]) : base
const pattern = process.argv[3] || 'useProjection'
const re = new RegExp(pattern)
const maxFiles = Number(process.argv[4] || 12)
const maxLines = Number(process.argv[5] || 3)
let files = 0
function walk (dir) {
  let entries = []
  try { entries = fs.readdirSync(dir, { withFileTypes: true }) } catch { return }
  for (const e of entries) {
    if (files >= maxFiles) return
    if (e.name.startsWith('.') || e.name === 'node_modules' || e.name === 'lib') continue
    const p = path.join(dir, e.name)
    if (e.isDirectory()) { walk(p); continue }
    const ext = path.extname(e.name)
    if (!['.ts', '.tsx', '.js', '.mjs', '.md'].includes(ext)) continue
    let text = ''
    try { text = fs.readFileSync(p, 'utf8') } catch { continue }
    if (!re.test(text)) continue
    files++
    console.log(p.slice(base.length + 1))
    const lines = text.split(/\r?\n/)
    let n = 0
    for (let i = 0; i < lines.length; i++) {
      if (!re.test(lines[i])) continue
      if (n++ >= maxLines) break
      console.log('  ' + (i + 1) + ': ' + lines[i].trim().slice(0, 200))
    }
  }
}
walk(root)
if (files === 0) console.log('no matches')
