# Turkish terms check for the four specs (Görev T)

Date 2026-11-20. Only this file was written. Strings come from the "New Turkish text" tables of kontrol-filters.md (A), quick-wins.md (B), qr-saved-filters.md (C), disa-aktar.md (D) as they stood during this run (Görev R may still edit them).

## Sources actually opened (term seen in the page or file)

| Tag | What was opened | Link |
|---|---|---|
| LO-vcl, LO-sc, LO-svx, LO-sfx2, LO-cui, LO-sw | LibreOffice Turkish `messages.po` files (read, searched by English msgid) | https://github.com/LibreOffice/translations/blob/master/source/tr/vcl/messages.po (same path with `sc`, `svx`, `sfx2`, `cui`, `sw`) |
| PAP | Paperless-ngx Turkish locale file | https://github.com/paperless-ngx/paperless-ngx/blob/dev/src-ui/src/locale/messages.tr_TR.xlf |
| PDFA | PDF Arranger Turkish .po | https://github.com/pdfarranger/pdfarranger/blob/main/po/tr.po |
| EVI | GNOME Evince Turkish .po | https://gitlab.gnome.org/GNOME/evince/-/blob/main/po/tr.po |
| GIMP | GIMP Turkish .po | https://gitlab.gnome.org/GNOME/gimp/-/blob/master/po/tr.po |
| MS-prev | Microsoft Excel Turkish help, "Yazdırmadan önce çalışma sayfalarını önizleme" (fetched) | https://support.microsoft.com/tr-tr/Excel/preview-worksheet-pages-before-you-print |
| MS-sel | Microsoft Excel Turkish help, "Çalışma sayfalarını seçme" (fetched) | https://support.microsoft.com/tr-tr/Excel/select-worksheets |
| ABBYY | ABBYY FineReader PDF 16 Turkish user guide (PDF, text searched) | https://help.abbyy.com/assets/tr-tr/finereader/16/Users_Guide.pdf |

Not usable: Adobe Turkish help (HTTP 403), NAPS2 and PDFsam locale files (path not found), Microsoft Terminology portal and e-Devlet/UYAP (not opened). A web search result list alone is not counted as "opened". Anything without a tag below is **unverified**.

Reading rules: "ok" = keep. "flag" = a source shows a different standard for a fixed or existing word; do not change, owner or reviewer decides. "change" = recommended edit to a new draft string.

## Findings that matter most

1. **"Seç…" alone is too thin for "Select by…"**. GIMP has "Seçim ölçütü" and "Renge Göre Seç". Recommend menu text "Ölçüte göre seç…" (button "Seç" stays, LO-sw "Seç").
2. **"kalıp (* ve ?)" -> "joker karakterli (* ve ?)"**. LO-sc uses "Joker Karakterleri" for wildcards; "kalıp" is not seen.
3. **"Seçimin içinde ara" -> "Seçimle kesiştir"**. GIMP: "Seçimle Kesiştir". The draft sounds like a text search.
4. **"Atılmış boş sayfa" -> "Silinen boş sayfa"**. ABBYY: "Silinen tüm boş sayfaların görüntülerini". "Atılmış" is not seen anywhere.
5. **flag: "filtre"** (fixed). LO-sc and GIMP use "Süzgeç" ("Standart Süzgeç"); Paperless uses "Filtre". Two usages exist; keep "filtre" (more common in plain Turkish and in Paperless).
6. **flag: "Kayıtlı filtreler"**. PAP says "Kaydedilen/kaydedilmiş görünümler", LO-cui "Kaydedilmiş Dosya". Short "Kayıtlı" is natural but unverified; keep, reviewer may prefer "Kaydedilmiş".

## A: kontrol-filters.md

