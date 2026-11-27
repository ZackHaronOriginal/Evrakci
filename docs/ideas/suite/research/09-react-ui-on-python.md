# 09 — Putting a React UI on the Python backend

*Research date: 2026-11-27. Every claim has a source URL. **[unverified]** marks points I could not confirm from a primary source. **[estimate]** marks my own arithmetic.*

## TL;DR

- **Recommendation:** ship v1 with **pywebview 6.x as a thin Python shell** around a React app built with Vite. Python owns the window and WebView2 renders the React app. The backend is a separate Python package that knows nothing about pywebview and speaks a small, versioned **JSON-RPC 2.0-style protocol**.
- Plan **Tauri 2 with a Python sidecar over stdio** as the fallback shell. Because the protocol does not depend on its transport, switching shells means writing a new adapter, not rewriting the UI.
- **Electron** works but is the heaviest option: it bundles Chromium and must be upgraded every 8 weeks. **Browser + FastAPI** is worth keeping only as a developer and test mode. Qt WebEngine is too large, and NiceGUI and Flet are not React.
- **Thumbnails never go over the bridge as base64.** The backend writes JPEG/WebP files to a cache folder and the UI loads them as URLs.
- Keep fine-grained interaction (scrolling, drawing boxes, editing cells) entirely inside React. Send coarse commits to Python.

## 1. Options in detail

### 1.1 pywebview (Python owns the window)

