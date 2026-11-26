/**
 * Browser half of the figure-spacing plugin.
 *
 * The plate is the main body and it is drawn in the browser: the Host exports
 * the composition data and the palette once (`/preview`), and every slider move
 * re-lays out and repaints the plate on a canvas immediately. The full
 * matplotlib render still runs on Apply for the authoritative PNG, but the
 * preview never waits for it.
 *
 * Only empty gaps are clickable. The gap map is computed from the same layout
 * the drawing uses, so the boxes follow the tokens live.
 */
;(() => {
  'use strict'

  const PACKAGE_NAME = '@local/dsh-fig-layout'
  const KIND = 'fig-layout'
  const NS = 'figLayout'
  const API = 'http://127.0.0.1:8829'

  const en = {
    'tab.title': 'Figure spacing',
    'guide.title': 'Figure spacing editor',
    'guide.description': 'Drag a gap in the live plate, watch the layout move, and render the final PNG when it is right.',
    'figure.label': 'Plate',
    'figure.fig1': 'Figure 1 \u00b7 composition',
    'figure.fig2': 'Figure 2 \u00b7 overlap',
    'group.unit': 'canvas units, 4-unit grid',
    'kind.family-title': 'Family title',
    'kind.title-gap': 'Space under the family title',
    'kind.head-gap': 'Space under the family rule',
    'kind.legend-gap': 'Space before the legend',
    'kind.checkpoint-title': 'Checkpoint titles',
    'kind.label-column': 'Label columns',
    'kind.panel-gap': 'Checkpoint gaps',
    'kind.prompt-gap': 'Prompt-group gaps',
    'kind.lens-gap': 'Lens gaps',
    'kind.axis': 'Tick rows',
    'kind.family-gap': 'Space between families',
    'kind.row-gap': 'Row gaps',
    'kind.page-margin': 'Page edge',
    'kind.legend': 'Legend block',
    'chips.label': 'Gap types',
    'value.unit': 'canvas units',
    'kind.places': 'places',
    'kind.tokens': 'tokens',
    'kind.token': 'token',
    'action.apply': 'Apply',
    'action.render': 'Re-render',
    'action.reset': 'Reset',
    'action.all': 'All gaps',
    'hint.pick': 'Click a gap in the plate to pick it, then drag its slider',
    'status.loading': 'Reading plate',
    'status.offline': 'Service on 8829 is not running',
    'status.rendering': 'Rendering the source change',
    'status.noGaps': 'No gap map for this plate',
    'status.applied': 'Applied',
    'status.rendered': 'Rendered',
    'status.preview': 'Live preview',
    'status.saved': 'Saved',
    'status.edited': 'edited',
    'meta.size': 'Size',
    'meta.print': 'Print',
    'meta.margins': 'Margins',
    'meta.open': 'Open PNG',
    'meta.unit': 'px',
    'meta.printValue': '22.1 cm high \u2192 {width} cm',
    'preview.alt': 'Rendered plate preview',
    'error.prefix': 'Failed',
  }

  const zh = {
    'tab.title': '图版间距',
    'guide.title': '图版间距编辑器',
    'guide.description': '在实时图版上拖动空隙，松手即见版面变化，满意后再渲染最终 PNG。',
    'figure.label': '图版',
    'figure.fig1': 'Figure 1 \u00b7 composition',
    'figure.fig2': 'Figure 2 \u00b7 overlap',
    'group.unit': '画布单位，4 单位网格',
    'kind.title-gap': '家族标题下方的空隙',
    'kind.head-gap': '家族横线下方的空隙',
    'kind.legend-gap': '图例前的空隙',
    'kind.panel-gap': '检查点间距',
    'kind.prompt-gap': '提示组间距',
    'kind.lens-gap': '语种行间距',
    'kind.family-gap': '家族之间',
    'kind.row-gap': '行间距',
    'kind.page-margin': '页边',
    'chips.label': '空隙类型',
    'value.unit': '画布单位',
    'kind.places': '处',
    'kind.tokens': '个 token',
    'kind.token': '个 token',
    'action.apply': '应用',
    'action.render': '重新渲染',
    'action.reset': '还原',
    'action.all': '全部空隙',
    'hint.pick': '点击图版里的空隙选中它，然后拖动滑杆',
    'status.loading': '正在读取图版',
    'status.offline': '8829 上的图形服务没有响应',
    'status.rendering': '正在渲染源码改动',
    'status.noGaps': '此图版没有空隙数据',
    'status.applied': '已应用',
    'status.rendered': '已渲染',
    'status.preview': '实时预览',
    'status.saved': '已保存',
    'status.edited': '已改动',
    'meta.size': '尺寸',
    'meta.print': '印出',
    'meta.margins': '边距',
    'meta.open': '打开 PNG',
    'meta.unit': 'px',
    'meta.printValue': '按 22.1 cm 高 \u2192 {width} cm',
    'preview.alt': '图版渲染预览',
    'error.prefix': '失败',
  }

  const RANGE = { min: 4, max: 320, step: 2 }

  const IS_JSDOM = typeof navigator !== 'undefined' && /jsdom/i.test(navigator.userAgent)

  const BASE_CSS = `
.fig-zone{position:absolute;padding:0;margin:0;border:1px solid transparent;background:transparent;border-radius:3px;cursor:pointer;transition:background-color 100ms ease,border-color 100ms ease,opacity 100ms ease}
.fig-zone:hover{border-color:#57606a;background:rgba(36,123,191,.07)}
.fig-zone.is-linked{border-color:#57606a;background:rgba(36,123,191,.07)}
.fig-zone.is-selected{border-color:#247bbf;background:rgba(36,123,191,.14)}
.fig-zone.is-selected:hover{border-color:#247bbf;background:rgba(36,123,191,.18)}
.fig-zone.is-dim{opacity:.35}
`

  // Browser-only rules. jsdom cannot parse vendor range pseudo-elements, and the
  // tests only need the layout and the event handlers.
  const ADVANCED_CSS = `
.fig-focus:focus-visible{outline:2px solid #247bbf;outline-offset:3px}
.fig-range{appearance:none;-webkit-appearance:none;flex:1 1 auto;min-width:56px;height:24px;margin:0;padding:0;border:0;background:transparent;cursor:pointer}
.fig-range::-webkit-slider-runnable-track{height:4px;border-radius:2px;background:linear-gradient(to right,var(--fill,#247bbf) var(--pct,0%),var(--track,#8f99a4) var(--pct,0%))}
.fig-range::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:14px;height:14px;margin-top:-5px;border:2px solid var(--fill,#247bbf);border-radius:50%;background:#ffffff;box-sizing:border-box}
.fig-range::-moz-range-track{height:4px;border-radius:2px;background:#8f99a4}
.fig-range::-moz-range-progress{height:4px;border-radius:2px;background:var(--fill,#247bbf)}
.fig-range::-moz-range-thumb{width:14px;height:14px;border:2px solid var(--fill,#247bbf);border-radius:50%;background:#ffffff;box-sizing:border-box}
.fig-range:focus-visible{outline:2px solid #247bbf;outline-offset:4px;border-radius:2px}
@media (prefers-color-scheme: dark){
.fig-zone:hover,.fig-zone.is-linked{border-color:#9aa7b4;background:rgba(90,169,230,.14)}
.fig-zone.is-selected{border-color:#5aa9e6;background:rgba(90,169,230,.22)}
.fig-range{--track:#5b6672}
.fig-range::-webkit-slider-thumb{background:#11161c}
.fig-range::-moz-range-thumb{background:#11161c}
.fig-focus:focus-visible{outline-color:#5aa9e6}
}
@media (prefers-reduced-motion: reduce){
.fig-zone{transition:none}
}
@media (forced-colors: active){
.fig-zone{border-color:ButtonText;background:transparent}
.fig-zone.is-selected{border-color:Highlight;background:transparent}
.fig-focus:focus-visible{outline-color:CanvasText}
}
`

  const ZONE_CSS = BASE_CSS + (IS_JSDOM ? '' : ADVANCED_CSS)

  window.__ModuleLoader__.load({
    id: PACKAGE_NAME,
    factory(require) {
      const React = require('react')
      const h = React.createElement

      const translate = props => (typeof props.t === 'function' ? props.t : key => key)

      async function call(path, options) {
        const response = await fetch(API + path, {
          cache: 'no-store',
          mode: 'cors',
          credentials: 'omit',
          ...options,
          headers: options && options.body ? { 'content-type': 'application/json' } : undefined,
        })
        const payload = await response.json().catch(() => ({}))
        if (!response.ok) throw new Error(payload.error || ('HTTP ' + response.status))
        return payload
      }

      const color = {
        primary: 'var(--dsw-alias-label-primary, #1f2328)',
        secondary: 'var(--dsw-alias-label-secondary, #57606a)',
        tertiary: 'var(--dsw-alias-label-tertiary, #6f7a86)',
        border: 'var(--dsw-alias-border-l1, rgba(127,127,127,.22))',
        hairline: 'var(--dsw-alias-border-l2, rgba(127,127,127,.12))',
        surface: 'var(--dsw-alias-bg-base, #ffffff)',
        raised: 'var(--dsw-alias-bg-l1, rgba(127,127,127,.06))',
        accent: 'var(--dsw-alias-brand-primary, #1c6ea4)',
        danger: 'var(--dsw-alias-state-error-primary, #b42318)',
      }

      const inputStyle = {
        width: 56,
        height: 24,
        padding: '0 6px',
        border: '1px solid ' + color.border,
        borderRadius: 6,
        background: color.surface,
        color: color.primary,
        fontSize: 12,
        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
        fontVariantNumeric: 'tabular-nums',
        textAlign: 'right',
      }

      const rangeStyle = { flex: '1 1 auto', minWidth: 56, accentColor: color.accent }

      function buttonStyle(primary, disabled) {
        if (disabled) {
          return {
            height: 28,
            padding: '0 12px',
            borderRadius: 8,
            border: '1px solid ' + color.hairline,
            background: color.raised,
            color: color.tertiary,
            fontSize: 12,
            fontWeight: 500,
            cursor: 'default',
          }
        }
        return {
          height: 28,
          padding: '0 12px',
          borderRadius: 8,
          border: '1px solid ' + (primary ? 'transparent' : color.border),
          background: primary ? color.accent : 'transparent',
          color: primary ? '#ffffff' : color.primary,
          fontSize: 12,
          fontWeight: 500,
          cursor: 'pointer',
        }
      }

      // ---------------------------------------------------------------- layout

      /**
       * Same layout as make_family_grids.draw_families, in canvas units, from
       * the draft tokens. Returns the block geometry and the gap zones, so the
       * drawing and the click boxes always agree.
       */
      function metaStrip(t, audit, state) {
        if (!state || !state.image) return null
        const marginText = audit
          ? 'T ' + audit.marginPx.top + ' \u00b7 R ' + audit.marginPx.right +
            ' \u00b7 B ' + audit.marginPx.bottom + ' \u00b7 L ' + audit.marginPx.left + ' ' + t('meta.unit')
          : '\u2014'
        const items = [
          [t('meta.size'), state.image.width + ' \u00d7 ' + state.image.height + ' px', false],
          [t('meta.print'), t('meta.printValue').replace('{width}', state.image.printWidthCmAt22_1.toFixed(2)), false],
          [t('meta.margins'), marginText, true],
        ]
        return h('div', {
          style: {
            display: 'grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: '8px 12px',
            padding: '10px 16px 12px',
            borderTop: '1px solid ' + color.hairline,
            borderBottom: '1px solid ' + color.hairline,
          },
        }, items.map(function (entry) {
          return h('div', {
            key: entry[0],
            style: entry[2] ? { gridColumn: '1 / -1' } : undefined,
          },
          h('div', { style: { fontSize: 10, color: color.tertiary, marginBottom: 1 } }, entry[0]),
          h('div', {
            style: {
              fontSize: 11,
              color: color.secondary,
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
              fontVariantNumeric: 'tabular-nums',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            },
            title: entry[0] + ': ' + entry[1],
          }, entry[1]))
        }))
      }

      function TokenRow(props) {
        const { name, value, original, onChange, unitLabel } = props
        const edited = value !== original
        const max = Math.max(64, Math.round((original * 2) / 4) * 4)
        return h('div', {
          style: {
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            minHeight: 28,
            paddingLeft: 10,
          },
        },
        h('span', {
          'aria-hidden': 'true',
          style: {
            position: 'absolute',
            left: 0,
            top: 5,
            bottom: 5,
            width: 2,
            borderRadius: 1,
            background: edited ? color.accent : 'transparent',
          },
        }),
        h('label', {
          htmlFor: 'fig-token-' + name,
          style: {
            width: 76,
            flex: '0 0 76px',
            fontSize: 11,
            color: edited ? color.primary : color.secondary,
            fontWeight: edited ? 500 : 400,
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          },
        }, name),
        h('input', {
          type: 'range',
          className: 'fig-range fig-focus',
          min: RANGE.min,
          max,
          step: RANGE.step,
          value: Math.min(value, max),
          onChange: event => onChange(Number(event.target.value)),
          'aria-label': name,
          'aria-valuetext': value + ' ' + (unitLabel || 'canvas units'),
          style: {
            '--pct': Math.round(((Math.min(value, max) - RANGE.min) / (max - RANGE.min)) * 100) + '%',
            '--fill': edited ? 'var(--dsw-alias-brand-primary,#1c6ea4)' : '#8f99a4',
          },
        }),
        h('input', {
          id: 'fig-token-' + name,
          type: 'number',
          className: 'fig-focus',
          inputMode: 'numeric',
          min: RANGE.min,
          max: 10000,
          step: 1,
          value,
          onChange: event => onChange(Number(event.target.value)),
          'aria-label': name + ' value',
          style: inputStyle,
        }))
      }

      function ZoneOverlay(props) {
        const { zone, width, height, active, hovered, onEnter, onLeave, onPick, label, dim } = props
        const [x, y, w, hgt] = zone.box
        const selected = active === zone.kind
        const linked = hovered === zone.kind
        const className = 'fig-zone' +
          (selected ? ' is-selected' : '') +
          (dim ? ' is-dim' : '') +
          (linked && !selected ? ' is-linked' : '')
        const borderColor = selected
          ? 'var(--dsw-alias-brand-primary,#247bbf)'
          : (linked ? 'var(--dsw-alias-label-secondary,#57606a)' : 'transparent')
        const fill = selected
          ? 'rgba(36,123,191,.14)'
          : (linked ? 'rgba(36,123,191,.08)' : 'transparent')
        return h('div', {
          className,
          tabIndex: -1,
          'aria-hidden': 'true',
          title: label,
          onMouseEnter: onEnter,
          onMouseLeave: onLeave,
          onClick: onPick,
          style: {
            position: 'absolute',
            left: (x / width) * 100 + '%',
            top: (y / height) * 100 + '%',
            width: (w / width) * 100 + '%',
            height: (hgt / height) * 100 + '%',
            padding: 0,
            margin: 0,
            border: '1px solid ' + borderColor,
            background: fill,
            borderRadius: 3,
            cursor: 'pointer',
            pointerEvents: 'auto',
            zIndex: 2,
            transition: 'background-color 100ms ease, border-color 100ms ease, opacity 100ms ease',
          },
        },
        h('span', {
          'aria-hidden': 'true',
          style: { position: 'absolute', top: -4, right: -4, bottom: -4, left: -4 },
        }))
      }

      function FigureBody(props) {
        const t = translate(props)
        const [figure, setFigure] = React.useState('fig1')
        const [state, setState] = React.useState(null)
        const [audit, setAudit] = React.useState(null)
        const [layout, setLayout] = React.useState(null)
        const [quick, setQuick] = React.useState(null)
        const [draft, setDraft] = React.useState({})
        const [activeKind, setActiveKind] = React.useState(null)
        const [hoverKind, setHoverKind] = React.useState(null)
        const [busy, setBusy] = React.useState(false)
        const [error, setError] = React.useState(null)
        const [note, setNote] = React.useState(null)
        const plateRef = React.useRef(null)
        const shellRef = React.useRef(null)
        const [shellWidth, setShellWidth] = React.useState(0)
        const [viewportH, setViewportH] = React.useState(() => {
          const height = typeof window !== 'undefined' ? window.innerHeight : 0
          return height > 0 ? height : 900
        })

        React.useEffect(() => {
          const element = shellRef.current
          if (!element) return undefined
          if (typeof ResizeObserver === 'undefined') {
            setShellWidth(element.clientWidth || 400)
            return undefined
          }
          const observer = new ResizeObserver(entries => {
            const width = entries[0] && entries[0].contentRect ? entries[0].contentRect.width : 0
            setShellWidth(width)
          })
          observer.observe(element)
          const onResize = () => setViewportH(window.innerHeight || 900)
          window.addEventListener('resize', onResize)
          return () => {
            observer.disconnect()
            window.removeEventListener('resize', onResize)
          }
        }, [])

        const load = React.useCallback(async (name) => {
          setBusy(true)
          setError(null)
          setActiveKind(null)
          try {
            let next = await call('/state?figure=' + name)
            if (next.stale) {
              setNote(t('status.rendering'))
              const rendered = await call('/render', {
                method: 'POST',
                body: JSON.stringify({ figure: name }),
              })
              next = rendered.state
              setNote(t('status.rendered'))
            }
            setState(next)
            setDraft({ ...next.tokens })
            const results = await Promise.all([
              call('/audit?figure=' + name),
              call('/layout?figure=' + name),
            ])
            setAudit(results[0])
            setLayout(results[1] && Array.isArray(results[1].zones) ? results[1] : { zones: [] })
            setQuick(null)
          } catch (problem) {
            setError(problem)
          } finally {
            setBusy(false)
          }
        }, [])

        React.useEffect(() => {
          void load(figure)
        }, [figure, load])

        const edited = state
          ? Object.keys(state.tokens).filter(name => draft[name] !== state.tokens[name])
          : []

        // live preview: every draft change asks the Host for a fast SVG
        React.useEffect(() => {
          if (!state) return undefined
          const timer = setTimeout(() => {
            call('/quick', {
              method: 'POST',
              body: JSON.stringify({ figure, tokens: draft }),
            }).then(result => {
              setQuick(result)
              setError(null)
            }).catch(() => {
              // The fast render is optional: keep the sidecar image and its
              // overlays instead of showing a failure banner.
              setQuick(null)
            })
          }, 120)
          return () => clearTimeout(timer)
        }, [draft, figure, state])

        const commit = async (path, body) => {
          setBusy(true)
          setError(null)
          try {
            const result = await call(path, { method: 'POST', body: JSON.stringify(body) })
            setState(result.state)
            setDraft({ ...result.state.tokens })
            const results = await Promise.all([
              call('/audit?figure=' + figure),
              call('/layout?figure=' + figure),
            ])
            setAudit(results[0])
            if (results[1] && Array.isArray(results[1].zones)) setLayout(results[1])
            if (plateRef.current && typeof plateRef.current.scrollIntoView === 'function') {
              plateRef.current.scrollIntoView({ block: 'start' })
            }
            return true
          } catch (problem) {
            setError(problem)
            return false
          } finally {
            setBusy(false)
          }
        }

        const applyTokens = async () => {
          if (!state || edited.length === 0) return
          const tokens = {}
          for (const name of edited) tokens[name] = draft[name]
          if (await commit('/apply', { figure, tokens })) setNote(t('status.applied'))
        }

        const renderOnly = async () => {
          if (await commit('/render', { figure })) setNote(t('status.rendered'))
        }

        const zones = quick ? quick.zones : ((layout && layout.zones) || [])
        const kinds = React.useMemo(() => {
          const byKind = new Map()
          for (const zone of zones) {
            if (!byKind.has(zone.kind)) {
              byKind.set(zone.kind, {
                kind: zone.kind,
                tokens: [],
                count: 0,
                first: zone.box,
              })
            }
            const entry = byKind.get(zone.kind)
            entry.count += 1
          }
          const list = [...byKind.values()]
          list.sort((a, b) => (a.first[1] - b.first[1]) || (a.first[0] - b.first[0]))
          return list
        }, [zones])

        // The tokens each gap kind controls. Kept beside the zone kinds so the
        // sheet always names the spacing the user clicked.
        const KIND_TOKENS = {
          'title-gap': ['TITLE_GAP'],
          'head-gap': ['HEAD_GAP'],
          'panel-gap': ['MGAP'],
          'prompt-gap': ['CELLGAP'],
          'lens-gap': ['LENS_GAP'],
          'row-gap': ['ROWGAP'],
          'family-gap': ['FGAP'],
          'legend-gap': ['LEGEND_GAP'],
          'page-margin': ['MX', 'PAD', 'TAILPAD'],
        }
        for (const entry of kinds) entry.tokens = KIND_TOKENS[entry.kind] || []

        const active = activeKind ? kinds.find(entry => entry.kind === activeKind) : null

        const root = {
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          minHeight: 0,
          background: color.surface,
          color: color.primary,
        }

        const header = h('div', {
          style: { display: 'flex', flexDirection: 'column', gap: 6, padding: '12px 16px 10px' },
        },
        h('select', {
          value: figure,
          className: 'fig-focus',
          onChange: event => setFigure(event.target.value),
          'aria-label': t('figure.label'),
          title: t('figure.label'),
          style: {
            width: shellWidth >= 860 ? 320 : '100%',
            height: 28,
            borderRadius: 8,
            border: '1px solid ' + color.border,
            background: color.surface,
            color: color.primary,
            fontSize: 12,
            padding: '0 8px',
          },
        },
        h('option', { value: 'fig1' }, t('figure.fig1')),
        h('option', { value: 'fig2' }, t('figure.fig2'))),
        h('div', {
          style: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: color.tertiary },
        },
        h('span', {
          'aria-hidden': 'true',
          style: {
            width: 6,
            height: 6,
            borderRadius: 3,
            background: edited.length ? color.accent : color.hairline,
          },
        }),
        h('span', {
          style: { color: edited.length ? color.secondary : color.tertiary, fontVariantNumeric: 'tabular-nums' },
        }, edited.length ? edited.length + ' ' + t('status.edited') : t('status.saved')),
        h('span', { style: { flex: '1 1 auto' } }),
        quick
          ? h('span', {}, t('status.preview') + ' \u00b7 ' + zones.length)
          : (zones.length
            ? h('span', {}, zones.length + ' ' + t('kind.places'))
            : (state ? h('span', {}, t('status.noGaps')) : null))))

        const wide = shellWidth >= 860
        const previewH = wide
          ? Math.max(420, Math.min(800, viewportH - 220))
          : Math.max(220, Math.min(420, viewportH * 0.40))
        const columnW = wide
          ? Math.max(320, shellWidth - 420 - 40)
          : Math.max(240, shellWidth - 32)
        const scale = quick ? Math.min(columnW / quick.W, previewH / quick.H) : 1
        const innerW = quick ? Math.max(120, quick.W * scale) : 0
        const innerH = quick ? quick.H * scale : 0

        const imageWidth = (layout && layout.image && layout.image.width) ||
          (state && state.image && state.image.width) || 1
        const imageHeight = (layout && layout.image && layout.image.height) ||
          (state && state.image && state.image.height) || 1
        const fallbackScale = Math.min(columnW / imageWidth, previewH / imageHeight)
        const fallbackW = Math.max(120, imageWidth * fallbackScale)
        const fallbackH = imageHeight * fallbackScale
        const zoneViews = (boxW, boxH) => zones.map(zone => h(ZoneOverlay, {
          key: zone.kind + ':' + zone.box.join(','),
          zone,
          width: boxW,
          height: boxH,
          active: activeKind,
          hovered: hoverKind,
          label: t('kind.' + zone.kind) || zone.kind,
          dim: Boolean(activeKind) && activeKind !== zone.kind,
          onEnter: () => setHoverKind(zone.kind),
          onLeave: () => setHoverKind(null),
          onPick: () => setActiveKind(current => (current === zone.kind ? null : zone.kind)),
        }))

        const plate = state && (quick || state.image)
          ? h('div', {
            ref: plateRef,
            style: {
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'flex-start',
              flex: '0 0 auto',
              margin: wide ? 0 : '0 16px',
              borderRadius: 8,
              border: '1px solid ' + color.hairline,
              background: '#ffffff',
              overflow: 'hidden',
            },
          },
          quick
            ? h('div', {
              style: { position: 'relative', width: innerW, height: innerH, flex: '0 0 auto' },
            },
            h('div', {
              'aria-label': t('preview.alt'),
              role: 'img',
              style: { width: '100%', height: '100%', lineHeight: 0, pointerEvents: 'none' },
              dangerouslySetInnerHTML: { __html: quick.svg },
            }),
            zoneViews(quick.W, quick.H),
            h('a', {
              className: 'fig-focus',
              href: API + '/figure.png?figure=' + figure + '&t=' + Date.now(),
              target: '_blank',
              rel: 'noreferrer',
              style: {
                position: 'absolute',
                right: 6,
                bottom: 6,
                fontSize: 10,
                color: color.secondary,
                background: 'rgba(255,255,255,.92)',
                border: '1px solid ' + color.hairline,
                borderRadius: 6,
                padding: '2px 6px',
                textDecoration: 'none',
              },
            }, t('meta.open')))
            : h('div', {
              key: 'preview-' + figure,
              style: { position: 'relative', width: fallbackW, height: fallbackH, flex: '0 0 auto', lineHeight: 0 },
            },
            h('img', {
              src: API + '/figure.png?figure=' + figure,
              alt: t('preview.alt'),
              style: { display: 'block', width: '100%', height: '100%', objectFit: 'contain' },
            }),
            zoneViews(imageWidth, imageHeight)))
          : h('div', {
            role: 'status',
            style: {
              display: 'grid',
              placeItems: 'center',
              minHeight: 160,
              margin: wide ? 0 : '0 16px',
              borderRadius: 8,
              border: '1px solid ' + color.hairline,
              background: '#f7f8f9',
              color: color.tertiary,
              fontSize: 12,
            },
          }, error ? t('status.offline') : t('status.loading'))

        const chips = kinds.length
          ? h('div', {
            role: 'group',
            'aria-label': t('chips.label'),
            style: { display: 'flex', flexWrap: 'wrap', gap: 6, padding: wide ? '8px 0 2px' : '8px 16px 2px' },
          }, kinds.map(entry => {
            const selected = activeKind === entry.kind
            return h('button', {
              key: entry.kind,
              type: 'button',
              className: 'fig-focus',
              'aria-pressed': selected,
              onClick: () => setActiveKind(current => (current === entry.kind ? null : entry.kind)),
              onMouseEnter: () => setHoverKind(entry.kind),
              onMouseLeave: () => setHoverKind(null),
              title: t('kind.' + entry.kind) || entry.kind,
              style: {
                minHeight: 28,
                padding: '0 10px',
                borderRadius: 14,
                border: '1px solid ' + (selected ? color.accent : '#7d8792'),
                background: selected ? 'rgba(36, 123, 191, .10)' : color.surface,
                color: selected ? color.primary : color.secondary,
                fontSize: 11,
                whiteSpace: 'nowrap',
                cursor: 'pointer',
              },
            }, (t('kind.' + entry.kind) || entry.kind) + ' \u00b7 ' + entry.count)
          }))
          : null

        const hint = kinds.length && !activeKind
          ? h('p', { style: { margin: wide ? '4px 0 0' : '4px 16px 0', fontSize: 10, color: color.tertiary, lineHeight: '15px' } },
            t('hint.pick'))
          : null

        const panelHead = active
          ? h('div', {
            style: { display: 'flex', alignItems: 'baseline', gap: 8, margin: '14px 0 2px', padding: '0 16px' },
          },
          h('h2', { style: { margin: 0, fontSize: 12, fontWeight: 500, color: color.primary } },
            t('kind.' + active.kind) || active.kind),
          h('span', { style: { fontSize: 10, color: color.tertiary } },
            active.count + ' ' + t('kind.places') + ' \u00b7 ' + active.tokens.length + ' ' +
            (active.tokens.length === 1 ? t('kind.token') : t('kind.tokens'))),
          h('span', { style: { flex: '1 1 auto' } }),
          h('button', {
            type: 'button',
            className: 'fig-focus',
            onClick: () => setActiveKind(null),
            style: {
              padding: 0, border: 0, background: 'transparent',
              color: color.secondary, fontSize: 10, cursor: 'pointer',
              textDecoration: 'underline', textUnderlineOffset: 2,
            },
          }, t('action.all')))
          : null

        const tokenPanel = active
          ? h('section', { style: { padding: '0 16px 4px' } },
            active.tokens
              .filter(name => state && Object.prototype.hasOwnProperty.call(state.tokens, name))
              .map(name => h(TokenRow, {
                key: name,
                name,
                value: draft[name],
                original: state.tokens[name],
                unitLabel: t('value.unit'),
                onChange: value => setDraft(current => ({ ...current, [name]: value })),
              })))
          : kinds.map(entry => {
            const rows = entry.tokens
              .filter(name => state && Object.prototype.hasOwnProperty.call(state.tokens, name))
              .map(name => h(TokenRow, {
                key: name,
                name,
                value: draft[name],
                original: state.tokens[name],
                unitLabel: t('value.unit'),
                onChange: value => setDraft(current => ({ ...current, [name]: value })),
              }))
            if (!rows.length) return null
            return h('section', { key: entry.kind, style: { padding: '0 16px' } },
            h('h2', {
              style: { margin: '16px 0 4px', fontSize: 12, fontWeight: 500, color: color.secondary },
            }, t('kind.' + entry.kind) || entry.kind),
            rows)
          })

        const footer = h('div', {
          style: {
            display: 'flex', gap: 8, alignItems: 'center',
            padding: '8px 16px 12px',
            borderTop: '1px solid ' + color.hairline,
            background: color.surface,
            flex: '0 0 auto',
          },
        },
        h('button', {
          type: 'button', className: 'fig-focus', onClick: applyTokens,
          disabled: busy || edited.length === 0,
          style: buttonStyle(true, busy || edited.length === 0),
        }, t('action.apply')),
        h('button', {
          type: 'button', className: 'fig-focus', onClick: renderOnly, disabled: busy,
          style: buttonStyle(false, busy),
        }, t('action.render')),
        h('span', { style: { flex: '1 1 auto' } }),
        h('button', {
          type: 'button',
          className: 'fig-focus',
          onClick: () => setDraft(state ? { ...state.tokens } : {}),
          disabled: busy || edited.length === 0,
          style: buttonStyle(false, busy || edited.length === 0),
        }, t('action.reset')))

        const statusLines = [
          error
            ? h('p', { key: 'err', role: 'alert', style: { margin: '6px 16px 0', fontSize: 12, color: color.danger } },
              t('error.prefix') + ': ' + (error.message || String(error)))
            : null,
          note
            ? h('p', { key: 'note', role: 'status', style: { margin: '6px 16px 0', fontSize: 12, color: color.secondary } }, note)
            : null,
        ]

        const content = wide
          ? h('div', {
            style: { flex: '1 1 auto', minHeight: 0, display: 'flex', alignItems: 'stretch' },
          },
          h('div', {
            style: { flex: '1 1 auto', minWidth: 0, overflowY: 'auto', padding: '0 16px', display: 'flex', flexDirection: 'column' },
          },
          h('div', {
            style: { flex: '1 1 auto', minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '8px 0' },
          }, plate),
          chips,
          hint),
          h('div', {
            style: {
              flex: '0 0 420px',
              width: 420,
              minWidth: 320,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              borderLeft: '1px solid ' + color.hairline,
              paddingBottom: 8,
            },
          },
          active ? h('div', {}, panelHead, tokenPanel) : tokenPanel,
          h('div', { style: { marginTop: 'auto' } },
            metaStrip(t, audit, state),
            statusLines)))
          : h('div', {
            style: { flex: '1 1 auto', minHeight: 0, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 },
          },
          plate,
          chips,
          hint,
          metaStrip(t, audit, state),
          active
            ? h('div', {
              style: {
                position: 'sticky', bottom: 0, zIndex: 2, margin: '10px 0 0', padding: '2px 0 8px',
                background: color.surface, borderTop: '1px solid ' + color.border,
              },
            }, panelHead, tokenPanel)
            : tokenPanel,
          statusLines)

        return h('div', {
          ref: shellRef,
          style: root,
          role: 'region',
          'aria-label': t('tab.title'),
          'data-fig-layout': 'body',
        },
        h('style', null, ZONE_CSS),
        h('h1', {
          style: {
            position: 'absolute', width: 1, height: 1, overflow: 'hidden',
            clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap', margin: -1,
          },
        }, t('tab.title')),
        header,
        content,
        footer)
      }

      function FigureGlyph(props) {
        const size = props && typeof props.size === 'number' ? props.size : 16
        return h('svg', {
          width: size, height: size, viewBox: '0 0 16 16', fill: 'none',
          stroke: 'currentColor', strokeWidth: 1.2, 'aria-hidden': 'true',
          focusable: 'false', style: { flex: '0 0 auto' },
        },
        h('rect', { x: 1.5, y: 3, width: 13, height: 10, rx: 1.5 }),
        h('path', { d: 'M5.5 6h2.2M8.3 9.9h2.2' }))
      }

      function FigureTitle(props) {
        const t = translate(props)
        return h('span', { style: { display: 'inline-flex', alignItems: 'center', gap: 6 } },
        h(FigureGlyph, { size: 14 }),
        t('tab.title'))
      }

      return {
        name: PACKAGE_NAME,
        inject: ['slots', 'locale', 'sidebarRight', 'sidebarRightTabs'],
        apply(ctx) {
          const t = ctx.locale.bind(NS)

          ctx.effect(() => ctx.locale.register(NS, { en, zh }), 'fig-layout: copy')

          ctx.effect(() => ctx.sidebarRightTabs.register({
            id: PACKAGE_NAME,
            kind: KIND,
            priority: 'extension',
            title: () => t('tab.title'),
            guide: [{
              id: 'open',
              order: 70,
              title: () => t('guide.title'),
              description: () => t('guide.description'),
              icon: FigureGlyph,
            }],
          }), 'fig-layout: tab type')

          // Free the right Sidebar of conversations that are not on screen. The
          // tab is only opened from the guide now, so leftover tabs from earlier
          // versions should not keep occupying other sessions.
          ctx.effect(() => {
            const timer = setTimeout(() => {
              let mounted
              let tabs
              try {
                mounted = ctx.sidebarRight.mounted.getSnapshot()
                tabs = ctx.sidebarRight.openTabs.getSnapshot()
              } catch {
                return
              }
              if (!mounted) return
              for (const tab of tabs) {
                if (tab.kind !== KIND || tab.sessionId === mounted) continue
                try {
                  ctx.sidebarRight.closeIn(tab.sessionId, tab.tabId)
                } catch {
                  /* the other Sidebar may already be gone */
                }
              }
            }, 0)
            return () => clearTimeout(timer)
          }, 'fig-layout: close tabs in other sessions')

          ctx.effect(() => ctx.slots.inject('sidebar.right.pane.tab', () => ctx.slots.register({
            name: 'sidebar.right.pane.tab',
            key: PACKAGE_NAME,
            locale: NS,
          }, FigureBody)), 'fig-layout: tab body')

          ctx.effect(() => ctx.slots.inject('sidebar.right.pane.tab.title', () => ctx.slots.register({
            name: 'sidebar.right.pane.tab.title',
            key: PACKAGE_NAME,
            locale: NS,
          }, FigureTitle)), 'fig-layout: tab title')

          ctx.effect(() => () => {
            let tabs
            try {
              tabs = ctx.sidebarRight.openTabs.getSnapshot()
            } catch {
              return
            }
            for (const tab of tabs) {
              if (tab.kind !== KIND) continue
              try {
                ctx.sidebarRight.closeIn(tab.sessionId, tab.tabId)
              } catch {
                /* the Sidebar may be gone during a profile unload */
              }
            }
          }, 'fig-layout: teardown')
        },
      }
    },
  })
})()
