# -*- coding: utf-8 -*-
"""Build the Edge preview page for the new click-a-gap interaction.

Reads the real zone sidecar, keeps a readable subset (every kind, a few
instances), and writes tools/ui-harness/preview.html. The component itself is
the shipped client.js, so the screenshot shows the real UI.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
layout_path = os.path.join(REPO, 'tools', 'fig-test', 'out', 'fig1_merged_grid.png.layout.json')
if not os.path.exists(layout_path):
    layout_path = os.path.join(REPO, 'figures', 'fig1_merged_grid_print.png.layout.json')
layout = json.load(open(layout_path, encoding='utf-8'))

keep = {}
for zone in layout['zones']:
    kind = zone['kind']
    bucket = keep.setdefault(kind, [])
    limit = 6 if kind in ('panel-gap', 'family-title', 'row-gap', 'family-gap') else 2
    if len(bucket) < limit:
        bucket.append(zone)
zones = [zone for bucket in keep.values() for zone in bucket]
zones.sort(key=lambda z: z['box'][2] * z['box'][3], reverse=True)

payload = json.dumps({'image': layout['image'], 'zones': zones}, ensure_ascii=False)

html = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Figure spacing editor - click a gap</title>
<style>
  html, body { margin: 0; height: 100%; background: #f6f7f9; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }
  #shell { width: 400px; height: 100%; margin: 0 auto; background: #fff; border-left: 1px solid #e3e6ea; border-right: 1px solid #e3e6ea; display: flex; flex-direction: column; }
  #head { padding: 10px 12px 8px; font-size: 12px; font-weight: 600; color: #1f2328; border-bottom: 1px solid #e3e6ea; }
  #root { flex: 1 1 auto; min-height: 0; }
</style>
</head>
<body>
<div id="shell">
  <div id="head">Right sidebar &middot; Figure spacing</div>
  <div id="root"></div>
</div>
<script src="node_modules/react/umd/react.development.js"></script>
<script src="node_modules/react-dom/umd/react-dom.development.js"></script>
<script>
  const LAYOUT = __LAYOUT__;
  const baseState = {
    figure: 'fig1',
    label: 'Figure 1 - composition plate',
    source: 'experiment/figures/make_family_grids.py',
    tokens: {
      MX: 64, PAD: 96, RULE_Y: 120, TITLE_GAP: 24, HEAD_GAP: 40, LABH: 60,
      LABEL_GAP: 32, TAILPAD: 64, LEGEND_GAP: 128, PLAB: 128, LENSW: 64,
      PH: 102, LENS_GAP: 32, CELLGAP: 64, FGAP: 144, ROW_GAP: 64,
      ROW_FAM_GAP: 96, TICKROW: 32, MGAP: 48,
    },
    png: 'figures/fig1_merged_grid_print.png',
    pngExists: true,
    image: { width: __IMG_W__, height: __IMG_H__, printWidthCmAt22_1: 11.39 },
  }
  const audit = { image: { width: __IMG_W__, height: __IMG_H__ }, marginPx: { top: 96, right: 96, bottom: 96, left: 96 } }
  window.fetch = async (url, options = {}) => {
    const body = options.body ? JSON.parse(options.body) : null
    if (String(url).includes('/state')) return { ok: true, status: 200, json: async () => baseState }
    if (String(url).includes('/layout')) return { ok: true, status: 200, json: async () => LAYOUT }
    if (String(url).includes('/audit')) return { ok: true, status: 200, json: async () => audit }
    if (String(url).includes('/apply')) {
      const tokens = Object.assign({}, baseState.tokens, body && body.tokens)
      return { ok: true, status: 200, json: async () => ({ ok: true, changed: [], rendered: true, state: Object.assign({}, baseState, { tokens }) }) }
    }
    return { ok: true, status: 200, json: async () => ({ ok: true, state: baseState }) }
  }
  let factory = null
  window.__ModuleLoader__ = { load({ id, factory: make }) { factory = make } }
</script>
<script src="../../plugins/fig-layout/client.js"></script>
<script>
  const T = {
    'figure.label': 'Plate', 'figure.fig1': 'Figure 1 \\u00b7 composition', 'figure.fig2': 'Figure 2 \\u00b7 overlap',
    'status.saved': 'Saved', 'status.edited': 'edited', 'status.applied': 'Applied', 'status.rendered': 'Rendered',
    'meta.size': 'Size', 'meta.print': 'Print', 'meta.printValue': '22.1 cm high \\u2192 {width} cm',
    'meta.margins': 'Margins', 'meta.unit': 'px', 'meta.open': 'Open PNG',
    'group.page': 'Page margins and labels', 'group.panels': 'Panels and rows',
    'group.unit': 'canvas units, 4-unit grid',
    'action.apply': 'Apply', 'action.render': 'Re-render', 'action.reset': 'Reset', 'action.all': 'All gaps',
    'hint.pick': 'Click a gap in the plate to filter the controls',
    'kind.family-title': 'Family title', 'kind.checkpoint-title': 'Checkpoint titles',
    'kind.label-column': 'Label columns', 'kind.panel-gap': 'Checkpoint gaps',
    'kind.prompt-gap': 'Prompt-group gaps', 'kind.lens-gap': 'Lens gaps', 'kind.axis': 'Tick rows',
    'kind.family-gap': 'Space between families', 'kind.row-gap': 'Row gaps',
    'kind.page-margin': 'Page edge', 'kind.legend-gap': 'Space before the legend',
    'kind.title-gap': 'Space under the family title', 'kind.head-gap': 'Space under the family rule',
    'kind.places': 'places', 'kind.tokens': 'tokens', 'kind.token': 'token',
    'status.loading': 'Reading plate', 'status.offline': 'Service on 8829 is not running',
    'error.prefix': 'Failed',
  }
  const plugin = factory(name => {
    if (name === 'react') return window.React
    throw new Error('unexpected require: ' + name)
  })
  const registrations = []
  const ctx = {
    locale: { bind: () => key => T[key] || key, register: () => () => {} },
    slots: {
      inject: (name, make) => make(),
      register: (options, component) => { registrations.push({ options, component }); return () => {} },
    },
    sidebarRightTabs: { register: () => () => {} },
    sidebarRight: {
      mounted: { getSnapshot: () => 'session-preview', subscribe: () => () => {} },
      openTabs: { getSnapshot: () => [] },
      openTab: () => {},
      closeIn: () => {},
    },
    effect: fn => { const dispose = fn(); if (typeof dispose === 'function') dispose() },
  }
  plugin.apply(ctx)
  const body = registrations.find(entry => entry.options && entry.options.name === 'sidebar.right.pane.tab')
  const root = window.ReactDOM.createRoot(document.getElementById('root'))
  root.render(window.React.createElement(body.component, { t: key => T[key] || key }))

  // Show the interaction in the screenshot: pick the checkpoint gaps once the
  // plate and its zones are on screen.
  const timer = setInterval(() => {
    const zone = document.querySelector('[aria-label="Checkpoint gaps"]')
    if (zone) {
      zone.click()
      clearInterval(timer)
    }
  }, 80)
  setTimeout(() => clearInterval(timer), 4000)
</script>
</body>
</html>
'''
img = layout['image']
html = html.replace('__LAYOUT__', payload)
html = html.replace('__IMG_W__', str(img['width'])).replace('__IMG_H__', str(img['height']))
out = os.path.join(REPO, 'tools', 'ui-harness', 'preview.html')
open(out, 'w', encoding='utf-8', newline='\n').write(html)
print('preview.html written with', len(zones), 'zones')
