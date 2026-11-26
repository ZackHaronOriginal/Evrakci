import pytest
from fakes import a5_page, landscape_page, make_pdf, qr_page, text_page, without_sizes

from evrakci.pipeline.analyze import BatchError
from evrakci.pipeline.job import apply_page_sizes
from evrakci.pipeline.store import BUSY_TRIES, JobFileError, JobStore


def test_create_save_load(tmp_path):
    src = make_pdf(tmp_path / "tarama.pdf", [text_page(), qr_page(), text_page()])
    store = JobStore(tmp_path / "Gökçe Şahin" / "jobs")
    job = store.create_job("Seçim 2026", [src, src])
    assert [b.id for b in job.batches] == ["b1", "b2"]
    assert len(job.pages) == 6 and job.pages["b2/1"].is_separator
    job.manual_cuts.add("b1/2")
    store.save(job)
    assert store.load(job.id) == job
    assert [j.id for j in store.list_jobs()] == [job.id]
    assert store.batch_file(job, job.batches[0]).exists()
    store.delete(job.id)
    assert store.list_jobs() == []
    with pytest.raises(KeyError):
        store.load(job.id)


def test_add_batch(tmp_path):
    src = make_pdf(tmp_path / "t.pdf", [text_page(), text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("x", [src])
    batch = store.add_batch(job, src)
    assert batch.id == "b2" and store.load(job.id).ordered_page_ids()[-1] == "b2/1"


def test_bad_batch_leaves_no_job(tmp_path):
    good = make_pdf(tmp_path / "ok.pdf", [text_page()])
    bad = tmp_path / "bozuk.pdf"
    bad.write_bytes(b"%PDF-1.4 broken")
    store = JobStore(tmp_path / "jobs")
    with pytest.raises(BatchError):
        store.create_job("x", [good, bad])
    assert store.list_jobs() == [] and not any((tmp_path / "jobs").glob("*"))


def test_bad_batch_leaves_job_unchanged(tmp_path):
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    bad = tmp_path / "bozuk.pdf"
    bad.write_bytes(b"nope")
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("x", [src])
    with pytest.raises(BatchError):
        store.add_batch(job, bad)
    assert store.load(job.id).batches == job.batches == [job.batches[0]]


def test_corrupt_job_file(tmp_path):
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    good = store.create_job("iyi", [src])
    bad = store.create_job("kötü", [src])
    (tmp_path / "jobs" / bad.id / "job.json").write_text("{bozuk", encoding="utf-8")
    with pytest.raises(JobFileError):
        store.load(bad.id)
    seen = []
    assert [j.id for j in store.list_jobs(on_error=seen.append)] == [good.id]
    assert seen == [bad.id]


def test_remove_batch_deletes_file(tmp_path):
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("x", [src, src])
    path = store.batch_file(job, job.batches[1])
    store.remove_batch(job, "b2")
    assert not path.exists() and [b.id for b in store.load(job.id).batches] == ["b1"]


def test_progress_total_known_from_the_start(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page(), text_page()])
    b = make_pdf(tmp_path / "b.pdf", [text_page()])
    calls = []
    JobStore(tmp_path / "jobs").create_job("x", [a, b], progress=lambda d, t: calls.append((d, t)))
    assert calls == [(1, 3), (2, 3), (3, 3)]


def test_add_batch_rolls_back_when_save_fails(tmp_path, monkeypatch):
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("x", [src])

    def broken_save(job):
        raise OSError("disk full")

    monkeypatch.setattr(store, "save", broken_save)
    with pytest.raises(OSError):
        store.add_batch(job, src)
    assert [b.id for b in job.batches] == ["b1"] and "b2/0" not in job.pages
    assert not (tmp_path / "jobs" / job.id / "batches" / "b2.pdf").exists()


def test_prepared_batch_is_attached_as_a_separate_step(tmp_path):
    from fakes import make_pdf, qr_page, text_page

    from evrakci.pipeline.store import JobStore

    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [make_pdf(tmp_path / "a.pdf", [text_page()])])
    prepared = store.prepare_batch(job, make_pdf(tmp_path / "b.pdf", [qr_page(), text_page()]))
    assert len(job.batches) == 1  # preparing never changes the job
    assert store.batch_file(job, prepared.batch).is_file()
    job.attach_batch(prepared.batch, prepared.pages)
    assert [b.id for b in job.batches] == ["b1", "b2"]
    assert job.pages["b2/0"].is_separator
    with pytest.raises(ValueError):
        job.attach_batch(prepared.batch, prepared.pages)


def test_prepare_batch_reports_progress_per_page(tmp_path):
    from fakes import make_pdf, text_page

    from evrakci.pipeline.store import JobStore

    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [make_pdf(tmp_path / "a.pdf", [text_page()])])
    seen = []
    store.prepare_batch(job, make_pdf(tmp_path / "b.pdf", [text_page(), text_page()]),
                        lambda done, total: seen.append((done, total)))
    assert seen == [(1, 2), (2, 2)]


