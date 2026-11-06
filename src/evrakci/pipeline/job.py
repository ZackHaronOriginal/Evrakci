"""A job: the scanned batches, what each page is, and every edit the user made.

All edits are methods here, so the command line and the window share them.
Pages are identified by `<batch id>/<index>`, so edits stay on the same pages
when batches are reordered.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from evrakci.pipeline.analyze import PageInfo
from evrakci.pipeline.templates.values import SectionReading, VariableValue

JOB_FORMAT_VERSION = 2


def page_id(batch_id: str, index: int) -> str:
    return f"{batch_id}/{index}"


def parse_page_id(pid: str) -> tuple[str, int]:
    batch_id, _, index = pid.rpartition("/")
    return batch_id, int(index)


@dataclass(frozen=True)
class Batch:
    id: str
    file_name: str
    page_count: int


@dataclass(frozen=True)
class FilterApplication:
    page_ids: frozenset[str]
    every_n: int


@dataclass(frozen=True)
class TemplateApplication:
    template_id: str
    page_ids: frozenset[str]


@dataclass(frozen=True)
class ValueSource:
    """What the stored values were read from: the document's pages and its template."""

    page_ids: tuple[str, ...]
    template_id: str


@dataclass
class Job:
    id: str
    name: str
    batches: list[Batch] = field(default_factory=list)
    pages: dict[str, PageInfo] = field(default_factory=dict)
    drop_empty: bool = False
    deleted: set[str] = field(default_factory=set)
    restored: set[str] = field(default_factory=set)
    rotations: dict[str, int] = field(default_factory=dict)
    manual_cuts: set[str] = field(default_factory=set)
    removed_cuts: set[str] = field(default_factory=set)
    filters: list[FilterApplication] = field(default_factory=list)
    templates: list[TemplateApplication] = field(default_factory=list)
    # Read variable values and reading errors, keyed by each document's first page id.
    values: dict[str, dict[str, VariableValue]] = field(default_factory=dict)
    read_errors: dict[str, str] = field(default_factory=dict)
    value_sources: dict[str, ValueSource] = field(default_factory=dict)

    def ordered_page_ids(self) -> list[str]:
        return [
            page_id(batch.id, index) for batch in self.batches for index in range(batch.page_count)
        ]

    def _check(self, pid: str) -> str:
        if pid not in self.pages:
            raise KeyError(pid)
        return pid

    def page_at(self, position: int) -> str:
        ordered = self.ordered_page_ids()
        if not 1 <= position <= len(ordered):
            raise IndexError(position)
        return ordered[position - 1]

    def position_of(self, pid: str) -> int:
        return self.ordered_page_ids().index(self._check(pid)) + 1

    def apply_filter(self, page_ids: Iterable[str], every_n: int) -> None:
        if every_n < 1:
            raise ValueError("every_n must be at least 1")
        ids = frozenset(self._check(pid) for pid in page_ids)
        self.filters.append(FilterApplication(ids, every_n))

    def apply_template(self, page_ids: Iterable[str], template_id: str) -> None:
        ids = frozenset(self._check(pid) for pid in page_ids)
        self.templates.append(TemplateApplication(template_id, ids))

    def rotate(self, pid: str, degrees: int) -> None:
        if degrees % 90:
            raise ValueError("rotation must be a multiple of 90")
        total = (self.rotations.get(self._check(pid), 0) + degrees) % 360
        if total:
            self.rotations[pid] = total
        else:
            self.rotations.pop(pid, None)

    def add_cut(self, pid: str) -> None:
        """Add a cut before `pid`. Raises ValueError if one is already there."""
        if self.pages[self._check(pid)].is_separator:
            if pid not in self.removed_cuts:
                raise ValueError(f"QR page {pid} already cuts")
            self.removed_cuts.discard(pid)
        elif pid in self.manual_cuts:
            raise ValueError(f"cut already at {pid}")
        else:
            self.manual_cuts.add(pid)

    def remove_cut(self, pid: str) -> None:
        if pid in self.manual_cuts:
            self.manual_cuts.discard(pid)
        elif self.pages[self._check(pid)].is_separator and pid not in self.removed_cuts:
            self.removed_cuts.add(pid)
        else:
            raise ValueError(f"no cut at {pid}")

    def move_batch(self, batch_id: str, index: int) -> None:
        batch = self.get_batch(batch_id)
        if not 0 <= index < len(self.batches):
            raise IndexError(index)
        self.batches.remove(batch)
        self.batches.insert(index, batch)

    def remove_batch(self, batch_id: str) -> None:
        batch = self.get_batch(batch_id)
        self.batches.remove(batch)
        gone = {page_id(batch.id, i) for i in range(batch.page_count)}
        for pid in gone:
            self.pages.pop(pid, None)
            self.rotations.pop(pid, None)
        for edits in (self.deleted, self.restored, self.manual_cuts, self.removed_cuts):
            edits -= gone
        kept = [FilterApplication(f.page_ids - gone, f.every_n) for f in self.filters]
        self.filters = [f for f in kept if f.page_ids]
        applied = [TemplateApplication(t.template_id, t.page_ids - gone) for t in self.templates]
        self.templates = [t for t in applied if t.page_ids]
        for pid in gone:
            self.values.pop(pid, None)
            self.read_errors.pop(pid, None)
            self.value_sources.pop(pid, None)

    def get_batch(self, batch_id: str) -> Batch:
        for batch in self.batches:
            if batch.id == batch_id:
                return batch
        raise KeyError(batch_id)

    def delete_page(self, pid: str) -> None:
        self.deleted.add(self._check(pid))

    def undelete_page(self, pid: str) -> None:
        self.deleted.discard(self._check(pid))

    def restore_empty(self, pid: str) -> None:
        self.restored.add(self._check(pid))

    def unrestore_empty(self, pid: str) -> None:
        self.restored.discard(self._check(pid))


