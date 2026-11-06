# OCR motor karşılaştırması

Tarih: 2026-11-06. Komut: `evrakci ocr-karsilastir`. Gerçek taramalarla kendi bilgisayarınızda
denemek için: [ocr-gercek-tarama-testi.md](ocr-gercek-tarama-testi.md).

## Özet

Kutu içindeki alanların harfi harfine doğru okunma oranı (her satır 10 sentetik A4 sayfa, ~100 alan):

| Motor | Taranmış görünüm | Aynı sayfalar, temiz | 2° eğik | 2° eğik + ön işleme | Türkçe harf hatası | Saniye/sayfa | Kurulum |
|---|---|---|---|---|---|---|---|
| **Tesseract + tur_best** | **%94,7** | **%93,7** | **%93,0** | %90,0 | %0,9–1,9 | 1,7 | ~7 MB veri + Tesseract programı |
| Tesseract + tur | %91,6 | %88,4 | %92,0 | %90,0 | %1,2–2,3 | 1,6 | ~4 MB veri + Tesseract programı |
| RapidOCR PP-OCRv5 Latin | %51,6 | %51,6 | %46,0 | %48,0 | %20–26 | 1,3–1,5 | ~175 MB (çalışma kütüphaneleri dahil) |
| RapidOCR PP-OCRv6 | bu ortamda indirilemedi | | | | | | |

- **Tesseract açık ara önde**, her koşulda %88–95. **tur_best** tur'dan her koşulda iyi ya da eşit.
- **RapidOCR'ın sorunu Türkçe harfler:** ı'yı i, İ'yi I olarak okuyor (Türkçe harflerin %20–26'sı
  yanlış). Bu harfler modelin karakter listesinde var; model onları ayırt edemiyor. Sayılarda sorun
  yok, ama firma unvanlarında dosya adları bozulur.
- **Hız:** 300 dpi A4 sayfa başına 1,3–1,7 saniye (bu sunucuda). 800 sayfa ≈ 20–25 dakika, hedefin
  (≤30 dk) içinde. Temiz veya siyah-beyaz sayfalarda Tesseract 3 kat hızlanıyor (~0,5 sn).
- **Ön işleme** (düzeltme + siyah-beyaz, her motora aynı): 2° eğik sayfalarda Tesseract'ı
  iyileştirmedi (%92–93 → %90). Tesseract eğikliği zaten iyi tolere ediyor. Gerçek taramalarda
  `--on-isleme` ile ayrıca denenebilir.
- **PP-OCRv6** bu ortamın ağından indirilemedi. Gerçek tarama testinde sizin bilgisayarınızda
  otomatik denenir.

**Önerim ve sahibin seçimi: Tesseract + tur_best.** Doğruluk, Türkçe harfler, kurulum boyutu ve Windows kurulumu
açısından en iyisi. Motor tek bir arayüzün arkasında olduğu için ileride değiştirilebilir.

## Tesseract'ın üç resmi Türkçe verisi

Tesseract projesi Türkçe için üç resmi dosya yayımlar: `tur_fast`, standart `tur` ve `tur_best`.
Linux paketleri ve birçok kurulum "tur" adıyla aslında **tur_fast** dosyasını kurar (bu ortamda
SHA-256 ile doğrulandı); yukarıdaki "Tesseract + tur" satırı bu dosyadır.

Üçü aynı sayfalarda karşılaştırıldı (toplam ~235 kutu; 10 sayfalık taranmış görünüm + 5'er
sayfalık taranmış, temiz ve 2° eğik):

| Veri | Tüm ölçümler (tam doğru) | Tek tek ölçümlerde aralık | Türkçe harf hatası | Boyut |
|---|---|---|---|---|
| **tur_best** | **~%92,7** | %90–95 | %0,9–2,3 | 7 MB |
| tur (standart) | ~%92,3 | %88–95 | %0,6–2,3 | 18 MB |
| tur_fast | ~%91,4 | %84–96 | %1,1–2,3 | 4,5 MB |

