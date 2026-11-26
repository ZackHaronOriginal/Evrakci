# Shortcut mismatches (Phase 3, step 1)

Status column added by Görev 3E (fixes need no new text and no owner decision; B-047 is fixed too: Ctrl+P on Dışa Aktar, `test_*[disa_aktar.yazdir[disa_aktar]Ctrl+P]`). Written by agent 3A from the handlers as they are on 2026-11-19; code unchanged. Every row is a place where today's behaviour differs from the contract in `docs/ui-goal/shortcut-contract.tsv` (that file holds the INTENDED behaviour).

Contract rows: 319 (registry bindings per tab where active). Rows touched by at least one mismatch: 138. By kind (a row can have more than one): silent key 135, label drift 11, wrong verb 9. Rows whose fix needs new Turkish text: 80.

Kinds: **silent key** = the key does nothing visible or is disabled with no reason shown; **wrong verb** = the key does something else than its label or its other tabs; **label drift** = menu text, tooltip or label does not say what the key does. Severity 1 = fix first.

## Mismatches

| ID | Sev | Kind | Tab | Key | Action | Today | Intended | New text | Ledger | Rows | Owner decides | Status (3E) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M-01 | 1 | silent key | Yükle, Şablonlar, Dışa Aktar, Rehber | Ctrl+G | app.git | Ctrl+G is disabled on four tabs; the menu item 'Belgeye veya sayfaya git…' is greyed with no reason (shortcuts.md says it is the same on every tab) | route Ctrl+G on every tab: Şablonlar picks the Örnek, Dışa Aktar the file row; Yükle and Rehber say 'PROPOSED: Bu sekmede belge listesi yok. Kontrol sekmesinde Ctrl+G ile belgeye gidin.' OWNER decides: route, or correct shortcuts.md to 'Kontrol and Değerler only' | yes | B-027 | 4 | yes | fixed (Q5: Ctrl+G is on every tab, B-027; Şablonlar picks the Örnek, Dışa Aktar the file row, Yükle and Rehber say 'Belgeye gitmek için Kontrol sekmesini açın (Ctrl+2).'; tests/ui/test_shortcut_contract.py::*app.git*, test_q5_shortcuts.py) |
| M-07 | 1 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar | F3, Shift+F3 | app.sonraki_sonuc + app.onceki_sonuc | F3 and Shift+F3 are disabled on five tabs (only Rehber steps through hits), menu items greyed without a reason | key stays on and says 'PROPOSED: Bu sekmede aranacak sonuç yok.' | yes | none | 10 | no | fixed (Q5: greyed, tooltip and key say 'Bu sekmede aranacak sonuç yok.'; tests/ui/test_shortcut_contract.py::*sonuc*) |
| M-22 | 1 | silent key | Kontrol, Rehber | F5 | app.yenile | F5 is enabled and does nothing, nothing said | key disabled on these tabs with the tooltip 'PROPOSED: Bu sekmede yenilenecek bir şey yok.' | yes | B-028 | 2 | no | fixed (Q5, B-028: F5 is off on Kontrol and Rehber and says 'Bu sekmede yenilenecek bir şey yok.') |
| M-33 | 1 | wrong verb | Kontrol | R, Shift+R, Del | kontrol.sil + saga_dondur + sola_dondur | with the loupe open on one page, R and Del act on EVERY selected page, not the page shown | act on the page shown, or the loupe says it acts on the selection | no | B-033 | 3 | yes | fixed earlier (7f14c61, B-033: the loupe keys act on the page shown; tests/ui/test_p4_review_fixes.py::test_r_shift_r_del_act_on_the_loupe_page_only) |
| M-34 | 1 | label drift | Şablonlar | Del | sablonlar.kutu_sil | label 'Kutuyu sil' while a variable without a box is chosen: the whole variable is removed (undoable, the toast names it) | item reads 'Değişkeni sil' when a variable is chosen (existing undo-entry text) | no | B-015 | 1 | no | fixed (3E, test_sablon_delete_item_names_a_variable; ledger B-015 test_b015_the_delete_command_names_what_it_deletes) |
| M-03 | 2 | label drift | Kontrol | Ctrl+F | app.bul | Ctrl+F is labelled 'Bul…' but opens the go-to dialog (Kontrol has no text search) | the item on Kontrol reads 'Belgeye veya sayfaya git…' (existing text) or Ctrl+F is left to Ctrl+G there | no | B-026 | 1 | yes | fixed (Q5: the item reads 'Belgeye veya sayfaya git…' on Kontrol; test_q5_shortcuts.py::test_b026_*) |
| M-10 | 2 | silent key | Yükle, Kontrol, Değerler, Dışa Aktar | Ctrl+S | app.kaydet | no job: key disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 4 | no | fixed (3E, test_not_applicable[app.kaydet[yukle]Ctrl+S], test_not_applicable[app.kaydet[kontrol]Ctrl+S], test_not_applicable[app.kaydet[degerler]Ctrl+S], test_not_applicable[app.kaydet[disa_aktar]Ctrl+S]) |
| M-12 | 2 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | Ctrl+E | app.disa_aktar | no job: Ctrl+E disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 6 | no | fixed (3E, test_not_applicable[app.disa_aktar[yukle]Ctrl+E], test_not_applicable[app.disa_aktar[kontrol]Ctrl+E], test_not_applicable[app.disa_aktar[sablonlar]Ctrl+E], test_not_applicable[app.disa_aktar[degerler]Ctrl+E], test_not_applicable[app.disa_aktar[disa_aktar]Ctrl+E], test_not_applicable[app.disa_aktar[rehber]Ctrl+E], test_export_key_with_no_job_on_the_export_tab) |
| M-13 | 2 | silent key | Dışa Aktar | Ctrl+E | app.disa_aktar | blocked or running: Ctrl+E disabled; the toast 'Dışa aktarılamıyor: <neden>' appears only when the button is clicked | key stays on and shows that toast (existing text) | no | none | 1 | no | fixed (Q5, Q-09: Ctrl+E stays greyed while blocked or running and says 'Dışa aktarılamıyor: <neden>' in the status bar; the export does not start) |
| M-14 | 2 | wrong verb | Yükle, Kontrol, Şablonlar, Değerler, Rehber | Ctrl+E | app.disa_aktar | label 'Dışa aktar…' (an action) but on five tabs the key only opens the Dışa Aktar tab; only on Dışa Aktar does it start the export | keep (starting an export blind from another tab is unsafe) and document as page-specific; OWNER decides whether the label should read 'Dışa Aktar sekmesine git' there | no | none | 5 | yes | kept (Q5: page-specific on purpose, starting an export from another tab is unsafe; documented in shortcuts.md) |
| M-17 | 2 | silent key | Rehber | Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z | app.geri_al + app.yinele | Ctrl+Z / Ctrl+Y on Rehber change the job's Kontrol or Değerler state out of sight; nothing on screen says what happened | status line 'PROPOSED: Geri alındı: <adım>.' / 'PROPOSED: Yinelendi: <adım>.' | yes | none | 3 | no | resolved differently (Q5): B-055 stays, Rehber shows nothing of the job so Ctrl+Z and Ctrl+Y are off there and say 'Rehber'de geri alınacak bir şey yok.' / 'Rehber'de yinelenecek bir şey yok.'; the proposed 'Geri alındı: <adım>.' texts are not used |
| M-31 | 2 | silent key | Kontrol | R, Shift+R, Del | kontrol.saga_dondur + kontrol.sola_dondur + kontrol.sil | R, Shift+R and Del with nothing selected return without a word | status line 'Önce sayfaları seçin.' (existing text) | no | none | 3 | no | fixed (3E, test_not_applicable[kontrol.saga_dondur[kontrol]R], test_not_applicable[kontrol.sola_dondur[kontrol]Shift+R], test_not_applicable[kontrol.sil[kontrol]Del]) |
| M-02 | 3 | silent key | Değerler | Ctrl+G | app.git | no rows: go_to() returns without a word | status line 'PROPOSED: Gidilecek bir belge yok.' | yes | none | 1 | no | fixed (Q5: 'Gidilecek bir belge yok.'; tests/ui/test_shortcut_contract.py::test_degerler_go_to_with_a_job_but_no_rows_says_so) |
| M-04 | 3 | silent key | Kontrol, Dışa Aktar | Ctrl+F | app.bul | no job: key disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 2 | no | fixed (3E, no job: test_not_applicable[app.bul[kontrol]Ctrl+F], test_not_applicable[app.bul[disa_aktar]Ctrl+F]) |
| M-06 | 3 | silent key | Değerler | Ctrl+F | app.bul | search field disabled: the key does nothing, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 1 | no | fixed (3E, test_not_applicable[app.bul[degerler]Ctrl+F]) |
| M-08 | 3 | silent key | Rehber | F3, Shift+F3 | app.sonraki_sonuc + app.onceki_sonuc | no query or no hits: key disabled; step() would say 'Sonuç yok.' but is unreachable by key | key stays on and announces 'Sonuç yok.' (existing text) | no | none | 2 | no | fixed (Q5: greyed with 'Sonuç yok.' as reason, key and palette say it) |
| M-09 | 3 | silent key | Rehber | Ctrl+S | app.kaydet | Ctrl+S is off on Rehber (by design) with no word | status line 'PROPOSED: Rehber'de kaydedilecek bir şey yok.' | yes | none | 1 | no | fixed (Q5: 'Rehber'de kaydedilecek bir şey yok.') |
| M-11 | 3 | silent key | Şablonlar | Ctrl+S | app.kaydet | no template: key disabled; the text in save() ('Kaydedilecek bir şablon yok. Önce bir şablon oluşturun.') is unreachable by key | key stays on and shows that existing text | no | none | 1 | no | fixed (Q5, Q-09: Ctrl+S stays greyed and says 'Kaydedilecek bir şablon yok. Önce bir şablon oluşturun.'; test_sablon_window.py keeps asserting the key is off) |
| M-15 | 3 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | Ctrl+W | app.isi_kapat | no job: Ctrl+W disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 6 | no | fixed (Q5, Q-09: Ctrl+W with no job says 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).') |
| M-18 | 3 | silent key | Yükle, Dışa Aktar | Ctrl+Num++, Ctrl++, Ctrl+=, Ctrl+-, Ctrl+Num+-, Ctrl+0 | app.yakinlastir + app.uzaklastir + app.sigdir | no zoom on these tabs: the six zoom keys are disabled, nothing said | key stays on and says 'PROPOSED: Bu sekmede yakınlaştırılacak bir şey yok.' | yes | none | 12 | no | fixed (Q5: 'Bu sekmede yakınlaştırılacak bir şey yok.') |
| M-20 | 3 | label drift | Kontrol, Rehber | Ctrl+0 | app.sigdir | 'Sığdır' (tooltip 'Sayfaya sığdır') resets thumbnails or guide text to 100 %, it does not fit anything | tooltip on these two tabs 'PROPOSED: Varsayılan boyuta dön (Ctrl+0)' | yes | none | 2 | no | fixed (Q5: the item reads 'Varsayılan boyut', tooltip 'Varsayılan boyuta dön (Ctrl+0)' on Kontrol and Rehber) |
| M-25 | 3 | silent key | Yükle | Alt+Up, Alt+Down, Del | yukle.yukari + yukle.asagi + yukle.cikar | no batch selected or batch at the edge: key disabled, nothing said | status lines 'PROPOSED: Önce bir parti seçin.' and 'PROPOSED: Parti zaten ilk sırada.' / 'PROPOSED: Parti zaten son sırada.' | yes | none | 3 | no | fixed (Q5: 'Önce bir parti seçin.', 'Parti zaten ilk sırada.', 'Parti zaten son sırada.') |
| M-27 | 3 | label drift | Yükle | F2 | yukle.yeniden_adlandir | label 'Yeniden adlandır' next to a batch list, but F2 renames the JOB | label 'İşi yeniden adlandır' (the dialog title already says it) | no | none | 1 | yes | fixed (Q5: label 'İşi yeniden adlandır') |
| M-28 | 3 | silent key | Yükle, Değerler, Dışa Aktar | Ctrl+. | yukle.iptal + degerler.durdur + disa_aktar.durdur | nothing running: Ctrl+. disabled, nothing said | status line 'PROPOSED: Şu an durdurulacak bir iş yok.' | yes | none | 3 | no | fixed (Q5: 'Şu an durdurulacak bir iş yok.') |
| M-30 | 3 | silent key | Kontrol | Ctrl+A, Esc, K, M, R, Shift+R, Del, Return, Enter, F, T, Space, N, Shift+N, U, Ctrl+Right, Ctrl+Left | kontrol.tumunu_sec + secimi_kaldir + kes + birlestir + saga_dondur + sola_dondur + sil + onayla + filtre + sablon + onizle + sonraki_kontrol + onceki_kontrol + sonraki_incelenmemis + sonraki_belge + onceki_belge | no job: every Kontrol key is disabled (the binder's 'Önce Yükle sekmesinden…' text shows only when a command is clicked while enabled, which never happens) | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 17 | no | fixed (Q5, Q-09: every Kontrol key with no job says the no-job text; Enter and Space with a button focused stay with the button; test_main_window.py still asserts the keys are disabled, which they are) |
| M-35 | 3 | silent key | Şablonlar | Del, Ctrl+D, Ctrl+Shift+N, Alt+Up, Alt+Down | sablonlar.kutu_sil + kutu_cogalt + degisken_ekle + yukari + asagi | no variable, box or template: keys disabled, nothing said | status lines 'PROPOSED: Önce bir değişken ya da kutu seçin.', 'PROPOSED: Önce bir kutu seçin.', 'PROPOSED: Önce bir şablon seçin ya da oluşturun.', 'PROPOSED: Zaten ilk sırada.' / 'PROPOSED: Zaten son sırada.' | yes | none | 5 | no | fixed (Q5: 'Önce bir değişken ya da kutu seçin.', 'Önce bir kutu seçin.', 'Önce bir şablon seçin ya da oluşturun.', 'Zaten ilk sırada.', 'Zaten son sırada.', 'Önce bir değişken seçin.') |
| M-37 | 3 | silent key | Şablonlar | Ctrl+T | sablonlar.dene | no page: Ctrl+T disabled; 'Denemek için bir şablon ve açık bir iş gerekir.' is unreachable by key | key stays on and shows that existing text | no | none | 1 | no | fixed (Q5, Q-09: Ctrl+T stays greyed and says 'Denemek için bir şablon ve açık bir iş gerekir.') |
| M-38 | 3 | label drift | Şablonlar | Alt+Up, Alt+Down | sablonlar.yukari + sablonlar.asagi | label 'Değişkeni yukarı/aşağı taşı' but with a box chosen in a multi-box variable the BOX's try order moves | item names what moves: 'PROPOSED: Bölümü yukarı taşı' / 'PROPOSED: Bölümü aşağı taşı' when a section is chosen | yes | none | 2 | no | fixed (Q5: 'Bölümü yukarı taşı' / 'Bölümü aşağı taşı' while a section of a multi-box variable is chosen) |
| M-39 | 3 | wrong verb | Şablonlar | Space | sablonlar.el | Space = hold to pan on the canvas, but Space = show the page large on Kontrol and Değerler | keep and document as page-specific (hand tool convention); OWNER decides | no | none | 1 | yes | kept (Q5: hand-tool convention, documented as local and page-specific) |
| M-41 | 3 | silent key | Değerler | Return, Enter, Ctrl+Return, Ctrl+Enter, F2, V, Ctrl+A, Space | degerler.* (single keys) | no current value, no selection or no rows: keys disabled, nothing said | status lines 'PROPOSED: Önce bir değer seçin.', 'PROPOSED: Önce satırları seçin.', 'PROPOSED: Önce şablonu olan bir belge seçin.' | yes | none | 8 | no | fixed (Q5: 'Önce bir değer seçin.', 'Önce satırları seçin.', 'Önce şablonu olan bir belge seçin.', 'Seçilecek bir satır yok.'; no job: the no-job text) |
| M-42 | 3 | silent key | Değerler | N, Shift+N | degerler.sonraki_kontrol + degerler.onceki_kontrol | no value waiting: key disabled, so 'Kontrol bekleyen değer yok.' (and the toast) are unreachable by key | key stays on and shows that existing text | no | none | 2 | no | fixed (Q5, Q-09: N and Shift+N stay greyed and say 'Kontrol bekleyen değer yok.') |
| M-43 | 3 | label drift | Değerler | Esc | degerler.vazgec | label and tooltip say 'Vazgeç' / 'Değişikliği bırak' but Esc only closes the page view or trims a multi-row selection | label 'Seçimi kaldır' like Kontrol, or leave 'Vazgeç' and fix the tooltip; OWNER decides | no | none | 1 | yes | open (owner decision, Q-08): label stays 'Vazgeç'; its key still says a reason when greyed |
| M-05 | 4 | silent key | Şablonlar | Ctrl+F | app.bul | no template: focus moves to an empty list, nothing said | status line 'PROPOSED: Aranacak değişken yok.' | yes | none | 1 | no | fixed (Q5: 'Aranacak değişken yok.') |
| M-16 | 4 | silent key | Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber | Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z | app.geri_al + app.yinele | empty stack: key disabled, item greyed, nothing said | status line 'PROPOSED: Geri alınacak bir şey yok.' / 'PROPOSED: Yinelenecek bir şey yok.' | yes | none | 18 | no | fixed (Q5: 'Geri alınacak bir şey yok.' / 'Yinelenecek bir şey yok.') |
| M-19 | 4 | silent key | Şablonlar | Ctrl+Num++, Ctrl++, Ctrl+=, Ctrl+-, Ctrl+Num+-, Ctrl+0 | app.yakinlastir + app.uzaklastir + app.sigdir | no template or page: zoom keys disabled, nothing said | same text as above | yes | none | 6 | no | fixed (Q5: same text as M-18) |
| M-21 | 4 | silent key | Kontrol | F9 | app.yan_panel | before a job is open the Kontrol placeholder has no side panel: F9 disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 1 | no | fixed (Q5, Q-09: F9 on the Kontrol placeholder is greyed and says the no-job text; test_shell.py asserts the new tooltip, the key still does nothing) |
| M-23 | 4 | silent key | Dışa Aktar | F5 | app.yenile | empty or running: F5 disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' when empty (existing text) | no | none | 1 | no | fixed (Q5: empty case as before; while an export runs: 'Dışa aktarma sürerken yenilenemez.') |
| M-24 | 4 | silent key | Rehber | F1 | app.yardim | F1 on Rehber changes nothing visible | focus moves to the guide text | no | none | 1 | no | fixed (3E, test_key_effect_and_feedback / test_not_applicable / test_same_through_menu_or_palette[app.yardim[rehber]F1]) |
| M-26 | 4 | silent key | Yükle | Ctrl+Shift+O, F2 | yukle.yeniden_adlandir + yukle.gezginde_goster | no job: key disabled, nothing said | status line 'Önce Yükle sekmesinden bir iş açın (Ctrl+1).' (existing text) | no | none | 2 | no | fixed (Q5, Q-09: F2 and Ctrl+Shift+O with no job say the no-job text; test_yukle_a.py still asserts the command is disabled, which it is) |
| M-29 | 4 | label drift | Yükle, Değerler, Dışa Aktar | Ctrl+. | yukle.iptal / degerler.durdur / disa_aktar.durdur | same key, same verb (stop what is running) but three labels: 'İptal et', 'Okumayı durdur', 'Dışa aktarmayı durdur' | document as page-specific (the object differs); OWNER decides whether Yükle should read 'Okumayı durdur' | no | none | 3 | yes | kept (Q5: same verb, three objects; documented in shortcuts.md) |
| M-32 | 4 | silent key | Kontrol | K, M, Space | kontrol.kes + kontrol.birlestir + kontrol.onizle | no current page: key returns without a word | status line 'Önce bir sayfa seçin.' (existing text) | no | none | 3 | no | fixed (3E, test_not_applicable[kontrol.kes[kontrol]K], test_not_applicable[kontrol.birlestir[kontrol]M], test_not_applicable[kontrol.onizle[kontrol]Space]) |
| M-36 | 4 | silent key | Şablonlar | B, G | sablonlar.kutu_ciz + sablonlar.izgara | no template or page: B and G disabled, nothing said | status lines 'PROPOSED: Kutu çizmek için bir şablon ve bir örnek sayfa gerekir.' / 'PROPOSED: Izgara için bir şablon ve bir örnek sayfa gerekir.' | yes | none | 2 | no | fixed (Q5: the two 'Kutu çizmek / Izgara için bir şablon ve bir örnek sayfa gerekir.' texts) |
| M-44 | 4 | silent key | Dışa Aktar | Ctrl+Shift+O, Ctrl+P | disa_aktar.yazdir + disa_aktar.gezginde_goster | empty list or no folder: keys disabled, nothing said | status lines 'PROPOSED: Yazdırılacak bir dizin yok.' / 'PROPOSED: Gösterilecek bir klasör yok.' | yes | none | 2 | no | fixed (Q5: 'Gösterilecek bir klasör yok.' and 'Yazdırılacak dizin sayfası yok.') |
| M-40 | 5 | silent key | Şablonlar | Left, Up, Right, Down, Shift+Left, Shift+Up, Shift+Right, Shift+Down | sablonlar.kaydir + sablonlar.kaydir_1mm | arrows with no box chosen scroll the view or move the list; nothing says why the box did not move | no change needed: the status hint 'Kaydır: ok tuşları 0,25 mm' already shows when a box has focus (accept; OWNER?) | no | none | 8 | no | kept (Q5: the status hint already shows) |
| M-45 | 5 | silent key | Kontrol, Değerler, Rehber | Esc | kontrol.secimi_kaldir + degerler.vazgec + rehber.aramayi_temizle | Esc with nothing to dismiss does nothing | accept: a dismiss key stays quiet (OWNER? approve) | no | none | 3 | yes | kept (Q5: a dismiss key stays quiet) |

## Turkish texts of Q5 (the owner sees these)

The 31 proposed texts, as used in `src/evrakci/ui/refusals.py` (and the labels in `actions.py`).
Changes against the proposal: text 1 is shorter and names a tab, not a key; text 30 avoids "dizin"
alone; text 11 is also the item's label; texts 8 and 9 are not used (M-17).

1. Belgeye gitmek için Kontrol sekmesini açın (Ctrl+2).
2. Gidilecek bir belge yok.
3. Aranacak değişken yok.
4. Bu sekmede aranacak sonuç yok.
5. Rehber'de kaydedilecek bir şey yok.
6. Geri alınacak bir şey yok.
7. Yinelenecek bir şey yok.
8. (not used) Geri alındı: <adım>. Rehber says "Rehber'de geri alınacak bir şey yok."
9. (not used) Yinelendi: <adım>. Rehber says "Rehber'de yinelenecek bir şey yok."
10. Bu sekmede yakınlaştırılacak bir şey yok.
11. Varsayılan boyuta dön (Ctrl+0), and the item "Varsayılan boyut"
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
30. Yazdırılacak dizin sayfası yok.
31. Önce bir değişken seçin. (Şablonlar, Alt+Up and Alt+Down with no variable chosen)

Texts added in Q5 for states the proposal did not list (greyed with no word before):
Dışa aktarma sürüyor. / Dışa aktarılamıyor. (Ctrl+E fallbacks), Dışa aktarma sürerken yenilenemez.
(F5 on Dışa Aktar while it runs), Okuma sürerken geri alınamaz. (undo while Değerler reads),
Zayıf örnekler için bir şablon ve bir örnek sayfa gerekir. (N, Shift+N, Ctrl+L on Şablonlar),
Deneme sürüyor; bitince yeniden deneyin. (Ctrl+T while a try-all runs), Okumaları göstermek için
bir şablon ve bir örnek sayfa gerekir., Okunacak, şablonu olan bir belge yok., Okuma sürüyor.,
Önce değerleri okuyun. (Değerler read and review items), Seçilecek bir satır yok. (Ctrl+A with no
rows), Düzeltilmiş bir değer yok. (R), Kopyalanacak bir ad listesi yok.,
Henüz yazılmış bir dizin dosyası yok., Karşılaştırılacak ad yok. (Dışa Aktar items),
Rehber'de geri alınacak bir şey yok. / Rehber'de yinelenecek bir şey yok.
Existing texts reused: "Önce Yükle sekmesinden bir iş açın (Ctrl+1).", "Sonuç yok.",
"Kaydedilecek bir şablon yok. Önce bir şablon oluşturun.", "Denemek için bir şablon ve açık bir iş
gerekir.", "Kontrol bekleyen değer yok.", "Bu değer elle yazıldı; okunmuş bir değer yok.",
"Bir iş sürüyor; bitince açın.", "Dışa aktarılamıyor: <neden>".

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
