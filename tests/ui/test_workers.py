"""run_background and the loading card: the window keeps running while work blocks, the card
shows after 300 ms and stays 400 ms, widgets are only touched on the window thread, and the
reading-engine probe never runs on the window thread."""
from __future__ import annotations

import inspect
import re
import threading
import time

import pytest
from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from saving import wait_saved

from evrakci.pipeline.store import JobFileError, JobStore
from evrakci.ui import gc_guard, loading, workers
from evrakci.ui.loading import LoadingCard
from evrakci.ui.workers import run_background


@pytest.fixture
def owner(qtbot):
    widget = QWidget()
    widget.resize(800, 500)
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_window_thread_keeps_running_while_a_job_loads(qtbot, owner, tmp_path, monkeypatch):
    """(a) Longest gap between 20 ms ticks stays under 100 ms while JobStore.load blocks 1.5 s."""
    store = JobStore(tmp_path / "jobs")
    release = threading.Event()
    monkeypatch.setattr(JobStore, "load", lambda self, job_id: release.wait(1.5) or "yüklendi")
    ticks: list[float] = []
    collected = dict(gc_guard.stats)
    timer = QTimer(owner)
    timer.setInterval(20)
    timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
    timer.start()
    got: list = []
    handle = run_background(owner, lambda _p: store.load("x"), title="İş açılıyor",
                            on_done=got.append)
    assert handle is not None and handle.running
    qtbot.waitUntil(lambda: bool(got), timeout=5000)
    timer.stop()
    gaps = [b - a for a, b in zip(ticks, ticks[1:], strict=False)]
    assert got == ["yüklendi"]
    assert len(ticks) >= 50
    # when the longest gap happened (seconds after the first tick) and the collections that ran,
    # so a CI miss (B-114) can be told apart from a real stall
    worst = max(range(len(gaps)), key=gaps.__getitem__) if gaps else -1
    assert max(gaps) < 0.1, (round(max(gaps), 3), round(ticks[worst] - ticks[0], 3),
                             sorted(round(g, 3) for g in gaps)[-5:],
                             {k: gc_guard.stats[k] - collected.get(k, 0) for k in gc_guard.stats})


def test_loading_card_shows_after_300_ms_and_stays_400_ms(qtbot, owner, monkeypatch):
    """(b) Short work: no card. Long work: card after 300 ms, hidden no sooner than 400 ms
    after it appeared (the clock is replaced, so the minimum is measured exactly)."""
    now = [100.0]
    monkeypatch.setattr(workers, "_clock", lambda: now[0])
    quick: list = []
    run_background(owner, lambda _p: 1, title="İş açılıyor", on_done=quick.append)
    qtbot.waitUntil(lambda: quick == [1], timeout=3000)
    assert getattr(owner, "loading_card", None) is None or not owner.loading_card.isVisible()

    gate = threading.Event()
    slow: list = []
    run_background(owner, lambda _p: gate.wait(5) and 2, title="İş açılıyor", name="Kasım",
                   on_done=slow.append)
    assert getattr(owner, "loading_card", None) is None or not owner.loading_card.isVisible()
    qtbot.waitUntil(lambda: getattr(owner, "loading_card", None) is not None
                    and owner.loading_card.isVisible(), timeout=3000)
    card = owner.loading_card
    assert card.title.text() == "İş açılıyor" and card.name.text() == "Kasım"
    gate.set()
    qtbot.waitUntil(lambda: slow == [2], timeout=3000)
    assert card.isVisible()  # still inside its 400 ms
    now[0] += 0.5
    qtbot.waitUntil(lambda: not card.isVisible(), timeout=3000)


