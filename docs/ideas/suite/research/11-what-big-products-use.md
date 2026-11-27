# What big products use for their desktop apps, and how it turned out

Research date: 2026-11-27. Each claim links to its source. Source labels:
**[P]** primary (company blog, docs, official repo, job post, release notes, the company's own people).
**[S]** secondary (press, third-party analysis, community wiki, forum).
**UNVERIFIED** means I could not confirm it from a source I reached; treat it as a lead, not a fact.

---

## 1. Summary table

| Product | Desktop UI tech | Core / backend | Changed? | Main lesson |
|---|---|---|---|---|
| Notion | Electron (React web app) | TS/JS; SQLite cache on desktop | No; added SQLite, native engineers | Keeps Electron but hires native Mac/Windows and Electron-core engineers |
| Slack | Electron | JS/TS | Rewrote inside Electron, 2019 | Fixed memory by changing architecture, not framework |
| VS Code | Electron | TypeScript + Node | No | A web editor (Monaco) became the #1 editor on Electron |
| Obsidian | Electron (Capacitor on mobile) | JS/TS, local Markdown | No | Small team, one codebase, plugin ecosystem |
| Linear | Electron wrapping the web app | TS, local-first sync engine | No | Speed comes from local data, not the shell |
| Figma | Electron shell; web UI + C++→WASM canvas | C++ (WASM) | asm.js→WASM (2017); WebGPU (2025-26) | Heavy core in native code; UI in web |
| Discord | Electron → Rust + GPUI ("Phoenix") | Rust | Yes, announced Nov 2026 | Memory/startup pain after ~10 years; months-to-years rewrite |
| 1Password 8 | Electron | Rust core | Yes (2021): native Mac/Win apps → one Electron UI | Fewer apps to maintain; users disliked non-native feel |
| Signal Desktop | Electron | libsignal (Rust) | Chrome App → Electron (2017) | Forced move; reused web code |
| Postman | Electron | JS | Chrome App → Electron (~2014-16) | Same pattern as Signal |
| Skype | Electron; RN detour on Win10 2018-20 | — | Back to Electron 2020 | React Native experiment reversed |
| Microsoft Teams | Electron/Angular → WebView2/React (2023) | web | Yes | Same web UI, OS webview, Fluent UI |
| New Outlook (Windows) | WebView2 + native integration layer | Outlook web | Yes, replaced Win32 Outlook path | One codebase with web; lost COM add-ins |
| WhatsApp (Windows) | native UWP/WinUI → WebView2 (2025) | web | Yes, native → web | Velocity/one codebase beat ~30% more RAM |
| Office / Windows shell | React Native for Windows islands in native apps | C++ | Partial; Start menu moving parts back to WinUI (2026) | Mixed results |
| GitButler | Tauri 2 + Svelte | Rust | — | Best-known Tauri product; few large ones exist |
| Telegram Desktop | Qt (C++) | C++ | No | Very light, fast; deep C++ skills needed |
| OBS Studio | Qt (Qt5→Qt6 in v28) | C/C++ | Qt upgrade only | Heavily themed Qt (QSS) |
| DaVinci Resolve | Qt 5 (bundled libs) | C++/GPU | No | Pro app; Linux support narrow |
| Autodesk Maya | Qt since 2011 (PySide for scripting) | C++ | Motif/Carbon → Qt (2011) | Qt unified three platform toolkits |
| Calibre | PyQt (Qt 6 since 6.0) | Python | Qt5→Qt6 (dropped 32-bit) | One developer + Python + Qt, for ~20 years |
| Anki | PyQt shell + Svelte/TS web screens | Rust core (rslib) + Python | Gradually moving screens to web | Hybrid: Qt shell, web screens, Rust core |
| Dropbox | Qt (2014) → Electron/React (UNVERIFIED) | Python → Rust sync engine "Nucleus" (2020) | Yes (core) | Rewrote core in Rust, UI became web |
| Mercedes MBUX | Qt / QML on Wayland | C++ | Expanded to MB.OS (2023) | Qt wins in embedded/automotive |
| Visual Studio | WPF (since VS 2010) | C++/C# | Win32 → WPF (2010) | Windows only |
| JetBrains Rider | IntelliJ (JVM) frontend | ReSharper (.NET) backend | — | UI process and engine process are separate |
| dotMemory / dotTrace | Avalonia (Mac/Linux, Rider integration) | .NET | WPF-only → Avalonia | .NET cross-platform via Avalonia |
| Paint.NET 5 | .NET + Direct2D GPU rendering | C# | — | Windows only |
| MS Photos, Settings | WinUI 3 / Windows App SDK | C++/C# | UWP → WinAppSDK (2024) | Windows only |
| Ubuntu installer, App Center | Flutter | Dart + Python/Go backends (subiquity) | GTK/Ubiquity → Flutter (22.04-24.04) | Flutter works on Linux; few non-Canonical big desktop apps |
| Adobe Acrobat | native C++; embedded web views; CEF → OS WebView (2026) | C++ | Moving off CEF | Even Acrobat hosts web UI inside native |
| ABBYY FineReader | Win32/MFC (UNVERIFIED) | C++ | — | — |
| PDF-XChange Editor | native Windows (C++ UNVERIFIED) | COM/C++ | — | Windows only |
| Foxit PDF Editor | Qt on Linux (UNVERIFIED) | C++ | — | — |
| NAPS2 | Eto.Forms (WinForms / GTK / Mac) | C# | Win-only → cross-platform | Scanning app with one .NET UI for 3 OSes |
| Paperless-ngx | Web (Angular) | Python (Django, Celery), OCRmyPDF/Tesseract | — | Python OCR backend + web UI, closest to Evrakçı |
| Zed | GPUI (own Rust GPU UI) | Rust | Prototype was Electron; dropped it | Built a UI framework; huge effort |

---

## 2. Electron and web products

**Notion.** Notion's desktop is Electron. Its own job post calls the Windows app "the Electron-based frame through which many of our most active and engaged users experience Notion", says it has "several Electron core maintainers on our team" and hires native macOS and Windows engineers to work with OS APIs [P] ([Greenhouse job](https://job-boards.greenhouse.io/notion/jobs/6585275003), [Built In listing](https://builtin.com/job/software-engineer-native-macos-development/6739386)). Performance work went into data, not the shell: desktop moved its cache from IndexedDB to SQLite after quota limits, bugs and slowness on Windows [P] ([Notion blog](https://www.notion.com/blog/faster-page-load-navigation)); later WASM SQLite in browsers gave about 20% faster navigation [P] ([Notion blog](https://www.notion.com/blog/how-we-sped-up-notion-in-the-browser-with-wasm-sqlite)), and the cache later became a real offline store [P] ([Notion blog](https://notion.com/blog/how-we-made-notion-available-offline)). Lesson: a company with hundreds of engineers still stays on Electron and buys native expertise for the edges.

**Slack.** In 2019 Slack rebuilt its desktop client because each workspace ran a separate copy of the web client in its own Electron process. Result claimed by Slack: up to 50% less memory, 33% faster launch [P] ([Slack Engineering](https://slack.engineering/rebuilding-slack-on-the-desktop/), [Slack blog](https://slack.com/intl/en-gr/blog/productivity/introducing-a-more-efficient-slack-desktop-experience)). They stayed on Electron. Lesson: the biggest memory win came from architecture.

**VS Code.** Started as "Monaco", a browser editor; Erich Gamma describes VS Code as a failed online editor pivoted to desktop [S] ([The Register](https://www.theregister.com/2021/01/28/erich_gamma_on_vs_code/)). Built on Electron, TypeScript and Node [S] ([Erich Gamma, Wikipedia](https://en.wikipedia.org/wiki/Erich_Gamma)). It is the counter-example to "Electron is slow": heavy work goes to separate processes (language servers, extension host). Gamma's own reasons for Electron are in a podcast I did not get a transcript of (UNVERIFIED rationale) ([podcast listing](https://metacast.app/podcasts/episode/12173f33_9b95_55a0_9131_4f6f7f394e26_046914d8_ec9f_4132_8498_7c0d005c1ea2)).

**Obsidian.** Electron on desktop, Capacitor on mobile [S] ([rywalker.com](https://rywalker.com/research/obsidian), [forum thread](https://forum.obsidian.md/t/what-framework-did-the-developer-use-to-create-obsidian-desktop-application/30724)). Very small team; local Markdown files and a plugin API (plugins are web code) drove adoption [S] ([MacStories](https://www.macstories.net/news/obsidians-popularity-explained/)). Founders' reason for Electron: UNVERIFIED.

**Linear.** Electron wrapping the same React web app; speed comes from a local-first sync engine (in-memory object graph, IndexedDB) [S] ([performance.dev](https://performance.dev/how-linear-feels-instant), [HN](https://hn.svelte.dev/item/44833834)); Linear's own talk on the sync engine [P] ([Linear](https://linear.app/blog/scaling-the-linear-sync-engine)). Lesson: "feels native-fast" is a data-layer achievement.

**Figma.** UI in web tech, the canvas engine in C++ compiled to WebAssembly; switching asm.js→WASM cut load time more than 3x (2017) [P] ([Figma blog](https://www.figma.com/blog/webassembly-cut-figmas-load-time-by-3x/)); later WebGPU rendering [P] ([Figma blog](https://www.figma.com/blog/figma-rendering-powered-by-webgpu/)). Desktop app is Electron [S] ([figma-linux](https://github.com/Figma-Linux/figma-linux)). Lesson: web UI around a native core is a deliberate high-end design, not a compromise.

**Discord.** CTO Stanislav Vishnevskiy announced on X (4 Nov 2026) that the desktop client is being rebuilt in Rust on GPUI (the Zed UI framework), codename "Phoenix"; mobile drops React Native for native views sharing a Rust core; browser keeps HTML with logic in WASM. Early build showed ~290 MB RAM with two accounts and near-instant cold start vs 5.5 s on Electron — self-reported, not independently verified. InfoQ notes GPUI lacks much of what browsers give for free: text layout, IME, screen-reader hooks, right-to-left; embedded web content will use the OS webview. No release date [S] ([InfoQ, 19 Nov 2026](https://infoq.com/news/2026/11/discord-rust-rewrite-gpui-zed), [Inven Global](https://www.invenglobal.com/articles/28182/discord-cto-confirms-the-desktop-and-mobile-apps-are-being-rebuilt-in-rust)). Context: Discord already used Rust since 2018 for infrastructure and voice. Lesson: a company with a large Rust team, ten years in, can afford this; the RTL/IME/accessibility gaps matter for Turkish text input too.

**1Password 8 (2021).** Replaced separate native Mac and Windows apps with one Electron UI over a shared Rust core; goal: "every feasible piece of 1Password into the Core library, stopping just short of the user interface" [P] ([1Password blog](https://1password.com/blog/1password-8-the-story-so-far)). Reason: fewer apps to maintain [S] ([Mac Observer summary](https://macobserver.com/?p=117449)). Strong user backlash about non-native Mac feel [S] ([community thread](https://www.1password.community/1password-at-home-31/1password-8-non-native-feel-16936/index2.html), [Michael Tsai](https://mjtsai.com/blog/2021/08/11/1password-8-for-mac-early-access/)). They did not reverse it. Lesson: moved TO web for velocity; native-feel complaints are real but survivable.

**Signal Desktop.** Forced off Chrome Apps in 2017, converted the existing web code to Electron "without too many changes" [P] ([Signal blog](https://signal.org/blog/standalone-signal-desktop/)). Crypto core libsignal is Rust exposed to TypeScript [S] ([Eclipse issue](https://gitlab.eclipse.org/eclipse/oniro-core/ohos-planning/-/issues/72)).

**Postman.** Chrome App → Electron, around 2014–2016 (sources disagree) [S] ([unofficial architecture docs](https://postman-app-architecture.pages.dev/docs/architecture/overview), [Apidog, competitor](https://apidog.com/blog/postman-slow-bloated-2026-alternatives/)). Frequent "slow and bloated" complaints, though that source is a competitor.

**ClickUp.** Has Windows/macOS/Linux desktop apps [P] ([ClickUp blog](https://clickup.com/blog/how-to-use-clickup-desktop-app/)); Electron is likely but UNVERIFIED.

**Skype.** Skype 8 desktop was Electron (2017) [S] ([BetaNews](https://betanews.com/2017/08/18/microsoft-releases-skype-for-desktop-8-preview)); the Windows 10 app went React Native in 2018, then was replaced by the Electron version in 2020 [S] ([Neowin](https://www.neowin.net/news/microsoft-officially-replaces-react-native-based-skype-on-windows-10-with-electron-version), [Windows Central](https://www.windowscentral.com/microsoft-swaps-skype-over-electron-windows-10)).

## 3. WebView2 and native-web hybrids (Microsoft)

**Teams 2.0.** Moved from Electron to WebView2, Angular to React, adopted Fluent UI; Microsoft credits shared Edge resources for lower memory and disk [P] ([Teams blog](https://techcommunity.microsoft.com/blog/microsoftteamsblog/microsoft-teams-advantages-of-the-new-architecture/3775704)). Main executable under 12 MB vs over 134 MB [P] ([Teams security blog](https://techcommunity.microsoft.com/t5/microsoft-teams-blog/what-s-new-for-security-in-the-new-microsoft-teams/ba-p/3804261)). The "50% less memory" was a 2021 projection by Microsoft's Rish Tandon for consumer accounts [S] ([Office365ITPros](https://office365itpros.com/2021/06/25/teams-2-webview2-replaces-electron/)). Enterprise GA date (2023) UNVERIFIED here. Lesson: Microsoft kept the web UI and swapped only the host.

**New Outlook for Windows.** Built on WebView2 with a "Native Windows Integration Component", experience taken from Outlook on the web; COM add-ins not supported [P] ([Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365-apps/outlook/overview-new-outlook-windows)). Goal: ship features once across web and desktop [S] ([Directions on Microsoft](https://www.directionsonmicrosoft.com/charts-illustrations/new-outlook-relies-on-web-and-edge-2)). Widely criticised by power users [S] ([Windows Central](https://www.windowscentral.com/software-apps/office-365/new-desktop-outlook-is-a-bad-idea-heres-why)).

**React Native for Windows.** Office is "incrementally adopting React Native alongside Windows App SDK", embedding RN components via content islands [P] ([RN devblog, May 2025](https://devblogs.microsoft.com/react-native/2025-05-09-office-modernize)); Windows 11 Settings had RN pieces [P] ([RN devblog 2022](https://devblogs.microsoft.com/react-native/rnw-settings-win11)). The Start menu's React parts were reportedly being replaced with WinUI in 2026 for performance [S] ([Windows Latest](https://www.windowslatest.com/2026/03/21/microsoft-confirms-windows-11-start-menu-performance-boost-shift-to-winui-from-web-based-components/)). Mixed picture.

**WhatsApp for Windows (Meta).** Native UWP/WinUI app replaced by a WebView2 wrapper of web.whatsapp.com: beta July 2025, stable rollout around Nov 2025 [S] ([Windows Latest](https://www.windowslatest.com/2025/07/21/whatsapp-for-windows-11-is-switching-back-to-chromium-web-wrapper-from-uwp-native/), [Notebookcheck](https://www.notebookcheck.net/WhatsApp-ditches-native-Windows-11-app-in-favor-of-Microsoft-WebView2.1063682.0.html), [Daring Fireball](https://daringfireball.net/2025/11/meta_whatsapp_windows_shitty_web_app)). About 30% more RAM in Windows Latest's test. Meta gave no official reason; one-codebase maintenance is the press's inference. Clear "moved TO web for velocity" case.

## 4. Tauri

Few well-known companies ship Tauri. The clearest is **GitButler** (Tauri 2 + SvelteKit + Rust, on Mac/Windows/Linux) [P/S] ([GitButler GitHub](https://GitHub.com/gitbutlerapp), [docs.rs](https://docs.rs/but)). Other users are mostly small open-source apps ([awesome-tauri](https://github.com/tauri-apps/awesome-tauri)). A TheirStack page claims Discord used Tauri since 2020 — this looks wrong (Discord picked GPUI, explicitly "instead of Tauri") and is UNVERIFIED/doubtful ([TheirStack](https://theirstack.com/en/technology/tauri)). Tauri's weak spot on Linux is WebKitGTK; on old Windows, WebView2 availability (not researched here).

## 5. Qt

- **Telegram Desktop:** official C++/Qt client, Qt 6 (Qt 5.15 patched for older systems) [P] ([tdesktop README](https://raw.githubusercontent.com/telegramdesktop/tdesktop/dev/README.md)). Known for low memory and speed; needs strong C++ developers.
- **OBS Studio:** C/C++ with Qt; moved to Qt 6 in v28 (2022); heavy QSS theming [S] ([It's FOSS](https://itsfoss.com/news/obs-studio-28-release/), [OBS discussion](https://github.com/obsproject/obs-studio/discussions/6481)).
- **DaVinci Resolve:** Linux build ships its own Qt 5 libraries (`/opt/resolve/libs/libQt5*`) [S] ([Arch forum ldd](https://bbs.archlinux.org/viewtopic.php?id=248495), [Blackmagic forum](https://forum.blackmagicdesign.com/viewtopic.php?p=968207)). Exact Qt version UNVERIFIED.
- **Autodesk Maya:** since Maya 2011 all widgets use Qt on all platforms, replacing Motif (Linux) and Carbon (Mac); PySide/PySide2 for Python UI [P] ([Autodesk docs](https://download.autodesk.com/us/maya/2011help/files/WS73099cc142f48755527cc80126d167ffa2-7181.htm), [Autodesk PySide](https://help.autodesk.com/cloudhelp/2018/ENU/Maya-SDK/files/GUID-3F96AF53-A47E-4351-A86A-396E7BFD6665.htm)).
- **KDE Plasma:** Qt/QML (Kirigami). Not re-verified in this pass (UNVERIFIED in this report, but well known).
- **Calibre:** almost entirely Python with PyQt; Qt 6 since 6.0 (2022), which dropped 32-bit [S] ([It's FOSS](https://itsfoss.com/news/calibre-6-release.md), [README](https://raw.githubusercontent.com/kovidgoyal/calibre/master/README.md)). Mostly one developer (Kovid Goyal) since 2006 [S] ([Podcast.__init__](https://pythonpodcast.com/calibre-with-kovid-goyal-episode-187)). The strongest proof that one person + Python + Qt can ship a large, long-lived desktop app.
- **Anki:** Rust core (`rslib`), Python layer via `rsbridge`, GUI "a mix of Qt (via PyQt) and TypeScript/HTML/CSS"; most new code goes into `ts/` (Svelte), shared with mobile [P] ([Anki architecture docs](https://docs.ankiweb.net/developers/architecture)). Community debate: some argue Svelte screens add complexity and hurt performance [S] ([Anki forum](https://forums.ankiweb.net/t/ankis-svelte-future/45164)). Lesson: a Python/Qt app can migrate screen by screen to web via QtWebEngine.
- **Dropbox:** Windows/Linux UI rewritten in Qt in 2014 [S] ([OMG Ubuntu](https://www.omgubuntu.co.uk/2014/07/dropbox-experimental-linux-build-qt-rewrite)); current Mac app detected as Electron/React [S] ([Desktop Insights](https://desktopinsights.com/apps/dropbox)), job posts mention Electron [S] ([Built In](https://www.builtinseattle.com/job/engineer/software-engineer-desktop-platform/5696)) — the Qt→Electron change is UNVERIFIED by Dropbox. The sync engine was rewritten from Python to Rust ("Nucleus", 2020, ~4 years) [P] ([Dropbox Tech](https://dropbox.tech/infrastructure/rewriting-the-heart-of-our-sync-engine)). Lesson: Python was the original desktop language of a huge product; they rewrote the core for correctness at scale, not the UI for looks.
- **Mercedes-Benz MBUX:** Qt is the foundation of MBUX (A-Class, ~2017–18) and expanded to MB.OS in 2023; Mercedes builds "an entire UX platform on top of Qt and Wayland" [P, vendor] ([Qt press](https://www.qt.io/press/leading-premium-automaker-builds-next-generation-operating-system-with-qt), [Qt WS23 talk](https://www.qt.io/development/resources/videos/customer-case-mercedes-benz-with-victoria-fischer-qtws23)), [S] ([S&P Global](https://autotechinsight.spglobal.com/news/5272942/mercedes-benz-expands-partnership-with-qt-group-to-accelerate-software-defined-vehicles)). Shows QML gives full design freedom (custom, branded UIs).

## 6. .NET

- **Visual Studio:** shell rewritten in WPF for VS 2010 [P] ([VS blog](https://devblogs.microsoft.com/visualstudio/wpf-in-visual-studio-2010-part-1-introduction/)). Windows only.
- **JetBrains Rider:** frontend is IntelliJ Platform (JVM, Kotlin); backend is ReSharper (.NET) in a separate process, talking over a protocol [P] ([ReSharper SDK](https://jetbrains.com/help/resharper/sdk/Rider.html), [JetBrains blog 2016](https://blog.jetbrains.com/dotnet/2016/07/26/rider-the-story-so-far/)). Rider's main UI is NOT Avalonia.
- **dotMemory / dotTrace:** Mac and Linux versions and their Rider integration built on Avalonia [P, vendor] ([Avalonia case study](https://avaloniaui.net/success/jetbrains)). Other Avalonia users per vendor: Unity Plastic SCM, Schneider Electric HMI, Devolutions (18-year-old WinForms app) [P, vendor] ([Avalonia showcase](https://avaloniaui.net/showcase)).
- **Paint.NET 5.0 (Jan 2023):** .NET 7, Direct2D GPU rendering across the UI; dropped Windows 7/8.1 and 32-bit [P] ([Paint.NET blog](https://blog.paint.net/2023/01/10/paint-net-5-0-is-now-available/)). UI toolkit (WinForms) UNVERIFIED.
- **WinUI 3:** Microsoft Photos migrated from UWP to Windows App SDK (2024) [P] ([Windows dev blog](https://blogs.windows.com/windowsdeveloper/2024/06/03/microsoft-photos-migrating-from-uwp-to-windows-app-sdk/)); Settings and PowerToys Command Palette [P] ([Microsoft](https://developer.microsoft.com/windows/develop)). Windows only; no Linux.

## 7. Flutter desktop

Canonical made Flutter its desktop UI choice: the Ubuntu installer announced in Flutter (Feb 2021), default in 22.04-era builds [P] ([Ubuntu blog](https://ubuntu.com/blog/flutter-and-ubuntu-so-far)); 24.04 installer and first-boot setup are `ubuntu-desktop-provision` in Flutter [P] ([GitHub](https://www.github.com/canonical/ubuntu-desktop-provision), [Discourse](https://discourse.ubuntu.com/t/ubuntu-24-04-testing-week/43090/5)); App Center is Flutter [P] ([Launchpad](https://edge.launchpad.net/app-center)). Big Google desktop apps in Flutter: none found (UNVERIFIED/none). Flutter means Dart, a second language next to Python.

## 8. Document-heavy and capture products

- **Adobe Acrobat:** native C++ app hosting web UI. Release notes (page last updated 2026-10-29) say new 64-bit installs no longer include CEF and support "the transition to a WebView-based architecture", plus DirectX 12 rendering [P, seen via search snippet; page returned 403 to my fetcher] ([Adobe release notes](https://helpx.adobe.com/lt/acrobat/desktop/whats-new/release-notes.html)). The 2023 redesign was web-first, then desktop [P] ([Adobe Design](https://adobe.design/stories/process/a-modern-adobe-acrobat)).
- **ABBYY FineReader:** C++ engine (FineReader Engine SDK) [P] ([ABBYY jobs](https://job-boards.eu.greenhouse.io/abbyy/jobs/4604614101)); desktop UI tech (Win32/MFC suspected from a job post) UNVERIFIED.
- **PDF-XChange Editor:** Windows-only, COM/ActiveX SDK [P] ([Editor SDK info](https://pdf-xchange.com/editor-sdk-more-info)); C++ UNVERIFIED.
- **Foxit PDF Editor:** Linux build appears to need Qt libraries [S] ([AUR](https://aur.archlinux.org/packages/foxit-pdf-editor)); UI toolkit UNVERIFIED.
- **NAPS2 (scanning):** shared Eto.Forms GUI with WinForms, Mac and GTK subprojects — one C# UI on three OSes [P] ([NAPS2 wiki](https://github.com/cyanfish/naps2/wiki/3.-Project-Structure)).
- **Paperless-ngx:** Django + Celery backend, Angular frontend, OCRmyPDF/Tesseract [P] ([docs](https://docs.paperless-ngx.com/development/), [setup](https://github.com/paperless-ngx/paperless-ngx/blob/d8858ce5c6a8c927cd73ee80e1d610da24aba39f/docs/setup.md)). Closest architecture to Evrakçı (Python OCR pipeline, web UI), but it is a server app, not a desktop app.

## 9. Moved off Electron vs moved to it

**Off Electron (performance):** Zed — first prototype was Electron with a Rust backend; they wrote GPUI and render "like a videogame" at 120 fps [P] ([Zed blog](https://zed.dev/blog/videogame), [Zed 120fps](https://zed.dev/blog/120fps)); Discord (2026, above); Teams (to WebView2, still web UI). Only Zed and Discord left web UI entirely, and both are Rust-heavy companies; Zed spent years building a framework.

**To Electron/web (velocity, one codebase):** 1Password 8 (2021), Skype (back to Electron 2020), WhatsApp Windows (2025), new Outlook (WebView2), Signal and Postman (from Chrome Apps), Acrobat (CEF → WebView, keeps web UI). Dropbox UI likely too (UNVERIFIED).

The "to web" list is longer and includes Microsoft and Meta, which have the most native-UI expertise in the world.

---

## 10. Patterns

1. **Collaboration/SaaS companies with a web app pick Electron or WebView2.** Their main asset is the web codebase; desktop is a frame (Notion, Slack, Linear, Figma, Teams, Outlook, WhatsApp). Design freedom and velocity win; memory is the cost (WhatsApp ~30% more RAM; Discord 1–2 GB before the rewrite per press).
2. **Performance- and media-heavy tools pick Qt/C++ or custom GPU UIs.** Telegram, OBS, Resolve, Maya, Zed. These have C++/Rust teams and long time horizons.
3. **Windows-only business software picks WPF/WinUI/WinForms.** Visual Studio, Paint.NET, PDF-XChange. No Linux.
4. **Cross-platform .NET picks Avalonia or Eto** (JetBrains profilers, Unity Plastic, NAPS2).
5. **Native core behind a web UI is now the mainstream "serious" design.** Figma (C++/WASM), 1Password (Rust), Signal (Rust libsignal), Anki (Rust + Python behind Qt/Svelte), Dropbox (Rust sync engine), Acrobat (C++ hosting web views), Rider (separate engine process). Counting the products above with a web UI layer, about half keep a separate native/Rust/C++ core. The UI layer and the engine layer are deliberately separate processes or libraries.
6. **Speed comes from data and process architecture more than framework.** Slack's 50% memory cut and Linear's/Notion's speed came from process and local-data changes inside Electron.
7. **Rewrites are expensive and rare.** Dropbox's core took ~4 years; Discord has no date; Zed built a framework. Framework switches happen at ~5–10 year intervals.
8. **Native feel matters less to buyers than expected** (1Password, WhatsApp kept shipping despite backlash) — but those users are consumers; enterprise IT (Outlook COM add-ins) pushes back harder.

## 11. What this suggests for Evrakçı (one person + AI agents, Python core, older Windows PCs, Linux)

- **The closest real-world analogues are Calibre and Anki**: Python core + Qt shell, maintained by one or a few people for 15–20 years, cross-platform including Linux. Anki shows a route to web-designed screens inside Qt (QtWebEngine) without leaving Python. Paperless-ngx shows the same OCR stack (OCRmyPDF/Tesseract) behind a web UI.
- **The big-company "web UI + native core" pattern maps directly**: Python plays the role Rust plays for 1Password/Discord. Options in that family: (a) PySide6 + QML (full design freedom, MBUX-style), (b) PySide6 with QtWebEngine panels (Anki), (c) a web UI in Electron/Tauri/pywebview talking to a Python process (Paperless-like). All keep the OCR/form core untouched.
- **Design freedom and AI-agent ease favour web UI**: every large company that wanted one codebase and fast design iteration chose web; AI agents also have by far the most training data for HTML/CSS/React. Cost: memory. On older Windows PCs, Electron adds a bundled Chromium (~100+ MB per process, Discord 1–2 GB is the extreme); WebView2 shares Edge (Teams' approach) but needs the WebView2 runtime, which is present on Windows 11 and usually on updated Windows 10 (not verified here for Evrakçı's target machines). Linux webviews (WebKitGTK) are a known weak spot for Tauri/pywebview (not researched in depth here).
- **Avoid the Discord/Zed route** (custom GPU UI in Rust): it took companies with large Rust teams years, and InfoQ lists missing IME, RTL, screen-reader and text-layout support — Turkish input and accessibility are table stakes for office users.
- **Avoid Windows-only stacks** (WPF/WinUI) because Linux matters; Flutter works on Linux (Canonical) but adds Dart and has few large desktop references outside Canonical.
- **Copy the architecture lessons regardless of stack**: keep the UI a thin, replaceable layer over a separately testable Python core with a clear API (Rider, 1Password, Anki); put performance effort into data and background processes (Slack, Linear, Notion); and expect a framework to last 5–10 years, so choose the one whose failure mode is cheapest to escape — a clean core/UI boundary makes a later UI swap a project, not a rewrite.

UNVERIFIED items collected: ClickUp's Electron use; Obsidian's and VS Code's stated reasons for Electron; Dropbox Qt→Electron timing; Teams 2.0 GA date; KDE details (not re-checked); DaVinci Resolve exact Qt version; Paint.NET UI toolkit; ABBYY, PDF-XChange, Foxit UI toolkits; Discord performance numbers (self-reported); TheirStack's Discord-Tauri claim (likely wrong); any Google Flutter desktop app; WebView2 presence on target PCs.
