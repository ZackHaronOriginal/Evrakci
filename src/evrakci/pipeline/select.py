"""Choose pages by a criterion: the core behind Kontrol's "Ölçüte göre seç…" and `is sec`.

Pure: no Qt, no imaging. The window and the command line call the same functions, so they give
the same page list (the parity test in tests/test_cli_select.py).

A `Criterion` is a kind and its parameters. `evaluate()` turns one into a `Match`: the page ids
in job order, how many documents they come from, and a count per reason. Separators, deleted
pages and pages the job leaves out never match, because they are not in any document (cuts.py),
and they cannot be filtered or deleted. `combine()` joins a match with the current selection.

Kinds of this step: `belge` (param `number`, the document's number from 1), `tek` and `cift`
(param `within`: count only inside the documents the selection touches). Odd and even are
counted from the first page of each document (1st, 3rd, 5th ... / 2nd, 4th ...), because that
is what a duplex pile follows. The kind `bos` (param `ink`, the highest ink share as a fraction,
default `analyze.EMPTY_INK_RATIO`) gives the pages with less ink than that; QR separator pages
never match and blank pages already deleted are counted apart (`reasons["silinmis"]`), not
selected. The kind `guven` (params `levels`, `checks`, `pages`) gives the pages of documents
that need a look, with a count per reason (see "Güven" below). The kind `farkli` (params `by`:
`boyut` and / or `yon`, `reference`: `is` or `belge`) gives the pages whose size or orientation
differs from the job's (or each document's) own majority (see "Farklı" below).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from evrakci.pipeline.analyze import EMPTY_INK_RATIO
from evrakci.pipeline.cuts import Document, compute_documents, current_values, document_template
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.job import Job
from evrakci.pipeline.templates.model import Template
from evrakci.pipeline.templates.values import box_section, value_level

MODES = ("replace", "add", "within")


@dataclass(frozen=True)
class Criterion:
    kind: str
    params: Mapping[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "params": dict(self.params)}

    @classmethod
    def from_dict(cls, data: Mapping) -> Criterion:
        return cls(str(data["kind"]), dict(data.get("params") or {}))


@dataclass(frozen=True)
class Match:
    page_ids: tuple[str, ...] = ()
    documents: int = 0
    reasons: Mapping[str, int] = field(default_factory=dict)

    def count(self) -> int:
        return len(self.page_ids)


Evaluator = Callable[[Job, Criterion, Mapping, frozenset[str]], Match]
_KINDS: dict[str, Evaluator] = {}


def kind(name: str) -> Callable[[Evaluator], Evaluator]:
    """Register the evaluator of one criterion kind."""

    def register(function: Evaluator) -> Evaluator:
        _KINDS[name] = function
        return function

    return register


def kinds() -> tuple[str, ...]:
    return tuple(_KINDS)


def evaluate(
    job: Job,
    criterion: Criterion,
    *,
    templates: Mapping | None = None,
    selection: Iterable[str] = (),
) -> Match:
    """The pages of `job` that meet `criterion`, in job order."""
    try:
        function = _KINDS[criterion.kind]
    except KeyError:
        raise ValueError(f"unknown criterion kind: {criterion.kind}") from None
    return function(job, criterion, templates or {}, frozenset(selection))


def combine(
    base: Iterable[str],
    match: Match,
    mode: str,
    *,
    order: Sequence[str] | None = None,
) -> tuple[str, ...]:
    """`base` (the current selection) joined with `match`: `replace` gives the match, `add`
    the union, `within` the pages in both. Job order when `order` (all page ids) is given."""
    base_ids = tuple(base)
    if mode == "replace":
        result: Iterable[str] = match.page_ids
    elif mode == "add":
        result = dict.fromkeys((*base_ids, *match.page_ids))
    elif mode == "within":
        keep = frozenset(base_ids)
        result = (pid for pid in match.page_ids if pid in keep)
    else:
        raise ValueError(f"unknown mode: {mode}")
    ids = tuple(result)
    if order is not None and mode == "add":
        position = {pid: i for i, pid in enumerate(order)}
        ids = tuple(sorted(ids, key=lambda pid: position.get(pid, len(position))))
    return ids


@dataclass(frozen=True)
class SelectionResult:
    """What `select_pages` found: the pages every known criterion matches (job order), how
    many pages each criterion matches alone (one number per criterion, in the order given; 0
    for an unknown kind) and the kinds this version does not know (in the order given)."""

    page_ids: tuple[str, ...] = ()
    per_filter_counts: tuple[int, ...] = ()
    unknown_kinds: tuple[str, ...] = ()


def select_pages(job: Job, criteria: Iterable[Criterion],
                 templates: Mapping | None = None) -> SelectionResult:
    """The pages that meet every criterion (AND). The window's saved-filter chips and
    `is sec --sablon` call only this, so both give the same pages and counts. An unknown kind
    is reported in `unknown_kinds` and cannot match, it is never dropped without a word; no
    criterion at all selects nothing."""
    ids: tuple[str, ...] | None = None
    counts: list[int] = []
    unknown: list[str] = []
    for criterion in criteria:
        if criterion.kind not in _KINDS:
            counts.append(0)
            unknown.append(criterion.kind)
            continue
        match = evaluate(job, criterion, templates=templates)
        counts.append(match.count())
        ids = match.page_ids if ids is None else combine(ids, match, "within")
    return SelectionResult(ids or (), tuple(counts), tuple(unknown))


def _documents(job: Job) -> list[Document]:
    return compute_documents(job)


@kind("belge")
def _document(job: Job, criterion: Criterion, _templates: Mapping, _selection: frozenset) -> Match:
    documents = _documents(job)
    number = criterion.params.get("number", 0)
    if not isinstance(number, int) or not 1 <= number <= len(documents):
        return Match()
    return Match(tuple(documents[number - 1].page_ids), 1)


def _every_other(job: Job, criterion: Criterion, selection: frozenset, first: int) -> Match:
    only = bool(criterion.params.get("within")) and bool(selection)
    found: list[str] = []
    touched = 0
    for document in _documents(job):
        if only and selection.isdisjoint(document.page_ids):
            continue
        pages = document.page_ids[first::2]
        if pages:
            found.extend(pages)
            touched += 1
    return Match(tuple(found), touched)


@kind("tek")
def _odd(job: Job, criterion: Criterion, _templates: Mapping, selection: frozenset) -> Match:
    return _every_other(job, criterion, selection, 0)


@kind("cift")
def _even(job: Job, criterion: Criterion, _templates: Mapping, selection: frozenset) -> Match:
    return _every_other(job, criterion, selection, 1)


def blank_limit(criterion: Criterion) -> float:
    """The ink share a `bos` criterion allows; the default when the param is missing or bad."""
    value = criterion.params.get("ink", EMPTY_INK_RATIO)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        return EMPTY_INK_RATIO
    return float(value)


@kind("bos")
def _blank(job: Job, criterion: Criterion, _templates: Mapping, _selection: frozenset) -> Match:
    limit = blank_limit(criterion)
    found: list[str] = []
    deleted = 0
    for pid in job.ordered_page_ids():
        info = job.pages[pid]
        if info.is_separator or info.ink_ratio >= limit:
            continue
        if pid in job.deleted:
            deleted += 1
        else:
            found.append(pid)
    found_set = set(found)
    touched = sum(1 for document in _documents(job) if found_set.intersection(document.page_ids))
    return Match(tuple(found), touched, {"silinmis": deleted} if deleted else {})


def ink_range(job: Job, match: Match) -> tuple[float, float] | None:
    """The emptiest and the fullest page of `match` as ink shares, or None for no pages."""
    if not match.page_ids:
        return None
    shares = [job.pages[pid].ink_ratio for pid in match.page_ids]
    return min(shares), max(shares)


# Güven: "Kontrol gerekenler"
GUVEN_LEVELS = ("kontrol", "okunamadi", "orta", "okunmadi")  # Emin is never a reason
GUVEN_CHECKS = ("eksik sayfa", "karışık şablon")  # the export plan's own words
GUVEN_REASONS = (*GUVEN_LEVELS, *GUVEN_CHECKS)
GUVEN_DEFAULT = ("kontrol", "okunamadi", "okunmadi", *GUVEN_CHECKS)  # Orta is off by default
GUVEN_VALUES = ("kontrol", "okunamadi", "orta")  # counted in values; the rest in documents
GUVEN_WORDS = {
    "kontrol": "Kontrol", "okunamadi": "Okunamadı", "orta": "Orta", "okunmadi": "Okunmadı",
    "eksik sayfa": "Eksik sayfa", "karışık şablon": "Karışık şablon",
}
GUVEN_PAGES = ("deger", "belge")


def value_page(template: Template | None, key: str, source: int | None, page_count: int) -> int:
    """Index (in the document) of the page the box of variable `key` is on; `source` is the
    section the shown reading came from (None: the first)."""
    if template is None:
        return 0
    variable = next((v for v in template.variables if v.key == key), None)
    if variable is None or not variable.sections:
        return 0
    section = variable.sections[min(source or 0, len(variable.sections) - 1)]
    index = section.page - 1 if section.page > 0 else page_count + section.page
    return max(0, min(page_count - 1, index))


def reason_count_text(reason: str, count: int) -> str:
    """"4 değer" for a value reason, "2 belge" for the others."""
    return f"{count} {'değer' if reason in GUVEN_VALUES else 'belge'}"


def _check_reason(check: str) -> str | None:
    for reason in GUVEN_CHECKS:
        if check == reason or check.startswith(reason + " "):
            return reason
    return None


@dataclass
class Finding:
    """What one document needs a look for: reasons with their counts and page indexes."""

    document: Document
    counts: dict[str, int] = field(default_factory=dict)  # reason -> values (or 1 document)
    pages: dict[str, set[int]] = field(default_factory=dict)  # reason -> page indexes


def guven_findings(job: Job, templates: Mapping[str, Template | None]) -> list[Finding]:
    found = []
    for item in plan_export(job, templates):
        finding = Finding(item.document)
        for check in item.checks:
            reason = _check_reason(check)
            if reason is not None:
                finding.counts[reason] = 1
                finding.pages[reason] = {0}  # the document's first page
        template_id, _ = document_template(job, item.document)
        template = templates.get(template_id) if template_id is not None else None
        if template is not None:
            values = current_values(job, item.document) or {}
            size = len(item.document.page_ids)
            for variable in template.variables:
                value = values.get(variable.key)
                level = value_level(value)
                if level == "emin":
                    continue
                source = box_section(value) if value is not None else None
                page = value_page(template, variable.key, source, size)
                # Unread values count as one document, the others one by one.
                finding.counts[level] = (1 if level == "okunmadi"
                                         else finding.counts.get(level, 0) + 1)
                finding.pages.setdefault(level, set()).add(page)
        found.append(finding)
    return found


def values_read(job: Job) -> bool:
    """Whether any document with a template has read values (else Güven has nothing to say)."""
    return any(current_values(job, document) is not None for document in _documents(job)
               if document_template(job, document)[0] is not None)


def guven_params(criterion: Criterion) -> tuple[tuple[str, ...], str]:
    """The reasons asked for (in the fixed order) and "deger" / "belge"; the defaults when
    neither `levels` nor `checks` is given."""
    levels = criterion.params.get("levels")
    checks = criterion.params.get("checks")
    if levels is None and checks is None:
        asked = set(GUVEN_DEFAULT)
    else:
        asked = {str(x) for x in (levels or ())} | {str(x) for x in (checks or ())}
    pages = criterion.params.get("pages", "deger")
    return (tuple(r for r in GUVEN_REASONS if r in asked),
            pages if pages in GUVEN_PAGES else "deger")


@kind("guven")
def _guven(job: Job, criterion: Criterion, templates: Mapping, _selection: frozenset) -> Match:
    return guven_match(job, guven_findings(job, templates), criterion)


def guven_match(job: Job, findings: Sequence[Finding], criterion: Criterion) -> Match:
    """`criterion` (kind guven) over findings built once with `guven_findings`: a window that
    asks again and again (the dialog's check boxes) builds them once and keeps them."""
    reasons, pages = guven_params(criterion)
    wanted = set(reasons)
    chosen: set[str] = set()
    touched = 0
    totals = dict.fromkeys(reasons, 0)
    for finding in findings:
        hit = wanted.intersection(finding.counts)
        if not hit:
            continue
        touched += 1
        for reason in hit:
            totals[reason] += finding.counts[reason]
        ids = finding.document.page_ids
        if pages == "belge":
            chosen.update(ids)
        else:
            chosen.update(ids[i] for reason in hit for i in finding.pages[reason])
    ordered = tuple(pid for pid in job.ordered_page_ids() if pid in chosen)
    return Match(ordered, touched, totals)


def guven_text(match: Match) -> str:
    """"9 belge seçildi: Kontrol 4, Okunamadı 3" (the reasons with something in them)."""
    parts = [f"{GUVEN_WORDS[r]} {n}" for r, n in match.reasons.items() if n]
    return f"{match.documents} belge seçildi: {', '.join(parts)}"


# Farklı: "Farklı boyut veya yön"
FARKLI_BY = ("boyut", "yon")  # size, orientation
FARKLI_REFERENCE = ("is", "belge")  # the whole job, or each document
FARKLI_TOLERANCE = 0.03  # scanner jitter: a side within 3 % of the reference is the same size
ODD_KINDS = ("boyut", "yatay", "dikey")  # what a marked page is: size, landscape, portrait


def _extent(job: Job, pid: str) -> tuple[float, float] | None:
    """(width, height) in millimetres as the page is exported, after the job's rotation of it
    (a quarter turn swaps the sides); None when the size is unknown."""
    info = job.pages[pid]
    if not info.has_size:
        return None
    width, height = info.width_mm, info.height_mm
    return (height, width) if job.rotations.get(pid, 0) % 180 else (width, height)


def _orientation(extent: tuple[float, float]) -> str | None:
    """"yatay" / "dikey"; a page whose sides are within the tolerance (square) has none."""
    width, height = extent
    if width > height * (1 + FARKLI_TOLERANCE):
        return "yatay"
    if height > width * (1 + FARKLI_TOLERANCE):
        return "dikey"
    return None


def _same_size(extent: tuple[float, float], reference: tuple[float, float]) -> bool:
    """Both sides, short with short and long with long (a sideways A4 is still A4), within the
    tolerance of the reference."""
    return all(abs(a - b) <= FARKLI_TOLERANCE * b
               for a, b in zip(sorted(extent), sorted(reference), strict=True))


MAX_CANDIDATES = 40  # distinct sizes tried as the centre of the majority (jitter makes many)


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def _majority(extents: Sequence[tuple[float, float]]) -> tuple[tuple[float, float] | None,
                                                                 str | None]:
    """The most frequent size and the most frequent orientation of `extents`.

    Each distinct size (to the millimetre, in page order; at most MAX_CANDIDATES, evenly
    spread) is tried as a centre and counted with the pages within the tolerance of it. The
    centre with most pages wins (the first in page order on a tie), and the reference is the
    median of the pages it counted, so scanner jitter around the real size, whichever page
    comes first, does not mark pages. O(n * k) with few distinct sizes."""
    orientations: dict[str, int] = {}
    seen: dict[tuple[int, int], tuple[float, float]] = {}
    for extent in extents:
        short, long_ = sorted(extent)
        seen.setdefault((round(short), round(long_)), extent)
        found = _orientation(extent)
        if found is not None:
            orientations[found] = orientations.get(found, 0) + 1
    orientation = max(orientations, key=orientations.get) if orientations else None
    if not seen:
        return None, orientation
    centres = list(seen.values())
    if len(centres) > MAX_CANDIDATES:
        step = len(centres) / MAX_CANDIDATES
        centres = [centres[int(i * step)] for i in range(MAX_CANDIDATES)]
    ordered = [tuple(sorted(e)) for e in extents]
    best: list[tuple[float, float]] = []
    for centre in centres:
        low, high = sorted(centre)
        members = [e for e in ordered if abs(e[0] - low) <= FARKLI_TOLERANCE * low
                   and abs(e[1] - high) <= FARKLI_TOLERANCE * high]
        if len(members) > len(best):
            best = members
    shorts, longs = zip(*best, strict=True)
    return (_median(list(shorts)), _median(list(longs))), orientation


def farkli_params(criterion: Criterion) -> tuple[tuple[str, ...], str]:
    """What a `farkli` criterion compares (in the fixed order; both when `by` is missing) and
    against what ("is" unless "belge")."""
    asked = criterion.params.get("by")
    asked = FARKLI_BY if asked is None else {str(x) for x in asked}
    reference = criterion.params.get("reference", "is")
    return (tuple(x for x in FARKLI_BY if x in asked),
            reference if reference in FARKLI_REFERENCE else "is")


def _mark_group(job: Job, pids: Sequence[str], by: Sequence[str], found: dict[str, str],
                reference_pids: Sequence[str]) -> None:
    reference_size, reference_orientation = _majority(
        [e for pid in reference_pids if (e := _extent(job, pid)) is not None])
    for pid in pids:
        extent = _extent(job, pid)
        if extent is None:
            continue  # unknown size: never marked
        if "boyut" in by and reference_size is not None and not _same_size(
                extent, reference_size):
            found[pid] = "boyut"
        elif "yon" in by and reference_orientation is not None:
            own = _orientation(extent)
            if own is not None and own != reference_orientation:
                found[pid] = own


def different_pages(job: Job, by: Sequence[str] = FARKLI_BY, reference: str = "is",
                    documents: Sequence[Document] | None = None) -> dict[str, str]:
    """The pages that look different, in job order, each with what is different: "boyut" (size
    differs), or "yatay" / "dikey" (the page's own orientation, when only that differs).

    The reference is the most frequent size, and the most frequent orientation, among the
    pages that are not deleted and not separators: of the whole job, or of each document.
    Orientation is judged after the job's rotations, so a quarter turn that stands a sideways
    page up takes its mark away. Pages whose size is unknown (`unknown_sizes`) are never marked;
    pages outside every document (dropped blank pages) are not marked either. Pure and O(n);
    `documents` are the job's documents when the caller has them already."""
    if not any(info.has_size for info in job.pages.values()):
        return {}
    usable = [pid for pid in job.ordered_page_ids()
              if not job.pages[pid].is_separator and pid not in job.deleted]
    found: dict[str, str] = {}
    documents = _documents(job) if documents is None else documents
    in_documents = {pid for document in documents for pid in document.page_ids}
    if reference == "belge":
        usable_set = set(usable)
        for document in documents:
            members = [pid for pid in document.page_ids if pid in usable_set]
            _mark_group(job, members, by, found, members)
    else:
        _mark_group(job, [pid for pid in usable if pid in in_documents], by, found, usable)
    return {pid: found[pid] for pid in job.ordered_page_ids() if pid in found}


def unknown_sizes(job: Job) -> int:
    """How many pages (not deleted, not separators) have no known size."""
    return sum(1 for pid, info in job.pages.items()
               if not info.has_size and not info.is_separator and pid not in job.deleted)


@kind("farkli")
def _farkli(job: Job, criterion: Criterion, _templates: Mapping, _selection: frozenset) -> Match:
    by, reference = farkli_params(criterion)
    found = different_pages(job, by, reference)
    counts = {"boyut": sum(1 for k in found.values() if k == "boyut"),
              "yon": sum(1 for k in found.values() if k != "boyut"),
              "bilinmiyor": unknown_sizes(job)}
    chosen = set(found)
    touched = sum(1 for document in _documents(job) if chosen.intersection(document.page_ids))
    return Match(tuple(found), touched, {k: n for k, n in counts.items() if n})
