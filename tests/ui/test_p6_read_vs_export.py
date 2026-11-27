"""MF-1 (P6 review): export during a Değerler read; a read finishing after the job closed."""

import threading

from test_degerler import GatedEngine, setup, window  # noqa: F401

# -- MF-1: an export must not start during a Değerler read; a late read is harmless --------


def test_export_is_refused_while_degerler_reads(qtbot, window, monkeypatch):  # noqa: F811
    win, _ = window
    gate = threading.Event()
    win.degerler.engine = lambda: GatedEngine(gate)
    win.degerler.read_button.click()
    try:
        assert win.degerler.busy()
        win.show_tab("disa_aktar")
        started = []
        monkeypatch.setattr(win.disa_aktar, "_plan", lambda *a: started.append(1))
        win.disa_aktar.export()
        assert not started and win.disa_aktar.task is None
    finally:
        gate.set()
        win.degerler.cancel()
        qtbot.waitUntil(lambda: not win.degerler.busy(), timeout=20000)


def test_read_finishing_after_the_job_closed_is_not_stuck_busy(qtbot, window):  # noqa: F811
    win, _ = window
    d = win.degerler
    d.task = object()  # a read is in flight
    d._set_busy(True)
    win._job_deleted()  # delete after export closed the job
    assert win.controller() is None
    d._read_done([])
    assert not d.busy()
    assert not win._busy_screens()
