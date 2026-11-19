# 07 - Quality-of-life audit (code audit, read-only)

Scope: `src/evrakci/ui/*.py` and `src/evrakci/app.py`. Citations are `file:line` under `src/evrakci/ui/` unless a path is given. `kontrol.py`, `sablon.py`, `timeline.py` and `yukle.py` have uncommitted edits from a stopped redesign, so for those four the line numbers refer to the committed version (`git show HEAD:...`). Every other file was audited in the working tree. The screenshot tool ran and the six PNGs are in the scratchpad `qol/` folder. Nothing in the repo was modified.

## TL;DR

- The window is a fixed-size, fixed-font window with no zoom of any kind. There is no `wheelEvent`, `QSettings`, `QMenu` or `QMenuBar` anywhere in the UI, and no `contextMenuEvent`. Mouse wheel and Ctrl+wheel do nothing useful on thumbnails or the template canvas.
- The template canvas (`sablon.py:66` `PageCanvas`) only does `fitInView` on resize (`sablon.py:90`, `:107-110`). The user cannot zoom in to place a 1 mm box on a small field. This is the worst gap for a drawing tool.
- The Kontrol timeline thumbnails are rendered at a fixed 110 px height (`main_window.py:~204`, `ThumbnailService(..., height=110)`). There is no large page preview, no Space or double-click to enlarge, and no way to read what a page says. Staff have to trust a 110 px thumbnail for split decisions.
- The app has about 30 shortcuts, mostly bare letters (K, T, R, M, N, F, B, G, V). They are scoped per screen and none is a standard Office key except Ctrl+Z/Y/S/N/O/E. Missing: Ctrl+A, Ctrl+F, Ctrl+G, Ctrl+W, Ctrl+P, F5, F11, Ctrl+Tab, Ctrl+0/+/-, Home/End/PgUp/PgDn on the timeline, and a cheat sheet. **F1 is wired to switch to the Rehber tab** (`main_window.py:133`), not to help.
- Nothing is remembered between runs except the last opened job id (`main_window.py:~195` `son-is.txt`) and the retention choice (`disa_aktar.py:438-450`). Window size, maximised state, last tab, splitter sizes, export folder, column widths and zoom are all lost. `resize(1366, 768)` is hard-coded (`main_window.py:97`).
- Undo exists only in Kontrol and Şablonlar (two separate undo stacks, `controller.py:62`, `sablon.py:203`). Değerler edits (typing, accepting a suggestion) have no undo, and Ctrl+Z does nothing on that tab. Ctrl+Z/Y are screen-scoped (`WidgetWithChildrenShortcut`), so they only fire while focus is inside that tab.
- No right-click menus on thumbnails, job rows, batch rows, table cells or template variables. Every command must be found in the toolbar or remembered as a bare letter.
- Feedback is thin: a status-bar text line (`main_window.py:219`, `:155`), a "Kaydedildi HH:MM" label in the header (`main_window.py:81`), and QMessageBox confirmations. No toasts, no taskbar progress, no busy cursor, no sound. Progress bars exist per tab (`yukle.py:105`, `degerler.py:374`, `disa_aktar.py:353`).
- Accessibility basics are absent: no `setAccessibleName`/`setAccessibleDescription`, no `setTabOrder`, no `&` mnemonics, and the font is a hard-coded 15 px (`theme.py:60`) with 14 px in the status bar (`theme.py:136`). The only focus ring is a 2 px border on buttons, lists and inputs (`theme.py:180`, `:195`, `:240`). The UI will not follow Windows text-size or high-contrast settings.
- Good news: the base is clean. Shortcuts are hinted on buttons and in tooltips (`widgets.py:53-55`), the status bar lists per-tab keys (`main_window.py:36-45`), drops are accepted on Yükle (`yukle.py:44`, `:246-258`), and close is guarded while work is running (`main_window.py:288-305`). Most gaps can be closed with one new module (zoom + settings + shortcut help) plus small per-screen hooks.

## 1. Feature gap table

Severity: high = blocks accuracy or daily speed for the stated users; med = noticeable friction; low = polish.

