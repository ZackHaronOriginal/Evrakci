"""I-28: the weakest examples first on Şablonlar (N / Shift+N, Ctrl+L, the status item)."""

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu, QStyle
from shiboken6 import isValid
from test_sablon_window import _window

from evrakci.pipeline.templates.values import SectionReading, VariableValue
from evrakci.ui import sablon_weak, theme
from evrakci.ui.style import EvrakciStyle

NEEDS_TRY = "Önce Ctrl+T ile örnekleri deneyin."


def _weak(*confidences):
    readings = tuple(SectionReading(i, "x", c) for i, c in enumerate(confidences))
    return VariableValue("", 0.0, None, True, "x", readings)


def _fine():
    return VariableValue("x", 0.95, 0, False, "", (SectionReading(0, "x", 0.95),))


@pytest.fixture
def screen(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.sablon
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen.set_example(1)
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen.read_example = lambda: None  # the order under test is the injected one
    return screen


def _tried(screen, results):
    """What "Bütün örneklerde dene" leaves behind."""
    screen.example_values = results
    screen.tried_all = True
    screen._mark_example_checks()
    screen._sync_all()


# worst first: 3 (two reads), 2 (one read, 38 %), 1 (one read, 61 %)
RESULTS = {1: {"a": _weak(0.61), "b": _fine()}, 2: {"a": _weak(0.38), "b": _fine()},
           3: {"a": _weak(0.5), "b": _weak(0.45)}}


def test_the_list_is_in_weakest_first_order(qtbot, screen):
    _tried(screen, RESULTS)
    screen.show_weak_list()
    menu = screen._weak_menu
    rows = [a.text() for a in menu.actions() if a.data() is not None]
    assert rows == ["Belge 3  2 kontrol  en düşük %45", "Belge 2  1 kontrol  en düşük %38",
                    "Belge 1  1 kontrol  en düşük %61"]
    header = menu.actions()[0]  # the title the sketch shows at the top: shown, never chosen
    assert header.text() == "Zayıf örnekler" and not header.isEnabled()
    menu.close()


def test_n_walks_the_order_and_wraps_round(qtbot, screen):
    _tried(screen, RESULTS)
    seen = []
    for _ in range(4):
        screen.jump_weak(1)
        seen.append(screen.example)
    assert seen == [3, 2, 1, 3]  # example 1 is last in the order: N wraps to the first (3)
    screen.jump_weak(-1)
    assert screen.example == 1  # and Shift+N wraps back to the last


def test_n_with_one_weak_example_says_so(qtbot, screen):
    _tried(screen, {1: {"a": _weak(0.4)}, 2: {"a": _fine()}})
    screen.jump_weak(1)
    assert screen.example == 1
    assert screen.message.text() == "Kontrol gereken tek belge bu."


def test_enter_in_the_list_opens_that_example(qtbot, screen):
    _tried(screen, RESULTS)
    screen.show_weak_list()
    menu = screen._weak_menu
    assert menu.isVisible()
    QTest.keyClick(menu, Qt.Key.Key_Down)  # first row: Belge 3
    QTest.keyClick(menu, Qt.Key.Key_Down)  # Belge 2
    QTest.keyClick(menu, Qt.Key.Key_Return)
    assert screen.example == 2
    assert not menu.isVisible()


def test_esc_closes_the_list_and_changes_nothing(qtbot, screen):
    _tried(screen, RESULTS)
    screen.show_weak_list()
    menu = screen._weak_menu
    QTest.keyClick(menu, Qt.Key.Key_Escape)
    assert not menu.isVisible() and screen.example == 1


def test_a_long_list_shows_eight_rows_then_scrolls(qtbot, screen):
    many = {n: {"a": _weak(0.1 + n / 100)} for n in range(1, 21)}
    _tried(screen, many)
    screen.show_weak_list()
    menu = screen._weak_menu
    item = theme.manager().menu_item_height()
    assert menu.height() <= item * (sablon_weak.POPUP_ROWS + 1) + theme.manager().size("s2")
    assert menu.height() < item * 20  # 20 rows do not all fit: the rest scrolls
    hint = EvrakciStyle().styleHint
    assert hint(QStyle.StyleHint.SH_Menu_Scrollable, None, menu)  # this list scrolls
    assert not hint(QStyle.StyleHint.SH_Menu_Scrollable, None, QMenu())  # no other menu changes
    assert not hint(QStyle.StyleHint.SH_Menu_Scrollable)
    menu.close()


def test_with_nothing_weak_the_list_says_so(qtbot, screen):
    _tried(screen, {1: {"a": _fine()}, 2: {"a": _fine()}})
    screen.show_weak_list()
    texts = [a.text() for a in screen._weak_menu.actions()]
    assert "Zayıf örnek yok: hiçbir okuma kontrol gerektirmiyor." in texts
    screen._weak_menu.close()
    screen.jump_weak(1)
    assert screen.message.text() == "Zayıf örnek yok: hiçbir okuma kontrol gerektirmiyor."


def test_the_keys_before_a_try_all_say_why_in_the_status_line(qtbot, screen):
    window = screen.window_
    registry = window.registry
    ids = ("sablonlar.sonraki_zayif", "sablonlar.onceki_zayif", "sablonlar.zayif_ornekler")
    for action_id in ids:
        assert registry.is_enabled(action_id)  # on, so the key answers instead of staying silent
        assert registry.action(action_id).toolTip().startswith(NEEDS_TRY)
    window.focus_work_area()
    presses = ((Qt.Key.Key_N, Qt.KeyboardModifier.NoModifier),
               (Qt.Key.Key_N, Qt.KeyboardModifier.ShiftModifier),
               (Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier))
    for key, modifier in presses:
        screen.message.setText("")
        QTest.keyClick(QApplication.focusWidget(), key, modifier)
        assert screen.message.text() == NEEDS_TRY, key
    assert screen.example == 1
    _tried(screen, RESULTS)
    for action_id in ids:
        assert registry.is_enabled(action_id), action_id
        assert not registry.action(action_id).toolTip().startswith(NEEDS_TRY)


def _live_menus(screen):
    return [m for m in screen.findChildren(QMenu) if m.objectName() == "zayifOrnekler"]


def test_the_list_is_deleted_on_close_and_does_not_pile_up(qtbot, screen):
    _tried(screen, RESULTS)
    for _ in range(5):
        screen.show_weak_list()
        QTest.keyClick(screen._weak_menu, Qt.Key.Key_Escape)
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert _live_menus(screen) == []
    screen.show_weak_list()
    screen.show_weak_list()  # a second Ctrl+L replaces the open one
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert len(_live_menus(screen)) == 1
    screen.close_weak_list()


def test_the_open_list_closes_when_the_template_or_job_changes(qtbot, screen):
    _tried(screen, RESULTS)
    screen.show_weak_list()
    menu = screen._weak_menu
    assert menu.isVisible()
    screen.open_template(screen.template.id)
    assert not isValid(menu) or not menu.isVisible()
    _tried(screen, RESULTS)
    screen.show_weak_list()
    menu = screen._weak_menu
    screen.job_id = "another"
    screen._refresh_examples()
    assert not isValid(menu) or not menu.isVisible()
    _tried(screen, RESULTS)
    screen.show_weak_list()
    menu = screen._weak_menu
    screen.window_.tabs.setCurrentIndex(0)
    assert not isValid(menu) or not menu.isVisible()


def test_a_single_example_read_is_not_a_try_all(qtbot, screen):
    screen.example_values = {1: {"a": _weak(0.3)}}  # what a live read of one example leaves
    screen._sync_all()
    tip = screen.window_.registry.action("sablonlar.sonraki_zayif").toolTip()
    assert tip.startswith(NEEDS_TRY)  # still "not tried": the key answers with the status line
    assert screen.weak_examples() == []


def test_the_list_empties_when_the_template_or_job_changes(qtbot, screen):
    _tried(screen, RESULTS)
    assert screen.weak_examples()
    screen.open_template(screen.template.id)
    assert screen.weak_examples() == []
    assert screen.window_.registry.action("sablonlar.zayif_ornekler").toolTip().startswith(
        NEEDS_TRY)
    _tried(screen, RESULTS)
    screen.job_id = "another"
    screen._refresh_examples()
    assert screen.weak_examples() == []


def test_n_and_ctrl_l_work_from_the_keyboard(qtbot, screen):
    window = screen.window_
    _tried(screen, RESULTS)
    window.focus_work_area()
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_N)
    assert screen.example == 3
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_N, Qt.KeyboardModifier.ShiftModifier)
    assert screen.example == 1
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
    assert isinstance(screen._weak_menu, QMenu) and screen._weak_menu.isVisible()
    screen._weak_menu.close()


def test_a_click_on_the_status_item_opens_the_list(qtbot, screen):
    _tried(screen, RESULTS)
    part = screen._status["check"]
    assert part.isVisibleTo(screen.window_)
    QTest.mouseClick(part.label, Qt.MouseButton.LeftButton)
    assert screen._weak_menu.isVisible()
    screen._weak_menu.close()
