"""`evrakci is sec bos --esik`: the same pages as the core criterion `bos` (I-03)."""

import pytest
from fakes import empty_page, make_pdf, qr_page, text_page

from evrakci.cli import main
from evrakci.pipeline.analyze import EMPTY_INK_RATIO
from evrakci.pipeline.select import Criterion, evaluate
from evrakci.pipeline.store import JobStore


def make_job(tmp_path, capsys, pages):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", pages)
    assert main(["--kok", str(root), "is", "olustur", "Boş", str(pdf)]) == 0
    return root, capsys.readouterr().out.strip().splitlines()[-1]


def printed_positions(out: str) -> list[int]:
    line = next(x for x in out.splitlines() if x.startswith("sayfa "))
    return [int(n) for n in line.removeprefix("sayfa ").split(", ")]


def test_the_cli_gives_the_pages_the_core_gives(tmp_path, capsys):
    dusty = empty_page(speckles=1400)  # between 0,05 % and 0,3 % of ink
    root, job_id = make_job(
        tmp_path, capsys, [text_page(), empty_page(), text_page(), dusty, qr_page()])
    job = JobStore(root).load(job_id)
    order = job.ordered_page_ids()
    assert 0.0005 < job.pages[order[3]].ink_ratio < EMPTY_INK_RATIO
    cases = [([], 0.3), (["--esik", "0,3"], 0.3), (["--esik", "0.3"], 0.3),
             (["--esik", "0,1"], 0.1), (["--esik", "5,0"], 5.0)]
    counts = []
    for extra, percent in cases:
        assert main(["--kok", str(root), "is", "sec", job_id, "bos", *extra]) == 0
        out = capsys.readouterr().out
        match = evaluate(job, Criterion("bos", {"ink": round(percent / 100, 6)}))
        counts.append(match.count())
        if match.count():
            assert f"{match.count()} sayfa seçildi." in out
            assert printed_positions(out) == [order.index(pid) + 1 for pid in match.page_ids]
        else:
            assert "Eşleşen sayfa yok." in out
    assert counts == [2, 2, 2, 1, 2]  # the dusty page needs more than 0,1 %; the QR page never


@pytest.mark.parametrize("bad", ["x", "0", "0,05", "5,1", "-1"])
def test_the_limit_must_be_a_percentage_in_range(tmp_path, capsys, bad):
    _root, job_id = make_job(tmp_path, capsys, [text_page(), empty_page()])
    assert main(["--kok", str(tmp_path / "kok"), "is", "sec", job_id, "bos",
                 f"--esik={bad}"]) == 2
    assert "0,1 ile 5,0 arası" in capsys.readouterr().err


def test_sil_deletes_only_the_blank_pages(tmp_path, capsys):
    root, job_id = make_job(
        tmp_path, capsys, [text_page(), empty_page(), text_page(), empty_page()])
    assert main(["--kok", str(root), "is", "sec", job_id, "bos", "--sil"]) == 0
    job = JobStore(root).load(job_id)
    assert sorted(job.deleted) == [job.ordered_page_ids()[i] for i in (1, 3)]