def job_to_dict(job: Job) -> dict:
    return {
        "version": JOB_FORMAT_VERSION,
        "id": job.id,
        "name": job.name,
        "batches": [
            {"id": b.id, "file_name": b.file_name, "page_count": b.page_count} for b in job.batches
        ],
        "pages": {
            pid: {"ink_ratio": info.ink_ratio, "is_separator": info.is_separator}
            for pid, info in job.pages.items()
        },
        "drop_empty": job.drop_empty,
        "deleted": sorted(job.deleted),
        "restored": sorted(job.restored),
        "rotations": dict(sorted(job.rotations.items())),
        "manual_cuts": sorted(job.manual_cuts),
        "removed_cuts": sorted(job.removed_cuts),
        "filters": [{"page_ids": sorted(f.page_ids), "every_n": f.every_n} for f in job.filters],
        "templates": [
            {"template_id": t.template_id, "page_ids": sorted(t.page_ids)} for t in job.templates
        ],
        "values": {
            pid: {name: _value_to_dict(value) for name, value in values.items()}
            for pid, values in job.values.items()
        },
        "read_errors": dict(job.read_errors),
        "value_sources": {
            pid: {"page_ids": list(s.page_ids), "template_id": s.template_id}
            for pid, s in job.value_sources.items()
        },
    }


def _value_to_dict(value: VariableValue) -> dict:
    return {
        "value": value.value,
        "confidence": value.confidence,
        "section": value.section,
        "flagged": value.flagged,
        "suggestion": value.suggestion,
        "edited": value.edited,
        "readings": [
            {"section": r.section, "text": r.text, "confidence": r.confidence, "problem": r.problem}
            for r in value.readings
        ],
    }


def _value_from_dict(data: dict) -> VariableValue:
    return VariableValue(
        value=data["value"],
        confidence=data["confidence"],
        section=data["section"],
        flagged=data["flagged"],
        suggestion=data.get("suggestion", ""),
        readings=tuple(
            SectionReading(r["section"], r["text"], r["confidence"], r.get("problem"))
            for r in data.get("readings", [])
        ),
        edited=data.get("edited", False),
    )


def job_from_dict(data: dict) -> Job:
    if data.get("version") not in (1, JOB_FORMAT_VERSION):  # version 1 had no templates
        raise ValueError(f"unsupported job format version: {data.get('version')}")
    return Job(
        id=data["id"],
        name=data["name"],
        batches=[Batch(b["id"], b["file_name"], b["page_count"]) for b in data["batches"]],
        pages={
            pid: PageInfo(p["ink_ratio"], p["is_separator"]) for pid, p in data["pages"].items()
        },
        drop_empty=data["drop_empty"],
        deleted=set(data["deleted"]),
        restored=set(data["restored"]),
        rotations={pid: int(deg) for pid, deg in data["rotations"].items()},
        manual_cuts=set(data["manual_cuts"]),
        removed_cuts=set(data["removed_cuts"]),
        filters=[
            FilterApplication(frozenset(f["page_ids"]), f["every_n"]) for f in data["filters"]
        ],
        templates=[
            TemplateApplication(t["template_id"], frozenset(t["page_ids"]))
            for t in data.get("templates", [])
        ],
        values={
            pid: {name: _value_from_dict(v) for name, v in values.items()}
            for pid, values in data.get("values", {}).items()
        },
        read_errors=dict(data.get("read_errors", {})),
        value_sources={
            pid: ValueSource(tuple(s["page_ids"]), s["template_id"])
            for pid, s in data.get("value_sources", {}).items()
        },
    )
