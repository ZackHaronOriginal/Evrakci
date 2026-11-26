"""I-07: saved filters as chips above Kontrol, stored with the template.

The demo job (test_kontrol_a.SPEC style, with empty pages): documents of 3 | QR | 3 | QR | 4 |
QR | 1 pages; page 1, 5 and 9 are empty.
"""

import re
import time
from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog
from test_kontrol_a import _key, _window

from evrakci.cli import main
from evrakci.pipeline.select import Criterion, select_pages
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import theme
from evrakci.ui.kontrol_chips import (
    NONE_ON,
    NOT_KNOWN,
    NOT_KNOWN_TIP,
    SaveFilterDialog,
    count_text,
)
from evrakci.ui.kontrol_dialogs import SelectDialog

SPEC = {"a": "pepqppeqpppeqp"}  # q = QR separator, e = empty


def _template(tmp_path, *filters, name="Süzgeç"):
    """A template in the window's template folder; `filters` are (name, kind, params)."""
    store = TemplateStore(tmp_path / "tpl")
    template = store.create(name)
    for item in filters:
        template.add_saved_filter(*item)
    store.save(template)
    return template


def _stored(tmp_path, template_id):
    return TemplateStore(tmp_path / "tpl").load(template_id)


def _chosen(window) -> list[int]:
    return sorted(i.row() for i in window.kontrol.timeline.selectionModel().selectedIndexes())


def _chip(window, name):
    return next(c for c in window.kontrol.chips.chips if c.info.name == name)


def _make(qtbot, tmp_path, *filters):
    template = _template(tmp_path, *filters)
    window = _window(qtbot, tmp_path, SPEC)
    window.kontrol._chips_sync()
    return window, template


DEFAULT = (("Tekler", "tek", {}), ("Boşlar", "bos", {}), ("Yedinci belge", "belge",
                                                          {"number": 99}))


# -- the row: hidden, shown, count line --------------------------------------------------------
def test_the_row_is_hidden_without_filters_and_without_a_result(qtbot, tmp_path):
    _template(tmp_path)
    window = _window(qtbot, tmp_path, SPEC)
    assert window.kontrol.chips.isHidden()
    _template(tmp_path, ("Tekler", "tek", {}), name="İkinci")
    window.kontrol._chips_sync()
    assert window.kontrol.chips.isHidden()  # the first template (by name) has none


