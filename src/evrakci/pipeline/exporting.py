"""Run an export: write the named PDFs, add the text layer, write index.xlsx.

The command line and the window both call `export_job`, so they always do the same thing.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

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
    items = plan_export(job, templates)
    try:
        fitted = unique_names(fit_names([i.name for i in items], out_dir))
    except ValueError as error:
        raise ExportError(str(error)) from None
    for item, name in zip(items, fitted, strict=True):
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
    result = ExportResult(items, paths)
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
                raise ExportError(
                    f"{path.name}: {error}. Tüm belgeler yazıldı; metin katmanı eklenenler: {done}."
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
    return result
