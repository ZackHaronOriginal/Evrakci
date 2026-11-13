# Proposals for the owner (not applied)

Direction A is the visual source of truth (decisions.md, "Owner correction after round 3").
Nothing below has been applied to the mockups, except item 3, whose option a is what the
provisional 150 % renders show today (it was there before this list and needs the owner's choice).
Each item changes or extends how A behaves and waits for the owner's yes or no. Items 1 and 5
were approved on 2026-11-13 and are built in the app (not redrawn in the mockups).

1. **Approved and built (owner, 2026-11-13).** **Edge above the pinned inspector action at 150 %
   text.** At 150 % the inspector content
   scrolls (as a QScrollArea) and used to run straight under the pinned primary ("Belgeyi onayla",
   "Onayla ve sonrakine geç"), so a half-visible line sat directly on the button
   (`png/kontrol-150-light.png`, `png/degerler-150-light.png`). The buttons now sit below the
   scroll area instead of over it (see REVIEW.md), but a cut line can still end right above them.
   Proposal: when the pane is scrolled, show A's 1 px `--stroke` hairline above the pinned
   button group. At 100 % nothing would change, since nothing scrolls there.
2. **Değerler table at 150 % text.** At 150 % the table scrolls sideways and the Güven column
   goes out of view first. Proposal: pin the Güven column at the right edge, or move it next to
   the edited value, so the Kontrol word stays visible. A's 100 % layout would stay as it is.
3. **Title-band tabs at 150 % text (decision needed; the 150 % renders are provisional until then).**
   At 150 % on a 1366 px window, A's six labelled tabs, the job name with "Kaydedildi", the search,
   ≡ and the caption buttons no longer fit in one 44 px band. The 150 % renders currently show
   every unselected tab as its icon only (name in the tooltip), the selected tab keeps its icon and
   label (`additions.css`, "150 % text" block; `png/*-150-light.png`). That changes how A's
   approved tabs look at that size, so it needs the owner's choice:
   - **a. Icon-only unselected tabs** (as rendered now). Everything stays in the band; the tab
     names are only in tooltips, so a new user has to hover to learn them.
   - **b. Keep the labels, overflow behind a chevron.** Tabs keep A's icon + label; the tabs that
     do not fit go into a "»" menu at the end of the strip (Fluent TabView overflow). The order and
     the Ctrl+1–6 keys stay; the hidden tabs are one click away.
   - **c. Shrink the job name first.** Tabs keep A's icon + label; the job name is elided with
     "…" (full name in the tooltip and in the job-switch menu), and "Kaydedildi 14:32" shows only
     its check icon. Only if that is still not enough does b or a apply.
   A's 100 % layout is the same under all three.
   *Phase 2 review note (115 % and 130 %, which A does not draw):* on Windows at 1366 px with the
   caption buttons, A's six labelled tabs fit at 100 % and 115 % but not at 130 % (the band needs
   about 1466 px). So that nothing overlaps, the Qt band applies the same provisional tab rule
   (option a) below 150 % only while the labelled tabs do not fit, and the job name elides with
   "…" (full name in its tooltip and accessible name). Both live in `theme.title_band_rule`
   (`fits` argument) and `TitleBand.fit`; whichever option the owner picks replaces that branch.
4. **"Kontrol'e geç" twice on Yükle.** It is both the command-bar button and the inspector's
   primary, with the same icon, close together (`png/yukle-light.png`). A does the same with
   "Değerlerde aç" (menu + inspector), so it follows A's pattern and is left as it is. Option: once
   the inspector primary exists, drop the command-bar copy (it stays in the Git menu and Ctrl+2).
