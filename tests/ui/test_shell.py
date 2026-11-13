"""The window chrome of direction A: title band, menus on Alt, command bars, shortcuts,
persistence and the custom title bar's hit test."""
from __future__ import annotations

import pytest
from fakes import make_pdf, text_page
from PySide6.QtCore import QPoint, QRect, QSize, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from evrakci import __version__
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions, theme, titlebar
from evrakci.ui.main_window import TAB_IDS, MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.zoomview import ZoomController


def _window(qtbot, tmp_path, show: bool = False) -> MainWindow:
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    if show:
        window.show()
        window.activateWindow()
        assert QTest.qWaitForWindowActive(window)
    return window


def _key(window: MainWindow, key: Qt.Key, mods=Qt.KeyboardModifier.NoModifier) -> None:
    QTest.keyClick(QApplication.focusWidget() or window, key, mods)


@pytest.fixture
def look():
    """Put the global look back after a test changes it."""
    m = theme.manager()
    mode, scale = m.mode(), m.text_scale()
    yield m
    m.set_text_scale(scale)
    m.set_mode(mode)


def test_every_action_has_text_and_a_tooltip_with_its_shortcut(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    for spec in actions.SPECS:
        action = window.registry.action(spec.id)
        assert action.text(), spec.id
        assert action.toolTip(), spec.id
        if spec.shortcuts:
            assert actions.key_text(spec.shortcuts[0]) in action.toolTip(), spec.id


def test_title_band_has_a_s_parts(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    tabs = window.title_tabs
    assert [tabs.tabText(i) for i in range(tabs.count())] == list(actions.TABS.values())
    assert all(not tabs.tabIcon(i).isNull() for i in range(tabs.count()))
    assert window.job_switch.name.text() == "İş açılmadı"
    assert window.search.word.text() == "Ara" and "Ctrl+K" in window.search.keys.text()
    band = theme.manager().title_band()
    assert window.search.width() == band.search_width
    # ≡ sits right of the search; offscreen keeps the system title bar (no caption buttons)
    assert window.menu_button.x() > window.search.x()
    assert window.title_band.caption == {} and window.frame is None


def test_ctrl_digits_switch_tabs(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    for index, key in enumerate((Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, Qt.Key.Key_4,
                                 Qt.Key.Key_5, Qt.Key.Key_6)):
        _key(window, key, Qt.KeyboardModifier.ControlModifier)
        assert window.current_tab() == TAB_IDS[index]
        assert window.title_tabs.currentIndex() == index
        assert window.registry.context == TAB_IDS[index]
        assert window.command_bars.currentWidget() is window.command_bar(TAB_IDS[index])
    window.cycle_tab(1)
    assert window.current_tab() == TAB_IDS[0]


def test_alt_alone_shows_the_menu_row_and_alt_letter_opens_a_menu(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    assert not window.menu_row.isVisible()
    _key(window, Qt.Key.Key_Alt)
    assert window.menu_row.isVisible()
    titles = [a.text() for a in window.menu_row.bar.actions()]
    assert titles == list(actions.MENUS.values())
    window.hide_menu_row()
    assert not window.menu_row.isVisible()
    window.activateWindow()
    _key(window, Qt.Key.Key_E, Qt.KeyboardModifier.AltModifier)  # Düz&en
    assert window.menu_row.isVisible()
    assert window.menu_row.bar.activeAction() is window.menu_row.bar.actions()[1]
    for menu in window.menu_row.menus():
        menu.close()
    window.hide_menu_row()
    assert not window.menu_row.isVisible()


def test_the_menu_button_holds_the_six_menus(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    items = window.menu_button.menu().actions()
    assert [i.text().split("\t")[0] for i in items] == list(actions.MENUS.values())
    assert all("\tAlt+" in i.text() for i in items)
    sub = items[0].menu()
    sub.aboutToShow.emit()
    assert window.registry.action("app.yeni_is") in sub.actions()


def test_ctrl_k_opens_the_palette_and_the_search_does_too(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    _key(window, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
    assert window.command_palette.isVisible()
    assert window.command_palette.parent() is window
    window.command_palette.hide()
    window.search.click()
    assert window.command_palette.isVisible()
    window.command_palette.hide()


def test_ctrl_comma_opens_settings_and_f1_goes_to_rehber(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    _key(window, Qt.Key.Key_Comma, Qt.KeyboardModifier.ControlModifier)
    assert window.settings_dialog is not None and window.settings_dialog.isVisible()
    window.settings_dialog.close()
    window.activateWindow()
    _key(window, Qt.Key.Key_F1)
    assert window.current_tab() == "rehber"
    window.registry.action("app.kisayollar").trigger()
    assert window.shortcut_sheet.isVisible()
    window.shortcut_sheet.close()


def test_about_shows_version_and_licences(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    window.registry.action("app.hakkinda").trigger()
    dialog = window.about_dialog
    assert __version__ in dialog.version.text()
    assert dialog.components.topLevelItemCount() > 0
    dialog.close()


def test_every_tab_has_a_filled_command_bar_and_a_status_slot(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    for tab in TAB_IDS:
        bar = window.command_bar(tab)
        assert len(bar.buttons()) > 2, tab
        for button in bar.buttons():
            assert button.toolTip(), (tab, button.text())
        assert window.status_slot(tab).layout() is not None


def test_geometry_and_last_tab_persist(qtbot, tmp_path):
    first = _window(qtbot, tmp_path, show=True)
    first.resize(1100, 640)  # the offscreen screen is 800 px wide: only the height is kept
    first.show_tab("degerler")
    first.close()
    second = _window(qtbot, tmp_path, show=True)
    assert second.current_tab() == "degerler"
    assert second.height() == 640
    second.showMaximized()
    second.close()
    third = _window(qtbot, tmp_path)
    assert third.windowState() & Qt.WindowState.WindowMaximized


def test_recent_jobs_fill_the_job_switcher(qtbot, tmp_path):
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Mart yazışmaları", [make_pdf(tmp_path / "a.pdf", [text_page()])])
    window = _window(qtbot, tmp_path)
    window.prefs.add_recent_job(job.id)
    assert [j.id for j, _when in window.recent_jobs()] == [job.id]
    window.open_job_switcher()
    texts = [a.text() for a in window.job_menu.actions()]
    assert any(t.startswith("Mart yazışmaları") for t in texts)
    assert "Tüm işler…" in texts
    window.job_menu.close()


def test_opening_a_job_shows_its_name_and_saved_state(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page()])
    with qtbot.waitSignal(window.yukle.job_opened, timeout=20000):
        window.yukle.create_job([pdf], "Nisan")
    assert window.job_switch.name.text() == "Nisan"
    assert window.job_switch.save_state.text().startswith("Kaydedildi ")
    assert window.prefs.recent_jobs()[0] == window.controller().job.id
    window.close_job()
    assert window.job_switch.name.text() == "İş açılmadı"
    assert not window.registry.is_enabled("app.isi_kapat")


def test_theme_and_text_size_switches_restyle(qtbot, tmp_path, look):
    window = _window(qtbot, tmp_path, show=True)
    for mode in ("dark", "hc", "light"):
        look.set_mode(mode)
        QApplication.processEvents()
        assert window.title_band.height() == look.title_band().height
    look.set_text_scale(150)
    QApplication.processEvents()
    tabs = window.title_tabs
    if look.title_band().tab_labels == "selected":
        shown = [i for i in range(tabs.count()) if tabs.tabText(i)]
        assert shown == [tabs.currentIndex()]
    assert all(tabs.accessibleTabName(i) for i in range(tabs.count()))


def test_zoom_keys_reach_the_registered_controller(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    view = QGraphicsView(QGraphicsScene())
    controller = ZoomController(view, None, "deneme")
    window.register_zoom("rehber", controller, "Deneme")
    window.show_tab("yukle")
    assert not window.zoom_slider.isVisible()
    assert not window.registry.is_enabled("app.yakinlastir")
    window.show_tab("rehber")
    assert window.zoom_slider.isVisible() and window.zoom_slider.controller() is controller
    window.title_tabs.setFocus()
    _key(window, Qt.Key.Key_Equal, Qt.KeyboardModifier.ControlModifier)
    assert controller.zoom() == 110
    _key(window, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    _key(window, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    assert controller.zoom() == 90
    _key(window, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
    assert controller.zoom() == 100


def test_f6_moves_between_regions(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    window.show_tab("yukle")
    window.title_tabs.setFocus()
    window.focus_region(1)
    focus = QApplication.focusWidget()
    assert focus is not None and not window.title_band.isAncestorOf(focus)


def test_native_title_bar_pref(tmp_path, monkeypatch):
    monkeypatch.delenv(titlebar.ENV_NATIVE, raising=False)
    prefs = Prefs(tmp_path / "p.ini")
    assert not titlebar.native_title_bar(prefs)
    prefs.set_native_title_bar(True)
    assert titlebar.native_title_bar(prefs)
    assert Prefs(tmp_path / "p.ini").native_title_bar()
    assert not titlebar.use_custom_frame(prefs)
    monkeypatch.setenv(titlebar.ENV_NATIVE, "1")
    assert titlebar.native_title_bar(None)


def test_hit_test_answers_like_windows():
    size, border, band = QSize(1000, 700), 6, 44
    button = QRect(908, 0, 46, 32)

    def hit(x, y, maximized=False, drag=True):
        return titlebar.hit_test(size, QPoint(x, y), border, band, maximized, button, drag)

    assert hit(2, 2) == titlebar.HTTOPLEFT
    assert hit(998, 698) == titlebar.HTBOTTOMRIGHT
    assert hit(500, 1) == titlebar.HTTOP
    assert hit(2, 300) == titlebar.HTLEFT
    assert hit(920, 10) == titlebar.HTMAXBUTTON
    assert hit(500, 20) == titlebar.HTCAPTION
    assert hit(500, 20, drag=False) == titlebar.HTCLIENT
    assert hit(500, 300) == titlebar.HTCLIENT
    assert hit(500, 1, maximized=True) == titlebar.HTCAPTION


LONG_NAME = "Kasım 2026 – Faaliyet belgeleri, Ankara Sanayi Odası arşivi ikinci"  # 60+ chars


def _band(width: int):
    from PySide6.QtWidgets import QToolButton

    from evrakci.ui import fonts
    from evrakci.ui.chrome import JobSwitch, SearchBox, TitleTabs

    fonts.register_fonts()  # Inter, as in the app: the widths below depend on it
    QApplication.instance().setFont(theme.manager().font("body"))
    tabs = TitleTabs([(t, actions.TABS[t]) for t in TAB_IDS])
    switch, search, menu = JobSwitch(), SearchBox(), QToolButton()
    switch.set_job(LONG_NAME)
    switch.save_state.set_saved(__import__("datetime").datetime.now())
    band = titlebar.TitleBand(tabs, switch, search, menu, caption=True)
    band.resize(width, band.height())
    band.show()
    for part in (tabs, switch, search, band):  # as MainWindow._restyle does after polish
        part.refresh()
    for _ in range(3):
        QApplication.processEvents()
        band.layout().activate()
    return band


@pytest.mark.parametrize("text", [100, 130, 150])
def test_title_band_fits_1366_with_caption_buttons_and_a_long_name(qapp, look, text):
    look.set_text_scale(text)
    band = _band(1366)
    try:
        parts = [band.logo, band.tabs, band.job_switch, band.search, band.menu,
                 *band.caption.values()]
        boxes = [w.geometry() for w in parts]
        assert all(box.right() < 1366 and box.left() >= 0 for box in boxes)
        for a, b in zip(boxes, boxes[1:], strict=False):
            assert a.right() < b.left(), (a, b)
        tabs = band.tabs
        assert tabs.width() >= tabs.sizeHint().width()  # every tab is shown whole
        for i in range(tabs.count()):
            assert tabs.tabRect(i).right() < tabs.width()
        name = band.job_switch.name
        assert name.full_text() == LONG_NAME
        shown = name.fontMetrics().horizontalAdvance(name.displayed_text())
        assert shown <= name.contentsRect().width()  # elided to the space left, never cut
        assert name.is_elided() or tabs.label_mode() == "selected"
        assert tabs.label_mode() == ("all" if text == 100 else "selected")
        assert band.minimumSizeHint().width() <= 1366  # never widens the window
        assert LONG_NAME in band.job_switch.accessibleName()
        assert LONG_NAME in band.job_switch.toolTip()
    finally:
        band.close()
        band.deleteLater()


def test_command_label_sits_two_gaps_after_its_icon(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    m = theme.manager()
    button = next(b for b in window.command_bar("kontrol").buttons()
                  if getattr(b, "labelled", lambda: False)())
    assert button.text() == "Kes"
    start = m.size("icon-md") + 2 * m.size("s2")
    assert button.text_rect().left() == start
    text_w = button.fontMetrics().horizontalAdvance("Kes")
    assert button.width() >= start + text_w + m.size("s3") - 2
    from PySide6.QtGui import QImage

    button.setEnabled(True)
    image = QImage(button.size(), QImage.Format.Format_RGB32)
    image.fill(m.color("layer"))
    button.render(image)
    background = m.color("layer").lightness()

    def inked(x: int) -> bool:
        return any(background - image.pixelColor(x, y).lightness() > 60
                   for y in range(image.height()))

    gap = range(m.size("s2") + m.size("icon-md") + 1, start - 1)
    assert not any(inked(x) for x in gap)  # nothing between the icon and the label
    assert any(inked(x) for x in range(m.size("s2"), m.size("s2") + m.size("icon-md")))
    assert any(inked(x) for x in range(start, start + 8))


def test_command_bars_follow_a(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    for tab in TAB_IDS:
        buttons = window.command_bar(tab).buttons()
        assert buttons[-1].objectName() == "moreButton"
        assert buttons[-2].action_.objectName() == "app.yan_panel", tab
    names = [b.action_.objectName() for b in window.command_bar("degerler").buttons()[:-1]]
    assert names[2:4] == ["degerler.oku", "degerler.eksikleri_oku"]
    read = window.command_bar("degerler").buttons()[2]
    assert read.text() == "Değerleri oku" and read.icon_name == "scan-text"
    assert not window.degerler.read_button.isVisibleTo(window.degerler)
    kontrol = [b.action_.objectName() for b in window.command_bar("kontrol").buttons()[:-1]]
    assert kontrol[-2:] == ["kontrol.onizle", "app.yan_panel"]


def test_f9_hides_and_shows_the_side_panel(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=True)
    window.show_tab("degerler")
    action = window.registry.action("app.yan_panel")
    assert action.isEnabled() and action.toolTip() == "Kaynak panelini gizle (F9)"
    window.title_tabs.setFocus()
    _key(window, Qt.Key.Key_F9)
    assert window.degerler.side.isHidden()
    assert action.toolTip() == "Kaynak panelini göster (F9)"
    _key(window, Qt.Key.Key_F9)
    assert not window.degerler.side.isHidden()
    window.show_tab("kontrol")  # no job open: nothing to hide
    assert not action.isEnabled()
    assert action.toolTip() == "Ayrıntı panelini gizle (F9)"


def test_theme_switch_restyles_the_screens_token_sheets(qtbot, tmp_path, look):
    from evrakci.ui.tokens import generated as g

    window = _window(qtbot, tmp_path, show=True)
    look.set_mode("light")
    # Değerler's table sits in a card (A): its token sheet uses `card`, not the old `base`
    assert g.COLORS["light"]["card"] in window.degerler.table.styleSheet()
    look.set_mode("hc")
    QApplication.processEvents()
    for sheet in (window.degerler.table.styleSheet(), window.disa_aktar.results.styleSheet()):
        assert f"QHeaderView::section {{ background: {look.hex('base')};" in sheet
        assert g.COLORS["light"]["base"] not in sheet
    assert look.hex("base") in (g.SYSTEM_COLORS["sys-window"],
                                theme._windows_system_colours().get("sys-window"))


def test_each_job_is_wired_once_and_the_old_one_let_go(qtbot, tmp_path):
    from PySide6.QtGui import QUndoCommand

    window = _window(qtbot, tmp_path)
    store = window.store
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page()])
    first, second = store.create_job("Bir", [pdf]), store.create_job("İki", [pdf])
    window.yukle.open_job(store.load(first.id))
    old = window.controller()
    window.yukle.open_job(store.load(second.id))
    new = window.controller()
    assert new is not old
    window.message.setText("")
    old.status.emit("eski iş")
    assert window.message.text() == ""
    new.status.emit("yeni iş")
    assert window.message.text() == "yeni iş"
    window.show_tab("kontrol")
    new.undo_stack.push(QUndoCommand("Kesim ekle"))
    assert window.registry.is_enabled("app.geri_al")
    assert "Kesim ekle" in window.registry.action("app.geri_al").toolTip()


def test_an_old_save_shows_its_date(qtbot, tmp_path):
    import os
    import time

    store = JobStore(tmp_path / "jobs")
    job = store.create_job("Eylül", [make_pdf(tmp_path / "a.pdf", [text_page()])])
    stamp = time.time() - 3 * 86400
    os.utime(store._job_file(job.id), (stamp, stamp))
    window = _window(qtbot, tmp_path)
    window.yukle.open_job(store.load(job.id))
    words = window.job_switch.save_state.text().split()
    assert words[0] == "Kaydedildi" and len(words) >= 4  # "Kaydedildi 10 Kas 14:32"
