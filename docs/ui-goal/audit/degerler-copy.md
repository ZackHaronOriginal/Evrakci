# Değerler audit: copy

Phase 4, Görev A, screen Değerler. Every Turkish string a user can see or hear on the screen, collected from the code (an AST pass over `degerler.py`, `degerler_model.py`,
`degerler_table.py`, `degerler_side.py`, `degerler_parts.py` and the Değerler entries of `actions.py` and `main_window.py`; about 230 string constants and f-string parts, grouped into the rows below)
and checked against the vocabulary Kontrol / Emin / Orta / Kontrol / Okunamadı / İncelendi / İncelenmedi. On this screen all of them occur: Emin, Orta, Kontrol and Okunamadı as level words,
İncelendi and İncelenmedi as the review state. This file records findings only; proposed rewrites go to `degerler-proposals.md`, which the fix task writes after the owner answers.

Verdicts: ok / unclear / inconsistent / no next step. "Next step" is judged for messages that report a refusal or an error. Findings reference `degerler-findings.md`. Turkish was read by the
auditor; a native-speaker check by the owner is still needed for tone (not done). Pure style strings (font sizes, object names, icon names) and the Windows-only surfaces are left out. Strings that
come from the core (`pipeline/`) are listed but not edited (D13).

Rows: 64. ok 44, unclear 8, inconsistent 10, no next step 2.

