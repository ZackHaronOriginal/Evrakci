# 10 — UI framework comparison for Evrakçı

Date: 2026-11-27. Scope: choose the UI technology for the Evrakçı desktop suite. The Python backend is fixed. Every claim has a URL. Points marked **[unverified]** come from memory, a secondary summary, or a source I could not open this session. Points marked **[spike]** come from this project's own measurements.

## 1. Constraints that decide the result

The owner's priorities:

1. Full freedom over design and features.
2. AI coding agents work well in it.
3. It runs on Windows first, then Linux (Pardus), maybe macOS.

Secondary: memory and startup on old PCs, installer size, licence fit with AGPL-3.0 plus a CLA for commercial dual licensing, and maintenance risk.

Three facts narrow the field before any framework is scored:

- **The backend stays in Python.** OCRmyPDF, pypdfium2, Tesseract, RapidOCR and openpyxl have no permissive equivalents in other ecosystems (earlier research, this project). Any UI that is not Python needs IPC to a Python process. That works (VS Code, Jupyter and many Tauri sidecar apps do it), but it is one more moving part.
- **The spike already showed that a React UI is fast enough** [spike]. TanStack Virtual ran at 60 fps with no dropped frames on 1000 pages, cold jumps took 0.1–0.4 s and a UI→backend call took 0.2 ms. The open question is memory: about 620 MB in the browser plus 59 MB of Python, against 259 MB for today's Qt UI.
- **Licences must allow AGPL now and a proprietary build sold under the CLA later.** Anything GPL-only works for the AGPL build. It blocks the commercial build unless the owner buys a licence. Permissive and LGPL (dynamically linked) dependencies are safe for both.

## 2. Evidence about AI-agent friendliness (cross-cutting)

