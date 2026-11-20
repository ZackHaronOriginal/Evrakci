"""Ledger repro tests, group A (B-020 to B-031, Kontrol and App).

Each test asserts the EXPECTED behaviour and is xfail(strict=True) while the bug exists.
When a bug is fixed the test XPASSes and fails the suite: remove the marker then.
"""

import pytest
from fakes import job_from_kinds
from PIL import Image
from PySide6.QtWidgets import QPushButton

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import feedback
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol import KontrolScreen
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.thumbnails import ThumbnailService


class Renderer:
    def __call__(self, pid, height):
        return Image.new("RGB", (int(height * 0.7), height), "white")


def _controller(tmp_path, spec):
    job = job_from_kinds(spec)
    store = JobStore(tmp_path / "jobs")
    store.save(job)
    return JobController(store, job)


def _screen(qtbot, ctl, renderer=None):
    screen = KontrolScreen(ctl, ThumbnailService(renderer or Renderer(), height=100),
                           templates=dict)
    qtbot.addWidget(screen)
    screen.resize(1366, 640)
    return screen


def _go(screen, row):
    screen.timeline.setCurrentIndex(screen.timeline.model().index(row))


def _window(qtbot, tmp_path, spec):
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds(spec)
    store.save(job)
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.resize(1366, 768)
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job(store.load(job.id))
    window.show_tab("kontrol")
    qtbot.wait(1)
    return window


def test_b020_k_on_the_first_page_changes_nothing_visible(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "pppp"})
    screen = _screen(qtbot, ctl)
    first = ctl.job.ordered_page_ids()[0]
    _go(screen, 0)
    screen.toggle_cut()
    assert len(ctl.documents()) == 1
    assert ctl.cut_kinds()[first] == "start"


def test_b020_k_on_the_first_page_is_refused_and_a_batch_move_keeps_one_document(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "pp", "b": "pp"})
    screen = _screen(qtbot, ctl)
    messages = []
    ctl.status.connect(messages.append)
    _go(screen, 0)
    screen.toggle_cut()
    assert messages == ["İlk belgenin öncesi yok."]
    assert not ctl.job.manual_cuts
    assert ctl.run("Partiyi taşı", lambda job: job.move_batch("a", 1))
    assert len(ctl.documents()) == 1


def test_b021_merge_joins_a_qr_document_that_also_has_a_manual_cut(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "pppqppp"})
    ctl.add_cut("a/4")  # first page after the QR page: the manual cut is hidden under the QR cut
    screen = _screen(qtbot, ctl)
    assert len(ctl.documents()) == 2
    _go(screen, 4)
    screen.merge_current()
    assert len(ctl.documents()) == 1
    ctl.undo()  # both cuts were removed as ONE step
    assert len(ctl.documents()) == 2