| ID | Where | String | Verdict | Note / finding |
|---|---|---|---|---|
| C-01 | `ui/actions.py (L301-L303)` | Onayla ve sonrakine geç (menu, button, Enter); tip "Öneriyi kabul et, incelendi işaretle ve geç" | unclear | Three names for one action: Onayla (button, menu), Öneriyi kabul et (tip, undo step), Değeri onayla (undo text) (F-degerler-39) |
| C-02 | `ui/actions.py (L304)` | Seçilenleri onayla (Ctrl+Enter) | ok | Toast names the count: "N değer onaylandı" |
| C-03 | `ui/actions.py (L306)` | Elle yaz (F2) | ok | Same on the button and the menu |
| C-04 | `ui/actions.py (L308)`, `degerler_side.py (L565)` | Yeni varyant çiz (menu, context menu, palette) / Yeni kutu çiz (inspector button, V) | inconsistent | One command, two names; Şablonlar says Bölüm / varyant / kutu (F-degerler-15) |
| C-05 | `ui/actions.py (L310)` | Vazgeç (Esc); tip "Değişikliği bırak" | ok | The tip is longer than the label and says what it does |
| C-06 | `ui/actions.py (L312)` | Tümünü seç (Ctrl+A) | ok |  |
| C-07 | `ui/actions.py (L314)` | Tüm sayfayı göster (Space) / Sayfanın tamamı (Boşluk) (inspector tooltip) | inconsistent | Space is spelled "Space" in the menu and "Boşluk" in the tooltip; the verb is "göster" in one and none in the other (F-degerler-39) |
| C-08 | `ui/actions.py (L316, L318)` | Sonraki kontrol (N), Önceki kontrol (Shift+N); keywords "şüpheli uyarı" | ok | The retired word "şüpheli" survives as a hidden search keyword in the palette (F-degerler-30) |
| C-09 | `ui/actions.py (L320)` | Tümünü incele; tip / accessible name "Emin olanlar dahil her değeri sırayla göster" | unclear | The icon-only bar button is named by the description, not by the command name (F-degerler-31) |
| C-10 | `ui/actions.py (L322)` | Örnek kontrol; tip "Dışa aktarmadan önce rastgele 20 emin değere bak" | unclear | "kontrol" here is a noun (a check), next to the status word Kontrol; "20" is a constant (F-degerler-31) |
| C-11 | `ui/actions.py (L324)` | Değerleri oku; tip "Şablonu olan bütün belgeleri yeniden oku" | unclear | The tip says "yeniden" (again) although the first read is also this command; the accessible name differs from the visible label (F-degerler-31) |
| C-12 | `ui/actions.py (L326)` | Yalnızca eksikleri oku | ok | Tooltip equals the label (no key) |
| C-13 | `ui/actions.py (L328)`, `degerler.py (L186-L187)` | Okumayı durdur (Ctrl+.) | ok | Same on the band button, the menu and the tooltip |
| C-14 | `ui/degerler.py (L192)` | Mesajı kapat | ok |  |
| C-15 | `ui/degerler.py (L183)` | Okuma ilerlemesi (accessible name) | ok |  |
| C-16 | `ui/degerler.py (L1460)` | Okunuyor: 3 / 12 belge | ok |  |
| C-17 | `ui/degerler.py (L1461-L1465)` | elle yazdıklarınız korunur / bir dakikadan az kaldı, ... / yaklaşık N dk kaldı, ... | ok | Good: tells what is safe. Starts lower case after the label |
| C-18 | `ui/degerler.py (L1494)` | N belge okundu. | inconsistent | N counts documents whose read failed too (F-degerler-05); and "0 belge okundu." after an undo (F-degerler-08) |
| C-19 | `ui/degerler.py (L1502)` | Okuma durduruldu: N belge okundu ve kaydedildi, kalanlar okunmadı. | ok | Says what was kept. "okunmadı" is the verb here, one letter from the status word Okunamadı (F-degerler-14) |
| C-20 | `ui/degerler.py (L1498)` | Okunamadı: <message> | no next step | The message is the raw text of an exception for an unexpected failure; no advice (F-degerler-06) |
| C-21 | `ui/degerler.py (L1427)` | Şablon bulunamadı: <8-character key> | no next step | Shows the internal key, not the template name, no advice (F-degerler-40) |
| C-22 | `pipeline/ocr/tesseract.py (read only)` | Okunamadı: Tesseract programı bulunamadı: ... (refusal band) | ok | Names the missing program; the text comes from the core (not edited, D13); whether it says how to install it was not read |
| C-23 | `ui/degerler.py (L476-L478)` | Henüz açık iş yok / Değerler, açık bir işin şablonlu belgelerinden okunur. / Yükle'ye git | ok | Next step is a button. The job switch says "İş açılmadı" for the same state (F-yukle C-75 class) |
| C-24 | `ui/degerler.py (L521-L524)` | Şablonlu belge yok / Kontrol'de belgelere şablon uygulayınca değerler burada okunur. / Kontrol'e git / Şablonlar'a git | ok | Two next steps |
| C-25 | `ui/degerler.py (L529-L534)` | Değerler henüz okunmadı / Okuyunca sicil no, firma adi ve tutar burada listelenir. / N belgeyi oku / Şablonlar'a git / Elle yazdıklarınız yeniden okumada korunur. | ok | Clear; the sentence lists three variable names in lower case |
| C-26 | `ui/degerler.py (L536-L538)` | Aramayla eşleşen değer yok / “x” hiçbir değerde geçmiyor. Başka bir sözcük deneyin. / Aramayı temizle | ok | Repeats the whole query, also 5,000 characters (E-113) |
| C-27 | `ui/degerler.py (L540-L544)` | Kontrol bekleyen değer yok / İncelenmemiş değer yok / Bu şablonun bütün değerleri emin okundu ya da incelendi. / Tümünü göster | unclear | "emin okundu" mixes the status word Emin with a verb; "Kontrol bekleyen" is a third phrasing of the state (F-degerler-38) |
| C-28 | `ui/degerler.py (L541)` | Değer yok | unclear | Fallback title for the Tümü view when nothing matches without a query; not reachable in the runs |
| C-29 | `ui/degerler.py (L224-L232, L587)` | Ara / Değerlerde ara / Sicil No ara / Firma Adi ara (placeholder, one variable name) / Şablon / Şablon yok | unclear | The placeholder names one column, the search covers every value and the document number (F-degerler-18) |
| C-30 | `ui/degerler.py (L571)` | Şablon bulunamadı (picker item) | ok | Shorter than the row error of the same words (F-degerler-40) |
| C-31 | `ui/degerler_model.py (L47)` | Kontrol gerekenler / İncelenmemiş / Tümü / Örnek (view switch) | ok | Matches the owner's vocabulary; Kontrol's own view says "gerekiyor" (F-kontrol-18) |
| C-32 | `ui/degerler_parts.py (L48)` | Kontrol gerekenler: 206 değer (tooltip and accessible name) | ok | Unit "değer" is clear |
| C-33 | `ui/degerler_model.py (L37-L41)` | Emin / Orta / Kontrol / Okunamadı / Okunmadı (level words) | inconsistent | Okunamadı (could not be read) and Okunmadı (not read yet) are two states one letter apart; the owner's list has only the first (F-degerler-14) |
| C-34 | `ui/degerler_table.py (L169, L178, L235)` | İnceleme (column), İncelendi, İncelenmedi | ok | Matches the vocabulary |
| C-35 | `ui/degerler_table.py (L84-L86)` | Belge / Sayfa / Değişken / Okunan değer / Güven (column titles) | ok | "Güven" is the owner's term for the confidence; the level words appear only in this column (F-degerler-10) |
| C-36 | `ui/degerler_table.py (L216)` | Öneri: <text> (cell tooltip) | ok |  |
| C-37 | `ui/degerler_table.py (L227, L230)` | <name>: okunmadı / <n> karakter belirsiz (spoken text) | ok | Spoken form carries the level word, the percent and "İncelendi" |
| C-38 | `ui/degerler_table.py (L586, degerler_side.py L490)` | boş (an empty Okunamadı cell) | ok | Clear; grey |
| C-39 | `ui/degerler_table.py (L610)` | <variable> düzenle (editor accessible name), "Değer" fallback | ok |  |
| C-40 | `ui/degerler.py (L887)` | Enter onayla, sonraki kontrol / Esc vazgeç (key hint chip) | ok | Short; in Tümünü incele the first part becomes "onayla, sonraki değer" |
| C-41 | `ui/degerler.py (L1018-L1019)` | Değer seçilmedi / Okunan değerler burada kaynağıyla görünür. / Tablodan bir değer seçince sayfadaki yeri, okunan değer ve öneri burada görünür. | inconsistent | Two sentences for one state, nearly the same, stacked in the same panel |
| C-42 | `ui/degerler.py (L1027, L1032, L1035)` | Belge 2, sayfa 5 / , örnek 3 / 20 / Kaynak kesiti: Sicil No, belge 2, sayfa 5 | ok | Page numbers are positions in the job (V-72) |
| C-43 | `ui/degerler_side.py (L466-L468)` | Okunan / Öneri / Okunan değer (card) | ok |  |
| C-44 | `ui/degerler.py (L1038-L1051)` | okunmadı / boş / İncelendi / Örnek 4 / 5 / Sayfadakiyle aynıysa onaylayın, değilse elle yazın. Örnekte bulunan bir hata, aynı değişkenin bütün değerlerini Kontrol'e alır. | ok | The last sentence is long (23 words) but names the consequence |
| C-45 | `ui/degerler_model.py (L175)` | Bu değer henüz okunmadı. Değerleri oku ile okunur. | inconsistent | Also shown for a document whose read failed, followed by the raw error text; the reason is wrong then (F-degerler-05). "Değerleri oku ile okunur" is stiff |
| C-46 | `ui/degerler_model.py (L177)` | Kutuda okunacak yazı bulunamadı: değeri elle yazın ya da yeni bir kutu çizin. | ok | Next step is clear |
| C-47 | `ui/degerler_model.py (L179-L187)` | <x> yerine <y> / Bölüm 1 ile okundu: Z yerine 2. / <x> ile okundu; emin olunamadı. / İncelendi: elle yazıldı ya da onaylandı; yeniden okumada korunur. | inconsistent | "Bölüm 1" and "Varyant 2" name what Şablonlar calls a box or variant (F-degerler-15); "Z yerine 2" reads as an instruction |
| C-48 | `ui/degerler_model.py (L74)` | Bölüm 1 / Varyant N | inconsistent | Same (F-degerler-15) |
| C-49 | `ui/degerler.py (L978, L999, L1002)` | Kontrol bekleyen değer yok. / Kontrol gereken değer kalmadı; N değer incelenmedi. Enter sıradakini onaylar. / Bu görünümdeki bütün değerler incelendi. | unclear | The middle one is the longest toast and is cut at 1366 wide (F-degerler-12); three phrasings of the state (F-degerler-38) |
| C-50 | `ui/degerler.py (L790, L794)` | Sayfa N şablonu olan bir belgede değil. / Belge N bu görünümde yok. | ok | Says why; the second does not say which view would show it |
| C-51 | `ui/degerler.py (L846)` | Örnek için emin okunmuş değer yok. | ok | Short |
| C-52 | `ui/degerler.py (L1159)` | Seçili satırlarda onaylanacak değer yok. | ok |  |
| C-53 | `ui/degerler.py (L1167-L1171)` | N değeri onayla (undo step) / N değer onaylandı / ; okunamayan M değer atlandı | ok | "atlandı" names what was skipped |
| C-54 | `ui/degerler.py (L1243-L1245)` | Örnekte hata: <değişken> / Örnekte hata: N <değişken> değeri Kontrol'e alındı | ok | Variable names are lower-cased into the sentence ("20 açıklama notu değeri") |
| C-55 | `ui/degerler.py (L1296)` | Örnek kontrol bitti: N değer, E hata. | ok |  |
| C-56 | `ui/degerler.py (L1362-L1385)` | Belge 2 / 3; N değer kontrol bekliyor; N okunamadı; x / y incelendi; N belgede şablon var, değer okunmadı; Örnek kontrol: x / N incelendi; N hata | ok | The unread line says "değer okunmadı" also after a read in which every document failed (F-degerler-05) |
| C-57 | `ui/degerler_side.py (L403-L405)` | Uzaklaştır (Ctrl+-) / Yakınlaştır (Ctrl++) / Sayfanın tamamı (Boşluk) | inconsistent | Key written "Boşluk" here and "Space" in the menu (F-degerler-39) |
| C-58 | `ui/degerler_side.py (L578-L580)` | Onayla ve sonrakine geç (Enter) / Elle yaz (F2) / Yeni kutu çiz (V) | ok | Keys in the tooltips |
| C-59 | `ui/degerler_side.py (L233)` | <ad> değerine git (crop box tooltip) | ok |  |
| C-60 | `ui/degerler.py (L351)` | Değer komutları (context menu accessible name) | ok |  |
| C-61 | `ui/degerler.py (L333, degerler_side.py L126)` | Kaynak kesiti (zoom label), Kaynak (panel name) | ok |  |
| C-62 | `ui/main_window.py (L1441, L1455-L1462)` | Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın. / Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır. / Durduruluyor… Pencere iş durunca kapanır. | inconsistent | The first is shown for Ctrl+O, Ctrl+E and Ctrl+S too, where "başka bir iş açın" is the wrong advice (F-yukle-35 class); the dialog buttons are Qt's English Yes/No (F-yukle-39 class) |
| C-63 | `ui/kontrol_dialogs.py (shared)` | Belge / Sayfa go-to dialog | ok | Shared with Kontrol, audited there |
| C-64 | `ui/feedback.py` | Geri al (toast button) | ok |  |

Vocabulary check in one line each:
- Kontrol: used as the level word (Güven column, inspector, status bar) and as the view name "Kontrol gerekenler"; also as the noun in "Örnek kontrol" (a check) and the verb-like "Sonraki kontrol". Consistent with the owner's list; the noun use sits next to the status word (F-degerler-31).
- Emin / Orta: Emin appears as the level word and inside sentences ("emin okundu", "emin değer"); Orta only in the Güven column and the inspector.
- Okunamadı: level word, status item ("N okunamadı") and the error band prefix "Okunamadı: ..."; Okunmadı (not read yet) is a second, near-identical word (F-degerler-14).
- İncelendi / İncelenmedi: review column, inspector note, status item ("x / y incelendi"), view name İncelenmemiş (a third form of the same stem; the owner's list has İncelenmedi).
- "Şüpheli" appears nowhere on screen; it is a hidden palette keyword (F-degerler-30).
