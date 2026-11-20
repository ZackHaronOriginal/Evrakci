"""Write-behind saving (I-47 part b): an edit never waits for the disk; one saver thread writes
the newest snapshot; close, Ctrl+S, export, job switch and delete first get the file equal to the
job in memory; a failed write is shown with its retry and keeps the old job open."""
from __future__ import annotations

import errno
import json
import os
import threading
import time

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from saving import wait_saved

from evrakci.pipeline.job import job_to_dict
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui.controller import JobController
from evrakci.ui.main_window import MainWindow
from evrakci.ui.saver import JobSaver


def _store_with_jobs(tmp_path, names=("A", "B")):
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    store = JobStore(tmp_path / "jobs")
    return store, [store.create_job(name, [pdf]) for name in names]


def _window(qtbot, tmp_path, names=("A", "B")):
    store, jobs = _store_with_jobs(tmp_path, names)
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(window)
    window.show()
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.open_job_id(jobs[0].id)
    assert window.controller().job.id == jobs[0].id
    return window, store, jobs


def _rename(controller, name):
    return controller.run("Ad", lambda job: setattr(job, "name", name))


class Disk:
    """A patched JobStore.save_dict: records every write (thread, name written), can hold the
    writes at a gate and can be made to fail."""

    def __init__(self, monkeypatch):
        self.gate = threading.Event()
        self.gate.set()  # open: writes go straight through
        self.started = threading.Event()
        self.writes: list[tuple[threading.Thread, str]] = []  # by the saver thread
        self.on_window_thread: list[str] = []
        self.events: list[str] = []
        self.fail: str | None = None
        self.real = JobStore.save_dict
        disk = self

        def save_dict(store, job_id, data):
            if threading.current_thread() is threading.main_thread():
                disk.on_window_thread.append(data["name"])  # set-up writes (create_job) land here
                return disk.real(store, job_id, data)
            disk.writes.append((threading.current_thread(), data["name"]))
            disk.events.append(f"write:{data['name']}")
            disk.started.set()
            disk.gate.wait(10)
            if disk.fail is not None:
                raise OSError(disk.fail)
            disk.real(store, job_id, data)
            disk.events.append(f"done:{data['name']}")

        monkeypatch.setattr(JobStore, "save_dict", save_dict)

    def hold(self):
        self.gate.clear()
        self.started.clear()

    def release(self):
        self.gate.set()

    @property
    def names(self):
        return [name for _thread, name in self.writes]


@pytest.fixture
def disk(monkeypatch):
    held = Disk(monkeypatch)
    yield held
    held.release()  # a test that hangs the disk on purpose never leaves a thread waiting


def _equal_on_disk(store, controller):
    assert store.load(controller.job.id) == controller.job


