"""Add a searchable Turkish text layer to a PDF, saved as PDF/A-2b without Ghostscript."""

from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import ocrmypdf
from ocrmypdf import exceptions

from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.tesseract import (
    TessData,
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


@contextmanager
def _tessdata_prefix(folder: Path | None):
    """For one call: point Tesseract at its data, and put the Tesseract we found first on PATH.

    OCRmyPDF finds Tesseract only through PATH, and the copy bundled with the installed app
    is never on PATH. Both variables are process-wide, so changes are made under a lock.
    """
    with _ENV_LOCK:
        previous = {name: os.environ.get(name) for name in ("TESSDATA_PREFIX", "PATH")}
        if folder is not None:
            os.environ["TESSDATA_PREFIX"] = str(folder)
        binary = find_tesseract()
        if binary is not None:
            os.environ["PATH"] = os.pathsep.join([str(binary.parent), previous["PATH"] or ""])
        try:
            yield
        finally:
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
            mode="skip",  # pages that already have text keep it
            jobs=jobs,
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
    if tessdata.folder is not None:
        prepare_tessdata(tessdata.folder)
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        try:
            code = _run(src, dst, tessdata, "pdfa-2" if pdfa else "pdf", jobs)
        except exceptions.PdfaConversionFailedError:
            code = ocrmypdf.ExitCode.pdfa_conversion_failed
        if pdfa and code == ocrmypdf.ExitCode.pdfa_conversion_failed:
            dst.unlink(missing_ok=True)
            code = _run(src, dst, tessdata, "pdf", jobs)
            if code != ocrmypdf.ExitCode.ok:
                raise EngineUnavailable(f"Metin katmanı eklenemedi: {src.name} (kod {code})")
            return TextLayerResult(dst, pdfa=False, note=PDFA_FALLBACK_NOTE)
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
    return TextLayerResult(dst, pdfa=pdfa)