- TypeScript became the most-used language on GitHub in August 2025, ahead of Python and JavaScript. GitHub links this to AI tooling, because types give agents structure ([GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), [VS Magazine](https://visualstudiomagazine.com/Articles/2025/10/31/TypeScript-Tops-GitHub-Octoverse-as-AI-Era-Reshapes-Language-Choices.aspx), [Hejlsberg interview](https://github.blog/developer-skills/programming-languages-and-frameworks/typescripts-rise-in-the-ai-era-insights-from-lead-architect-anders-hejlsberg)).
- The most-watched public benchmarks for AI-generated UI test web stacks only. WebDev Arena centres on React, TypeScript and Tailwind (Next.js), and Arena now runs separate "Frontend" and "React" leaderboards ([Simon Willison](https://simonwillison.net/2024/Dec/16/webdev-arena/), [Arena React board](https://arena.ai/leaderboard/code/webdev/react), [Design Arena](https://www.ycombinator.com/companies/design-arena)). I found no comparable public benchmark for QML, XAML, Dart or Slint. Model quality on those stacks is therefore **unmeasured**, not shown to be worse.
- Earlier research for this project found agents fixed about 70% of Python tasks against about 40% of C# tasks on SWE-Sharp-Bench (carried over from the earlier report; not re-checked here).
- Screenshot testing works best in web shells. Playwright can attach to a WebView2 app over CDP: set `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--remote-debugging-port=…` and call `connect_over_cdp` ([Playwright WebView2 docs](https://playwright.dev/python/docs/webview2)). The same React UI can also run in plain Chromium under Playwright with a mocked backend, which is how the spike was measured. Tauri supports WebDriver through `tauri-driver` on Windows and Linux only; macOS needs the WebdriverIO service's embedded server ([Tauri WebDriver](https://v2.tauri.app/develop/tests/webdriver/)). Avalonia's headless mode can render real frames with `CaptureRenderedFrame()` once Skia is enabled ([Avalonia headless](https://docs.avaloniaui.net/docs/concepts/headless/)). Flutter has golden-file tests (`matchesGoldenFile`) ([API](https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html), **[unverified: not fetched]**). Qt can grab widgets and windows to images (`QWidget.grab`, `QQuickWindow.grabWindow`), but there is no Playwright-class tool for it.

Conclusion for priority 2: React + TypeScript has the most training data and the only public UI-generation benchmarks. It also has the most mature automated screenshot tooling (Playwright, Storybook, visual regression). Everything else trails, and how far behind it is varies by stack.

## 3. Candidates

### 3.1 React in a web shell

All three web shells run the same React code. They differ in which browser engine renders it on each OS, how Python is attached, and the installer.

#### pywebview (Python hosts the window)

- **Engines.** On Windows it uses WebView2, which is Chromium-based (`edgechromium`). On Linux you choose between GTK (WebKit2GTK) and Qt (QtWebEngine, which is Chromium). macOS uses WKWebView/Cocoa ([pywebview web engine docs](https://sources.debian.org/src/python-pywebview/6.1%2Bdfsg-1/docs/guide/web_engine.md)). On Linux you must pick GTK or Qt explicitly, and the docs recommend `pywebview[qt]` ([installation guide](https://sources.debian.org/src/python-pywebview/6.0%2Bdfsg-1/docs/guide/installation.md)). You can force a backend with `gui='qt'` or `PYWEBVIEW_GUI=qt` (same source).
- **Why the Qt backend matters for Pardus.** With `gui='qt'` the app renders in Chromium on both Windows and Linux, so WebKitGTK quirks never arise (section 3.1 "WebKitGTK" below). PySide6 and QtWebEngine are LGPL, the same licence footing the project uses today. The cost is size: QtWebEngine adds roughly 100+ MB on Linux **[unverified estimate]**.
- **Python link.** In-process. The JS bridge (`js_api` / `expose`) calls Python functions directly, and the spike measured 0.2 ms per call [spike]. You don't need a second process, a port or a lifecycle manager.
- **Release status.** 6.0 added state management and network events, and 6.1 can bundle a fixed WebView2 runtime through `WEBVIEW2_RUNTIME_PATH` ([6.0 blog](https://sources.debian.org/src/python-pywebview/6.1%2Bdfsg-1/docs/blog/pywebview6.md), [CHANGELOG](https://sources.debian.org/src/python-pywebview/6.1%2Bdfsg-1/docs/CHANGELOG.md)). Arch ships 6.2.1 ([Arch package](https://archlinux.org/packages/extra/any/python-pywebview/)).
- **Licence.** BSD-3-Clause, so it fits both the AGPL and the commercial build ([GitHub](https://github.com/r0x0r/pywebview)).
- **Maintenance risk.** pywebview has about 6.2k stars and one creator-maintainer, Roman Sirokov ([GitHub](https://github.com/r0x0r/pywebview)). This bus factor is the main risk. It is limited, because the wrapper is thin: if the project died, the React UI would move to Tauri or Electron and only the bridge layer would change.
- **Size and memory.** On Windows, WebView2 is already installed on Windows 11 and is evergreen on Windows 10 ([WebView2 end-user FAQ](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/end-user-faq)), so it adds almost nothing to the installer. Memory is Chromium's: the spike measured about 620 MB in Chromium [spike], and one third-party WPF test measured a WebView2 app at about 582 MB working set ([dev.to comparison](https://dev.to/noseratio/comparing-process-working-sets-of-webview-based-windows-desktop-apps-5dkk), anecdotal). WebView2 offers `MemoryUsageTargetLevel = Low` for inactive views ([MS docs](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.memoryusagetargetlevel)) and Microsoft's performance guidance applies ([WebView2 performance](https://learn.microsoft.com/microsoft-edge/webview2/concepts/performance)).

#### Tauri 2 (Rust host, Python as a sidecar)

- **Engines.** WebView2 on Windows, WKWebView on macOS and WebKitGTK on Linux, with no Chromium option on Linux. This is the main Linux risk for Pardus.
- **WebKitGTK quirks are documented officially.** On some systems, especially with NVIDIA, you can get a blank or white window, flickering, crashes on resize, DMABUF errors or Wayland "Error 71". The workarounds are `WEBKIT_DISABLE_DMABUF_RENDERER=1`, which turns off the fast path, and `WEBKIT_DISABLE_COMPOSITING_MODE=1` as a last resort. WebGL or canvas can drop silently to a software path, and the GPU string is masked ([Tauri Linux graphics](https://v2.tauri.app/develop/debug/linux-graphics/)). WebKit's own tracker has "painfully slow" GTK reports ([WebKit bug 239934](https://bugs.webkit.org/show_bug.cgi?id=239934)), and CPU-side blur filters are a known limit (summarised from WebKit bugs; secondary).
- **Pardus WebKitGTK version.** Debian 12 currently ships webkit2gtk 2.48.x security updates ([Debian packages](https://packages.debian.org/source/stable/webkit2gtk)). That Pardus 23 tracks the same version is **[unverified]** ([Pardus 23.3 changelog](https://pardus.org.tr/en/pardus-23-3-changelog/) does not say).
- **Python link.** Out-of-process sidecar, typically PyInstaller-built and declared in `externalBin`. The official docs name "Python CLI applications or API servers bundled using pyinstaller" as the main use ([Tauri sidecar](https://v2.tauri.app/develop/sidecar)). Known pitfalls: the NSIS installer can fail to replace a running sidecar on reinstall ([tauri#15134](https://github.com/tauri-apps/tauri/issues/15134)), and you have to manage the process lifecycle yourself ([Substack write-up](https://aiechoes.substack.com/p/building-production-ready-desktop)). `tauri-plugin-python` (PyO3) can embed Python instead ([docs.rs](https://docs.rs/crate/tauri-plugin-python/0.2.1/source/README.md)), but it is young.
- **Size and memory.** Shell installers of about 1 MB against about 106 MB for Electron in one Windows 11 test ([tech-insider](https://tech-insider.org/tauri-vs-electron-desktop-app-framework-2026/), secondary). The real installer is dominated by the PyInstaller bundle, so this advantage is small for Evrakçı. On Windows, memory is the same as pywebview because both use WebView2.
- **Licence.** MIT/Apache-2.0 ([repo](https://github.com/tauri-apps/tauri), **[not re-fetched]**).
- **Agent friendliness.** The front end is React. The host is Rust, which agents handle well, but it is a third language in a one-owner project.

#### Electron (bundled Chromium + Node, Python as a sidecar)

- **Engines.** The same pinned Chromium on every OS. Rendering is identical on Windows, Pardus and macOS, with no WebKitGTK problems, and this is Electron's real advantage.
- **Cost.** It is the largest option on disk and in memory. A hello-world install is about 115–150 MB on disk, with installers around 85–106 MB ([Vivian Voss](https://vivianvoss.net/blog/the-electron-tax), [Better Stack](https://betterstack.com/community/guides/scaling-nodejs/electron-desktop-architecture/), [tech-insider](https://tech-insider.org/tauri-vs-electron-desktop-app-framework-2026/); figures vary by method). One empty-app comparison measured about 268 MB on macOS (same tech-insider source). Our 620 MB spike number is a Chromium figure, so expect similar or slightly more, because Node is added.
- **Python link.** A sidecar over stdio, HTTP or WebSocket. The pattern is well established, but it is more code than pywebview's in-process bridge.
- **Testing.** Playwright supports Electron natively (`_electron.launch`) ([Playwright Electron](https://playwright.dev/docs/api/class-electron), **[not re-fetched]**). This is the best automated UI testing of any desktop shell.
- **Licence.** MIT ([repo](https://github.com/electron/electron), **[not re-fetched]**).
- **Maturity.** Very high: VS Code, Slack and many other apps use it, and releases track Chromium closely ([Electron 44 news](https://tech-insider.org/electron-44-7-0-chromium-152-node-24-2026/), secondary).

#### Turkish text in web engines

CSS `text-transform` and `toLocaleUpperCase('tr')` honour `lang="tr"` for dotted İ and dotless ı. WebKit fixed this in 2013 ([WebKit r156948](https://trac.webkit.org/r156948), [bug 21312](https://bugs.webkit.org/show_bug.cgi?id=21312)), and Chromium runs the web-platform-test for it ([WPT test](https://chromium.googlesource.com/external/w3c/web-platform-tests.git/+/HEAD/css/CSS2/text/text-transform-bicameral-005.xht)). Current behaviour should be checked with a test in our suite **[unverified for current releases]**. Rule: always set `<html lang="tr">` and never call bare `toUpperCase()`.

#### Accessibility and keyboard

Chromium and WebKit expose the ARIA tree to UIA and NVDA on Windows and to AT-SPI on Linux. Mature headless React libraries (React Aria, Radix) ship keyboard and ARIA behaviour, so agents compose accessible widgets instead of hand-rolling them **[well known; not fetched this session]**.

### 3.2 PySide6 + Qt Widgets (today)

- **Design freedom.** Low to medium. Stylesheets (QSS) are a subset of CSS 2. Animation needs code (`QPropertyAnimation`), and custom looks mean custom `paintEvent`s. The project's own experience is that the result "looks poor". Nothing new here.
- **Memory.** Best of the mainstream options: 259 MB for today's UI [spike]. The Python link is in-process and synchronous. The licence is LGPL (PySide6).
- **Agents.** Python is strong. Qt Widgets code is plentiful but old-style, and there is no Playwright-class testing. pytest-qt and `QWidget.grab()` screenshots work.

### 3.3 PySide6 + QML / Qt Quick

- **Design freedom.** Much higher than Widgets. QML has declarative states, transitions, shaders, and `Control` templates you can fully restyle. Qt Quick Controls ships styles (Basic, Fusion, Material, Universal, Imagine, and FluentWinUI3 from Qt 6.8 **[style list partly unverified]**), all of which can be customised ([Qt Quick Controls](https://doc.qt.io/qt-6/qtquickcontrols-index.html)). Figma-to-QML tooling exists: the new "Figma to Qt" generates QML directly ([Qt blog](https://www.qt.io/blog/introducing-figma-to-qt-the-fastest-way-to-bring-figma-designs-to-the-product)). The older Qt Bridge for Figma is Enterprise-only and no longer developed ([Qt docs](https://doc.qt.io/qtdesignstudio/qtbridge-figma-template.html)). So yes, QML can produce a modern custom design. The ecosystem is the problem: it has nothing like shadcn/ui, Radix or TanStack Table, so tables, comboboxes, date pickers and command palettes have to be built by hand.
- **Licence traps.** Qt Quick Controls is LGPLv3/GPLv2 ([Qt Quick Controls](https://doc.qt.io/qt-6/qtquickcontrols-index.html)). Several modules are **GPL-only** for open-source use: Qt Graphs, Qt Lottie, Qt Quick 3D, **Qt Quick Timeline**, Qt Virtual Keyboard, **Qt Qml Compiler** and others ([Qt licensing](https://doc.qt.io/qt-6/licensing.html)). Using any of them blocks the commercial build unless the owner buys a Qt commercial licence. The Qt Quick Compiler (AOT) is a startup optimisation, and it is on that GPL list.
- **Memory and performance.** Probably close to today's Qt figure, plus the scene-graph GPU cost. It is GPU-accelerated, and software rendering is available for old GPUs **[not measured]**.
- **Python link.** In-process, as today.
- **Agents.** QML exists in far less public code than React and there is no public benchmark, so this is **unmeasured**. From experience, agents mix up Qt 5 and Qt 6 QML syntax and import versions **[anecdotal]**. There is no browser-grade inspector or Playwright, so screenshots are self-built with `grabWindow`.

### 3.4 Qt in C++ (Widgets or QML), Python as a separate process

This option has the same design ceiling as 3.2 and 3.3, adds a C++ build, and needs IPC to Python. The language agents handle worst of the shortlist, with the most memory-safety risk, replaces the Python UI layer. It gains memory over PySide6 but none of the owner's priorities. **Rejected.**

### 3.5 C# / .NET

- **.NET release cycle.** LTS releases get 36 months (.NET 10, released November 2025, is supported to November 14, 2028). STS releases now get 24 months ([.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core), [heise](https://heise.de/-11120775)). That means a forced major upgrade every two to three years.
- **Avalonia UI.** The core is MIT, and a sponsorship deal requires it to stay MIT ([Avalonia blog](https://avaloniaui.net/blog/building-a-sustainable-future-for-avalonia), [DevClass](https://devclass.com/2025/06/26/avalonia-ui-sponsorship-completely-removes-open-source-vs-commercial-conflict-claims-ceo/)). Paid Accelerate tier: **TreeDataGrid** (since 11.2.0), **WebView**, Media Player, Markdown Viewer, and the new Dev Tools and VS extension. Prices are about €219 per seat for Business and €599 for Enterprise, with 12 months of updates ([discussion #19804](https://github.com/AvaloniaUI/Avalonia/discussions/19804), [NuGet TreeDataGrid](https://www.nuget.org/packages/Avalonia.Controls.TreeDataGrid/)). The free Community tier grants no right to redistribute Accelerate components ([Community Edition](https://docs.avaloniaui.net/accelerate/community)). An AGPL app that ships the paid TreeDataGrid is a licence conflict, so you would use the archived MIT fork or the planned free v12 Table control (same discussion). Design freedom is high (Skia-rendered, fully templatable styles), Linux support is good (Avalonia's own Linux focus: [Avalonia for Linux](https://avaloniaui.net/platforms/linux)), and headless screenshots work (section 2). Against it: C# agent success is lower (earlier SWE-Sharp-Bench result) and Python needs IPC.
- **.NET MAUI.** It has no official Linux target. An Avalonia-built backend for Linux and WASM is in preview with .NET 11 ([The Register](https://www.theregister.com/2025/11/13/dotnet_maui_linux_avalonia/), [Avalonia MAUI preview](https://avaloniaui.net/blog/maui-avalonia-preview-1)). The desktop look is mobile-first. **Rejected** for Pardus.
- **WinUI 3 / WPF.** Windows-only, which fails priority 3. WPF's design freedom is high but tooling is old. **Rejected.**
- **Uno Platform.** The framework is Apache-2.0, with a paid Studio for tooling ([Uno pricing](https://platform.uno/pricing)). It has a Skia desktop target on Linux with X11/Wayland DPI caveats ([Uno Skia docs](https://platform.uno/docs/articles/features/using-skia-desktop.html)). It is a smaller community than Avalonia, and it shares the C# and IPC costs.

### 3.6 Flutter desktop (Dart)

- **Design freedom.** Very high: Flutter draws every pixel and has strong animation.
- **Maintenance.** Google handed desktop stewardship to Canonical at I/O 2026. Canonical now leads the desktop roadmap and the embedders ([OMG! Ubuntu](https://www.omgubuntu.co.uk/2026/05/flutter-desktop-canonical-maintained)). That is good for Linux, but the governance change is new. Multi-window was still a preview in 3.44 ([Flutter 3.44](https://flutter.dev/blog/whats-new-in-flutter-3-44), [Canonical](https://canonical.com/blog/multiple-window-flutter-desktop)).
- **Accessibility on Windows.** The engine turns semantics on only when Windows sends an accessibility query, because not every screen reader (Narrator included) sets the system flag ([engine source](https://flutter.googlesource.com/mirrors/engine/+/4fddc0160af856de1c60cd8274a135d8d69f588c/shell/platform/windows/window.cc), [Windows a11y doc](https://flutter.googlesource.com/mirrors/flutter/+/HEAD/docs/platforms/desktop/windows/Accessibility-on-Windows.md)). Some IME messages are still TODO ([flutter#74547](https://flutter.googlesource.com/mirrors/engine/+/4fddc0160af856de1c60cd8274a135d8d69f588c/shell/platform/windows/window.cc)). Turkish uses a plain keyboard layout rather than an IME, so it is probably unaffected **[unverified]**.
- **Python link.** IPC only. Dart and Python have no in-process bridge.
- **Agents.** Dart has less public code than TS. Golden tests are a plus, but desktop-specific examples are thin.
- **Licence.** BSD-3 **[not re-fetched]**.

### 3.7 Others, briefly

- **Compose Multiplatform (Kotlin/JVM).** Design is good, Windows 10+ is supported ([compat docs](https://kotlinlang.org/docs/multiplatform/compose-compatibility-and-versioning.html)), and JVM memory is about 108–180 MB idle by anecdote ([lightrun issue](https://lightrun.com/answers/jetbrains-compose-jb-memory-usage-seems-surprisingly-high-mostly-coming-from-native-code-non-java), [Kotlin Slack](https://slack-chats.kotlinlang.org/t/23174617/anyone-done-much-recent-experimentation-with-compose-desktop)). It adds a JVM next to Python and is a fourth language. Not a fit.
- **Slint.** Licensed GPLv3, royalty-free (desktop, attribution required) or commercial ([LICENSE.md](https://raw.githubusercontent.com/slint-ui/slint/HEAD/LICENSE.md)). GPLv3 is compatible with the AGPL build, and the royalty-free licence covers a proprietary desktop build as long as it carries attribution, so the licence fits. It is lightweight and has Python bindings **[maturity of Python bindings unverified]**. The ecosystem is small and agents have little data, so complex tables and grids would be hand-built.
- **GPUI (Rust, Zed).** Apache-2.0 per a third-party book; Zed itself is GPL ([gpui-book](https://vanuan.github.io/gpui-book/appendix_a.html)). It is consumed as a git dependency, and the third-party `gpui-component` library (Longbridge, Apache-2.0) powers a production trading app ([gpui-component](https://github.com/longbridge/gpui-component)). It is pre-1.0 with churning APIs, Rust-only, and has few examples. The claim that Discord's rewrite uses GPUI is **[unverified, no source found]**.
- **Dioxus.** Desktop rendering goes through a system webview (wry), so it has the same WebKitGTK exposure as Tauri, written in Rust instead of TS **[not fetched]**.
- **wxWidgets.** Native widgets give it the lowest design freedom on the list. **Rejected.**

## 4. Scored comparison

Scale 1–5 (5 = best). Weights: priority 1 ×3, priority 2 ×3, priority 3 ×2, every secondary criterion ×1. The memory score assumes a 4–8 GB older PC.

| Option | P1 Design freedom | P2 AI agents | P3 Multi-OS | Memory/startup | Installer size | Licence fit | Python link | Maintenance risk | **Weighted (max 60)** |
|---|---|---|---|---|---|---|---|---|---|
| **pywebview + React** (WebView2 / QtWebEngine on Linux) | 5 | 5 | 4 | 2 | 4 (Win) / 2 (Linux w/ QtWebEngine) → 3 | 5 | 5 (in-process) | 3 (single maintainer, thin layer) | **56** |
| **Electron + React** | 5 | 5 | 5 | 1 | 2 | 5 | 3 (sidecar) | 5 | **56** |
| Tauri 2 + React | 5 | 4 (Rust host) | 3 (WebKitGTK) | 2 | 4 | 5 | 3 (sidecar) | 4 | **51** |
| PySide6 + QML | 4 | 3 | 4 | 4 | 3 | 3 (GPL-only modules to avoid) | 5 | 4 | **48** |
| Avalonia (C#) | 4 | 3 | 5 | 4 | 3 | 3 (Accelerate parts) | 2 | 3 | **46** |
| PySide6 + Widgets (today) | 2 | 3 | 4 | 4 | 3 | 5 | 5 | 4 | **44** |
| Flutter desktop | 5 | 3 | 4 | 4 | 3 | 5 | 2 | 3 | **49** |
| Slint | 3 | 2 | 4 | 5 | 5 | 4 | 3 | 3 | **43** |
| Uno Platform | 4 | 2 | 4 | 3 | 3 | 4 | 2 | 3 | **41** |
| Compose MP | 4 | 3 | 4 | 3 | 2 | 5 | 2 | 4 | **45** |
| GPUI | 4 | 2 | 3 | 5 | 5 | 5 | 2 | 2 | **43** |
| Qt C++ | 4 | 2 | 4 | 5 | 3 | 3 | 2 | 4 | **43** |
| .NET MAUI / WinUI / WPF | 3 | 3 | 1–2 | 3 | 3 | 4 | 2 | 3 | **~35** |

Arithmetic example for pywebview: 5·3 + 5·3 + 4·2 + 2 + 3 + 5 + 5 + 3 = 56. pywebview and Electron tie at 56. The tie is broken on the two criteria that matter most for this product's users: memory on old PCs (Electron adds Node and a bundled Chromium) and an in-process Python link with no sidecar to supervise. Electron wins on maintenance risk and identical rendering on every OS. All scores are judgement on the evidence above, not measurements.

## 5. Recommendation

**Build the UI in React + TypeScript and host it with pywebview: WebView2 on Windows, `gui='qt'` (QtWebEngine/Chromium) on Linux, WKWebView on macOS. Keep Python in-process.**

Why:

1. **Priority 1.** Only the web stack offers a design ceiling plus an off-the-shelf component ecosystem (headless accessible primitives, virtualised grids, editable tables, canvas libraries). QML and Flutter match the ceiling, but you would build the components yourself.
2. **Priority 2.** TS/React is GitHub's top language and the only stack with public UI-generation benchmarks. Playwright can screenshot the same UI in plain Chromium during CI and inside WebView2 over CDP ([Playwright WebView2](https://playwright.dev/python/docs/webview2)).
3. **Priority 3.** Choosing the Qt backend on Linux sidesteps the WebKitGTK problems that Tauri documents itself ([Tauri Linux graphics](https://v2.tauri.app/develop/debug/linux-graphics/)) and gives Chromium on both main targets. macOS on WKWebView is acceptable as a nice-to-have.
4. **In-process Python.** The bridge measured 0.2 ms [spike], with no sidecar lifecycle, ports or installer-replacement bugs ([tauri#15134](https://github.com/tauri-apps/tauri/issues/15134)).
5. **Licence.** BSD-3 (pywebview), LGPL (PySide6/QtWebEngine), WebView2 is a system component, and React is MIT, so the stack fits AGPL and the commercial build alike. Avoid the GPL-only Qt modules listed in [Qt licensing](https://doc.qt.io/qt-6/licensing.html). None of them are needed in this design.

Make it cheap to change your mind:

- Put every UI→backend call behind one TypeScript `bridge` module with typed request/response objects (e.g. generated from Pydantic models). The UI must not know whether it is talking to pywebview's `window.pywebview.api`, a WebSocket or Electron IPC.
- Keep the backend runnable as a standalone process (stdio or WebSocket server) as well. Then Electron or Tauri is only a shell swap.
- Cut memory: thumbnail sizes tied to devicePixelRatio, decoded off the main thread, a bounded image cache, `content-visibility`, and `MemoryUsageTargetLevel=Low` when minimised ([MS docs](https://learn.microsoft.com/en-us/dotnet/api/microsoft.web.webview2.core.corewebview2.memoryusagetargetlevel)). Set a budget, for example under 450 MB for the whole app on a 1000-page job, and re-measure on a 4 GB Windows 10 machine **[target, not yet measured]**.
- Set `<html lang="tr">`, call `toLocaleUpperCase('tr')` only through one helper, and add a Playwright test for İ/ı casing and sorting (`Intl.Collator('tr')`).

## 6. Runner-up

**Electron + React with the Python backend as a sidecar.** It renders identically on all OSes, has first-class Playwright support and the lowest maintenance risk. It loses on installer size (about 85–106 MB extra) and memory (Chromium plus Node, on PCs that already struggle). The sidecar also has to be supervised. With the bridge abstraction above, moving there costs a few days of work, not a rewrite.

**Best non-web fallback: PySide6 + QML.** If memory on old PCs proves to be the deciding factor, QML keeps Python in-process and roughly Qt-level memory, and it can look modern. Expect much more hand-built component work, weaker agent output, and care to stay off the GPL-only modules.

## 7. What would change the recommendation

- **pywebview stalls** (no release for about 12 months, or a blocking WebView2/QtWebEngine bug with no fix): move to Electron.
- **The Pardus field test fails with the Qt backend** (QtWebEngine GPU blocklist, or software rendering too slow on old Intel iGPUs): try Electron first, since it ships its own Chromium with its own GPU fallbacks. Tauri does not fix this, because it would put the app on WebKitGTK.
- **Memory on target PCs stays above about 600 MB after optimisation and causes swapping on 4 GB machines:** switch to PySide6 + QML.
- **macOS becomes a primary target:** test WKWebView in pywebview thoroughly. If it diverges, Electron gains points.
- **A credible public benchmark shows agents producing QML, Dart or XAML UI at React-level quality:** re-score priority 2. No such benchmark exists today.
- **Avalonia makes TreeDataGrid/WebView free again, or the free v12 Table control covers editable grids:** Avalonia rises. It still loses on in-process Python and agent success rates.

## 8. Unverified items, collected

- The QtWebEngine size overhead on Linux (about 100+ MB) is an estimate.
- That Pardus 23 ships the same webkit2gtk as Debian 12 is not confirmed.
- That current Chromium and WebKit releases still apply Turkish casing correctly needs our own test.
- The Qt Quick Controls style list (FluentWinUI3 from Qt 6.8) comes from memory.
- The Flutter golden-test API, the Electron/Tauri/Flutter licences and Playwright's Electron API were not re-fetched this session.
- Dioxus's desktop renderer, the maturity of Slint's Python bindings, and Discord's use of GPUI are unverified.
- Agent quality on QML, Dart, Slint and XAML is unmeasured, and anecdotes are marked as such.
- All weighted scores are judgement. Memory figures other than the spike are anecdotal third-party numbers.