# -- K1: nothing is written on the window thread --------------------------------------------
def test_an_edit_is_never_written_on_the_window_thread(qtbot, tmp_path, monkeypatch, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    direct: list[str] = []
    real_save = JobStore.save

    def save(self, job):
        direct.append(threading.current_thread().name)
        return real_save(self, job)

    monkeypatch.setattr(JobStore, "save", save)
    controller = JobController(store, store.load(job.id))
    disk.on_window_thread.clear()  # (create_job wrote the first file, before any edit)
    for n in range(3):
        assert _rename(controller, f"Ad {n}")
    controller.undo()
    wait_saved(controller)
    assert disk.writes and disk.on_window_thread == []
    assert direct == []  # JobStore.save (the window-thread writer) is no longer used for edits
    _equal_on_disk(store, controller)


# -- K2: a slow disk does not stall the window ----------------------------------------------
def test_a_slow_disk_never_stalls_the_window(qtbot, tmp_path, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    band = window.job_switch.save_state
    ticks: list[float] = []
    timer = QTimer(window)
    timer.setInterval(20)
    timer.timeout.connect(lambda: ticks.append(time.perf_counter()))
    timer.start()
    disk.hold()
    QTimer.singleShot(1000, disk.release)  # the write blocks for a second
    started = time.perf_counter()
    assert _rename(controller, "Yavaş disk")
    assert time.perf_counter() - started < 0.1  # the edit did not wait for the disk
    qtbot.waitUntil(lambda: band.state() == "saving", timeout=3000)
    assert band.text() == "Kaydediliyor…"
    qtbot.waitUntil(lambda: band.state() == "saved", timeout=5000)
    timer.stop()
    assert band.text().startswith("Kaydedildi")
    gaps = [b - a for a, b in zip(ticks, ticks[1:], strict=False)]
    assert len(ticks) >= 30 and max(gaps) < 0.1
    _equal_on_disk(store, controller)


def test_a_quick_write_does_not_flicker_the_title_band(qtbot, tmp_path, disk):
    window, _store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    seen: list[str] = []
    controller.saving.connect(lambda: seen.append("saving"))
    assert _rename(controller, "Hızlı")
    qtbot.waitUntil(lambda: window.job_switch.save_state.state() == "saved", timeout=3000)
    assert seen == []  # saved before SAVING_SHOW_MS: no "Kaydediliyor…" at all


# -- K3: coalescing --------------------------------------------------------------------------
def test_quick_edits_are_coalesced_and_the_last_one_wins(qtbot, tmp_path, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    disk.hold()
    assert _rename(controller, "Ad 0")
    assert disk.started.wait(3)  # the first write is in flight and blocked
    for n in range(1, 50):
        assert _rename(controller, f"Ad {n}")
    disk.release()
    wait_saved(controller)
    assert disk.names == ["Ad 0", "Ad 49"]  # 50 edits, 2 writes, in order
    _equal_on_disk(store, controller)


def test_an_edit_during_a_write_is_written_after_it_not_lost(qtbot, tmp_path, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    disk.hold()
    _rename(controller, "Birinci")
    assert disk.started.wait(3)
    _rename(controller, "İkinci")
    controller.undo()
    controller.undo()  # undo during the same write: the newest state is the first one again
    disk.release()
    wait_saved(controller)
    assert disk.names == ["Birinci", "A"]
    assert store.load(job.id).name == "A"


def test_the_job_file_is_whole_whenever_it_is_read_while_the_saver_writes(qtbot, tmp_path):
    """Readers (the job list, a second window) see the old or the new file, never half of one."""
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    stop = threading.Event()
    bad: list[str] = []
    reads = [0]

    def reader():
        path = store._job_file(job.id)
        while not stop.is_set():
            try:
                json.loads(path.read_text(encoding="utf-8"))
                reads[0] += 1
            except (OSError, ValueError) as error:
                bad.append(repr(error))

    thread = threading.Thread(target=reader)
    thread.start()
    try:
        for n in range(60):
            _rename(controller, f"Ad {n}")
            QApplication.processEvents()
        wait_saved(controller)
    finally:
        stop.set()
        thread.join()
    assert reads[0] > 0 and bad == []
    _equal_on_disk(store, controller)


# -- K4: flush points -------------------------------------------------------------------------
def test_close_waits_for_the_write_then_closes(qtbot, tmp_path, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    disk.hold()
    _rename(controller, "Kapanırken")
    assert disk.started.wait(3)
    assert window.close() is False  # deferred, not refused
    assert window.isVisible() and window.controller() is controller
    assert window.job_switch.save_state.state() == "saving"
    assert store.load(controller.job.id).name != "Kapanırken"
    disk.release()
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=3000)
    assert window._closed
    _equal_on_disk(store, controller)
    assert controller.saver.idle and not controller.saver._running  # nothing writes after exit


def test_close_with_nothing_pending_closes_at_once(qtbot, tmp_path, disk):
    window, _store, _jobs = _window(qtbot, tmp_path)
    assert window.close() is True


def test_ctrl_s_says_saving_then_saved(qtbot, tmp_path, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    band = window.job_switch.save_state
    disk.hold()
    window.registry.action("app.kaydet").trigger()
    assert band.state() == "saving" and band.text() == "Kaydediliyor…"
    assert "İş kaydedildi" not in window.toaster.current_text()
    path = store._job_file(controller.job.id)
    old = time.time() - 86400
    os.utime(path, (old, old))
    disk.release()
    qtbot.waitUntil(lambda: band.state() == "saved", timeout=3000)
    assert "İş kaydedildi" in window.toaster.current_text()
    assert path.stat().st_mtime > old + 3600  # written even though nothing changed
    _equal_on_disk(store, controller)


def test_ctrl_s_pressed_twice_while_writing_answers_once(qtbot, tmp_path, disk):
    window, _store, _jobs = _window(qtbot, tmp_path)
    shown: list[str] = []
    real = window.toaster.show
    window.toaster.show = lambda text, **kw: shown.append(text) or real(text, **kw)
    disk.hold()
    window.save_job()
    window.save_job()
    disk.release()
    qtbot.waitUntil(lambda: any("İş kaydedildi" in t for t in shown), timeout=3000)
    wait_saved(window.controller())
    assert sum("İş kaydedildi" in t for t in shown) == 1


def test_export_starts_only_after_the_job_is_on_disk(qtbot, tmp_path, monkeypatch, disk):
    from test_disa_aktar import _screen

    from evrakci.ui import disa_aktar as module

    screen, controller, _template = _screen(qtbot, tmp_path)
    seen: list[bool] = []
    real = module.export_job

    def checking(job, files, *args, **kwargs):  # runs in the export worker
        seen.append(controller.store.load(job.id) == job)  # the file equals the copy exported
        return real(job, files, *args, **kwargs)

    monkeypatch.setattr(module, "export_job", checking)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    disk.hold()
    _rename(controller, "Dışa aktarmadan önce")
    assert disk.started.wait(3)
    screen.export_button.click()
    qtbot.wait(100)
    assert screen.task is None and seen == []  # waiting for the write
    screen.export_button.click()  # a second press while waiting changes nothing
    disk.release()
    qtbot.waitUntil(lambda: screen.state() == "done", timeout=30000)
    assert seen == [True]


def test_a_failed_write_before_export_stops_the_export(qtbot, tmp_path, monkeypatch, disk):
    from test_disa_aktar import _screen

    screen, controller, _template = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    disk.fail = "disk dolu"
    screen.export_button.click()
    qtbot.waitUntil(lambda: controller.saver.error != "", timeout=3000)
    qtbot.wait(50)
    assert screen.task is None and not screen._flushing
    assert not (tmp_path / "out").exists()


def test_a_job_switch_writes_the_old_job_first(qtbot, tmp_path, disk):
    window, store, jobs = _window(qtbot, tmp_path)
    old = window.controller()
    disk.hold()
    _rename(old, "Eski iş değişti")
    assert disk.started.wait(3)
    window.yukle.open_job_id(jobs[1].id)
    qtbot.wait(150)  # the other job is read meanwhile
    assert window.controller() is old  # not swapped before the write is over
    assert window.yukle.can_switch() is not None  # a second open waits (swap pending)
    disk.release()
    qtbot.waitUntil(lambda: window.controller() is not old, timeout=5000)
    assert window.controller().job.id == jobs[1].id
    assert store.load(old.job.id).name == "Eski iş değişti"
    assert window.yukle.can_switch() is None


def test_a_failed_write_keeps_the_old_job_open_and_the_second_try_goes_ahead(
        qtbot, tmp_path, disk):
    window, store, jobs = _window(qtbot, tmp_path)
    old = window.controller()
    disk.fail = "salt okunur"
    _rename(old, "Kaydedilemeyen")
    qtbot.waitUntil(lambda: window.job_switch.save_state.state() == "failed", timeout=3000)
    window.yukle.open_job_id(jobs[1].id)
    qtbot.waitUntil(lambda: window.message.text() == "Kaydedilemedi: salt okunur", timeout=3000)
    qtbot.wait(100)
    assert window.controller() is old and old.job.name == "Kaydedilemeyen"  # stays open
    window.yukle.open_job_id(jobs[1].id)  # second attempt: the edits stay unsaved, it goes on
    qtbot.waitUntil(lambda: window.controller() is not old, timeout=5000)
    assert window.controller().job.id == jobs[1].id


def test_closing_the_job_writes_it_first(qtbot, tmp_path, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    disk.hold()
    _rename(controller, "Ctrl+W")
    assert disk.started.wait(3)
    window.close_job()
    assert window.controller() is controller
    disk.release()
    qtbot.waitUntil(lambda: window.controller() is None, timeout=3000)
    assert store.load(controller.job.id).name == "Ctrl+W"


def _delete_ready(window, tmp_path):
    from types import SimpleNamespace

    screen = window.disa_aktar
    screen._finished_at = "10:00"
    screen.out_dir = tmp_path
    return screen, SimpleNamespace(paths=[], needing_check=0, index_written=False)


def test_delete_waits_for_the_write_and_nothing_brings_the_folder_back(
        qtbot, tmp_path, monkeypatch, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    job = controller.job
    screen, result = _delete_ready(window, tmp_path)
    real_delete = JobStore.delete

    def delete(self, job_id):
        disk.events.append("delete")
        real_delete(self, job_id)

    monkeypatch.setattr(JobStore, "delete", delete)
    disk.hold()
    _rename(controller, "Silinecek 1")
    assert disk.started.wait(3)
    _rename(controller, "Silinecek 2")  # queued behind the write in flight
    assert screen._delete_in_worker(controller, job, result)
    assert controller.frozen
    qtbot.wait(150)
    assert store._job_dir(job.id).exists()  # the delete waits for the write
    assert "delete" not in disk.events
    disk.release()
    qtbot.waitUntil(lambda: window.controller() is None, timeout=5000)
    qtbot.wait(200)  # a late write would bring the folder back now
    assert not store._job_dir(job.id).exists()
    assert disk.events[-1] == "delete" and disk.events.count("delete") == 1


def test_a_frozen_job_takes_no_snapshot(qtbot, tmp_path, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    controller.freeze()
    controller._changed()
    controller.save_now()
    assert controller.saver.idle and disk.writes == []
    controller.unfreeze()
    controller.save_now()
    wait_saved(controller)
    assert len(disk.writes) == 1


# -- K5: failure and retry ---------------------------------------------------------------------
def test_a_failed_write_is_shown_with_its_retry_and_retry_saves(qtbot, tmp_path, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    band = window.job_switch.save_state
    disk.fail = "salt okunur"
    _rename(controller, "Yeniden")
    qtbot.waitUntil(lambda: band.state() == "failed", timeout=3000)
    assert window.message.text() == "Kaydedilemedi: salt okunur"
    assert band.toolTip() == "Kaydedilemedi: salt okunur" and band._retry.isVisibleTo(band)
    assert store.load(controller.job.id).name != "Yeniden"
    disk.fail = None  # the disk recovers; the retry is "flush again"
    band._retry.click()
    qtbot.waitUntil(lambda: band.state() == "saved", timeout=3000)
    _equal_on_disk(store, controller)


def test_a_later_good_write_clears_an_earlier_failure(qtbot, tmp_path, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    failures: list[str] = []
    controller.save_failed.connect(failures.append)
    disk.fail = "kilitli"
    _rename(controller, "Bir")
    wait_saved(controller)
    assert controller.saver.error == "kilitli" and failures == ["kilitli"]
    disk.fail = None
    _rename(controller, "İki")
    wait_saved(controller)
    assert controller.saver.clean and failures == ["kilitli"]
    _equal_on_disk(store, controller)


def test_an_error_that_is_not_oserror_is_reported_not_swallowed(qtbot, tmp_path, monkeypatch):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))

    def broken(self, job_id, data):
        raise TypeError("yazılamaz")

    monkeypatch.setattr(JobStore, "save_dict", broken)
    _rename(controller, "Bozuk")
    wait_saved(controller)  # the writer thread did not die with the saver stuck "busy"
    assert controller.saver.error == "yazılamaz" and not controller.saver._running


def test_close_after_a_failed_write_is_refused_once_as_before(qtbot, tmp_path, disk):
    window, _store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    disk.fail = "salt okunur"
    _rename(controller, "Kapanmayan")
    qtbot.waitUntil(lambda: window.job_switch.save_state.state() == "failed", timeout=3000)
    assert window.close() is False
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)
    assert window.message.text() == "Kaydedilemedi: salt okunur"
    assert window.isVisible() and window.controller() is controller
    assert window.close() is True  # the second attempt goes ahead; the edits stay unsaved
    assert controller.saver.idle


def test_the_saver_survives_its_controller(qtbot, tmp_path, disk):
    """A write in flight when the controller is dropped finishes quietly (no crash, no signal
    into a dead object)."""
    import gc

    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    disk.hold()
    _rename(controller, "Yetim")
    assert disk.started.wait(3)
    saver = controller.saver
    del controller
    gc.collect()
    disk.release()
    qtbot.waitUntil(lambda: saver.idle, timeout=3000)
    assert store.load(job.id).name == "Yetim"


def test_wait_idle_for_a_worker_thread(qtbot, tmp_path, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    disk.hold()
    _rename(controller, "Bekle")
    assert disk.started.wait(3)
    assert controller.saver.wait_idle(0.05) is False  # still writing
    disk.release()
    assert controller.saver.wait_idle(3) is True
    wait_saved(controller)
    assert job_to_dict(controller.job) == job_to_dict(store.load(job.id))


# -- a write that hangs (an unreachable share) must not hold the window -------------------------
def _hang(monkeypatch, disk):
    """A saver that gives up waiting after 0.1 s, and a disk write that hangs."""
    monkeypatch.setattr("evrakci.ui.saver.STALL_MS", 100)
    disk.hold()


TIMED_OUT = os.strerror(errno.ETIMEDOUT)


def test_a_hung_write_refuses_the_close_once_and_the_second_close_goes_ahead(
        qtbot, tmp_path, monkeypatch, disk):
    window, _store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    _hang(monkeypatch, disk)
    _rename(controller, "Takılan")
    assert disk.started.wait(3)
    assert window.close() is False
    qtbot.waitUntil(lambda: window._close_warned, timeout=3000)
    assert window.message.text() == f"Kaydedilemedi: {TIMED_OUT}"
    band = window.job_switch.save_state
    assert band.state() == "failed" and band._retry.isVisibleTo(band)
    assert window.controller() is controller and not window._closed
    assert controller.saver.stalled and not controller.saver.idle  # the write still hangs
    assert disk.writes[0][0].daemon  # it cannot keep the process alive
    assert window.close() is True  # B-035: the second attempt goes ahead
    assert window._closed
    disk.release()  # the hung write ends; its late result is taken before the window goes
    wait_saved(controller)


def test_after_a_hang_ctrl_s_and_job_switch_are_not_dead_ends(
        qtbot, tmp_path, monkeypatch, disk):
    window, _store, jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    _hang(monkeypatch, disk)
    _rename(controller, "Takılan")
    assert disk.started.wait(3)
    window.save_job()
    assert window._save_waiting
    qtbot.waitUntil(lambda: not window._save_waiting, timeout=3000)  # answered, not stuck
    assert "kaydedilemedi" in window.toaster.current_text()
    window.save_job()  # and Ctrl+S works again
    assert window._save_waiting
    qtbot.waitUntil(lambda: not window._save_waiting, timeout=3000)
    window.yukle.open_job_id(jobs[1].id)  # job switch: refused once with the message ...
    qtbot.waitUntil(lambda: window.message.text() == f"Kaydedilemedi: {TIMED_OUT}", timeout=5000)
    qtbot.waitUntil(lambda: window.yukle.can_switch() is None, timeout=5000)  # not BUSY for ever
    assert not window.yukle.swapping and window.controller() is controller
    window.yukle.open_job_id(jobs[1].id)  # ... and the second attempt goes ahead
    qtbot.waitUntil(lambda: window.controller() is not controller, timeout=5000)
    disk.release()  # the hung write ends; its late result is taken before the window goes
    wait_saved(controller)


def test_after_a_hang_the_export_is_released_and_does_not_start(
        qtbot, tmp_path, monkeypatch, disk):
    from test_disa_aktar import _screen

    screen, controller, _template = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    _hang(monkeypatch, disk)
    _rename(controller, "Takılan")
    assert disk.started.wait(3)
    screen.export_button.click()
    assert screen._flushing
    qtbot.waitUntil(lambda: not screen._flushing, timeout=3000)
    assert screen.task is None and not (tmp_path / "out").exists()
    screen.export_button.click()  # not a dead end: the press is taken up again
    assert screen._flushing
    qtbot.waitUntil(lambda: not screen._flushing, timeout=3000)
    disk.release()  # the hung write ends; its late result is taken before the window goes
    wait_saved(controller)


def test_delete_gives_up_on_a_hung_write_and_keeps_the_job(qtbot, tmp_path, monkeypatch, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    screen, result = _delete_ready(window, tmp_path)
    _hang(monkeypatch, disk)
    _rename(controller, "Takılan silme")
    assert disk.started.wait(3)
    assert screen._delete_in_worker(controller, controller.job, result)
    assert controller.frozen
    qtbot.waitUntil(lambda: not controller.frozen, timeout=3000)  # the worker gave up
    assert store._job_dir(controller.job.id).exists()
    assert window.controller() is controller
    assert controller.job.id in [j.id for j in store.list_jobs()]
    disk.release()  # the hung write ends; its late result is taken before the window goes
    wait_saved(controller)


def test_a_failed_delete_writes_job_json_again(qtbot, tmp_path, monkeypatch, disk):
    window, store, _jobs = _window(qtbot, tmp_path)
    controller = window.controller()
    screen, result = _delete_ready(window, tmp_path)
    job_file = store._job_file(controller.job.id)

    def delete(self, job_id):  # rmtree got as far as job.json, then failed
        job_file.unlink()
        raise OSError("kullanımda")

    monkeypatch.setattr(JobStore, "delete", delete)
    assert screen._delete_in_worker(controller, controller.job, result)
    qtbot.waitUntil(lambda: not controller.frozen, timeout=5000)
    qtbot.waitUntil(lambda: job_file.is_file(), timeout=3000)  # written again after the unfreeze
    wait_saved(controller)
    _equal_on_disk(store, controller)
    assert controller.job.id in [j.id for j in store.list_jobs()]
    assert window.controller() is controller


def test_a_thread_that_cannot_start_is_reported_and_the_saver_recovers(
        qtbot, tmp_path, monkeypatch, disk):
    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    failures: list[str] = []
    controller.save_failed.connect(failures.append)
    real_start = threading.Thread.start

    def start(self):
        if self.name == "evrakci-saver":
            raise RuntimeError("can't start new thread")
        return real_start(self)

    monkeypatch.setattr(threading.Thread, "start", start)
    _rename(controller, "Başlamayan")
    wait_saved(controller)  # idle: not stuck "busy" with nobody to write
    assert failures == ["can't start new thread"] and not controller.saver._running
    monkeypatch.setattr(threading.Thread, "start", real_start)
    _rename(controller, "Başlayan")
    wait_saved(controller)
    assert controller.saver.clean and store.load(job.id).name == "Başlayan"


def test_a_writer_that_dies_hard_does_not_leave_the_saver_running(qtbot, tmp_path, monkeypatch):
    class Hard(BaseException):
        pass

    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    controller = JobController(store, store.load(job.id))
    real = JobStore.save_dict
    state = {"die": True}

    def save_dict(self, job_id, data):
        if state["die"]:
            raise Hard
        return real(self, job_id, data)

    monkeypatch.setattr(JobStore, "save_dict", save_dict)
    monkeypatch.setattr(threading, "excepthook", lambda args: None)  # the dying thread is expected
    _rename(controller, "Ölen")
    assert controller.saver.wait_idle(3) is True  # `_running` was reset on the way out
    state["die"] = False
    controller.save_now()
    deadline = time.monotonic() + 3
    while store.load(job.id).name != "Ölen" and time.monotonic() < deadline:
        QApplication.processEvents()
        time.sleep(0.001)  # a new writer thread started and wrote
    assert store.load(job.id).name == "Ölen"


def test_a_controller_deleted_while_its_write_is_in_flight_is_freed_on_the_window_thread(
        qtbot, tmp_path, disk):
    """The writer thread must not hold the last reference to the saver: a QObject destroyed on
    the writer thread (killTimer from another thread) crashed the process in a later
    `processEvents` (the CI segfault). Dropping the controller mid-write frees it here."""
    import gc

    store, (job,) = _store_with_jobs(tmp_path, ("A",))
    freed_on: list[threading.Thread] = []

    class Watched(JobController):
        def __del__(self):
            freed_on.append(threading.current_thread())

    class WatchedSaver(JobSaver):
        def __del__(self):
            freed_on.append(threading.current_thread())

    for _ in range(20):
        disk.hold()
        controller = Watched(store, store.load(job.id))
        controller.saver = saver = WatchedSaver(store)  # the saver that is really in use
        saver.submit(job.id, job_to_dict(controller.job))
        assert disk.started.wait(3)
        del controller, saver
        gc.collect()  # the controller and its saver are gone while the write is held
        disk.release()
        deadline = time.monotonic() + 3
        while any(t.name == "evrakci-saver" for t in threading.enumerate()):
            assert time.monotonic() < deadline
            time.sleep(0.001)  # the writer thread has ended
        for _ in range(5):
            QApplication.processEvents()  # the late result finds nobody and must not crash
            time.sleep(0.001)
    gc.collect()
    assert freed_on, "the objects were never freed"
    assert all(thread is threading.main_thread() for thread in freed_on)
