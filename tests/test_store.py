import pytest
from fakes import make_pdf, qr_page, text_page

from evrakci.pipeline.analyze import BatchError
from evrakci.pipeline.store import JobStore


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
