# Shortcut mismatches (Phase 3, step 1)

Status column added by Görev 3E (fixes need no new text and no owner decision; B-047 is fixed too: Ctrl+P on Dışa Aktar, `test_*[disa_aktar.yazdir[disa_aktar]Ctrl+P]`). Written by agent 3A from the handlers as they are on 2026-11-19; code unchanged. Every row is a place where today's behaviour differs from the contract in `docs/ui-goal/shortcut-contract.tsv` (that file holds the INTENDED behaviour).

Contract rows: 319 (registry bindings per tab where active). Rows touched by at least one mismatch: 138. By kind (a row can have more than one): silent key 135, label drift 11, wrong verb 9. Rows whose fix needs new Turkish text: 80.

Kinds: **silent key** = the key does nothing visible or is disabled with no reason shown; **wrong verb** = the key does something else than its label or its other tabs; **label drift** = menu text, tooltip or label does not say what the key does. Severity 1 = fix first.

## Mismatches

| ID | Sev | Kind | Tab | Key | Action | Today | Intended | New text | Ledger | Rows | Owner decides | Status (3E) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M-01 | 1 | silent key | Yükle, Şablonlar, Dışa Aktar, Rehber | Ctrl+G | app.git | Ctrl+G is disabled on four tabs; the menu item 'Belgeye veya sayfaya git…' is greyed with no reason (shortcuts.md says it is the same on every tab) | route Ctrl+G on every tab: Şablonlar picks the Örnek, Dışa Aktar the file row; Yükle and Rehber say 'PROPOSED: Bu sekmede belge listesi yok. Kontrol sekmesinde Ctrl+G ile belgeye gidin.' OWNER decides: route, or correct shortcuts.md to 'Kontrol and Değerler only' | yes | B-027 | 4 | yes | open (waits for owner text, Q-08) |
| M-07 | 1 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar | F3, Shift+F3 | app.sonraki_sonuc + app.onceki_sonuc | F3 and Shift+F3 are disabled on five tabs (only Rehber steps through hits), menu items greyed without a reason | key stays on and says 'PROPOSED: Bu sekmede aranacak sonuç yok.' | yes | none | 10 | no | open (waits for owner text, Q-08) |
| M-22 | 1 | silent key | Kontrol, Rehber | F5 | app.yenile | F5 is enabled and does nothing, nothing said | key disabled on these tabs with the tooltip 'PROPOSED: Bu sekmede yenilenecek bir şey yok.' | yes | B-028 | 2 | no | open (waits for owner text, Q-08) |
| M-33 | 1 | wrong verb | Kontrol | R, Shift+R, Del | kontrol.sil + saga_dondur + sola_dondur | with the loupe open on one page, R and Del act on EVERY selected page, not the page shown | act on the page shown, or the loupe says it acts on the selection | no | B-033 | 3 | yes | open (owner decision, Q-08) |
| M-34 | 1 | label drift | Şablonlar | Del | sablonlar.kutu_sil | label 'Kutuyu sil' while a variable without a box is chosen: the whole variable is removed (undoable, the toast names it) | item reads 'Değişkeni sil' when a variable is chosen (existing undo-entry text) | no | B-015 | 1 | no | fixed (3E, test_sablon_delete_item_names_a_variable; ledger B-015 test_b015_the_delete_command_names_what_it_deletes) |
| M-03 | 2 | label drift | Kontrol | Ctrl+F | app.bul | Ctrl+F is labelled 'Bul…' but opens the go-to dialog (Kontrol has no text search) | the item on Kontrol reads 'Belgeye veya sayfaya git…' (existing text) or Ctrl+F is left to Ctrl+G there | no | B-026 | 1 | yes | open (owner decision, Q-08) |
| M-10 | 2 | silent key | Yükle, Kontrol, Değerler, Dışa Aktar | Ctrl+S | app.kaydet | no job: key disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 4 | no | fixed (3E, test_not_applicable[app.kaydet[yukle]Ctrl+S], test_not_applicable[app.kaydet[kontrol]Ctrl+S], test_not_applicable[app.kaydet[degerler]Ctrl+S], test_not_applicable[app.kaydet[disa_aktar]Ctrl+S]) |
| M-12 | 2 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | Ctrl+E | app.disa_aktar | no job: Ctrl+E disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 6 | no | fixed (3E, test_not_applicable[app.disa_aktar[yukle]Ctrl+E], test_not_applicable[app.disa_aktar[kontrol]Ctrl+E], test_not_applicable[app.disa_aktar[sablonlar]Ctrl+E], test_not_applicable[app.disa_aktar[degerler]Ctrl+E], test_not_applicable[app.disa_aktar[disa_aktar]Ctrl+E], test_not_applicable[app.disa_aktar[rehber]Ctrl+E], test_export_key_with_no_job_on_the_export_tab) |
| M-13 | 2 | silent key | Dışa Aktar | Ctrl+E | app.disa_aktar | blocked or running: Ctrl+E disabled; the toast 'Dışa aktarılamıyor: <neden>' appears only when the button is clicked | key stays on and shows that toast (existing text) | no | none | 1 | no | open: fix written and reverted; tests/ui/test_disa_aktar.py::test_registry_actions_are_wired_and_enabled_when_usable asserts Ctrl+E is off while blocked |
| M-14 | 2 | wrong verb | Yükle, Kontrol, Şablonlar, Değerler, Rehber | Ctrl+E | app.disa_aktar | label 'Dışa aktar…' (an action) but on five tabs the key only opens the Dışa Aktar tab; only on Dışa Aktar does it start the export | keep (starting an export blind from another tab is unsafe) and document as page-specific; OWNER decides whether the label should read 'Dışa Aktar sekmesine git' there | no | none | 5 | yes | open (owner decision, Q-08) |
| M-17 | 2 | silent key | Rehber | Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z | app.geri_al + app.yinele | Ctrl+Z / Ctrl+Y on Rehber change the job's Kontrol or Değerler state out of sight; nothing on screen says what happened | status line 'PROPOSED: Geri alındı: <adım>.' / 'PROPOSED: Yinelendi: <adım>.' | yes | none | 3 | no | open (waits for owner text, Q-08) |
| M-31 | 2 | silent key | Kontrol | R, Shift+R, Del | kontrol.saga_dondur + kontrol.sola_dondur + kontrol.sil | R, Shift+R and Del with nothing selected return without a word | status line 'Önce sayfaları seçin.' (existing text) | no | none | 3 | no | fixed (3E, test_not_applicable[kontrol.saga_dondur[kontrol]R], test_not_applicable[kontrol.sola_dondur[kontrol]Shift+R], test_not_applicable[kontrol.sil[kontrol]Del]) |
| M-02 | 3 | silent key | Değerler | Ctrl+G | app.git | no rows: go_to() returns without a word | status line 'PROPOSED: Gidilecek bir belge yok.' | yes | none | 1 | no | open (waits for owner text, Q-08) |
| M-04 | 3 | silent key | Kontrol, Dışa Aktar | Ctrl+F | app.bul | no job: key disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 2 | no | fixed (3E, no job: test_not_applicable[app.bul[kontrol]Ctrl+F], test_not_applicable[app.bul[disa_aktar]Ctrl+F]) |
| M-06 | 3 | silent key | Değerler | Ctrl+F | app.bul | search field disabled: the key does nothing, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 1 | no | fixed (3E, test_not_applicable[app.bul[degerler]Ctrl+F]) |
| M-08 | 3 | silent key | Rehber | F3, Shift+F3 | app.sonraki_sonuc + app.onceki_sonuc | no query or no hits: key disabled; step() would say 'Sonuç yok' but is unreachable by key | key stays on and announces 'Sonuç yok' (existing text) | no | none | 2 | no | open: fix written and reverted; tests/ui/test_rehber.py::test_the_tab_wires_its_actions_and_fills_the_bar_and_status asserts F3 / Shift+F3 are disabled with no hits |
| M-09 | 3 | silent key | Rehber | Ctrl+S | app.kaydet | Ctrl+S is off on Rehber (by design) with no word | status line 'PROPOSED: Rehber'de kaydedilecek bir şey yok.' | yes | none | 1 | no | open (waits for owner text, Q-08) |
| M-11 | 3 | silent key | Şablonlar | Ctrl+S | app.kaydet | no template: key disabled; the text in save() ('Kaydedilecek bir şablon yok. Önce bir şablon oluşturun.') is unreachable by key | key stays on and shows that existing text | no | none | 1 | no | fixed (3E, test_not_applicable[app.kaydet[sablonlar]Ctrl+S]) |
| M-15 | 3 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | Ctrl+W | app.isi_kapat | no job: Ctrl+W disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 6 | no | open: fix written and reverted; effect.job_closed (contract_helpers.py) asserts Ctrl+W is disabled after closing |
| M-18 | 3 | silent key | Yükle, Dışa Aktar | Ctrl+Num++, Ctrl++, Ctrl+=, Ctrl+-, Ctrl+Num+-, Ctrl+0 | app.yakinlastir + app.uzaklastir + app.sigdir | no zoom on these tabs: the six zoom keys are disabled, nothing said | key stays on and says 'PROPOSED: Bu sekmede yakınlaştırılacak bir şey yok.' | yes | none | 12 | no | open (waits for owner text, Q-08) |
| M-20 | 3 | label drift | Kontrol, Rehber | Ctrl+0 | app.sigdir | 'Sığdır' (tooltip 'Sayfaya sığdır') resets thumbnails or guide text to 100 %, it does not fit anything | tooltip on these two tabs 'PROPOSED: Varsayılan boyuta dön (Ctrl+0)' | yes | none | 2 | no | open (waits for owner text, Q-08) |
| M-25 | 3 | silent key | Yükle | Alt+Up, Alt+Down, Del | yukle.yukari + yukle.asagi + yukle.cikar | no batch selected or batch at the edge: key disabled, nothing said | status lines 'PROPOSED: Önce bir parti seçin.' and 'PROPOSED: Parti zaten ilk sırada.' / 'PROPOSED: Parti zaten son sırada.' | yes | none | 3 | no | open (waits for owner text, Q-08) |
| M-27 | 3 | label drift | Yükle | F2 | yukle.yeniden_adlandir | label 'Yeniden adlandır' next to a batch list, but F2 renames the JOB | label 'İşi yeniden adlandır' (the dialog title already says it) | no | none | 1 | yes | open (owner decision, Q-08) |
| M-28 | 3 | silent key | Yükle, Değerler, Dışa Aktar | Ctrl+. | yukle.iptal + degerler.durdur + disa_aktar.durdur | nothing running: Ctrl+. disabled, nothing said | status line 'PROPOSED: Şu an durdurulacak bir iş yok.' | yes | none | 3 | no | open (waits for owner text, Q-08) |
| M-30 | 3 | silent key | Kontrol | Ctrl+A, Esc, K, M, R, Shift+R, Del, Return, Enter, F, T, Space, N, Shift+N, U, Ctrl+Right, Ctrl+Left | kontrol.tumunu_sec + secimi_kaldir + kes + birlestir + saga_dondur + sola_dondur + sil + onayla + filtre + sablon + onizle + sonraki_kontrol + onceki_kontrol + sonraki_incelenmemis + sonraki_belge + onceki_belge | no job: every Kontrol key is disabled (the binder's 'Önce Yükle sekmesinden…' text shows only when a command is clicked while enabled, which never happens) | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 17 | no | open: fix written and reverted; tests/ui/test_main_window.py::test_kontrol_without_a_job_offers_the_way_to_yukle asserts the Kontrol keys are disabled with no job (and a focused placeholder button owns Enter / Space) |
| M-35 | 3 | silent key | Şablonlar | Del, Ctrl+D, Ctrl+Shift+N, Alt+Up, Alt+Down | sablonlar.kutu_sil + kutu_cogalt + degisken_ekle + yukari + asagi | no variable, box or template: keys disabled, nothing said | status lines 'PROPOSED: Önce bir değişken ya da kutu seçin.', 'PROPOSED: Önce bir kutu seçin.', 'PROPOSED: Önce bir şablon seçin ya da oluşturun.', 'PROPOSED: Zaten ilk sırada.' / 'PROPOSED: Zaten son sırada.' | yes | none | 5 | no | open (waits for owner text, Q-08) |
| M-37 | 3 | silent key | Şablonlar | Ctrl+T | sablonlar.dene | no page: Ctrl+T disabled; 'Denemek için bir şablon ve açık bir iş gerekir.' is unreachable by key | key stays on and shows that existing text | no | none | 1 | no | fixed (3E, test_not_applicable[sablonlar.dene[sablonlar]Ctrl+T]) |
| M-38 | 3 | label drift | Şablonlar | Alt+Up, Alt+Down | sablonlar.yukari + sablonlar.asagi | label 'Değişkeni yukarı/aşağı taşı' but with a box chosen in a multi-box variable the BOX's try order moves | item names what moves: 'PROPOSED: Bölümü yukarı taşı' / 'PROPOSED: Bölümü aşağı taşı' when a section is chosen | yes | none | 2 | no | open (waits for owner text, Q-08) |
| M-39 | 3 | wrong verb | Şablonlar | Space | sablonlar.el | Space = hold to pan on the canvas, but Space = show the page large on Kontrol and Değerler | keep and document as page-specific (hand tool convention); OWNER decides | no | none | 1 | yes | open (owner decision, Q-08) |
| M-41 | 3 | silent key | Değerler | Return, Enter, Ctrl+Return, Ctrl+Enter, F2, V, Ctrl+A, Space | degerler.* (single keys) | no current value, no selection or no rows: keys disabled, nothing said | status lines 'PROPOSED: Önce bir değer seçin.', 'PROPOSED: Önce satırları seçin.', 'PROPOSED: Önce şablonu olan bir belge seçin.' | yes | none | 8 | no | open (waits for owner text, Q-08) |
| M-42 | 3 | silent key | Değerler | N, Shift+N | degerler.sonraki_kontrol + degerler.onceki_kontrol | no value waiting: key disabled, so 'Kontrol bekleyen değer yok.' (and the toast) are unreachable by key | key stays on and shows that existing text | no | none | 2 | no | open: fix written and reverted; broken.degerler_no_check (contract_degerler.py) asserts N is disabled in the broken state |
| M-43 | 3 | label drift | Değerler | Esc | degerler.vazgec | label and tooltip say 'Vazgeç' / 'Değişikliği bırak' but Esc only closes the page view or trims a multi-row selection | label 'Seçimi kaldır' like Kontrol, or leave 'Vazgeç' and fix the tooltip; OWNER decides | no | none | 1 | yes | open (owner decision, Q-08) |
| M-05 | 4 | silent key | Şablonlar | Ctrl+F | app.bul | no template: focus moves to an empty list, nothing said | status line 'PROPOSED: Aranacak değişken yok.' | yes | none | 1 | no | open (waits for owner text, Q-08) |
| M-16 | 4 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z | app.geri_al + app.yinele | empty stack: key disabled, item greyed, nothing said | status line 'PROPOSED: Geri alınacak bir şey yok.' / 'PROPOSED: Yinelenecek bir şey yok.' | yes | none | 18 | no | open (waits for owner text, Q-08) |
| M-19 | 4 | silent key | Şablonlar | Ctrl+Num++, Ctrl++, Ctrl+=, Ctrl+-, Ctrl+Num+-, Ctrl+0 | app.yakinlastir + app.uzaklastir + app.sigdir | no template or page: zoom keys disabled, nothing said | same text as above | yes | none | 6 | no | open (waits for owner text, Q-08) |
| M-21 | 4 | silent key | Kontrol | F9 | app.yan_panel | before a job is open the Kontrol placeholder has no side panel: F9 disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 1 | no | fixed (3E, test_not_applicable[app.yan_panel[kontrol]F9]) |
| M-23 | 4 | silent key | Dışa Aktar | F5 | app.yenile | empty or running: F5 disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' when empty (existing text) | no | none | 1 | no | fixed for the empty case (3E, test_not_applicable[app.yenile[disa_aktar]F5]); while an export runs F5 stays disabled (no existing text) |
| M-24 | 4 | silent key | Rehber | F1 | app.yardim | F1 on Rehber changes nothing visible | focus moves to the guide text | no | none | 1 | no | fixed (3E, test_key_effect_and_feedback / test_not_applicable / test_same_through_menu_or_palette[app.yardim[rehber]F1]) |
| M-26 | 4 | silent key | Yükle | Ctrl+Shift+O, F2 | yukle.yeniden_adlandir + yukle.gezginde_goster | no job: key disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 2 | no | fixed (3E, test_not_applicable[yukle.yeniden_adlandir[yukle]F2], test_not_applicable[yukle.gezginde_goster[yukle]Ctrl+Shift+O]) |
| M-29 | 4 | label drift | Yükle, Değerler, Dışa Aktar | Ctrl+. | yukle.iptal / degerler.durdur / disa_aktar.durdur | same key, same verb (stop what is running) but three labels: 'İptal et', 'Okumayı durdur', 'Dışa aktarmayı durdur' | document as page-specific (the object differs); OWNER decides whether Yükle should read 'Okumayı durdur' | no | none | 3 | yes | open (owner decision, Q-08) |
| M-32 | 4 | silent key | Kontrol | K, M, Space | kontrol.kes + kontrol.birlestir + kontrol.onizle | no current page: key returns without a word | status line 'Önce bir sayfa seçin.' (existing text) | no | none | 3 | no | fixed (3E, test_not_applicable[kontrol.kes[kontrol]K], test_not_applicable[kontrol.birlestir[kontrol]M], test_not_applicable[kontrol.onizle[kontrol]Space]) |
| M-36 | 4 | silent key | Şablonlar | B, G | sablonlar.kutu_ciz + sablonlar.izgara | no template or page: B and G disabled, nothing said | status lines 'PROPOSED: Kutu çizmek için bir şablon ve bir örnek sayfa gerekir.' / 'PROPOSED: Izgara için bir şablon ve bir örnek sayfa gerekir.' | yes | none | 2 | no | open (waits for owner text, Q-08) |
| M-44 | 4 | silent key | Dışa Aktar | Ctrl+Shift+O, Ctrl+P | disa_aktar.yazdir + disa_aktar.gezginde_goster | empty list or no folder: keys disabled, nothing said | status lines 'PROPOSED: Yazdırılacak bir dizin yok.' / 'PROPOSED: Gösterilecek bir klasör yok.' | yes | none | 2 | no | open (waits for owner text, Q-08) |
| M-40 | 5 | silent key | Şablonlar | Left, Up, Right, Down, Shift+Left, Shift+Up, Shift+Right, Shift+Down | sablonlar.kaydir + sablonlar.kaydir_1mm | arrows with no box chosen scroll the view or move the list; nothing says why the box did not move | no change needed: the status hint 'Kaydır: ok tuşları 0,25 mm' already shows when a box has focus (accept; OWNER?) | no | none | 8 | no | open |
| M-45 | 5 | silent key | Kontrol, Değerler, Rehber | Esc | kontrol.secimi_kaldir + degerler.vazgec + rehber.aramayi_temizle | Esc with nothing to dismiss does nothing | accept: a dismiss key stays quiet (OWNER? approve) | no | none | 3 | yes | open (owner decision, Q-08) |

## New Turkish texts for the owner to approve

None of these is in `src/`. Each appears in the contract's feedback column prefixed `PROPOSED:`.

1. Bu sekmede belge listesi yok. Kontrol sekmesinde Ctrl+G ile belgeye gidin.
2. Gidilecek bir belge yok.
3. Aranacak değişken yok.
4. Bu sekmede aranacak sonuç yok.
5. Rehber'de kaydedilecek bir şey yok.
6. Geri alınacak bir şey yok.
7. Yinelenecek bir şey yok.
8. Geri alındı: <adım>.
9. Yinelendi: <adım>.
10. Bu sekmede yakınlaştırılacak bir şey yok.
11. Varsayılan boyuta dön (Ctrl+0)
12. Bu sekmede yenilenecek bir şey yok.
13. Parti zaten ilk sırada.
14. Parti zaten son sırada.
15. Önce bir parti seçin.
16. Şu an durdurulacak bir iş yok.
17. Önce bir şablon seçin ya da oluşturun.
18. Önce bir değişken ya da kutu seçin.
19. Önce bir kutu seçin.
20. Zaten ilk sırada.
21. Zaten son sırada.
22. Kutu çizmek için bir şablon ve bir örnek sayfa gerekir.
23. Izgara için bir şablon ve bir örnek sayfa gerekir.
24. Bölümü yukarı taşı
25. Bölümü aşağı taşı
26. Önce şablonu olan bir belge seçin.
27. Önce bir değer seçin.
28. Önce satırları seçin.
29. Gösterilecek bir klasör yok.
30. Yazdırılacak bir dizin yok.
31. Önce bir değişken seçin.

## Where two tabs differ on purpose (owner decides: keep and document, or change)

The 14 keys of `docs/ui-goal/baseline/shortcuts-divergent.txt`. The contract's `same_as` column says `page-specific: <why>` for each.

| Key | Tabs and labels | Proposal |
|---|---|---|
| Alt+Up / Alt+Down | Yükle 'Partiyi yukarı/aşağı taşı', Şablonlar 'Değişkeni yukarı/aşağı taşı' | keep: same verb, own list; fix Şablonlar label (M-38) |
| Ctrl+. | Yükle 'İptal et', Değerler 'Okumayı durdur', Dışa Aktar 'Dışa aktarmayı durdur' | keep: same verb, three objects (M-29) |
| Ctrl+P | Dışa Aktar 'Dizini yazdır…', Rehber 'Ayıraç sayfasını yazdır…' | keep: decided in shortcuts.md |
| Del | Yükle 'Partiyi çıkar', Kontrol 'Sayfayı sil', Şablonlar 'Kutuyu sil' | keep: same verb on the chosen item, always undoable (M-34) |
| Enter / Return | Kontrol 'Belgeyi onayla', Değerler 'Onayla ve sonrakine geç' | keep: decided (Enter confirms and moves on) |
| Esc | Kontrol 'Seçimi kaldır', Değerler 'Vazgeç', Rehber 'Aramayı temizle' | keep: dismiss; fix Değerler label (M-43) |
| F2 | Yükle 'Yeniden adlandır', Değerler 'Elle yaz' | keep: edit the current item by name (M-27) |
| Left / Right | Kontrol 'Önceki / sonraki sayfa', Şablonlar 'Kutuyu 0,25 mm kaydır' | keep: local keys of the widget with focus |
| Shift+Left / Shift+Right | Kontrol 'Seçimi genişlet', Şablonlar 'Kutuyu 1 mm kaydır' | keep: local keys of the widget with focus |
| Space | Kontrol 'Önizle', Değerler 'Tüm sayfayı göster', Şablonlar 'Sayfayı sürükle' | OWNER? the verb differs on Şablonlar (M-39) |

## Other decisions for the owner

- Ctrl+G (M-01): route it on all six tabs as shortcuts.md says, or change shortcuts.md to 'Kontrol and Değerler only'.
- Ctrl+E (M-14): keep 'opens Dışa Aktar from other tabs, starts the export there'.
- Esc with nothing to dismiss (M-45) and arrows with no box chosen (M-40): accept silence.
- Undo and redo with an empty stack (M-16): greyed item only, or the proposed status line.