@pytest.mark.xfail(strict=True, reason="B-022: status line messages are never announced")
def test_b022_status_line_message_is_announced(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    window.controller().status.emit("Bu ilk belge.")
    assert window.message.text() == "Bu ilk belge."
    assert window.message.accessibleName() == "Bu ilk belge."


def test_b023_geri_al_on_the_older_toast_never_undoes_another_step(qtbot, tmp_path):
    """B-023: the older toast's Geri al must never undo a step other than the one it names.

    Bound changed on purpose (Phase 0 run lead): the triage version expected a selective undo
    of the older step (a/0 restored, a/1 still deleted). The undo stack is linear, so that is
    a new feature, not a fix; the S1 harm was undoing the NEWER step while the toast named the
    older one. Decided behaviour: once a newer step exists the older toast's Geri al does
    nothing. Selective undo is a Phase 5 idea.
    """
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    screen, ctl = window.kontrol, window.controller()
    _go(screen, 0)
    screen.toggle_delete()  # toast 1: page a/0
    _go(screen, 1)
    screen.toggle_delete()  # toast 2 waits in the queue: page a/1
    assert window.toaster.pending() == 1
    for button in window.toaster._current.findChildren(QPushButton):
        if button.text() == "Geri al":
            button.click()
    assert {"a/0", "a/1"} <= ctl.job.deleted  # neither the newer nor any other step undone


def test_b023_geri_al_on_a_queued_toast_never_undoes_a_newer_step(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    screen, ctl = window.kontrol, window.controller()
    _go(screen, 0)
    screen.toggle_delete()  # step 1, toast 1
    _go(screen, 1)
    screen.toggle_delete()  # step 2, toast 2 waits in the queue
    index = ctl.undo_stack.index()
    older = window.toaster._current
    buttons = [b for b in older.findChildren(QPushButton) if b.text() == "Geri al"]
    assert buttons  # toast 1 is shown first, while its step is no longer the newest
    window.toaster.dismiss()  # toast 2 is shown now: it is the newest step
    button = next(b for b in window.toaster._current.findChildren(QPushButton)
                  if b.text() == "Geri al")
    assert ctl.undo_stack.index() == index
    for b in buttons:  # pressing the stale button does nothing
        b.click()
    assert ctl.undo_stack.index() == index
    assert {"a/0", "a/1"} <= ctl.job.deleted
    button.click()
    assert "a/1" not in ctl.job.deleted
    assert "a/0" in ctl.job.deleted


@pytest.mark.xfail(strict=True, reason="B-024: a page whose render fails stays on the "
                                       "Yükleniyor placeholder, with no error state")
def test_b024_failed_render_is_not_shown_as_loading(qtbot, tmp_path, monkeypatch):
    from evrakci.ui import kontrol_paint

    def broken(pid, height):
        raise RuntimeError("bozuk sayfa")

    ctl = _controller(tmp_path, {"a": "ppp"})
    screen = _screen(qtbot, ctl, broken)
    screen.show()
    screen.timeline.viewport().repaint()
    service = screen.thumbnails
    qtbot.waitUntil(service.idle, timeout=5000)
    qtbot.wait(50)
    painted = []
    original = kontrol_paint.paint_placeholder
    monkeypatch.setattr(kontrol_paint, "paint_placeholder",
                        lambda *a, **k: painted.append(a[2]) or original(*a, **k))
    screen.timeline.viewport().grab()
    service.stop()
    service._pool.waitForDone(5000)
    assert painted == []  # a failed page needs its own error state, not "Yükleniyor"


@pytest.mark.xfail(strict=True, reason="B-027: Ctrl+G is routed on Kontrol and Değerler only; "
                                       "disabled on the other four tabs")
@pytest.mark.parametrize("tab", ["yukle", "sablonlar", "disa_aktar", "rehber"])
def test_b027_ctrl_g_answers_on_every_tab(qtbot, tmp_path, tab):
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    window.show_tab(tab)
    assert window.registry.is_enabled("app.git")


@pytest.mark.xfail(strict=True, reason="B-028: F5 is enabled on Kontrol and Rehber but does "
                                       "nothing there")
@pytest.mark.parametrize("tab", ["kontrol", "rehber"])
def test_b028_f5_is_disabled_where_it_does_nothing(qtbot, tmp_path, tab):
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    window.show_tab(tab)
    assert not window.registry.is_enabled("app.yenile")


def test_b029_failed_autosave_is_reported_not_raised(qtbot, tmp_path, monkeypatch):
    ctl = _controller(tmp_path, {"a": "pppp"})
    messages = []
    ctl.status.connect(messages.append)

    def fail(job):
        raise OSError("disk dolu")

    monkeypatch.setattr(ctl.store, "save", fail)
    ctl.add_cut("a/2")  # must not raise
    assert messages


def test_b029_failed_autosave_shows_the_failed_state_until_a_save_works(qtbot, tmp_path,
                                                                        monkeypatch):
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    ctl = window.controller()
    band = window.job_switch.save_state
    real_save = ctl.store.save

    def fail(job):
        raise OSError("disk dolu")

    monkeypatch.setattr(ctl.store, "save", fail)
    assert ctl.add_cut("a/2")  # the edit stays applied
    assert band.state() == "failed"
    assert "a/2" in ctl.job.manual_cuts
    monkeypatch.setattr(ctl.store, "save", real_save)
    ctl.add_cut("a/3")
    assert band.state() == "saved"


@pytest.mark.xfail(strict=True, reason="B-030: an error toast shows the info icon")
def test_b030_error_toast_has_its_own_icon(qtbot, tmp_path):
    from PySide6.QtWidgets import QLabel, QWidget

    host = QWidget()
    qtbot.addWidget(host)

    def icon_of(kind):
        toast = feedback._Toast(host, "Metin", None, None, kind)
        qtbot.addWidget(toast)
        label = next(w for w in toast.findChildren(QLabel) if w.pixmap() is not None
                     and not w.pixmap().isNull())
        return label.pixmap().toImage()

    assert icon_of("error") != icon_of("info")


@pytest.mark.xfail(strict=True, reason="B-031: palette placeholder says documents are "
                                       "searched; it lists commands only")
def test_b031_palette_placeholder_is_true(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, {"a": "pppp"})
    window.open_palette()
    text = window.command_palette.field.placeholderText().lower()
    window.command_palette.hide()
    assert "belge ara" not in text


def test_b032_scrolling_repaints_and_loads_visible_rows(qtbot, tmp_path):
    from PySide6.QtCore import QEvent, QObject

    class PaintWatcher(QObject):
        paints = 0

        def eventFilter(self, obj, event):  # noqa: N802
            if event.type() == QEvent.Type.Paint:
                self.paints += 1
            return False

    ctl = _controller(tmp_path, {"b1": "p" * 200})
    screen = _screen(qtbot, ctl)
    screen.show()
    qtbot.waitExposed(screen)
    view = screen.timeline
    model, service = view.model(), screen.thumbnails

    def loaded():
        rows = list(view.visible_rows())
        return bool(rows) and all(service.is_current(model.page_id(r)) for r in rows)

    qtbot.waitUntil(loaded, timeout=3000)
    qtbot.wait(100)
    watcher = PaintWatcher(view.viewport())
    view.viewport().installEventFilter(watcher)
    bar = view.verticalScrollBar()
    first = view.visible_rows().start
    bar.setValue(bar.value() + 4 * 120)  # no repaint(), no mouse event
    assert view.visible_rows().start > first
    qtbot.wait(100)
    assert watcher.paints > 0  # the viewport was painted after the scroll
    for _ in range(40):  # within about 2 s every visible row is current
        if loaded():
            break
        qtbot.wait(50)
    assert loaded()
