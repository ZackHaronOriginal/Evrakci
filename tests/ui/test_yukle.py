import pytest
from fakes import empty_page, make_pdf, qr_page, text_page

from evrakci.pipeline.job import job_to_dict
from evrakci.pipeline.store import JobStore
from evrakci.ui.yukle import YukleScreen


@pytest.fixture
def pdfs(tmp_path):
    (tmp_path / "in").mkdir()
    first = make_pdf(tmp_path / "in" / "tarama-1.pdf", [text_page("A"), qr_page(), text_page("B")])
    second = make_pdf(tmp_path / "in" / "tarama-2.pdf", [text_page("C"), empty_page()])
    return [first, second]


def _comparable(job):
    data = job_to_dict(job)
    data.pop("id")
    return data


def test_creating_a_job_through_the_screen_matches_the_cli(qtbot, tmp_path, pdfs):
    screen_store = JobStore(tmp_path / "screen")
    cli_store = JobStore(tmp_path / "cli")
    screen = YukleScreen(screen_store)
    qtbot.addWidget(screen)
    with qtbot.waitSignal(screen.job_opened, timeout=20000) as opened:
        screen.create_job(pdfs, "Kasım")
    expected = cli_store.create_job("Kasım", pdfs)
    assert _comparable(opened.args[0]) == _comparable(expected)
    assert screen.jobs.count() == 1
    assert "Kasım" in screen.jobs.item(0).text()


def test_cancelling_analysis_leaves_no_job(qtbot, tmp_path, pdfs, monkeypatch):
    import threading

    store = JobStore(tmp_path / "s")
    gate = threading.Event()
    real = store.create_job

    def held(name, paths, progress=None):
        gate.wait(5)  # the user presses İptal while analysis runs
        return real(name, paths, progress)

    monkeypatch.setattr(store, "create_job", held)
    screen = YukleScreen(store)
    qtbot.addWidget(screen)
    with qtbot.waitSignal(screen.task_finished, timeout=20000):
        screen.create_job(pdfs, "İptal")
        screen.cancel_button.click()
        gate.set()
    assert store.list_jobs() == []
    assert screen.progress_label.text().startswith("İptal edildi")


def test_batches_are_listed_and_moving_one_is_undoable(qtbot, tmp_path, pdfs):
    store = JobStore(tmp_path / "s")
    screen = YukleScreen(store)
    qtbot.addWidget(screen)
    with qtbot.waitSignal(screen.job_opened, timeout=20000):
        screen.create_job(pdfs, "Sıra")
    assert screen.batches.count() == 2
    assert "tarama-1.pdf" in screen.batches.item(0).text()
    screen.batches.setCurrentRow(1)
    screen.up_button.click()
    assert "tarama-2.pdf" in screen.batches.item(0).text()
    screen.controller.undo()
    assert "tarama-1.pdf" in screen.batches.item(0).text()
