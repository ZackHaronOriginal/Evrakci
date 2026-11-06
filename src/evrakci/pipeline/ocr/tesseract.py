"""Tesseract, run as an external program."""

from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from evrakci.pipeline.ocr.engine import EngineUnavailable, Reading, Word, nfc, reading_from_words

_WINDOWS_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]


def find_tesseract() -> Path | None:
    configured = os.environ.get("EVRAKCI_TESSERACT")
    if configured and Path(configured).is_file():
        return Path(configured)
    found = shutil.which("tesseract")
    if found:
        return Path(found)
    return next((p for p in _WINDOWS_PATHS if p.is_file()), None)


class TesseractEngine:
    def __init__(
        self, lang: str = "tur", tessdata_dir: Path | None = None, name: str = "tesseract-tur"
    ) -> None:
        self.lang = lang
        self.tessdata_dir = Path(tessdata_dir) if tessdata_dir else None
        self.name = name
        self._checked = False
        self._reason: str | None = None

    def available(self) -> str | None:
        if not self._checked:
            self._reason = self._check()
            self._checked = True
        return self._reason

    def _check(self) -> str | None:
        binary = find_tesseract()
        if binary is None:
            return "Tesseract programı bulunamadı"
        if self.tessdata_dir is not None:
            if not (self.tessdata_dir / f"{self.lang}.traineddata").is_file():
                return f"'{self.lang}' dil verisi bulunamadı: {self.tessdata_dir}"
            return None
        result = subprocess.run(
            [str(binary), "--list-langs"], capture_output=True, text=True, check=False
        )
        languages = result.stdout.split()
        if self.lang not in languages:
            return f"'{self.lang}' dil verisi kurulu değil"
        return None

    def _run(self, image: Image.Image, psm: int) -> list[Word]:
        reason = self.available()
        if reason:
            raise EngineUnavailable(reason)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        command = [str(find_tesseract()), "stdin", "stdout", "-l", self.lang, "--psm", str(psm)]
        if self.tessdata_dir is not None:
            command += ["--tessdata-dir", str(self.tessdata_dir)]
        command.append("tsv")
        result = subprocess.run(command, input=buffer.getvalue(), capture_output=True, check=False)
        if result.returncode != 0:
            message = result.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            raise EngineUnavailable(f"Tesseract hata verdi: {' '.join(message)}")
        rows = csv.DictReader(
            io.StringIO(result.stdout.decode("utf-8")), delimiter="\t", quoting=csv.QUOTE_NONE
        )
        words = []
        for row in rows:
            text = (row.get("text") or "").strip()
            if row.get("level") != "5" or not text:
                continue
            left, top = int(row["left"]), int(row["top"])
            box = (left, top, left + int(row["width"]), top + int(row["height"]))
            words.append(Word(nfc(text), box, max(float(row["conf"]), 0.0) / 100))
        return words

    def read_page(self, image: Image.Image) -> list[Word]:
        return self._run(image, psm=3)

    def read_region(self, image: Image.Image) -> Reading:
        return reading_from_words(self._run(image, psm=6))