def test_widget_use_off_the_window_thread_is_refused(qtbot):
    """(h) LoadingCard methods raise when called from a thread; worker functions in the
    modules that use run_background do not name QWidget."""
    card = LoadingCard()
    qtbot.addWidget(card)
    errors: list[BaseException] = []

    def call(method, *args):
        def run():
            try:
                method(*args)
            except RuntimeError as error:
                errors.append(error)
        thread = threading.Thread(target=run)
        thread.start()
        thread.join()

    call(card.show_loading, "İş açılıyor", "")
    call(card.show_progress, 1, 2)
    call(card.close)
    assert len(errors) == 3
    assert QThread.currentThread() is QApplication.instance().thread()
    card.show_loading("İş açılıyor")  # on the window thread it works
    assert card.isVisible()
    forbidden = re.compile(r"QWidget|QPixmap|QAction|\bcontroller\b|\.model\b")
    worker_lambda = re.compile(r"(?:Task\(|work = )lambda [^\n]*")
    scanned = 0
    for module in ("degerler", "sablon_read", "sablon_live", "ocr_engine", "yukle", "disa_aktar",
                   "main_window"):
        source = inspect.getsource(__import__(f"evrakci.ui.{module}", fromlist=["x"]))
        found = [m.group() for m in worker_lambda.finditer(source)]
        lines = source.splitlines()
        for number, line in enumerate(lines):
            head = re.match(r"(\s*)def (?:run|work)\(_?progress\):", line)
            if head is None:
                continue
            body = [line]
            for later in lines[number + 1:]:  # the lines indented deeper than the def
                if later.strip() and len(later) - len(later.lstrip()) <= len(head.group(1)):
                    break
                body.append(later)
            found.append("\n".join(body))
        for text in found:
            scanned += 1
            assert not forbidden.search(text), (module, text)
    assert scanned >= 6  # yukle, disa_aktar, ocr_engine, sablon_live x2, degerler, main_window
    assert "QWidget" not in inspect.getsource(loading.assert_window_thread)


def test_engine_probe_runs_off_the_window_thread(qtbot, tmp_path):
    """(i) Oku in Değerler and the Şablonlar read probe the engine in a worker."""
    from fakes import make_pdf, qr_page, text_page

    from evrakci.pipeline.ocr.engine import Reading
    from evrakci.pipeline.templates.store import TemplateStore
    from evrakci.ui.main_window import MainWindow
    from evrakci.ui.sablon_read import ReadInput, read_examples

    seen: list[tuple[str, QThread]] = []

    class Engine:
        name = "sahte"

        def available(self):
            seen.append(("available", QThread.currentThread()))
            return "yok"

        def read_region(self, image):
            return Reading("1", 1.0)

    store = JobStore(tmp_path / "jobs")
    templates = TemplateStore(tmp_path / "tpl")
    window = MainWindow(store, templates, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Kasım")
    window.degerler.engine = Engine
    window.show_tab("degerler")
    window.degerler.read_values(False)
    qtbot.waitUntil(lambda: window.degerler.task is None and bool(seen), timeout=10000)
    assert seen and all(t is not QApplication.instance().thread() for _, t in seen)

    seen.clear()
    from evrakci.ui.workers import Task, start
    job = ReadInput(None, {}, {}, {}, Engine())
    done: list = []
    task = Task(lambda _p: read_examples(job, []))
    task.signals.failed.connect(done.append)
    start(task)
    qtbot.waitUntil(lambda: bool(done), timeout=5000)
    assert done == ["yok"]
    assert all(t is not QApplication.instance().thread() for _, t in seen)


# -- opening a job through run_background (c) to (g) ------------------------------------------
def _two_jobs(qtbot, tmp_path):
    from fakes import make_pdf, qr_page, text_page

    from evrakci.pipeline.templates.store import TemplateStore
    from evrakci.ui.main_window import MainWindow

    store = JobStore(tmp_path / "jobs")
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page()])
    first, second, third = (store.create_job(name, [pdf]) for name in ("A", "B", "C"))
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.show()
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.open_job_id(first.id)
    assert window.controller().job.id == first.id
    return window, store, first, second, third


