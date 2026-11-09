"""`evrakci ocr-karsilastir` and `evrakci ocr-modelleri-indir`."""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import time
import urllib.request
from pathlib import Path

import pypdfium2 as pdfium

from evrakci.cli.errors import UserError
from evrakci.pipeline.ocr.compare import cell, compare_synthetic, install_sizes, render_report
from evrakci.pipeline.ocr.engine import EngineUnavailable, OcrEngine
from evrakci.pipeline.ocr.metrics import exact
from evrakci.pipeline.ocr.models import ensure_model, official_model
from evrakci.pipeline.ocr.preprocess import prepare_page, prepare_region
from evrakci.pipeline.ocr.rapid import RapidOcrEngine
from evrakci.pipeline.ocr.synthetic import make_pages
from evrakci.pipeline.ocr.tesseract import (
    TESSDATA_VARIANTS,
    TUR_BEST_URL,
    TesseractEngine,
    default_tessdata,
    prepare_tessdata,
    tessdata_dir,
    verify_tessdata,
)
from evrakci.pipeline.ocr.textlayer import add_text_layer

_DPI = 300
_TUR_BEST_URL = TUR_BEST_URL
_MODELS = [
    ("PP-OCRv5", "det", "ch_PP-OCRv5_det_mobile"),
    ("PP-OCRv5", "rec", "latin_PP-OCRv5_rec_mobile"),
    ("PP-OCRv6", "rec", "multi_PP-OCRv6_rec_small"),
]
_SYNTHETIC_NOTES = [
    "Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) "
    "gerçek metinde biraz daha iyi sonuç verebilir.",
    "Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program dosyası ve dil "
    "verisi sayılır, paylaşılan kütüphaneleri sayılmaz; Windows'ta Tesseract programı ve "
    "kütüphaneleri ayrıca onlarca MB yer kaplar. RapidOCR sayısına çalışma kütüphaneleri "
    "(onnxruntime, OpenCV) dahildir.",
    "Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.",
]


def all_engines() -> list[OcrEngine]:
    return [
        TesseractEngine("tur", name="tesseract-tur (sistem)"),
        *(
            TesseractEngine("tur", tessdata_dir=tessdata_dir(v), name=f"tesseract-tur_{v}")
            for v in ("fast", "standard", "best")
        ),
        RapidOcrEngine(),
        RapidOcrEngine("multi_PP-OCRv6_rec_small", "PP-OCRv6", name="rapidocr-v6-multi"),
    ]


# The one page image kept at a time: real scans are rendered page by page, never all at once.
_RENDERED: dict[tuple[str, int], object] = {}


def _open_pdf(path: Path):
    if not path.is_file():
        raise UserError(f"Dosya bulunamadı: {path.name}")
    try:
        return pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError:
        raise UserError(f"PDF açılamadı: {path.name}") from None


class _Pages:
    """The pages of the real scans, rendered at 300 dpi only when needed."""

    def __init__(self, pdfs: list[Path]) -> None:
        self.paths = {path.name: path for path in pdfs}
        self.counts = {}
        for path in pdfs:
            pdf = _open_pdf(path)
            try:
                self.counts[path.name] = len(pdf)
            finally:
                pdf.close()
            if not self.counts[path.name]:
                raise UserError(f"PDF'de sayfa yok: {path.name}")

    def image(self, name: str, number: int):
        key = (name, number)
        if key not in _RENDERED:
            _RENDERED.clear()  # let the previous page go first
            pdf = _open_pdf(self.paths[name])
            try:
                page = pdf[number - 1]
                try:
                    bitmap = page.render(scale=_DPI / 72, grayscale=True)
                    _RENDERED[key] = bitmap.to_pil().convert("L")
                finally:
                    page.close()
            finally:
                pdf.close()
        return _RENDERED[key]