| Draft string | Concept | Sector terms found (source) | Recommendation | Reason |
|---|---|---|---|---|
| Seç… | Select by… | "Seçim ölçütü", "Renge Göre Seç" (GIMP) | change: Ölçüte göre seç… | Names the idea; bare "Seç…" in a menu is vague |
| Sayfaları seç | Select pages | "Sayfa seç" (EVI), "Tümünü Seç" (EVI, GIMP) | ok | Same verb and order |
| Ölçüt | Criterion | "Seçim ölçütü" (GIMP) | ok | Matches |
| Seçimi değiştir | Replace selection | "Yerine Koy" (GIMP Replace) | ok | Clear in context; GIMP word is weaker |
| Seçime ekle | Add to selection | "seçmek istediğiniz diğer sayfalar" (MS-sel); no exact UI string | ok (unverified exact) | Plain and short |
| Seçimin içinde ara | Keep only matches inside selection | "Seçimle Kesiştir" (GIMP) | change: Seçimle kesiştir | Exact standard for the intersect mode |
| Seç | Select button | "Seç" (LO-sw, LO-svx) | ok | Matches |
| Hiç yok | None | "Hiçbirini Seçme" (GIMP, for Select None) | ok | Different use; "Hiç yok" is fine for a count |
| {n} sayfa seçildi. / Eşleşen sayfa yok. | status lines | "seçili sayfalar" (MS-sel) | ok | Consistent |
| Bu belgeyi &seç, Bu belge | select this document | "Seç" (LO) | ok | Fixed word "belge" |
| Tek sayfalar / Çift sayfalar | Odd / even pages | "Tek Sayfalar", "Çift Sayfalar" (LO-vcl); "Tek sayfalar veya ..." (ABBYY) | ok | Exact match |
| Her belgenin 1., 3., 5. ... sayfaları (and 2., 4., 6.) | hints | none | ok (unverified) | Plain Turkish |
| Sayfayı seçime ekle / çıkar | Ctrl+Space toggle | "seçimini kaldırmak" (MS-sel) | ok | Close enough |
| Seçimi bozmadan git | move without changing selection | none | ok (unverified) | Plain |
| Bu belgede seçilecek sayfa yok. | status | none | ok (unverified) | Plain |
| Boş sayfalar | Blank pages | "Boş Sayfaları Sil" (ABBYY), "boş sayfa" (LO-sw) | ok | Matches |
| En çok mürekkep oranı; Bu orandan az mürekkepli sayfalar boş sayılır. | ink share threshold | none ("mürekkep" not seen as a scanner term) | ok (unverified) | No sector wording to compare; consider "doluluk oranı" if a reader finds "mürekkep" odd |
| {n} sayfa boş; en boş {a} %, en dolu {b} % | live counts | none | ok (unverified) | Plain |
| {n} boş sayfa seçildi. Silmek için Del. | status | "Seçili sayfaları sil" (ABBYY) | ok | Same verb |
| Farklı boyut veya yön; Boyut; Yön | different size or orientation | "Sayfa boyutu", "sayfa boyutunu ve yönünü" (ABBYY); LO-svx uses "Yönelim" | ok (flag: LO says Yönelim) | ABBYY uses "yön" like the draft |
| Karşılaştır: Bütün iş / Her belge | Compare with | "Karşılaştır:" (LO-sc) | ok | Matches |
| Farklı boyut; Yatay; Dikey | marks | "Yatay", "Dikey" (LO-vcl, PDFA, LO-svx) | ok | Exact match |
| {n} sayfa farklı görünüyor; Farklı görünenleri işaretle; Sonraki/Önceki farklı sayfa; Farklı sayfa yok. | live count, menu | "Sonraki sayfa" (LO-vcl, MS-prev), "Önceki Sayfa" (MS-prev) | ok | Navigation words match |
| Boyutu bilinmiyor | Size unknown | "Bilinmeyen" (LO-svx, LO-sfx2) | ok | Same root |
| Sayfa boyutları okunuyor | status | none | ok (unverified) | Plain |
| {n} değer; {n} belge; Sayfalar; Değerin sayfası; Belgenin bütün sayfaları; {d} belge, {p} sayfa; {d} belge seçildi: Kontrol {a}, Okunamadı {b} | reason counts | none beyond fixed vocabulary | ok (unverified) | Uses fixed words |
| &Filtreyi kaldır; Şablonu &kaldır; Boş sayfayı geri &getir | remove filter / template / restore blank | "Filtreleri sıfırla", "Tümünü kaldır" (PAP); "Şablon" (LO-sfx2) | ok (flag: LO says süzgeç) | "kaldır" in PAP; fixed "filtre", "şablon" |
| Filtre kaldırıldı, {n} sayfa.; Şablon kaldırıldı, {n} sayfa.; Boş sayfa geri getirildi.; Bu sayfalarda filtre yok.; Bu sayfalarda şablon yok.; Filtre yok | toasts, status | none | ok (unverified) | Plain |
| Atılmış boş sayfa yok. | No dropped blank page | "Silinen ... boş sayfalar" (ABBYY) | change: Silinen boş sayfa yok. | "Atılmış" not seen |
| Undo step names (Filtreyi kaldır, Şablonu kaldır, Boş sayfayı geri getir) | undo | same as above | ok | Same as menu |

