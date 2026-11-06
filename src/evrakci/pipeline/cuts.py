"""Turn a job into documents, from its QR pages, manual cuts and filters."""

from __future__ import annotations

from dataclasses import dataclass

from evrakci.pipeline.job import FilterApplication, Job


@dataclass(frozen=True)
class Document:
    page_ids: tuple[str, ...]
    flags: frozenset[str] = frozenset()


def compute_documents(job: Job) -> list[Document]:
    """Cut the job into documents.

    - A QR page cuts (unless its cut was removed) and never reaches the output.
    - A manual cut cuts before its page.
    - Inside a filter, every N pages is one document. Counting restarts after any
      cut, and a shorter last group is flagged "leftover".
    - Elsewhere, everything between two cuts is one document.
    - Empty pages never cut. They are only left out when `drop_empty` is on.
    """
    filter_of: dict[str, FilterApplication] = {}
    for application in job.filters:  # later filters overwrite earlier ones
        for pid in application.page_ids:
            filter_of[pid] = application

    documents: list[Document] = []
    current: list[str] = []
    current_filter: FilterApplication | None = None

    def close() -> None:
        if not current:
            return
        leftover = current_filter is not None and len(current) < current_filter.every_n
        flags = frozenset({"leftover"}) if leftover else frozenset()
        documents.append(Document(tuple(current), flags))
        current.clear()

    # A manual cut on a page that is left out still cuts before the next kept page.
    cut_pending = False
    for pid in job.ordered_page_ids():
        cut_pending = cut_pending or pid in job.manual_cuts
        if pid in job.deleted:
            continue
        info = job.pages[pid]
        if info.is_separator:
            if pid not in job.removed_cuts:
                close()
            cut_pending = False
            continue
        if job.drop_empty and info.is_empty and pid not in job.restored:
            continue
        if cut_pending:
            close()
            cut_pending = False
        application = filter_of.get(pid)
        if application is not current_filter:
            close()
            current_filter = application
        current.append(pid)
        if application is not None and len(current) == application.every_n:
            close()
    close()
    return documents
