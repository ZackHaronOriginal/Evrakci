"""Jobs on disk: `<root>/<job id>/job.json` plus a copy of every batch PDF."""

from __future__ import annotations

import json
import os
import re
import shutil
import time
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import platformdirs

from evrakci.pipeline.analyze import PageInfo, analyze_pdf, count_pages
from evrakci.pipeline.job import Batch, Job, job_from_dict, job_to_dict, page_id

Progress = Callable[[int, int], None]


class JobFileError(Exception):
    """A saved job file that cannot be read. The message is shown to staff (Turkish)."""


def default_root() -> Path:
    configured = os.environ.get("EVRAKCI_KOK")
    return Path(configured) if configured else (
        platformdirs.user_data_path("Evrakci", appauthor=False) / "jobs")


_JOB_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")


@dataclass(frozen=True)
class PreparedBatch:
    batch: Batch
    pages: list[PageInfo]


class JobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _job_dir(self, job_id: str) -> Path:
        # A job id is a plain folder name: never "..", a path or anything outside the root.
        if not isinstance(job_id, str) or not _JOB_ID.fullmatch(job_id):
            raise KeyError(job_id)
        return self.root / job_id

    def _job_file(self, job_id: str) -> Path:
        return self._job_dir(job_id) / "job.json"

    def batch_file(self, job: Job, batch: Batch) -> Path:
        return self._job_dir(job.id) / "batches" / f"{batch.id}.pdf"

    def batch_files(self, job: Job) -> dict[str, Path]:
        return {batch.id: self.batch_file(job, batch) for batch in job.batches}

    def create_job(
        self, name: str, pdf_paths: Sequence[Path], progress: Progress | None = None
    ) -> Job:
        # Check and analyze everything first, so a bad file never leaves a half-made job.
        total = sum(count_pages(Path(path)) for path in pdf_paths)
        analyses = []
        done = 0
        for path in pdf_paths:
            offset = done

            def report(d: int, t: int, offset: int = offset) -> None:
                if progress:
                    progress(offset + d, total)

            infos = analyze_pdf(Path(path), report)
            done += len(infos)
            analyses.append((Path(path), infos))

        job = Job(id=uuid.uuid4().hex[:12], name=name)
        try:
            for path, infos in analyses:
                self._attach(job, path, infos)
            self.save(job)
        except BaseException:
            shutil.rmtree(self._job_dir(job.id), ignore_errors=True)
            raise
        return job

    def add_batch(self, job: Job, pdf_path: Path) -> Batch:
        infos = analyze_pdf(Path(pdf_path))
        batch = self._attach(job, Path(pdf_path), infos)
        try:
            self.save(job)
        except BaseException:
            job.remove_batch(batch.id)
            self.batch_file(job, batch).unlink(missing_ok=True)
            raise
        return batch

    def prepare_batch(
        self, job: Job, pdf_path: Path, progress: Progress | None = None
    ) -> PreparedBatch:
        """Analyze a PDF and copy it into the job folder, without changing `job`.

        Attach it afterwards with `job.attach_batch`, so slow analysis can run on the side
        while the job is still being edited. `progress(done, total)` reports pages read.
        """
        infos = analyze_pdf(Path(pdf_path), progress)
        number = max((int(b.id[1:]) for b in job.batches), default=0) + 1
        while self.batch_file(job, Batch(f"b{number}", "", 0)).exists():
            number += 1  # a file left by an undone earlier batch keeps its name
        batch = Batch(f"b{number}", Path(pdf_path).name, len(infos))
        target = self.batch_file(job, batch)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_path, target)
        return PreparedBatch(batch, infos)

    def _attach(self, job: Job, path: Path, infos: list[PageInfo]) -> Batch:
        number = max((int(b.id[1:]) for b in job.batches), default=0) + 1
        batch = Batch(f"b{number}", path.name, len(infos))
        target = self.batch_file(job, batch)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        job.batches.append(batch)
        for index, info in enumerate(infos):
            job.pages[page_id(batch.id, index)] = info
        return batch

    def save(self, job: Job) -> None:
        target = self._job_file(job.id)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(job_to_dict(job), ensure_ascii=False, indent=1), encoding="utf-8"
        )
        os.replace(temporary, target)

    def load(self, job_id: str) -> Job:
        path = self._job_file(job_id)
        if not path.is_file():
            raise KeyError(job_id)
        try:
            job = job_from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (ValueError, KeyError, TypeError, OSError) as error:
            raise JobFileError(f"İş dosyası okunamadı: {job_id}") from error
        # The folder is the job: a copied folder must never save into, or delete, the original.
        job.id = job_id
        return job

    def list_jobs(self, on_error: Callable[[str], None] | None = None) -> list[Job]:
        """Readable jobs, most recently edited first. Unreadable ones go to `on_error`."""
        if not self.root.is_dir():
            return []
        files = [p for p in self.root.glob("*/job.json") if p.is_file()]
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        jobs = []
        for path in files:
            try:
                jobs.append(self.load(path.parent.name))
            except JobFileError:
                if on_error:
                    on_error(path.parent.name)
        return jobs

    def remove_batch(self, job: Job, batch_id: str) -> None:
        batch = job.get_batch(batch_id)
        path = self.batch_file(job, batch)
        job.remove_batch(batch_id)
        self.save(job)
        path.unlink(missing_ok=True)

    def delete_older_than(
        self,
        days: int,
        now: float | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> list[str]:
        """Delete Evrakçı jobs whose job.json was last changed more than `days` days ago.

        Only real job folders are touched: not links, and only when job.json is a readable
        Evrakçı job whose id matches its folder. Anything else is left alone.
        """
        if not self.root.is_dir():
            return []
        limit = (time.time() if now is None else now) - days * 86400
        deleted = []
        for folder in sorted(self.root.iterdir()):
            path = folder / "job.json"
            try:
                if folder.is_symlink() or not folder.is_dir() or not path.is_file():
                    continue
                if path.stat().st_mtime >= limit:
                    continue
                if self.load(folder.name).id != folder.name:
                    continue
            except (JobFileError, KeyError, OSError):
                continue
            try:
                shutil.rmtree(folder)
                deleted.append(folder.name)
            except OSError as error:
                if on_error:
                    on_error(f"{folder.name}: {error}")
        return deleted

    def delete(self, job_id: str) -> None:
        if not self._job_file(job_id).is_file():
            raise KeyError(job_id)
        shutil.rmtree(self._job_dir(job_id))
