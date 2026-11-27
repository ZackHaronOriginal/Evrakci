"""`evrakci is sec farkli`: the same pages as the core criterion `farkli` (I-04)."""

import json
import os

from fakes import a5_page, landscape_page, make_pdf, text_page, without_sizes

from evrakci.cli import main
from evrakci.pipeline.select import Criterion, evaluate
from evrakci.pipeline.store import JobStore

PAGES = [text_page(), text_page(), landscape_page(), a5_page(), text_page(), text_page()]


def make_job(tmp_path, capsys, pages=PAGES):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", pages)
    assert main(["--kok", str(root), "is", "olustur", "Farklı", str(pdf)]) == 0
    return root, capsys.readouterr().out.strip().splitlines()[-1]


def printed_positions(out: str) -> list[int]:
    line = next(x for x in out.splitlines() if x.startswith("sayfa "))
    return [int(n) for n in line.removeprefix("sayfa ").split(", ")]


def run(root, job_id, *extra):
    return main(["--kok", str(root), "is", "sec", job_id, "farkli", *extra])


def test_the_cli_gives_the_pages_the_core_gives(tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys)
    job = JobStore(root).load(job_id)
    order = job.ordered_page_ids()
    cases = [([], ("boyut", "yon")), (["--boyut"], ("boyut",)), (["--yon"], ("yon",)),
             (["--boyut", "--yon"], ("boyut", "yon"))]
    results = []
    for extra, by in cases:
        assert run(root, job_id, *extra) == 0
        out = capsys.readouterr().out
        match = evaluate(job, Criterion("farkli", {"by": list(by), "reference": "is"}))
        assert f"{match.count()} sayfa seçildi." in out
        assert printed_positions(out) == [order.index(pid) + 1 for pid in match.page_ids]
        results.append(printed_positions(out))
    assert results == [[3, 4], [4], [3], [3, 4]]  # the sideways page, then the A5 page


def test_the_reference_can_be_each_document(tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys)
    assert run(root, job_id, "--karsilastir", "belge") == 0  # one document: same as the job
    assert printed_positions(capsys.readouterr().out) == [3, 4]


def test_nothing_different_says_so(tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys, [text_page(), text_page()])
    assert run(root, job_id) == 0
    assert "Eşleşen sayfa yok." in capsys.readouterr().out


def test_an_older_job_is_counted_with_sizes_read_in_memory_and_the_file_is_not_written(
        tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys)
    path = root / job_id / "job.json"
    path.write_text(json.dumps(without_sizes(json.loads(path.read_text(encoding="utf-8")))),
                    encoding="utf-8")
    os.utime(path, (1_000_000_000, 1_000_000_000))
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert run(root, job_id) == 0
    assert printed_positions(capsys.readouterr().out) == [3, 4]
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before  # nothing was saved
    assert "width_mm" not in path.read_text(encoding="utf-8")


def test_pages_of_unknown_size_are_named_not_marked(tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys)
    path = root / job_id / "job.json"
    path.write_text(json.dumps(without_sizes(json.loads(path.read_text(encoding="utf-8")))),
                    encoding="utf-8")
    (root / job_id / "batches" / "b1.pdf").unlink()
    assert run(root, job_id) == 0
    out = capsys.readouterr().out
    assert "Eşleşen sayfa yok." in out and "Boyutu bilinmiyor (6)" in out


def test_the_options_are_checked(tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys, [text_page(), a5_page()])
    assert run(root, job_id, "--karsilastir", "x") == 2


def test_is_sec_sablon_reads_missing_sizes_of_an_older_job_like_the_farkli_path(tmp_path, capsys):
    root, job_id = make_job(tmp_path, capsys)
    path = root / job_id / "job.json"
    path.write_text(
        json.dumps(without_sizes(json.loads(path.read_text(encoding="utf-8")))), encoding="utf-8"
    )
    templates = str(tmp_path / "sablonlar")
    assert main(["--sablon-kok", templates, "sablon", "olustur", "Süzgeç"]) == 0
    template_id = capsys.readouterr().out.strip().splitlines()[-1]
    assert (
        main(
            ["--sablon-kok", templates, "sablon", "filtre-ekle", template_id, "Farklılar", "farkli"]
        )
        == 0
    )
    capsys.readouterr()
    for extra in ([], ["--filtre", "Farklılar"]):
        assert (
            main(
                [
                    "--kok",
                    str(root),
                    "--sablon-kok",
                    templates,
                    "is",
                    "sec",
                    job_id,
                    "--sablon",
                    template_id,
                    *extra,
                ]
            )
            == 0
        )
        out = capsys.readouterr().out
        assert "Eşleşen sayfa yok." not in out and printed_positions(out) == [3, 4]
    assert "width_mm" not in path.read_text(encoding="utf-8")  # read in memory, not written
