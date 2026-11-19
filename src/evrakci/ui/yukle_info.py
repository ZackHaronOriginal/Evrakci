"""What the Yükle tab says about a job: batch rows, the pre-flight counts and the scan profile.

Pure functions over the core's `Job` (no Qt), so the numbers are easy to test. The tab only
paints them: the batch table, the "Ön kontrol" card, the one-sentence reason in the inspector
head and the scan profile read from the PDFs themselves.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from evrakci.pipeline.cuts import Document
from evrakci.pipeline.job import Job, parse_page_id

# FPDF_COLORSPACE_* (pdfium): the only values scanners produce in practice
_GRAY, _RGB, _CMYK = 1, 2, 3


@dataclass(frozen=True)
class BatchSummary:
    id: str
    name: str
    pages: int
    qr: int
    status: str  # "hazir" | "kontrol"


@dataclass(frozen=True)
class JobSummary:
    name: str
    pages: int
    qr: int
    documents: int
    checks: int  # documents that need a look (Kontrol)
    batches: tuple[BatchSummary, ...]
    reason: str

    @property
    def parties(self) -> int:
        return len(self.batches)


def ordinals(numbers: list[int]) -> str:
    """"2." / "2. ve 4." / "2., 3. ve 5." (Turkish ordinals are the number and a dot)."""
    parts = [f"{n}." for n in numbers]
    if len(parts) <= 1:
        return "".join(parts)
    return ", ".join(parts[:-1]) + " ve " + parts[-1]


def reason(qr_by_batch: list[int]) -> str:
    """One sentence on how the batches will be split: which have QR separators, which not."""
    if not qr_by_batch:
        return "Henüz parti yok. Dosya ekleyin ya da PDF'leri pencereye bırakın."
    without = [i for i, qr in enumerate(qr_by_batch, start=1) if qr == 0]
    with_qr = len(qr_by_batch) - len(without)
    if not without:
        return ("Parti QR ayıraçlı." if len(qr_by_batch) == 1
                else f"{len(qr_by_batch)} partinin hepsi QR ayıraçlı.")
    if with_qr == 0:
        return ("Partilerde QR ayıraç yok; belgeleri Kontrol'de filtreyle ya da elle bölün."
                if len(qr_by_batch) > 1
                else "Partide QR ayıraç yok; belgeleri Kontrol'de filtreyle ya da elle bölün.")
    return (f"{with_qr} parti QR ayıraçlı; {ordinals(without)} "
            f"{'partide' if len(without) == 1 else 'partilerde'} ayıraç yok, "
            "Kontrol'de filtreyle bölebilirsiniz.")


def summarize(job: Job, documents: list[Document],
              checked: Iterable[Document] = ()) -> JobSummary:
    """Counts for the open job. `checked` are the documents that need a Kontrol (the export
    plan's checks); a batch with checks, or with no QR separator at all, is marked Kontrol."""
    checked = list(checked)
    flagged = {parse_page_id(d.page_ids[0])[0] for d in checked if d.page_ids}
    checks = len(checked)
    rows = []
    for batch in job.batches:
        qr = sum(1 for i in range(batch.page_count)
                 if job.pages[f"{batch.id}/{i}"].is_separator)
        status = "kontrol" if qr == 0 or batch.id in flagged else "hazir"
        rows.append(BatchSummary(batch.id, batch.file_name, batch.page_count, qr, status))
    return JobSummary(job.name, sum(b.pages for b in rows), sum(b.qr for b in rows),
                      len(documents), checks, tuple(rows), reason([b.qr for b in rows]))


# -- scan profile -----------------------------------------------------------------------
@dataclass(frozen=True)
class ScanProfile:
    title: str  # "300 dpi, siyah-beyaz"
    detail: str  # "A4, dosyalardan okundu"


def paper_name(width_pt: float, height_pt: float) -> str:
    """"A4" for a page within 3 mm of 210 x 297 (either way up), else "W × H mm"."""
    w, h = sorted((width_pt / 72 * 25.4, height_pt / 72 * 25.4))
    for name, (pw, ph) in (("A4", (210, 297)), ("A3", (297, 420)), ("A5", (148, 210))):
        if math.isclose(w, pw, abs_tol=3) and math.isclose(h, ph, abs_tol=3):
            return name
    return f"{round(w)} × {round(h)} mm"


def scan_profile(path: Path) -> ScanProfile | None:
    """Resolution, colour mode and paper of the first page's scan image, from the file itself.

    None when the file has no scan image on its first page (a text PDF) or cannot be read."""
    try:
        import pypdfium2 as pdfium
        import pypdfium2.raw as raw

        from evrakci.pipeline.pdfium_lock import PDFIUM_LOCK

        with PDFIUM_LOCK:
            pdf = pdfium.PdfDocument(str(path))
            try:
                page = pdf[0]
                try:
                    size = page.get_size()
                    images = [o.get_metadata() for o in page.get_objects(
                        filter=[raw.FPDF_PAGEOBJ_IMAGE])]
                finally:
                    page.close()
            finally:
                pdf.close()
    except Exception:  # noqa: BLE001 - an unreadable file just has no profile
        return None
    if not images:
        return None
    meta = max(images, key=lambda m: m.width * m.height)
    dpi = round(max(meta.horizontal_dpi, meta.vertical_dpi) / 10) * 10 or 0
    if meta.colorspace == _RGB or meta.colorspace == _CMYK:
        mode = "renkli"
    elif meta.bits_per_pixel == 1:
        mode = "siyah-beyaz"
    elif meta.colorspace == _GRAY or meta.bits_per_pixel:
        mode = "gri tonlamalı"
    else:
        mode = ""
    title = ", ".join(part for part in (f"{dpi} dpi" if dpi else "", mode) if part)
    if not title:
        return None
    return ScanProfile(title, f"{paper_name(*size)}, dosyalardan okundu")
