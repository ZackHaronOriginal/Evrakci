"""Add a searchable Turkish text layer to a PDF, saved as PDF/A-2b without Ghostscript."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import ocrmypdf
from ocrmypdf import exceptions

from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.tesseract import (
    TessData,
    ascii_copy_root,
    ascii_safe_dir,
    default_tessdata,
    find_tesseract,
    prepare_tessdata,
)

PDFA_FALLBACK_NOTE = "PDF/A doğrulanamadı; normal PDF yazıldı"

# OCRmyPDF logs warnings in English to the console; staff only see our Turkish messages.
logging.getLogger("ocrmypdf").setLevel(logging.ERROR)

# TESSDATA_PREFIX is process-wide, so only one text-layer call may change it at a time.
_ENV_LOCK = threading.Lock()


@dataclass(frozen=True)
class TextLayerResult:
    path: Path
    pdfa: bool
    note: str | None = None


def ascii_temp_dir(
    windows: bool | None = None, current: str | None = None, root: Path | None = None
) -> Path | None:
    """A fresh ASCII temp folder when the user's temp folder has non-ASCII letters (Windows).

    OCRmyPDF passes temp file paths to Tesseract, which cannot open non-ASCII paths on Windows.
    Each run gets its own folder that only this user can open; the caller removes it.
    """
    windows = os.name == "nt" if windows is None else windows
    current = tempfile.gettempdir() if current is None else current
    if not windows or current.isascii():
        return None
    parent = (root or ascii_copy_root()) / "tmp"
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="ocr-", dir=parent))


@contextmanager
def _tessdata_prefix(folder: Path | None):
    """For one call: point Tesseract at its data, and put the Tesseract we found first on PATH.

    OCRmyPDF finds Tesseract only through PATH, and the copy bundled with the installed app
    is never on PATH. Both variables are process-wide, so changes are made under a lock.
    """
    with _ENV_LOCK:
        names = ("TESSDATA_PREFIX", "PATH", "TEMP", "TMP")
        previous = {name: os.environ.get(name) for name in names}
        previous_tempdir = tempfile.tempdir
        temp = ascii_temp_dir()
        if temp is not None:
            os.environ["TEMP"] = os.environ["TMP"] = str(temp)
            # Process-wide: other threads also use this folder while OCR runs (harmless).
            tempfile.tempdir = str(temp)
        if folder is not None:
            os.environ["TESSDATA_PREFIX"] = str(ascii_safe_dir(folder))
        binary = find_tesseract()
        if binary is not None:
            os.environ["PATH"] = os.pathsep.join([str(binary.parent), previous["PATH"] or ""])
        try:
            yield
        finally:
            if temp is not None:  # page images of scans never stay behind
                shutil.rmtree(temp, ignore_errors=True)
            tempfile.tempdir = previous_tempdir
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def _run(src: Path, dst: Path, tessdata: TessData, output_type: str, jobs: int | None):
    with _tessdata_prefix(tessdata.folder):
        return ocrmypdf.ocr(
            src,
            dst,
            language=tessdata.language,
            output_type=output_type,
            pdfa_backend="internal",  # never Ghostscript
            rasterizer="pypdfium",  # never Ghostscript
            optimize=0,  # the optimizer would ask Ghostscript for its version; scans stay as is
            # Scanners' own hidden text (often wrong on Turkish letters) is read again in
            # Turkish; visible text in born-digital pages is kept.
            mode="redo",
            jobs=jobs,
            # Threads by default; EVRAKCI_OCR_SURECLER=1 uses worker processes instead (the
            # Windows smoke test checks that the frozen app can start them).
            use_threads=os.environ.get("EVRAKCI_OCR_SURECLER") != "1",
            progress_bar=False,
        )


def add_text_layer(
    src: Path,
    dst: Path,
    tessdata: TessData | None = None,
    pdfa: bool = True,
    jobs: int | None = None,
) -> TextLayerResult:
    src, dst = Path(src), Path(dst)
    if find_tesseract() is None:
        raise EngineUnavailable("Tesseract bulunamadı")
    tessdata = tessdata or default_tessdata()
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        if tessdata.folder is not None:
            prepare_tessdata(tessdata.folder)
        reason = ""
        try:
            code = _run(src, dst, tessdata, "pdfa-2" if pdfa else "pdf", jobs)
        except exceptions.PdfaConversionFailedError as error:
            code = ocrmypdf.ExitCode.pdfa_conversion_failed
            reason = " ".join(str(error).split())[:200]
        if pdfa and code == ocrmypdf.ExitCode.pdfa_conversion_failed:
            dst.unlink(missing_ok=True)
            code = _run(src, dst, tessdata, "pdf", jobs)
            if code != ocrmypdf.ExitCode.ok:
                raise EngineUnavailable(f"Metin katmanı eklenemedi: {src.name} (kod {code})")
            note = f"{PDFA_FALLBACK_NOTE} ({reason})" if reason else PDFA_FALLBACK_NOTE
            return TextLayerResult(dst, pdfa=False, note=note)
        if code != ocrmypdf.ExitCode.ok:
            raise EngineUnavailable(f"Metin katmanı eklenemedi: {src.name} (kod {code})")
    except exceptions.EncryptedPdfError as error:
        raise EngineUnavailable(f"PDF şifreli: {src.name}") from error
    except exceptions.MissingDependencyError as error:
        raise EngineUnavailable(f"Gerekli bir program eksik: {error}") from error
    except (exceptions.InputFileError, exceptions.BadArgsError) as error:
        raise EngineUnavailable(f"PDF okunamadı veya bozuk: {src.name}") from error
    except exceptions.ExitCodeException as error:
        detail = f" ({error})" if str(error).strip() else ""
        raise EngineUnavailable(f"Metin katmanı eklenemedi: {src.name}{detail}") from error
    except EngineUnavailable:
        raise
    except Exception as error:  # anything else inside OCRmyPDF/pikepdf: a clear Turkish message
        raise EngineUnavailable(f"Metin katmanı eklenemedi: {src.name} ({error})") from error
    return TextLayerResult(dst, pdfa=pdfa)
