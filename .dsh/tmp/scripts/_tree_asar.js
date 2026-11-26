const fs = require('node:fs')
const path = require('node:path')
const base = 'D:/Software/DSH_desktop/resources/app.asar/dsh/node_modules/@deepseek-ai'
function tree (dir, depth, prefix) {
  if (depth < 0) return
  let names = []
  try { names = fs.readdirSync(dir).filter(n => !n.startsWith('.')) } catch (e) { console.log(prefix + 'ERR ' + e.message); return }
  for (const n of names) {
    const p = path.join(dir, n)
    let st = null
    try { st = fs.statSync(p) } catch { continue }
    if (st.isDirectory()) {
      if (n === 'node_modules' || n === 'src' || n === 'lib') { console.log(prefix + n + '/'); tree(p, depth - 1, prefix + '  ') }
      else { console.log(prefix + n + '/'); if (depth > 0) tree(p, depth - 1, prefix + '  ') }
    } else {
      console.log(prefix + n + '  ' + st.size)
    }
  }
}
for (const pkg of process.argv.slice(2)) {
  console.log('=== ' + pkg)
  tree(path.join(base, pkg), 1, '')
}
