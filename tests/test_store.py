import pytest
from fakes import make_pdf, qr_page, text_page

from evrakci.pipeline.analyze import BatchError
from evrakci.pipeline.store import JobFileError, JobStore


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
