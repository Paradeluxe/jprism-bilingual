const fs = require('node:fs')
const path = require('node:path')
const base = 'D:/Software/DSH_desktop/resources/app.asar/dsh'
function ls (p) {
  try { return fs.readdirSync(p).filter(n => !n.startsWith('.')).join('\n') } catch (e) { return 'ERR ' + e.message }
}
const pkgRoot = path.join(base, 'node_modules/@deepseek-ai')
const names = fs.readdirSync(pkgRoot).filter(n => !n.startsWith('.'))
console.log('count=' + names.length)
console.log(names.filter(n => n.includes('client')).join('\n'))
