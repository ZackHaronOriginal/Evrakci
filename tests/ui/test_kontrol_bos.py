"""I-03: "Boş sayfalar" in Ölçüte göre seç… (ink limit, live count) and Araçlar > Boş sayfaları at.

Job of the tests: "ppeppepp": pages 2 and 5 are blank (no ink), page 3 is pale (0,2 %).
"""

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from test_kontrol_a import _window

from evrakci.pipeline.analyze import PageInfo
from evrakci.pipeline.select import Criterion
from evrakci.ui.kontrol_dialogs import SelectDialog

SPEC = {"a": "ppeppepp"}


def _job_with_pale(window):
    job = window.controller().job
    job.pages["a/3"] = PageInfo(0.002, False)
    return job


def _settle(dialog):
    """Let the 80 ms debounce of the ink spin box run."""
    dialog._ink_timer.stop()
    dialog._ink_settled()


def _rows(window):
    return sorted(i.row() for i in window.kontrol.timeline.selectionModel().selectedIndexes())


def test_the_row_its_spin_box_hint_and_live_count(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    job = _job_with_pale(window)
    dialog = SelectDialog(job, 1, [], "bos", parent=window)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.kind() == "bos" and dialog._radios["bos"].text() == "Boş sayfalar"
    assert dialog.ink.value() == 0.3 and dialog.ink.text() == "0,3 %"
    assert (dialog.ink.minimum(), dialog.ink.maximum(), dialog.ink.singleStep()) == (0.1, 5.0, 0.1)
    assert dialog.ink_hint.text() == "Bu orandan az mürekkepli sayfalar boş sayılır."
    assert dialog.ink.accessibleName() == "En çok mürekkep oranı"
    assert dialog.ink_count.text() == "3 sayfa boş   (en boş 0,0 %, en dolu 0,2 %)"
    assert dialog._counts["bos"].text() == "3"
    assert dialog.criterion().params == {"ink": 0.003}


def test_the_count_follows_the_limit_after_a_pause(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    job = _job_with_pale(window)
    dialog = SelectDialog(job, 1, [], "bos", parent=window)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.ink.setValue(0.1)
    assert dialog.ink_count.text().startswith("3 sayfa boş")  # not evaluated per key
    qtbot.waitUntil(lambda: dialog.ink_count.text().startswith("2 sayfa boş"), timeout=2000)
    assert dialog.ink_count.text() == "2 sayfa boş   (en boş 0,0 %, en dolu 0,0 %)"
    assert dialog._counts["bos"].text() == "2"
    assert dialog.criterion().params == {"ink": 0.001}
    dialog.ink.setValue(5.0)
    _settle(dialog)
    assert dialog.ink_count.text().startswith("3 sayfa boş")


def test_blank_pages_already_deleted_are_counted_apart(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    job = window.controller().job
    dialog = SelectDialog(job, 1, [], "bos", parent=window)
    qtbot.addWidget(dialog)
    assert dialog.ink_count.text() == "2 sayfa boş   (en boş 0,0 %, en dolu 0,0 %)"
    job.delete_page("a/5")
    other = SelectDialog(job, 1, [], "bos", parent=window)
    qtbot.addWidget(other)
    assert other.ink_count.text() == "1 sayfa boş   (en boş 0,0 %, en dolu 0,0 %, 1 silinmiş)"
    assert other.criterion().params == {"ink": 0.003}
    assert other._counts["bos"].text() == "1"


def test_no_blank_page_says_zero(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    dialog = SelectDialog(window.controller().job, 1, [], "bos", parent=window)
    qtbot.addWidget(dialog)
    assert dialog.ink_count.text() == "0 sayfa boş"
    assert dialog._counts["bos"].text() == "Hiç yok"


def test_the_pane_shows_only_for_this_row(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    dialog = SelectDialog(window.controller().job, 1, [], parent=window)
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.ink.isHidden()
    dialog._radios["bos"].setChecked(True)
    assert not dialog.ink.isHidden() and dialog.title.text() == "Boş sayfalar"
    dialog._radios["tek"].setChecked(True)
    assert dialog.ink.isHidden()


def test_sec_selects_what_the_count_said_and_says_how_to_delete(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path, spec=SPEC)
    _job_with_pale(window)
    seen = {}

    def answer(dialog):
        dialog._radios["bos"].setChecked(True)
        dialog.ink.setValue(0.1)
        _settle(dialog)
        seen["count"] = dialog.ink_count.text()
        return True

    monkeypatch.setattr(SelectDialog, "exec", answer)
    ctl = window.controller()
    before = ctl.undo_stack.index()
    window.kontrol.select_by()
    assert seen["count"].startswith("2 sayfa boş")
    assert _rows(window) == [2, 5]  # the same pages the count named
    assert window.toaster.current_text() == "2 boş sayfa seçildi. Silmek için Del."
    assert ctl.undo_stack.index() == before
    assert len(_rows(window)) == int(seen["count"].split()[0])


def test_enter_in_the_spin_box_selects(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    dialog = SelectDialog(window.controller().job, 1, [], "bos", parent=window)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.ink.setFocus()
    qtbot.waitUntil(dialog.ink.hasFocus)
    with qtbot.waitSignal(dialog.accepted, timeout=2000):
        QTest.keyClick(dialog.ink, Qt.Key.Key_Return)


def test_del_after_selecting_blanks_is_one_undo_step(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    screen = window.kontrol
    ctl = window.controller()
    assert screen.select_matching(Criterion("bos", {"ink": 0.003})) == 2
    screen.timeline.setFocus()
    screen.toggle_delete()
    assert ctl.job.deleted == {"a/2", "a/5"}
    ctl.undo()
    assert ctl.job.deleted == set()


# -- Araçlar > Boş sayfaları at (O-4, B-006) ----------------------------------------------------
def test_the_switch_is_a_checkable_menu_command_with_no_key(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    registry = window.registry
    action = registry.action("kontrol.bos_at")
    spec = registry.spec("kontrol.bos_at")
    assert spec.checkable and spec.shortcuts == () and spec.menu == "araclar"
    assert action.text().replace("&", "") == "Boş sayfaları at"
    assert registry.is_enabled("kontrol.bos_at") and not action.isChecked()


def test_the_switch_is_one_undo_step_each_way_and_the_page_stays_drawn(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, spec=SPEC)
    ctl = window.controller()
    screen = window.kontrol
    action = window.registry.action("kontrol.bos_at")
    restore = window.registry.action("kontrol.bos_geri_getir")
    base = ctl.undo_stack.index()
    assert not restore.isVisible()
    action.trigger()
    assert ctl.job.drop_empty and action.isChecked()
    assert ctl.undo_stack.index() == base + 1 and ctl.undo_stack.undoText() == "Boş sayfaları at"
    assert [len(d.page_ids) for d in ctl.documents()] == [6]  # the two blanks left out
    assert screen.model.rowCount() == 8  # ... but still in the timeline
    assert restore.isVisible()  # "Boş sayfayı geri getir" shows while the switch is on
    action.trigger()
    assert not ctl.job.drop_empty and not action.isChecked()
    assert ctl.undo_stack.index() == base + 2
    assert [len(d.page_ids) for d in ctl.documents()] == [8]
    ctl.undo()  # back to on: the check mark follows the job
    assert ctl.job.drop_empty and action.isChecked()
    ctl.undo()
    assert not ctl.job.drop_empty and not action.isChecked() and not restore.isVisible()
