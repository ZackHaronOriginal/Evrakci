"""Write one PDF per document."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from pathlib import Path

import pikepdf

from evrakci.pipeline.cuts import Document
from evrakci.pipeline.export import CHECK_SUBFOLDER
from evrakci.pipeline.job import parse_page_id
from evrakci.pipeline.naming import name_key


def write_documents(
    documents: Sequence[Document],
    batch_files: Mapping[str, Path],
    rotations: Mapping[str, int],
    out_dir: Path,
    stem: str = "belge",
    names: Sequence[str] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> list[Path]:
    """Write one PDF per document and return their paths in order.

    Files are named `names[i].pdf`, or `{stem}_001.pdf`, `_002.pdf`, ... by default.
    """
    if not documents:
        return []
    out_dir = Path(out_dir)
    names = list(names) if names else [f"{stem}_{n:03d}" for n in range(1, len(documents) + 1)]
    keys = [name_key(n) for n in names]
    if len(set(keys)) != len(keys):
        raise ValueError("Aynı dosya adı iki kez yazılamaz.")  # one file would overwrite another
    # Never mix with an earlier export: any old PDF or index would look like part of this one.
    # Letter case is ignored: a USB stick or Windows share treats Belge.PDF as belge.pdf.
    # Names may carry a subfolder ("Kontrol gerekenler/ad"): its old PDFs count too.
    # An existing "Kontrol gerekenler" counts even when this export does not use it: its old
    # PDFs would sit unlisted beside the new files.
    folders = {out_dir, out_dir / CHECK_SUBFOLDER} | {
        out_dir / Path(n).parent for n in names if Path(n).parent != Path(".")}
    for folder in sorted(folders):
        if folder.is_dir():
            old = sorted(p for p in folder.iterdir()
                         if p.suffix.lower() == ".pdf"
                         or (folder == out_dir and p.name.lower() == "index.xlsx"))
            if old:
                raise FileExistsError(old[0].name)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with ExitStack() as stack:
        sources: dict[str, pikepdf.Pdf] = {}
        for number, document in enumerate(documents, start=1):
            target = out_dir / f"{names[number - 1]}.pdf"
            target.parent.mkdir(parents=True, exist_ok=True)
            with pikepdf.new() as output:
                for pid in document.page_ids:
                    batch_id, index = parse_page_id(pid)
                    if batch_id not in sources:
                        sources[batch_id] = stack.enter_context(pikepdf.open(batch_files[batch_id]))
                    output.pages.append(sources[batch_id].pages[index])
                    extra = rotations.get(pid, 0)
                    if extra:
                        output.pages[-1].rotate(extra, relative=True)
                # "x": never replaces a file that appeared since the check above.
                with open(target, "xb") as handle:
                    output.save(handle)
            written.append(target)
            if progress:  # may raise to stop between files; written files stay complete
                progress(len(written), len(documents))
    return written