def test_save_dict_writes_the_same_file_as_save_and_leaves_no_temporary(tmp_path):
    from evrakci.pipeline.job import job_to_dict

    src = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Anlık", [src])
    job.manual_cuts.add("b1/2")
    store.save(job)
    by_save = store._job_file(job.id).read_bytes()
    snapshot = job_to_dict(job)
    job.manual_cuts.clear()  # the snapshot is plain data: later edits do not reach it
    store.save_dict(job.id, snapshot)
    assert store._job_file(job.id).read_bytes() == by_save
    assert store.load(job.id).manual_cuts == {"b1/2"}
    assert not list(store._job_dir(job.id).glob("*.tmp"))


def test_save_dict_refuses_an_id_that_is_not_a_folder_name(tmp_path):
    store = JobStore(tmp_path / "jobs")
    with pytest.raises(KeyError):
        store.save_dict("../kacak", {"id": "x"})
    assert not (tmp_path / "kacak").exists()


def test_save_dict_that_fails_keeps_the_old_file(tmp_path, monkeypatch):
    import os

    from evrakci.pipeline.job import job_to_dict

    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Eski", [src])
    before = store._job_file(job.id).read_bytes()

    def broken(*_args):
        raise OSError("yazılamadı")

    monkeypatch.setattr(os, "replace", broken)
    with pytest.raises(OSError):
        store.save_dict(job.id, {**job_to_dict(job), "name": "Yeni"})
    assert store._job_file(job.id).read_bytes() == before


def test_save_retries_a_replace_that_a_reader_blocks(tmp_path, monkeypatch):
    import os

    store = JobStore(tmp_path / "jobs")
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    job = store.create_job("x", [src])
    job.name = "yeni ad"
    real, sleeps, calls = os.replace, [], []

    def replace(source, target):
        calls.append(1)
        if len(calls) <= 2:
            raise PermissionError("kullanımda")
        return real(source, target)

    monkeypatch.setattr("evrakci.pipeline.store.os.replace", replace)
    monkeypatch.setattr("evrakci.pipeline.store.time.sleep", sleeps.append)
    store.save(job)
    assert len(calls) == 3 and sleeps == pytest.approx([0.05, 0.1])
    monkeypatch.undo()
    assert store.load(job.id).name == "yeni ad"


def test_save_gives_up_after_busy_tries_blocked_replaces(tmp_path, monkeypatch):
    store = JobStore(tmp_path / "jobs")
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    job = store.create_job("x", [src])
    calls = []

    def replace(source, target):
        calls.append(1)
        raise PermissionError("kullanımda")

    monkeypatch.setattr("evrakci.pipeline.store.os.replace", replace)
    monkeypatch.setattr("evrakci.pipeline.store.time.sleep", lambda _s: None)
    with pytest.raises(PermissionError):
        store.save(job)
    assert len(calls) == BUSY_TRIES == 8


def test_load_retries_a_read_that_a_replace_blocks(tmp_path, monkeypatch):
    from pathlib import Path

    store = JobStore(tmp_path / "jobs")
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    job = store.create_job("x", [src])
    real, sleeps, calls = Path.read_text, [], []

    def read_text(self, *args, **kwargs):
        calls.append(1)
        if len(calls) <= 2:
            raise PermissionError("Permission denied")
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr("evrakci.pipeline.store.time.sleep", sleeps.append)
    assert store.load(job.id).name == "x"
    assert len(calls) == 3 and sleeps == pytest.approx([0.05, 0.1])


def test_load_gives_up_after_busy_tries_blocked_reads(tmp_path, monkeypatch):
    from pathlib import Path

    store = JobStore(tmp_path / "jobs")
    src = make_pdf(tmp_path / "t.pdf", [text_page()])
    job = store.create_job("x", [src])
    calls = []

    def read_text(self, *args, **kwargs):
        calls.append(1)
        raise PermissionError("Permission denied")

    monkeypatch.setattr(Path, "read_text", read_text)
    monkeypatch.setattr("evrakci.pipeline.store.time.sleep", lambda _s: None)
    with pytest.raises(JobFileError) as info:
        store.load(job.id)
    assert isinstance(info.value.__cause__, PermissionError)
    assert len(calls) == BUSY_TRIES == 8


def _fill(store, job):
    """What the window does when an older job opens: read the sizes, store them in the job."""
    return apply_page_sizes(job, JobStore.read_sizes(store.size_requests(job)))


def _old_job(tmp_path, pages):
    """A stored job as an older program wrote it: the file has no page sizes."""
    import json

    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Eski", [make_pdf(tmp_path / "a.pdf", pages)])
    path = store._job_file(job.id)
    path.write_text(json.dumps(without_sizes(json.loads(path.read_text(encoding="utf-8")))),
                    encoding="utf-8")
    return store, store.load(job.id)


