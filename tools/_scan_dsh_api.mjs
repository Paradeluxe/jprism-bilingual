import fs from 'node:fs'
import path from 'node:path'

const install = process.env.DSH_INSTALL_DIR || ''
const root = path.dirname(install)
const hits = []
const pattern = /commands\.execute|remote\.commands|Slots\.listSubTree|sidebar-right|conversation\.composer\.dock/

function scan(dir, depth) {
  if (depth > 2) return
  let names
  try { names = fs.readdirSync(dir) } catch { return }
  for (const name of names.slice(0, 300)) {
    const p = path.join(dir, name)
    let st
    try { st = fs.statSync(p) } catch { continue }
    if (st.isDirectory()) scan(p, depth + 1)
    else if (/\.(md|js|mjs|json)$/.test(name) && st.size < 700000) {
      let text
      try { text = fs.readFileSync(p, 'utf8') } catch { continue }
      if (pattern.test(text)) {
        const lines = text.split('\n')
        const found = []
        lines.forEach((line, i) => {
          if (pattern.test(line)) found.push((i + 1) + ': ' + line.trim().slice(0, 140))
        })
        if (found.length) hits.push({ file: p.replace(install, '<dsh>'), found: found.slice(0, 4) })
      }
    }
  }
}

scan(root, 0)
for (const hit of hits.slice(0, 40)) {
  console.log(hit.file)
  for (const line of hit.found) console.log('  ' + line)
}
console.log('files with hits:', hits.length)
