"""Q6 (Q-16 measured fails, toast position, title-band focus ring). The window is the demo
job of tools/screenshots.py; sizes are the ones tools/ui_measure.py checks."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QScrollArea, QToolButton

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import screenshots  # noqa: E402

from evrakci.ui import style, theme  # noqa: E402
from evrakci.ui.main_window import TAB_IDS, MainWindow  # noqa: E402
from evrakci.ui.widgets import add_clear_button  # noqa: E402


@pytest.fixture
def demo(qtbot, tmp_path) -> MainWindow:
    app = QApplication.instance()
    style.install(app)
    app.setStyleSheet(theme.manager().stylesheet())
    window = screenshots.build(tmp_path / "demo")
    qtbot.addWidget(window)
    window.resize(1366, 768)
    window.show()
    window.activateWindow()
    qtbot.waitUntil(window.isActiveWindow, timeout=3000)
    yield window
    app.setStyleSheet("")


def _settle(rounds: int = 5) -> None:
    for _ in range(rounds):
        QApplication.processEvents()


def _control_h() -> int:
    return theme.manager().size("control-h")


def test_search_field_icon_buttons_are_a_full_height_click_area(demo):
    for tab, field in (("rehber", demo.rehber.search), ("degerler", demo.degerler.search)):
        demo.show_tab(tab)
        _settle()
        field.setText("x")
        _settle()
        buttons = [b for b in field.findChildren(QToolButton) if b.isVisible()]
        assert buttons, field
        for button in buttons:
            assert button.width() >= 24 and button.height() >= _control_h()
            # centred in the field, not hanging below it
            assert abs(button.y() - (field.height() - button.height()) // 2) <= 1
            assert button.toolTip(), field
        field.clear()


def test_clear_button_is_named_temizle_and_clears(demo):
    demo.show_tab("degerler")
    _settle()
    clear = demo.degerler.search._clear_button.button
    assert clear.toolTip() == "Temizle"
    demo.degerler.search.setText("abc")
    _settle()
    assert clear.isVisible() and clear.height() >= _control_h()
    clear.click()
    assert demo.degerler.search.text() == ""
    field = QLineEdit()
    add_clear_button(field)
    assert field._clear_button.button.height() >= _control_h()


def test_word_role_lifts_quiet_and_green_words_to_the_text_tier():
    assert theme.word_role("ok") == "text" and theme.word_role("text-2") == "text"
    for role in ("check-text", "danger", "accent"):
        assert theme.word_role(role) == role


def _ratio(a: str, b: str) -> float:
    def lum(value: str) -> float:
        lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
               for c in (int(value[i:i + 2], 16) / 255 for i in (1, 3, 5))]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_status_words_read_at_7_to_1(mode):
    manager = theme.manager()
    before = manager.mode()
    try:
        manager.set_mode(mode)
        for bg in ("card", "selected"):
            ratio = _ratio(manager.hex(theme.word_role("ok")), manager.hex(bg))
            assert ratio >= 7.0, (mode, bg, ratio)
    finally:
        manager.set_mode(before)


def test_degerler_side_scroll_takes_no_focus(demo):
    scrolls = [w for w in demo.degerler.findChildren(QScrollArea)
               if type(w).__name__ == "_Scroll"]
    assert scrolls
    assert all(w.focusPolicy() == Qt.FocusPolicy.NoFocus for w in scrolls)


@pytest.mark.parametrize("scale", [100, 150])
@pytest.mark.parametrize("tab", TAB_IDS)
def test_toast_is_at_the_bottom_left_above_the_status_bar(demo, tab, scale):
    manager = theme.manager()
    try:
        manager.set_text_scale(scale)
        demo.show_tab(tab)
        _settle()
        demo.toaster.show("Merhaba", "Geri al", lambda: None, timeout_ms=0)
        toast = demo.toaster._current
        frame = toast.frame.geometry().translated(toast.pos())
        assert frame.left() <= 16 and frame.left() >= 0
        assert frame.right() < demo.width() // 2 + frame.width()
        assert frame.bottom() <= demo.height() - demo.statusBar().height()
        # the main button at the bottom right of the window is never under the toast
        right_edge = demo.width() - 24 - 120
        assert frame.right() < right_edge or frame.width() > demo.width() // 2
        demo.toaster.dismiss()
    finally:
        manager.set_text_scale(100)


def test_a_fresh_window_does_not_start_on_the_title_tabs(demo):
    assert QApplication.focusWidget() is not demo.title_tabs


def test_title_tabs_show_the_focus_ring_when_tabbed_to(demo):
    ring = style.focus_ring()
    assert ring is not None
    demo.title_tabs.clearFocus()
    _settle()
    demo.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
    _settle()
    overlay = ring.overlay
    assert overlay is not None and overlay.isVisible()
    assert overlay.target() is demo.title_tabs
    assert (overlay.width() - demo.title_tabs.width()) // 2 >= 3


def test_pending_count_ellipsis_is_drawn_strong(demo):
    from evrakci.ui.yukle_side import KvRow

    row = demo.yukle.findChildren(KvRow)[0]
    row.set("…", state="num")
    assert row.value.property("state") == "pending"
    assert "QLabel[state=\"pending\"] { font-weight: 600; }" in theme.manager().stylesheet()
    row.set("3", state="num")
    assert row.value.property("state") == "num"


def test_inspector_captions_in_cards_use_the_text_colour(demo):
    from evrakci.ui.degerler_side import ReadingItem, ReadingRow

    row = ReadingRow(ReadingItem("A", "metin", (), 90, False))
    assert row.name.property("kind") == "inspector-value"
    from evrakci.ui.degerler_side import ValueCard
    from evrakci.ui.sablon_inspector import _label

    assert ValueCard().read_label.property("kind") == "inspector-value"
    assert _label("Ad").property("kind") == "inspector-value"
    assert _label("Kutu", "group-label").property("kind") == "group-label"


def test_status_bar_labels_use_the_text_colour():
    sheet = theme.manager().stylesheet()
    assert "QStatusBar#statusBar QLabel { color: " + theme.manager().hex("text") in sheet
