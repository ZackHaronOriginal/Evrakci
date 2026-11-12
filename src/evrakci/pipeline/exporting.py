"""Run an export: write the named PDFs, add the text layer, write index.xlsx.

The command line and the window both call `export_job`, so they always do the same thing.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pikepdf

from evrakci.pipeline.export import ExportItem, plan_export
from evrakci.pipeline.index import write_index
from evrakci.pipeline.job import Job
from evrakci.pipeline.naming import fit_names, unique_names
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.textlayer import add_text_layer
from evrakci.pipeline.templates.model import Template
from evrakci.pipeline.writer import write_documents

Progress = Callable[[str, int, int], None]  # stage ("write" | "layer"), done, total


class ExportError(Exception):
    """The export stopped; the message (Turkish) says what was written and what was not."""


@dataclass
class ExportResult:
    items: list[ExportItem]
    paths: list[Path]
    # Per file with a text layer: (is PDF/A, note when it is not)
    notes: dict[Path, tuple[bool, str | None]] = field(default_factory=dict)
    index_written: bool = False
    with_layer: bool = False  # every file got the searchable text layer

    @property
    def needing_check(self) -> int:
        return sum(1 for item in self.items if item.checks)


def export_job(
    job: Job,
    batch_files: Mapping[str, Path],
    templates: Mapping[str, Template | None],
    out_dir: Path,
    with_layer: bool = True,
    progress: Progress | None = None,
    engine=None,
    add_layer=add_text_layer,
    tessdata=None,
) -> ExportResult:
    """Raises EngineUnavailable before writing anything if the text layer cannot be made."""
    out_dir = Path(out_dir)
    if out_dir.exists() and not out_dir.is_dir():
        raise ExportError(f"Hedef bir klasör değil, bir dosya: {out_dir}. Bir klasör seçin.")
    items = plan_export(job, templates)
    try:
        fitted = fit_names([i.name for i in items], out_dir)
    except ValueError as error:
        raise ExportError(str(error)) from None
    for item, name in zip(items, fitted, strict=True):
        if name == item.name:
            continue
        if len(name) < item.keep:  # a required value would be cut: never silently
            item.checks.append("zorunlu değer dosya adına sığmadı (klasör yolu uzun)")
            name = f"belge_{item.number:03d}"
        else:
            item.checks.append("dosya adı kısaltıldı (klasör yolu uzun)")
        item.name = name
    for item, name in zip(items, unique_names([i.name for i in items]), strict=True):
        item.name = name
    if with_layer and items:
        if engine is None:
            from evrakci.pipeline.ocr.tesseract import default_engine

            engine = default_engine()
        reason = engine.available()
        if reason:
            raise EngineUnavailable(reason)
    report = progress or (lambda stage, done, total: None)
    report("write", 0, len(items))
    def written_so_far() -> str:
        names = sorted(p.name for p in out_dir.glob("*.pdf")) if out_dir.is_dir() else []
        return ", ".join(names) or "yok"

    try:
        paths = write_documents(
            [i.document for i in items], batch_files, job.rotations, out_dir,
            names=[i.name for i in items],
            progress=lambda done, total: report("write", done, total),
        )
    except FileExistsError as error:
        raise ExportError(
            f"Çıktı klasöründe önceki bir dışa aktarımdan dosya var ({error}): {out_dir}. "
            "Lütfen boş bir klasör seçin."
        ) from None
    except OSError as error:
        raise ExportError(
            f"Dosyalar yazılamadı ({error.strerror or error}). Yazılanlar: {written_so_far()}. "
            "index.xlsx yazılmadı; yer açıp boş bir klasöre yeniden dışa aktarın."
        ) from None
    except (pikepdf.PdfError, KeyError, IndexError) as error:
        raise ExportError(
            f"Taranan dosyalardan biri okunamadı ({error}). Yazılanlar: {written_so_far()}. "
            "index.xlsx yazılmadı; işin partilerini kontrol edin."
        ) from None
    result = ExportResult(items, paths, with_layer=with_layer and bool(paths))
    if with_layer and paths:
        for number, (path, item) in enumerate(zip(paths, items, strict=True), start=1):
            report("layer", number - 1, len(paths))
            # The original stays in place until the layered copy is complete.
            layered = path.with_name(path.name + ".gecici")
            try:
                layer = add_layer(path, layered, tessdata=tessdata)
                os.replace(layered, path)
            except (EngineUnavailable, OSError) as error:
                done = ", ".join(p.name for p in paths[: number - 1]) or "yok"
                for later in items[number - 1:]:
                    later.checks.append("metin katmanı eklenmedi")
                index_note = _write_index_quietly(items, job, out_dir)
                raise ExportError(
                    f"{path.name}: {error}. Tüm belgeler yazıldı; metin katmanı eklenenler: {done}."
                    f" {index_note}"
                ) from None
            finally:
                layered.unlink(missing_ok=True)
            item.pdfa = layer.pdfa
            if not layer.pdfa and layer.note:
                item.checks.append(f"PDF/A değil: {layer.note}")
            result.notes[path] = (layer.pdfa, layer.note)
        report("layer", len(paths), len(paths))
    if paths:
        try:
            write_index(items, job, out_dir / "index.xlsx")
        except Exception as error:  # the PDFs are safe; say clearly what is missing
            raise ExportError(f"PDF'ler yazıldı ama index.xlsx yazılamadı: {error}") from None
        result.index_written = True
    return result


def _write_index_quietly(items, job: Job, out_dir: Path) -> str:
    try:
        write_index(items, job, out_dir / "index.xlsx")
    except Exception as error:
        return f"index.xlsx da yazılamadı: {error}"
    return "index.xlsx yazıldı; metin katmanı eksik olanlar orada işaretli."


def may_delete_after_export(result: ExportResult) -> bool:
    """'Delete after export' only after a full export: files, text layer and index written,
    nothing to check. Without the text layer the job is kept, so it can be exported again."""
    return (bool(result.paths) and result.index_written and result.with_layer
            and not result.needing_check)
