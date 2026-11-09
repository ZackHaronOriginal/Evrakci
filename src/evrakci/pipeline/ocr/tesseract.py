"""Tesseract, run as an external program."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from evrakci.pipeline.ocr.engine import EngineUnavailable, Reading, Word, nfc, reading_from_words
from evrakci.pipeline.ocr.models import app_dir, data_dir


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


_HASHES: dict[tuple[str, int, int], str] = {}


def _file_hash(path: Path) -> str | None:
    """SHA-256 of a file, remembered until the file changes (data files are several MB)."""
    try:
        stat = path.stat()
    except OSError:
        return None
    key = (str(path), stat.st_size, stat.st_mtime_ns)
    if key not in _HASHES:
        _HASHES[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _HASHES[key]


def _file_matches(path: Path, sha256: str) -> bool:
    return path.is_file() and _file_hash(path) == sha256


def tessdata_dir(variant: str) -> Path:
    """Where a variant's data lives.

    Order: EVRAKCI_TESSDATA_<VARIANT>, then the copy bundled with the installed app (only if it
    verifies; bundled files are never deleted), then the app data folder.
    """
    configured = os.environ.get(f"EVRAKCI_TESSDATA_{variant.upper()}")
    if configured:
        return Path(configured)
    bundle = app_dir()
    if bundle is not None:
        bundled = bundle / f"tessdata_{variant}"
        if _file_matches(bundled / "tur.traineddata", TESSDATA_VARIANTS[variant].sha256):
            return bundled
    return data_dir() / f"tessdata_{variant}"


def verify_tessdata(variant: str, folder: Path | None = None) -> bool:
    """True if the folder holds the correct tur.traineddata.

    A wrong file is deleted only in the app's own download folder; a folder an admin
    configured, or the bundled copy, is never touched.
    """
    folder = Path(folder or tessdata_dir(variant))
    path = folder / "tur.traineddata"
    if not path.is_file():
        return False
    if _file_hash(path) == TESSDATA_VARIANTS[variant].sha256:
        return True
    if folder.resolve() == (data_dir() / f"tessdata_{variant}").resolve():
        path.unlink()
    return False


def tessdata_best_dir() -> Path:
    return tessdata_dir("best")


def verify_tur_best(folder: Path) -> bool:
    return verify_tessdata("best", folder)


def _windows_short_path(path: Path) -> Path:
    """Windows' 8.3 short form of a path (ASCII when short names are enabled)."""
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer)):  # type: ignore[attr-defined]
        return Path(buffer.value)
    return path


def ascii_safe_dir(
    folder: Path,
    windows: bool | None = None,
    short_path=None,
    copy_root: Path | None = None,
) -> Path:
    """A path to `folder` that Windows Tesseract can open.

    Tesseract on Windows fails on data folders with non-ASCII letters (C:\\Users\\Şükrü\\...).
    Try the short 8.3 path; if that is still not ASCII, use a copy under an ASCII folder.
    """
    folder = Path(folder)
    windows = os.name == "nt" if windows is None else windows
    if not windows or str(folder).isascii():
        return folder
    short = (short_path or _windows_short_path)(folder)
    if str(short).isascii():
        return short
    root = copy_root or ascii_copy_root()
    # Named after the data itself, so a new download never reuses an old copy.
    content = _file_hash(folder / "tur.traineddata")
    digest = (content or hashlib.sha256(str(folder).encode("utf-8")).hexdigest())[:12]
    target = root / f"tessdata-{digest}"
    if target.is_dir():
        if content is None or _file_hash(target / "tur.traineddata") == content:
            return target
        shutil.rmtree(target, ignore_errors=True)  # changed or planted: never reuse it
    # Copy beside the target, then rename: a half-finished copy is never handed out.
    root.mkdir(parents=True, exist_ok=True)
    partial = root / f"tessdata-{digest}-{uuid.uuid4().hex[:8]}.tmp"
    try:
        shutil.copytree(folder, partial)
        os.rename(partial, target)
    except OSError:
        if not target.is_dir():
            raise
    finally:
        shutil.rmtree(partial, ignore_errors=True)
    return target


def ascii_copy_root() -> Path:
    """Where ASCII-path copies go: EVRAKCI_ASCII_KOK, or a folder of this user's own.

    The folder sits under ProgramData/Evrakci (an ASCII path) but is named per user, so one
    user's scans and data are never mixed with another's on a shared office PC.
    """
    configured = os.environ.get("EVRAKCI_ASCII_KOK")
    if configured:
        return Path(configured)
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "kullanici"
    folder = "u-" + hashlib.sha256(user.casefold().encode("utf-8")).hexdigest()[:12]
    return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Evrakci" / folder


def system_tessdata() -> Path | None:
    """The language data folder of the installed Tesseract."""
    binary = find_tesseract()
    if binary is None:
        return None
    env = {k: v for k, v in os.environ.items() if k != "TESSDATA_PREFIX"}
    out = subprocess.run(
        [str(binary), "--list-langs"], capture_output=True, text=True, check=False, env=env
    ).stdout
    return tessdata_from_list_langs(out, binary)


def tessdata_from_list_langs(output: str, binary: Path) -> Path | None:
    """The data folder from `tesseract --list-langs`.

    Tesseract 5 names it on the first line; Tesseract 4 (e.g. Ubuntu 22.04) does not, so then
    the usual folders beside the program (…/share/tesseract-ocr/*/tessdata, …/share/tessdata)
    are tried.
    """
    first = output.splitlines()[0] if output else ""
    if first.count('"') >= 2:
        return Path(first.split('"')[1])
    share = Path(binary).resolve().parent.parent / "share"
    candidates = [*sorted(share.glob("tesseract-ocr/*/tessdata"), reverse=True),
                  share / "tessdata"]
    return next((c for c in candidates if (c / "configs" / "hocr").is_file()), None)


def prepare_tessdata(folder: Path) -> None:
    """Copy Tesseract's small output config folders into a separate data folder.

    Tesseract looks for its `hocr`, `txt` and `tsv` configs next to the language data.
    """
    if (folder / "configs" / "hocr").is_file():
        return
    source = system_tessdata()
    if source is not None:
        for name in ("configs", "tessconfigs"):
            if (source / name).is_dir() and not (folder / name).is_dir():
                shutil.copytree(source / name, folder / name)
    if not (folder / "configs" / "hocr").is_file():
        raise EngineUnavailable(f"Tesseract ayar dosyaları bulunamadı (configs): {folder}")


@dataclass(frozen=True)
class TessData:
    language: str
    folder: Path | None  # None: the system folder


def default_tessdata() -> TessData:
    """tur_best when it is installed and verified, otherwise the system's tur."""
    if find_tesseract() is None:  # no program: the caller reports "Tesseract bulunamadı"
        return TessData("tur", None)
    best = tessdata_best_dir()
    if verify_tur_best(best):
        prepare_tessdata(best)
        return TessData("tur", best)
    return TessData("tur", None)


def find_tesseract() -> Path | None:
    """EVRAKCI_TESSERACT, then the copy bundled with the app, then PATH, then usual folders."""
    configured = os.environ.get("EVRAKCI_TESSERACT")
    if configured and Path(configured).is_file():
        return Path(configured)
    bundle = app_dir()
    if bundle is not None:
        name = "tesseract.exe" if os.name == "nt" else "tesseract"
        if (bundle / "tesseract" / name).is_file():
            return bundle / "tesseract" / name
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
            command += ["--tessdata-dir", str(ascii_safe_dir(self.tessdata_dir))]
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
