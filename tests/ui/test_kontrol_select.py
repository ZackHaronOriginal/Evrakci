"""I-09: Ölçüte göre seç… (S), Bu belgeyi seç (B), Ctrl+Space and Alt+Left / Alt+Right on Kontrol.

Documents of the demo job (test_kontrol_a.SPEC): rows 0-2 | QR 3 | 4-5 | QR 6 | 7-10 | QR 11 | 12.
"""

from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import QItemSelectionModel, QModelIndex, Qt
from PySide6.QtTest import QTest
from test_kontrol_a import _key, _screen, _window

from evrakci.cli import main
from evrakci.pipeline.select import Criterion, evaluate
from evrakci.pipeline.store import JobStore
from evrakci.ui import actions
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol_dialogs import SelectDialog
from evrakci.ui.main_window import COMMANDS, Cmd

CTRL = Qt.KeyboardModifier.ControlModifier
ALT = Qt.KeyboardModifier.AltModifier


def _chosen(window) -> list[int]:
    return sorted(i.row() for i in window.kontrol.timeline.selectionModel().selectedIndexes())


def _go(window, row):
    screen = window.kontrol
    screen.timeline.select_rows(row, row, row)
    screen.timeline.setFocus()


def test_ctrl_space_adds_and_removes_the_current_page(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(0, 1, 1)
    screen.timeline.selectionModel().setCurrentIndex(
        screen.model.index(8), QItemSelectionModel.SelectionFlag.NoUpdate)
    _key(window, Qt.Key.Key_Space, CTRL)
    assert _chosen(window) == [0, 1, 8]  # the other pages stay selected
    _key(window, Qt.Key.Key_Space, CTRL)
    assert _chosen(window) == [0, 1]
    assert not screen._loupe or not screen._loupe.is_open()  # it is not Space (the loupe)


def test_ctrl_space_with_no_current_page_says_so(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.selectionModel().setCurrentIndex(
        QModelIndex(), QItemSelectionModel.SelectionFlag.NoUpdate)
    messages = []
    screen.controller.status.connect(messages.append)
    screen.toggle_current()
    assert messages == ["Önce bir sayfa seçin."]


def test_alt_arrows_move_the_focus_and_keep_the_selection(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(4, 6, 6)
    _key(window, Qt.Key.Key_Right, ALT)
    assert screen.current_row() == 7 and _chosen(window) == [4, 5, 6]
    _key(window, Qt.Key.Key_Left, ALT)
    _key(window, Qt.Key.Key_Left, ALT)
    assert screen.current_row() == 5 and _chosen(window) == [4, 5, 6]
    for _ in range(20):
        _key(window, Qt.Key.Key_Left, ALT)
    assert screen.current_row() == 0 and _chosen(window) == [4, 5, 6]  # the first page stops it


def test_b_selects_exactly_the_pages_of_the_current_document(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    _go(window, 5)
    _key(window, Qt.Key.Key_B)
    assert _chosen(window) == [4, 5]
    assert window.toaster.current_text() == "2 sayfa seçildi."
    _go(window, 9)
    screen.select_document()
    assert _chosen(window) == [7, 8, 9, 10]


def test_b_on_a_document_with_every_page_deleted_says_so(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    assert ctl.delete_page(ctl.job.page_at(5)) and ctl.delete_page(ctl.job.page_at(6))
    _go(window, 4)
    messages = []
    ctl.status.connect(messages.append)
    screen.select_document()
    assert messages == ["Bu belgede seçilecek sayfa yok."]


def test_the_select_dialog_counts_and_selects_odd_pages(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    ctl = window.controller()
    before = ctl.undo_stack.index()
    _go(window, 5)
    seen = {}

    def answer(dialog):
        seen["title"] = dialog.windowTitle()
        seen["counts"] = {k: dialog._counts[k].text() for k in dialog._counts}
        seen["checked"] = dialog.kind()
        dialog._radios["tek"].setChecked(True)
        seen["hint"] = dialog.hint.text()
        return True  # Seç

    monkeypatch.setattr(SelectDialog, "exec", answer)
    _key(window, Qt.Key.Key_S)
    assert seen["title"] == "Sayfaları seç" and seen["checked"] == "belge"
    # documents of 3, 2, 4, 1; the demo job has no blank page
    assert seen["counts"] == {"belge": "2", "tek": "6", "cift": "4", "bos": "Hiç yok",
                              "guven": "Değerler henüz okunmadı", "farkli": "Hiç yok"}
    assert seen["hint"] == "Her belgenin 1., 3., 5. ... sayfaları"
    assert _chosen(window) == [0, 2, 4, 7, 9, 12]
    assert window.toaster.current_text() == "6 sayfa seçildi."
    assert ctl.undo_stack.index() == before  # selecting is not an edit


def test_the_select_dialog_modes_and_counts_in_the_selection(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    job = window.controller().job
    chosen = [screen.model.page_id(r) for r in (4, 5, 6, 7)]  # document 2, a QR page, a page
    dialog = SelectDialog(job, 2, chosen, parent=window)
    qtbot.addWidget(dialog)
    assert dialog._counts["belge"].text() == "2" and dialog._counts["tek"].text() == "6"
    dialog._mode_radios["within"].setChecked(True)
    assert dialog._counts["tek"].text() == "2"  # odd pages of documents 2, 3 in it
    assert dialog._counts["cift"].text() == "1"
    assert dialog.criterion("tek").params == {"within": True}
    dialog._mode_radios["replace"].setChecked(True)
    assert dialog.criterion("tek").params == {"within": False}
    other = SelectDialog(job, 99, [], parent=window)
    qtbot.addWidget(other)
    assert other._counts["belge"].text() == "Hiç yok"
    assert other._radios["belge"].accessibleName() == "Bu belge, Hiç yok"
    assert other.ok.isDefault()


def test_select_with_nothing_matching_keeps_the_selection(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(0, 1, 1)
    messages = []
    window.controller().status.connect(messages.append)
    assert screen.select_matching(Criterion("belge", {"number": 99})) == 0
    assert messages == ["Eşleşen sayfa yok."] and _chosen(window) == [0, 1]
    screen.select_matching(Criterion("cift", {"within": True}), "within")
    assert _chosen(window) == [1]
    screen.select_matching(Criterion("belge", {"number": 4}), "add")
    assert _chosen(window) == [1, 12]


def test_select_menu_paths_and_the_command_bar(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    registry = window.registry
    for action_id, key in (("kontrol.sec", "S"), ("kontrol.belgeyi_sec", "B"),
                           ("kontrol.sayfa_sec", "Ctrl+Space"),
                           ("kontrol.git_secimsiz", "Alt+Right"),
                           ("kontrol.git_secimsiz_sol", "Alt+Left")):
        assert registry.is_enabled(action_id), action_id
        assert (actions.key_text(key) in registry.action(action_id).text()
                or key in registry.live_keys(action_id))
    on_bar = {e.id: e for e in COMMANDS["kontrol"] if isinstance(e, Cmd)}
    assert on_bar["kontrol.sec"].icon == "list-checks"
    assert registry.action("kontrol.sec").toolTip() == "Ölçüte göre seç (S)"
    screen = window.kontrol
    _go(window, 5)
    registry.action("kontrol.belgeyi_sec").trigger()
    assert _chosen(window) == [4, 5]
    screen._context_menu(screen.timeline.page_rect(4).center())
    names = [a.text().replace("&", "").split("\t")[0] for a in screen.menu.actions()
             if not a.isSeparator()]
    assert "Bu belgeyi seç" in names and "Ölçüte göre seç…" in names
    screen.menu.close()


def test_the_window_and_the_command_line_select_the_same_pages(qtbot, tmp_path):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()] * 4 + [qr_page()] + [text_page()] * 3)
    assert main(["--kok", str(root), "is", "olustur", "Test", str(pdf)]) == 0
    store = JobStore(root)
    job = store.load(store.list_jobs()[0].id)
    screen = _screen(qtbot, JobController(store, job))
    screen.select_matching(Criterion("cift"))
    rows = sorted(i.row() for i in screen.timeline.selectionModel().selectedIndexes())
    assert rows == [1, 3, 6]
    order = job.ordered_page_ids()
    assert [order[r] for r in rows] == list(evaluate(job, Criterion("cift")).page_ids)


def test_select_add_with_nothing_matching_says_so_and_changes_nothing(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(0, 1, 1)
    messages = []
    window.controller().status.connect(messages.append)
    for mode in ("add", "within"):
        assert screen.select_matching(Criterion("belge", {"number": 99}), mode) == 0
        assert _chosen(window) == [0, 1]
    assert messages == ["Eşleşen sayfa yok."] * 2


def test_alt_left_has_its_own_git_menu_item_with_the_same_label(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    registry = window.registry
    right = registry.action("kontrol.git_secimsiz")
    left = registry.action("kontrol.git_secimsiz_sol")
    label = [a.text().replace("&", "").split("\t")[0] for a in (right, left)]
    assert label[0] == label[1] == "Seçimi bozmadan git"
    assert actions.key_text("Alt+Right") in right.text()
    assert actions.key_text("Alt+Left") in left.text()
    _go(window, 6)
    left.trigger()
    assert window.kontrol.current_row() == 5
    right.trigger()
    right.trigger()
    assert window.kontrol.current_row() == 7


def test_access_keys_are_unique_in_every_menu_including_the_page_context_menu(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    for title, items in actions.menu_structure("kontrol"):
        letters = [actions.access_key(actions.spec(i).text) for i in items if i]
        letters = [x for x in letters if x]
        assert len(letters) == len(set(letters)), title
    screen = window.kontrol
    _go(window, 5)
    screen._context_menu(screen.timeline.page_rect(4).center())
    keys = [a.text().split("\t")[0].split("&")[1][0].upper() for a in screen.menu.actions()
            if not a.isSeparator() and "&" in a.text().split("\t")[0]]
    screen.menu.close()
    repeated = {k for k in keys if keys.count(k) > 1}
    assert repeated <= {"D"}, keys  # D (Sağa döndür / Değerlerde aç) was already shared before I-09


def _tab_stops(dialog, count):
    from PySide6.QtWidgets import QApplication
    stops = []
    for _ in range(count):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        stops.append(QApplication.focusWidget())
    return stops


def test_tab_goes_criterion_then_parameters_then_modes_then_sec(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    dialog = SelectDialog(window.controller().job, 1, [], "bos", parent=window)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.activateWindow()
    qtbot.waitUntil(dialog.isActiveWindow)
    dialog._radios["bos"].setFocus()
    first, second, third = _tab_stops(dialog, 3)
    assert first is dialog.ink  # the criterion's parameter comes before the modes
    assert second is dialog._mode_radios["replace"]
    assert third is dialog.ok


def test_tab_from_guven_visits_its_reasons_and_pages_before_the_modes(qtbot, tmp_path):
    from test_kontrol_guven import SPEC, _dialog, _prepare
    window = _window(qtbot, tmp_path, spec=SPEC)
    _prepare(window)
    dialog = _dialog(window, qtbot)
    dialog.show()
    dialog.activateWindow()
    qtbot.waitUntil(dialog.isActiveWindow)
    dialog._radios["guven"].setFocus()
    stops = _tab_stops(dialog, 1)
    assert stops[0] is next(iter(dialog._reason_boxes.values()))
    seen = _tab_stops(dialog, 12)
    modes = dialog._mode_radios["replace"]
    assert dialog.pages_value in seen[:seen.index(modes)]
    assert seen[seen.index(modes) + 1] is dialog.ok


def test_the_dialog_count_in_add_mode_is_the_size_of_the_union(qtbot, tmp_path):
    """R-A-8: the row count equals what Seç selects in the chosen mode."""
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(0, 0, 0)  # an odd page (row 0) outside the match "cift"
    dialog = SelectDialog(window.controller().job, 1, screen._chosen_ids(), "cift", window)
    qtbot.addWidget(dialog)
    match = evaluate(window.controller().job, Criterion("cift"))
    assert dialog.count("cift") == len(match.page_ids)  # replace
    dialog._mode_radios["add"].setChecked(True)
    assert dialog.count("cift") == len(match.page_ids) + 1
    chosen = screen.select_matching(dialog.criterion(), dialog.mode())
    assert chosen == dialog.count("cift")


def test_menu_bar_entries_that_would_do_nothing_are_dimmed(qtbot, tmp_path):
    """R-A-12 (spec I-08 section 4): dimmed in Araçlar as in the context menu; the key
    itself still answers in words (the registry action stays enabled)."""
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(0, 0, 0)

    def araclar():
        menu = next(a.menu() for a in window.menu_row.bar.actions()
                    if actions.plain_text(a.text()) == "Araçlar")
        menu.aboutToShow.emit()
        return {a.objectName(): a for a in menu.actions()}

    items = araclar()
    for action_id in ("kontrol.filtre_kaldir", "kontrol.sablon_kaldir"):
        assert action_id in items and not items[action_id].isEnabled(), action_id
        assert window.registry.action(action_id).isEnabled()
    job = window.controller().job
    job.apply_filter(job.ordered_page_ids()[:3], 3)
    screen.timeline.select_rows(0, 0, 0)
    screen.sync_availability()
    assert araclar()["kontrol.filtre_kaldir"].isEnabled()
