# OCR motorlarını gerçek taramalarla deneme

Bu rehber, OCR motorlarını kendi bilgisayarınızda **gerçek** taramalarla karşılaştırmak içindir.
Sentetik test sonuçları için: [ocr-motor-karsilastirma.md](ocr-motor-karsilastirma.md).

> ⚠️ Gerçek taramaları, `kutular.json` dosyanızı ve oluşan raporu **asla depoya eklemeyin**.
> Hepsini depo dışında bir klasörde tutun (örneğin `Belgeler\ocr-deneme`). Rapor, belgelerdeki
> metinleri içerir.

## 1. Kurulum (Windows)

1. **Tesseract:** UB Mannheim Windows kurulum dosyasını indirip kurun
   (<https://github.com/UB-Mannheim/tesseract/wiki>). Kurulumda **Turkish** dil paketini işaretleyin.
   Evrakçı, Tesseract'ı `C:\Program Files\Tesseract-OCR` içinde kendisi bulur. Başka bir yere
   kurduysanız `EVRAKCI_TESSERACT` ortam değişkenine `tesseract.exe` yolunu yazın.
2. **Evrakçı ve RapidOCR** (depo klasöründe):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e ".[rapidocr]"
   ```

3. **Modeller:** RapidOCR modellerini ve Tesseract'ın daha büyük Türkçe verisini (`tur_best`)
   indirin:

   ```bash
   evrakci ocr-modelleri-indir
   ```

   Tüm dosyalar SHA-256 ile doğrulanır (RapidOCR modelleri RapidOCR'ın yayımladığı değerlerle,
   `tur_best` Evrakçı'da kayıtlı değerle). Doğrulanamayan dosya silinir ve kullanılmaz. Bir dosya
   indirilemezse komut hata koduyla biter ve hangi dosya olduğunu yazar.

## 2. Taramaları hazırlayın

- 5–10 farklı belgeden birkaç sayfa seçin: kendi formlarınız ve dışarıdan gelen belgeler.
- 300 dpi, gri tonlu PDF olarak tarayın (günlük kullandığınız ayarla).

## 3. Sadece okuma ve hız

```bash
evrakci ocr-karsilastir tarama1.pdf tarama2.pdf --cikti rapor.md
```

Rapor, her motorun sayfa başına süresini ve her sayfadan okuduğu metnin başını yan yana gösterir.

## 4. Kutularla doğruluk ölçümü (önerilir)

İsimlendirmede kullanılacak alanların doğru okunup okunmadığını ölçmek için bir `kutular.json`
yazın. Her satır bir kutudur: hangi PDF, kaçıncı sayfa, kutunun milimetre cinsinden yeri (sol, üst,
sağ, alt; sayfanın sol üst köşesinden) ve kutudaki doğru metin.

```json
[
  {"pdf": "tarama1.pdf", "sayfa": 1, "kutu_mm": [20, 40, 150, 50], "beklenen": "Örnek Ticaret Ltd. Şti."},
  {"pdf": "tarama1.pdf", "sayfa": 1, "kutu_mm": [20, 55, 80, 63], "beklenen": "123456"},
  {"pdf": "tarama2.pdf", "sayfa": 2, "kutu_mm": [110, 30, 190, 38]}
]
```

- `beklenen` yazılmazsa o kutu puanlanmaz, yalnızca okunanlar gösterilir.
- Milimetreyi ölçmek için: PDF'i bir PDF okuyucuda açın, sayfanın sol üst köşesinden cetvelle veya
  okuyucunun ölçü aracıyla ölçün. Kutuyu metinden biraz büyük tutun.

```bash
evrakci ocr-karsilastir tarama1.pdf tarama2.pdf --kutular kutular.json --cikti rapor.md
```

Taramalarınız eğikse veya soluksa, aynı komutu `--on-isleme` ile bir kez daha çalıştırın: her motor
için sayfayı düzeltir ve siyah-beyaz yapar. İki raporu karşılaştırın.

- PDF adları farklı olmalı; aynı adlı iki PDF verirseniz komut uyarır.
- `beklenen` içine sayı yazarken tırnak unutulursa da sorun olmaz, metin olarak okunur.

Raporun "Kutularda tam doğru" sütunu, her motorun kaç kutuyu harfi harfine doğru okuduğunu
gösterir. "Kutular" tablosunda okumalar yan yana durur.

## 5. Sonucu paylaşın

Raporu paylaşmanız gerekmez. Bana yalnızca özet tabloyu (motorlar, süreler, doğru kutu sayıları)
ve hangi tür belgelerde hangi motorun hata yaptığını yazmanız yeterli.
