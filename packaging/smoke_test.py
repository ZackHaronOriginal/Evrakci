"""Smoke test for a built Evrakçı: make a synthetic scan, OCR it, check the text layer.

python packaging/smoke_test.py --komut build/evrakci/evrakci.exe --klasor TEMP
python packaging/smoke_test.py --komut python --modul --klasor TEMP   (source checkout)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# The Windows console code page (cp1252) cannot print Turkish letters: always write UTF-8.
for _stream in (sys.stdout, sys.stderr):
    _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from evrakci.pipeline.ocr.synthetic import find_font  # noqa: E402

TEXT = "Örnek Kayıt Şişli 2026"


def make_scan(path: Path) -> None:
    page = Image.new("L", (2480, 3508), 255)
    font = ImageFont.truetype(str(find_font()), 60)
    ImageDraw.Draw(page).text((236, 354), TEXT, fill=0, font=font)
    page.save(path, resolution=300)


def page_text(path: Path) -> str:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(path))
    try:
        return pdf[0].get_textpage().get_text_range()
    finally:
        pdf.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--komut", required=True, help="evrakci.exe, or python with --modul")
    parser.add_argument("--modul", action="store_true", help="run as python -m evrakci.cli")
    parser.add_argument("--klasor", type=Path, required=True)
    parser.add_argument("--beklenen-veri", help="e.g. tur_best: the OCR data that must be used")
    args = parser.parse_args()
    args.klasor.mkdir(parents=True, exist_ok=True)
    scan, out = args.klasor / "tarama.pdf", args.klasor / "cikti.pdf"
    make_scan(scan)
    out.unlink(missing_ok=True)
    command = [args.komut, "-c", "from evrakci.cli import main; raise SystemExit(main())"]
    if not args.modul:
        command = [args.komut]
    for extra in (["--version"], ["ocr", str(scan), str(out)]):
        result = subprocess.run(command + extra, capture_output=True, text=True, encoding="utf-8")
        print(result.stdout.strip())
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return 1
    if args.beklenen_veri and f"OCR verisi: {args.beklenen_veri}" not in result.stdout:
        print(f"Beklenen OCR verisi kullanılmadı: {args.beklenen_veri}", file=sys.stderr)
        return 1
    text = page_text(out)
    if TEXT not in text:
        print(f"Metin katmanı yanlış: {text!r}", file=sys.stderr)
        return 1
    print("Duman testi geçti")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