def test_a_new_job_knows_its_page_sizes_and_keeps_them_in_the_file(tmp_path):
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Yeni", [make_pdf(tmp_path / "a.pdf",
                                             [text_page(), a5_page(), landscape_page()])])
    assert [i.has_size for i in job.pages.values()] == [True] * 3
    again = store.load(job.id)
    assert again == job
    assert store.size_requests(again) == []  # nothing to fill


def test_the_sizes_of_an_old_job_are_read_once(tmp_path):
    store, job = _old_job(tmp_path, [text_page(), a5_page(), landscape_page()])
    assert [i.has_size for i in job.pages.values()] == [False] * 3
    assert _fill(store, job) == 3
    assert job.pages["b1/1"].width_mm == pytest.approx(148.0, abs=0.2)
    assert job.pages["b1/2"].width_mm == pytest.approx(297.0, abs=0.2)
    assert _fill(store, job) == 0  # once: a second call reads nothing


def test_filling_sizes_does_not_touch_the_edits(tmp_path):
    store, job = _old_job(tmp_path, [text_page(), text_page()])
    job.rotate("b1/0", 90)
    job.delete_page("b1/1")
    store.save(job)
    before = (dict(job.rotations), set(job.deleted), job.drop_empty, list(job.batches))
    _fill(store, job)
    assert (dict(job.rotations), set(job.deleted), job.drop_empty, list(job.batches)) == before


def test_a_page_whose_file_is_gone_stays_unknown(tmp_path):
    store, job = _old_job(tmp_path, [text_page(), text_page()])
    store.batch_file(job, job.batches[0]).unlink()
    assert _fill(store, job) == 0
    assert [i.has_size for i in job.pages.values()] == [False, False]
    assert store._job_file(job.id).is_file()  # nothing was lost


def test_a_batch_file_that_is_not_the_scanned_one_is_not_trusted(tmp_path):
    store, job = _old_job(tmp_path, [text_page(), text_page()])
    make_pdf(store.batch_file(job, job.batches[0]), [a5_page()])  # one page, not two
    assert _fill(store, job) == 0


def test_size_requests_name_only_the_batches_with_unknown_pages(tmp_path):
    store, job = _old_job(tmp_path, [text_page(), text_page()])
    extra = store.prepare_batch(job, make_pdf(tmp_path / "b.pdf", [a5_page()]))
    job.attach_batch(extra.batch, extra.pages)  # a new batch knows its sizes
    requests = store.size_requests(job)
    assert [r.batch_id for r in requests] == ["b1"]
    assert requests[0].page_ids == ("b1/0", "b1/1")


def test_read_sizes_runs_without_a_job_and_reports_progress(tmp_path):
    store, job = _old_job(tmp_path, [text_page(), a5_page()])
    seen = []
    sizes = JobStore.read_sizes(store.size_requests(job), lambda d, t: seen.append((d, t)))
    assert seen == [(2, 2)]
    assert sizes["b1/1"][0] == pytest.approx(148.0, abs=0.2)
    assert not job.pages["b1/1"].has_size  # the job was not touched


def test_filling_800_pages_is_fast(tmp_path):
    import time

    from evrakci.pipeline.analyze import PageInfo
    from evrakci.pipeline.job import Batch, page_id

    store, job = _old_job(tmp_path, [text_page() if i % 2 else a5_page() for i in range(40)])
    source = store.batch_file(job, job.batches[0])
    for n in range(2, 21):  # 800 pages: twenty batches of the same 40-page file
        batch = Batch(f"b{n}", "a.pdf", 40)
        store.batch_file(job, batch).write_bytes(source.read_bytes())
        job.batches.append(batch)
        for i in range(40):
            job.pages[page_id(batch.id, i)] = PageInfo(0.05, False)
    start = time.perf_counter()
    assert _fill(store, job) == 800
    elapsed = time.perf_counter() - start
    print(f"reading 800 page sizes: {elapsed * 1000:.0f} ms")
    assert elapsed < 3.0, elapsed


def test_two_writers_of_one_job_never_lose_a_write(tmp_path):
    """Each write has its own temporary file: two threads saving the same job at once both
    succeed and the file is always one whole snapshot (CI: FileNotFoundError on job.json.tmp)."""
    import threading

    from evrakci.pipeline.job import job_to_dict

    store = JobStore(tmp_path / "jobs")
    job = store.create_job("A", [make_pdf(tmp_path / "a.pdf", [text_page("A")])])
    data = job_to_dict(job)
    errors: list[BaseException] = []

    def write(name: str) -> None:
        try:
            for n in range(100):
                store.save_dict(job.id, {**data, "name": f"{name}{n}"})
        except BaseException as error:  # noqa: BLE001 - the test reports any failure
            errors.append(error)

    threads = [threading.Thread(target=write, args=(name,)) for name in ("x", "y")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []
    assert store.load(job.id).name in {"x99", "y99"}
    assert [p.name for p in (tmp_path / "jobs" / job.id).glob("*.tmp")] == []