- Fark, bu örnek büyüklüğünde **gürültü düzeyinde** (bir iki kutu). Bazı ölçümlerde tur_fast,
  bazılarında tur_best önde.
- **Karar (sahibin seçimi): Tesseract + tur_best.** Genel ortalamada hafif önde ve boyutu makul.
- Asıl karar verici test gerçek taramalardır: `evrakci ocr-karsilastir` üç dosyayı da otomatik
  dener (bkz. [ocr-gercek-tarama-testi.md](ocr-gercek-tarama-testi.md)).

## Nasıl ölçüldü?

- Uydurma Türkçe kelimeler, sayılar ve tarihlerden oluşan sentetik A4 sayfalar (%40 serif, 9–14 pt).
  Her alanın yeri ve doğru metni bilinir. Uydurma kelimeler, sözlük bilgisi kullanan Tesseract'ı biraz
  dezavantajlı kılar; gerçek metinde fark daha da açılabilir.
- **Taranmış görünüm:** hafif eğiklik (±0,7°), gürültü, bulanıklık ve JPEG sıkıştırma. "Temiz"
  sütunu aynı sayfaların bozulmasız hâlidir.
- **2° eğik:** sayfalar ±2°'ye kadar eğik. **Ön işleme:** her motora aynı uygulanan düzeltme ve
  siyah-beyaz (Otsu).
- **Tam doğru:** alan kutusu kesilip okutuldu; büyük/küçük harf ve Türkçe harfler birebir aynıysa doğru.
- **Türkçe harf hatası:** doğru metindeki ı, i, İ, I, ş, ğ, ç, ö, ü (büyük ve küçük) harflerinden
  yanlış okunanların oranı.
- **Metin katmanı hizası:** tam sayfa okumada bulunan kelimelerin gerçek kelimelerle örtüşme oranı
  (aranabilir PDF katmanı için). Tüm motorlarda %99,6–100.


## OCR motor karşılaştırması: 10 sentetik sayfa (tohum 2)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur | 91.6 | 0.5 | 1.2 | 1.62 | 99.6 | 4.4 |
| tesseract-tur_best | 94.7 | 0.4 | 0.9 | 1.72 | 100.0 | 7.1 |
| rapidocr-v5-latin | 51.6 | 4.9 | 26.0 | 1.45 | 100.0 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 95.

### Hatalı okumalar: tesseract-tur

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şıtmenyu |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLMIĞHEK züm |
| YUTCUL kıykelışsam ci yıntömçut | YUTCUL kıykeliışsam ci yıntömçut |
| sizçanlal MUYKUTLUŞLAL BİNNOZ Rıcerseş | sizçanlal MUYKUTLUŞLAL BİNNOZ Ricerseş |
| Münlömsanpiz Lımmim | Münlömsanpiz LLmmim |
| 32608 Ser | 320608 Ser |
| 229371 Nı | 229371Nı |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| GITBUZ | GIİTBUZ |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVİĞHEK züm |
| 894325 CUŞFIŞ zıt Güzfönboygım | 894325 CUŞFİŞ zıt Güzfönboygım |
| Çozden MIY Müm | Çozden MIİY Müm |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbikgit Şuyvöz guyşiğlütvöm |
| goğmoyvul çöybiydaz Dılki CÖK | goğmoyvul cöyk biydaz Dilki CÖK |
| boğyalrığkem | boğyalrigkem |
| Sazzaşvıtö mölbudor | Sazzaşvitö mölbudor |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR cepitfuçan Şitmenyu |
| Zığşazrış luytötneykiş | Ziğşazri luytötneykiş |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVIGHEK : züm |
| 25.07.2006 Cığrüm 584508 | 25.07.2006 Ciğrüm 584508 |
| Tığyolöl rethuzvıt | Tiğyolöl rethuzvit |
| HOKGERTİMPIK 281694 Rölvöyrotçöl 12.08.2020 | HOKGERTIMPIK 281694 Rölvöyrotçöl 12.08.2020 |
| dıroğ 111117 gansek Ti | diroğ 111117 gansek Ti |
| VİNPÜFER | VINPÜFER |
| Venhış Sışno vülkuyfe HUZCIM | Venhi Sişno vülkuyfe HUZCIM |
| CİFIŞOR veşsağmem | CIFIŞOR veşsağmem |
| sıygüğ HÜĞHÜZNO KIMMİTMEBİK ŞEŞTALZIR | siygüğ HÜGHÜZNO KIMMITMEBIK ŞEŞTALZIR |

