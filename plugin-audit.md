# DSH desktop profile — third-party UI plugin audit (read-only)

Profile: `C:\Users\User\.dsh\profiles\desktop` — enabled bundles are the `dsh.profile.bundles` array in
`C:\Users\User\.dsh\profiles\desktop\package.json:20-43`. The two disabled packages are listed as dependencies
(`package.json:4-17`) but absent from that array, so their rows are never inserted.

Method: opened each `package.json`, `cordis.patch.yml`, locale files and the browser half; searched for slot-name
string literals, `slots.register`, `documentPreviews.register`, `sidebarRightTabs.register`, `settings.section`,
`document.head` / `document.body` / `createPortal` / `addEventListener` / `MutationObserver`. Official baseline was
read from the shipped app package (read-only extract of `D:\Software\DSH_desktop\resources\app.asar`; the workspace
copy of the two official client files is under `.audit\official\`). No plugin file was modified.

Slot seats referenced below are the ones named in the task; absent seats (`sidebar.panellist`, `sidebar.footer.action`,
`settings.plugins.tab`, `deliverables.file.actions`, `conversation.input.right`) have **no** third-party occupant and
are omitted from per-plugin tables.

---

## 1. @local/dsh-docx-preview v1.0.0

Directory: `E:\hermes_playground\paper-writing\plugins\dsh-docx-preview`
Client entry: `client.js` (78 KB); host half `index.js`.

| Seat | Key / id | order | Visible label (zh) | Citation |
|---|---|---|---|---|
| `sidebar.right.tab.document` (keyed child body of the official document-preview tab) | `@local/dsh-docx-preview/v2` | keyed child, no order | `DOCX 修订预览` (renderer title) | `client.js:22`, `:1701-1714`; zh title `client.js:1594`; locale `locale/zh-CN.json:3` |
| document-preview registry (renderer implementation) | `@local/dsh-docx-preview/v2` | priority `extension` | `DOCX 修订预览` | `client.js:1679-1687` (`extensions: ['docx']`, `binaryExtensions: ['docx']`, `loading: 'bytes-complete'`, `wrap: false`), `:26`, `:1684` |
| `sidebar.right.tab.document.actions` | — | — | none | no registration in `client.js` (grep: only `:1701`) |

**Extensions claimed:** only `docx` (`client.js:26`, `:1681-1682`) — extension band, i.e. it wins the default
renderer for `.docx`.

**Global side effects:**
- Injects one `<style>` into `document.head` (`client.js:1581-1588`).
- Removes a stale debug badge `#dsh-docx-debug` by `getElementById` (`client.js:1575-1579`).
- POSTs diagnostics to `/dsh-docx-preview/log` (`client.js:48-56`); host registers that route (`index.js`, `server.register` for `/dsh-docx-preview/log` and `/dsh-docx-preview/apply`).
- Host registers the `docx_revisions` tool (`index.js`, `defineRevisionsTool` / `ctx.tools.register`).

**User-visible buttons it adds** (inside the preview body, zh labels from `client.js:1592-1628`): 修订 / 干净稿 tabs;
`N 处` (`:1492`), `N 条批注` (`:1499`), 定位, 应用, 忽略, 写入副本, 适应宽度 / 100%, 批注 rail, close.
These are body-local, not extra header buttons.

**Duplicate / overlap:** it competes with the official Office renderer exactly on `.docx`:
official `@deepseek-ai/dsh-client-ui-sidebar-documentpreview/office` claims `doc`, `docx`, `ppt`, `pptx` at
priority `builtin` with title **`Office 文档`** (official `lib/client.js:6068`, `:6712-6743`). Because this plugin
claims the extension band, the preview header's renderer picker for a `.docx` shows the **two items** the user
reported: `DOCX 修订预览` vs `Office 文档`.

---

## 2. @dongasai/dsh-editor v1.2.0

Directory: `E:\hermes_playground\dsh-plugins\dsh-editor` (fork of a shipped editor; `FORK.md`).
Client entry: `client.js` (296 KB); host half `index.js` (6 POST routes).

| Seat | Key / id | order | Visible label (zh) | Citation |
|---|---|---|---|---|
| document-preview registry — band 1 | `@dongasai/dsh-editor/text` | priority `extension` | `编辑器` | `client.js:192`, `:5833-5847`, title key `client.js:377` |
| document-preview registry — band 2 | `@dongasai/dsh-editor/text-option` | priority `builtin` | `编辑器` | `client.js:193`, `:5833-5847` |
| `sidebar.right.tab.document` | key `@dongasai/dsh-editor/text` and key `@dongasai/dsh-editor/text-option` | keyed child | — | `client.js:5848-5853` |
| `sidebar.right.tab.document.actions` | `workspace-editor` | **5** | `编辑` | `client.js:5885-5890`, zh `:379` |
| `sidebar.right.tab.document.actions` | `workspace-editor-delete` | **6** | `删除` | `client.js:5893-5898`, zh `:394` |
| `sidebar.right.pane.tab` | key `@dongasai/dsh-editor/tab` (kind `workspace-editor`) | priority `builtin` | tab title `编辑 {name}` | `client.js:5855-5867`, zh `:378` |
| `sidebar.right.pane.tab` | key `@dongasai/dsh-editor/image` (kind `workspace-editor-image`) | `builtin` | `预览 {name}` | `client.js:5871-5883`, zh `:504` |
| `sidebar.right.pane.tab` | key `workspace-editor-files` | `builtin`, `keepMounted` | `文件编辑` | `client.js:5908-5927`, zh `:416` |
| sidebar-right guide cards | `workspace-editor-files` | **20** | `文件编辑` | `client.js:5914-5921` |
| `conversation.input.dock` | `workspace-editor-input` | **90** | none (invisible sink) | `client.js:5929-5937` |
| global shortcut | `workspace.editor.files` | — | `打开「文件编辑」面板` (Ctrl/Cmd+Alt+E) | `client.js:5940-5961`, zh `:419` |

**Extensions claimed for document preview:**
- Band 1 (`extension`, i.e. takes over by default), `client.js:165-168`:
  `txt text log json jsonc json5 jsonl ndjson yaml yml toml ini cfg conf config env properties lock`.
- Band 2 (`builtin`, an extra alternative in the picker), `client.js:171-182`: `md markdown mdx rst adoc tex`,
  `html htm xhtml xml xsl xslt svg`, `css scss sass less`, `js mjs cjs jsx ts mts cts tsx vue svelte astro`,
  `py pyi rb go rs java kt kts scala swift cs php`, `c h cc cpp cxx hpp hh hxx m mm`, `lua pl pm r jl dart ex exs erl hrl hs clj cljs`,
  `sh bash zsh fish ksh ps1 psm1 bat cmd`, `sql graphql gql proto csv tsv gradle groovy cmake mk`,
  `diff patch asm s nim zig v` — ~110 extensions.
- `docx` is **not** claimed by the editor.

**Global side effects:**
- `document.body.appendChild` for an off-screen textarea clipboard fallback (`client.js:959`, removed after copy).
- Registers global Custom Highlight names in `CSS.highlights` (`client.js:1593-1601`, `:1684`, `:1991`) — global
  browser registry, prefixed names only.
- Styles are rendered as component-local `<style>` elements (e.g. `client.js:2535`, `:2603`, `:2854`), not injected
  into `<head>`; no `document.addEventListener`.
- Host routes: `ENDPOINTS` POST routes for write/delete/mkdir/rename/copy/upload (`index.js`, `ENDPOINTS` /
  `webServer.register`).
- Registers a global shortcut (`client.js:5940-5961`).

**Duplicate / overlap:** (a) its `编辑`/`删除` buttons sit in the official preview header actions for **every**
previewed file; (b) band 1 grabs `.json/.txt/...` away from the official code/text renderers, so the picker grows a
`编辑器` entry on those files; (c) band 2 puts `编辑器` into the picker for Markdown and all code files, on top of
official `Markdown` and `@local/dsh-github-md`'s `GitHub 风格 Markdown`; (d) `文件编辑` is a 4th right-sidebar tab type
(plus 编辑/图片 tab types) with its own guide card at order 20.

---

## 3. @local/dsh-github-md v0.15.3

Directory: `E:\hermes_playground\dsh-plugins\dsh-github-md`
Client entry: `client.js` (146 KB); host half `index.js` (`/github-md` prefix routes + vendored assets).

| Seat | Key / id | order | Visible label (zh) | Citation |
|---|---|---|---|---|
| document-preview registry | `@local/dsh-github-md/github-markdown` | priority `extension` | `GitHub 风格 Markdown` | `client.js:27`, `:2314-2321`, zh `:133`; locale `locale/zh.json:3` |
| `sidebar.right.tab.document` | key `@local/dsh-github-md/github-markdown` | keyed child | — | `client.js:2322-2330` |
| `sidebar.right.pane.tab` | key `@local/dsh-github-md/markdown-editor` (kind `markdown-editor`) | `keepMounted` | tab title `Markdown 工作台` | `client.js:2335-2347`, `:2348-2365`, zh `:145` |
| `sidebar.right.pane.tab.title` | key `@local/dsh-github-md/markdown-editor` | — | `Markdown 工作台` | `client.js:2366-2370` |
| sidebar-right guide cards | `open` | **30** | `Markdown 工作台` | `client.js:2340-2346` |
| `sidebar.right.tab.document.actions` | `github-md-editor` | no order (default) | icon-only button, tooltip/aria `在此编辑` | `client.js:2375-2393`, zh `:194` |
| composer quote capture | reads `conversation.input` (not a slot registration) | — | 引用 | `client.js:1316`, `:2326-2329` |

**Extensions claimed:** `md`, `markdown` (`client.js:2316`), extension band — it becomes the default renderer for
Markdown and adds its own picker entry alongside official `Markdown` and editor `编辑器`.

**Global side effects:**
- Module-level `ensureDocumentStyle()` at load: appends a `<style data-github-md="style">` into `document.head`
  (`client.js:918-924`, called `:2400-2405`).
- Writes typography CSS variables onto the document root (`client.js:108-115`).
- Appends vendor `<script>`/`<link>` tags into `document.head` for marked / DOMPurify / KaTeX / CodeMirror / Shiki
  (`client.js:771-808`, `:814-840`, `:847-882`, `:888-898`).
- Persists settings in `localStorage` key `github-md:settings:v1` (`client.js:33`).
- Quotes selected preview text straight into the composer (`client.js:1316`, `:2326-2329`).

**Duplicate / overlap:** third Markdown implementation (after official `Markdown` and editor `编辑器`); its
`在此编辑` header action duplicates editor's `编辑` action (same slot, different id/order → two edit buttons); its
`Markdown 工作台` tab duplicates editor's `编辑`/`文件编辑` tab types; its guide card (order 30) is a second
right-sidebar empty-state card.

---

## 4. @local/dsh-git-buttons v0.1.0

Directory: `E:\hermes_playground\dsh-plugins\dsh-git-buttons`
Client entry: `client.js` (20 KB); host half `index.js` (RPC route + SSE route).

| Seat | Key / id | order | Visible label (zh) | Citation |
|---|---|---|---|---|
| `conversation.input.left` | `git-buttons` | **45** | two icon buttons `拉取` / `推送` (aria-label + tooltip) | `client.js:449-454`, zh `:101-103` |
| `conversation.composer.dock` | `git-buttons-status` | **45** | status pill: `正在提交并推送…` / `已推送 · …` / `已拉取 · …` | `client.js:455-460`, zh `:107-114` |

**Global side effects:** `window.addEventListener('focus')` and `document.addEventListener('visibilitychange')`
(`client.js:274-292`); `EventSource('/git-buttons/events?sessionId=…')` per session plus 5 s fallback polling and
30 s non-repo retry (`client.js:294-358`); per-session module-level store map (`client.js:136-152`); local
`<style>` only. Host: `connection.fetch.register` RPC `/api`/`git-buttons` and `webServer.register` SSE
`/git-buttons/events` (`index.js`).

**Duplicate / overlap:** no third-party rival in `conversation.input.left` while the second Git plugin is disabled.
It still adds a 2-button cluster + a persistent status row to the composer for every git-repo session.

---

## 5. @zephinel/dsh-intelligent-ui v0.5.0

Directory: `C:\Users\User\.dsh\profiles\desktop\node_modules\@zephinel\dsh-intelligent-ui`
Client entry: `lib/client.js` (3.8 MB minified, 1433 lines — all slot registrations are on **line 1427**;
character offsets noted because the file is one long minified line per section). Host half: `lib/index.js`.

| Seat | Key / id | order | Visible label (zh) | Citation |
|---|---|---|---|---|
| `conversation.chat.turnTail` | `intelligent-ui` | — | per-answer card/toolbar: 显示样式 (Auto/Card/Article), 保存为模板, 导出, 调整样式, 目录 | `lib/client.js:1427` (offset ≈3,795,275); ids `:1427` (`S6r="intelligent-ui"` at offset ≈3,794,455); zh keys from bundle dictionary (`style.slider.label`, `template.saveFromResult`, `onDemand.adjust`) |
| `conversation.chat.assistant-actions` | `intelligent-ui-export` | **20** | `导出` / `导出回答` menu (`导出图片` / `交互页面`) | `lib/client.js:1427` (offset ≈3,795,698); `I6r="intelligent-ui-export"` at ≈3,794,476; zh keys `export.button.label`, `export.menu.image`, `export.menu.page` |
| `tool.call.toolview` | key `render_ui` | — | custom view for its own `render_ui` tool call | `lib/client.js:1427` (offset ≈3,796,013) |
| `conversation.input.activity` | **no id/key given** | — | composer chip `UI：{scope}` (关闭 / 仅本会话 / 全部会话) | `lib/client.js:1427` (offset ≈3,796,070); zh keys `chip.label`, `chip.aria` |
| `conversation.input.overlay` | `intelligent-ui-on-demand` | — | `按需生成` overlay panel (取消, 重试, 填入示例, 调整样式, 关闭) | `lib/client.js:1427` (offset ≈3,796,410); zh keys `onDemand.label`, `onDemand.cancel`, `onDemand.retry`, `onDemand.examples` |
| `plugins.bundle.config` | key `@zephinel/dsh-intelligent-ui` | — | plugin detail page form: 全局默认 / 在所有会话中启用 / 回答样式 / 导出 | `lib/client.js:1427` (offset ≈3,796,841); zh keys `settings.title`, `settings.enable.label` |

**Global side effects:**
- Bundle-owned stylesheet injected into `document.head` once per document, removed on dispose
  (`lib/client.js:15`, offset ≈147,255).
- Portals into `document.body` for popovers, export menu, scope menu, style popover, confetti
  (offsets ≈2,757,052 / ≈2,761,330 / ≈3,458,346 / ≈3,748,819 / ≈3,787,676).
- `MutationObserver` on `document.body` for `data-ds-dark-theme` (`lib/client.js:1390`, offset ≈3,453,609), and on
  `document.documentElement` for theme (`:1373`, offset ≈3,418,182); dialog helpers set
  `document.body.style.overflow="hidden"` and add capture `keydown`/`pointerdown` listeners (`:1373`).
- Host side registers the `render_ui` tool, a system-prompt section and ships an embedded skill
  (`cordis.patch.yml:12-16`).

**Duplicate / overlap:** adds the heaviest per-answer chrome — an export action (order 20) next to official
assistant actions, a turn-tail toolbar, a composer chip **and** a composer overlay, plus a plugin-detail config form.
The `conversation.input.activity` registration is the only registration in this whole audit that supplies no
`id`/`key`, which makes its chip hard to attribute and to disable selectively.

---

## 6. @happyqu/dsh-plugin-git v0.1.28 — **DISABLED** (not in `dsh.profile.bundles`)

Directory: `C:\Users\User\.dsh\profiles\desktop\node_modules\@happyqu\dsh-plugin-git`
Client entry: `dist/client.js` (1.1 MB). It is a dependency (`package.json:6`) but absent from the bundle array
(`package.json:20-43`), so none of the following is currently mounted.

| Seat | Key / id | order | Visible label (zh) | Citation |
|---|---|---|---|---|
| `conversation.session.header.utilities` | `git` | **40** | `Git` (opens Git window) | `dist/client.js:21610-21614` |
| `conversation.input.left` | `git-blank` | **40** | workspace Git action | `dist/client.js:21635-21636` |
| `conversation.hero.workspace.directoryFlow` | (no id) | priority **-10** | 新建项目 / 克隆仓库 flow entries | `dist/client.js:21304` |
| `sidebar.workspaces.directoryFlow` | (no id) | priority **-10** | same flow in sidebar | `dist/client.js:21304` |
| `shell.overlay` | `git-clone-workspace` | **45** | clone wizard | `dist/client.js:21329` |
| `shell.overlay` | `git-directory-picker` | **46** | directory picker | `dist/client.js:21351` |
| `shell.overlay` | `git-new-project` | **47** | new-project wizard | `dist/client.js:21356` |
| `shell.overlay` | `git-window` | **40** | `Git` workbench window | `dist/client.js:21640-21644` |
| `settings.section` | `git-plugin` | **60** | `Git` settings section | `dist/client.js:21656-21660` |
| direct DOM injection | — | — | `打开 Git 窗口` button added to each sidebar workspace row + branch/actions cluster in the hero | `dist/client.js:21501-21598` (sidebar rows), `:21386-21440` (`insertHeroActions` / `MutationObserver` on `document.body`) |

Also: injects `<style data-plugin="dsh-plugin-git">` into `document.head` (`dist/client.js:1166-1173`), wraps
`uiWorkspace.openWorkspace` (`observeWorkspaceNavigation`), and uses `createPortal` to `document.body` 18 times.

**Duplicate / overlap if re-enabled:** a second `Git` entry in the composer (`conversation.input.left` order 40 vs
git-buttons order 45), a Git button in the session header, a `Git` settings section, four extra `shell.overlay`
windows, plus raw DOM mutation of the official hero row and sidebar workspace rows — the largest footprint of all
seven packages.

---

## 7. @s1lencewill/dsh-markdown-reader v0.4.2 — **DISABLED** (not in `dsh.profile.bundles`)

Directory: `C:\Users\User\.dsh\profiles\desktop\node_modules\@s1lencewill\dsh-markdown-reader`
Client entry: `lib/client.cjs` (150 KB); host half `lib/index.js` (read-only `/md-reader/*` routes + prompt section).
It registers **no slots at all** (grep for `slots.register` / `slots.inject` = 0), so it cannot collide on a seat.

| Surface | Detail | Citation |
|---|---|---|
| DOM-injected toolbar button | `阅读模式` appended to the official preview toolbar (`.aionui-root` second child) | `lib/client.cjs:3407-3437`, label `:1417`, watcher `:3439-3449`, click tracking `:3385-3405` |
| Full-screen reader root | `div#mr-mount` appended to `document.body`, React root mounts the overlay reader | `:3537-3544` |
| Floating button | `.mr-float-btn` | `:3264`, CSS `:1976-1983` |
| Global shortcut | Ctrl/Cmd+Shift+M toggles the reader | `:3451-3457`, wired `:3624-3634` |
| Global listeners/observers | capture-click tracking, `MutationObserver` on `document.body` (panel button) and `document.head` (style re-attach), theme observer, titlebar inset | `:3385`, `:3439`, `:3328-3335`, `:1786`, `:3630-3635` |
| Head style injection | `#dsh-markdown-reader-style` + `#dsh-markdown-reader-theme` | `:3514-3530` |

**Duplicate / overlap if re-enabled:** a manual DOM button inside the official preview toolbar (not a slot, so the
official renderer cannot control order/visibility), plus a global shortcut and a body-level overlay. It overlaps
the same Markdown preview surface as `@local/dsh-github-md` and the editor; currently zero visible impact.

---

## Official baseline for the seats above

| Official seat | Official occupant | Citation (app.asar, shipped package) |
|---|---|---|
| document-preview registry | `.../sidebar-documentpreview/text` (extensions `[]`, `builtin`), `.../markdown` (`md`,`markdown`, `builtin`), `.../pdf`, `.../excel`, `.../code` (`CODE_HIGHLIGHT_EXTENSIONS`, `builtin`), `.../html`, `.../image`, `.../office` (`doc`,`docx`,`ppt`,`pptx`, `builtin`, title **Office 文档**) | `app.asar:/dsh/node_modules/@deepseek-ai/dsh-client-ui-sidebar-documentpreview/lib/client.js:659-674`, `:1988-2025`, `:6034-6062`, `:6712-6743`, `:8004-8062` |
| `sidebar.right.tab.document` and children | owned by `ui-sidebar-documentpreview` (renders `.actions`, `.unpreviewable`, `.action` seats inside its text tab) | same file `:8021-8054`, `:925-949`, `:1048` |
| `sidebar.right.tab.document.actions` | also registered by `@deepseek-ai/dsh-client-ui-open-in-app` (package-level scan of shipped client bundles) | `open-in-app/lib/client.js` |
| `conversation.input.left`, `conversation.input.right`, `conversation.input.overlay`, `conversation.input.activity`, `conversation.input.dock`, `conversation.composer.dock`, `conversation.chat.assistant-actions`, `conversation.chat.turnTail`, `tool.call.toolview` | official chat / conversation / action-cards / message-feedback / plan / deliverables / schedule / tool / skill / commands / input-trigger packages | package-level scan of `@deepseek-ai/dsh-client-ui-*` client bundles |
| `settings.section` / `settings.plugins.tab` | official settings-account / general / models / plugins / plugin-inventory / agent-preset | package-level scan |

---

## Conflict map — every seat with more than one third-party occupant

| Seat | Third-party occupants (id/key, order, visible zh label) | Duplicate / overlap conclusion |
|---|---|---|
| `sidebar.right.tab.document.actions` | 1) editor `workspace-editor`, order 5 — `编辑` (`dsh-editor/client.js:5885-5890`); 2) editor `workspace-editor-delete`, order 6 — `删除` (`:5893-5898`); 3) github-md `github-md-editor`, no order — tooltip `在此编辑` (`dsh-github-md/client.js:2375-2393`). Official `open-in-app` also occupies this list. | **Worst duplicate.** 3 third-party buttons + official open-in-app in one preview header. On a `.md` file the user sees two edit affordances (编辑 and 在此编辑) plus 删除. |
| document-preview registry → becomes the renderer picker in `sidebar.right.tab.document` | docx-preview `@local/dsh-docx-preview/v2` (`docx`, extension, `DOCX 修订预览`); editor `@dongasai/dsh-editor/text` (+ `.../text-option`) (~120 ext, `编辑器`); github-md `@local/dsh-github-md/github-markdown` (`md`,`markdown`, extension, `GitHub 风格 Markdown`) | Duplicate renderer implementations. `.docx` → 2 items: `DOCX 修订预览` vs `Office 文档` (the user's complaint). `.md` → ≥3 items: `GitHub 风格 Markdown`, `编辑器`, `Markdown`. `.json/.txt/.yaml/...` → `编辑器` plus official code/text. `.doc/.ppt/.pptx` untouched. |
| `sidebar.right.pane.tab` | editor keys `@dongasai/dsh-editor/tab`, `.../image`, `workspace-editor-files` (`dsh-editor/client.js:5863-5927`); github-md key `@local/dsh-github-md/markdown-editor` (`dsh-github-md/client.js:2348-2365`) | Distinct keys, no overwrite, but **4 third-party tab types** on top of official tabs; 2 extra empty-state guide cards: `文件编辑` order 20 (editor `:5914-5921`) and `Markdown 工作台` order 30 (github-md `:2340-2346`). |
| `sidebar.right.pane.tab.title` | github-md `@local/dsh-github-md/markdown-editor` (`dsh-github-md/client.js:2366-2370`) | Only third-party occupant; harmless chrome. |
| `conversation.input.left` | git-buttons `git-buttons`, order 45 — `拉取` / `推送` (`dsh-git-buttons/client.js:449-454`); happyqu git `git-blank`, order 40 — workspace Git action (*disabled*, `dsh-plugin-git/dist/client.js:21635-21636`) | While happyqu stays disabled: one 2-button Git cluster. If re-enabled: a second Git entry at order 40 immediately left of `拉取/推送`. |
| `conversation.composer.dock` | git-buttons `git-buttons-status`, order 45 — status pill (`dsh-git-buttons/client.js:455-460`) | One third-party row in the composer dock (official chat also uses this seat). |
| `conversation.input.overlay` | intelligent-ui `intelligent-ui-on-demand` — `按需生成` panel (`dsh-intelligent-ui/lib/client.js:1427`) | Only third-party overlay; official commands/input-trigger/message-feedback also occupy the seat, so the composer overlay layer is now shared by 4+ owners. |
| `conversation.input.activity` | intelligent-ui — chip `UI：{scope}`, **registration has no id/key** (`dsh-intelligent-ui/lib/client.js:1427`, offset ≈3,796,070) | Chip collides conceptually with official conversation/voice-input activity, and cannot be individually ordered/disabled. |
| `conversation.chat.assistant-actions` | intelligent-ui `intelligent-ui-export`, order 20 — `导出` (`dsh-intelligent-ui/lib/client.js:1427`) | Adds a per-answer export button beside official chat/message-feedback actions. |
| `conversation.chat.turnTail` | intelligent-ui `intelligent-ui`, no order — card + 显示样式/保存为模板/导出 toolbar (`dsh-intelligent-ui/lib/client.js:1427`) | Adds a toolbar under every rendered answer, on top of official action-cards/plan/deliverables turn tails. |
| `tool.call.toolview` | intelligent-ui key `render_ui` (`dsh-intelligent-ui/lib/client.js:1427`) | Keyed by its own tool name — no duplicate with other tool views. |
| `settings.section` | happyqu git `git-plugin`, order 60 — `Git` (*disabled*, `dsh-plugin-git/dist/client.js:21656-21660`) | No active third-party settings section. |
| `shell.overlay` | happyqu git ×4: `git-window` order 40, `git-clone-workspace` 45, `git-directory-picker` 46, `git-new-project` 47 (*disabled*, `dsh-plugin-git/dist/client.js:21329-21356`, `21640-21644`) | No active third-party overlay. |
| `plugins.bundle.config` | intelligent-ui key `@zephinel/dsh-intelligent-ui` (`dsh-intelligent-ui/lib/client.js:1427`) | Keyed config form on the plugin detail page — expected, not a conflict. |
| `sidebar.panellist`, `sidebar.footer.action`, `settings.plugins.tab`, `deliverables.file.actions`, `conversation.input.right`, `sidebar.right.tab.document.action`, `sidebar.right.tab.document.unpreviewable` | none | No third-party occupants on these seats. |

### Exact duplicate buttons / entries visible today (enabled plugins only)

1. **`.docx` renderer picker:** `DOCX 修订预览` ↔ `Office 文档` (two items, docx-preview vs official office).
2. **`.md` renderer picker:** `GitHub 风格 Markdown` ↔ `编辑器` ↔ `Markdown` (github-md + editor + official).
3. **Preview header actions on `.md`:** `编辑` (editor, order 5), `删除` (editor, order 6), icon `在此编辑`
   (github-md, no order), plus official `open-in-app` action.
4. **Preview header actions on `.txt/.json/.yaml/...`:** `编辑` + `删除` (editor) on top of official code/text preview.
5. **Composer left cluster:** `拉取` + `推送` icon pair (git-buttons, order 45).
6. **Composer dock:** Git status pill (git-buttons, order 45).
7. **Composer UI chrome:** `UI：{scope}` chip (intelligent-ui activity slot) + `按需生成` overlay + per-answer
   `导出` action (order 20) + turn-tail style/export toolbar (intelligent-ui).
8. **Right-sidebar empty state:** two extra guide cards, `文件编辑` (editor, order 20) and `Markdown 工作台`
   (github-md, order 30), plus 4 extra tab types.

### Biggest sources of UI clutter (ranked)

1. **@dongasai/dsh-editor** — ~120 claimed extensions across two renderer bands (pollutes the picker on nearly
   every text file), plus 2 header actions, 3 tab types, a guide card and a global shortcut.
2. **@zephinel/dsh-intelligent-ui** — chip + overlay + per-answer export action + turn-tail toolbar + plugin config
   form; the composer and every answer get extra chrome.
3. **@local/dsh-github-md** — third Markdown renderer + a second edit button + a fourth tab type + guide card, with
   heavy `<head>`/vendor/CSS injection.
4. **@local/dsh-docx-preview** — narrow but exactly the confusing two-item `DOCX 修订预览` vs `Office 文档` picker on
   `.docx`, plus a whole revision/comment UI inside the preview body.
5. **@local/dsh-git-buttons** — modest: 2 composer buttons + a status row, but persistent for every git repo.
6. **@happyqu/dsh-plugin-git** (disabled) and **@s1lencewill/dsh-markdown-reader** (disabled) — currently invisible;
   if re-enabled, happyqu is the single largest clutter source (9 seat registrations, 4 overlays, a settings section,
   and raw DOM mutation of the hero row and every sidebar workspace row) and markdown-reader injects a toolbar
   button + global shortcut by direct DOM manipulation.

---

### Audit limits

- All seven packages' package.json / cordis.patch.yml / client entry were opened. `dsh-intelligent-ui` and
  `dsh-plugin-git` clients are minified bundles: for `dsh-intelligent-ui` slot cites give the one minified line
  (1427) plus byte offsets; for `dsh-plugin-git` line numbers are the readable build output's lines.
- Complete `zh` label extraction was done from `locale/*.json` where present and from embedded zh dictionaries
  otherwise; a few inner-locale strings (intelligent-ui toolbars) are cited by locale key rather than by line.
- Official renderer/tab ownership beyond the two extracted official packages is based on a package-level scan of
  shipped client bundles (slot name string present), not per-line registration order.