## B: quick-wins.md

| Draft string | Concept | Sector terms found (source) | Recommendation | Reason |
|---|---|---|---|---|
| Bu değere bakın: okuma emin değil. | look at this value; reading not sure | none | ok (unverified) | "Emin" is fixed |
| Tüm okumalar | All readings | none | ok (unverified) | Plain |
| +{n} daha | n more | none (MS "diğer" not opened) | ok (unverified) | "+{n} diğer" is also common; low stakes |
| Kontrol'de aç | Open in Kontrol | none | ok | Tab name fixed |
| Bu belgenin şablonu yok; Değerler'de görünmez. | no template | "Şablon" (LO-sfx2) | ok | Fixed word |
| Belge {n} seçildi. | document selected | "seçili" (MS-sel) | ok | Plain |
| Zorunlu değer boş: ...; Zorunlu değer boş bırakılamaz; Kontrol'e alındı. | required value empty | LO-sc "zorunlu" (for mandatory argument) | ok | Same word |
| Okunana dön | Back to what was read | none | ok (unverified) | Plain; short for a menu |
| Okunana dönüldü: {değişken}. Kontrol'e alındı. | revert status | none | ok (unverified) | Plain |
| Bu değer elle yazıldı; okunmuş bir değer yok. | typed by hand | none | ok (unverified) | Plain |
| Zayıf örnekler; Sonraki/Önceki zayıf örnek; Belge {n}  {k} kontrol  en düşük %{p}; Önce Ctrl+T ile örnekleri deneyin.; Zayıf örnek yok: hiçbir okuma kontrol gerektirmiyor. | weak examples | "Sonraki/Önceki ..." (MS-prev) | ok (unverified for "zayıf örnek") | No sector term; self-explaining |

## C: qr-saved-filters.md

| Draft string | Concept | Sector terms found (source) | Recommendation | Reason |
|---|---|---|---|---|
| QR içeriğine göre seç… | Select by QR content | "Renge Göre Seç" (GIMP) | ok | Same "…e göre seç" pattern; also supports change of A's "Seç…" |
| QR içeriği; QR metni | QR content / text | none | ok (unverified) | QR fixed |
| ile başlar | starts with | "ile başlar" (LO-sc, "begins with") | ok | Exact |
| içerir | contains | "içerir" (LO-sc); "İçeren" (PAP) | ok | Exact |
| kalıp (* ve ?) | pattern with wildcards | "Joker Karakterleri" (LO-sc); "Eşleşme düzeni" (PAP); "eşleşme karakterleri" (LO-sc) | change: joker karakterli (* ve ?) | "kalıp" not seen |
| Örnek: KAP-04?? | hint | none | ok | |
| {n} sayfa eşleşti, {m} farklı değer | live line | "eşleşen" (PAP, "Eşleşme düzeni") | ok | |
| Sayfaları seç | button | "Sayfa seç" (EVI) | ok | Same as A |
| {n} sayfa seçildi (QR: {text}) | status | | ok | |
| Seçili sayfaların önünde kes | cut before selected | "Seçili sayfaları sil" (ABBYY) | ok | "kesim" fixed |
| Kesim ekle, {n} sayfa; {n} sayfada zaten kesim var | cuts | none | ok | |
| Bu iş, QR metni kaydedilmeden önce yüklendi | note | none | ok (unverified) | |
| QR metnini yeniden oku | button | none | ok | |
| Kayıtlı filtreler | Saved filters | "Kaydedilen görünümler" (PAP); "Kaydedilmiş" (LO-cui); "Kayıtlı" not seen | flag only | Keep "Kayıtlı"; "Kaydedilmiş" is the seen form |
| Kayıtlı filtrelere ekle… | add to saved | "Ekle" (PAP) | ok | |
| Filtrenin adı | name of filter | "Adı" (LO-cui), "İsim" (PAP) | ok | App uses "ad" |
| Kaydet | Save | "Kaydet" (PAP, PDFA, LO) | ok | Exact |
| {n} filtre açık: {m} sayfa; Hiçbir filtre açık değil | counts | none | ok (unverified) | |
| Kayıtlı filtre eklendi: {ad}; Kayıtlı filtre silindi; Kayıtlı filtre ekle | toasts, undo | "Sil" (PAP, LO) | ok | |
| Tanınmıyor; Bu filtreyi bu sürüm tanımıyor | unknown filter | "Bilinmeyen" (LO-svx, LO-sfx2) | ok (flag) | "Bilinmeyen filtre" is the seen form; draft is also clear |
| Sil, Yeniden adlandır | Delete, Rename | "Sil"; "Yeniden Adlandır" (LO-cui, LO-svx, LO-sfx2) | ok | Exact |