def _load_boxes(path: Path) -> list[dict]:
    try:
        boxes = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(boxes, list):
            raise ValueError("liste değil")
        for box in boxes:
            box["kutu_mm"] = [float(v) for v in box["kutu_mm"]]
            box["sayfa"] = int(box["sayfa"])
            box["pdf"] = str(box["pdf"])
            if len(box["kutu_mm"]) != 4 or box["sayfa"] < 1:
                raise ValueError("kutu_mm 4 sayı, sayfa 1 veya büyük olmalı")
            if box.get("beklenen") is not None:
                box["beklenen"] = str(box["beklenen"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise UserError(f"Kutu dosyası okunamadı: {path.name} ({error})") from None
    return boxes


def _box_pixels(box_mm: list[float], size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (round(float(v) / 25.4 * _DPI) for v in box_mm)
    if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
        raise UserError(f"Kutu sayfanın dışında: {box_mm}")
    return x0, y0, x1, y1


def _real_report(
    pdfs: list[Path], boxes: list[dict], engines: list[OcrEngine], preprocess: bool = False
) -> str:
    names = [path.name for path in pdfs]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        names_text = ", ".join(duplicates)
        raise UserError(f"Aynı adlı PDF'ler var: {names_text}. Lütfen yeniden adlandırın.")
    pages = _Pages(pdfs)
    for box in boxes:
        name = Path(box["pdf"]).name
        if not 1 <= int(box["sayfa"]) <= pages.counts.get(name, 0):
            raise UserError(f"Kutudaki PDF veya sayfa yok: {box['pdf']} sayfa {box['sayfa']}")
        box["_px"] = _box_pixels(box["kutu_mm"], pages.image(name, int(box["sayfa"])).size)

    usable = []
    lines = ["# OCR motor karşılaştırması: gerçek taramalar", ""]
    if preprocess:
        lines += ["Ön işleme açık: her motor için düzeltme ve siyah-beyaz yapıldı.", ""]
    lines += ["| Motor | Saniye/sayfa | Kutularda tam doğru |", "|---|---|---|"]
    texts: dict[str, dict[tuple[str, int], str]] = {}
    readings: dict[str, list[str]] = {}
    for engine in engines:
        reason = engine.available()
        if reason is None:
            try:
                seconds, count = _read_all(engine, pages, boxes, texts, readings, preprocess)
            except EngineUnavailable as error:
                reason = str(error)
        if reason:
            lines.append(f"| {engine.name} | kullanılamıyor: {cell(reason)} | |")
            continue
        usable.append(engine)
        scored = [b for b in boxes if b.get("beklenen")]
        right = sum(
            exact(b["beklenen"], readings[engine.name][i])
            for i, b in enumerate(boxes)
            if b.get("beklenen")
        )
        score = f"{right}/{len(scored)}" if scored else "-"
        lines.append(f"| {engine.name} | {seconds / max(count, 1):.2f} | {score} |")

    if boxes and usable:
        lines += ["", "## Kutular", ""]
        lines.append("| PDF | Sayfa | Beklenen | " + " | ".join(e.name for e in usable) + " |")
        lines.append("|---|---|---|" + "---|" * len(usable))
        for i, box in enumerate(boxes):
            cells = [cell(readings[e.name][i]) or "(boş)" for e in usable]
            lines.append(
                f"| {cell(box['pdf'])} | {box['sayfa']} | {cell(box.get('beklenen') or '')} | "
                + " | ".join(cells)
                + " |"
            )
    _RENDERED.clear()
    for name, count in pages.counts.items():
        for number in range(1, count + 1):
            lines += ["", f"## {name}, sayfa {number}", ""]
            for engine in usable:
                lines.append(f"- **{engine.name}:** {texts[engine.name][(name, number)]}")
    return "\n".join(lines) + "\n"


def _read_all(
    engine: OcrEngine,
    pages: _Pages,
    boxes: list[dict],
    texts: dict[str, dict[tuple[str, int], str]],
    readings: dict[str, list[str]],
    preprocess: bool,
) -> tuple[float, int]:
    """Read every page and box with one engine. Returns (seconds, pages read)."""
    first = pages.image(next(iter(pages.counts)), 1)
    engine.read_region(first.crop((0, 0, min(400, first.width), min(100, first.height))))  # warm-up
    seconds, count = 0.0, 0
    page_texts = {}
    for name, count in pages.counts.items():
        for number in range(1, count + 1):
            image = pages.image(name, number)
            prepared = prepare_page(image) if preprocess else image
            started = time.perf_counter()
            words = engine.read_page(prepared)
            seconds += time.perf_counter() - started
            count += 1
            page_texts[(name, number)] = " ".join(w.text for w in words)[:400]
    box_readings = []
    for box in boxes:
        crop = pages.image(Path(box["pdf"]).name, box["sayfa"]).crop(box["_px"])
        box_readings.append(engine.read_region(prepare_region(crop) if preprocess else crop).text)
    texts[engine.name] = page_texts
    readings[engine.name] = box_readings
    return seconds, count


def compare(args: argparse.Namespace, store) -> int:
    engines = all_engines()
    if args.sentetik:
        pages = make_pages(
            args.sentetik, seed=args.tohum, degrade=not args.temiz, max_skew=args.egim
        )
        title = f"OCR motor karşılaştırması: {args.sentetik} sentetik sayfa (tohum {args.tohum})"
        notes = list(_SYNTHETIC_NOTES)
        if args.temiz:
            notes.insert(0, "Sayfalar temiz (tarama bozulması eklenmedi).")
        if args.on_isleme:
            notes.insert(0, "Ön işleme açık: her motor için düzeltme ve siyah-beyaz yapıldı.")
        results = compare_synthetic(engines, pages, preprocess=args.on_isleme)
        report = render_report(results, install_sizes(), title, notes)
    else:
        if not args.pdf:
            raise UserError("PDF dosyası veya --sentetik verin.")
        boxes = _load_boxes(args.kutular) if args.kutular else []
        report = _real_report(args.pdf, boxes, engines, preprocess=args.on_isleme)
    args.cikti.parent.mkdir(parents=True, exist_ok=True)
    args.cikti.write_text(report, encoding="utf-8")
    print(f"Rapor yazıldı: {args.cikti}")
    return 0


def download_models(args: argparse.Namespace, store) -> int:
    failed = False
    for version, kind, key in _MODELS:
        try:
            path = ensure_model(official_model(version, kind, key))
            print(f"{key}: hazır ({path})")
        except ImportError:  # e.g. the installed app: RapidOCR is only for the comparison
            print("RapidOCR kurulu değil; yalnızca motor karşılaştırması için gerekir, atlandı.")
            break
        except (EngineUnavailable, KeyError) as error:
            failed = True
            print(f"{key}: hata: {error}")
    for variant in ("fast", "standard", "best"):
        failed |= not _download_tessdata(variant)
    return 1 if failed else 0


def _download_tessdata(variant: str) -> bool:
    folder = tessdata_dir(variant)
    target = folder / "tur.traineddata"
    label = f"tur_{variant}"
    partial = target.with_name(target.name + ".part")
    try:
        if verify_tessdata(variant, folder):
            prepare_tessdata(folder)
            print(f"{label}: hazır ({target})")
            return True
        folder.mkdir(parents=True, exist_ok=True)
        url = _TUR_BEST_URL if variant == "best" else TESSDATA_VARIANTS[variant].url
        with urllib.request.urlopen(url, timeout=120) as response:
            data = response.read()
        # Checked before it takes the real name, so an unverified file never sits there.
        if hashlib.sha256(data).hexdigest() != TESSDATA_VARIANTS[variant].sha256:
            raise OSError("indirilen dosya doğrulanamadı")
        partial.write_bytes(data)
        partial.replace(target)
        prepare_tessdata(folder)
        print(f"{label}: indirildi ({target})")
        return True
    except (OSError, EngineUnavailable, http.client.HTTPException) as error:
        partial.unlink(missing_ok=True)
        print(f"{label}: hata: {error!r}" if not str(error) else f"{label}: hata: {error}")
        return False


def ocr_file(args: argparse.Namespace, store) -> int:
    if not args.giris.is_file():
        raise UserError(f"Dosya bulunamadı: {args.giris}")
    if args.cikti.resolve() == args.giris.resolve():
        raise UserError("Giriş ve çıktı aynı dosya olamaz.")
    if args.cikti.exists() and not args.uzerine_yaz:
        raise UserError(
            f"Çıktı dosyası zaten var: {args.cikti} (üzerine yazmak için --uzerine-yaz)"
        )
    # Written beside the target and moved into place only when complete, so a failed run
    # never damages an existing output file.
    temporary = args.cikti.with_name(args.cikti.name + ".gecici")
    tessdata = default_tessdata()
    try:
        result = add_text_layer(args.giris, temporary, tessdata=tessdata, pdfa=not args.pdf)
        os.replace(temporary, args.cikti)
    except EngineUnavailable as error:
        raise UserError(str(error)) from None
    finally:
        temporary.unlink(missing_ok=True)
    kind = "PDF/A-2b" if result.pdfa else f"normal PDF: {result.note}" if result.note else "PDF"
    print(f"Metin katmanı eklendi: {args.cikti.name} ({kind})")
    print(f"OCR verisi: {'tur_best' if tessdata.folder else 'sistemdeki tur'}")
    return 0


def add_commands(commands: argparse._SubParsersAction) -> None:
    p = commands.add_parser("ocr", help="bir PDF'e aranabilir Türkçe metin katmanı ekler")
    p.add_argument("giris", type=Path, metavar="GIRIS.pdf", help="taranmış PDF")
    p.add_argument("cikti", type=Path, metavar="CIKTI.pdf", help="yazılacak PDF")
    p.add_argument("--pdf", action="store_true", help="PDF/A yerine normal PDF yaz")
    p.add_argument(
        "--uzerine-yaz", action="store_true", help="var olan çıktı dosyasının üzerine yaz"
    )
    p.set_defaults(handler=ocr_file)

    p = commands.add_parser("ocr-karsilastir", help="OCR motorlarını karşılaştırır, rapor yazar")
    p.add_argument("pdf", type=Path, nargs="*", help="gerçek taramalar (PDF)")
    p.add_argument("--sentetik", type=int, default=0, metavar="N", help="N sentetik sayfa kullan")
    p.add_argument("--tohum", type=int, default=1, help="sentetik sayfalar için tohum")
    p.add_argument(
        "--temiz", action="store_true", help="sentetik sayfalara tarama bozulması ekleme"
    )
    p.add_argument("--egim", type=float, default=0.7, help="sentetik sayfalarda en çok eğim (°)")
    p.add_argument(
        "--on-isleme",
        action="store_true",
        help="her motor için düzeltme ve siyah-beyaz ön işleme uygula",
    )
    p.add_argument("--kutular", type=Path, help="kutu ve beklenen metin listesi (JSON)")
    p.add_argument("--cikti", type=Path, required=True, help="rapor dosyası (.md)")
    p.set_defaults(handler=compare)

    p = commands.add_parser(
        "ocr-modelleri-indir",
        help="Türkçe OCR verilerini (tur_fast, tur, tur_best) ve varsa RapidOCR "
             "modellerini indirir",
    )
    p.set_defaults(handler=download_models)
