"""Phase 4 review fixes: keyboard order and traps, focus ring, Space/Enter on buttons,
single-character keys, action ownership, visual details. The window is the demo job of
tools/screenshots.py (three documents with a template and values, one needing a check)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractButton, QApplication, QSplitter

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import screenshots  # noqa: E402

from evrakci.ui.main_window import TAB_IDS, MainWindow  # noqa: E402


@pytest.fixture
def demo(qtbot, tmp_path) -> MainWindow:
    window = screenshots.build(tmp_path / "demo")
    qtbot.addWidget(window)
    window.resize(1366, 768)
    window.show()
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window)
    return window


def _settle(rounds: int = 5) -> None:
    for _ in range(rounds):
        QApplication.processEvents()


def _press(key, mods=Qt.KeyboardModifier.NoModifier) -> None:
    QTest.keyClick(QApplication.focusWidget(), key, mods)
    _settle(2)


@pytest.mark.parametrize("tab", TAB_IDS)
def test_tab_walks_every_region_in_reading_order_and_comes_back(demo, tab):
    demo.show_tab(tab)
    _settle()
    demo.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
    bar, area, status = demo.command_bars.currentWidget(), demo.tabs.currentWidget(), \
        demo.statusBar()
    seen = []
    for _ in range(80):
        _press(Qt.Key.Key_Tab)
        focus = QApplication.focusWidget()
        if focus is demo.title_tabs:
            break
        seen.append(next(i for i, r in enumerate((demo.title_band, bar, area, status))
                         if r.isAncestorOf(focus)))
    else:
        pytest.fail("Tab never came back to the tabs")
    assert 2 in seen, "Tab never reached the work area"
    assert seen == sorted(seen), "regions out of reading order"
    if any(isinstance(w, QAbstractButton) and w.isVisible() for w in bar.findChildren(
            QAbstractButton)):
        assert 1 in seen


@pytest.mark.parametrize("tab", TAB_IDS)
def test_focus_ring_never_becomes_a_splitter_pane(demo, tab):
    demo.show_tab(tab)
    _settle()
    counts = {id(s): s.count() for s in demo.findChildren(QSplitter)}
    demo.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
    for _ in range(60):
        _press(Qt.Key.Key_Tab)
        assert {id(s): s.count() for s in demo.findChildren(QSplitter)} == counts
        if QApplication.focusWidget() is demo.title_tabs:
            break
    for _ in range(4):
        _press(Qt.Key.Key_F6)
        assert {id(s): s.count() for s in demo.findChildren(QSplitter)} == counts


def test_ctrl_digit_moves_focus_into_the_tabs_main_view(demo):
    from PySide6.QtWidgets import QAbstractScrollArea

    for index, tab in enumerate(TAB_IDS):
        demo.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
        _press(Qt.Key(Qt.Key.Key_1.value + index), Qt.KeyboardModifier.ControlModifier)
        assert demo.current_tab() == tab
        focus = QApplication.focusWidget()
        assert demo.tabs.currentWidget().isAncestorOf(focus), tab
        assert isinstance(focus, QAbstractScrollArea) or tab == "yukle" and focus, tab


@pytest.mark.parametrize("tab", ["kontrol", "degerler"])
def test_space_and_enter_on_a_focused_button_press_that_button_only(demo, tab):
    demo.show_tab(tab)
    _settle()
    registry = demo.registry
    watched = [a for a in ("kontrol.onayla", "kontrol.onizle", "degerler.onayla",
                           "degerler.tum_sayfa") if a.startswith(tab)]
    fired = []
    for action_id in watched:
        registry.action(action_id).triggered.connect(lambda *_a, i=action_id: fired.append(i))
    buttons = [b for b in demo.tabs.currentWidget().findChildren(QAbstractButton)
               if b.isVisible() and b.isEnabled()
               and b.focusPolicy() & Qt.FocusPolicy.TabFocus]
    buttons += [b for b in demo.command_bars.currentWidget().findChildren(QAbstractButton)
                if b.isVisible() and b.isEnabled() and b.focusPolicy() & Qt.FocusPolicy.TabFocus]
    assert buttons
    for button in buttons:
        button.setFocus(Qt.FocusReason.TabFocusReason)
        _settle(2)
        assert QApplication.focusWidget() is button
        for action_id in watched:
            assert all(not actions_key_is(registry, action_id, k)
                       for k in ("Space", "Return", "Enter"))
    # A real press on a harmless button: the button runs, the window's Enter does not.
    bar_button = demo.command_bars.currentWidget().findChildren(QAbstractButton)
    target = next(b for b in bar_button if "Sonraki kontrol" in b.toolTip() and b.isEnabled())
    clicks = []
    target.clicked.connect(lambda *_a: clicks.append(1))
    target.setFocus(Qt.FocusReason.TabFocusReason)
    _press(Qt.Key.Key_Space)
    assert clicks == [1]
    assert fired == []


def actions_key_is(registry, action_id, name):
    return name in registry.live_keys(action_id)


def test_character_keys_can_be_switched_off(demo):
    demo.show_tab("kontrol")
    _settle()
    demo.kontrol.timeline.setFocus()
    assert "K" in demo.registry.live_keys("kontrol.kes")
    demo.open_settings()
    dialog = demo.settings_dialog
    dialog.character_keys.setChecked(False)
    assert demo.registry.live_keys("kontrol.kes") == []
    assert "Return" in demo.registry.live_keys("kontrol.onayla")
    assert demo.prefs.flag("tek_tuslu_kisayollar", True) is False
    dialog.character_keys.setChecked(True)
    assert "K" in demo.registry.live_keys("kontrol.kes")


def test_settings_and_sheet_give_focus_back(demo):
    demo.show_tab("kontrol")
    _settle()
    timeline = demo.kontrol.timeline
    timeline.setFocus(Qt.FocusReason.TabFocusReason)
    demo.open_settings()
    _settle()
    demo.settings_dialog.reject()
    _settle()
    assert QApplication.focusWidget() is timeline
    demo.open_shortcut_sheet()
    _settle()
    demo.shortcut_sheet.reject()
    _settle()
    assert QApplication.focusWidget() is timeline


# -- Ctrl+S, Ctrl+E and Ctrl+F: one owner per action, a route on every tab --------------------
def test_kaydet_belongs_to_the_tab_and_a_template_sync_elsewhere_does_not_enable_it(demo):
    demo.show_tab("rehber")
    _settle()
    assert not demo.registry.is_enabled("app.kaydet")  # nothing to save on Rehber
    demo.sablon._sync_actions()  # a background Şablonlar sync while on another tab
    assert not demo.registry.is_enabled("app.kaydet")
    demo.show_tab("kontrol")
    _settle()
    assert demo.registry.is_enabled("app.kaydet")
    demo.registry.action("app.kaydet").trigger()
    assert demo.toaster.current_text().startswith("İş kaydedildi")


def test_export_action_has_one_owner(demo):
    demo.show_tab("disa_aktar")
    _settle()
    screen = demo.disa_aktar
    screen.can_export = lambda: False  # e.g. blocked
    demo.controller().job_changed.emit()  # the window's own job sync runs too
    _settle()
    demo._sync_job_actions()
    assert not demo.registry.is_enabled("app.disa_aktar")
    demo.show_tab("kontrol")
    _settle()
    assert demo.registry.is_enabled("app.disa_aktar")  # elsewhere: Ctrl+E goes to the tab


@pytest.mark.parametrize("tab", TAB_IDS)
def test_ctrl_f_answers_on_every_tab(demo, tab):
    demo.show_tab(tab)
    _settle()
    assert demo.registry.is_enabled("app.bul"), tab


def test_undo_history_is_listed_by_name_and_steps_back(demo):
    demo.show_tab("kontrol")
    _settle()
    history = demo.undo_history()
    assert history and history[-1][1] == "Şablon uygula" and history[-1][2]
    menu = demo._history_menu(demo.app_menu)
    names = [a.text() for a in menu.actions()]
    assert names[0].startswith("Başlangıç") and "Şablon uygula" in names[1]
    demo._undo_to(0)
    assert not demo.undo_history()[-1][2]  # undone, still listed for Yinele
    demo.redo()
    assert demo.undo_history()[-1][2]


# -- remembered choices (QOL 10) -----------------------------------------------------------------
def test_degerler_view_template_and_snap_are_remembered(demo):
    demo.show_tab("degerler")
    _settle()
    demo.degerler.set_view("kontrol")
    assert demo.prefs.view_state("degerler.gorunum") == "kontrol"
    demo.sablon.set_snap(not demo.sablon.is_snapping())
    assert demo.prefs.flag("sablonlar.izgara", None) == demo.sablon.is_snapping()


def test_the_last_export_folder_is_offered_without_touching_the_default(demo, tmp_path):
    demo.prefs.set_last_export_folder(tmp_path / "son")
    screen = demo.disa_aktar
    screen.folder.setText("")
    screen._folder_touched = False
    screen._prefill_folder(demo.controller())
    assert screen.folder.text() == str(tmp_path / "son")
    assert demo.prefs.export_folder() == ""


# -- Değerler ------------------------------------------------------------------------------------
def test_hc_selected_row_draws_the_uncertain_character_readable():
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPainter

    from evrakci.ui import theme
    from evrakci.ui.degerler_table import paint_marked

    manager = theme.manager()
    old = manager.mode()
    try:
        for mode in ("light", "dark", "hc"):
            manager.set_mode(mode)
            for on_highlight in (False, True):
                ink = manager.color("sys-highlight-text" if mode == "hc" and on_highlight
                                    else "text")
                ground = manager.color("sys-highlight" if mode == "hc" and on_highlight
                                       else "card")
                image = QImage(200, 40, QImage.Format.Format_RGB32)
                image.fill(ground)
                painter = QPainter(image)
                font = manager.font("value")
                paint_marked(painter, QRectF(0, 0, 200, 40), "48Z13", font, ink, (2,),
                             on_highlight=on_highlight)
                painter.end()
                # the marked character's middle is not one solid block of ink
                from PySide6.QtGui import QFontMetricsF
                metrics = QFontMetricsF(font)
                left = metrics.horizontalAdvance("48")
                right = metrics.horizontalAdvance("48Z")
                inks = sum(1 for x in range(int(left) + 1, int(right) - 1)
                           for y in range(14, 26) if QColor(image.pixel(x, y)) == ink)
                area = (int(right) - int(left) - 2) * 12
                assert inks < area * 0.7, (mode, on_highlight)
                if mode != "hc" and not on_highlight:  # the wash keeps body text contrast
                    from test_theme import _contrast
                    assert _contrast(manager.hex("text"), manager.hex("check-wash")) >= 7
    finally:
        manager.set_mode(old)


def test_accepted_values_carry_no_rescored_percentage_and_enter_goes_on(demo):
    demo.show_tab("degerler")
    _settle()
    screen = demo.degerler
    screen.set_view("tumu")
    _settle()
    assert screen.select_value(2, next(c.key for c in screen.rows[1].cells
                                          if c.needs_check))
    told = []
    screen._say = told.append
    screen.accept_current()
    cell = next(c for c in screen.rows[1].cells if c.reviewed)
    assert cell.percent is None
    assert told and told[-1].startswith("Kontrol gereken değer kalmadı;")
    assert screen.table.currentIndex().isValid()


def test_guven_stays_in_view_at_150_percent(qtbot, tmp_path):
    from evrakci.ui import theme

    manager = theme.manager()
    manager.set_text_scale(150)
    try:
        window = screenshots.build(tmp_path / "w")
        qtbot.addWidget(window)
        window.resize(1366, 768)
        window.show()
        window.show_tab("degerler")
        _settle(10)
        table = window.degerler.table
        last = table.model().columnCount() - 1
        header = table.horizontalHeader()
        assert header.sectionViewportPosition(last) + header.sectionSize(last) \
            <= table.viewport().width() + 1
        window.show_tab("disa_aktar")
        _settle(10)
        assert screenshots._cells(window.disa_aktar.results, "x") == []
    finally:
        manager.set_text_scale(100)


_TAB_CHECK = """
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import screenshots as s
from PySide6.QtWidgets import QApplication
from evrakci.app import configure_application
from evrakci.ui import theme
s.force_custom_frame()
app = QApplication([])
configure_application(app)
theme.manager().set_text_scale(int(sys.argv[2]))
theme.manager().set_mode("light")
s._settle(app)
with tempfile.TemporaryDirectory() as tmp:
    window = s.build(Path(tmp) / "w")
    window.resize(1366, 768)
    window.show()
    report = []
    for index, slug in enumerate(s.SLUGS):
        window.tabs.setCurrentIndex(index)  # as Ctrl+number does, not through the strip
        s._settle(app, window=window)
        report.append({"slug": slug, "clipped": s.clipping(window, slug),
                       "selected_shown": window.title_tabs.isTabVisible(index),
                       "overflow": window.title_band.overflow.isVisible(),
                       "name_elided": window.job_switch.name.is_elided()})
    window.close()