### Notlar

- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 10 sentetik sayfa (tohum 2)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur | 88.4 | 0.8 | 1.9 | 0.44 | 99.6 | 4.4 |
| tesseract-tur_best | 93.7 | 0.5 | 1.9 | 0.55 | 100.0 | 7.1 |
| rapidocr-v5-latin | 51.6 | 4.5 | 24.8 | 1.28 | 100.0 | 174.8 |
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
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 10 sentetik sayfa (tohum 3)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur | 92.0 | 0.5 | 1.8 | 1.62 | 99.6 | 4.4 |
| tesseract-tur_best | 93.0 | 0.3 | 1.0 | 1.74 | 99.6 | 7.1 |
| rapidocr-v5-latin | 46.0 | 4.7 | 23.1 | 1.37 | 99.6 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 100.

### Hatalı okumalar: tesseract-tur

| Doğrusu | Okunan |
|---|---|
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbil |
| Geysöyföpıl püzömheyyoz SOSÖŞTÖZ ZUYDÖT | Geysöyföpil püzömheyyoz SOSÖŞTÖZ ZUYDÖT |
| Vıkşutzuş | Vikşutzuş |
| firbuy TÜŞVUZHÜŞCI fut 623565 | firbuy TÜŞVUZHÜŞCİ fut 623565 |
| Söt Güdıktoşviğ BÖĞZÜTŞAĞ | Söt Güdiktoşviğ BÖĞZÜTŞAĞ |
| mögım | mMögım |
| boşitşirır Dığsazrer Çeğbır | boşitşirır Dığsazrer Çeğbir |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| 990336 tö fıkşe | 990336 tö fikşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiıksürşük |
| 510669 Hokguşnalhak cışlutir | 210669 Hokguşnalhak cışlutir |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbil |
| non mükkeryakyek 16.03.2010 892771 | non mMmükkeryakyek 16.03.2010 892771 |
| boşitşirır Dığsazrer Çeğbır | boşitşirir Dığsazrer Çeğbır |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| zezbülyirtüş 21.03.2023 | zezbülyirtüs 21.03.2023 |
| Mulvot buzzınük Tazcaklül | Mulvot buzzinük Tazcaklül |
| Dazfotkornım nöm Çöyhül | Dazfotkornim nöm Çöyhül |
| Pış şömsoşzu 01.08.2029 | PIs şömsoşzu 01.08.2029 |
| Nıkçöşroklik | Nikçöşroklik |
| POŞEYVUM ZAĞ | POŞEYVUM ZAG |
| 01.06.1997 120697 ZOCİYET çinküz | 01.06.1997 120697 ZOCIYET cinküz |
| sışzün | sişzün |
| forför SORMALTUR tıştiğzağ 993593 | forför SORMALTUR tiştiğzağ 993593 |
| 474340 baknuşter Rıtnelçuşo | 474340 baknuşter Ritnelçuşo |
| 990336 tö fıkşe | 990336 tö fkşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| fışhızgilpo RÖTZOMTOMTAZ Kün Vivü | fişhizgilpo RÖTZOMTOMTAZ Kün Vivü |
| çayçör Kükdaşçiyguğ 893172 | çayçör Kükdaşciyguğ 893172 |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiksürşük |

### Notlar

- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 10 sentetik sayfa (tohum 3)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur | 90.0 | 0.7 | 2.3 | 0.47 | 99.6 | 4.4 |
| tesseract-tur_best | 90.0 | 0.6 | 1.8 | 0.56 | 99.6 | 7.1 |
| rapidocr-v5-latin | 48.0 | 4.6 | 20.3 | 1.35 | 99.6 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 100.

