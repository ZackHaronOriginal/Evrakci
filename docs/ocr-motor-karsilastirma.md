# OCR motor karşılaştırması

Tarih: 2026-11-06. Komut: `evrakci ocr-karsilastir`. Gerçek taramalarla kendi bilgisayarınızda
denemek için: [ocr-gercek-tarama-testi.md](ocr-gercek-tarama-testi.md).

## Özet

| Motor | Tam doğru (taranmış görünüm) | Türkçe harf hatası | Saniye/sayfa | Kurulum |
|---|---|---|---|---|
| **Tesseract + tur_best** | **%94,1** | %1,6 | 1,7 | ~7 MB (+ Tesseract programı) |
| Tesseract + tur | %93,6 | %1,2 | 1,6 | ~4 MB (+ Tesseract programı) |
| RapidOCR PP-OCRv5 Latin | %51,0 | %21,2 | 1,3 | ~175 MB |
| RapidOCR PP-OCRv6 | bu ortamda indirilemedi | | | |

- **Tesseract açık ara önde.** Kutu içindeki alanların ~%94'ünü harfi harfine doğru okuyor.
- **RapidOCR'ın asıl sorunu Türkçe harfler:** ı'yı i, İ'yi I olarak okuyor (Türkçe harflerin
  ~%21'i yanlış). Bu harfler modelin karakter listesinde var; model onları ayırt edemiyor. Sicil
  numarası gibi sayılarda sorun yok, ama firma unvanlarında dosya adları bozulur.
- **Hız benzer:** 300 dpi A4 sayfa başına 1,3–1,7 saniye (bu sunucuda). 800 sayfa ≈ 20–25 dakika,
  hedefin (≤30 dk) içinde.