print(json.dumps(report))
"""


def _tab_report(text: int) -> list[dict]:
    """Every tab of the demo window at 1366x768 in light, with the app's real look (Inter,
    stylesheet) and A's title band with caption buttons, exactly as the screenshot matrix
    builds it; in a child process so the look never leaks into other tests."""
    import json
    import os
    import subprocess

    tools = str(Path(__file__).resolve().parents[2] / "tools")
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    done = subprocess.run([sys.executable, "-c", _TAB_CHECK, tools, str(text)], env=env,
                          capture_output=True, text=True, timeout=300, check=True)
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_no_tab_clips_at_1366x768_100_percent():
    """GOAL §3.3: nothing clipped, elided or overlapping on any tab at the default size,
    the full job name in the title band included (A's kontrol-light.png)."""
    report = _tab_report(100)
    assert [r["slug"] for r in report] == screenshots.SLUGS
    for tab in report:
        assert tab["clipped"] == [], tab["slug"]
        assert not tab["name_elided"] and not tab["overflow"], tab["slug"]


def test_title_band_at_150_percent_keeps_selected_tab_and_full_job_name():
    """Option b at 1366 px and 150 %: the tabs overflow into "»" before the job name gives
    way, the selected tab is in the strip however it was chosen, and nothing clips."""
    for tab in _tab_report(150):
        assert tab["selected_shown"] and tab["overflow"], tab["slug"]
        assert not tab["name_elided"], tab["slug"]
        assert tab["clipped"] == [], tab["slug"]


@pytest.mark.parametrize("policy, clipped", [
    (Qt.ScrollBarPolicy.ScrollBarAsNeeded, False),  # the bar shows: scrolled, not clipped
    (Qt.ScrollBarPolicy.ScrollBarAlwaysOff, True),  # no bar: the cut card is clipped
])
def test_card_at_a_scroll_edge_is_clipped_only_without_a_scroll_bar(qtbot, policy, clipped):
    from PySide6.QtWidgets import QFrame, QScrollArea, QVBoxLayout, QWidget

    area = QScrollArea()
    qtbot.addWidget(area)
    area.setVerticalScrollBarPolicy(policy)
    area.setWidgetResizable(True)
    content = QWidget()
    column = QVBoxLayout(content)
    cards = []
    for _ in range(4):
        card = QFrame()
        card.setProperty("kind", "card")
        card.setFixedHeight(90)
        column.addWidget(card)
        cards.append(card)
    area.setWidget(content)
    area.resize(300, 170)  # the second card is cut by the bottom edge
    area.show()
    _settle()
    assert any(screenshots._cut_by_scroll_edge(c) for c in cards) is clipped
    area.verticalScrollBar().setEnabled(False)  # a disabled bar does not say "more" either
    assert any(screenshots._cut_by_scroll_edge(c) for c in cards)


def test_long_company_name_wraps_and_its_row_grows_at_150_percent(qtbot, tmp_path):
    """A's 150 % Değerler: a company name too long for its column wraps onto a second line
    in a taller row instead of eliding; short names keep A's row height."""
    from evrakci.ui import theme

    manager = theme.manager()
    manager.set_text_scale(150)
    try:
        window = screenshots.build(tmp_path / "w")
        qtbot.addWidget(window)
        window.resize(1366, 768)
        window.show()
        window.show_tab("degerler")
        screenshots._settle(QApplication.instance(), window=window)  # thumbnails done too
        table = window.degerler.table
        model = table.model()
        column = next(c for c, col in enumerate(model.columns) if col.title == "Firma Adi")
        texts = [model.data(model.index(r, column)) for r in range(model.rowCount())]
        long_row = texts.index("Akçay Tekstil San. ve Tic. Ltd. Şti.")
        row_h = manager.size("row-h")
        assert table.rowHeight(long_row) > row_h
        assert all(table.rowHeight(r) == row_h for r in range(model.rowCount()) if r != long_row)
        assert screenshots._cells(table, "x") == []
    finally:
        manager.set_text_scale(100)


# -- Kontrol -------------------------------------------------------------------------------------
def test_overview_draws_small_left_aligned_squares_for_a_short_job(demo):
    from evrakci.ui.kontrol_overview import SEG_MAX

    demo.show_tab("kontrol")
    _settle()
    strip = demo.kontrol.strip
    track = strip.track_rect()
    first, last = strip._segment(1, track), strip._segment(strip.documents, track)
    assert first.width() == SEG_MAX and first.left() == track.left()
    assert last.right() < track.left() + 40  # three documents: about 28 px, not the strip


def test_overview_label_follows_the_last_segment(demo):
    from evrakci.ui import theme

    demo.show_tab("kontrol")
    _settle()
    strip = demo.kontrol.strip
    last = strip._segment(strip.documents, strip.track_rect())
    gap = theme.manager().size("s4")
    assert strip.where_x() == last.right() + gap  # A: the label sits s4 after the track's end


def test_selection_card_counts_only_pages_drawn_selected(demo):
    demo.show_tab("kontrol")
    _settle()
    screen = demo.kontrol
    assert not screen.timeline.selectionModel().selectedIndexes()
    assert screen.side.selection_group.isHidden()  # the current page alone is no selection


def test_placeholder_has_no_form_shapes():
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QColor, QImage, QPainter

    from evrakci.ui import theme
    from evrakci.ui.kontrol_paint import paint_placeholder

    image = QImage(148, 210, QImage.Format.Format_RGB32)
    image.fill(theme.manager().color("paper"))
    painter = QPainter(image)
    paint_placeholder(painter, QRectF(0, 0, 148, 210), 1)
    painter.end()
    line = theme.manager().color("paper-line")
    assert not any(QColor(image.pixel(x, 120)) == line for x in range(148))


# -- Şablonlar -------------------------------------------------------------------------------------
def test_a_variable_without_a_box_is_not_a_false_kontrol():
    from evrakci.pipeline.templates.values import VariableValue
    from evrakci.ui import sablon_read

    nothing = VariableValue("", 0.0, None, True)
    assert sablon_read.shown_for(nothing, None, 0.9).level == "okunmadi"
    assert sablon_read.flagged_count({"k": nothing}) == 0


def test_a_box_can_be_drawn_and_resized_from_the_keyboard(demo):
    demo.show_tab("sablonlar")
    _settle()
    screen = demo.sablon
    canvas = screen.canvas
    screen.select_variable(screen.template.variables[0].name)
    before = len(screen.template.variables[0].sections)
    screen.set_drawing(True)
    canvas.setFocus(Qt.FocusReason.TabFocusReason)
    QTest.keyClick(canvas, Qt.Key.Key_Return)
    _settle()
    sections = screen.template.variables[0].sections
    assert len(sections) == before + 1
    x0, y0, x1, y1 = sections[-1].box_mm
    assert round(x1 - x0) == 40 and round(y1 - y0) == 10
    screen.set_drawing(False)
    screen.select_section(screen.template.variables[0].name, len(sections) - 1)
    canvas.setFocus(Qt.FocusReason.TabFocusReason)
    QTest.keyClick(canvas, Qt.Key.Key_Right, Qt.KeyboardModifier.ControlModifier
                   | Qt.KeyboardModifier.ShiftModifier)
    _settle()
    x0, y0, x1, y1 = screen.template.variables[0].sections[-1].box_mm
    assert round(x1 - x0, 2) == 41.0


# -- Yükle, Rehber, chrome -------------------------------------------------------------------------
def test_tables_and_the_guide_do_not_trap_tab(demo):
    assert not demo.yukle.table.tabKeyNavigation()
    assert demo.rehber.text.tabChangesFocus()


def test_targets_are_at_least_24_px(demo):
    from PySide6.QtWidgets import QSlider

    from evrakci.ui import theme

    for tab in TAB_IDS:
        demo.show_tab(tab)
        _settle()
        for widget in demo.findChildren(QSlider):
            if widget.isVisible():
                assert max(widget.sizeHint().height(), widget.minimumHeight()) >= 24, tab
    sheet = theme.manager().stylesheet()  # the app's sheet (tests run without it applied)
    assert "QCheckBox, QRadioButton { spacing:" in sheet and "min-height: 24px" in sheet
    clear = demo.degerler.search._clear_button.button
    assert clear.width() >= 24 and clear.height() >= 24


def test_inline_icons_grow_with_the_text_size():
    from evrakci.ui import theme

    manager = theme.manager()
    assert manager.inline_icon() == 14
    manager.set_text_scale(150)
    try:
        assert manager.inline_icon() == 20 and manager.inline_icon(16) == 24
    finally:
        manager.set_text_scale(100)


def test_zoom_is_watched_once_per_controller(demo):
    from evrakci.ui.zoomview import ZoomController

    controller = ZoomController(demo.rehber, None, "deneme")
    for _ in range(5):
        demo.register_zoom("rehber", controller)
    assert sum(1 for key in demo._zoom_watched if key[1] == id(controller)) == 1


def test_separator_pdf_falls_back_when_the_usual_file_is_held(demo, monkeypatch, tmp_path):
    from evrakci.ui import rehber

    monkeypatch.setattr(rehber, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(rehber.QDesktopServices, "openUrl", lambda _url: True)
    real = demo.rehber.write_separators

    def held(path, sheets):
        if path.name == "ayirac-sayfalari.pdf":
            raise PermissionError(13, "Erişim engellendi")
        return real(path, sheets)

    monkeypatch.setattr(demo.rehber, "write_separators", held)
    path = demo.rehber.open_separators()
    assert path is not None and path.name == "ayirac-sayfalari-2.pdf" and path.exists()


def test_invalid_characters_box_is_live_and_stays_on(demo):
    box = demo.disa_aktar.side.chars_box
    assert box.isEnabled() and box.isChecked()
    box.setChecked(False)
    assert box.isChecked()
