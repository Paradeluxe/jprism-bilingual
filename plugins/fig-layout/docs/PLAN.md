# Plan

## Done

- Research: mpltweak is the closest prior art (drag matplotlib layout, write
  numbers back into code); FigureForge edits a live figure object; Inkscape-style
  tools edit exported artwork only. Notes in `docs/RESEARCH.md`.
- Host plugin `@local/dsh-fig-layout` installed and active.
  - Tools: `fig_spacing_read`, `fig_spacing_apply`, `fig_spacing_audit`.
  - Loopback service on `127.0.0.1:8829` with `GET /state`, `GET /figure.png`,
    `GET /audit`, `POST /apply`, `POST /render`.
  - Verified: state and audit return real measurements (96 px margins on all
    four sides of Figure 1); `POST /apply` changed `TITLE_GAP` 24 -> 28,
    re-rendered, and the revert restored 24 with the same pixel size.

## Next

1. (done) Client module (`client.js`): register a right-sidebar tab type and body.
   - Sliders/steppers for each token returned by `/state`.
   - Live PNG from `/figure.png` with a cache-busting query.
   - Apply / render buttons calling `POST /apply` and `POST /render`.
   - Show `/audit` margins next to the token values.
2. Add `dsh.client` to `package.json` and the `./client` export; reinstall and
   verify the tab opens from the sidebar guide and applies a change.
3. Optional: per-token groups by section (page margin, titles, panels, prompt
   groups, legend) with a reset-to-rendered-defaults action.

## Verified

- Host: real HTTP round-trip on 8829 (state, audit, apply 24 -> 28 -> 24).
- Client: jsdom render with real React, one edit (MGAP 48 -> 56) reached
  POST /apply with the right body and the UI reported the result.
- Visual: headless Edge screenshot of the real component
  (docs/editor-preview.png).
- In-app tab: registration mirrors the shipped jspace-dashboard sidebar-tab
  plugin; the tab needs one page reload because the web print URL credential is
  never exposed to the agent, so the running browser cannot be driven from here.

## UI/UX pass (unslop)

Direction: a quiet measuring console for a drafting table. The plate preview is
the one rich element; every control around it is neutral, mono where it carries
numbers, and the accent appears only on the primary action and on tokens whose
value differs from the saved render.

Audit and fixes:
- meta read as one run-on sentence with two units -> three labelled stats
  (size, print width at 22.1 cm, margins T/R/B/L), each with mono figures and no
  truncation.
- twenty identical blue sliders read as a wall -> slider chrome is neutral; only
  edited rows keep the accent, plus a 2px left rule and a heavier label.
- header status floated outside the panel at narrow widths -> the select gets
  its own row, status and the unit hint sit on a second row.
- disabled primary looked like a pastel button -> disabled controls use the
  raised surface and muted text; the accent is reserved for the enabled action.
- preview had no way out -> an Open PNG affordance on the plate card.
- copy: Apply and render -> Apply (the action re-renders by definition),
  No edits -> Saved, and group labels name their contents.

## Interaction pass: click a gap

The controls now start from the plate, not from a list of tokens.

- The generator exports a zone sidecar (`*.layout.json`) with one box per
  spacing zone, in the same canvas coordinates the plate is drawn with. The Host
  serves it on `/layout`; the client maps boxes to percentages of the natural
  image, so overlays stay on their gaps at any sidebar width.
- Clicking a zone selects every zone of that kind, dims unrelated kinds, and
  narrows the controls to that spacing's tokens in a sticky sheet above the
  footer. The chip row wraps and is ordered by where each kind first appears on
  the plate.
- Verified with jsdom: clicking a checkpoint gap narrows to `MGAP` only,
  `All tokens` restores the full list, and an edit still posts the right body.

## Gap-only pass

- Every exported zone is now an empty band: `TITLE_GAP`, `HEAD_GAP`, `MGAP`,
  `LENS_GAP`, `CELLGAP`, `ROWGAP`, `FGAP`, `LEGEND_GAP` and the page edge.
  Content zones (titles, label columns, tick rows, legend block) were removed,
  so clicking text no longer selects anything.
- The default control list is the set of gap kinds from the zone map, each with
  exactly the token that names it. **All gaps** clears a selection.
- The tab renders once on open when the source is newer than the saved PNG, and
  after Apply it scrolls the plate back into view, so the preview is visible
  after a change.

## Live preview pass

- The Host exposes `POST /quick`, which runs a lightweight SVG layout
  (`tools/fig-test/quick_svg.py`) in about 0.2 s instead of the 13.5 s matplotlib
  render. It returns the SVG and the gap zones for the same tokens.
- The tab calls it on every draft change (120 ms debounce) and swaps the SVG, so
  the plate moves without pressing Apply. The header shows `Live preview`.
- The preview figure is the isolated test copy; the working figure in
  `experiment/figures` is untouched.
- Verified in a headless browser against the real Host: two `POST /quick` calls
  (initial and after a simulated slider move to MGAP 72), SVG present, input
  value kept, no console error. Host timing via curl: 0.22 s.

## Layout and sidebar pass

- Automatic opening was removed. The tab is only added from the Sidebar guide,
  so it no longer takes over the right Sidebar of other conversations.
- Wide panes use two columns: plate on the left, controls in a 420 px column,
  measurements pinned to its bottom. Narrow panes stack and keep the preview at
  40% of the window height.
- The plate is sized from the measured pane width and window height, so the SVG
  is never clipped by its default 150 px height.

## Hover box restored

- The gap boxes are driven by CSS :hover and an is-linked class instead of
  React enter state, so hovering a narrow gap reliably outlines all gaps of its
  kind. A 4 px child expands the hit area.
- Verified with a real CDP mouse move in headless Edge: the six checkpoint gaps
  all draw a box on hover (docs/hover-preview.png).

## Web design guide pass

- Slider: native input, custom WebKit/Firefox track and thumb, filled part via
  `--pct`, quiet grey fill until a row is edited, 2px focus-visible outline.
- Semantics: hidden `h1`, `h2` group headings, labelled region, chip group with
  `aria-pressed`, status/alert live regions, localised `aria-valuetext`.
- Keyboard: 102 gap overlays are `tabIndex=-1` and `aria-hidden`; chips are the
  keyboard path, so tab order stays short.
- Colour: darker accent for white text, tertiary text darkened to 4.5:1,
  28px chip targets with a 3:1 border, dark and forced-colours rules.
- Verified with a CDP probe: 102 zones, 0 focusable, 9 pressed-capable chips,
  10 ranges, `aria-valuetext` present, first Tab lands on the plate select with a
  2px outline.

## Fallback overlay fix and tests

- Root cause found: the img fallback branch never rendered ZoneOverlay, so any
  /quick failure removed every hover and click target while the PNG still
  showed. The image also shrank to a 2px plate height inside the flex column.
- Fix: fit the fallback image to columnW x previewH, mark the plate
  lex: 0 0 auto, and render the sidecar zones over it. /quick failures are
  silent and the count label falls back to N places.
- Tests: check.mjs now runs in both modes. QUICK_FAIL=1 asserts the static
  image plus zones and still applies MGAP; normal mode asserts the SVG.
- Real-browser CDP hover: normal 6 linked, border rgb(87,96,106); fallback
  6 linked at 102 zones with the fitted image visible.
