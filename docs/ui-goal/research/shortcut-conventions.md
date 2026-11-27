# Shortcut conventions: index and match (2026-11-20)

Purpose: so that someone who knows Windows, Office, a PDF reader or a GNOME/KDE app finds the same key doing the same thing in Evrakçı. Method: every page below was opened on 2026-11-20 and the key quoted is the key the page shows. Pages that could not be opened are listed at the end and are not used as evidence. Nothing in `shortcut-contract.tsv`, `src/` or `tests/` was changed; section 4 only proposes.

## 1. Sources opened

| Id | Page | What it is |
|---|---|---|
| MS-KA | https://learn.microsoft.com/en-us/windows/apps/design/input/keyboard-accelerators | Windows app guidance, "Common Keyboard Accelerators" table (Fluent / WinUI) |
| MS-W32 | https://learn.microsoft.com/en-us/windows/win32/uxguide/inter-keyboard | Win32 UX guide "Keyboard" (marked as written for Windows 7, "much of the guidance still applies") |
| MS-WIN | https://support.microsoft.com/en-us/windows/keyboard-shortcuts-in-windows-dcc61a57-8ff0-cffe-9796-cb9706c75eec | Windows and File Explorer shortcuts |
| MS-WORD | https://support.microsoft.com/en-us/office/keyboard-shortcuts-in-word-95ef89dd-7142-4b50-afb2-f762f663ceb2 | Word for Windows |
| MS-XL | https://support.microsoft.com/en-us/office/keyboard-shortcuts-in-excel-1798d9d5-842a-42b8-9c99-9b7213f0040f | Excel (Windows column) |
| QT | https://doc.qt.io/qt-6/qkeysequence.html | `QKeySequence::StandardKey` table (Windows, GNOME, KDE Plasma, Apple) |
| GNOME | https://developer.gnome.org/hig/reference/keyboard.html | GNOME HIG, Keyboard reference |
| SUM | https://www.sumatrapdfreader.org/docs/Keyboard-shortcuts | SumatraPDF |
| FOXIT | https://resource-cms.foxit.com/foxit-pdf-editor-for-windows/keyboard-shortcuts | Foxit PDF Editor for Windows (the Reader's own page was not found; the Editor shares the viewer keys) |
| MTE-ACR | https://maketecheasier.com/cheatsheet/adobe-acrobat-keyboard-shortcuts/ | Third-party Acrobat cheat sheet (Adobe's own page returned 403), weak evidence |
| MTE-EV | https://maketecheasier.com/cheatsheet/evince-pdf-reader-keyboard-shortcuts/ | Third-party Evince cheat sheet (GNOME's own page returned 404), weak evidence |
| CHEN | https://devblogs.microsoft.com/oldnewthing/?p=7803 | Raymond Chen (Microsoft) on Ctrl+Alt and AltGr |
| ANKI | https://forums.ankiweb.net/t/inconsistent-keyboard-shortcuts-on-turkish-q-layout/38850 | Qt app (Anki) with Turkish-Q shortcut bugs |

Apple HIG: not used (background only, as the task says). Qt's table shows the Apple column anyway.

## 2. Index of conventions

"Win" = Windows/Office standard (MS-KA, MS-WIN, MS-WORD, MS-XL). "Qt" = StandardKey, Windows / GNOME / KDE columns. "PDF" = Sumatra, Foxit, Acrobat (weak), Evince (weak). Blank = the source shows nothing.