| Feature | Office / Acrobat / Lightroom expectation | Evrakçı today | Sev | Suggested behaviour (keys, Turkish labels) |
|---|---|---|---|---|
| Zoom, template canvas | Ctrl+wheel zooms about the cursor; Ctrl+0 fit; Ctrl+1 100%; hand-drag with Space or middle button | Missing. Only `fitInView` on set_page and resize (`sablon.py:90`, `:107-110`). Plain wheel scrolls. | high | Ctrl+wheel and Ctrl+`+`/`-` zoom 25-400% about the cursor; Ctrl+0 "Sayfaya sığdır"; Ctrl+1 "%100"; Space+drag or middle-drag pans (only while not in "kutu çiz" mode). Do not re-fit on resize once the user has zoomed. |
| Zoom, timeline thumbnails | Lightroom grid slider, Acrobat thumbnail size; Ctrl+wheel resizes | Missing. Fixed `ITEM_H` and `height=110` (`timeline.py` module constants, `main_window.py:~204`). | high | Ctrl+wheel and a status-bar slider "Küçük resim boyu" 80-260 px; Ctrl+0 resets. Re-request thumbnails at the new height (the service already versions renders, `thumbnails.py:76`). |
| Large page preview | Acrobat/Lightroom Loupe: Space or double-click opens page large, arrows page through, Esc returns | Missing. Double-click on a page does nothing; `_current_changed` only fills the side card (`kontrol.py:422`). | high | Space or double-click on a page opens "Sayfa önizleme" (a dock or modal at about 900 px high); Left/Right previous/next page, Up/Down previous/next document, Esc closes; Ctrl+wheel zooms inside; shows page number, belge no, cut reason. |
| Whole-UI text scaling | Office/Windows follow system text size; Ctrl+wheel in many apps; Lightroom UI scale | Missing. `FONT_SIZE = 15` px fixed (`theme.py:60`, `apply_font` `:72`); stylesheet has many literal px sizes (`theme.py:136`, `kontrol.py:95`, `rehber.py:32,45`). | high | Settings "Yazı boyutu": Küçük 14 / Normal 15 / Büyük 17 / Çok büyük 20 px, applied by regenerating `theme.stylesheet()` with a scale factor; Ctrl+Shift+`+` / Ctrl+Shift+`-` do the same live. Needs literal px in per-widget `setStyleSheet` calls moved into theme tokens. |
| Rehber zoom | Browser/Word: Ctrl+wheel, Ctrl+`+`/`-` | Missing. `QTextBrowser` fixed 16 px via stylesheet (`rehber.py:44`). | med | Ctrl+wheel and Ctrl+`+`/`-` call `zoomIn/zoomOut` on the browser (the widget supports it natively but the stylesheet px size fights it; use `setFont` instead). |
| Status-bar zoom control | Word/Excel: slider + percent + "Sığdır" button at bottom right | Missing. Status bar has counts, checks, message, key list (`main_window.py:146-156`). | med | Permanent widget: `[-] ----o---- [+] %100 [Sığdır]`, bound to the zoom of the current tab (thumbnail height in Kontrol, canvas zoom in Şablonlar, hidden elsewhere). |
| Fit width / fit page | Acrobat: Ctrl+1 actual, Ctrl+2 fit width, Ctrl+0 fit page | Canvas always fits the whole page (`sablon.py:90`). No other fit modes. | med | Ctrl+0 "Sayfaya sığdır", Ctrl+2 "Genişliğe sığdır", Ctrl+1 "%100". |
| Keyboard paging on timeline | Home/End/PgUp/PgDn move; Ctrl+Home/End jump to first/last | Only what `QListView` gives for free (Left/Right, Home/End, PgUp/PgDn, Shift+arrows). Untested and undocumented. Status bar says "← → sayfa" only (`main_window.py:39`). | med | Document Home/End; add Ctrl+Left/Right "önceki/sonraki belge"; make PgUp/PgDn move one screen of thumbnails; show in the key list and cheat sheet. |
| Go to page / document | Word Ctrl+G; Acrobat Ctrl+Shift+N | Missing. `go_to_row` exists (`kontrol.py:333`) but is only called by the overview strip and N. | high (500+ page jobs) | Ctrl+G "Sayfaya git": small input "Sayfa no veya B12 (belge)". Also accepted: typing a number in a box on the strip. |
| Find / filter | Ctrl+F everywhere; Excel filter; Acrobat find | Only Değerler has a search box (`degerler.py:343`) and a filter line (`filter_line`), not bound to Ctrl+F. No find in Yükle jobs list, Kontrol, template list, Rehber text. | high | Ctrl+F focuses the search box on the current tab (Değerler existing box; add one for Yükle jobs, Şablonlar list, Rehber `QTextBrowser.find`). Esc clears and returns focus to the list. F3 / Shift+F3 next/previous match. |
| Select all / invert | Ctrl+A; Lightroom Ctrl+Shift+A deselect | Missing on timeline (ExtendedSelection supports Ctrl+A natively when the view has focus, but nothing documents it; no deselect or invert). | med | Ctrl+A "Hepsini seç"; Ctrl+Shift+A "Seçimi kaldır"; Ctrl+Shift+I "Seçimi ters çevir"; "Belgenin sayfalarını seç" on double-click of the document label. |
| Selection range | Shift+click range, Ctrl+click toggle, rubber band, Shift+arrow | Shift/Ctrl click via `ExtendedSelection` (`timeline.py:306`). No rubber band (QListView in single row has it only with `setSelectionRectVisible`). Status text "Shift seçimi genişlet" (`main_window.py:39-40`). | med | `setSelectionRectVisible(True)`; Ctrl+Shift+Left/Right extends selection by a document; click on the document header selects its pages. |
| Context menus | Right-click on every object with the common verbs and shortcuts shown | Missing everywhere. No `QMenu` use outside the stylesheet (`theme.py:266-268`). | high | Thumbnail: "Burada kes (K)", "Kesimi kaldır", "Sayfayı sil (Del)", "Döndür (R)", "Önceki belgeyle birleştir (M)", "Önizle (Space)", "Sayfa no kopyala". Yükle job row: "Aç", "Klasörü göster", "Yeniden adlandır (F2)", "Sil". Batch row: "Yukarı/Aşağı taşı", "Çıkar", "Dosyayı göster". Değerler cell: "Öneriyi kabul et (Enter)", "Elle yaz (F2)", "Boşalt", "Sayfayı göster". Şablon variable: "Yeniden adlandır", "Çoğalt", "Sil". |
| Menu bar / command palette | Office ribbon or menu; Fluent command bar; Ctrl+Shift+P / Ctrl+K palette | Missing. `setMenuWidget(HeaderBar)` replaces the menu bar with a branding strip (`main_window.py:99-100`, `:60-87`). | med | Add a slim menu bar (Dosya, Düzen, Görünüm, Araçlar, Yardım) inside the header, every item showing its shortcut; later a Ctrl+K "Komut ara" palette listing all actions. Menus also make Alt access keys work. |
| Shortcut cheat sheet | Office `?`/F1 help, Gmail `?`, Lightroom `Ctrl+/` overlay | Missing. Per-tab key list in status bar only (`main_window.py:36-45`). F1 = Rehber tab (`main_window.py:133`). | high | Ctrl+/ and Shift+F1 open "Klavye kısayolları" dialog grouped by tab, searchable; F1 opens "Yardım" (the Rehber content plus shortcuts). Generate the table from the real `QAction`s so it cannot go stale. |
| Discoverability of shortcuts | Tooltips and menu items show "Ad (Ctrl+X)" | Good on buttons: `KeyHintButton` tooltip "text (key)" (`widgets.py:53-55`). Not on the table, canvas, or tab bar items other than Ctrl+N (`main_window.py:129`, `:215`). Tooltip delay and wrap are Qt defaults. | low | Keep; add tooltips for canvas, timeline, thumbnails, status-bar items; show the key in menus. |
| Access keys / mnemonics | Alt+letter on menus and dialog buttons (`&Dosya`) | Missing: no `&` in any label. | low | Add `&` to menu titles (D&osya, D&üzen, G&örünüm, Y&ardım) and dialog buttons; choose ASCII letters. Qt Fusion shows underlines only while Alt is held, which is fine. |
| Standard keys | Ctrl+S save, Ctrl+W close tab/job, Ctrl+Tab next tab, Ctrl+P print, F5 refresh, F11 fullscreen | Ctrl+S only in Şablonlar (`sablon.py:216`); there is no document-level Save because jobs auto-save (header says "Kaydedildi", `main_window.py:81`). None of the others exist. | med | Ctrl+Tab / Ctrl+Shift+Tab next/previous tab; Ctrl+W "İşi kapat"; Ctrl+P prints separator sheets or the index (Rehber/Dışa Aktar); F5 refresh job lists and thumbnails; F11 full screen; Ctrl+S everywhere shows "Kaydedildi" toast (it is already saved). |
| Tab switching | Ctrl+1..9 / Ctrl+Tab | Ctrl+1..5 only (`main_window.py:128-132`); Rehber tab (6th) has no Ctrl+6 and uses F1 (`:133`). Ctrl+1 hint repeated "Ctrl+1…5" (`main_window.py:39`, `:44`). | low | Add Ctrl+6 = Rehber; Ctrl+Tab cycling; keep F1 for Yardım dialog. |
| Delete key | Delete removes selected; Shift+Delete skips bin | Kontrol "Del" toggles delete flag on pages (`kontrol.py:246`). Not on Yükle jobs/batches, Şablonlar variables/templates. | med | Delete on a batch row = "Partiyi çıkar" (existing confirm, `yukle.py:218`); on a variable = remove (undoable). |
| Undo / redo coverage | Ctrl+Z/Y everywhere, Edit menu shows "Geri al: <ad>", history list | Kontrol: `controller.undo_stack` (`controller.py:62`, shortcuts `kontrol.py:240-241`). Şablonlar: own stack (`sablon.py:203`, `:217`). Değerler/Yükle/Dışa Aktar: none. `remove_batch` explicitly clears the stack (`yukle.py` `remove_batch`: "geri alınamaz"). Ctrl+Shift+Z not bound. No "Geri al: …" text, no history panel. | high | Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z everywhere. Button labels "Geri al: Kesim ekle" using `QUndoStack.undoText()`. Put Değerler accept/type into the controller stack (`controller.run`). "Düzen > Geri alma geçmişi" opens `QUndoView`. Keep batch removal confirm. |
| Multi-select outside timeline | Excel ranges, Ctrl+click rows | Değerler table `SingleSelection` (`degerler.py:417`); Dışa Aktar results `SingleSelection` (`disa_aktar.py:363`); Yükle job and batch lists default single. | med | Değerler: allow `ExtendedSelection` to accept all suggestions in a selection ("Seçili önerileri kabul et", Ctrl+Enter). Yükle jobs: multi-select delete with confirm. |
| Drag and drop: files | Drop onto window opens | Works on Yükle only (`yukle.py:44`, `:246-258`). Dropping onto Kontrol or other tabs does nothing and gives no hint. Folder drop is not handled (only `.pdf` URLs). | med | Accept drops on the whole main window (`MainWindow.setAcceptDrops`), switch to Yükle, accept folders (scan for PDFs). Show a drop overlay "Bırakın: PDF ekle". |
| Drag and drop: reorder | Drag pages in thumbnails; drag rows | Missing. Batches move by Alt+Up/Down and buttons only (`yukle.py:133-135`, `:93-94`). Kontrol reorder not applicable to page order (physical), but dragging a cut line or a page to another document is absent. Template variables reorder by buttons (`sablon.py:263-265`). | med | Enable `InternalMove` drag on batch list and variable tree with a drop indicator; Kontrol: drag a document header to merge. Keep Alt+arrow as keyboard path. |
| Persistence: window | Office reopens at last size, position, monitor, maximised | Missing. Hard-coded `resize(1366, 768)` (`main_window.py:97`), min 1100x640 (`:98`). Min width 1100 fails on a 1024-wide office laptop. | high | `QSettings("Evrakci","Evrakci")`: `saveGeometry`, `saveState`, current tab, per-screen splitter sizes; restore on start, clamp to visible screen area; drop minimum to 1024x600. Add `--sifirla` / menu "Görünüm > Düzeni sıfırla". |
| Persistence: other | Recent files, last folder, column widths, sort order, zoom | Only last job id (`main_window.py:195` file `son-is.txt`, `LAST_JOB` `:31`) and retention (`disa_aktar.py:438-450`) via `pipeline.settings`. Export folder, last PDF open dir (`yukle.py:168`, `:187` pass `""`), column widths, filter state and zoom are not stored. | high | Remember: last open/save directories per dialog, last export folder (prefill `disa_aktar.py:230`), Değerler column widths and filter, timeline thumbnail size, canvas zoom, font scale, last tab. |
| Recent jobs | File > Open Recent; Lightroom recent catalogs | Yükle lists all jobs, no recency order or pin (`yukle.py:140-149`, store order). Last job reopens automatically. | low | Sort by last opened; show "Son açılan" badge and relative time ("dün 16:20"); "Dosya > Son işler" submenu with 5 entries. |
| Sort order / columns | Click header to sort, drag to resize, remember | Değerler `setSortingEnabled(False)` (`degerler.py:420`); Dışa Aktar results fixed. No column resize persistence. | low | Header click sorts "Sorunlu önce / Belge no / Ad"; save state. |
| Toasts / notifications | Non-blocking confirmations "Kaydedildi", with Undo | Missing. Status bar `message` label only (`main_window.py:155`, `:219`), cleared by nothing, and low contrast (`role=keys`). Blocking `QMessageBox` for confirms (`yukle.py:218`, `main_window.py:291`). | med | Small bottom-right toast (3 s, 5 s with Geri al button): "Belge 12 birleştirildi - Geri al". Keep status bar for persistent info. |
| Autosave indicator | "Kaydedildi" vs "Kaydediliyor..." (Word, Google) | Partial: header label "Kaydedildi HH:MM" appears after save (`main_window.py:78-82`). No "saving" or "failed" state, no dirty state. | med | Three states: "Kaydediliyor..." (spinner), "Kaydedildi 14:32", "Kaydedilemedi - Yeniden dene" in red with a click action. |
| Taskbar progress / busy cursor | Windows taskbar progress bar on the app button; wait cursor on long ops | Missing. Progress bars live inside tabs (`yukle.py:105`, `degerler.py:374`, `disa_aktar.py:353`); no `QApplication.setOverrideCursor`, no `QWinTaskbarButton` (removed in Qt6). | med | Use `QtWinExtras` replacement via `ITaskbarList3` (ctypes, Windows only) or fall back to `QWindow.requestUpdate` + window title suffix "(%42)". Wait cursor during job open. Flash taskbar (`QApplication.alert`) when a long task finishes while the window is inactive. |
| Sounds | Optional completion beep | Missing. | low | `QApplication.beep()` on error and on export completion, off by default, toggle in Ayarlar. |
| Errors and empty states | Plain-language message + next step + retry | Mixed. Kontrol with no job has a good empty state with "Yükle'ye git" (`main_window.py:162-185`). Others show blank lists. Errors go to status bar or `QMessageBox`. Değerler has an info row (`degerler.py:235-244`). | med | Empty states with an action for: no jobs (Yükle), no templates (Şablonlar: "İlk şablonu oluşturun"), no values (Değerler: "Okumayı başlat"), nothing exported. Every error: what happened, what to do, "Ayrıntılar" expander, "Kopyala". |
| Tooltips coverage | Every icon-only control and truncated text | Buttons yes (`widgets.py:53-55`). Strip, canvas, a few combos (`kontrol.py:46`, `:213`, `:219`; `sablon.py:83`, `:284`). Table cells explain state (`degerler.py:612-624`). Missing on status-bar items, header, tab bar (other than key), Yükle lists, Rehber. | low | Add; also elide long names with full-path tooltip. |
| Status bar content | Page x of y, selection count, zoom, mode, background task | Counts (`counts`), checks, message, key list (`main_window.py:146-156`). Selection text is inside Kontrol toolbar (`kontrol.py:208`). No current page or document, no zoom, no task. | med | Left to right: `Sayfa 134/612  Belge 17/58  3 seçili  |  mesaj  |  [zoom]  |  kısayol ipucu`. Make key list collapsible (it grows with each tab). |
| Accessibility: names, order | `setAccessibleName`, logical Tab order, no focus traps | Missing entirely (no `setAccessible*`, no `setTabOrder`). Custom-painted widgets (`WholeJobStrip` `kontrol.py:35-82`, `TimelineDelegate`, `PageCanvas`) expose nothing to screen readers. | med | Name every control; set `QAccessible` text on strip and delegate rows ("Sayfa 14, belge 3, kesim: QR"); verify Tab order per screen; Esc always returns focus to the main list. |
| Accessibility: focus | Visible focus on every control, 3:1 contrast | Buttons, inputs, list items have a 2 px focus border (`theme.py:180`, `:187`, `:195`, `:240`). Tab bar, table cells, canvas, strip, timeline thumbnails: not verified; the timeline delegate draws its own current-item mark. | med | Audit with Tab key through each screen; add visible focus to the tab bar and timeline current page. |
| High-contrast / dark mode | Follows Windows contrast themes and dark mode | Fixed light palette (`theme.py:42` tokens; `app.setStyle("Fusion")` `app.py:~46`). No `QStyleHints.colorScheme` handling, no contrast theme. | med | Read `app.styleHints().colorScheme()` and `highContrast`; provide a `dark` and `contrast` token set; Settings "Görünüm: Sistem / Açık / Koyu / Yüksek karşıtlık". |
| Fullscreen / window | F11, remember maximised, sane minimum size, multi-monitor, high DPI | No F11. Minimum 1100x640 (`main_window.py:98`) exceeds 1024x768 and 1366x768 minus taskbar heights on some laptops. No `AA_*` DPI policy set (Qt 6 default is per-monitor with rounding policy; pixel-based fonts `setPixelSize` ignore the Windows text scale, `theme.py:77`). | med | F11 "Tam ekran"; restore geometry across monitors; use point-based or scaled px for fonts; test at 125%/150%/175% display scale. |
| Help: in-app | F1 help, onboarding, tooltips tour | Rehber tab = scanning guide + separator sheets (`rehber.py`). No UI help (what N does, what colours mean), no first-run tour, no "Yardım" menu. | med | F1 opens "Yardım" dialog with three tabs: Başlarken, Kısayollar, Sorun giderme. First-run 4-step overlay (Yükle, Kontrol, Şablon, Dışa aktar) with "Bir daha gösterme". |
| About / version / updates | Help > About; update notice | Version only in window title (`main_window.py:95`, `:222`). No About dialog, no licence/credits, no check for updates (local-first app, so keep it opt-in). | low | "Yardım > Evrakçı hakkında": version, build date, licence, data folder path with "Klasörü aç", log file path. Optional "Güncelleme var" banner reading a static JSON only if the user enables it. |
| Printing / open externally / reveal | Ctrl+P; "Show in Explorer"; open with default viewer | Dışa Aktar has open-folder / open-index via `QDesktopServices` (`disa_aktar.py:735-738`). Rehber opens separator PDF (`rehber.py:85`). No print dialog, no "open source PDF", no reveal for job folder or batch file. | med | Right-click "Dosyayı göster" (Windows: `explorer /select,`), "Varsayılan uygulamada aç". Ctrl+P on Rehber prints separator sheet; on Dışa Aktar prints the index. |
| Settings dialog | Preferences (Ctrl+,) | No dialog. Retention is a combo on Dışa Aktar (`disa_aktar.py:269`, stored via `pipeline.settings`). | med | Ctrl+Virgül or "Düzen > Ayarlar": Görünüm (yazı boyutu, tema), Saklama süresi, Varsayılan klasörler, Sesler, Kısayolları sıfırla. |
| Close / quit | Ctrl+Q / Alt+F4; unsaved warning | Window close handled with busy-job guard (`main_window.py:288-305`). No Ctrl+Q. Cancel while closing shows only status text. | low | Ctrl+Q "Çık"; show a modal progress "Durduruluyor..." instead of a status message. |