def _slow_load(monkeypatch, gate, slow_id, *, error=None, answer=None):
    real = JobStore.load

    def load(self, job_id):
        if job_id != slow_id or QThread.currentThread() is QApplication.instance().thread():
            return real(self, job_id)  # only the worker's load is slowed or broken
        gate.wait(5)
        if error is not None:
            raise error
        return real(self, answer or job_id)

    monkeypatch.setattr(JobStore, "load", load)


def _wait_card(qtbot, window):
    qtbot.waitUntil(lambda: window.loading_card.isVisible(), timeout=3000)
    return window.loading_card


def _bytes(store, job_id):
    return store._job_file(job_id).read_bytes()


@pytest.mark.parametrize("how", ["key", "button"])
def test_cancel_leaves_the_open_job_as_it_was(qtbot, tmp_path, monkeypatch, how):
    """(c) Ctrl+. and the card's button: old job open, no new controller, nothing saved."""
    window, store, first, second, _third = _two_jobs(qtbot, tmp_path)
    window.show_tab("yukle")
    before = (_bytes(store, first.id), _bytes(store, second.id), window.controller())
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id)
    opened: list = []
    window.yukle.job_opened.connect(opened.append)
    window.yukle.open_job_id(second.id)
    card = _wait_card(qtbot, window)
    assert card.title.text() == "İş açılıyor" and card.cancel_button.isVisible()
    assert window.registry.action("yukle.iptal").isEnabled()
    if how == "key":
        window.registry.action("yukle.iptal").trigger()
    else:
        card.cancel_button.click()
    assert card.title.text() == "İptal ediliyor…"
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    qtbot.waitUntil(lambda: not card.isVisible(), timeout=3000)
    assert window.yukle.last_message == "İptal edildi; hiçbir şey değişmedi."
    assert window.controller() is before[2] and window.controller().job.id == first.id
    assert (_bytes(store, first.id), _bytes(store, second.id)) == before[:2]
    assert opened == []


@pytest.mark.parametrize("error", [JobFileError("bozuk dosya"), OSError("disk yok")])
def test_open_errors_are_told_and_leave_the_open_job_alone(qtbot, tmp_path, monkeypatch, error):
    """(d) JobFileError and OSError: the Turkish line and toast, the card closes, old job intact."""
    window, store, first, second, _third = _two_jobs(qtbot, tmp_path)
    before = (_bytes(store, first.id), window.controller())
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id, error=error)
    window.yukle.open_job_id(second.id)
    card = _wait_card(qtbot, window)
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    assert window.yukle.last_message == f"İş açılamadı: {error}"
    assert f"İş açılamadı: {error}" in window.toaster.current_text()
    qtbot.waitUntil(lambda: not card.isVisible(), timeout=3000)
    assert window.controller() is before[1] and _bytes(store, first.id) == before[0]


def test_second_open_while_loading_is_refused_with_the_reason(qtbot, tmp_path, monkeypatch):
    """(e) A second open, a new job and an export are refused with the busy reason."""
    window, _store, first, second, third = _two_jobs(qtbot, tmp_path)
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id)
    window.yukle.open_job_id(second.id)
    _wait_card(qtbot, window)
    with qtbot.waitSignal(window.yukle.refused, timeout=2000) as refused:
        window.yukle.open_job_id(third.id)
    assert refused.args == [workers.BUSY_REASON]
    window.open_job_switcher()
    assert window.message.text() == workers.BUSY_REASON
    for action_id in ("app.yeni_is", "app.dosya_ekle", "app.disa_aktar"):
        action = window.registry.action(action_id)
        assert not action.isEnabled() and action.toolTip() == workers.BUSY_REASON
    gate.set()
    qtbot.waitUntil(lambda: window.controller().job.id == second.id, timeout=3000)
    assert window.registry.action("app.yeni_is").isEnabled()
    assert window.registry.action("app.yeni_is").toolTip() != workers.BUSY_REASON
    assert first.id != second.id


