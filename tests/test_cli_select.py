"""`evrakci is sec`: the same pages as pipeline/select.py (and so as the window's dialog)."""

from fakes import make_pdf, qr_page, text_page

from evrakci.cli import main
from evrakci.pipeline.select import Criterion, evaluate
from evrakci.pipeline.store import JobStore

PAGES = [text_page()] * 4 + [qr_page()] + [text_page()] * 3 + [qr_page()] + [text_page()] * 2


def setup_job(tmp_path, capsys):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", PAGES)
    assert main(["--kok", str(root), "is", "olustur", "Seç", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]

    def run(*args):
        return main(["--kok", str(root), *args])

    return run, JobStore(root), job_id


def printed_positions(out: str) -> list[int]:
    line = next(x for x in out.splitlines() if x.startswith("sayfa "))
    return [int(n) for n in line.removeprefix("sayfa ").split(", ")]


def test_cli_gives_the_pages_the_core_gives(tmp_path, capsys):
    run, store, job_id = setup_job(tmp_path, capsys)
    job = store.load(job_id)
    order = job.ordered_page_ids()
    cases = [("tek", {}, []), ("cift", {}, []), ("belge", {"number": 2}, ["--numara", "2"])]
    for kind, params, extra in cases:
        assert run("is", "sec", job_id, kind, *extra) == 0
        out = capsys.readouterr().out
        match = evaluate(job, Criterion(kind, params))
        assert f"{match.count()} sayfa seçildi." in out
        assert printed_positions(out) == [order.index(pid) + 1 for pid in match.page_ids]
    assert printed_positions_of(run, capsys, job_id, "tek") == [1, 3, 6, 8, 10]
    assert printed_positions_of(run, capsys, job_id, "cift") == [2, 4, 7, 11]


def printed_positions_of(run, capsys, job_id, kind):
    assert run("is", "sec", job_id, kind) == 0
    return printed_positions(capsys.readouterr().out)


def test_sil_deletes_the_selected_pages_like_del(tmp_path, capsys):
    run, store, job_id = setup_job(tmp_path, capsys)
    assert run("is", "sec", job_id, "cift", "--sil") == 0
    assert "Sayfa 2, 4, 7, 11 silindi" in capsys.readouterr().out
    job = store.load(job_id)
    assert {job.page_at(n) for n in (2, 4, 7, 11)} == job.deleted
    run("is", "goster", job_id)
    assert "1. belge: sayfa 1, 3" in capsys.readouterr().out


def test_nothing_matches_and_errors(tmp_path, capsys):
    run, _store, job_id = setup_job(tmp_path, capsys)
    assert run("is", "sec", job_id, "belge", "--numara", "9") == 0
    assert "Eşleşen sayfa yok." in capsys.readouterr().out
    assert run("is", "sec", job_id, "belge") == 2
    assert "--numara" in capsys.readouterr().err  # argparse's own "required" message
    assert run("is", "sec", "yok", "tek") == 2
    assert "İş bulunamadı" in capsys.readouterr().err
    assert run("is", "sec", job_id, "bos") == 2
