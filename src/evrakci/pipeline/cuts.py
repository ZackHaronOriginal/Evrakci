"""Turn a job into documents, from its QR pages, manual cuts and filters."""

from __future__ import annotations

from dataclasses import dataclass

from evrakci.pipeline.job import FilterApplication, Job, ValueSource
from evrakci.pipeline.templates.values import VariableValue


@dataclass(frozen=True)
class Document:
    page_ids: tuple[str, ...]
    flags: frozenset[str] = frozenset()


def _template_of(job: Job) -> dict[str, str]:
    template_of: dict[str, str] = {}
    for application in job.templates:  # later applications overwrite earlier ones
        for pid in application.page_ids:
            template_of[pid] = application.template_id
    return template_of


def document_template(job: Job, document: Document) -> tuple[str | None, bool]:
    """The template of the document's first page, and whether its pages disagree."""
    template_of = _template_of(job)
    found = {template_of.get(pid) for pid in document.page_ids}
    return template_of.get(document.page_ids[0]), len(found) > 1


def record_values(
    job: Job, document: Document, template_id: str, values: dict[str, VariableValue]
) -> None:
    """Store values together with what they were read from."""
    first = document.page_ids[0]
    job.values[first] = values
    job.read_errors.pop(first, None)
    job.value_sources[first] = ValueSource(tuple(document.page_ids), template_id)


def record_read_error(job: Job, document: Document, template_id: str, message: str) -> None:
    """Remember that reading this exact document failed, and why."""
    first = document.page_ids[0]
    job.values.pop(first, None)
    job.read_errors[first] = message
    job.value_sources[first] = ValueSource(tuple(document.page_ids), template_id)


def _source_matches(job: Job, document: Document) -> bool:
    source = job.value_sources.get(document.page_ids[0])
    template_id, _ = document_template(job, document)
    return (
        source is not None
        and source.page_ids == tuple(document.page_ids)
        and source.template_id == template_id
    )


def current_read_error(job: Job, document: Document) -> str | None:
    """A reading error, only if it belongs to exactly this document and template."""
    first = document.page_ids[0]
    if first in job.read_errors and _source_matches(job, document):
        return job.read_errors[first]
    return None


def current_values(job: Job, document: Document) -> dict[str, VariableValue] | None:
    """The stored values, only if they were read from exactly this document and template.

    After the cuts or the template change, old values must not be used for naming.
    """
    first = document.page_ids[0]
    source = job.value_sources.get(first)
    template_id, _ = document_template(job, document)
    if (
        first not in job.values
        or source is None
        or source.page_ids != tuple(document.page_ids)
        or source.template_id != template_id
    ):
        return None
    return job.values[first]


def compute_documents(job: Job) -> list[Document]:
    """Cut the job into documents (see `_split`)."""
    return [document for document, _ in _split(job)]


def cut_kinds(job: Job) -> dict[str, str]:
    """What starts each document, keyed by its first page id.

    "qr" (a separator page), "manual" (a manual cut), "filter" (a filter group or
    the edge of a filtered range) or "start" (the first document).
    """
    return {document.page_ids[0]: kind for document, kind in _split(job)}


def _split(job: Job) -> list[tuple[Document, str]]:
    """Cut the job into documents, each with what started it.

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

    template_of = _template_of(job)
    documents: list[tuple[Document, str]] = []
    current: list[str] = []
    current_filter: FilterApplication | None = None
    reason = "start"  # what will have started the next document

    def close(next_reason: str) -> None:
        nonlocal reason
        if not current:
            # The strongest reason since the last document wins.
            if reason == "filter" or (reason == "start" and next_reason != "filter"):
                reason = next_reason
            return
        flags = set()
        if current_filter is not None and len(current) < current_filter.every_n:
            flags.add("leftover")
        if len({template_of.get(pid) for pid in current}) > 1:
            flags.add("mixed_templates")
        documents.append((Document(tuple(current), frozenset(flags)), reason))
        reason = next_reason
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
                close("qr")
            cut_pending = False
            continue
        if job.drop_empty and info.is_empty and pid not in job.restored:
            continue
        if cut_pending:
            close("manual")
            cut_pending = False
        application = filter_of.get(pid)
        if application is not current_filter:
            close("filter")
            current_filter = application
        current.append(pid)
        if application is not None and len(current) == application.every_n:
            close("filter")
    close("filter")
    return documents