def test_closing_the_window_while_a_job_loads_is_quiet(qtbot, tmp_path, monkeypatch):
    """(f) The loading job is cancelled first; its late result reaches nothing."""
    window, _store, first, second, _third = _two_jobs(qtbot, tmp_path)
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id)
    opened: list = []
    window.yukle.job_opened.connect(opened.append)
    window.yukle.open_job_id(second.id)
    _wait_card(qtbot, window)
    window.close()
    assert window.loading()  # still waiting for the worker; its result will be dropped
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)  # the late result is dropped
    assert not window.loading()
    assert opened == [] and window.controller().job.id == first.id


def test_result_for_a_switched_job_is_dropped(qtbot, tmp_path, monkeypatch):
    """(g) A load that answers with another job than the one asked for is not applied."""
    window, _store, first, second, third = _two_jobs(qtbot, tmp_path)
    gate = threading.Event()
    _slow_load(monkeypatch, gate, third.id, answer=second.id)
    opened: list = []
    window.yukle.job_opened.connect(opened.append)
    window.yukle.open_job_id(third.id)
    _wait_card(qtbot, window)
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    qtbot.wait(100)
    assert opened == [] and window.controller().job.id == first.id
    # the next, correct open still works: the slot was freed
    monkeypatch.undo()
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job_id(second.id)
    assert window.controller().job.id == second.id


# -- fix round 1 -----------------------------------------------------------------------------
def test_reopening_the_open_job_keeps_it_and_loads_nothing(qtbot, tmp_path, monkeypatch):
    """S1: "Tüm işler" shows the open job too; opening it again must not read the old copy from
    disk (an edit made while that read ran would be lost to the next save)."""
    window, store, first, _second, _third = _two_jobs(qtbot, tmp_path)
    controller = window.controller()
    gate = threading.Event()
    _slow_load(monkeypatch, gate, first.id)  # a reload of the open job would block here
    opened: list = []
    window.yukle.job_opened.connect(opened.append)
    window.yukle.show_job_list()
    window.yukle.open_job_id(first.id)
    assert not window.loading()  # nothing was started
    assert window.controller() is controller
    assert controller.run("Ad", lambda job: setattr(job, "name", "Düzenlendi"))
    gate.set()
    qtbot.wait(50)
    assert window.controller() is controller and window.controller().job.name == "Düzenlendi"
    wait_saved(controller)  # saving is write-behind (I-47 part b)
    assert store.load(first.id).name == "Düzenlendi"
    assert opened == [] and not window.yukle._listing


def test_late_close_of_a_finished_card_does_not_hit_the_next_job(qtbot, owner, monkeypatch):
    """S2: job A's card waits out its minimum time; job B starts meanwhile. B's card and its
    "İptal et" must still be there after A's close time has passed."""
    monkeypatch.setattr(workers, "LOADING_MIN_MS", 150)
    first: list = []
    shown = threading.Event()  # A ends only once its card is up, also on a slow machine
    run_background(owner, lambda _p: shown.wait(5) and 1, title="İş açılıyor",
                   on_done=first.append, show_after_ms=0)
    qtbot.waitUntil(lambda: getattr(owner, "loading_card", None) is not None
                    and owner.loading_card.isVisible(), timeout=3000)
    shown.set()
    qtbot.waitUntil(lambda: first == [1], timeout=3000)
    card = owner.loading_card
    assert card.isVisible()  # A is over, its card waits out the minimum
    gate = threading.Event()
    second: list = []
    handle = run_background(owner, lambda _p: gate.wait(5) and 2, title="İş siliniyor",
                            on_done=second.append, on_cancelled=lambda: second.append("iptal"))
    assert handle is not None
    qtbot.wait(250)  # past A's 150 ms
    assert card.isVisible() and card.cancel_button.isVisible()
    handle.cancel()
    gate.set()
    qtbot.waitUntil(lambda: second == ["iptal"], timeout=3000)
    qtbot.waitUntil(lambda: not card.isVisible(), timeout=3000)