## 2. Shortcut inventory (as implemented)

All `QShortcut`s use `WidgetWithChildrenShortcut` except the main-window ones, which use the default `WindowShortcut`. That means Ctrl+Z, N, K etc. work only when focus is inside the screen's widget tree; they stop working while a dialog or the status bar has focus, and they do nothing on other tabs.

| Key | Action | Scope | Source |
|---|---|---|---|
| Ctrl+1 ... Ctrl+5 | Switch to Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar | Window | `main_window.py:128-132` |
| F1 | Switch to Rehber tab (not help) | Window | `main_window.py:133` |
| Ctrl+N | Yeni iş | Yükle | `yukle.py:133` (hint `yukle.py:63`) |
| Ctrl+O | Dosya seç (add batch) | Yükle | `yukle.py:133` (hint `yukle.py:85`) |
| Esc | Cancel running task | Yükle | `yukle.py:134` |
| Alt+Up / Alt+Down | Move batch up / down | Yükle | `yukle.py:134-135` (hints `:93-94`) |
| Ctrl+Z | Geri al | Kontrol | `kontrol.py:240` (hint `:204`) |
| Ctrl+Y | Yinele | Kontrol | `kontrol.py:241` (hint `:205`) |
| F | Filtre uygula | Kontrol | `kontrol.py:242` |
| K | Kes / kesimi kaldır | Kontrol | `kontrol.py:243` |
| T | Şablon uygula | Kontrol | `kontrol.py:244` |
| R | Döndür | Kontrol | `kontrol.py:245` |
| Del | Sil / geri getir | Kontrol | `kontrol.py:246` |
| M | Önceki belgeyle birleştir | Kontrol | `kontrol.py:247` |
| N / Shift+N | Sonraki / önceki kontrol | Kontrol | `kontrol.py:248-249` (hints `:163-164`) |
| Ctrl+4 (hint only) | "Değerlerde aç" button label; the real shortcut is the global Ctrl+4 | Kontrol | `kontrol.py:104` |
| Left/Right, Shift+arrows, Ctrl+click, Home/End | Native `QListView` behaviour, not defined by the app | Kontrol | `timeline.py:306` |
| B | Kutu çiz modu | Şablonlar | `sablon.py:216` |
| G | Izgara aç/kapa | Şablonlar | `sablon.py:216` |
| Ctrl+S | Şablonu kaydet | Şablonlar | `sablon.py:216` (hint `:326`) |
| Ctrl+Z / Ctrl+Y | Geri al / yinele (template stack) | Şablonlar | `sablon.py:217` |
| Ctrl+T | Bütün örneklerde dene | Şablonlar | `sablon.py:218` (hint `:324`) |
| Alt+Up / Alt+Down (hint) | Move variable section | Şablonlar | `sablon.py:263-265` (no QShortcut found, buttons only) |
| Return | Öneriyi kabul et | Değerler | `degerler.py:~438` |
| F2 | Elle yaz | Değerler | `degerler.py:~438` |
| V | Çizerek yeni kutu (variant) | Değerler | `degerler.py:~438` |
| N | Sonraki kontrol | Değerler | `degerler.py:~438` |
| Esc | Cancel reading | Değerler | `degerler.py:~438` |
| Ctrl+E | Dışa aktar | Dışa Aktar | `disa_aktar.py:413` (hint `:319`) |
| Esc | İptal | Dışa Aktar | `disa_aktar.py:413` |

