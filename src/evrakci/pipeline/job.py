"""A job: the scanned batches, what each page is, and every edit the user made.

All edits are methods here, so the command line and the window share them.
Pages are identified by `<batch id>/<index>`, so edits stay on the same pages
when batches are reordered.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from evrakci.pipeline.analyze import PageInfo

JOB_FORMAT_VERSION = 1


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

    def ordered_page_ids(self) -> list[str]:
        return [
            page_id(batch.id, index)
            for batch in self.batches
            for index in range(batch.page_count)
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

    def rotate(self, pid: str, degrees: int) -> None:
        if degrees % 90:
            raise ValueError("rotation must be a multiple of 90")
        total = (self.rotations.get(self._check(pid), 0) + degrees) % 360
        if total:
            self.rotations[pid] = total
        else:
            self.rotations.pop(pid, None)

    def add_cut(self, pid: str) -> None:
        if self.pages[self._check(pid)].is_separator and pid in self.removed_cuts:
            self.removed_cuts.discard(pid)
        else:
            self.manual_cuts.add(pid)

    def remove_cut(self, pid: str) -> None:
        if pid in self.manual_cuts:
            self.manual_cuts.discard(pid)
        elif self.pages[self._check(pid)].is_separator and pid not in self.removed_cuts:
            self.removed_cuts.add(pid)
        else:
            raise ValueError(f"no cut at {pid}")

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
            {"id": b.id, "file_name": b.file_name, "page_count": b.page_count}
            for b in job.batches
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
        "filters": [
            {"page_ids": sorted(f.page_ids), "every_n": f.every_n} for f in job.filters
        ],
    }


def job_from_dict(data: dict) -> Job:
    if data.get("version") != JOB_FORMAT_VERSION:
        raise ValueError(f"unsupported job format version: {data.get('version')}")
    return Job(
        id=data["id"],
        name=data["name"],
        batches=[Batch(b["id"], b["file_name"], b["page_count"]) for b in data["batches"]],
        pages={
            pid: PageInfo(p["ink_ratio"], p["is_separator"])
            for pid, p in data["pages"].items()
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
    )