def test_an_error_after_cancel_is_a_cancel_not_a_failure(qtbot, owner):
    """S2: the user cancelled and the work then raised: on_cancelled runs, not on_failed."""
    gate = threading.Event()
    seen: list = []

    def work(_progress):
        gate.wait(5)
        raise OSError("disk yok")

    handle = run_background(owner, work, title="İş açılıyor", on_done=seen.append,
                            on_failed=lambda m: seen.append("hata:" + m),
                            on_cancelled=lambda: seen.append("iptal"))
    handle.cancel()
    gate.set()
    qtbot.waitUntil(lambda: bool(seen), timeout=3000)
    assert seen == ["iptal"]


def test_a_cancelled_run_never_applies_and_the_next_run_does(qtbot, owner):
    """S3 (g): a stale run number: run 1 is cancelled and its late result dropped; run 2 applies."""
    gate = threading.Event()
    applied: list = []
    first = run_background(owner, lambda _p: gate.wait(5) and "bayat", title="İş açılıyor",
                           on_done=lambda r: applied.append(("1", r)),
                           on_cancelled=lambda: applied.append(("1", "iptal")))
    first.cancel()
    gate.set()
    qtbot.waitUntil(lambda: not first.running, timeout=3000)
    second = run_background(owner, lambda _p: "yeni", title="İş açılıyor",
                            on_done=lambda r: applied.append(("2", r)))
    assert second is not None and second.run == first.run + 1
    qtbot.waitUntil(lambda: ("2", "yeni") in applied, timeout=3000)
    assert applied == [("1", "iptal"), ("2", "yeni")]


def test_the_engine_is_made_in_the_worker(qtbot, tmp_path, monkeypatch):
    """S2: making the shared engine reads the disk; neither Oku in Değerler nor the Şablonlar
    read may do it on the window thread."""
    from fakes import make_pdf, qr_page, text_page

    from evrakci.pipeline.templates.store import TemplateStore
    from evrakci.ui import ocr_engine
    from evrakci.ui.main_window import MainWindow
    from evrakci.ui.sablon_read import ReadInput, read_examples

    made: list[QThread] = []

    class Engine:
        name = "sahte"

        def available(self):
            return "yok"

    def default_engine():
        made.append(QThread.currentThread())
        return Engine()

    monkeypatch.setattr("evrakci.pipeline.ocr.tesseract.default_engine", default_engine)
    monkeypatch.setattr(ocr_engine, "_engine", None)
    monkeypatch.setattr(ocr_engine, "warm_up", lambda: None)  # it would make the engine in a
    # worker first and hide an engine made on the window thread by the code under test
    store = JobStore(tmp_path / "jobs")
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Kasım")
    window.show_tab("degerler")
    assert ocr_engine.cached_engine() is None and not made  # nothing made before the read
    window.degerler.read_values(False)
    qtbot.waitUntil(lambda: window.degerler.task is None and bool(made), timeout=10000)
    assert made and all(t is not QApplication.instance().thread() for t in made)
    made.clear()
    monkeypatch.setattr(ocr_engine, "_engine", None)
    job = ReadInput(None, {}, {}, {}, ocr_engine.LazyEngine())
    from evrakci.ui.workers import Task, start
    done: list = []
    task = Task(lambda _p: read_examples(job, []))
    task.signals.failed.connect(done.append)
    start(task)
    qtbot.waitUntil(lambda: bool(done), timeout=5000)
    assert made and all(t is not QApplication.instance().thread() for t in made)
    assert ocr_engine.cached_engine() is not None


@pytest.mark.parametrize("tab", ["yukle", "degerler", "disa_aktar"])
def test_stop_key_cancels_a_loading_job_on_these_tabs(qtbot, tmp_path, monkeypatch, tab):
    """S2: Ctrl+. (the tab's stop command) cancels a job that is opening, whichever of the
    tabs that own the key is showing."""
    window, store, first, second, _third = _two_jobs(qtbot, tmp_path)
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id)
    window.yukle.open_job_id(second.id)
    card = _wait_card(qtbot, window)
    window.show_tab(tab)
    action_id = {"yukle": "yukle.iptal", "degerler": "degerler.durdur",
                 "disa_aktar": "disa_aktar.durdur"}[tab]
    assert window.registry.action(action_id).isEnabled()
    window.registry.action(action_id).trigger()
    assert card.title.text() == "İptal ediliyor…"
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    assert window.controller().job.id == first.id
    assert window.yukle.last_message == "İptal edildi; hiçbir şey değişmedi."


