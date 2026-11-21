# Şablonlar audit: copy

Phase 4, Görev A, screen Şablonlar. Every Turkish string on the screen, checked for clarity, correctness, and consistency with the vocabulary Kontrol / Emin / Orta / Kontrol / Okunamadı / İncelendi / İncelenmedi, and for errors that say what to do next. On this screen Emin, Orta, Kontrol and Okunamadı occur as read levels (İncelendi and İncelenmedi do not occur: the tab reads, it does not review). This file records findings only; proposed rewrites go to `sablonlar-proposals.md`, which the fix task writes after the owner answers.

Verdicts: ok / unclear / inconsistent / no next step. "Next step" is judged for messages that report a refusal or an error. Findings reference `sablonlar-findings.md`. Turkish was read by the auditor; a native-speaker check by the owner is still needed for tone (not done). Pure style strings (object names, icon names) and the Windows-only surfaces are left out. Strings that come from the core (`pipeline/`) are listed but not edited (D13). Strings are grouped; a row can hold several strings of one place.

Rows: 38. ok 26, unclear 5, inconsistent 5, no next step 2.

| ID | Where | String | Verdict | Note / finding |
|---|---|---|---|---|
| C-01 | `sablon.py:_ask_text`, `new_template` | Yeni şablon / Şablonun adı / Oluştur / Vazgeç | ok | Clear; the blank name does nothing and says nothing (O-17, F-sablonlar-34 family) |
| C-02 | `sablon.py:ask_variable` | Değişken ekle / Değişkenin adı (örn. Firma_Adi) / Ekle / Vazgeç | unclear | The example has an underscore; the README example and Değerler column titles use spaces (O-14), so the example teaches a convention the product does not need |
| C-03 | `ui/actions.py:274-297`, `sablon_nav.py`, `sablon_inspector.py`, `sablon_sync.py:85-89` | Kutu / Bölüm / Varyant / Kutuyu çoğalt / "Bölüm 2, sayfa 1" / "Kutu 2 / 3" / "Bölümler yukarıdan aşağı denenir" | inconsistent | One thing, four words (F-sablonlar-31); Değerler adds "Yeni varyant çiz" (F-degerler-15) |
| C-04 | `actions.py:274` | Kutu çiz (B), tooltip "Kutu çiz (B)" | ok | Short, verb first |
| C-05 | `actions.py:276` | Izgaraya oturt (G) | unclear | No grid is drawn (O-05): "Izgara" suggests lines; the tool snaps to whole millimetres. Owner's word |
| C-06 | `actions.py:278`, `sablon_live.py:147` | Bütün örneklerde dene / "Örnekler okunuyor n / N, Esc durdurur" | inconsistent | Three verbs for one run: dene, oku, test (the keyword list has "oku test"); the status says Esc stops it, the button has no stop |
| C-07 | `actions.py:280`, `sablon_sync.py:121-129` | Kutuyu sil (geri alınabilir) / Değişkeni sil (geri alınabilir) | ok | The name follows what is chosen; says it can be undone |
| C-08 | `actions.py:282` | Kutuyu çoğalt (Ctrl+D) | ok | Mnemonic sits mid-word ("çoğa&lt"); harmless |
| C-09 | `actions.py:284` | Değişken ekle (Ctrl+Shift+N) | ok | Same on the button, the menu, the dialog title and the + tip |
| C-10 | `actions.py:286-289` | Değişkeni yukarı taşı / Değişkeni aşağı taşı | inconsistent | The same command moves a section when a section is chosen (try order), but only the delete item changes its name (F-sablonlar-31) |
| C-11 | `actions.py:290` | Okumaları sayfada göster | ok | Icon only on the bar; the tip carries the words |
| C-12 | `main_window.py:136` | Ayrıntı panelini gizle (F9) / göster | ok | Switches with the state |
| C-13 | `sablon_sync.py:37-40` | Henüz şablon yok / Örnek bir sayfada her bilginin çevresine kutu çizin. / Yeni şablon oluştur / Rehber'i aç | ok | Says what to do next; the note names the open job or tells to open one |
| C-14 | `sablon_sync.py:41-45` | Örnek sayfa yok / Kutuları çizmek için bir iş açın; örnek sayfalar o işten gelir. / Yükle'ye git | unclear | Right for no job; wrong when a job is open but its file is missing (F-sablonlar-18) |
| C-15 | `sablon_sync.py:68-71` | Değişkenler: Değişken seçilmedi / Soldaki listeden bir değişken seçin. / Değişken yok / Eklemek için Ctrl+Shift+N tuşlarına basın. | ok | Next step given (layout fault: F-sablonlar-03) |
| C-16 | `sablon_sync.py:77-81` | Henüz kutu yok / Sayfada Kutu çiz (B) ile bu değişkenin kutusunu çizin. / Bir bölüm seçin ya da sayfada bir kutuya tıklayın. | ok | Next step given; names the key |
| C-17 | `sablon_inspector.py` | Kutu / Ad / Zorunlu / Kutunun sayfası / X, Y, genişlik, yükseklik (mm) / Okunan, örnek N / Değer / Güven / Not / Dosya adı / .pdf / Şablonu kaydet | ok | "Kutu" is the card title also for a variable (state "variable"): minor |
| C-18 | `sablon_read.py:25-31` | Emin / Orta / Kontrol / Okunamadı / Okunmadı | ok | Emin, Orta, Kontrol and Okunamadı are the vocabulary; Okunmadı is the fifth word (next row) |
| C-19 | `sablon_read.py:30` | Okunmadı (clock icon, state orta) | inconsistent | One letter from Okunamadı, a different meaning (not read yet vs could not read); not in the vocabulary list (F-sablonlar-32). In the inspector it also shares the colour of Orta |
| C-20 | `sablon_read.py:67-79` | Emin olunamadı; Değerler sekmesinde kontrol edilir. / Önceki bölüm emin okuduğu için denenmedi. / Kutu çizilince okunur. | ok | Each says why and what happens next |
| C-21 | `pipeline/templates/read.py:22-23` | sayfa yok / kutu sayfa dışında | no next step | Lowercase fragments from the core, no sentence, no action (F-sablonlar-33; core text, D13) |
| C-22 | `sablon.py:744-747, 845` | Önce soldan bir değişken seçin. / Çizmeden önce soldan bir değişken seçin. / Önce Yükle sekmesinden bir iş açın; örnek sayfalar oradan gelir. | ok | Each gives the first step |
| C-23 | `sablon.py:571`, `sablon_live.py:116` | Önce bir bölüm seçin. / Denemek için bir şablon ve açık bir iş gerekir. | ok | Unreachable through the window (O-23): not shown |
| C-24 | `sablon.py:974` | Şablon kaydedilemedi. Diskte yer olduğundan emin olup Şablonu kaydet'e basın. | ok | Cause and next step; shown in the left column and the status bar, no toast (O-22) |
| C-25 | `sablon.py:991` | Kaydedilecek bir şablon yok. Önce bir şablon oluşturun. | ok | Next step given |
| C-26 | `sablon.py:702` | Sayfa gösterilemedi: {hata}. Yükle sekmesinden işi kontrol edin. | unclear | Has a next step but prints the raw error (a path) inside the sentence |
| C-27 | `sablon_live.py:73, 182` | Okuma yapılamadı: {neden} / Örnekler okunamadı: {neden} | no next step | The reason is raw engine or file text (a path in the demo: S:E4b); no action named (F-sablonlar-18) |
| C-28 | `sablon.py:815, 826, 996`, `sablon_live.py:176` | Şablon kaydedildi. / “X” değişkeni silindi (N kutu). / “X” değişkeninin N. bölümü silindi. / N örnekte denendi. Kontrol gerektiren okuma yok. / N okuma kontrol bekliyor. | ok | Name the thing and the count; Geri al on the two deletions |
| C-29 | `sablon_sync.py:143-186` | Örnek n / N / Kutu x … mm / Kaydır: ok tuşları 0,25 mm, Shift 1 mm / İmleç x … mm / N okuma kontrol bekliyor | ok | Turkish decimal comma, units given |
| C-30 | `sablon_sync.py:159-169` | Şablon seçilmedi / kaydedilmedi / kaydedilemedi / kaydedildi HH:MM | inconsistent | "kaydedilmedi" (not yet) and "kaydedilemedi" (failed) differ by two letters and the first is normal while the second is an error (F-sablonlar-32); the icon differs (dashed circle, red x) |
| C-31 | core `model.py:54-183` | Kalıpta bilinmeyen değişken: X / Dosya adı kalıbında eşleşmeyen süslü parantez: … / Kalıpta boş değişken adı var: {} | ok | Say what is wrong; no example of a valid pattern, the placeholder does that |
| C-32 | core `model.py:36-45, 129` | Bu adla bir değişken zaten var: X / Değişken adında { veya } olamaz: X / Değişken adı boş olamaz. | ok | Clear; shown in the left column, not at the field (the pattern error is at its field) |
| C-33 | core `model.py:45` | Değişken adında görünmeyen veya özel karakter var: 'a\u200bb' | unclear | Python repr (quotes, \u escapes) shown to the user (F-sablonlar-33; core text, D13) |
| C-34 | `sablon.py:180-186`, `sablon_inspector.py`, `sablon_canvas.py:277` | Kutuların çizildiği örnek belge / Örnek belgenin sayfası / Kutunun sayfası (son: son sayfa) / Dışa aktarılan her belgenin adı. Değişkenleri {Ad} ile yazın. / Kutu çizmek için Kutu çiz (B) açıkken sayfada sürükleyin. | ok | Short and useful |
| C-35 | `sablon_canvas.py:_update_a11y` | Kutu 1: Ad, bölüm 1. x 20,0 y 30,0 milimetre, genişlik 70,0, yükseklik 12,0. Ok tuşları 0,25 mm, Shift ile 1 mm kaydırır; Ctrl ile oklar boyutu değiştirir. | ok | Spoken description names the box, the place and the keys |
| C-36 | `sablon.py:622, 646` | Örnek N, sayfa P / Örnek N, sayfa P · k kontrol / 1 / N | ok | "kontrol" here is a count of reads needing a check, with the warning icon |
| C-37 | `sablon_nav.py:add_template` | N değişken / kaydedilmedi / kutu yok / N bölüm / Sayfa p / son sayfa | ok | Short; "son sayfa" and the spin's "son" agree |
| C-38 | `sablon_nav.py:406-415`, `sablon.py:510` | * zorunlu. Bölümler yukarıdan aşağı denenir; ilk emin okuma kazanır. / Şablonlar bu bilgisayarda saklanır ve her işte kullanılabilir… / Bu şablonda henüz değişken yok. Eklemek için + düğmesine ya da Ctrl+Shift+N tuşlarına basın. | ok | The first explains the try order in a line; "Bölümler" see the vocabulary row |
