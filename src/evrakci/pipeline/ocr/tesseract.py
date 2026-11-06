"""Tesseract, run as an external program."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from evrakci.pipeline.ocr.engine import EngineUnavailable, Reading, Word, nfc, reading_from_words
from evrakci.pipeline.ocr.models import data_dir


@dataclass(frozen=True)
class TessDataVariant:
    url: str
    sha256: str


_RAW = "https://raw.githubusercontent.com/tesseract-ocr"
# The three official Turkish data files from the Tesseract project (unchanged upstream for years).
# Linux packages and many installers ship "fast" as plain "tur".
TESSDATA_VARIANTS = {
    "fast": TessDataVariant(
        f"{_RAW}/tessdata_fast/main/tur.traineddata",
        "7393381111e1152420fc4092cb44eef4237580d21b92bf30d7d221aad192c6b7",
    ),
    "standard": TessDataVariant(
        f"{_RAW}/tessdata/main/tur.traineddata",
        "489b9504e80d7184ed1ac9a1976647884ee71149da231ff3c2c1dc15370f2f3d",
    ),
    "best": TessDataVariant(
        f"{_RAW}/tessdata_best/main/tur.traineddata",
        "e0c3338dc17503dc7d335a507c9ae01b2b46cfd07561171e1e1ac55d85e8e438",
    ),
}
TUR_BEST_SHA256 = TESSDATA_VARIANTS["best"].sha256
TUR_BEST_URL = TESSDATA_VARIANTS["best"].url

_WINDOWS_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]


def tessdata_dir(variant: str) -> Path:
    """Where a variant's data lives: EVRAKCI_TESSDATA_<VARIANT>, or the app data folder."""
    configured = os.environ.get(f"EVRAKCI_TESSDATA_{variant.upper()}")
    return Path(configured) if configured else data_dir() / f"tessdata_{variant}"


def verify_tessdata(variant: str, folder: Path | None = None) -> bool:
    """True if the folder holds the correct tur.traineddata. A wrong file is deleted."""
    path = (folder or tessdata_dir(variant)) / "tur.traineddata"
    if not path.is_file():
        return False
    if hashlib.sha256(path.read_bytes()).hexdigest() == TESSDATA_VARIANTS[variant].sha256:
        return True
    path.unlink()
    return False


def tessdata_best_dir() -> Path:
    return tessdata_dir("best")


def verify_tur_best(folder: Path) -> bool:
    return verify_tessdata("best", folder)


def system_tessdata() -> Path | None:
    """The language data folder of the installed Tesseract."""
    binary = find_tesseract()
    if binary is None:
        return None
    out = subprocess.run(
        [str(binary), "--list-langs"], capture_output=True, text=True, check=False
    ).stdout
    first = out.splitlines()[0] if out else ""
    return Path(first.split('"')[1]) if first.count('"') >= 2 else None


def prepare_tessdata(folder: Path) -> None:
    """Copy Tesseract's small output config folders into a separate data folder.

    Tesseract looks for its `hocr`, `txt` and `tsv` configs next to the language data.
    """
    source = system_tessdata()
    if source is None:
        return
    for name in ("configs", "tessconfigs"):
        if (source / name).is_dir() and not (folder / name).is_dir():
            shutil.copytree(source / name, folder / name)


@dataclass(frozen=True)
class TessData:
    language: str
    folder: Path | None  # None: the system folder


def default_tessdata() -> TessData:
    """tur_best when it is installed and verified, otherwise the system's tur."""
    best = tessdata_best_dir()
    if verify_tur_best(best):
        prepare_tessdata(best)
        return TessData("tur", best)
    return TessData("tur", None)


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
        command += ["-c", "tessedit_create_tsv=1"]  # works without the "tsv" config file
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


def default_engine() -> TesseractEngine:
    data = default_tessdata()
    name = "tesseract-tur_best" if data.folder else "tesseract-tur"
    return TesseractEngine(data.language, tessdata_dir=data.folder, name=name)