- **What it is:** a BSD-3-Clause library, version 6.2.1 released 2026-04-15 ([PyPI](https://pypi.org/pypi/pywebview/json), [repo](https://github.com/r0x0r/pywebview)). It uses WinForms + WebView2 on Windows and GTK or Qt on Linux ([repo README](https://github.com/r0x0r/pywebview)). Version 6.0 (2025-08-08) added a shared state object between Python and JS ([6.0 blog](https://sources.debian.org/src/python-pywebview/6.0%2Bdfsg-1/docs/blog/pywebview6.md)). The Windows backend uses pythonnet (MIT, 3.2.1, released Oct 2026, per [PyPI](https://pypi.org/pypi/pythonnet/json)).
- **How the bridge works** (I read the source on `master`):
  - JS calls `window.pywebview.api.method(...)` and gets a Promise back ([API docs](https://sources.debian.org/src/python-pywebview/6.0%2Bdfsg-1/docs/guide/api.md)).
  - On WebView2 the message arrives through `WebMessageReceived` / `postMessage` ([edgechromium.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/platforms/edgechromium.py)).
  - Python then **starts a new `Thread` for every call**. The return value is JSON-encoded and pushed back with `run_js(...)`, so it goes through script evaluation ([util.py `js_bridge_call`](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/util.py)).
  - Consequences:
    - (a) The backend must serialise access to PDFium itself, for example with one render thread or worker process behind a queue, because the bridge calls in from arbitrary threads.
    - (b) Large binary returns would be JSON or base64 strings inside a script, which is the slowest path.
    - (c) Many small calls each pay for a thread start plus a script evaluation. I found no published benchmark **[unverified: per-call latency; measure it]**.
- **Local files and images:**
  - For a relative entry URL, pywebview starts a **bottle static file server on `127.0.0.1` with an OS-assigned port**. It serves only files and has no API routes ([http.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/http.py), [architecture docs](https://sources.debian.org/src/python-pywebview/6.0%2Bdfsg-1/docs/guide/architecture.md)).
  - That server has no authentication, so any local process could read files under its root. The js_api does not go through HTTP.
  - pywebview creates a per-session token for CSRF defence if you add your own REST server ([security guide](https://sources.debian.org/src/python-pywebview/6.1%2Bdfsg-1/docs/guide/security.md)).
  - You can also pass your own WSGI app as the URL; it is served on the same loopback server ([http.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/http.py)). That lets you put a token check and a `Host` check on thumbnail URLs.
  - pywebview registers `AddWebResourceRequestedFilter('*')` for every request ([edgechromium.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/platforms/edgechromium.py)). Microsoft notes that `WebResourceRequested` is resolved on the host UI thread and is slower than file URLs or virtual-host mapping ([MS: local content](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/working-with-local-content)). The handler returns early when no Python listener is attached, but how much this costs a 1000-image grid is **[unverified]**.
  - `window.native` exposes the WinForms form ([window.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/window.py), [winforms.py](https://raw.githubusercontent.com/r0x0r/pywebview/master/webview/platforms/winforms.py)). Through it you could probably call WebView2's `SetVirtualHostNameToFolderMapping` for a fast, server-less image origin. That is not a documented pywebview API **[unverified]**.
- **Packaging:** freeze with PyInstaller or Nuitka. Exclude Qt, or PyInstaller will bundle it anyway ([freezing guide](https://pywebview.flowrl.com/guide/freezing)). WebView2 is the system Evergreen runtime, so the shell adds only a few MB on top of the frozen backend **[estimate]**.
- **Linux:** WebKitGTK through GTK, or Qt. WebKitGTK has known rendering and performance problems on some GPU/driver combinations ([Tauri Linux graphics page](https://v2.tauri.app/develop/debug/linux-graphics/), [WebKit bug 239934](https://bugs.webkit.org/show_bug.cgi?id=239934)).
- **Maturity:** about 6.2k stars and few open issues ([repo](https://github.com/r0x0r/pywebview)). It is essentially a **single-maintainer project**, which is a bus-factor risk.
- **Real users:** NiceGUI's "native mode" is built on pywebview ([NiceGUI docs](https://nicegui.io/documentation/section_configuration_deployment)).

### 1.2 Tauri 2 with a Python sidecar (and PyTauri)

- **Licence and activity:** Apache-2.0 OR MIT. `@tauri-apps/cli` is at 2.12.6 ([npm](https://registry.npmjs.org/@tauri-apps/cli/latest)) and the project is very active.
- **Sidecar mechanics:**
  - Declare the binary in `bundle.externalBin` with a target-triple suffix. The docs name PyInstaller-built Python servers as a typical case ([sidecar docs](https://v2.tauri.app/develop/sidecar/)).
  - Spawn it from Rust or JS and talk over stdin/stdout. Capability permissions control what may be spawned (same page).
- **IPC:**
  - Commands use a JSON-RPC-like protocol ([IPC concept](https://v2.tauri.app/concept/inter-process-communication/)).
  - `invoke` can send and receive **raw `ArrayBuffer`** payloads without JSON. **Channels** are the fast, ordered streaming path; events are "not designed for low latency or high throughput" ([core JS API](https://v2.tauri.app/reference/javascript/api/namespacecore/), [calling the frontend](https://v2.tauri.app/develop/calling-frontend/)).
  - With a Python sidecar, every call goes JS → Rust → stdin → Python → stdout → Rust → JS. One write-up notes that messages get JSON-stringified twice on such paths ([tauri-plugin-js write-up](https://dev.to/huakun/tauri-without-electron-bloat-a-type-safe-js-runtime-bridge-with-tauri-plugin-js-35m8)).
- **Images:** `convertFileSrc()` with the **asset protocol** serves files from disk inside a configured scope, with no HTTP server ([core JS API](https://v2.tauri.app/reference/javascript/api/namespacecore/)). This is the cleanest thumbnail path of all the options.
- **Installer:**
  - NSIS defaults to **current-user, no admin**, installing to `%LOCALAPPDATA%` ([Windows installer docs](https://v2.tauri.app/distribute/windows-installer/)).
  - WebView2 options: `downloadBootstrapper` (default, needs internet), `embedBootstrapper` (+1.8 MB, needs internet), `offlineInstaller` (+127 MB), `fixedVersion` (+180 MB) (same page).
- **Auto-update:** the updater needs signed artifacts; signing "cannot be disabled". It accepts a static JSON endpoint ([updater](https://v2.tauri.app/plugin/updater/)). The docs do not describe updating from a local file, which matters for offline offices **[unverified]**.
- **Pitfalls found:**
  - NSIS may not replace a running sidecar on reinstall ([tauri#15134](https://github.com/tauri-apps/tauri/issues/15134)).
  - With a PyInstaller **onefile** sidecar, Tauri tracks the *launcher* PID, so `child.kill()` orphans the real Python process. One team needed three PRs to fix this ([write-up](http://timetobuildbob.com/blog/the-launcher-is-not-the-process/)).
  - Fixes: use onedir builds, and on Windows put the sidecar in a Job Object with `KILL_ON_JOB_CLOSE` ([Raymond Chen](https://devblogs.microsoft.com/oldnewthing/?p=107812)).
- **PyTauri** (Apache-2.0, about 1.4k stars) embeds Python through PyO3 with "no IPC overhead". It calls itself "a fairly young project" and is not endorsed by Tauri ([repo](https://github.com/pytauri/pytauri)). Its last PyPI release, 0.8.0, dates from **2025-09-01**, over a year old ([PyPI](https://pypi.org/pypi/pytauri/json)). Too immature for this app.
- **Testing:** WebDriver via `tauri-driver` on Windows and Linux; Playwright is not mentioned ([Tauri WebDriver](https://v2.tauri.app/develop/tests/webdriver/)). Playwright can attach to any WebView2 over CDP using `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=…` ([Playwright WebView2](https://playwright.dev/docs/webview2)). That should apply to both Tauri and pywebview on Windows **[unverified for Tauri specifically]**.

### 1.3 Electron with a Python sidecar

- **Licence and cadence:** MIT, version 45.5.0 ([npm](https://registry.npmjs.org/electron/latest)). A new major ships every 8 weeks and only the latest three are supported ([timelines](https://www.electronjs.org/docs/latest/tutorial/electron-timelines)), so you are on a permanent upgrade treadmill.
- **Images:** `protocol.handle` serves files through a custom scheme, and the experimental `protocol.registerSource` serves directories off the main thread ([protocol API](https://www.electronjs.org/docs/latest/api/protocol)).
- **Size:** about 151 MB installer and 644 MB on disk in one recent Windows measurement **[third-party]** ([guide](https://dev.to/raxxostudios/how-to-build-and-distribute-an-electron-desktop-app-in-2026-24nk)).
- **Installer:** electron-builder NSIS defaults to `oneClick: true` and `perMachine: false`, i.e. per-user ([nsisOptions.d.ts](https://unpkg.com/app-builder-lib/out/targets/nsis/nsisOptions.d.ts)). `electron-updater` is MIT.
- **Strengths:** the same Chromium on Windows and Linux, so no WebKitGTK problems. Playwright's Electron support exists but is labelled **experimental** ([Playwright Electron](https://playwright.dev/docs/api/class-electron)).
- **Real apps:**
  - Datasette Desktop bundled a full standalone Python, installed packages on first run, and had to sign every bundled Python binary ([Willison](https://simonwillison.net/2021/Sep/8/datasette-desktop/), [TIL](https://til.simonwillison.net/electron/python-inside-electron)).
  - JupyterLab Desktop bundles a conda environment; its Flatpak is about 347 MB to download and 503 MB installed ([Flathub](https://flathub.org:443/apps/org.jupyter.JupyterLab), [CONTRIBUTING](https://raw.githubusercontent.com/jupyterlab/jupyterlab-desktop/master/CONTRIBUTING.md)).
  - ComfyUI Desktop (Electron + Python via uv) shows recurring Windows start-up failure threads and at least one Defender kill report ([repo](https://github.com/Comfy-Org/desktop), [forum](https://forum.comfy.org/t/unable-to-start-comfyui-desktop-v0-3-18-on-windows/706), [Defender anecdote](https://discussions.reallusion.com/t/fashiongen-gets-shut-down-by-windows-when-launching-comfy-ui/16395)).
  - Common lesson: shipping and starting Python is the fragile part, not the UI.

### 1.4 Python serving the UI to the default browser (FastAPI/Starlette + token)

- **Pros:** the simplest dev loop and no shell at all (FastAPI is MIT, 0.165.0, per [PyPI](https://pypi.org/pypi/fastapi/json)).
- **Security:** any web page can reach a localhost server (Zoom CVE, from the earlier report). You need a token, `Origin` and `Host` checks against DNS rebinding, and a 127.0.0.1-only bind. Binding to loopback usually avoids the firewall prompt **[anecdotal]** ([SO mirror](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/21230691/why-are-localhost-connections-blocked-by-the-firewall)).
- **Cons:** for non-technical staff it is a poor product. Browser shortcuts (Ctrl+W, Ctrl+P, F5, Backspace history) collide with a keyboard-heavy app, and closing the tab does not stop the backend.
- **Verdict:** keep it as **dev/test mode**, not as the product.

### 1.5 Other options, briefly

- **Qt WebEngine inside PySide6:** this keeps Qt *and* adds a Chromium. Windows builds are around 95 MB+ even for empty apps, and Linux bundles exceeded 600 MB in one report ([Qt forum](https://forum.qt.io/topic/106323/what-s-the-blank-size-of-qwebengine-view), [pyinstaller#6447](https://github.com/pyinstaller/pyinstaller/issues/6447)). PySide6 is LGPL-3.0 ([PyPI](https://pypi.org/pypi/pyside6/json)), which is allowed. It makes sense only as a step-by-step migration path inside the current app.
- **NiceGUI** (MIT, 4.1.0): Vue/Quasar, not React; its native mode is pywebview ([docs](https://nicegui.io/documentation/section_configuration_deployment)).
- **Flet** (Apache-2.0, 1.1.4): Flutter, not React ([PyPI](https://pypi.org/pypi/flet/json)).
- Neither NiceGUI nor Flet meets the owner's React requirement.

## 2. Comparison table

| | pywebview 6 | Tauri 2 + Py sidecar | Electron + Py sidecar | Browser + FastAPI | Qt WebEngine |
|---|---|---|---|---|---|
| Shell size on top of frozen Python | ~few MB [estimate] | ~10 MB shell (third-party figures vary, [Better Stack](https://betterstack.com/community/guides/scaling-nodejs/tauri-vs-electron-vs-deno-vs-electrobun/)) | ~150 MB ([guide](https://dev.to/raxxostudios/how-to-build-and-distribute-an-electron-desktop-app-in-2026-24nk)) | 0 | ~95 MB+ ([Qt forum](https://forum.qt.io/topic/106323/what-s-the-blank-size-of-qwebengine-view)) |
| Web engine | System WebView2 / WebKitGTK | System WebView2 / WebKitGTK | Bundled Chromium | User's browser | Bundled Chromium |
| Offline WebView2 | Ship MS standalone installer (+~127 MB) if missing | `offlineInstaller` +127 MB | not needed | not needed | not needed |
| Processes | Python + WebView2 | Rust + Python + WebView2 | Node + Chromium + Python | Python + browser | Python + QtWebEngineProcess |
| JS↔Python path | postMessage → new thread → `run_js` | invoke → Rust → stdio → Python | IPC → Node → stdio → Python | HTTP/WS | QWebChannel |
| Image path | loopback static server or your WSGI app (token) | asset protocol (no server) | `protocol.handle` | HTTP + token | custom scheme |
| Orphan risk | workers only | sidecar + workers | sidecar + workers | backend outlives tab | workers only |
| Per-user install | yes (Inno `PrivilegesRequired=lowest`, [docs](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm)) | yes (NSIS default) | yes (NSIS default) | yes | yes |
| Auto-update | DIY | signed updater plugin | electron-updater | DIY | DIY |
| Licence | BSD-3 | MIT/Apache | MIT | MIT | LGPL-3 |
| Maintenance | single maintainer | large team | large team, 8-week majors | n/a | Qt Co. |
| Languages to maintain | Python + TS | Python + TS + Rust | Python + TS + Node | Python + TS | Python + TS |
| UI tests | Playwright via CDP ([docs](https://playwright.dev/docs/webview2)) or browser mode | WebDriver / CDP | Playwright (experimental) | Playwright native | hard |

**Startup time:** no trustworthy Windows numbers exist for these stacks with a frozen Python inside. Published Tauri vs Electron figures conflict, and several look AI-generated ([Hopp benchmark](https://dev.to/gethopp/tauri-vs-electron-performance-bundle-size-and-the-real-trade-offs-1el4)). Frozen Python start-up dominates in every option. Use **onedir, not onefile**, because onefile extracts to a temp folder on each launch ([PyWry guide](https://deeleeramone.github.io/PyWry/guides/standalone-executable)). WebView2 cold start also costs time on slow disks ([MS perf](https://learn.microsoft.com/microsoft-edge/webview2/concepts/performance)). **[unverified: measure on a target PC]**

## 3. WebView2 availability on target PCs

- WebView2 is part of Windows 11. "The vast majority of Windows 10 devices" already have it, but "a small number" do not, so check the registry key `pv` under `EdgeUpdate\Clients\{F3017226-…}` in HKLM and HKCU ([MS distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)).
- When it is missing, the standalone installer works offline. Run without elevation it installs **per-user** (same page).
- Fixed Version is "over 250 MB". On Windows 10 it needs `icacls` grants from v120 onwards, and it cannot run from UNC paths (same page).
- **Use Evergreen + bundled standalone installer as a fallback.** Never use Fixed Version.
- Offline PCs will not receive Evergreen updates, so feature-detect newer WebView2 APIs (same page).

## 4. Antivirus, firewall and process lifetime

- PyInstaller executables are "regularly flagged" by antivirus products. The maintainers recommend code signing and reporting false positives to vendors; PE checksums are now set ([pyinstaller#5579](https://github-redirect.dependabot.com/pyinstaller/pyinstaller/issues/5579)). This applies equally to every option, because Python is frozen in all of them.
- Mitigations: sign the binaries, ship onedir, and submit each release to Microsoft's false-positive portal.
- pywebview without a custom server opens only the loopback static server. Tauri needs no listening socket. Electron and Tauri sidecars on stdio open no ports.
- **Job Objects:** in every option, OCR worker processes must sit in a kill-on-close Job Object ([Raymond Chen](https://devblogs.microsoft.com/oldnewthing/?p=107812)). In pywebview, Python is the root process, so if it dies the job dies with it. Tauri and Electron also have to manage the sidecar.

## 5. React techniques for the hard screens

### 5.1 A grid of 1000+ thumbnails

- **Virtualisation libraries:**
  - **TanStack Virtual** (MIT, 3.14): headless; combine row and column virtualisers for a grid ([docs](https://tanstack.com/virtual/latest/docs/introduction), [npm](https://registry.npmjs.org/@tanstack/react-virtual/latest)).
  - **React Aria `Virtualizer` with `GridLayout`** on a `GridList` (Apache-2.0): virtualisation and grid keyboard navigation in one component, with DOM nodes reused while scrolling ([React Aria Virtualizer](https://react-aria.adobe.com/Virtualizer)).
  - Alternatives: react-window 2.x (MIT) and react-virtuoso (MIT).
- **Rules:**
  - Fixed tile size so layout is O(1).
  - `<img src="thumb://job/123/p0042.webp" decoding="async">` from a file URL, never base64.
  - The backend pre-generates thumbnails at 1–2 fixed sizes and stores them on disk.
  - The UI asks for visible plus overscan ranges and cancels ranges that scroll away.
- **Thumbnail transport cost:** base64 inflates data by about 33% and goes through JSON parsing. WebView2 users report slow large-buffer transfers over the message channel ([WebView2Feedback#3486](https://github.com/MicrosoftEdge/WebView2Feedback/issues/3486)). File and protocol URLs let Chromium's image pipeline decode off the main thread **[decoding detail unverified]**.

### 5.2 Drawing boxes on a page

- **Konva + react-konva** (MIT): canvas, good for many shapes, built-in Transformer handles ([npm konva](https://registry.npmjs.org/konva/latest), [react-konva](https://registry.npmjs.org/react-konva/latest)).
- **Plain SVG over an `<img>`:** simplest, accessible and easy for AI agents to write. Fine up to a few hundred boxes per page **[estimate]**.
- **Annotorious** (`@annotorious/react`, BSD-3): ready-made image box annotation ([npm](https://registry.npmjs.org/@annotorious/react/latest)).
- **Fabric.js** (MIT).
- **Avoid tldraw:** it is source-available, needs a licence key in production, and every downstream user needs their own licence ([tldraw licence](https://tldraw.dev/community/license)). That is incompatible with an AGPL product.
- **Keep geometry in React state** in page-normalised coordinates (0–1) and send the backend one `regions.set` per committed edit, not per mouse move. This is the xi lesson: no round trip inside the interaction loop.

### 5.3 Keyboard-heavy accessible UI

- **React Aria Components** (Apache-2.0, 1.22): the strongest keyboard and focus model, including Table, GridList and virtualisation ([npm](https://registry.npmjs.org/react-aria-components/latest), [Virtualizer](https://react-aria.adobe.com/Virtualizer)).
- **Fluent UI React v9** (MIT, 9.75): the Windows 11 look, matching the repo's Fluent 2 design references ([npm](https://registry.npmjs.org/@fluentui/react-components/latest)).
- **Radix Primitives** (MIT): releases now look like low-velocity maintenance under WorkOS ([releases](https://radix-ui.com/primitives/docs/overview/releases)); "slowing" is an inference **[unverified]**. Base UI (MIT, 1.9) is the more active successor ([npm](https://registry.npmjs.org/@base-ui/react/latest)).
- **Editable tables:**
  - TanStack Table (MIT) with React Aria cells.
  - AG Grid Community (MIT; the Enterprise tier is commercial, so avoid importing its features) ([npm](https://registry.npmjs.org/ag-grid-community/latest)).
  - Glide Data Grid (MIT, canvas-based; weaker for screen readers **[unverified]**).
- **Recommendation:** React Aria Components as the behaviour layer, with Fluent 2 tokens for the look.

## 6. Dev workflow, testing and AI agents

- **Vite HMR:**
  - In pywebview, point `create_window(url="http://localhost:5173")` at the Vite dev server in debug mode; the bridge object is still injected.
  - In Tauri, `devUrl` does the same.
  - Better still, give the React app a **WebSocket transport to a dev-only Python server**. The UI then runs in plain Chromium with HMR, React DevTools and Playwright's normal runner, and no shell is involved. This is also how the UI stays swappable.
- **Tests:**
  - pytest on the backend, calling the protocol handlers directly.
  - Contract tests shared by both sides, built from one JSON Schema/TypeScript definition.
  - Playwright on the browser build with a fake backend.
  - A few smoke tests against the real shell via CDP ([Playwright WebView2](https://playwright.dev/docs/webview2)).
- **AI agents:** they do best with one language per side and a typed contract. pywebview keeps the shell in Python, which agents already handle in this repo. Tauri adds Rust (Cargo, capabilities, NSIS hooks), a third toolchain agents must not break. Electron adds Node main-process code and a fast upgrade cadence. **[judgement]**

## 7. Recommendation for Evrakçı

**Use pywebview 6 as a thin shell.** Python stays the only native language, the installer is the smallest, Python is the root process (no sidecar orphans), and WebView2 is already on almost every target PC.

**The separation the owner wants lives in the protocol, not in the process count.** Structure the code like this:

```
evrakci_core/      # pure backend, no UI imports, pytest
evrakci_protocol/  # schema: methods, events, errors, version
shell_pywebview/   # ~200-400 lines: window, bridge adapter, thumb URLs, Job Object
ui/                # React + Vite + TS; talks only to a Transport interface
dev_server/        # WebSocket transport for browser/Playwright
```

**Keep Tauri 2 as plan B.** Switch if pywebview's bridge or image path fails the spike thresholds below, or if pywebview stops being maintained. The UI then needs a new `Transport` and the backend needs a stdio framing loop. Nothing else changes.

### 7.1 What the boundary should look like

- **Messages:** JSON-RPC 2.0 shape: `{jsonrpc, id, method, params}` for requests and `{method, params}` without an `id` for events. On stdio, use one JSON object per line (NDJSON) or length-prefixed frames.
  - Method names follow a `noun.verb` pattern, e.g. `job.open`, `pages.list(range)`, `regions.set`, `ocr.start`.
  - Define params with pydantic models and generate TypeScript types from the JSON Schema, so both sides share one source of truth.
- **Versioning:**
  - The first call is `hello {protocol: "1.3", app: "x.y.z"}`, answered with the supported range.
  - Additive changes are minor versions: new optional fields and new methods. Removing or renaming anything is a major version. The UI refuses a different major version with a clear Turkish message.
- **Granularity:**
  - No calls inside interaction loops: no per-keystroke and no per-mousemove calls.
  - Batch reads, e.g. `pages.meta({from, to})`.
  - Commits are idempotent with an `edit_id`, so they are safe to retry.
- **Progress and cancel:**
  - Long work returns a `task_id` at once.
  - The backend emits `task.progress {task_id, done, total, stage}` events, throttled to at most about 10 per second.
  - It finishes with `task.done` or `task.failed`.
  - `task.cancel {task_id}` must reach the worker process (a multiprocessing Event, or killing the worker inside the Job Object).
  - The UI shows progress from events and never polls.
- **Images:**
  - The backend renders thumbnails and previews to `%LOCALAPPDATA%\Evrakci\cache\<job>\<page>-<size>-<rev>.webp`.
  - Events carry only `{page, rev, url}`. Change `rev` whenever a page changes, so the browser cache stays correct.
  - Serving per shell: pywebview uses a token-checked loopback WSGI route that checks `Host` is `127.0.0.1:<port>` (or `SetVirtualHostNameToFolderMapping` via `window.native` if the spike shows it works **[unverified]**). Tauri uses the asset protocol. Dev mode uses an HTTP route.
  - The full-resolution page canvas loads one large image the same way. Raw bytes never cross the bridge.
- **Threading:** bridge handlers only enqueue work. A single PDFium owner (thread or process) renders. OCR runs in worker processes inside a Job Object.
- **Errors:** typed codes (`E_FILE_LOCKED`, `E_OCR_TIMEOUT`…) plus a user message key. Stack traces go to the log, not the UI.

### 7.2 Main risks and how to contain them

1. **pywebview bus factor and API drift.** Pin the version and keep the shell thin. Run contract tests in the browser transport so a move to Tauri stays cheap.
2. **Bridge latency and threads.** Make it a 2-day spike on an old Windows 10 PC with a 1000-page job before committing. Thresholds:
   - p95 round trip under 15 ms for a small call **[proposed threshold]**
   - grid scrolling at 60 fps with thumbnails loading
   - 1000 thumbnails loaded within 5 s from a warm cache
3. **Thumbnails served by a loopback server.** Use a token in the URL, check `Host`, bind to 127.0.0.1 and keep `DenyCors`-like behaviour. Otherwise use virtual-host mapping.
4. **WebView2 missing or old on offline Windows 10.** Check the registry at install time, carry the standalone installer (+127 MB; consider shipping it as a separate "offline kit"), and feature-detect APIs.
5. **Antivirus false positives on frozen Python.** Sign the binaries, use onedir, keep the bootloader standard, and submit releases to Microsoft.
6. **Linux WebKitGTK rendering bugs.** Document `WEBKIT_DISABLE_DMABUF_RENDERER=1` ([Tauri Linux graphics](https://v2.tauri.app/develop/debug/linux-graphics/)) and test on one Intel and one NVIDIA box. If WebKitGTK is unacceptable, pywebview's Qt backend is the fallback there.
7. **Updates with no internet.** Ship a signed full installer that upgrades in place, per-user. In-app updating is optional, from a shared folder or USB **[design proposal]**.