def test_two_chips_and_with_one_count(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    row = screen.chips
    assert not row.isHidden() and [c.info.name for c in row.chips] == [
        "Tekler", "Boşlar", "Yedinci belge"]
    assert row.count.text() == NONE_ON
    _chip(window, "Tekler").click()
    odd = select_pages(screen.controller.job, [Criterion("tek")]).page_ids
    assert row.count.text() == count_text(1, len(odd))
    assert _chosen(window) == sorted(screen.model.row_of(p) for p in odd)
    _chip(window, "Boşlar").click()
    both = select_pages(screen.controller.job, [Criterion("tek"), Criterion("bos")])
    assert row.count.text() == count_text(2, len(both.page_ids))
    assert _chosen(window) == sorted(screen.model.row_of(p) for p in both.page_ids)
    assert 0 < len(both.page_ids) < len(odd)
    assert "2 filtre açık" in row.count.text()
    # everything off clears the selection the chips made
    _chip(window, "Boşlar").click()
    _chip(window, "Tekler").click()
    assert row.count.text() == NONE_ON and _chosen(window) == []


def test_turning_chips_off_keeps_a_selection_the_chips_did_not_make(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    _chip(window, "Tekler").click()
    screen.timeline.select_rows(1, 2, 2)  # the user selects by hand
    _chip(window, "Tekler").click()
    assert _chosen(window) == [1, 2]


def test_a_chip_that_matches_nothing_is_marked_zero_and_says_zero_pages(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    qtbot.waitUntil(lambda: _chip(window, "Yedinci belge").info.count == 0, timeout=3000)
    chip = _chip(window, "Yedinci belge")
    assert chip.tail_text() == "0" and chip.accessibleDescription() == "0 sayfa"
    assert _chip(window, "Tekler").tail_text() == ""
    chip.click()
    assert screen.chips.count.text() == "1 filtre açık: 0 sayfa"
    assert _chosen(window) == []


def test_an_unknown_kind_is_inert_and_says_so(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, ("Tekler", "tek", {}), ("Yeni", "gelecek", {}))
    messages = []
    window.controller().status.connect(messages.append)
    chip = _chip(window, "Yeni")
    assert chip.tail_text() == NOT_KNOWN and chip.toolTip() == NOT_KNOWN_TIP
    assert chip.accessibleDescription() == NOT_KNOWN_TIP
    chip.click()
    assert not chip.isChecked() and messages[-1] == NOT_KNOWN_TIP
    assert window.kontrol.chips.on_names() == []
    chip.setFocus()
    _key(window, Qt.Key.Key_Space)
    assert not chip.isChecked()
    # it can still be deleted: it is not disabled for the keyboard
    _key(window, Qt.Key.Key_Delete)
    assert [f.name for f in _stored(tmp_path, window.kontrol._chip_owner_id).saved_filters] == [
        "Tekler"]


def test_accessible_names_say_on_and_the_state_is_checkable(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    chip = _chip(window, "Boşlar")
    assert chip.accessibleName() == "Boşlar" and chip.isCheckable()
    chip.click()
    assert chip.accessibleName() == "Boşlar, açık" and chip.isChecked()
    assert window.kontrol.chips.accessibleName() == "Kayıtlı filtreler"


# -- keys ---------------------------------------------------------------------------------------
def test_ctrl_shift_f_focuses_the_row_and_the_local_keys_work(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    screen.timeline.setFocus()
    pages_before = set(screen.controller.job.deleted)
    _key(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier
         | Qt.KeyboardModifier.ShiftModifier)
    assert QApplication.focusWidget() is _chip(window, "Tekler")
    _key(window, Qt.Key.Key_Right)
    assert QApplication.focusWidget() is _chip(window, "Boşlar")
    _key(window, Qt.Key.Key_Left)
    _key(window, Qt.Key.Key_Left)  # the first chip stops it
    assert QApplication.focusWidget() is _chip(window, "Tekler")
    _key(window, Qt.Key.Key_Space)
    assert _chip(window, "Tekler").isChecked() and _chosen(window)
    _key(window, Qt.Key.Key_Return)
    assert not _chip(window, "Tekler").isChecked()
    _key(window, Qt.Key.Key_Escape)  # back to the timeline, nothing else happens
    assert QApplication.focusWidget() is screen.timeline
    assert set(screen.controller.job.deleted) == pages_before


def test_del_on_a_chip_deletes_the_filter_not_a_page_and_undo_brings_it_back(qtbot, tmp_path):
    window, template = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    screen.timeline.select_rows(1, 1, 1)
    deleted_pages = set(screen.controller.job.deleted)
    screen.focus_saved_filters()
    _key(window, Qt.Key.Key_Right)  # Boşlar
    _key(window, Qt.Key.Key_Delete)
    assert set(screen.controller.job.deleted) == deleted_pages  # no page was deleted
    assert [f.name for f in _stored(tmp_path, template.id).saved_filters] == [
        "Tekler", "Yedinci belge"]
    assert window.toaster.current_text() == "Kayıtlı filtre silindi"
    assert [c.info.name for c in screen.chips.chips] == ["Tekler", "Yedinci belge"]
    assert QApplication.focusWidget() is screen.chips.chips[1]  # focus stays in the row
    stack = window.sablon.undo_stack
    assert stack.undoText() == "Kayıtlı filtre silindi"
    stack.undo()  # Geri al
    assert [f.name for f in _stored(tmp_path, template.id).saved_filters] == [
        "Tekler", "Boşlar", "Yedinci belge"]
    assert [c.info.name for c in screen.chips.chips] == ["Tekler", "Boşlar", "Yedinci belge"]
    stack.redo()
    assert [c.info.name for c in screen.chips.chips] == ["Tekler", "Yedinci belge"]


def test_the_close_mark_and_the_context_menu_delete_and_rename(qtbot, tmp_path, monkeypatch):
    window, template = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    chip = _chip(window, "Tekler")
    chip.show()
    chip._hover = True  # the × is on show while the pointer is over the chip
    close = chip._close_rect().center().toPoint()
    QTest.mouseClick(chip, Qt.MouseButton.LeftButton, pos=close)
    assert [f.name for f in _stored(tmp_path, template.id).saved_filters] == [
        "Boşlar", "Yedinci belge"]
    # the context menu lists "Yeniden adlandır" and "Sil"
    chip = _chip(window, "Boşlar")
    screen.chips._menu("Boşlar", chip.mapToGlobal(chip.rect().center()))
    assert [a.text() for a in screen.chips.menu.actions()] == ["Yeniden adlandır", "Sil"]
    screen.chips.menu.close()

    def fake_exec(self):
        self.field.setText("Boş olanlar")
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(SaveFilterDialog, "exec", fake_exec)
    screen.rename_saved_filter("Boşlar")
    assert [f.name for f in _stored(tmp_path, template.id).saved_filters] == [
        "Boş olanlar", "Yedinci belge"]
    assert window.sablon.undo_stack.undoText() == "Yeniden adlandır"


# -- saving a result ----------------------------------------------------------------------------
def _select_by(screen, monkeypatch, kind="tek"):
    monkeypatch.setattr(SelectDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    screen.select_by(kind)


def test_a_select_by_result_can_be_saved_as_a_chip_with_undo(qtbot, tmp_path, monkeypatch):
    window, template = _make(qtbot, tmp_path, ("Tekler", "tek", {}))
    screen = window.kontrol
    assert screen.chips.save.isHidden()
    _select_by(screen, monkeypatch, "bos")
    window.toaster.dismiss()  # the "3 boş sayfa seçildi" toast of the selection
    assert not screen.chips.save.isHidden() and screen.chips.save.text() == (
        "Kayıtlı filtrelere ekle…")
    names = []

    def fake_exec(self):
        names.append(self.field.text())  # the field starts with the kind's own word
        self.field.setText("  Boş sayfalarım ")
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(SaveFilterDialog, "exec", fake_exec)
    screen.chips.save.click()
    assert names == ["Boş sayfalar"]
    saved = _stored(tmp_path, template.id).saved_filters
    assert [(f.name, f.kind) for f in saved] == [("Tekler", "tek"), ("Boş sayfalarım", "bos")]
    assert window.toaster.current_text() == "Kayıtlı filtre eklendi: Boş sayfalarım"
    assert window.sablon.undo_stack.undoText() == "Kayıtlı filtre ekle"
    assert screen.chips.save.isHidden()  # saved: nothing more to add for this result
    window.sablon.undo_stack.undo()
    assert [f.name for f in _stored(tmp_path, template.id).saved_filters] == ["Tekler"]
    assert [c.info.name for c in screen.chips.chips] == ["Tekler"]


def test_a_new_selection_takes_the_save_button_away(qtbot, tmp_path, monkeypatch):
    window, _template_ = _make(qtbot, tmp_path, ("Tekler", "tek", {}))
    screen = window.kontrol
    _select_by(screen, monkeypatch, "tek")
    assert not screen.chips.save.isHidden()
    screen.timeline.select_rows(0, 0, 0)
    assert screen.chips.save.isHidden()


def test_with_no_filters_a_result_shows_the_row_and_the_button(qtbot, tmp_path, monkeypatch):
    _template(tmp_path)
    window = _window(qtbot, tmp_path, SPEC)
    screen = window.kontrol
    assert screen.chips.isHidden()
    _select_by(screen, monkeypatch, "tek")
    assert not screen.chips.isHidden() and not screen.chips.save.isHidden()
    assert screen.chips.count.text() == NONE_ON and screen.chips.chips == []
    screen.timeline.selectionModel().clearSelection()
    assert screen.chips.isHidden()  # no filters and no result: no empty bar


def test_with_no_template_the_row_says_there_is_none_and_offers_no_save(
        qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path, SPEC)  # the template folder is empty
    screen = window.kontrol
    assert screen.chips.isHidden()
    _select_by(screen, monkeypatch, "tek")
    assert not screen.chips.isHidden()
    assert screen.chips.note.text() == "Şablon yok" and not screen.chips.note.isHidden()
    assert screen.chips.save.isHidden()


def test_the_save_dialog_enter_saves_and_a_taken_name_stays_open(qtbot):
    dialog = SaveFilterDialog("Kayıtlı filtrelere ekle", {"Tekler"}, "Tekler")
    qtbot.addWidget(dialog)
    dialog.show()
    assert dialog.field.accessibleName() == "Filtrenin adı"
    assert [b.text() for b in dialog.findChildren(type(dialog.ok))] == ["Vazgeç", "Kaydet"]
    QTest.keyClick(dialog.field, Qt.Key.Key_Return)
    assert dialog.result() != QDialog.DialogCode.Accepted and not dialog.error.isHidden()
    assert "zaten var" in dialog.error.text()
    dialog.field.setText("Başka")
    QTest.keyClick(dialog.field, Qt.Key.Key_Return)
    assert dialog.result() == QDialog.DialogCode.Accepted and dialog.name() == "Başka"
    empty = SaveFilterDialog("Kayıtlı filtrelere ekle", set(), "  ")
    qtbot.addWidget(empty)
    empty.accept()
    assert empty.result() != QDialog.DialogCode.Accepted and "boş" in empty.error.text()


def test_saving_a_template_filter_is_fast_and_stays_on_the_window_thread(qtbot, tmp_path):
    window, template = _make(qtbot, tmp_path, ("Tekler", "tek", {}))
    start = time.perf_counter()
    for number in range(10):
        assert window.edit_template(template.id, "Kayıtlı filtre ekle",
                                    lambda t, n=number: t.add_saved_filter(f"F{n}", "tek"))
    each_ms = (time.perf_counter() - start) * 1000 / 10
    assert each_ms < 50, each_ms  # a few hundred bytes: no worker needed


# -- the window and the command line --------------------------------------------------------------
def test_the_window_and_is_sec_sablon_select_the_same_pages(qtbot, tmp_path, capsys):
    window, template = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    _chip(window, "Tekler").click()
    _chip(window, "Boşlar").click()
    rows = [r + 1 for r in _chosen(window)]  # positions as the command line counts them
    job = window.controller().job
    assert main(["--kok", str(tmp_path / "jobs"), "--sablon-kok", str(tmp_path / "tpl"),
                 "is", "sec", job.id, "--sablon", template.id,
                 "--filtre", "Tekler", "--filtre", "Boşlar"]) == 0
    out = capsys.readouterr().out
    line = next(x for x in out.splitlines() if x.startswith("sayfa "))
    assert [int(n) for n in line.removeprefix("sayfa ").split(", ")] == rows
    assert screen.chips.count.text() in out


def test_the_chip_row_selects_only_and_never_acts_on_pages(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    job = window.controller().job
    before = (set(job.deleted), dict(job.rotations), set(job.manual_cuts), list(job.filters),
              list(job.templates))
    _chip(window, "Tekler").click()
    _chip(window, "Boşlar").click()
    after = (set(job.deleted), dict(job.rotations), set(job.manual_cuts), list(job.filters),
             list(job.templates))
    assert before == after and not window.controller().undo_stack.canUndo()


# -- looks: tokens, size, wrapping ----------------------------------------------------------
def test_chips_are_32_px_high_pill_shaped_and_at_least_13_px(qtbot, tmp_path):
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    for chip in window.kontrol.chips.chips:
        assert chip.sizeHint().height() >= 32
        assert chip._font().pixelSize() >= 13
        assert chip.property("focusRadius") == 16
    source = (Path(theme.__file__).parent / "kontrol_chips.py").read_text(encoding="utf-8")
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", source)  # tokens only, no hex colours


def test_eight_chips_wrap_at_150_percent_and_keep_their_names(qtbot, tmp_path):
    filters = tuple((f"Kayıtlı süzgeç {n}", "tek", {}) for n in range(8))
    window, _template_ = _make(qtbot, tmp_path, *filters)
    window.resize(1366, 768)
    manager = theme.manager()
    before = manager.text_scale()
    manager.set_text_scale(150)
    try:
        qtbot.wait(20)
        row = window.kontrol.chips
        row.resize(900, row.heightForWidth(900))
        lines = row.heightForWidth(900)
        assert lines > 2 * 32  # more than one line of chips
        for chip in row.chips:
            width = chip.fontMetrics().horizontalAdvance(chip.info.name)
            assert chip.sizeHint().width() >= width  # the name is never cut
        assert row.heightForWidth(2400) < lines
    finally:
        manager.set_text_scale(before)


def test_a_long_name_is_cut_only_past_the_row_width_and_keeps_a_tooltip(qtbot, tmp_path):
    long_name = "Çok uzun bir filtre adı " * 8
    window, _template_ = _make(qtbot, tmp_path, (long_name.strip(), "tek", {}))
    chip = window.kontrol.chips.chips[0]
    assert chip.sizeHint().width() <= window.kontrol.chips.chip_room()
    assert chip.grab().width() > 0 and chip.toolTip() == long_name.strip()


# -- the template the row follows -----------------------------------------------------------------
def test_the_row_follows_the_template_of_the_selected_pages_until_the_chips_select(
        qtbot, tmp_path):
    first = _template(tmp_path, ("Tekler", "tek", {}), name="A şablonu")
    second = _template(tmp_path, ("Boşlar", "bos", {}), name="B şablonu")
    window = _window(qtbot, tmp_path, SPEC)
    screen = window.kontrol
    screen._chips_sync()
    assert [c.info.name for c in screen.chips.chips] == ["Tekler"]  # first by name
    ids = screen.controller.job.ordered_page_ids()
    screen.controller.apply_template([ids[4], ids[5]], second.id)
    screen.timeline.select_rows(4, 5, 5)
    assert [c.info.name for c in screen.chips.chips] == ["Boşlar"]
    _chip(window, "Boşlar").click()  # the pages it selects carry no template: the row stays
    assert [c.info.name for c in screen.chips.chips] == ["Boşlar"]
    assert first.id != second.id


# -- the registry ---------------------------------------------------------------------------------
def test_the_action_is_in_the_registry_the_menu_and_the_palette(qtbot, tmp_path):
    from evrakci.ui import actions

    spec = actions.spec("kontrol.kayitli_filtreler")
    assert spec.text.replace("&", "") == "Kayıtlı filtreler" and spec.menu == "araclar"
    assert spec.shortcuts == ("Ctrl+Shift+F",) and spec.context == "kontrol"
    assert not actions.validate()
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    action = window.registry.action("kontrol.kayitli_filtreler")
    assert action.isEnabled() and window.registry.live_keys("kontrol.kayitli_filtreler") == [
        "Ctrl+Shift+F"]
    window.kontrol.timeline.setFocus()
    action.trigger()  # the menu path
    assert QApplication.focusWidget() is _chip(window, "Tekler")
    ids = [e.id for e in window.registry.palette_entries("kontrol")]
    assert "kontrol.kayitli_filtreler" in ids


def test_ctrl_shift_f_with_nothing_to_focus_says_so(qtbot, tmp_path):
    _template(tmp_path)
    window = _window(qtbot, tmp_path, SPEC)
    messages = []
    window.controller().status.connect(messages.append)
    window.kontrol.timeline.setFocus()
    _key(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier
         | Qt.KeyboardModifier.ShiftModifier)
    assert messages[-1] == NONE_ON and QApplication.focusWidget() is window.kontrol.timeline


def test_del_and_esc_on_a_chip_are_not_page_commands(qtbot, tmp_path):
    """The chip accepts the shortcut override for its local keys, so the window's Del and Esc
    never fire while a chip has focus."""
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    chip = _chip(window, "Tekler")
    chip.setFocus()
    for key in (Qt.Key.Key_Delete, Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Space):
        event = QKeyEvent(QEvent.Type.ShortcutOverride, key, Qt.KeyboardModifier.NoModifier)
        event.ignore()
        QApplication.sendEvent(chip, event)
        assert event.isAccepted(), key
    other = QKeyEvent(QEvent.Type.ShortcutOverride, Qt.Key.Key_K, Qt.KeyboardModifier.NoModifier)
    other.ignore()
    QApplication.sendEvent(chip, other)
    assert not other.isAccepted()  # K (Burada kes) is not a chip key


def test_the_row_clips_nothing_at_1366x768_in_both_text_sizes(qtbot, tmp_path):
    """The matrix's clipping check (tools/screenshots.py) with the row on show: eight chips
    (one on, one that gives zero pages, one unknown), wrapped at 150 %."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    import screenshots

    manager = theme.manager()
    before = manager.text_scale()
    filters = (
        ("Boş sayfalar", "bos", {}), ("Tek sayfalar", "tek", {}),
        ("Çift sayfalar", "cift", {}), ("Farklı boyut veya yön", "farkli", {}),
        ("Kontrol gerekenler", "guven", {}), ("Yedinci belge", "belge", {"number": 99}),
        ("Bu belge", "gelecek", {}), ("Eski süzgeç", "tek", {}))
    try:
        for scale in (100, 150):
            manager.set_text_scale(scale)
            window, _template_ = _make(qtbot, tmp_path / f"s{scale}", *filters)
            window.resize(1366, 768)
            window.show_tab("kontrol")
            _chip(window, "Boş sayfalar").click()
            for _ in range(30):
                QApplication.processEvents()
            found = [f for f in screenshots.clipping(window, f"chips-{scale}")
                     if "kayitliFiltreler" in f or "FilterChip" in f]
            assert not found, found
    finally:
        manager.set_text_scale(before)


def test_tab_enters_the_row_on_one_chip_and_arrows_move_inside(qtbot, tmp_path):
    """HIG-FOC-08: one Tab stop for the whole row (the chip last used), arrows inside it;
    Shift+Tab from the timeline lands on it, Tab from it reaches the timeline again."""
    window, _template_ = _make(qtbot, tmp_path, *DEFAULT)
    screen = window.kontrol
    stops = [c for c in screen.chips.chips if c.focusPolicy() == Qt.FocusPolicy.StrongFocus]
    assert len(stops) == 1 and stops[0] is screen.chips.chips[0]
    screen.timeline.setFocus()
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Backtab)
    assert QApplication.focusWidget() is screen.chips.chips[0]
    _key(window, Qt.Key.Key_Right)
    _key(window, Qt.Key.Key_Right)
    last = screen.chips.chips[2]
    assert QApplication.focusWidget() is last
    stops = [c for c in screen.chips.chips if c.focusPolicy() == Qt.FocusPolicy.StrongFocus]
    assert stops == [last]  # the row remembers where you were
    for _ in range(4):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        if QApplication.focusWidget() is screen.timeline:
            break
    assert QApplication.focusWidget() is screen.timeline
