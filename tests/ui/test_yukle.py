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
    # the job list is the empty page's "Son işler" (a QListWidget before the A rebuild)
    assert [e.name for e in screen.empty.entries] == ["Kasım"]


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
        screen.cancel()  # İptal et (Ctrl+.); the old in-page button moved to the command bar
        gate.set()
    assert store.list_jobs() == []
    assert screen.last_message.startswith("İptal edildi")


def test_batches_are_listed_and_moving_one_is_undoable(qtbot, tmp_path, pdfs):
    store = JobStore(tmp_path / "s")
    screen = YukleScreen(store)
    qtbot.addWidget(screen)
    with qtbot.waitSignal(screen.job_opened, timeout=20000):
        screen.create_job(pdfs, "Sıra")
    assert [i.name for i in screen.model.items if i.kind == "batch"] == [
        "tarama-1.pdf", "tarama-2.pdf"]
    screen.table.select_batch(screen.controller.job.batches[1].id)
    screen.move_batch(-1)
    assert [i.name for i in screen.model.items if i.kind == "batch"] == [
        "tarama-2.pdf", "tarama-1.pdf"]
    screen.controller.undo()
    assert [i.name for i in screen.model.items if i.kind == "batch"] == [
        "tarama-1.pdf", "tarama-2.pdf"]
