/**
 * Browser half of the jspace dashboard bundle.
 *
 * A resident right-Sidebar tab that embeds the live jspace lens-experiment
 * dashboard page served at http://127.0.0.1:8904/. The page keeps itself
 * current: it carries `<meta http-equiv="refresh" content="30">`, so the tab
 * only embeds it and never reads or copies its numbers.
 *
 * Liveness: before showing the page the tab probes the same origin with a
 * cheap cross-origin HEAD request (BaseHTTPRequestHandler answers 501 without
 * rendering the dashboard, so the probe costs the service nothing). While the
 * service answers, the iframe is mounted; when the probe fails the iframe is
 * unmounted and one line of status text replaces it, so a dead service never
 * leaves stale numbers on screen. The probe repeats while the body is mounted.
 *
 * The tab type is registered through the public two-stage right-Sidebar path:
 * `sidebarRightTabs.register` for the type, then keyed entries in
 * `sidebar.right.pane.tab` (body) and `sidebar.right.pane.tab.title` (chip).
 * `sidebarRight.mounted` opens the tab only while the one Session this page
 * belongs to is on screen, and an effect disposer closes exactly this plugin's
 * tabs on unload.
 */
;(() => {
  'use strict'

  /** Package identity: the browser module id and the tab type's keyed Slot key. */
  const PACKAGE_NAME = '@dsh-local/view-51901211-6038-40f3-8878-edd2998f1732'

  /** Tab-type discriminator and locale dictionary namespace. */
  const KIND = 'jspace-dashboard'
  const NS = 'jspaceDashboard'

  /** The dashboard the tab embeds; the page refreshes itself every 30 seconds. */
  const PAGE_URL = 'http://127.0.0.1:8904/?embed=1'

  /**
   * The Session this page belongs to. The tab is opened only while that Session is the one on
   * screen: a personalized page is Session-bound, and opening it beside every conversation takes
   * over their right Sidebar. Everywhere else it stays reachable from the Sidebar's tab menu.
   */
  const OWNER_SESSION_ID = 'session-889466f5-5ec2-49e6-887f-2b1b54ac5089'

  /** A probe that has not answered by now counts as an unavailable service. */
  const PROBE_TIMEOUT_MS = 3000

  /** Probe cadence: the page's own refresh rhythm while up, a faster retry while down. */
  const ONLINE_POLL_MS = 30000
  const OFFLINE_POLL_MS = 10000

  /**
   * The page refreshes itself (every 60 s in embed mode) and keeps the scroll position, so a timed
   * remount is counter-productive: only remount when a probe brings a dead service back.
   */
  const REMOUNT_EVERY_TICKS = 0

  /** Cell-counter feed: /progress.json answers CORS, so the tab title can show 114/135. */
  const PROGRESS_URL = 'http://127.0.0.1:8904/progress.json'

  /** Chip cadence; the embedded page refreshes itself every 60 s. */
  const CELLS_POLL_MS = 20000

  /** Tiny store shared by the poller and the Slot-rendered title. */
  const cells = { text: '', listeners: new Set() }

  function setCells(text) {
    if (cells.text === text) return
    cells.text = text
    for (const fn of Array.from(cells.listeners)) {
      try { fn(text) } catch (error) { /* a stale title render must not break the poller */ }
    }
  }

  async function pollCells() {
    try {
      const res = await fetch(PROGRESS_URL, { cache: 'no-store', credentials: 'omit' })
      if (!res.ok) return
      const data = await res.json()
      setCells(typeof data.cells === 'number' && typeof data.target === 'number'
        ? `${data.cells}/${data.target}` : '')
    } catch (error) {
      /* keep the last good value */
    }
  }

  /** Subscribe a title render to the counter and poll while it is mounted. */
  function useCells() {
    const [text, setText] = React.useState(cells.text)
    React.useEffect(() => {
      cells.listeners.add(setText)
      setText(cells.text)
      void pollCells()
      const timer = setInterval(() => { void pollCells() }, CELLS_POLL_MS)
      return () => {
        clearInterval(timer)
        cells.listeners.delete(setText)
      }
    }, [])
    return text
  }

  /**
   * Liveness probe options. `no-cors` makes a cross-origin HEAD a simple
   * request (no CORS contract, no preflight); a resolved fetch means the
   * service answered at all, whatever the status code.
   */
  const PROBE_OPTIONS = {
    method: 'HEAD',
    mode: 'no-cors',
    cache: 'no-store',
    credentials: 'omit',
    redirect: 'follow',
  }

  /** Copy; every visible string goes through the Client locale service. */
  const en = {
    'tab.title': 'jspace',
    'guide.title': 'jspace dashboard',
    'guide.description': 'Embeds the live lens-experiment dashboard served on port 8904.',
    'frame.title': 'jspace lens-experiment dashboard',
    'status.offline': '8904 is not running',
  }

  const zh = {
    'tab.title': 'jspace',
    'guide.title': 'jspace 仪表盘',
    'guide.description': '内嵌 8904 上运行的透镜实验仪表盘。',
    'frame.title': 'jspace 透镜实验仪表盘',
    'status.offline': '8904 端口未运行，每 10 秒自动重试。',
  }

  window.__ModuleLoader__.load({
    id: PACKAGE_NAME,
    factory(require) {
      const React = require('react')
      const h = React.createElement

      /** Translate through the synthesized Slot seat, with a harmless fallback. */
      const translate = props => (typeof props.t === 'function' ? props.t : key => key)

      /**
       * The tab's glyph: a lens ring with an aperture dot. Drawn inline so the
       * Client bundle needs no Harness primitives module.
       * @param props - optional `size` in pixels; `marginRight` spaces it in a
       * tab chip. Inherits `currentColor`.
       */
      function LensGlyph(props) {
        const size = props !== null && typeof props === 'object' && typeof props.size === 'number' ? props.size : 16
        const spaced = props !== null && typeof props === 'object' && props.marginRight === true
        return h('svg', {
          width: size,
          height: size,
          viewBox: '0 0 16 16',
          fill: 'none',
          stroke: 'currentColor',
          strokeWidth: 1.3,
          strokeLinecap: 'round',
          'aria-hidden': 'true',
          focusable: 'false',
          style: { flex: '0 0 auto', marginRight: spaced ? 4 : 0 },
        },
        h('circle', { cx: 8, cy: 8, r: 5.6 }),
        h('circle', { cx: 8, cy: 8, r: 2.1 }),
        h('path', { d: 'M8 0.9v2.2M8 12.9v2.2M0.9 8h2.2M12.9 8h2.2' }))
      }

      /**
       * Ask once whether the dashboard service answers. A connection refusal,
       * a blocked request, or an aborted (timed-out) probe counts as
       * unavailable; any HTTP answer counts as available.
       * @param signal - aborted on timeout or when the body unmounts.
       * @returns whether the service answered.
       */
      async function probeService(signal) {
        try {
          await fetch(PAGE_URL, { ...PROBE_OPTIONS, signal })
          return true
        } catch (error) {
          return false
        }
      }

      /** Tab body: the embedded page, or one status line while the service is down. */
      function DashboardBody(props) {
        const t = translate(props)
        const [view, setView] = React.useState({ status: 'checking', epoch: 0 })
        const ticks = React.useRef(0)

        React.useEffect(() => {
          let disposed = false
          let timer
          let inFlight

          const tick = async () => {
            timer = undefined
            if (disposed) return
            const controller = new AbortController()
            inFlight = controller
            const timeout = setTimeout(() => { controller.abort() }, PROBE_TIMEOUT_MS)
            const alive = await probeService(controller.signal)
            clearTimeout(timeout)
            if (inFlight === controller) inFlight = undefined
            if (disposed) return
            setView(current => {
              const status = alive ? 'online' : 'offline'
              if (!alive) return current.status === 'offline' ? current : { status, epoch: current.epoch }
              ticks.current += 1
              const forceRemount = REMOUNT_EVERY_TICKS > 0 && ticks.current % REMOUNT_EVERY_TICKS === 0
              if (current.status === 'online' && !forceRemount) return current
              // A fresh epoch remounts the iframe: on recovery, and periodically as a safety net.
              return { status, epoch: current.epoch + 1 }
            })
            timer = setTimeout(tick, alive ? ONLINE_POLL_MS : OFFLINE_POLL_MS)
          }

          void tick()
          return () => {
            disposed = true
            if (timer !== undefined) clearTimeout(timer)
            timer = undefined
            if (inFlight !== undefined) inFlight.abort()
            inFlight = undefined
          }
        }, [])

        const root = {
          display: 'flex',
          flex: '1 1 auto',
          flexDirection: 'column',
          height: '100%',
          minHeight: 0,
          background: 'var(--dsw-alias-bg-base)',
        }

        if (view.status === 'online') {
          return h('div', { style: root, 'data-jspace-dashboard': 'page' },
            h('iframe', {
              key: `jspace-frame-${view.epoch}`,
              src: PAGE_URL,
              title: t('frame.title'),
              referrerPolicy: 'no-referrer',
              sandbox: 'allow-scripts allow-same-origin',
              'data-jspace-dashboard-frame': '',
              style: {
                display: 'block',
                flex: '1 1 auto',
                width: '100%',
                height: '100%',
                minHeight: 0,
                border: 0,
                background: 'var(--dsw-alias-bg-base)',
              },
            }))
        }

        return h('div', {
          style: { ...root, alignItems: 'center', justifyContent: 'center' },
          'data-jspace-dashboard': view.status,
        },
        view.status === 'offline'
          ? h('p', {
            role: 'status',
            'aria-live': 'polite',
            style: {
              margin: 0,
              padding: '0 16px',
              color: 'var(--dsw-alias-label-tertiary)',
              fontSize: 12,
              lineHeight: '18px',
              textAlign: 'center',
            },
          }, t('status.offline'))
          : null)
      }

      /** The tab chip: the lens glyph beside the dashboard's name. */
      function DashboardTitle(props) {
        const t = translate(props)
        const count = useCells()
        return h(React.Fragment, null, h(LensGlyph, { size: 14, marginRight: true }),
          count ? `${t('tab.title')} ${count}` : t('tab.title'))
      }

      /**
       * Keep the dashboard tab present beside the on-screen Session.
       *
       * The open needs the arriving Session's Sidebar surface, which the seat
       * mints during the render that follows `sidebarRight.mounted`; a failed
       * attempt is retried with a short backoff instead of spinning, and the
       * attempt budget resets whenever the Session changes.
       * @param ctx - Client context carrying the right-Sidebar faces.
       * @returns an idempotent stop function.
       */
      function followSessions(ctx) {
        let timer
        let attempt = 0
        let stopped = false

        const cancel = () => {
          if (timer !== undefined) clearTimeout(timer)
          timer = undefined
        }

        const run = () => {
          timer = undefined
          if (stopped) return
          const sessionId = ctx.sidebarRight.mounted.getSnapshot()
          // A personalized page is bound to one Session. Open the tab only while that Session is
          // the one on screen; in any other conversation it stays available from the Sidebar's own
          // tab menu, and the right Sidebar there belongs to that conversation.
          if (sessionId !== OWNER_SESSION_ID) {
            attempt = 0
            return
          }
          const present = ctx.sidebarRight.openTabs.getSnapshot()
            .some(tab => tab.sessionId === sessionId && tab.kind === KIND)
          if (present) {
            attempt = 0
            return
          }
          try {
            ctx.sidebarRight.openTab(KIND)
            attempt = 0
          } catch (error) {
            attempt += 1
            if (attempt <= 8) {
              timer = setTimeout(run, 200 * attempt)
              return
            }
            console.warn(`[jspace-dashboard] could not open the dashboard tab: ${String(error)}`)
          }
        }

        const schedule = () => {
          if (stopped) return
          attempt = 0
          cancel()
          timer = setTimeout(run, 0)
        }

        const unsubscribe = ctx.sidebarRight.mounted.subscribe(schedule)
        schedule()

        return () => {
          if (stopped) return
          stopped = true
          unsubscribe()
          cancel()
        }
      }

      return {
        name: PACKAGE_NAME,
        inject: ['slots', 'locale', 'sidebarRight', 'sidebarRightTabs'],
        apply(ctx) {
          const t = ctx.locale.bind(NS)
          let stopFollow = () => {}

          ctx.effect(() => ctx.locale.register(NS, { en, zh }), 'jspace-dashboard: copy')

          ctx.effect(() => ctx.sidebarRightTabs.register({
            id: PACKAGE_NAME,
            kind: KIND,
            priority: 'extension',
            title: () => t('tab.title'),
            guide: [{
              id: 'open',
              order: 60,
              title: () => t('guide.title'),
              description: () => t('guide.description'),
              icon: LensGlyph,
            }],
          }), 'jspace-dashboard: tab type')

          ctx.effect(() => {
            stopFollow = followSessions(ctx)
            return () => { stopFollow() }
          }, 'jspace-dashboard: resident tab')

          ctx.effect(() => ctx.slots.inject('sidebar.right.pane.tab', () => ctx.slots.register({
            name: 'sidebar.right.pane.tab',
            key: PACKAGE_NAME,
            locale: NS,
          }, DashboardBody)), 'jspace-dashboard: tab body')

          ctx.effect(() => ctx.slots.inject('sidebar.right.pane.tab.title', () => ctx.slots.register({
            name: 'sidebar.right.pane.tab.title',
            key: PACKAGE_NAME,
            locale: NS,
          }, DashboardTitle)), 'jspace-dashboard: tab title')

          // Registered last, so it unloads first: stop following, then close
          // only this plugin's tabs. Matching by kind leaves the guide and any
          // unrelated tab untouched. The faces may already be gone while a
          // whole profile unloads, so nothing here may throw.
          ctx.effect(() => () => {
            stopFollow()
            let tabs
            try {
              tabs = ctx.sidebarRight.openTabs.getSnapshot()
            } catch (error) {
              console.warn(`[jspace-dashboard] left its tabs for the removed Sidebar: ${String(error)}`)
              return
            }
            for (const tab of tabs) {
              if (tab.kind !== KIND) continue
              try {
                ctx.sidebarRight.closeIn(tab.sessionId, tab.tabId)
              } catch (error) {
                console.warn(`[jspace-dashboard] could not close its tab on unload: ${String(error)}`)
              }
            }
          }, 'jspace-dashboard: teardown')
        },
      }
    },
  })
})()