Conflicts and issues found:

1. **F1 hijacked.** Every Windows user expects F1 = Help; here it silently changes tab (`main_window.py:133`).
2. **Bare-letter shortcuts versus text entry.** K, T, R, M, N, F, B, G, V are plain letters. On Değerler the table is editable (`degerler.py:421-422`, `EditKeyPressed`), and the filter box and search box are on the same screen; the shortcut is only suppressed while an editor has focus because Qt gives the focused text widget the key first, but the Kontrol toolbar has a combo (`every_n`) and a template combo (`kontrol.py:213`, `:219`) that can swallow letters via type-ahead and fire commands from typed text. Needs a test.
3. **Same key, different meaning per tab.** N = sonraki kontrol in Kontrol and Değerler (consistent, fine); Esc = cancel in Yükle, Değerler, Dışa Aktar but closes nothing in Kontrol or Şablonlar; Ctrl+S exists only in Şablonlar.
4. **Ctrl+Z/Y duplicated** as two separate stacks; no Ctrl+Shift+Z.
5. **Hints disagree with reality.** The Yükle key list claims "Alt+↑ ↓ sırala" (`main_window.py:38`) which is valid, but Şablonlar "Yukarı/Aşağı" buttons advertise Alt+Up/Down with no shortcut registered (`sablon.py:263-265`).
6. **Ctrl+Z on Değerler and Dışa Aktar silently does nothing**, even though the user just edited a value.
7. **Not Turkish-keyboard-safe.** Current keys are fine (letters are ASCII), but `+`/`-` zoom needs care: on the Turkish Q keyboard `+` is Shift+4 and `=` sits on a different key. Use Ctrl+wheel and Ctrl+NumPad, plus `Ctrl+=` and `Ctrl+-`.