5. **Approved and built (owner, 2026-11-13).** **Scroll areas at 150 % text show a cut row at the edge.** At 150 % the inspector content and
   the Kontrol timeline scroll (they do not fit), so the last visible row is cut by the scroll
   area's edge (e.g. "Filtre uygula" above "Belgeyi onayla" in `png/kontrol-150-light.png`). The
   pinned buttons now sit below the scroll area instead of over it, and the thin scrollbar shows
   there is more. Together with item 1 (hairline above the pinned buttons) the owner could also
   choose to let the inspector scroll per card (a cut card is never shown; the gap is left empty).
   *Built (items 1 and 5 together):* `card_scroll.CardScroll`, one class used by every side panel
   with cards (Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber, plus Şablonlar' left
   column and Dışa Aktar's summary column). The viewport is trimmed below the last whole card
   (the rest stays empty); wheel, scroll bar, keys and focus moving into a card stop on card
   boundaries; the 1 px `stroke` hairline shows above the pinned button group only while more
   lies below. Nothing changes where the cards fit (100 %). `tools/screenshots.py` is strict
   again: a card cut by a scroll area's edge is clipped even with a scroll bar showing; only
   item views (tables, lists, the Kontrol timeline, thumbnail grids) may show a part row.

Apart from item 3 (which describes a change already visible in the provisional 150 % renders
and asks for a decision), no proposal touches the title band, logo, tabs, ≡, job name, search, caption buttons, command
bar, overview strip, inspector cards, buttons, spacing, radii, colours, fonts, labels or icons.

## Değerler (Phase 3 build notes; nothing here is applied beyond what A needs to work)

- **D1. The other boxes in the crop are invisible links.** The Qt crop is linked both ways (GOAL
  §3.2): clicking another variable's box on the same page selects that value in the table. A draws
  only the selected box, so the others are found by the pointer cursor and a tooltip ("Firma
  değerine git"). Option: draw them as a 1 px `paper-line` outline so the link can be seen.
- **D2. States A does not draw**, built only from A's empty-state component: no job ("Henüz açık
  iş yok" + "Yükle'ye git"), no templated document ("Şablonlu belge yok" + "Kontrol'e git"), a
  search that finds nothing ("Aramayla eşleşen değer yok" + "Aramayı temizle") and an empty view
  ("Kontrol bekleyen değer yok" + "Tümünü göster"). In a partly read job, a document whose values
  are not read yet shows Güven "Okunmadı" with a clock icon; it is not one of the four levels, so
  the owner may prefer an empty cell.

## Kontrol (Phase 3 build notes; nothing here is applied beyond what A needs to work)

- **K1. The job's first document has no cut.** A draws QR, filter and manual guide tabs only.
  The first document of a job was started by nothing, so its tab shows the number alone (no
  pictogram) and its lip has a 1 px solid line. Option: a small "file" pictogram, or the QR one.
- **K2. "Değerlerde aç Ctrl+4" in A's page menu.** `shortcuts.md` gives "Değerlerde aç" no key
  (Ctrl+4 stays the tab key), so the Qt menu shows no key there; Ctrl+4 still opens Değerler.
  Option: show "Ctrl+4" beside it as A does (it opens the tab, not the document).
- **K3. Timeline scrollbar at 100 %.** A clips the timeline at the second row; the Qt timeline
  holds the whole job and shows the thin scrollbar at its right edge.
- **K4. States A does not draw.** "Filtre uygula…" asks "Her belgedeki sayfa sayısı" in a small
  dialog (Vazgeç / Filtreyi uygula); Ctrl+G asks Belge or Sayfa and a number (Vazgeç / Git); a
  deleted page that is no longer part of any document stays in the document it was filed in;
  an empty page left out by "Boş sayfaları at" is dimmed with "N Boş". Each is built from A's
  components. Deleting every page of a document shows a toast naming the document with "Geri al".
- **K5. Approval survives only unchanged pages.** "Belgeyi onayla" is remembered for the exact
  pages of the document; a cut or merge that changes them makes it "İncelenmedi" again (undo
  brings it back). It is kept beside `job.json` (`incelendi.json`); option: a field in the job
  file, so the CLI and the export could also show it (a core change, D13).

## Yükle (Phase 3 build notes; nothing here is applied beyond what A needs to work)

- **Y1. "Sırada" for files that wait their turn.** Files dropped while a batch is read join a
  queue (one read at a time, one undoable "N parti ekle" at the end). A draws only "Okunuyor", so
  the waiting rows say "Sırada" with a clock icon (text-2). Option: show them as "Okunuyor" too.
- **Y2. "Tüm işler…" has no drawing.** The job switch's last row opens the empty page's layout
  (job search and the list, titled "Tüm işler", Esc goes back) even while a job is open. A draws
  only the empty page with no job. Option: a separate jobs page with sorting by date and size.
- **Y3. "İptal et" only in the command bar.** As drawn, the progress card has no cancel button;
  the bar's "İptal et" (and Ctrl+.) is the only way. Option: a quiet "İptal et" link at the end
  of the card's note line for people who look where the progress is.
- **Y4. The reason sentence.** A's demo text says "4. partide ayıraç yok, filtreyle bölünecek".
  Nothing applies the filter by itself, so the build says "4. partide ayıraç yok, Kontrol'de
  filtreyle bölebilirsiniz." (computed from the real batches).
- **Y5. Scan profile from the files.** Resolution, colour mode and paper are read from the first
  page's scan image; "İki yüzlü" cannot be known from a file, so it is not shown. A text PDF with
  no scan image shows "Tarama bilgisi yok". Option: let the user state the scanner profile
  (duplex, dpi) in Ayarlar and show that.
- **Y6. A removed batch's file stays in the job folder** until the job is deleted (Del is undoable,
  so the copy cannot go at once). Option: delete orphaned batch copies when the job is closed.

## Şablonlar (Phase 3 build notes; nothing here is applied beyond what A needs to work)

- **S1. "kaydedilmedi" is not a resting state.** A's list row and status bar say "kaydedilmedi" for
  the open template, as if saving were manual. The app has always saved every edit at once (and
  undo restores it), so the resting state is "Şablon kaydedildi 14:32" (check icon, `ok`). A's
  words and icon (`circle-dashed`) appear only during the 0,3 s before a nudge is written, and
  "Şablon kaydedilemedi" (`circle-x`, `danger`, plus a message) when the disk refuses. "Şablonu
  kaydet" (Ctrl+S) saves now and shows a toast. Option: make saving manual, as A draws it (a
  template left unsaved would then need the dirty guard of the other tabs).