def test_job_lists_are_read_off_the_window_thread(qtbot, tmp_path, monkeypatch):
    """S2: list_jobs (job list) and store.load (recent-jobs menu) run in a worker."""
    window, store, first, second, _third = _two_jobs(qtbot, tmp_path)
    window.prefs.add_recent_job(second.id)
    main = QApplication.instance().thread()
    calls: list[tuple[str, QThread]] = []
    real_list, real_load = JobStore.list_jobs, JobStore.load

    def list_jobs(self, *args, **kwargs):
        calls.append(("list_jobs", QThread.currentThread()))
        return real_list(self, *args, **kwargs)

    def load(self, job_id):
        calls.append(("load", QThread.currentThread()))
        return real_load(self, job_id)

    monkeypatch.setattr(JobStore, "list_jobs", list_jobs)
    monkeypatch.setattr(JobStore, "load", load)
    with qtbot.waitSignal(window.recent_changed, timeout=5000):
        window.refresh_recent_jobs()
    window.open_job_switcher()
    qtbot.waitUntil(lambda: any(a.text().startswith("B") for a in window.job_menu.actions()),
                    timeout=5000)
    window.job_menu.close()
    window.yukle.refresh_jobs()
    qtbot.waitUntil(lambda: any(c[0] == "list_jobs" for c in calls), timeout=5000)
    qtbot.wait(100)  # the answer arrives and is applied on this thread
    assert calls and all(thread is not main for _name, thread in calls)


def test_a_late_job_list_does_not_replace_the_newer_one(qtbot, tmp_path, monkeypatch):
    """S3: refresh_jobs run 1 answers after run 2; only run 2's list is shown."""
    window, store, first, second, third = _two_jobs(qtbot, tmp_path)
    shown: list = []
    window.yukle.empty.set_jobs = shown.append
    gate = threading.Event()
    real = JobStore.list_jobs
    calls = {"n": 0}

    def list_jobs(self, *args, **kwargs):
        calls["n"] += 1
        mine = calls["n"]
        if mine == 1:
            gate.wait(5)
            return real(self, *args, **kwargs)[:1]  # the stale answer differs
        return real(self, *args, **kwargs)

    monkeypatch.setattr(JobStore, "list_jobs", list_jobs)
    window.yukle.refresh_jobs()
    qtbot.waitUntil(lambda: calls["n"] == 1, timeout=3000)
    window.yukle.refresh_jobs()
    qtbot.waitUntil(lambda: len(shown) == 1, timeout=3000)
    gate.set()
    qtbot.wait(250)
    assert len(shown) == 1 and len(shown[0]) == 3


def test_a_late_recent_list_does_not_replace_the_newer_one(qtbot, tmp_path, monkeypatch):
    """S3: refresh_recent_jobs run 1 answers after run 2; only run 2's list is kept."""
    window, store, first, second, third = _two_jobs(qtbot, tmp_path)
    window.prefs.add_recent_job(second.id)
    gate = threading.Event()
    real = JobStore.load
    calls = {"n": 0}

    def load(self, job_id):
        if QThread.currentThread() is QApplication.instance().thread():
            return real(self, job_id)
        calls["n"] += 1
        if calls["n"] == 1:
            gate.wait(5)
            raise OSError("bayat")  # the stale run would leave an empty list
        return real(self, job_id)

    monkeypatch.setattr(JobStore, "load", load)
    window.refresh_recent_jobs()
    qtbot.waitUntil(lambda: calls["n"] == 1, timeout=3000)
    with qtbot.waitSignal(window.recent_changed, timeout=3000):
        window.refresh_recent_jobs()
    assert {job.id for job, _when in window._recent} == {first.id, second.id}
    gate.set()
    qtbot.wait(250)
    assert {job.id for job, _when in window._recent} == {first.id, second.id}