## 3. Proposed complete shortcut map

Rules: Windows-standard meanings win; ASCII letters only (no ç ş ğ ı ö ü, which sit on punctuation keys); no Ctrl+Alt combinations (AltGr on a Turkish keyboard is Ctrl+Alt, so these type characters such as @, {, [, \\); no bare single-letter shortcuts while a text field has focus; every key must be visible in a menu or tooltip. Application-wide shortcuts use `Qt.ApplicationShortcut`; per-tab ones keep `WidgetWithChildrenShortcut`.

| Group | Key | Turkish label | Where |
|---|---|---|---|
| Uygulama | Ctrl+1 ... Ctrl+6 | Sekme: Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | everywhere |
| Uygulama | Ctrl+Tab / Ctrl+Shift+Tab | Sonraki / önceki sekme | everywhere |
| Uygulama | F1 | Yardım | everywhere |
| Uygulama | Ctrl+/ , Shift+F1 | Klavye kısayolları | everywhere |
| Uygulama | Ctrl+K | Komut ara (palette) | everywhere |
| Uygulama | Ctrl+, | Ayarlar | everywhere |
| Uygulama | F11 | Tam ekran | everywhere |
| Uygulama | Ctrl+Q | Çık | everywhere |
| Uygulama | Ctrl+W | İşi kapat | everywhere |
| Uygulama | F5 | Yenile (iş listesi, küçük resimler) | everywhere |
| Uygulama | Ctrl+P | Yazdır (ayıraç sayfası / dizin) | Rehber, Dışa Aktar |
| Dosya | Ctrl+N | Yeni iş | everywhere |
| Dosya | Ctrl+O | Dosya ekle / iş aç | everywhere |
| Dosya | Ctrl+S | Kaydet (toast "Kaydedildi") | everywhere |
| Dosya | Ctrl+E | Dışa aktar | everywhere |
| Dosya | Ctrl+Shift+O | Dosyayı klasörde göster | Yükle, Dışa Aktar |
| Düzen | Ctrl+Z / Ctrl+Y / Ctrl+Shift+Z | Geri al / Yinele | everywhere (one routed stack per context) |
| Düzen | Ctrl+A / Ctrl+Shift+A / Ctrl+Shift+I | Hepsini seç / Seçimi kaldır / Seçimi ters çevir | Kontrol, Değerler, listeler |
| Düzen | Ctrl+F / F3 / Shift+F3 | Bul / sonraki / önceki | everywhere |
| Düzen | Ctrl+G | Sayfaya / belgeye git | Kontrol, Değerler |
| Düzen | Del | Sil (onaylı veya geri alınabilir) | Kontrol, Yükle, Şablonlar |
| Düzen | F2 | Yeniden adlandır / elle yaz | Yükle, Şablonlar, Değerler |
| Görünüm | Ctrl+wheel, Ctrl+`=`/NumPad`+`, Ctrl+`-`/NumPad`-` | Yakınlaştır / uzaklaştır | Kontrol, Şablonlar, Rehber |
| Görünüm | Ctrl+0 / Ctrl+1 / Ctrl+2 | Sığdır / %100 / Genişliğe sığdır | Kontrol, Şablonlar |
| Görünüm | Ctrl+Shift+`=` , Ctrl+Shift+`-` | Yazı boyutunu büyüt / küçült | everywhere |
| Görünüm | Space | Sayfa önizleme aç / kapat | Kontrol |
| Gezinme | Left/Right, Home/End, PgUp/PgDn | Sayfa, ilk/son, ekran | Kontrol |
| Gezinme | Ctrl+Left / Ctrl+Right | Önceki / sonraki belge | Kontrol |
| Gezinme | N / Shift+N | Sonraki / önceki kontrol | Kontrol, Değerler (only when no text field focused) |
| Kontrol | K | Burada kes / kesimi kaldır | Kontrol |
| Kontrol | Del | Sayfayı sil / geri getir | Kontrol |
| Kontrol | R / Shift+R | Sağa / sola döndür | Kontrol |
| Kontrol | M | Önceki belgeyle birleştir | Kontrol |
| Kontrol | T | Şablon uygula | Kontrol |
| Kontrol | F | Filtre uygula | Kontrol |
| Şablonlar | B | Kutu çiz | Şablonlar |
| Şablonlar | G | Izgara | Şablonlar |
| Şablonlar | Ctrl+T | Bütün örneklerde dene | Şablonlar |
| Şablonlar | Alt+Up / Alt+Down | Değişkeni yukarı / aşağı taşı | Şablonlar |
| Şablonlar | Space (held) | Kaydırma eli | Şablonlar |
| Şablonlar | Arrows / Shift+arrows | Seçili kutuyu 1 mm / 5 mm kaydır | Şablonlar |
| Değerler | Enter / F2 / V | Öneriyi kabul et / elle yaz / kutu çiz | Değerler |
| Değerler | Ctrl+Enter | Seçili önerileri kabul et | Değerler |
| Yükle | Alt+Up / Alt+Down | Partiyi taşı | Yükle |
| Genel | Esc | İptal / seçimi bırak / önizlemeyi kapat | everywhere |

Notes: Ctrl+0..2 are free because the tab keys are Ctrl+1..6, so zoom-to-100 must not use Ctrl+1. Decide one of two layouts: keep Ctrl+1..6 for tabs (current, recommended because staff already learned it, `main_window.py:128`) and use **Ctrl+0 fit, Ctrl+Shift+0 = 100%, Ctrl+Shift+2 = fit width** for zoom presets. The table above lists the Acrobat convention for reference; the rename to Ctrl+Shift+0/Ctrl+Shift+2 avoids the clash. Qt's `QKeySequence.ZoomIn` standard key already maps Ctrl++ and handles keyboard layouts; prefer standard keys (`QKeySequence.StandardKey.Undo`, `.Redo`, `.SelectAll`, `.Find`, `.HelpContents`, `.FullScreen`, `.Quit`, `.Preferences`) so the platform supplies correct variants.

## 4. Prioritised top 25

1. **Template canvas zoom and pan** (Ctrl+wheel, Ctrl+0, Space-drag, no re-fit after user zoom). `sablon.py:66`, `:90`, `:107`.
2. **Large page preview** (Space or double-click, arrows page through, Ctrl+wheel zoom). New dialog, hooks `kontrol.py:333`, `:422`.
3. **Thumbnail size control** (Ctrl+wheel and status-bar slider; re-render at new height). `timeline.py`, `main_window.py:~204`.
4. **Remember window state** (size, position, maximised, tab, splitters) via `QSettings`; lower minimum size to 1024x600. `main_window.py:97-98`.
5. **Whole-UI text size setting** (Küçük/Normal/Büyük/Çok büyük) and Ctrl+Shift+`=`/`-`. `theme.py:60`, `:72`, `:107`.
6. **Shortcut cheat sheet** (Ctrl+/ and Shift+F1) generated from the real actions; **move F1 to Yardım** and give Rehber Ctrl+6. `main_window.py:133`.
7. **Right-click context menus** on thumbnails, job rows, batch rows, table cells, template variables, each showing its shortcut.
8. **Ctrl+F find** on every tab and **Ctrl+G go to page/document**. `degerler.py:343`, `kontrol.py:333`.
9. **Undo everywhere**: route Ctrl+Z/Y/Shift+Z application-wide, undo Değerler edits, "Geri al: <ad>" labels, history list via `QUndoView`. `controller.py:62`, `sablon.py:203`.
10. **Persist the small things**: last directories for file dialogs (`yukle.py:168`, `:187`), export folder (`disa_aktar.py:230`), Değerler filter and column widths, zoom levels.
11. **Menu bar** (Dosya, Düzen, Görünüm, Yardım) with shortcuts shown; this also enables Alt mnemonics. Replace the plain `HeaderBar` menu widget (`main_window.py:99-100`).
12. **Select all, deselect, invert, rubber-band** on the timeline (Ctrl+A, Ctrl+Shift+A, Ctrl+Shift+I). `timeline.py:306`.
13. **Toasts with Undo** for destructive or surprising actions (merge, delete, rotate, rename), replacing silent status-bar text. `main_window.py:219`.
14. **Autosave state** with "Kaydediliyor / Kaydedildi / Kaydedilemedi" and Ctrl+S confirming it everywhere. `main_window.py:78-82`.
15. **Timeline keyboard navigation documented and extended**: Home/End/PgUp/PgDn, Ctrl+Left/Right per document; show in status key list. `main_window.py:39`.
16. **Status-bar upgrade**: current page / document, selection count, zoom slider with percent and "Sığdır". `main_window.py:146-156`.
17. **Whole-window file drop** with folder support and a drop overlay. `yukle.py:44`, `:246`.
18. **Reveal in Explorer / open in default app** for jobs, batches, source PDFs; **Ctrl+P** print for separators and index. `disa_aktar.py:735`, `rehber.py:85`.
19. **Windows taskbar progress, busy cursor and attention flash** for long tasks (open job, OCR, export). New; ctypes `ITaskbarList3`.
20. **Dark and high-contrast support** via `QStyleHints.colorScheme()`; token sets in `theme.py:42`.
21. **Accessibility pass**: `setAccessibleName`/Description on all controls and custom-painted widgets, Tab order, visible focus on tab bar and timeline. `kontrol.py:35`, `timeline.py`.
22. **Settings dialog (Ctrl+,)** collecting font size, theme, retention, folders, sounds, reset layout. Retention currently sits on Dışa Aktar (`disa_aktar.py:269`).
23. **Real empty states and error text** for every list and failure, with a next-step button. `main_window.py:162-185` is the model.
24. **Drag reorder** for batches and template variables, keeping Alt+Up/Down as the keyboard path. `yukle.py:90-94`, `sablon.py:255`.
25. **About dialog, first-run tour, F11 full screen, Ctrl+Q**, optional completion sound, recent jobs ordering. Low effort, completes the "solid app" feel.

## 5. Implementation notes (Qt/PySide6)

- One new `ui/actions.py` that defines every command once as a `QAction` (text, `QKeySequence`, context, tooltip), so menus, context menus, buttons, the status key list and the cheat sheet are generated from one table. This also removes the drift found in section 2 (hint vs. real binding).
- Zoom: subclass handling `wheelEvent` with `event.modifiers() & Qt.ControlModifier`; for `QGraphicsView` use `setTransformationAnchor(AnchorUnderMouse)` and `scale()`; keep a `user_zoomed` flag so `resizeEvent` stops calling `fitInView`. For `QListView` thumbnails change `ITEM_H` through a property and call `doItemsLayout()`.
- Settings: `QSettings` with an INI file next to the existing `pipeline.settings` data (the app is local-first and may run from a USB stick, so prefer `QSettings.IniFormat` in the data folder over the registry).
- Taskbar progress on Qt 6: `QWinTaskbarButton` was removed; use `ITaskbarList3` through `ctypes`/`comtypes`, guarded by `os.name == "nt"`.
- Font scaling: `theme.FONT_SIZE` is a module constant used to build stylesheet strings (`theme.py:60`, `:107`); turn it into a function parameter, regenerate with `app.setStyleSheet`, and replace per-widget literal `font-size` styles (`kontrol.py:95`, `rehber.py:32,45`, `sablon.py` titles) with `role` properties.
- Everything above is untested on screen at 125-175% Windows scaling; verify before adopting fixed pixel sizes.

## Sources

Code only; see file:line citations above. Pattern references: `docs/research/05-sector-examples.md`, `docs/research/03-fluent-and-enterprise-systems.md` (not opened for this audit; the Office/Acrobat/Lightroom expectations in the tables come from general knowledge of those products, so treat them as unverified against those files). Items marked "not verified" or "needs a test" were not exercised at runtime. Line numbers with a `~` are approximate (grep-located, not individually re-checked).
