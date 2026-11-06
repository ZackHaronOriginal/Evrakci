"""Add a searchable Turkish text layer to a PDF, saved as PDF/A-2b without Ghostscript."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import ocrmypdf
from ocrmypdf import exceptions

from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.tesseract import TessData, default_tessdata, find_tesseract

PDFA_FALLBACK_NOTE = "PDF/A doğrulanamadı; normal PDF yazıldı"


@dataclass(frozen=True)
class TextLayerResult:
    path: Path
    pdfa: bool
    note: str | None = None


@contextmanager
def _tessdata_prefix(folder: Path | None):
    """Point Tesseract at a separate data folder for the duration of one call."""
    if folder is None:
        yield
        return
    previous = os.environ.get("TESSDATA_PREFIX")
    os.environ["TESSDATA_PREFIX"] = str(folder)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TESSDATA_PREFIX", None)
        else:
            os.environ["TESSDATA_PREFIX"] = previous


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
        raise EngineUnavailable(f"Eksik program: {error}") from error
    except exceptions.ExitCodeException as error:
        raise EngineUnavailable(f"Metin katmanı eklenemedi: {src.name} ({error})") from error
    return TextLayerResult(dst, pdfa=pdfa)
