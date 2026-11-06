"""`evrakci ocr-karsilastir` and `evrakci ocr-modelleri-indir`."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

import pypdfium2 as pdfium

from evrakci.cli.errors import UserError
from evrakci.pipeline.ocr.compare import compare_synthetic, install_sizes, render_report
from evrakci.pipeline.ocr.engine import EngineUnavailable, OcrEngine
from evrakci.pipeline.ocr.metrics import exact
from evrakci.pipeline.ocr.models import data_dir, ensure_model, official_model
from evrakci.pipeline.ocr.rapid import RapidOcrEngine
from evrakci.pipeline.ocr.synthetic import make_pages
from evrakci.pipeline.ocr.tesseract import TesseractEngine

_DPI = 300
_TUR_BEST_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/tur.traineddata"
_MODELS = [
    ("PP-OCRv5", "det", "ch_PP-OCRv5_det_mobile"),
    ("PP-OCRv5", "rec", "latin_PP-OCRv5_rec_mobile"),
    ("PP-OCRv6", "rec", "multi_PP-OCRv6_rec_small"),
]
_SYNTHETIC_NOTES = [
    "Sayfalar sentetiktir: kelimeler uydurmadır. Sözlük bilgisi kullanan motorlar (Tesseract) "
    "gerçek metinde biraz daha iyi sonuç verebilir.",
    "Kurulum boyutları yaklaşıktır. Linux'ta Tesseract için yalnızca program ve dil dosyası "
    "sayılır; Windows'ta tüm Tesseract-OCR klasörü sayılır.",
    "Saniye/sayfa: tam sayfa okuma süresi, 300 dpi A4, bu bilgisayarda.",
]


def all_engines() -> list[OcrEngine]:
    return [
        TesseractEngine("tur", name="tesseract-tur"),
        TesseractEngine(
            "tur", tessdata_dir=data_dir() / "tessdata_best", name="tesseract-tur_best"
        ),
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
            if len(box["kutu_mm"]) != 4 or int(box["sayfa"]) < 1:
                raise ValueError("kutu_mm veya sayfa hatalı")
            str(box["pdf"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise UserError(f"Kutu dosyası okunamadı: {path.name} ({error})") from None
    return boxes


def _box_pixels(box_mm: list[float], size: tuple[int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (round(float(v) / 25.4 * _DPI) for v in box_mm)
    if not (0 <= x0 < x1 <= size[0] and 0 <= y0 < y1 <= size[1]):
        raise UserError(f"Kutu sayfanın dışında: {box_mm}")
    return x0, y0, x1, y1


def _real_report(pdfs: list[Path], boxes: list[dict], engines: list[OcrEngine]) -> str:
    pages = {path.name: _render_pages(path) for path in pdfs}
    for box in boxes:
        images = pages.get(Path(box["pdf"]).name)
        if images is None or int(box["sayfa"]) > len(images):
            raise UserError(f"Kutudaki PDF veya sayfa yok: {box['pdf']} sayfa {box['sayfa']}")
        box["_px"] = _box_pixels(box["kutu_mm"], images[int(box["sayfa"]) - 1].size)

    usable = []
    lines = ["# OCR motor karşılaştırması: gerçek taramalar", ""]
    lines += ["| Motor | Saniye/sayfa | Kutularda tam doğru |", "|---|---|---|"]
    texts: dict[str, dict[tuple[str, int], str]] = {}
    readings: dict[str, list[str]] = {}
    for engine in engines:
        reason = engine.available()
        if reason:
            lines.append(f"| {engine.name} | kullanılamıyor: {reason} | |")
            continue
        usable.append(engine)
        seconds, count = 0.0, 0
        texts[engine.name] = {}
        for name, images in pages.items():
            for number, image in enumerate(images, start=1):
                started = time.perf_counter()
                words = engine.read_page(image)
                seconds += time.perf_counter() - started
                count += 1
                texts[engine.name][(name, number)] = " ".join(w.text for w in words)[:400]
        readings[engine.name] = [
            engine.read_region(pages[Path(b["pdf"]).name][int(b["sayfa"]) - 1].crop(b["_px"])).text
            for b in boxes
        ]
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
            cells = [readings[e.name][i] or "(boş)" for e in usable]
            lines.append(
                f"| {box['pdf']} | {box['sayfa']} | {box.get('beklenen', '')} | "
                + " | ".join(cells)
                + " |"
            )
    for name, images in pages.items():
        for number in range(1, len(images) + 1):
            lines += ["", f"## {name}, sayfa {number}", ""]
            for engine in usable:
                lines.append(f"- **{engine.name}:** {texts[engine.name][(name, number)]}")
    return "\n".join(lines) + "\n"


def compare(args: argparse.Namespace, store) -> int:
    engines = all_engines()
    if args.sentetik:
        pages = make_pages(args.sentetik, seed=args.tohum, degrade=not args.temiz)
        title = f"OCR motor karşılaştırması: {args.sentetik} sentetik sayfa (tohum {args.tohum})"
        notes = list(_SYNTHETIC_NOTES)
        if args.temiz:
            notes.insert(0, "Sayfalar temiz (tarama bozulması eklenmedi).")
        report = render_report(compare_synthetic(engines, pages), install_sizes(), title, notes)
    else:
        if not args.pdf:
            raise UserError("PDF dosyası veya --sentetik verin.")
        boxes = _load_boxes(args.kutular) if args.kutular else []
        report = _real_report(args.pdf, boxes, engines)
    args.cikti.parent.mkdir(parents=True, exist_ok=True)
    args.cikti.write_text(report, encoding="utf-8")
    print(f"Rapor yazıldı: {args.cikti}")
    return 0


def download_models(args: argparse.Namespace, store) -> int:
    for version, kind, key in _MODELS:
        try:
            path = ensure_model(official_model(version, kind, key))
            print(f"{key}: hazır ({path})")
        except (EngineUnavailable, ImportError, KeyError) as error:
            print(f"{key}: hata: {error}")
    target = data_dir() / "tessdata_best" / "tur.traineddata"
    if target.is_file():
        print(f"tur_best: hazır ({target})")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".part")
        try:
            with urllib.request.urlopen(_TUR_BEST_URL, timeout=120) as response:
                partial.write_bytes(response.read())
            partial.replace(target)
            print(f"tur_best: indirildi ({target})")
        except OSError as error:
            partial.unlink(missing_ok=True)
            print(f"tur_best: hata: {error}")
    return 0


def add_commands(commands: argparse._SubParsersAction) -> None:
    p = commands.add_parser("ocr-karsilastir", help="OCR motorlarını karşılaştırır, rapor yazar")
    p.add_argument("pdf", type=Path, nargs="*", help="gerçek taramalar (PDF)")
    p.add_argument("--sentetik", type=int, default=0, metavar="N", help="N sentetik sayfa kullan")
    p.add_argument("--tohum", type=int, default=1, help="sentetik sayfalar için tohum")
    p.add_argument(
        "--temiz", action="store_true", help="sentetik sayfalara tarama bozulması ekleme"
    )
    p.add_argument("--kutular", type=Path, help="kutu ve beklenen metin listesi (JSON)")
    p.add_argument("--cikti", type=Path, required=True, help="rapor dosyası (.md)")
    p.set_defaults(handler=compare)

    p = commands.add_parser(
        "ocr-modelleri-indir", help="RapidOCR modellerini ve tur_best verisini indirir"
    )
    p.set_defaults(handler=download_models)
