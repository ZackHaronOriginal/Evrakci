"""Write one PDF per document."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from pathlib import Path

import pikepdf

from evrakci.pipeline.cuts import Document
from evrakci.pipeline.job import parse_page_id


def write_documents(
    documents: Sequence[Document],
    batch_files: Mapping[str, Path],
    rotations: Mapping[str, int],
    out_dir: Path,
    stem: str = "belge",
) -> list[Path]:
    """Write `out_dir/{stem}_001.pdf`, `_002.pdf`, ... and return their paths in order."""
    if not documents:
        return []
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with ExitStack() as stack:
        sources: dict[str, pikepdf.Pdf] = {}
        for number, document in enumerate(documents, start=1):
            target = out_dir / f"{stem}_{number:03d}.pdf"
            with pikepdf.new() as output:
                for pid in document.page_ids:
                    batch_id, index = parse_page_id(pid)
                    if batch_id not in sources:
                        sources[batch_id] = stack.enter_context(
                            pikepdf.open(batch_files[batch_id])
                        )
                    output.pages.append(sources[batch_id].pages[index])
                    extra = rotations.get(pid, 0)
                    if extra:
                        output.pages[-1].rotate(extra, relative=True)
                output.save(target)
            written.append(target)
    return written
