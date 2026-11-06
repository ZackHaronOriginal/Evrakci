"""`evrakci ocr-karsilastir` and `evrakci ocr-modelleri-indir`."""

from __future__ import annotations

import argparse
import json
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
    TUR_BEST_URL,
    TesseractEngine,
    prepare_tessdata,
    tessdata_best_dir,
    verify_tur_best,
)

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
        TesseractEngine("tur", name="tesseract-tur"),
        TesseractEngine("tur", tessdata_dir=tessdata_best_dir(), name="tesseract-tur_best"),
        RapidOcrEngine(),
        RapidOcrEngine("multi_PP-OCRv6_rec_small", "PP-OCRv6", name="rapidocr-v6-multi"),
    ]


def _render_pages(path: Path) -> list:
    if not path.is_file():
        raise UserError(f"Dosya bulunamadı: {path.name}")
    try:
        pdf = pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError:
        raise UserError(f"PDF açılamadı: {path.name}") from None
    try:
        images = []
        for index in range(len(pdf)):
            page = pdf[index]
            try:
                images.append(page.render(scale=_DPI / 72, grayscale=True).to_pil().convert("L"))
            finally:
                page.close()
        return images
    finally:
        pdf.close()


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
    pages = {path.name: _render_pages(path) for path in pdfs}
    for box in boxes:
        images = pages.get(Path(box["pdf"]).name)
        if images is None or int(box["sayfa"]) > len(images):
            raise UserError(f"Kutudaki PDF veya sayfa yok: {box['pdf']} sayfa {box['sayfa']}")
        box["_px"] = _box_pixels(box["kutu_mm"], images[int(box["sayfa"]) - 1].size)

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
    for name, images in pages.items():
        for number in range(1, len(images) + 1):
            lines += ["", f"## {name}, sayfa {number}", ""]
            for engine in usable:
                lines.append(f"- **{engine.name}:** {texts[engine.name][(name, number)]}")
    return "\n".join(lines) + "\n"


def _read_all(
    engine: OcrEngine,
    pages: dict[str, list],
    boxes: list[dict],
    texts: dict[str, dict[tuple[str, int], str]],
    readings: dict[str, list[str]],
    preprocess: bool,
) -> tuple[float, int]:
    """Read every page and box with one engine. Returns (seconds, pages read)."""
    first = next(iter(pages.values()))[0]
    engine.read_region(first.crop((0, 0, min(400, first.width), min(100, first.height))))  # warm-up
    seconds, count = 0.0, 0
    page_texts = {}
    for name, images in pages.items():
        for number, image in enumerate(images, start=1):
            prepared = prepare_page(image) if preprocess else image
            started = time.perf_counter()
            words = engine.read_page(prepared)
            seconds += time.perf_counter() - started
            count += 1
            page_texts[(name, number)] = " ".join(w.text for w in words)[:400]
    box_readings = []
    for box in boxes:
        crop = pages[Path(box["pdf"]).name][box["sayfa"] - 1].crop(box["_px"])
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
        except (EngineUnavailable, ImportError, KeyError) as error:
            failed = True
            print(f"{key}: hata: {error}")
    folder = data_dir_for_tur_best()
    target = folder / "tur.traineddata"
    if verify_tur_best(folder):
        prepare_tessdata(folder)
        print(f"tur_best: hazır ({target})")
    else:
        folder.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".part")
        try:
            with urllib.request.urlopen(_TUR_BEST_URL, timeout=120) as response:
                partial.write_bytes(response.read())
            partial.replace(target)
            if not verify_tur_best(folder):
                raise OSError("indirilen dosya doğrulanamadı")
            prepare_tessdata(folder)
            print(f"tur_best: indirildi ({target})")
        except OSError as error:
            partial.unlink(missing_ok=True)
            failed = True
            print(f"tur_best: hata: {error}")
    return 1 if failed else 0


def data_dir_for_tur_best() -> Path:
    return tessdata_best_dir()


def add_commands(commands: argparse._SubParsersAction) -> None:
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
        "ocr-modelleri-indir", help="RapidOCR modellerini ve tur_best verisini indirir"
    )
    p.set_defaults(handler=download_models)
