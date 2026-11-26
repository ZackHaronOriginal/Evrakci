"""Q-09: a key that cannot act is never silent.

On every tab, in a window with no job and in one with the demo job, every command that is
greyed (disabled) has a reason; the reason is the tooltip of the greyed menu item and button, and
pressing the command's key puts the same sentence in the status bar. The key still does nothing
harmful: the action stays disabled, so nothing it would do has happened.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import screenshots  # noqa: E402
from contract_helpers import press, reset, settle  # noqa: E402

from evrakci.ui import actions, refusals  # noqa: E402
from evrakci.ui.main_window import TAB_IDS  # noqa: E402
from evrakci.ui.palette import ID_ROLE  # noqa: E402


@pytest.fixture(scope="module")
def windows(qapp, tmp_path_factory):
    patch = pytest.MonkeyPatch()
    patch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path_factory.mktemp("ui") / "ui-ayarlar.ini"))
    made = {}

    def get(kind: str):
        if kind not in made:
            if kind == "empty":
                win = screenshots._empty_window(tmp_path_factory.mktemp("empty"))
            else:
                win = screenshots.build(tmp_path_factory.mktemp("demo"))
            win.resize(1366, 768)
            win.show()
            made[kind] = win
        win = made[kind]
        win.activateWindow()  # two windows are open: this one takes the keyboard
        assert QTest.qWaitForWindowActive(win)
        settle()
        return win

    yield get
    for win in made.values():
        if getattr(win, "thumbnails", None) is not None:
            win.thumbnails.stop()
        win.close()
        win.deleteLater()
    settle()
    patch.undo()


def _commands(win, tab: str):
    """The commands of `tab` and of the app that are shown and greyed right now."""
    reset(win, tab)
    registry = win.registry
    for spec in actions.SPECS:
        if spec.context not in ("app", tab) or (spec.local and not spec.menu):
            continue  # a widget's own keys (arrows, Tab, Alt+1..4) are not greyed commands
        action = registry.action(spec.id)
        if action.isVisible() and not action.isEnabled():
            yield spec, action


@pytest.mark.parametrize("window_kind", ["empty", "job"])
@pytest.mark.parametrize("tab", TAB_IDS)
def test_every_greyed_command_has_a_reason_as_its_tooltip(windows, tab, window_kind):
    win = windows(window_kind)
    missing = []
    for spec, action in _commands(win, tab):
        reason = win.registry.disabled_reason(spec.id)
        if not reason:
            missing.append(spec.id)
        elif action.toolTip() != reason:
            missing.append(f"{spec.id}: tooltip {action.toolTip()!r} is not {reason!r}")
    assert not missing, f"{tab} ({window_kind}): {missing}"


@pytest.mark.parametrize("window_kind", ["empty", "job"])
@pytest.mark.parametrize("tab", TAB_IDS)
def test_every_greyed_key_says_its_reason_in_the_status_bar(windows, tab, window_kind):
    win = windows(window_kind)
    silent = []
    pressed = 0
    for spec, _action in list(_commands(win, tab)):
        if spec.local:
            continue
        for key in spec.shortcuts:
            reset(win, tab)
            win.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)  # no field, no button
            settle()
            reason = win.registry.disabled_reason(spec.id)
            if not reason or win.registry.is_enabled(spec.id):
                continue
            win.message.setText("")
            win.sablon.message.setText("")
            press(win, key)
            pressed += 1
            if reason not in (win.message.text(), win.sablon.message.text(),
                              win.toaster.current_text()):
                silent.append(f"{spec.id} {key}: {win.message.text()!r}")
            assert not win.registry.is_enabled(spec.id), "the key must not enable the command"
    assert not silent, f"{tab} ({window_kind}): {silent}"
    assert QApplication.activeModalWidget() is None
    assert pressed or tab in ("rehber",) or window_kind == "job", (tab, window_kind)


def test_the_reason_goes_back_to_the_normal_tooltip_when_the_command_can_act(windows):
    win = windows("job")
    reset(win, "kontrol")
    action = win.registry.action("app.yan_panel")
    assert action.isEnabled()
    assert action.toolTip().endswith("(F9)"), action.toolTip()
    win.registry.set_enabled("app.yan_panel", False)
    assert win.registry.disabled_reason("app.yan_panel") == refusals.NO_JOB_TEXT
    assert action.toolTip() == refusals.NO_JOB_TEXT
    win._sync_inspector()
    assert action.isEnabled() and action.toolTip().endswith("(F9)"), action.toolTip()


def test_a_greyed_menu_item_shows_its_reason_as_a_tooltip(windows):
    win = windows("empty")
    reset(win, "kontrol")
    menu = win.menu_row.menus()[1]  # Düzen
    menu.aboutToShow.emit()
    assert menu.toolTipsVisible()
    item = win.registry.action("kontrol.kes")
    assert item in menu.actions()
    assert not item.isEnabled() and item.toolTip() == refusals.NO_JOB_TEXT


def test_the_palette_says_the_reason_when_a_greyed_command_is_chosen(windows):
    win = windows("empty")
    reset(win, "yukle")
    win.message.setText("")
    palette = win.command_palette
    palette.open_for("yukle")
    palette.field.setText("sonraki sonuç")
    settle()
    for row in range(palette.list.count()):
        if palette.list.item(row).data(ID_ROLE) == "app.sonraki_sonuc":
            palette.list.setCurrentRow(row)
    QTest.keyClick(palette.field, Qt.Key.Key_Return)
    settle()
    assert win.message.text() == refusals.NO_RESULTS_HERE
    assert not palette.isVisible()