def test_a_frozen_job_refuses_edit_undo_and_redo_and_says_why(qtbot, tmp_path):
    """S2: while the job is deleted nothing may change memory (it would part from the disk if
    the delete fails); the refusal is shown, undo/redo are off, and a toast undo does nothing."""
    from evrakci.ui.feedback import undo_last

    window, store, first, _screen, _result = _delete_ready(qtbot, tmp_path)
    controller = window.controller()
    name = controller.job.name
    assert controller.run("Ad", lambda job: setattr(job, "name", "Yeni"))
    undo_toast, available = undo_last(controller.undo_stack)
    said: list[str] = []
    controller.status.connect(said.append)
    controller.freeze()
    assert not controller.run("Ad", lambda job: setattr(job, "name", "Sonra"))
    assert said[-1] == "İş siliniyor"
    said.clear()
    window.undo()
    controller.undo()
    undo_toast()
    assert controller.job.name == "Yeni"  # nothing was undone
    assert "İş siliniyor" in said
    assert not window.registry.action("app.geri_al").isEnabled()
    controller.unfreeze()
    assert window.registry.action("app.geri_al").isEnabled()
    window.undo()
    assert controller.job.name == name
    controller.freeze()
    window.redo()
    assert controller.job.name == name
    assert not window.registry.action("app.yinele").isEnabled()


def _delete_ready(qtbot, tmp_path):
    from types import SimpleNamespace

    window, store, first, _second, _third = _two_jobs(qtbot, tmp_path)
    screen = window.disa_aktar
    screen._finished_at = "10:00"
    screen.out_dir = tmp_path
    result = SimpleNamespace(paths=[], needing_check=0, index_written=False)
    return window, store, first, screen, result


def test_delete_in_a_worker_freezes_the_job_against_saves(qtbot, tmp_path, monkeypatch):
    """S2: while the folder is deleted in a worker no edit, undo or save may write job.json
    back; nothing may be written after the delete either; yukle.iptal stays off (the delete
    cannot be stopped)."""
    window, store, first, screen, result = _delete_ready(qtbot, tmp_path)
    controller = window.controller()
    gate = threading.Event()
    real_delete = JobStore.delete

    def delete(self, job_id):
        gate.wait(5)
        real_delete(self, job_id)

    monkeypatch.setattr(JobStore, "delete", delete)
    before = _bytes(store, first.id)
    assert screen._delete_in_worker(controller, first, result)
    assert controller.frozen
    assert not controller.run("Ad", lambda job: setattr(job, "name", "Sonradan"))
    assert controller.job.name == first.name
    window.save_job()
    assert _bytes(store, first.id) == before
    for action_id in ("yukle.iptal", "degerler.durdur", "disa_aktar.durdur"):
        assert not window.registry.action(action_id).isEnabled()
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    qtbot.waitUntil(lambda: window.controller() is None, timeout=3000)
    assert not store._job_file(first.id).exists()


def test_a_failed_delete_unfreezes_the_job(qtbot, tmp_path, monkeypatch):
    window, store, first, screen, result = _delete_ready(qtbot, tmp_path)
    controller = window.controller()

    def delete(self, job_id):
        raise OSError("kilitli")

    monkeypatch.setattr(JobStore, "delete", delete)
    assert screen._delete_in_worker(controller, first, result)
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    assert not controller.frozen
    assert controller.run("Ad", lambda job: setattr(job, "name", "Sonra"))
    wait_saved(controller)  # saving is write-behind (I-47 part b)
    assert store.load(first.id).name == "Sonra"