### Hatalı okumalar: tesseract-tur

| Doğrusu | Okunan |
|---|---|
| 990336 tö fıkşe | 990336 tö fikşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| Feğmuğçin rönsoğtik şök VAFIT | Feğmuğçin rönsoğtik şök VAFTTI |
| Geysöyföpıl püzömheyyoz SOSÖŞTÖZ ZUYDÖT | Geysöyföpil püzömheyyoz SOSÖŞTÖZ ZUYDÖT |
| Vıkşutzuş | Vikşutzuş |
| firbuy TÜŞVUZHÜŞCI fut 623565 | firbuy TÜŞVUZHÜŞCİ fut 623565 |
| Söt Güdıktoşviğ BÖĞZÜTŞAĞ | Söt Güdiktoşviğ BÖĞZÜTŞAĞ |
| mögım | mögim |
| boşitşirır Dığsazrer Çeğbır | boşitşirır Dığsazrer Çeğbir |
| RILPOZKÜ pezpil vıçut | RILPOZKÜU pezpil vıçut |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| 474340 baknuşter Rıtnelçuşo | 474340 baknuşter Ritnelçüuşo |
| 990336 tö fıkşe | 990336 tö fikşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiksürşük |
| 228480 hüyyuk Tuğzalbıbıl 495039 | 228480 hüyyuk Tuğzalbıbil 495039 |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbiıl |
| firbuy TÜŞVUZHÜŞCI fut 623565 | firbuy TÜŞVUZHÜŞSCI fut 623565 |
| mögım | mögim |
| boşitşirır Dığsazrer Çeğbır | boşitşirir Dığsazrer Çeğbır |
| ZEKHOZTİZŞOY DÜVÜMGÖM Bilponşın | ZEKHOZTİZŞOY DÜVÜMGÜÖM Bilponşın |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| Mulvot buzzınük Tazcaklül | Mulvot t buzzinük Tazcaklül |
| Dazfotkornım nöm Çöyhül | Dazfotkornim nöm Çöyhül |
| Pış şömsoşzu 01.08.2029 | Piş şömsoşzu  01.08.2029 |
| yörçoka Saten 120-9601 Dön | yörçoka Saten n 120-9601 Dön |
| Nıkçöşroklik | Nikçöşroklik |
| POŞEYVUM ZAĞ | POŞEYVUM ZAG |
| 01.06.1997 120697 ZOCİYET çinküz | 01.06.1997 120697 ZOCIYET çinküz |
| sışzün | sizün |
| forför SORMALTUR tıştiğzağ 993593 | forför SORMALTUR t tiştiğzağ 993593 |
| 474340 baknuşter Rıtnelçuşo | 474340 baknuşter  Ritnelçuşo |
| 990336 tö fıkşe | 990336 tö fikşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| fışhızgilpo RÖTZOMTOMTAZ Kün Vivü | fişhizgilpo RÖTZOMTOMTAZ Kün n Vivü |
| çayçör Kükdaşçiyguğ 893172 | çayçör Kükdaşςyguğ 893172 |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiksürşük |

### Notlar

- Ön işleme açık: her motor için düzeltme ve siyah-beyaz yapıldı.
- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 5 sentetik sayfa (tohum 2)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur (sistem) | 93.2 | 0.2 | 1.1 | 1.59 | 100.0 | 4.4 |
| tesseract-tur_fast | 93.2 | 0.2 | 1.1 | 5.25 | 100.0 | 4.4 |
| tesseract-tur_standard | 90.9 | 0.6 | 1.1 | 2.17 | 100.0 | 17.9 |
| tesseract-tur_best | 90.9 | 0.6 | 1.7 | 1.68 | 100.0 | 7.1 |
| rapidocr-v5-latin | 47.7 | 5.5 | 27.4 | 1.43 | 100.0 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 44.

### Hatalı okumalar: tesseract-tur (sistem)

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şıtmenyu |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLMIĞHEK züm |

### Hatalı okumalar: tesseract-tur_fast

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şıtmenyu |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLMIĞHEK züm |