- **S2. The file-name pattern.** A moves the pattern to Dışa Aktar (per job); the template's own
  default (`filename_pattern`, used by every job and the CLI) still has to be set somewhere. It is
  a third inspector card, "Dosya adı" with the field and ".pdf", in the free space under "Okunan".
  Its message sits at the field and what was typed stays. Option: a "Dosya adı" row in the left
  column, or only the per-job override in Dışa Aktar (a core question, D13).
- **S3. States A does not draw**, all from A's components. *A variable without a box*: its row
  says "kutu yok", the inspector shows its name and "Zorunlu" and one sentence ("Sayfada Kutu çiz
  (B) ile bu değişkenin kutusunu çizin."). *A template with no variables*: "Değişken yok" and
  "Eklemek için Ctrl+Shift+N tuşlarına basın.". *No example page* (no job open): A's empty state,
  "Örnek sayfa yok", "Yükle'ye git". *A read that fails* (no reader installed, damaged page): a
  message under the lists ("Okuma yapılamadı: …"). *Reading*: "Okunuyor…" appears only for a read
  longer than 0,15 s. *A later section not tried* (an earlier one already read sure): Güven
  "Okunmadı" and a "Not" row. *"Bütün örneklerde dene"*: progress in the status bar ("Örnekler
  okunuyor 2 / 4, Esc durdurur", taskbar progress), then a toast ("4 örnekte denendi. 1 okuma
  kontrol bekliyor."), and an example with reads that need a check carries the warn icon and
  "· 1 kontrol" in the Örnek picker.
- **S4. Boxes are all `paper-box` with the variable's number**, as A draws them (the four variable
  colours of the old screen are gone). A draws every box solid; the build keeps the old rule that
  a variant (second section on) or a box drawn on another example is dashed, so a box that does not
  belong to this example is not mistaken for one that does.
- **S5. The Örnek picker says "Örnek 1, sayfa 4"**, not A's "Örnek 1, Ege Kalıp San. Ltd.": the
  company is a read value, and reading all examples first would make opening the tab slow.
  Option: after "Bütün örneklerde dene", use the first variable's read value as A does.
- **S6. Zoom %100 is life size** (1 mm = 3,78 px at 96 dpi, the Word and Acrobat convention). A's
  %135 is not defined; the page starts fitted to the width (about %90 at 1366 px) and keeps that
  while the window is resized, until the user zooms. Ctrl+0 fits the width again.
- **S7. A variable with a single box is one row** (A: only "Firma unvanı", which has two, lists its
  sections). Its row stands for the box: selecting it selects the box, Del removes the box, and
  Alt+Up/Down moves the variable. A variable with two or more boxes is selected as a variable (name
  and Zorunlu in the inspector) or by one of its section rows.
- **S8. The window's own counts ("3 belge, 7 sayfa") are hidden on this tab**, so the status line
  is A's: Örnek, İmleç or Kutu position, save state, reads that need a check. They come back on the
  other tabs (the same rule Yükle uses).
- **S9. Drag to reorder** variables and sections in the left column (the grip is A's handle);
  Alt+Up / Alt+Down is the keyboard path. A draws the grip but not a drop line; Qt's is used.

## Dışa Aktar (Phase 3 build notes; nothing here is applied beyond what A needs to work)

- **E1. The file-name pattern is a per-job override.** A draws one "Dosya adı kalıbı" field; the
  core keeps the pattern in each template (`filename_pattern`, also used by the CLI). The field
  shows the templates' common pattern; typing another one replaces it for every document that has a
  template, in this export only (it is not written to the templates, and it is undoable: "Geri al:
  Dosya adı kalıbı"). When the job's templates have different patterns the field is empty with
  "Şablondaki kalıplar kullanılır". The override is kept while the program runs, not in the job
  file. Option: keep it in the job file (a core change, D13).
- **E2. "Geçersiz karakterleri değiştir" is on and cannot be switched off.** The core always takes
  the characters Windows refuses out of a name, so a switch would do nothing; the row is drawn
  checked and disabled (tooltip says why). A draws it as a live checkbox. Option: a real choice in
  the core (for example "keep the document's number instead of a cleaned name").
- **E3. The status bar's "2 engel var" uses the danger colour and the ban icon, not the rider
  orange A paints** (orange means kontrol only, D1; the Engel row beside it is danger too).
- **E4. Stopping.** As drawn, the progress card has no stop button: the command bar's "Dışa
  aktarmayı durdur" and Ctrl+. are the way (the card's note says so, as in A). Option: a quiet
  "Durdur" link at the end of the note line (same as Y3). Esc no longer stops it (shortcuts.md).
- **E5. Reason captions are the core's own words.** The core numbers a clash as "ad (2)", not
  "ad_2", and takes forbidden characters out instead of writing "-", so the rows say "Ad
  çakışması, (2) eklendi" (the "(2)" in accent) and "Geçersiz karakter silindi".
- **E6. States A does not draw**, from A's components. *The export fails* ("Dışa aktarma
  tamamlanamadı" + the core's sentence and a close button) and *is stopped* ("Dışa aktarma
  durduruldu: 3 dosya yazıldı, index.xlsx yazılmadı.") use the done card with its icon changed;
  the list then shows the plan again and the full folder is an Engel. *No folder chosen* is a Bilgi
  row ("Hedef klasör seçilmedi", "Klasör seç"); pressing Dışa aktar then puts the error under the
  field and focuses it. *A folder that is a file / cannot be written* are Engel rows. *A pattern
  with a missing or unmatched brace* is an Engel row.
- **E7. Folder.** Ayarlar' "Varsayılan dışa aktarma klasörü" is put in the field when a job opens
  (it is usually full, so the pre-flight offers "Yeni alt klasör oluştur", named after the job).
  The folder used last is not remembered: the preferences have no key for it, and the default
  must not be overwritten. "İşi sakla" is not on this screen (A has no such row); it is in Ayarlar.
- **E8. "index.xlsx'i aç"** (the sheet icon of A's bar) is added by the screen, not a registry
  action, so it is not in the menus or the palette. "Dizini yazdır…" prints the file list with the
  system print dialog; A draws no print dialog.
- **E9. The written list still says what needed a check.** After writing, every Durum is "Yazıldı"
  (as drawn) and the Kontrol files keep their reason caption at the top. Option: keep the
  "Kontrol" word and triangle in that column.

## Owner-approved for a later update (not in this overhaul)

The owner said yes to these on 2026-11-13, but for a later update, after the current runs finish:

- **Şablonlar: show only the selected variable's boxes.** A command-bar toggle (key H) that hides the other variables' boxes and variants on the canvas.
- **Şablonlar: delete the selected box.** The Del key (and a context-menu item) removes the selected box or variant. It is undoable, with no confirmation, and names the box ("Kutuyu sil: Firma_Adi, Varyant 2").

## Phase 4 review (2026-11-13): decisions the owner still has to make

The Phase 4 reviewers flagged the build notes below as deviations from A. Under the owner rule
nothing here may change A's look until the owner answers. What the build does today, and why:

- **P4-1. S1, "Şablon kaydedildi" as the resting state.** Still built as S1 describes. A's resting
  "Şablon kaydedilmedi" with circle-dashed would tell the user an autosaved template is unsaved,
  which is false ("nothing silently wrong", PRODUCT.md). Options: (a) keep S1; (b) make saving
  manual as A draws it (needs a dirty guard on every tab switch). Needs a yes or no.
- **P4-2. S2, the "Dosya adı" card on Şablonlar.** Still shown. Hiding it would leave no way in the
  app to set a template's default file name (the core's `filename_pattern`, also used by the CLI);
  every new template would then export numbered names unless each export overrides it on Dışa
  Aktar (E1). Options as in S2. Needs a yes or no.
- **P4-3. S4, dashed boxes for a variant or another example's box.** Still dashed: a solid box
  that does not belong to this example would be mistaken for one that does. Needs a yes or no.
- **P4-4. E2 is now A's look.** "Geçersiz karakterleri değiştir" is a live, checked box as A draws
  it; unticking it ticks it again and says why ("bu seçenek kapatılamaz") in a tooltip and the
  accessible description. No owner decision needed unless the owner wants a real choice.
- **P4-5. Item 3 (title-band tabs at 150 %) is decided and built** (owner, 2026-11-13, option b;
  decisions.md). Tabs always keep A's icon and name; the tabs that do not fit go into a "»" menu
  right after the strip, in strip order with their Ctrl+number keys, and the selected tab is
  always one of the visible ones (`TitleBand.fit`). At 1920 px all six fit at every text size;
  at 1366 px with the caption buttons all six fit at 100 %, and at 130 % and 150 % the first
  tabs and the selected one show (how many depends on the job name's room). The icon-only rule
  (option a) is gone. The job name still elides with "…" when the band is short (full name in
  its tooltip and accessible name), as noted in Phase 2.
- **P4-6. Item 2 (Değerler at 150 %).** Built as a fit rule, not a new look: when the table is
  wider than its pane, the long text column (then the other value columns, down to a floor)
  narrows and its long values wrap onto a second line in a taller row (full value also in
  its tooltip), so the Güven column stays in view.
  Only when even the floors do not fit does the table scroll sideways as A draws it. Option: pin
  Güven as a frozen right column instead (a second view), or move it next to the value.
- **P4-7. Dışa Aktar at 150 %.** The file name is never elided: the Şablon column (also in each
  row's tooltip) steps aside first, then Durum narrows; this matches A's own 150 % render, where
  Şablon is out of view.

## Phase 4 additions that need the owner's yes (not yet visible, or visible only in Ayarlar)

- **P4-8. Ayarlar > Kısayollar: "Tek tuşlu kısayollar" check box** (default on, WCAG 2.1.4). It is
  a settings-dialog row, not a change to A's screens. Needs a yes or no on the wording.
- **P4-9. Düzen > "Geri alma geçmişi" submenu** (the GOAL §3.1 "one visible undo history"): every
  step by name, newest first; choosing one goes back (or forward) to it. A has no drawing for it.
- **P4-10. Visible mm fields in Şablonlar' Kutu card.** The card already has X, Y, width and height
  spin boxes; the keyboard can now also place (B, Enter) and resize (Ctrl+arrows) a box. Proposal:
  a one-line hint under the fields ("B ve Enter: kutu koy · Ctrl+oklar: boyut").
- **P4-11. Yükle's empty page while jobs exist.** A titles it "Henüz iş yok" above a list of
  existing jobs. Proposal: when jobs exist, title "Açık iş yok" with "Bir iş seçin ya da yeni bir iş
  oluşturun." (copy only).
- **P4-12. Uncertain characters drawn on the Değerler crop.** A marks them on the scan. The app
  does not know where each character sits inside the box (the readers return text, not glyph
  positions), so marking them would be a guess drawn as evidence. Option: a core hook for glyph
  boxes from the OCR engines (D13), then draw them.
- **P4-13. A filter field for the Dışa Aktar file list** (QOL 8, 1,000-file exports). Today Ctrl+F
  focuses the list and typing a file name jumps to it. Option: a search field in the list's head
  bar, as Değerler has.