- **tur_best vs tur:** temiz sayfalarda tur_best belirgin daha iyi (%93,7'ye %88,4), taranmış
  görünümde ikisi neredeyse eşit. Fark 3 MB.
- **PP-OCRv6** bu ortamın ağından indirilemedi. Gerçek tarama testinde sizin bilgisayarınızda
  otomatik denenir.

**Önerim: Tesseract + tur_best.** Doğruluk, Türkçe harfler, kurulum boyutu ve Windows kurulumu
açısından en iyisi. Motor, tek bir arayüzün arkasında olduğu için ileride değiştirilebilir.

## Nasıl ölçüldü?

- Uydurma Türkçe kelimeler, sayılar ve tarihlerden oluşan sentetik A4 sayfalar, %40 serif, 9–14 pt,
  her alanın yeri ve doğru metni bilinerek üretildi.
- "Taranmış görünüm": hafif eğiklik (±0,7°), gürültü, bulanıklık ve JPEG sıkıştırma eklendi.
- **Tam doğru:** alan kutusu kesilip okutuldu; harfi harfine aynıysa doğru (büyük/küçük harf ve
  Türkçe harfler birebir).
- **Türkçe harf hatası:** doğru metindeki ı, i, İ, I, ş, ğ, ç, ö, ü (büyük ve küçük) harflerinden
  yanlış okunanların oranı.
- **Metin katmanı hizası:** tam sayfa okumada bulunan kelime kutularının gerçek kelimelerle
  örtüşme oranı (aranabilir PDF katmanı için).

## OCR motor karşılaştırması: 20 sentetik sayfa (tohum 1)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur | 93.6 | 0.4 | 1.2 | 1.62 | 99.4 | 4.4 |
| tesseract-tur_best | 94.1 | 0.3 | 1.6 | 1.69 | 99.4 | 7.1 |
| rapidocr-v5-latin | 51.0 | 4.3 | 21.2 | 1.30 | 99.8 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 202.

### Hatalı okumalar: tesseract-tur

| Doğrusu | Okunan |
|---|---|
| 916-7623 Pöşen Bümumgıtkar rözpül | 916-7623 Pöşen Bümumygıtkar rözpül |
| Gılsizcümröş | Gilsizcümröş |
| böl Fültığval çöşanvıyçum | böl Fültiğval çöşanvıyçum |
| VATDIKNÖZ şöyrezcıvüz 351-6548 | VATDIKNÖZ şöyrezcivüz 351-6548 |
| fö Cim vökdışcoz | ft6 Cim vökdışcoz |
| Füykaykeyçat Vızturün | Füykaykeyçat Vizturün |
| 942-6247 dupeşfet | 942-6247 dupeştfet |
| Vınkipeğ 09.03.2023 Büllorfumcuğ 242865 | Vinkipeğ 09.03.2023 Büllorfumcuğ 242865 |
| FÖKINRIZNİN | FOKINRIZNİN |
| beğsul şöltılbor 62598 | beğsul şöltilbor 62598 |
| KARVAM For DOŞPAT nol | KARVAM For DOŞPAT' nol |
| çütçuk Römmütçıçiz Vınfuçömmoy | çütçuk Römmütçıçiz Viınftuçömmoy |
| 563-9054 | 063-9054 |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| VATDIKNÖZ şöyrezcıvüz 351-6548 | VATDIKNÖZ şöyrezcivüz 351-6548 |
| ketpı sölcuşröl VINET | ketpı sölcuşröl VİNET |
| zoyber Yilcımyişluş 871404 Yağcür | zoyber Yilciımyişluş 871404 Yağcür |
| 05.08.1996 Nümyöyzöt rinkizkakcöş Silköşrı | 05.08.1996 Nümyöyzöt rinkizkakcöş Silköşri |
| zümlışpöşsuk çırkar zegasoşfiy natşıyvözcö | zümlişpöşsuk çırkar zegasoşfiy natşıyvözcö |
| 370035 Lılzilasoğ | 370035 Lıiılzilasoğ |
| 175239 Şiğratlel vırmenşöş | 175239 Şiğratlel virmenşöş |
| comfı fergurrün hemfir | comfi fergurrün hemfir |
| duğnecış HEMGÜT | duğneciş HEMGÜT |
| çütçuk Römmütçıçiz Vınfuçömmoy | çütçuk Römmütçiçiz Vınfuçömmoy |
| su Fit Fozfıtfız Biğyük | su Fit Fozfitfiz Biğyük |
| 399737 fızleşdüşcü nuznöy | 399737 fizleşdüşcü nuznöy |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| 916-7623 Pöşen Bümumgıtkar rözpül | 916-7623 Pöşen Bümumgitkar rözpül |
| Sağpit patyöğbimgı | Sağpit patyöğbimgi |
| Boş DOYVİZSAR 753763 | Boş DOYVIZSAR 753763 |
| gaşhöhuzhü Bözrogikzık | gaşhöhuzhü Bözrogikzik |
| çafın 25.06.2028 Pökdortız 41048 | çafin 25.06.2028 Pökdortiz 41048 |
| 15.03.2005 28.02.2017 YOTLÜKDİMNA nüşnuçöz | 15.03.2005 28.02.2017 YOTLÜKDIMNA nüşnuçöz |
| Gılsizcümröş | Gilsizcümröş |
| RUŞGÖĞ duzyu YARVÜZBAMKOR 210194 | RUŞGÖG duzyu YARVÜZBAMKOR 210194 |
| züruryal şuymığ vamruşneğ | züruryal şuymiğ vamruşneğ |
| böl Fültığval çöşanvıyçum | böl Fültigval çöşanviyçum |
| dıkurtüş Mützur 608-2817 ca | dikurtüş Mützur 608-2817 ca |
| bun lışocatfal | bun locatfal |
| Nolkizıksak ÇOYÇONDIHU | Nolkiziksak ÇOYÇONDIHU |
| VATDIKNÖZ şöyrezcıvüz 351-6548 | VATDIKNÖZ şöyrezcivüz 351-6548 |
| böğmirtişşöt 16.12.1994 | böğmirtişöt 16.12.1994 |

### Notlar

- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program ve dil dosyası sayılır; Windows'ta tüm Tesseract-OCR klasörü sayılır.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 10 sentetik sayfa (tohum 2)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur | 88.4 | 0.8 | 1.9 | 0.41 | 99.6 | 4.4 |
| tesseract-tur_best | 93.7 | 0.5 | 1.9 | 0.52 | 100.0 | 7.1 |
| rapidocr-v5-latin | 51.6 | 4.5 | 24.8 | 1.25 | 100.0 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 95.

### Hatalı okumalar: tesseract-tur

| Doğrusu | Okunan |
|---|---|
| suyvöt | Suyvöt |
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| FÖLLUMBIM 169003 15.11.2004 Kiy | FOLLUMBIM 169003 15.11.2004 Kiy |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şıtmenyu |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLMIĞHEK züm |
| 26.08.1994 990-8925 Matyisın cöğcır | 26.08.1994 990-8925 Matyisın cöğcir |
| 874567 | 8/4567 |
| fın RIMUĞ CİŞ | fin RIMUĞ CİŞ |
| Münlömsanpiz Lımmim | Münlömsanpiz LImmim |
| noynonyulcom Yomgemfozröt Şoyoldez Bum | noynonyulcom Yomgemtfozröt Şoyoldez Bum |
| 229371 Nı | 229371Nı |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgit Şuyvöz guyşiğlütvöm |
| GITBUZ | GİTBUZ |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVİĞHEK züm |
| Cekmımfol MÖTZÜŞREŞ Döştey | Cekmiımfol MÖTZÜŞREŞ Döştey |
| Şıyyüş 735-4708 Tortu 405-6164 | Şiyyüş 735-4708 Tortu 405-6164 |
| 229371 Nı | 229371 NI |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbikgit Şuyvöz guyşiğlütvöm |
| goğmoyvul çöybiydaz Dılki CÖK | goğmoyvul çöyl biydaz Dilki CÖK |
| boğyalrığkem | boğyalriğkem |
| Sazzaşvıtö mölbudor | Sazzavitö mölbudor |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şitmenyu |
| Zığşazrış luytötneykiş | Ziğşazri luytötneykiş |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVIGHEK züm |
| 25.07.2006 Cığrüm 584508 | 25.07.2006 Cigrüm 584508 |
| Tığyolöl rethuzvıt | Tiğyolöl rethuzvit |
| HOKGERTİMPIK 281694 Rölvöyrotçöl 12.08.2020 | HOKGERTIMPIK 281694 Rölvöyrotçöl 12.08.2020 |
| dıroğ 111117 gansek Ti | diroğ 111117 gansek Ti |
| VİNPÜFER | VINPÜFER |
| Venhış Sışno vülkuyfe HUZCIM | Venhiş Sişno vülkuyfe HUZCIM |
| CİFIŞOR veşsağmem | CIFIŞOR veşsağmem |
| sıygüğ HÜĞHÜZNO KIMMİTMEBİK ŞEŞTALZIR | siygüg HÜGHÜZNO KIMMITMEBIK ŞEŞTALZIR |

### Notlar

- Sayfalar temiz (tarama bozulması eklenmedi).
- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program ve dil dosyası sayılır; Windows'ta tüm Tesseract-OCR klasörü sayılır.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.