### Hatalı okumalar: tesseract-tur_standard

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| GITBUZ | GIİTBUZ |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVİĞHEK züm |
| 894325 CUŞFIŞ zıt Güzfönboygım | 894325 CUŞFİIŞ zıt Güzfönboygım |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| GITBUZ | GIİTBUZ |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVİĞHEK züm |
| 894325 CUŞFIŞ zıt Güzfönboygım | 894325 CUŞFİŞ zıt Güzfönboygım |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbikgit Şuyvöz guyşiğlütvöm |
| goğmoyvul çöybiydaz Dılki CÖK | goğmoyvul cöyk biydaz Dilki CÖK |
| boğyalrığkem | boğyalrigkem |
| Sazzaşvıtö mölbudor | Sazzaşvitö mölbudor |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR cepitfuçan Şitmenyu |
| Zığşazrış luytötneykiş | Ziğşazri luytötneykiş |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVIGHEK : züm |
| 25.07.2006 Cığrüm 584508 | 25.07.2006 Ciğrüm 584508 |
| Tığyolöl rethuzvıt | Tiğyolöl rethuzvit |
| HOKGERTİMPIK 281694 Rölvöyrotçöl 12.08.2020 | HOKGERTIMPIK 281694 Rölvöyrotçöl 12.08.2020 |
| dıroğ 111117 gansek Ti | diroğ 111117 gansek Ti |
| VİNPÜFER | VINPÜFER |
| Venhış Sışno vülkuyfe HUZCIM | Venhi Sişno vülkuyfe HUZCIM |
| CİFIŞOR veşsağmem | CIFIŞOR veşsağmem |
| sıygüğ HÜĞHÜZNO KIMMİTMEBİK ŞEŞTALZIR | siygüğ HÜGHÜZNO KIMMITMEBIK ŞEŞTALZIR |

### Notlar

- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 5 sentetik sayfa (tohum 2)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur (sistem) | 84.1 | 1.1 | 2.3 | 0.43 | 100.0 | 4.4 |
| tesseract-tur_fast | 84.1 | 1.1 | 2.3 | 0.43 | 100.0 | 4.4 |
| tesseract-tur_standard | 93.2 | 0.6 | 1.7 | 0.70 | 100.0 | 17.9 |
| tesseract-tur_best | 93.2 | 0.6 | 2.3 | 0.51 | 100.0 | 7.1 |
| rapidocr-v5-latin | 47.7 | 4.8 | 25.1 | 1.49 | 100.0 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 44.

### Hatalı okumalar: tesseract-tur (sistem)

| Doğrusu | Okunan |
|---|---|
| suyvöt | Suyvöt |
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| FÖLLUMBIM 169003 15.11.2004 Kiy | FOLLUMBIM 169003 15.11.2004 Kiy |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şıtmenyu |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLMIĞHEK züm |
| 26.08.1994 990-8925 Matyisın cöğcır | 26.08.1994 990-8925 Matyisın cöğcir |
| 874567 | 8/4567 |

### Hatalı okumalar: tesseract-tur_fast

| Doğrusu | Okunan |
|---|---|
| suyvöt | Suyvöt |
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgıt Şuyvöz guyşiğlütvöm |
| FÖLLUMBIM 169003 15.11.2004 Kiy | FOLLUMBIM 169003 15.11.2004 Kiy |
| FÖLTÜYSÜMMUR çepıtfuçan Şıtmenyu | FÖLTÜYSÜMMUR çepitfuçan Şıtmenyu |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLMIĞHEK züm |
| 26.08.1994 990-8925 Matyisın cöğcır | 26.08.1994 990-8925 Matyisın cöğcir |
| 874567 | 8/4567 |

### Hatalı okumalar: tesseract-tur_standard

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgit Şuyvöz guyşiğlütvöm |
| GITBUZ | GIİTBUZ |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVİĞHEK züm |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| Vıtgirbıkgıt Şuyvöz guyşiğlütvöm | Vitgirbıkgit Şuyvöz guyşiğlütvöm |
| GITBUZ | GİTBUZ |
| bur duthoy FAZSÜLVIĞHEK züm | bur duthoy FAZSÜLVİĞHEK züm |

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
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.