## D: disa-aktar.md

| Draft string | Concept | Sector terms found (source) | Recommendation | Reason |
|---|---|---|---|---|
| Belge no; No | document number; no. | none opened (e-Devlet not opened) | ok (unverified) | Common Turkish form-field wording |
| Özet | Summary sheet | none opened | ok (unverified) | Standard word |
| İş adı; Dışa aktarma zamanı; Belge sayısı | job name, export time, count | "Dışa Aktar" (LO-cui, LO-sfx2, PDFA "Dışa Aktar…") | ok | Verb matches fixed vocab; noun "dışa aktarma" unverified |
| Baskı önizleme | Print preview | "Baskı Önizleme" (MS-prev); "Yazdırma ön izleme" (LO-vcl); "Ön İzleme" (PAP); "Önizleme" (ABBYY) | ok | Microsoft form, one word "önizleme" |
| Yazdır… | Print | "Yazdır" (MS-prev, PAP) | ok | Exact |
| Sayfa {n} / {m} | page n of m | "Sayfa %d" (EVI); n/m form not seen in MS-prev | ok (unverified for "/") | |
| Önceki sayfa, Sonraki sayfa | previous, next | "Önceki Sayfa", "Sonraki Sayfa" (MS-prev); "Sonraki Sayfa" (EVI) | ok | Exact |
| Dışa aktarma planı, henüz yazılmadı; Dışa aktarıldı: {zaman} | sub titles | none | ok (unverified) | "yazılmadı" could be "kaydedilmedi"; plain either way |
| Önizleme hazırlanıyor… | busy | "Önizleme" (ABBYY, MS-prev) | ok | |
| Adları karşılaştır | compare names | "Karşılaştır" (LO-sc) | ok | |
| Kaynak | Source column | "Kaynak" (LO-sfx2); "Kaynaklar" (PAP) | ok | Exact |
| Ad listesini kopyala; Ad listesi panoya kopyalandı | copy name list | "Kopyala" (LO, PAP); "Simgeyi Panoya Kopyala" (GIMP) | ok | "Panoya kopyala" confirmed |
| Adı değişenler | names that changed | none | ok (unverified) | Plain |
| {dosya} +{n} | file and n more | none | ok | |
| Kontrol gerektiren belge yok.; Kontrol listesi: index.xlsx, sayfa 'Kontrol gerekenler'.; Kontrol listesini kaydet…; Kontrol listesi yazıldı | check list | "Kaydet" (PAP, PDFA) | ok | Fixed word "Kontrol"; "yazıldı" vs "kaydedildi" both fine |

## Counts

- Rows checked: about 123 (A 57, B 16, C 27, D 23), grouped into the tables above.
- Changes recommended: 5 (A: "Seç…", "Seçimin içinde ara", "Atılmış boş sayfa yok."; C: "kalıp"; plus "Atılmış" counted once). Flags for fixed words: 2 ("filtre"/"süzgeç", "Kayıtlı"/"Kaydedilmiş"); minor flags: "Yön"/"Yönelim", "Tanınmıyor"/"Bilinmeyen".
- Unverified (no opened source): about 70 rows, mostly status lines and long sentences that contain only fixed words.
