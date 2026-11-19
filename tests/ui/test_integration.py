"""The window as one app after the Phase 3 tab rebuilds: one visible undo history, context
menus, zoom on every zoomable view, and every QAction named, keyed and unique per tab."""

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMenu

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions, motion
from evrakci.ui.main_window import TAB_IDS, MainWindow
from evrakci.ui.prefs import Prefs


@pytest.fixture(autouse=True)
def _instant():
    motion.set_reduced_motion_override(True)
    yield
    motion.set_reduced_motion_override(None)


@pytest.fixture
def window(qtbot, tmp_path):
    win = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                     settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(win)
    win.resize(1366, 768)
    win.show()
    win.activateWindow()
    assert QTest.qWaitForWindowActive(win)
    a = make_pdf(tmp_path / "a.pdf", [text_page("A"), qr_page(), text_page("B"), text_page()])
    b = make_pdf(tmp_path / "b.pdf", [text_page("C"), text_page()])
    job = win.store.create_job("Kasım", [a, b])
    win.yukle.open_job(win.store.load(job.id))
    QApplication.processEvents()
    return win


def _undo_tip(window) -> str:
    return window.registry.action("app.geri_al").toolTip()


def _key(window, key, mods=Qt.KeyboardModifier.NoModifier) -> None:
    QTest.keyClick(QApplication.focusWidget() or window, key, mods)


def test_one_undo_history_names_the_step_on_every_tab(window):
    ctl = window.controller()
    r = window.registry
    window.show_tab("yukle")
    first = ctl.job.batches[0].id
    window.yukle.move_batch_to(first, 1)  # a batch move
    assert _undo_tip(window) == "Geri al: Partiyi taşı (Ctrl+Z)"
    assert r.action("app.geri_al").text().replace("&", "") == "Geri al: Partiyi taşı"
    window.show_tab("kontrol")
    pid = ctl.job.ordered_page_ids()[1]
    assert ctl.add_cut(pid)  # a Kontrol edit
    assert _undo_tip(window) == "Geri al: Kesim ekle (Ctrl+Z)"
    window.show_tab("degerler")
    assert _undo_tip(window) == "Geri al: Kesim ekle (Ctrl+Z)"  # the same job history
    window.show_tab("sablonlar")  # the template editor's own history, named the same way
    assert not r.is_enabled("app.geri_al") and _undo_tip(window) == "Geri al (Ctrl+Z)"
    window.show_tab("kontrol")
    window.kontrol.timeline.setFocus()
    _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert _undo_tip(window) == "Geri al: Partiyi taşı (Ctrl+Z)"
    assert window.registry.action("app.yinele").toolTip() == "Yinele: Kesim ekle (Ctrl+Y)"
    _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert ctl.job.batches[0].id == first  # the batch move undone from Kontrol too
    _key(window, Qt.Key.Key_Y, Qt.KeyboardModifier.ControlModifier)
    assert ctl.job.batches[1].id == first


def test_the_duzen_menu_shows_the_named_step(window):
    window.show_tab("yukle")
    window.yukle.move_batch_to(window.controller().job.batches[0].id, 1)
    menu = QMenu()
    title = actions.MENUS["duzen"]
    window._fill_menu(menu, title)
    texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
    assert texts[0] == "Geri al: Partiyi taşı"
    assert texts[1] == "Yinele"


def test_every_zoomable_view_takes_the_zoom_keys(window, tmp_path):
    for tab in ("kontrol", "degerler", "rehber"):
        window.show_tab(tab)
        controller = window.zoom_controller()
        assert controller is not None, tab
        assert window.zoom_slider.isVisible(), tab
        before = controller.zoom()
        window.registry.action("app.yakinlastir").trigger()
        assert controller.zoom() > before, tab
        window.registry.action("app.sigdir").trigger()
    window.show_tab("kontrol")
    window.kontrol.open_loupe(0)  # the page preview takes the slider while it is open
    assert window.zoom_controller() is window.kontrol.loupe().zoom
    window.kontrol.close_loupe()
    window.show_tab("yukle")
    assert window.zoom_controller() is None and not window.zoom_slider.isVisible()


def test_every_live_action_is_named_keyed_and_unique_on_its_tab(window):
    for tab in TAB_IDS:
        window.show_tab(tab)
        QApplication.processEvents()
        keys: dict[str, QAction] = {}
        for item in window.findChildren(QAction):
            if not item.isEnabled() or not item.shortcuts():
                continue
            assert actions.plain_text(item.text()).strip(), (tab, item.objectName())
            first = item.shortcuts()[0]
            assert item.toolTip(), (tab, item.objectName())
            for key in item.shortcuts():
                name = key.toString()
                assert name not in keys or keys[name] is item, (tab, name, item.objectName(),
                                                                keys[name].objectName())
                keys[name] = item
            spec = window.registry.spec(item.objectName())
            assert f"({actions.key_text(spec.shortcuts[0])})" in item.toolTip(), (tab, first)


def test_typing_never_fires_a_single_key_command(window):
    window.show_tab("rehber")
    window.rehber.search.setFocus()
    QApplication.processEvents()
    assert window.registry.live_keys("app.kisayollar") == ["Shift+F1", "Ctrl+/"]  # not "?"
    window.show_tab("kontrol")
    window.kontrol.timeline.setFocus()
    QApplication.processEvents()
    assert "K" in window.registry.live_keys("kontrol.kes")


def test_job_rows_have_a_context_menu(window):
    window.close_job()
    window.show_tab("yukle")
    QApplication.processEvents()
    page = window.yukle.empty
    assert page.entries, "the closed job is listed"
    menu = page.job_menu(page.entries[0], window.mapToGlobal(window.rect().center()))
    texts = [a.text().replace("&", "") for a in menu.actions()]
    assert texts == ["İşi aç", "Klasörünü Dosya Gezgini'nde göster"]
    opened = []
    page.open_job.connect(opened.append)
    menu.actions()[0].trigger()
    assert opened == [page.entries[0].id]
    menu.close()