def test_a_delete_result_after_the_window_closed_is_dropped(qtbot, tmp_path, monkeypatch):
    """S3 (rule 6): the late result of a delete does nothing once the window is closed."""
    window, store, first, screen, result = _delete_ready(qtbot, tmp_path)
    gate = threading.Event()
    real_delete = JobStore.delete
    monkeypatch.setattr(JobStore, "delete", lambda self, i: gate.wait(5) or real_delete(self, i))
    told: list = []
    gone: list = []
    monkeypatch.setattr(screen, "_write_outcome", lambda *a: told.append(a))
    screen.job_deleted.connect(lambda: gone.append(1))
    assert screen._delete_in_worker(window.controller(), first, result)
    window.close()
    gate.set()
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    assert told == [] and gone == []


def test_a_refused_close_does_not_cancel_the_loading_job(qtbot, tmp_path, monkeypatch):
    """S3: the close is refused (the person says no): the job that is opening goes on."""
    from PySide6.QtWidgets import QMessageBox

    window, _store, first, second, _third = _two_jobs(qtbot, tmp_path)
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id)
    window.yukle.open_job_id(second.id)
    card = _wait_card(qtbot, window)
    monkeypatch.setattr(window, "_busy_screens", lambda: [window.yukle])
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.No)
    window.close()
    assert window.loading() and card.title.text() == "İş açılıyor"
    assert card.cancel_button.isEnabled()
    monkeypatch.undo()  # the pretend busy screen goes; the load is then applied as usual
    monkeypatch.setattr(JobStore, "load", JobStore.load)
    gate.set()
    qtbot.waitUntil(lambda: window.controller().job.id == second.id, timeout=3000)


def test_read_commands_are_off_with_the_reason_while_a_job_loads(qtbot, tmp_path, monkeypatch):
    """S3: Oku and Bütün örneklerde dene are off and say why while a job is opening."""
    window, _store, _first, second, _third = _two_jobs(qtbot, tmp_path)
    window.show_tab("degerler")
    gate = threading.Event()
    _slow_load(monkeypatch, gate, second.id)
    window.yukle.open_job_id(second.id)
    _wait_card(qtbot, window)
    for action_id in ("degerler.oku", "degerler.eksikleri_oku", "sablonlar.dene"):
        action = window.registry.action(action_id)
        assert not action.isEnabled() and action.toolTip() == workers.BUSY_REASON
    for button in (window.degerler.read_button, window.degerler.missing_button):
        assert not button.isEnabled() and button.toolTip() == workers.BUSY_REASON
    gate.set()
    qtbot.waitUntil(lambda: window.controller().job.id == second.id, timeout=3000)
    qtbot.waitUntil(lambda: not window.loading(), timeout=3000)
    for action_id in ("degerler.oku", "sablonlar.dene"):
        assert window.registry.action(action_id).toolTip() != workers.BUSY_REASON


def test_loading_card_note_fits_at_150_percent(qtbot, owner):
    """S2: the note "İptal ederseniz hiçbir şey değişmez." is not cut at 150 % text size."""
    from evrakci.ui import theme

    theme.manager().set_text_scale(150)
    try:
        card = LoadingCard(owner)
        card.show_loading("İş açılıyor", "Kasım")
        QApplication.processEvents()
        label = card.note
        assert label.fontMetrics().horizontalAdvance(label.text()) <= label.width()
    finally:
        theme.manager().set_text_scale(100)


def test_a_finished_run_frees_what_its_callbacks_held(qtbot, owner, tmp_path):
    """R-B-3: the handle stays as the owner's last one, but a deleted job's controller (held by
    its done callback) is not kept in memory with it."""
    import gc
    import weakref

    from fakes import job_from_kinds

    from evrakci.ui.controller import JobController

    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds({"b1": "ppp"})
    store.save(job)
    controller = JobController(store, job)
    ref = weakref.ref(controller)
    done: list = []

    def finished(result, held=controller):
        done.append(held is not None and result)

    handle = run_background(owner, lambda _p: "bitti", title="İş açılıyor", on_done=finished)
    del controller, job, finished
    qtbot.waitUntil(lambda: done == ["bitti"] and not handle.running, timeout=3000)
    QApplication.processEvents()
    gc.collect()
    assert ref() is None
