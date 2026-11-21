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
is what a duplex pile follows. The kinds `bos`, `farkli` and `guven` of the later steps plug in
with `kind()` and need nothing else here.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from evrakci.pipeline.cuts import Document, compute_documents
from evrakci.pipeline.job import Job

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
