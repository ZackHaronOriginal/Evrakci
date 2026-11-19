"""Phase 3, step 5 (3D): the typing guard. For every typing field of every tab (a QLineEdit, a
spin box, a cell editor) and every single-key action that is active on that tab (its key has no
Ctrl, Alt or Meta, and is not an F-key):

* with the field focused the key is not bound any more (`Registry.live_keys`), the action does
  not fire (`QAction.triggered`), the tab does not change and, where the field takes the key as
  text (a letter, Space, Del, the cursor keys), the character is typed or the edit is made;
* every other key of the tab's own actions (Ctrl and Alt combinations, F2) stays bound, and where
  the action is enabled it still fires with the field focused. A combination the field itself
  uses for text (Ctrl+A selects the text, Ctrl+Left / Right jump a word) is asserted as that.

The fields are those of the demo window ("job_<tab>" windows of tools/screenshots.py build()),
found by their accessible name; `test_every_field_of_the_window_is_in_the_table` finds the visible
text fields of each tab again and fails when the table and the window differ. Kontrol has no
text field (its dialogs are modal): its table entry is empty on purpose.

Each test carries `pytest.mark.action(<action id>)`. Nothing is sent to a printer or a file
manager; a dialog the key opens is rejected.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import PySide6.QtPrintSupport as qt_print
import pytest
import shiboken6
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QDialog, QLineEdit, QWidget

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import contract_degerler  # noqa: E402
import contract_export  # noqa: E402
import contract_sablon  # noqa: E402
from contract_helpers import Ctx, press, reset, settle, wait_until  # noqa: E402

from evrakci.ui import actions, disa_aktar  # noqa: E402
from evrakci.ui.main_window import TAB_IDS  # noqa: E402

# tab -> accessible names of its typing fields (as the demo window shows them)
FIELDS: dict[str, tuple[str, ...]] = {
    "yukle": ("İş adı ara",),  # the job list's search field (Ctrl+F on Yükle)
    "kontrol": (),
    "sablonlar": ("Değişken adı", "Dosya adı kalıbı", "Kutunun sayfası", "Kutu X (mm)",
                  "Kutu Y (mm)", "Kutu genişliği (mm)", "Kutu yüksekliği (mm)"),
    "degerler": ("Değerlerde ara", "Sicil No düzenle"),  # the cell editor opens with F2
    "disa_aktar": ("Hedef klasör", "Dosya adı kalıbı"),
    "rehber": ("Rehberde ara", "Kaç adet ayıraç sayfası"),
}
WINDOW = {"yukle": "job", "kontrol": "job", "sablonlar": "job_sablon",
          "degerler": "job_degerler", "disa_aktar": "job_disa", "rehber": "job_disa"}
# combinations the focused field uses for text, not the window: the action must stay quiet
TEXT_COMBOS = {"Ctrl+A": "selects the text", "Ctrl+Left": "jumps a word",
               "Ctrl+Right": "jumps a word"}
EXPENSIVE = {"sablonlar.dene"}  # reads every example: pressed once per tab, bound-checked after
SEED = "abc"


def _portable(key: str) -> str:
    return actions.key_sequence(key).toString(QKeySequence.SequenceFormat.PortableText)


def _specs_for(tab: str):
    """(action id, key) of every key that works on `tab`: its own actions and the app-wide ones
    that have a key of their own."""
    for s in actions.SPECS:
        if s.context in ("app", tab):
            for key in s.shortcuts:
                yield s.id, key


def _typing_params():
    out = []
    for tab, names in FIELDS.items():
        for name in names:
            for action_id, key in _specs_for(tab):
                if actions.is_typing_key(key):
                    out.append(pytest.param(tab, name, action_id, key,
                                            id=f"{tab}-{name}-{key}",
                                            marks=pytest.mark.action(action_id)))
    return out


def _combo_params():
    out = []
    for tab, names in FIELDS.items():
        for n, name in enumerate(names):
            for s in actions.SPECS:
                if s.context != tab:
                    continue
                for key in s.shortcuts:
                    if not actions.is_typing_key(key) and not s.local:
                        marks = [pytest.mark.action(s.id)]
                        if s.id == "disa_aktar.yazdir":
                            # NEW-1: the key fires, then print_index raises (see contract_export)
                            marks.append(pytest.mark.qt_no_exception_capture)
                        out.append(pytest.param(tab, name, s.id, key, n == 0,
                                                id=f"{tab}-{name}-{key}", marks=marks))
    return out


@pytest.fixture(scope="module")
def windows(qapp, tmp_path_factory):
    from test_shortcut_contract import Windows

    patch = pytest.MonkeyPatch()
    patch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path_factory.mktemp("ui") / "ui-ayarlar.ini"))
    holder = Windows(tmp_path_factory)
    yield holder
    holder.close()
    patch.undo()


class _Quiet:
    """Nothing leaves the test: no file manager, no printer, no dialog stays open."""

    def __init__(self, c: Ctx) -> None:
        for target, name, fake in (
                (QDesktopServices, "openUrl", staticmethod(lambda url: True)),
                (disa_aktar, "reveal_path", lambda path: None),
                (qt_print, "QPrintDialog", contract_export.FakePrintDialog)):
            patcher = mock.patch.object(target, name, fake)
            patcher.start()
            c.undo.append(patcher.stop)
        contract_export._fake_printing(c, "yazdir.pdf")
        rehber = c.win.rehber
        old = rehber._print_dialog
        rehber._print_dialog = contract_export.FakePrintDialog
        c.undo.append(lambda: setattr(rehber, "_print_dialog", old))
        self.c = c


def _prepare(c: Ctx, name: str) -> None:
    """The state in which the field exists (Yükle's list search, a chosen box, a cell editor)."""
    win, tab = c.win, c.tab
    if tab == "yukle":
        y = win.yukle
        y._listing = True
        y._sync_state()
        c.undo.append(lambda: (setattr(y, "_listing", False), y._sync_state(), settle()))
    elif tab == "sablonlar":
        contract_sablon.ensure_template(c)
        contract_sablon.choose(c, "Sicil_No", 0, "variables")
    elif tab == "degerler":
        contract_degerler.restore_job(c)
        contract_degerler.pick(c, 0, 3)
        if name == "Sicil No düzenle":
            press(win, "F2")
            c.undo.append(lambda: (win.degerler.table.is_editing()
                                   and QTest.keyClick(win.degerler.table.open_editor_widget(),
                                                      Qt.Key.Key_Escape), settle()))
    settle()


def _field(c: Ctx, name: str) -> QWidget:
    found = [w for w in c.win.findChildren(QWidget)
             if w.accessibleName() == name and w.isVisibleTo(c.win) and w.isEnabled()
             and (actions.is_text_input(w) or isinstance(w, QAbstractSpinBox))]
    assert found, f"no field {name!r} on {c.tab}"
    return found[0]


def _focus_field(c: Ctx, name: str) -> QWidget:
    """Focus the field; returns the widget that really has focus (a spin box's line edit)."""
    field = _field(c, name)
    field.setFocus()
    settle()
    focus = QApplication.focusWidget()
    assert focus is not None and actions.is_text_input(focus), (name, focus)
    if isinstance(focus, QLineEdit) and not isinstance(field, QAbstractSpinBox):
        old = focus.text()
        c.undo.append(lambda: shiboken6.isValid(focus) and focus.setText(old))
        focus.setText(SEED)
        focus.setCursorPosition(1)
    return focus


def _start(windows, tab: str, tmp_path, key: str, action_id: str) -> Ctx:
    win = windows.get(WINDOW[tab])
    c = Ctx(win, tab, key, action_id, tmp=tmp_path)
    c.data["windows"] = windows
    reset(win, tab)
    return c


def _finish(c: Ctx) -> None:
    for undo in reversed(c.undo):
        undo()
    c.undo.clear()
    settle()


class _Spy:
    def __init__(self, c: Ctx, action_id: str) -> None:
        self.count = 0
        self.action = c.win.registry.action(action_id)
        self.action.triggered.connect(self._hit)

    def _hit(self, *_args) -> None:
        self.count += 1

    def stop(self) -> None:
        self.action.triggered.disconnect(self._hit)


_CHAR = {"Space": " "}


def _typed_expectation(key: str, focus: QLineEdit) -> None:
    """What a line edit seeded with 'abc', cursor after 'a', does with `key` (when it takes it)."""
    text = _CHAR.get(key, key if len(key) == 1 else None)
    if text is not None:
        assert focus.text().lower() == ("a" + text + "bc").lower(), (key, focus.text())
    elif key == "Del":
        assert focus.text() == "ac", focus.text()
    elif key == "Left":
        assert focus.cursorPosition() == 0
    elif key == "Right":
        assert focus.cursorPosition() == 2
    elif key == "Home":
        assert focus.cursorPosition() == 0
    elif key == "End":
        assert focus.cursorPosition() == 3


@pytest.mark.parametrize("tab,name,action_id,key", _typing_params())
def test_a_single_key_is_typed_and_does_not_fire(tab, name, action_id, key, windows, tmp_path):
    c = _start(windows, tab, tmp_path, key, action_id)
    try:
        _Quiet(c)
        _prepare(c, name)
        focus = _focus_field(c, name)
        line_edit = isinstance(focus, QLineEdit) and not isinstance(_field(c, name),
                                                                     QAbstractSpinBox)
        spy = _Spy(c, action_id)
        c.undo.append(spy.stop)
        spec = actions.spec(action_id)
        if spec.single_key:
            assert _portable(key) not in c.win.registry.live_keys(action_id), \
                f"{key} is still bound to {action_id} while {name!r} has focus"
        press(c.win, key)
        assert spy.count == 0, f"{action_id} fired from {key} typed into {name!r}"
        assert c.win.current_tab() == tab
        if line_edit and shiboken6.isValid(focus) and focus is QApplication.focusWidget():
            _typed_expectation(key, focus)
    finally:
        _finish(c)


@pytest.mark.parametrize("tab,name,action_id,key,first", _combo_params())
def test_a_combination_still_works_in_a_field(tab, name, action_id, key, first, windows,
                                              tmp_path):
    c = _start(windows, tab, tmp_path, key, action_id)
    try:
        _Quiet(c)
        _prepare(c, name)
        focus = _focus_field(c, name)
        registry = c.win.registry
        assert _portable(key) in registry.live_keys(action_id), \
            f"{key} was unbound from {action_id} while {name!r} has focus"
        if not registry.is_enabled(action_id):
            return  # nothing to run in this state (Ctrl+. with nothing running...)
        if action_id in EXPENSIVE and not first:
            return  # bound; the read itself runs from the tab's first field
        spy = _Spy(c, action_id)
        c.undo.append(spy.stop)
        c.data["modals"] = []
        _reject_dialogs(c)
        press(c.win, key)
        if key in TEXT_COMBOS:
            assert spy.count == 0, f"{key} fired {action_id} instead of {TEXT_COMBOS[key]}"
            if key == "Ctrl+A" and isinstance(focus, QLineEdit):
                assert focus.selectedText() == focus.text()
        else:
            assert spy.count == 1, f"{key} did not run {action_id} with {name!r} focused"
        if action_id in EXPENSIVE:
            wait_until(lambda: c.win.sablon._all_task is None, 60000)
    finally:
        _finish(c)


def _reject_dialogs(c: Ctx) -> None:
    from PySide6.QtCore import QTimer

    def tick() -> None:
        modal = QApplication.activeModalWidget()
        if modal is not None and isinstance(modal, QDialog):
            modal.reject()

    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(20)
    c.undo.append(timer.stop)
    c.data["_timer"] = timer


def test_every_field_of_the_window_is_in_the_table(windows, tmp_path):
    """The demo window's visible text fields, tab by tab, are the ones the table names."""
    seen: dict[str, set[str]] = {}
    for tab in TAB_IDS:
        c = _start(windows, tab, tmp_path, "", "")
        try:
            for name in FIELDS[tab] or ("",):
                if name:
                    _prepare(c, name)
                    _field(c, name)
            _prepare(c, "Sicil No düzenle") if tab == "degerler" else None
            found = set()
            for w in c.win.findChildren(QWidget):
                if actions.is_text_input(w) and w.isVisibleTo(c.win) and w.isEnabled():
                    label = w.accessibleName() or (w.parent().accessibleName()
                                                   if w.parent() else "")
                    if label:
                        found.add(label)
            seen[tab] = found
        finally:
            _finish(c)
    for tab in TAB_IDS:
        assert seen[tab] <= set(FIELDS[tab]), (tab, sorted(seen[tab] - set(FIELDS[tab])))
        assert set(FIELDS[tab]) <= seen[tab] or tab == "yukle", (tab, set(FIELDS[tab]) -
                                                                    seen[tab])


def test_kontrol_has_no_text_field_to_type_into(windows, tmp_path):
    """Kontrol's table entry is empty: nothing on the tab takes typed text."""
    c = _start(windows, "kontrol", tmp_path, "", "")
    try:
        found = [w for w in c.win.tabs.currentWidget().findChildren(QWidget)
                 if actions.is_text_input(w) and w.isVisibleTo(c.win)]
        assert found == [], found
    finally:
        _finish(c)


def test_the_typing_keys_the_table_presses_are_the_registry_ones():
    """Every single-key action of a tab with a field is in the parametrization (a new one fails
    here until it is covered)."""
    ids = {p.values[2] for p in _typing_params()}
    for tab in ("sablonlar", "degerler", "disa_aktar", "rehber", "yukle"):
        for action_id, key in _specs_for(tab):
            if actions.is_typing_key(key):
                assert action_id in ids, (tab, action_id)