| Action | Win | Qt (Win / GNOME / KDE) | GNOME HIG | PDF tools |
|---|---|---|---|---|
| New | Ctrl+N (MS-KA, MS-WORD) | Ctrl+N all | Ctrl+N | Sumatra Ctrl+N = new window; Foxit: none (Ctrl+N is "Create PDF") |
| New secondary item | Ctrl+Shift+N (MS-KA); Explorer: new folder (MS-WIN) | | | Sumatra Ctrl+Shift+N = open in new window |
| Open | Ctrl+O | Ctrl+O all | Ctrl+O | Sumatra, Foxit, Evince Ctrl+O |
| Save | Ctrl+S | Ctrl+S all | Ctrl+S | Foxit Ctrl+S; Sumatra Ctrl+S = save as |
| Save as | F12 (MS-WORD) | Ctrl+Shift+S all | Shift+Ctrl+S | Foxit Ctrl+Shift+S; Sumatra Ctrl+Shift+S = save annotations |
| Close tab / document | Ctrl+W (MS-KA, MS-WIN, MS-WORD, MS-XL), Ctrl+F4 (MS-WIN) | Ctrl+F4, Ctrl+W / Ctrl+W / Ctrl+W | Ctrl+W | Sumatra Ctrl+W, Ctrl+F4; Foxit Ctrl+W, Ctrl+F4; Evince Ctrl+W |
| Close window / quit | Alt+F4 (MS-WIN); Qt Windows: no Quit key | none / Ctrl+Q / Ctrl+Q | Ctrl+Q | Sumatra Ctrl+Q, Alt+F4 |
| Undo | Ctrl+Z (also Alt+Backspace in Qt) | Ctrl+Z all | Ctrl+Z | Sumatra Ctrl+Z (PDF edits); Foxit Ctrl+Z |
| Redo | Ctrl+Y (MS-KA, MS-WORD) | Ctrl+Y, Ctrl+Shift+Z / Ctrl+Shift+Z / Ctrl+Shift+Z | Shift+Ctrl+Z | Foxit Ctrl+Shift+Z; Sumatra Ctrl+Shift+Z |
| Cut / Copy / Paste | Ctrl+X / Ctrl+C / Ctrl+V; Shift+Del / Ctrl+Ins / Shift+Ins (MS-WIN, MS-KA) | same, plus F20/F16/F18 on Linux | same | |
| Delete | Del; Ctrl+D "with undo"; Shift+Del "without undo" (MS-KA) | Del / Del, Ctrl+D / Del, Ctrl+D | | Sumatra Delete = delete annotation |
| Select all | Ctrl+A (MS-KA, MS-XL) | Ctrl+A all | Ctrl+A | Sumatra, Foxit Ctrl+A |
| Deselect all | | | Shift+Ctrl+A | |
| Find | Ctrl+F (MS-KA, MS-WORD) | Ctrl+F all | Ctrl+F | Sumatra Ctrl+F or `/`; Foxit Ctrl+F; Evince Ctrl+F |
| Find next / previous | F3 / (MS-KA: "Go to the next search result" F3) | F3, Ctrl+G / Ctrl+G, F3 / F3; previous Shift+F3, Ctrl+Shift+G | Ctrl+G / Shift+Ctrl+G | Sumatra F3 / Shift+F3; Foxit F3; Evince (weak) Ctrl+G |
| Replace | Ctrl+H (MS-KA, MS-WORD) | Ctrl+H / Ctrl+H / Ctrl+R | Ctrl+H | |
| Go to (page, cell) | Ctrl+G (MS-WORD); Excel F5 (MS-XL, Ctrl+G not in the Windows table) | | | Sumatra Ctrl+G or `g`; Foxit Ctrl+G |
| Print | Ctrl+P | Ctrl+P all | Ctrl+P | Sumatra, Foxit, Evince Ctrl+P |
| Print preview | Ctrl+Alt+I (MS-WORD) | | Shift+Ctrl+P | |
| Zoom in / out | Ctrl++ / Ctrl+- (MS-KA, MS-WORD) | Ctrl+Plus / Ctrl+Minus all | Ctrl++ / Ctrl+- | Sumatra `+`/`-`; Foxit Ctrl++/Ctrl+-; Evince Ctrl++/Ctrl+- (weak) |
| Zoom reset | Ctrl+0 (MS-KA "default view", MS-WORD "100%") | | Ctrl+0 "Normal Size" | Sumatra Ctrl+0 = fit page, Ctrl+1 = actual size, Ctrl+2 fit width; Foxit Ctrl+0 fit page, Ctrl+1 actual size |
| Full screen | F11 (MS-WIN, File Explorer) | F11, Alt+Enter / Ctrl+F11 / F11, Ctrl+Shift+F | | Sumatra F11, `f`; Foxit F11; Evince F11 (weak) |
| Refresh / reload | F5 or Ctrl+R (MS-KA) | F5 / Ctrl+R, F5 / F5 | Ctrl+R "Reload" | Sumatra `r` |
| Rename | F2 (MS-KA, MS-WIN) | | | Sumatra F2 = rename file |
| Properties | Alt+Enter (MS-WIN) | | Alt+Return | Sumatra Ctrl+D |
| Help | F1 (MS-WORD) | F1 all (Apple Ctrl+?) | F1 | Sumatra F1 |
| Shortcut sheet | Shift+F1 = context help (MS-W32) | | Ctrl+? | |
| Preferences / settings | none (Qt Windows, MS-KA) | none / none / Ctrl+Shift+, | Ctrl+, | |
| Menu | | | F10 | Sumatra F9 = show/hide menu |
| Side pane | | | F9 | Sumatra F12 = bookmarks; Evince F9 (weak) |
| Next UI pane / previous | F6 / Shift+F6 (MS-KA) | NextChild Ctrl+Tab, Ctrl+F6 | | Sumatra F6 = focus bookmarks/main window |
| Next / previous tab | Ctrl+Tab / Ctrl+Shift+Tab (MS-WIN) | NextChild: Ctrl+Tab | | Sumatra Ctrl+Tab, Ctrl+PgDn/PgUp; Foxit Ctrl+Tab, Ctrl+Shift+PgDn |
| Tab 1..9 | Ctrl+1..9 in File Explorer (MS-WIN); Ctrl+1, Ctrl+2 app-wide in Outlook (MS-KA) | | | Sumatra Alt+1..8, Alt+9 = last; Ctrl+1/2/3 there are zoom |
| New tab | Ctrl+T (MS-WIN, File Explorer) | AddTab Ctrl+T | Ctrl+T | |
| Context menu | Shift+F10 (MS-WIN, MS-WORD) | | | |
| Next / previous item | Arrow keys; Tab / Shift+Tab (MS-W32) | | | |
| First / last item | Home / End (MS-W32, in a group) | | | |
| First / last page | Ctrl+Home / Ctrl+End (MS-XL start/end of sheet) | MoveToStartOfDocument Ctrl+Home | Ctrl+Home / Ctrl+End | Sumatra Home / End; Foxit Ctrl+Home / End; Evince Ctrl+Home/End (weak) |
| Next / previous page | PgDn / PgUp | | PageDown / PageUp | Sumatra Right/Left, PgDn/PgUp, `n`/`p`, Ctrl+Down/Up; Foxit Ctrl+PgDn/PgUp; Acrobat Right/Left (weak); Evince `N`/`P` (weak) |
| Page up / down (a screen) | PgUp / PgDn | | | Sumatra Space / Shift+Space |
| Back / forward (history) | Alt+Left / Alt+Right (MS-WIN) | Back: Alt+Left | Alt+Left / Alt+Right | Sumatra Alt+Left / Alt+Right |
| Up one level | Alt+Up (MS-WIN, Explorer) | | Alt+Up | |
| Toggle selection | Ctrl+Arrow then Space "Select multiple individual items" (MS-WIN) | | | |
| Extend selection | Shift+Arrow (MS-W32 navigation; Excel Ctrl+Shift+Arrow to the last nonblank cell, MS-XL) | | | |
| Edit cell / value | F2 (MS-XL "Edit active cell"); Ctrl+E "Begin editing mode" (MS-KA) | | | |
| Cancel / dismiss | Esc "cancels or closes the window" (MS-W32); Enter = default button (MS-W32) | | | Sumatra Esc = leave full screen |
| Rotate view / page | | | | Sumatra Ctrl+Shift+- / Ctrl+Shift++ (also `[` `]`); Foxit Ctrl+Shift+Minus / Plus; Evince Ctrl+Left / Right (weak) |
| Add bookmark / favorite | Ctrl+D "Add favorites" (MS-KA) | | Ctrl+D | Sumatra Ctrl+B |
| Command palette | | | | Sumatra Ctrl+K |
| Press-and-hold pan (hand tool) | | | | not shown on any page opened (Acrobat's hand tool: not verified, Adobe page not reachable) |

Rules the Windows pages state that matter here (quoted from MS-W32):
- "Don't assign different meanings to well-known shortcut keys." "Don't make a shortcut key the only way to perform a task."
- "Don't use Ctrl+Alt combinations, because Windows interprets this combination in some language versions as an AltGR key."
- "Don't use the following characters for shortcut keys: @ $ {} [] \ ~ | ^ ' < >" (they need different key combinations across languages).
- "Don't use Alt+alphanumeric key combinations for shortcut keys" (clash with access keys). "Avoid ... three or more keys together."
- Free keys the guide recommends for app-specific frequent commands: "Ctrl+G, J, K, L M, Q, R, or T", "Ctrl+any number", "F7, F8, F9, or F12"; for less frequent: "Ctrl+Shift+any letter or number".
- "Use function keys for commands that have a small-scale effect ... Use Ctrl key combinations for commands that apply to an entire document." "F1 displays Help, whereas Shift+F1 displays context-sensitive Help."
- MS-KA: "Notice that some of the combinations are not valid for localized versions of Windows" (Spanish Ctrl+N = bold). Shortcut keys in MS-W32 "aren't localized"; MS-KA recommends localizing.
- MS-KA: scoped accelerators are normal (Outlook: Ctrl+B, Ctrl+I, Esc only inside the send form; Ctrl+1, Ctrl+2 app-wide). So page-specific keys are fine if their meaning is the convention's meaning.

## 3. Turkish keyboard notes

- AltGr = Ctrl+Alt on Windows. MS-W32 and CHEN both say not to use Ctrl+Alt as a shortcut modifier because AltGr "produces characters on many non-English layouts" (CHEN: using it "prevents people from typing perfectly legitimate letters"). The repo rule "no Ctrl+Alt" is the same rule. The Turkish-Q AltGr characters (`{ } [ ] \ | @ € ₺ ~`) are exactly the kind of characters MS-W32's character list excludes. The sources do not name which Turkish key holds which character; that is from the Turkish layout, not from these pages.
- Punctuation shortcuts depend on the layout. ANKI (a Qt app) reports that on Turkish-Q `Ctrl+,`, `Ctrl+Shift+,` and `Ctrl+Shift+.` fired from the key where the comma and period sit on the English layout, which on Turkish-Q is the Ö and Ç keys; the character-based reading did not work, and `Ctrl+=` did not work at all. The Anki developers named no agreed fix ("translatable shortcuts had caused bugs"). For Evrakçı this says: Ctrl+, (Ayarlar), Ctrl+. (stop), Ctrl+/ (shortcut sheet), Ctrl+= and Ctrl++ (zoom) may fire from a different physical key than the one the user sees printed. Not verified in Evrakçı. Test it once on a Turkish-Q layout (offscreen tests cannot show it), and keep the second key for each (Shift+F1, Ctrl+Num+, Ctrl+Num+-, F-keys).
- Q versus F layout: no page opened says anything about the Turkish-F layout. Keys bound by physical position (Qt, as ANKI describes) stay in the Q positions on F keyboards; letter shortcuts (Ctrl+S, Ctrl+P, ...) are bound by character and follow the layout. Not verified further; a letter key printed differently on F keyboards is a risk for the single-letter keys (K, M, R, N, U, S, B, D, Q, F, T) that the README lists.
- Dotted and dotless I (I / ı / İ / i): no source opened gives a rule for shortcuts (the Qt bug reports found by search, QTBUG-108665 and QTBUG-109520, could not be opened: `bugreports-test.qt.io` is outside this session's allowed hosts, so they are not cited). The existing repo rule "no I" in a shortcut stands and costs nothing: the key labelled I on a Turkish keyboard is the dotless ı, and Ctrl+I is "Italic" in MS-KA and GNOME anyway.

## 4. Match against Evrakçı

Status words: **matches** = same action on the convention; **differs** = the convention says something else for that action (what); **no convention** = none of the sources has the action; **conflicts** = our key means something else somewhere in the sources. Rows of the contract are grouped by key (87 distinct keys in the 319 rows, listed in groups here; the tabs in brackets where a key is local).

### 4.1 Contract keys

| Key (contract rows) | Our action | Status | Convention says |
|---|---|---|---|
| Ctrl+N (6) | Yeni iş oluştur | matches | New: MS-KA, QT, GNOME |
| Ctrl+O (6) | Dosya ekle | matches | Open: all |
| Ctrl+S (6) | Kaydet | matches | Save (our job also saves as you work) |
| Ctrl+W (6) | İşi kapat | matches | Close document: MS-WIN, QT, GNOME |
| Ctrl+Q (6) | Çıkış | matches | Quit: QT GNOME/KDE, GNOME, SUM; Windows has none, Alt+F4 works natively |
| Ctrl+Z (6) | Geri al | matches | all |
| Ctrl+Y, Ctrl+Shift+Z (6 each) | Yinele | matches | Ctrl+Y MS, QT Windows; Ctrl+Shift+Z QT, GNOME, FOXIT |
| Ctrl+A (Kontrol, Değerler) | Tümünü seç | matches | all |
| Ctrl+F (6) | Bul | matches | all |
| F3, Shift+F3 (6) | Sonraki / önceki sonuç | matches | MS-KA, QT, SUM |
| Ctrl+G (6) | Belgeye veya sayfaya git | differs (partly) | Go to: MS-WORD, SUM, FOXIT agree. QT and GNOME assign Ctrl+G to Find next, but our F3 is Find next. Keep |
| Ctrl+P (Dışa Aktar, Rehber) | yazdır | matches | Print: all |
| Ctrl+Num++, Ctrl++, Ctrl+=, Ctrl+-, Ctrl+Num+- (6) | yakınlaştır / uzaklaştır | matches | Ctrl+Plus / Ctrl+Minus: QT, MS-WORD, GNOME |
| Ctrl+0 (6) | Sığdır / sıfırla | matches (label differs) | MS-KA and GNOME: reset to default (100 %). SUM and FOXIT: fit page. Our Kontrol/Rehber action resets to 100 %, so only the label "Sığdır" is off (M-20) |
| Ctrl+Tab, Ctrl+Shift+Tab (6) | sonraki / önceki sekme | matches | MS-WIN, QT NextChild |
| Ctrl+1 .. Ctrl+6 (6 each) | sekmeye git | matches (browser, Explorer, Outlook); differs from PDF tools | MS-WIN Ctrl+1..9, MS-KA Outlook Ctrl+1/2. FOXIT Ctrl+1 = actual size and SUM Ctrl+1 = actual size / Ctrl+0..3 zoom |
| F1 (6) | Yardım | matches | all |
| Shift+F1, Ctrl+/, ? (6 each) | Klavye kısayolları | differs | MS-W32: Shift+F1 = context-sensitive help. GNOME: Ctrl+? = keyboard shortcuts (our Ctrl+/ is the unshifted form of it). Keep both |
| F2 (Yükle, Değerler) | işi yeniden adlandır / değeri yaz | matches | Rename F2 (MS-KA, MS-WIN), edit cell F2 (MS-XL) |
| F5 (6) | Yenile | matches | MS-KA, QT |
| F6, Shift+F6 (6) | sonraki / önceki bölge | matches | MS-KA |
| F9 (6) | Yan paneli gizle / göster | matches | GNOME Side Pane F9 |
| F11 (6) | Tam ekran | matches | MS-WIN, QT |
| Ctrl+, (6) | Ayarlar | matches (GNOME only) | GNOME Ctrl+,; QT Windows none; KDE Ctrl+Shift+, |
| Ctrl+K, Ctrl+Shift+P (6) | Komut ara | Ctrl+K: no convention (SUM Ctrl+K palette; MS-W32 lists Ctrl+K as a free key). Ctrl+Shift+P: conflicts | GNOME: Print Preview = Shift+Ctrl+P |
| Ctrl+E (6) | Dışa aktar | conflicts | MS-KA: Ctrl+E = "Begin editing mode"; MS-WIN Explorer: Ctrl+E = search box |
| Ctrl+Shift+O (Yükle, Dışa Aktar) | Dosya Gezgini'nde göster | no convention | |
| Ctrl+Shift+Num++, Ctrl+Shift+Num+- (6) | yazı boyutu | Ctrl+Shift+Num++/-- conflicts | FOXIT and SUM: Ctrl+Shift+Plus / Minus = rotate view |
| Ctrl+. (Yükle, Değerler, Dışa Aktar) | iptal et / durdur | no convention | MS-W32: Esc cancels. No source has Ctrl+. |
| Alt+Up, Alt+Down (Yükle, Şablonlar) | taşı | differs | MS-WIN, GNOME: Alt+Up = up one level (Explorer). No source uses it for reordering |
| Del (Kontrol, Şablonlar, Yükle) | sil / çıkar | matches | Delete: MS-KA, QT |
| Home, End (Kontrol) | ilk / son sayfa | matches (SUM) | SUM Home / End; QT, GNOME, FOXIT use Ctrl+Home / Ctrl+End. Ctrl+Home/End is not bound |
| PgUp, PgDn (Kontrol) | bir ekran | matches | |
| Left, Right (Kontrol) | önceki / sonraki sayfa | matches | SUM Right / Left = next / previous page |
| Ctrl+Left, Ctrl+Right (Kontrol) | önceki / sonraki belge | differs | SUM: Ctrl+Shift+Left/Right = previous/next document in folder; MS-WIN: Ctrl+Arrow moves focus without selecting |
| Enter, Return (Kontrol, Değerler) | onayla | matches | MS-W32: Enter = default action |
| Ctrl+Enter, Ctrl+Return (Değerler) | seçilenleri onayla | no convention | MS-WORD Ctrl+Enter = page break (different app domain) |
| Esc (Kontrol, Değerler, Rehber) | seçimi kaldır / vazgeç | matches | MS-W32: Esc cancels / closes |
| Tab, Shift+Tab (Değerler) | sonraki / önceki değer | matches | MS-W32 |
| Space (Kontrol, Değerler) | Tüm sayfayı göster | differs / no convention | SUM Space = scroll one screen; MS-WIN: Space with Ctrl+Arrow selects items. No source has "preview on Space" |
| Space hold (Şablonlar) | sayfayı sürükle (el) | no convention in opened sources | hand tool: could not verify (Adobe unreachable) |
| Ctrl+D (Şablonlar) | kutuyu çoğalt | conflicts | MS-KA, QT KDE/GNOME: Ctrl+D = Delete; MS-KA, GNOME: Add favorite / bookmark. GNOME: Duplicate = Ctrl+U |
| Ctrl+Shift+N (Şablonlar) | değişken ekle | matches | MS-KA "Add a new secondary item" |
| Ctrl+T (Şablonlar) | örnekleri dene | conflicts (mild) | Ctrl+T = New tab: MS-WIN, QT AddTab, GNOME |
| B, G (Şablonlar) | kutu çiz, ızgara | no convention | |
| K, M, R, Shift+R, F, T, U (Kontrol, single letters) | kes, birleştir, döndür ... | no convention; R/Shift+R: differs | rotate in PDF tools is Ctrl+Shift+Minus / Ctrl+Shift+Plus (FOXIT, SUM); our R is the page-edit rotate |
| N, Shift+N (Kontrol, Değerler) | sonraki / önceki kontrol | no convention | SUM `n` / `p` = next / previous page; MTE-EV the same |
| V (Değerler) | varyant | no convention | |
| Arrow keys, Shift+arrows (Şablonlar) | kutuyu kaydır | matches | MS-W32: arrows move, Ctrl+arrow for finer; ours is Shift = 1 mm (differs in modifier) |

Summary (counted by hand from the table rows): 5 keys conflict (Ctrl+E, Ctrl+D, Ctrl+T, Ctrl+Shift+P, Ctrl+Shift+Num++/Num+-); the differs rows are Ctrl+G (partly), Ctrl+1..6 against PDF tools, Shift+F1 / Ctrl+/, Alt+Up/Down, Ctrl+Left/Right, Space, R/Shift+R; single letters and app-specific keys have no convention; everything else matches.

### 4.2 Keys in the new specs (README §3)

| Key | Spec | Status | Convention says |
|---|---|---|---|
| Ctrl+Space | A | matches | MS-WIN: Ctrl+Arrow then Space selects multiple individual items. (MS-XL has Ctrl+Space = select column; unrelated domain) |
| Alt+Left / Alt+Right "Seçimi bozmadan git" | A | differs | Alt+Left / Alt+Right = Back / Forward in MS-WIN, QT, GNOME, SUM. The sources' way to "move focus without changing the selection" is Ctrl+Arrow, which in Kontrol already means previous/next document |
| S, B, Shift+F, Shift+T, D, Q, Shift+K | A-C | no convention (single letters) | SUM and Acrobat (weak) use single letters for their own tools; none of these are in the sources |
| Ctrl+Shift+F | C saved filters | conflicts (KDE) | QT KDE FullScreen = F11, Ctrl+Shift+F. On Windows nothing |
| Ctrl+Shift+A | D compare names | conflicts | GNOME: Deselect All = Shift+Ctrl+A |
| Ctrl+Shift+C | D copy name list | no convention | |
| Ctrl+Shift+R | D save check list (only if O-19 yes) | no convention | GNOME: Reload = Ctrl+R |
| Ctrl+P "open print preview" | D I-38, O-16 | matches | Print = Ctrl+P everywhere; the preview key is not Ctrl+P in any source (Word: Ctrl+Alt+I, GNOME: Shift+Ctrl+P) |
| K / R on Değerler, N / Shift+N / Ctrl+L on Şablonlar | B | Ctrl+L: conflicts (mild) | GNOME: Enter Location = Ctrl+L; MS-WIN: focus the address bar. N pair: see above |
| Alt+1 .. Alt+4 (editor) | B I-19 | differs (Alt+digit) | MS-W32 says not to use Alt+alphanumeric for shortcuts (access keys); SUM uses Alt+1..8 for tabs. Local to the editor, so low risk |

### 4.3 Universal shortcuts the app lacks

Checked against the 87 keys. Not in the contract:
- Ctrl+Home / Ctrl+End (first / last page; QT, GNOME, FOXIT). Home / End exist.
- Ctrl+PgDn / Ctrl+PgUp (next / previous tab; SUM, FOXIT, MS-XL sheets). Ctrl+Tab exists.
- Shift+F10 and the Menu key (context menu; MS-WIN, MS-WORD). Whether Qt already provides it on our widgets was not tested here; the contract has no row.
- Ctrl+C / Ctrl+X / Ctrl+V / Ctrl+Insert / Shift+Insert (MS-WIN). Text fields have them from Qt; no page or box copy row exists.
- Alt+Left / Alt+Right as Back / Forward and Alt+Enter as Properties (no history or properties exist; not needed).
- Ctrl+Shift+S save as, Ctrl+H replace, Ctrl+R reload, Ctrl+T new tab: no matching feature, not needed.
- F10 (menu; GNOME), Ctrl+F4 (close; QT, MS-WIN): optional.
- Esc to cancel a running read or export (MS-W32: Esc cancels). We have Ctrl+. only.
- A page-rotate key in the PDF form: Ctrl+Shift+Plus / Ctrl+Shift+Minus (FOXIT, SUM); we have R / Shift+R.
- Select none: GNOME Shift+Ctrl+A; ours is Esc (matches MS-W32 on Esc).

## 5. Proposals, ranked by familiarity gained against what breaks

Nothing here is applied. Test pins: see `shortcut-mismatches.md` (Q-09 lists the five keys older tests pin as "disabled": F3 on Rehber with no hits, Ctrl+E while export is blocked, Ctrl+W after closing, Kontrol keys with no job, N with no kontrol). None of the proposals touches those.

| Rank | Proposal | Familiarity bought | Breaks / cost |
|---|---|---|---|
| 1 | Spec D: do not give "Adları karşılaştır" Ctrl+Shift+A; leave it menu and palette only, or pick another key | avoids GNOME's Deselect All = Shift+Ctrl+A | nothing built yet; zero cost |
| 2 | Spec D O-16: keep Ctrl+P and open the preview first (recommended in the spec); do not put the preview on Ctrl+Shift+P | Ctrl+P stays Print everywhere; avoids GNOME Print Preview clash | none |
| 3 | Add Ctrl+Home / Ctrl+End as aliases of Home / End in Kontrol (first / last page) | QT, GNOME, FOXIT all use Ctrl+Home / Ctrl+End | new rows, no existing key changes; Home / End stay |
| 4 | Add Esc as a second key for "stop the running read / export" while one runs; keep Ctrl+. | MS-W32: Esc cancels | Esc already means "clear selection" on Kontrol/Değerler, so only on Yükle and Dışa Aktar while a job runs; needs a test that Esc with nothing running stays quiet (M-45) |
| 5 | Drop Ctrl+Shift+P as the second palette key, keep Ctrl+K | removes the only palette key that collides with a convention (GNOME print preview) | 6 contract rows and their tests (test pins); low value if nobody uses it, so decide with Q-08 |
| 6 | Add Ctrl+PgDn / Ctrl+PgUp as aliases of Ctrl+Tab / Ctrl+Shift+Tab | SUM, FOXIT, Excel (sheets) | new rows; check Kontrol PgUp/PgDn is plain only |
| 7 | Spec A Alt+Left / Alt+Right: either keep (label it "Seçimi bozmadan git" and note Back/Forward is not used by Evrakçı), or use Ctrl+Left / Ctrl+Right for "move focus, keep selection" (the Explorer way) and move the document jump elsewhere | the sources use Alt+arrows for history and Ctrl+arrow for "move without selecting" | second option changes today's Ctrl+Left / Ctrl+Right (contract rows, tests); first option costs nothing. Recommend keep for now: Evrakçı has no history, so nobody expects Back |
| 8 | Ctrl+E: keep; document as "Dışa aktar" (MS-KA Ctrl+E editing mode and Explorer search are not features of this app; Ctrl+F is our search) | conflict is theoretical | none; no change |
| 9 | Ctrl+D "Kutuyu çoğalt": keep or move to a free key; convention says Delete / bookmark | avoids "I pressed Ctrl+D to delete" | undoable, local to Şablonlar; a change touches 1 row |
| 10 | Ctrl+Shift+Num++ / Num+- (text size): keep, but note PDF tools use the same keys to rotate | low (Evrakçı's page rotate is R) | none |
| 11 | Test Ctrl+, Ctrl+. Ctrl+/ Ctrl+= on a Turkish-Q layout (section 3, ANKI) | possible silent failure | a manual check or a test with the Turkish layout; add it to `shortcut-checklist.md` |
| 12 | Keep as page-specific, no change: Space on Kontrol / Değerler (preview) and Space hold on Şablonlar (pan), F9, single letters | no source has these | covered by Q-08 (14 page-specific keys) |

## 6. Not opened (not used as evidence)

- Adobe Acrobat shortcuts (https://helpx.adobe.com/acrobat/using/keyboard-shortcuts.html and two localized copies): HTTP 403. The Acrobat column comes from the third-party MTE-ACR and is weak.
- GNOME Evince (https://help.gnome.org/users/evince/stable/shortcuts.html.en and `keyboard-shortcuts.html`): HTTP 404. Evince column from MTE-EV, weak.
- KDE Okular handbook (docs.kde.org, two paths): HTTP 404. KDE HIG (https://develop.kde.org/hig/) opened but has no shortcut table; KDE keys come from the Qt table only.
- Foxit PDF Reader's own page: not found; the Foxit Editor for Windows page is used.
- PDF-XChange: not searched.
- Qt bug reports QTBUG-108665 / QTBUG-109520 (Turkish İ): host `bugreports-test.qt.io` is not in the allowed network domains; to read them it has to be allowed.