## OCR motor karşılaştırması: 5 sentetik sayfa (tohum 3)

| Motor | Tam doğru % | Karakter hatası % | Türkçe harf hatası % | Saniye/sayfa | Metin katmanı hizası % | Kurulum MB |
|---|---|---|---|---|---|---|
| tesseract-tur (sistem) | 96.0 | 0.1 | 1.1 | 12.40 | 99.2 | 4.4 |
| tesseract-tur_fast | 96.0 | 0.1 | 1.1 | 1.56 | 99.2 | 4.4 |
| tesseract-tur_standard | 88.0 | 0.5 | 2.3 | 1.91 | 99.2 | 17.9 |
| tesseract-tur_best | 90.0 | 0.4 | 1.7 | 1.68 | 99.2 | 7.1 |
| rapidocr-v5-latin | 40.0 | 5.0 | 25.6 | 1.29 | 100.0 | 174.8 |
| rapidocr-v6-multi | kullanılamıyor: Model indirilemedi: multi_PP-OCRv6_rec_small.onnx (<urlopen error Tunnel connection failed: 403 Forbidden>) | | | | | - |

Alan sayısı: 50.

### Hatalı okumalar: tesseract-tur (sistem)

| Doğrusu | Okunan |
|---|---|
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbil |

### Hatalı okumalar: tesseract-tur_fast

| Doğrusu | Okunan |
|---|---|
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbil |

### Hatalı okumalar: tesseract-tur_standard

| Doğrusu | Okunan |
|---|---|
| 474340 baknuşter Rıtnelçuşo | 474340 baknuşter Ritnelçuşo |
| 990336 tö fıkşe | 990336 tö fikşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiıksürşük |
| 510669 Hokguşnalhak cışlutir | 210669 Hokguşnalhak cışlutir |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbil |

### Hatalı okumalar: tesseract-tur_best

| Doğrusu | Okunan |
|---|---|
| 990336 tö fıkşe | 990336 tö fikşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiıksürşük |
| 510669 Hokguşnalhak cışlutir | 210669 Hokguşnalhak cışlutir |
| golpo Hil tirpin Goğpayüğbıl | golpo Hil tirpin Goğpayüğbil |

### Hatalı okumalar: rapidocr-v5-latin

| Doğrusu | Okunan |
|---|---|
| zezbülyirtüş 21.03.2023 | zezbülyirtüs 21.03.2023 |
| Mulvot buzzınük Tazcaklül | Mulvot buzzinük Tazcaklül |
| Dazfotkornım nöm Çöyhül | Dazfotkornim nöm Çöyhül |
| Pış şömsoşzu 01.08.2029 | PIs şömsoşzu 01.08.2029 |
| Nıkçöşroklik | Nikçöşroklik |
| POŞEYVUM ZAĞ | POŞEYVUM ZAG |
| 01.06.1997 120697 ZOCİYET çinküz | 01.06.1997 120697 ZOCIYET cinküz |
| sışzün | sişzün |
| forför SORMALTUR tıştiğzağ 993593 | forför SORMALTUR tiştiğzağ 993593 |
| 474340 baknuşter Rıtnelçuşo | 474340 baknuşter Ritnelçuşo |
| 990336 tö fıkşe | 990336 tö fkşe |
| Tonçeygukdol tor Rütçöğdıl | Tonçeygukdol tor Rütçöğdil |
| fışhızgilpo RÖTZOMTOMTAZ Kün Vivü | fişhizgilpo RÖTZOMTOMTAZ Kün Vivü |
| çayçör Kükdaşçiyguğ 893172 | çayçör Kükdaşciyguğ 893172 |
| 25.08.2011 Culrelgu Gutpıksürşük | 25.08.2011 Culrelgu Gutpiksürşük |

### Notlar

- Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) gerçek metinde biraz daha iyi sonuç verebilir.
- Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri (onnxruntime, OpenCV) dahildir.
- Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.
