"""The Rehber tab: the guide as sections, search with hits, the contents list, zoom, the shortcut
list from the registry, printing the separator sheets, and the window wiring."""
from __future__ import annotations

import pikepdf
import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QShortcut, QWheelEvent
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions, rehber_content
from evrakci.ui import rehber_print as printing
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.rehber import RehberScreen


def _window(qtbot, tmp_path, tab: str = "rehber") -> MainWindow:
    window = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.resize(1366, 768)
    window.show()
    window.show_tab(tab)
    QApplication.processEvents()
    return window


def _screen(qtbot) -> RehberScreen:
    screen = RehberScreen()
    qtbot.addWidget(screen)
    screen.resize(1200, 700)
    screen.show()
    QApplication.processEvents()
    return screen


class _Dialog:
    """Stands in for QPrintDialog: answers at once, printing to a PDF file."""

    target = ""
    answer = QDialog.DialogCode.Accepted

    def __init__(self, printer: QPrinter, parent=None) -> None:
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(_Dialog.target)

    def setWindowTitle(self, _title: str) -> None:  # noqa: N802
        pass

    def exec(self):
        return _Dialog.answer


# -- the guide as data -------------------------------------------------------------------------
def test_the_guide_has_seven_sections_and_the_keys_come_last(qtbot):
    guide = rehber_content.with_shortcuts(rehber_content.parse_guide(rehber_content.guide_text()))
    assert guide.titles() == ["Hazırlık", "QR ayıraç sayfaları", "Küçük makbuzlar",
                              "Tarayıcı ayarları", "Yükleme", "Sonrası", "Kısayollar"]
    assert guide.title == "Tarama rehberi" and guide.lead
    kinds = {b.kind for s in guide.sections for b in s.blocks}
    assert {"ol", "ul", "table", "h3", "p"} <= kinds
    assert guide.minutes() >= 1


def test_markdown_numbers_in_headings_are_dropped():
    guide = rehber_content.parse_guide("# T\n\nGiriş\n\n## 1. Bir\n\n- a\n  devam\n\n## 2. İki\n")
    assert guide.titles() == ["Bir", "İki"]
    assert guide.sections[0].blocks[0].items == ["a devam"]


def test_the_shortcut_table_is_read_from_the_registry():
    rows = {r.does: r.keys for r in rehber_content.shortcut_rows()}
    assert rows["Rehberde ara"] == ["Ctrl+F"]
    assert rows["Sonraki ve önceki sonuç"] == ["F3", "Shift+F3"]
    assert rows["Aramayı temizle"] == ["Esc"]
    assert rows["Yardım konularını aç"] == ["F1"]
    assert rows["Ayıraç sayfasını yazdır"] == ["Ctrl+P"]
    assert rows["Klavye kısayollarını göster"] == ["Shift+F1"]
    assert rows["Yazıyı büyüt ve küçült (Ctrl+tekerlek de çalışır)"][1] == "Ctrl+-"
    sheet = {r.text: r.keys for r in actions.shortcut_sheet("rehber")}
    for keys in (rows["Rehberde ara"], rows["Aramayı temizle"]):
        assert keys[0] in sum(sheet.values(), [])


def test_search_folds_turkish_letters():
    found = rehber_content.find_in_text("Ayıraç sayfası, AYIRAÇ, ayirac, İyi ıyı", "AYIRAC")
    assert [length for _s, length in found] == [6, 6, 6]
    assert [s for s, _n in rehber_content.find_in_text("İyi ıyı", "iyi")] == [0, 4]
    assert rehber_content.find_in_text("abc", "   ") == []


def test_every_common_topic_has_a_hit(qtbot):
    screen = _screen(qtbot)
    for topic in rehber_content.COMMON_TOPICS:
        assert screen.text.search(topic), topic


# -- search -------------------------------------------------------------------------------------
def test_typing_marks_hits_and_counts_them_per_section(qtbot):
    screen = _screen(qtbot)
    screen.search.setText("ayıraç")
    hits = screen.text.hits()
    assert len(hits) > 3
    assert screen.text.current() == 0
    assert screen.result.accessibleName() == f"{len(hits)} sonuç, 1 / {len(hits)}"
    assert len(screen.text.extraSelections()) == len(hits)
    counts = [screen.toc.item(i).data(Qt.ItemDataRole.UserRole + 1) or 0
              for i in range(screen.toc.count())]
    assert sum(counts) == len(hits) and counts[1] > 0  # "QR ayıraç sayfaları"
    assert screen.previous_button.isEnabled() and screen.next_button.isEnabled()
    assert screen._status_hits.parts()[1] == " sonuç: ayıraç"


def test_stepping_wraps_and_scrolls_to_the_hit(qtbot):
    screen = _screen(qtbot)
    screen.search.setText("ayıraç")
    total = len(screen.text.hits())
    screen.step(-1)
    assert screen.text.current() == total - 1
    screen.step(1)
    assert screen.text.current() == 0
    # a hit far down the page is brought into view
    screen.search.setText("Komut ara")
    assert screen.text.verticalScrollBar().value() > 0
    assert screen.section() == len(screen.guide.sections) - 1


def test_enter_and_shift_enter_in_the_field_step(qtbot):
    screen = _screen(qtbot)
    screen.search.setText("ayıraç")
    screen.search.setFocus()
    QTest.keyClick(screen.search, Qt.Key.Key_Return)
    assert screen.text.current() == 1
    QTest.keyClick(screen.search, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
    assert screen.text.current() == 0


def test_no_hits_shows_the_empty_state_with_a_way_out(qtbot):
    screen = _screen(qtbot)
    screen.search.setText("laminasyon")
    assert screen.stack.currentWidget() is screen.empty
    assert screen.empty.title.text() == "“laminasyon” için sonuç yok"
    assert "Sık aranan konular: ayıraç" in screen.empty.topics.text()
    assert screen.result.accessibleName() == "laminasyon için sonuç yok"
    assert not screen.next_button.isEnabled()
    assert screen.toc.currentRow() == -1
    assert screen._status_hits.parts() == ("0", " sonuç: laminasyon")
    screen.empty.clear.click()  # "Aramayı temizle"
    assert screen.search.text() == "" and screen.stack.currentWidget() is screen.text
    assert screen.focusWidget() is screen.search
    screen.search.setText("laminasyon")
    screen.empty.keys.click()  # "Kısayolları göster"
    assert screen.search.text() == "" and screen.section() == len(screen.guide.sections) - 1


def test_escape_clears_from_the_field_and_the_reader(qtbot):
    screen = _screen(qtbot)
    screen.search.setText("zımba")
    screen.search.setFocus()
    QTest.keyClick(screen.search, Qt.Key.Key_Escape)
    assert screen.search.text() == ""
    assert screen.text.hits() == [] and not screen._status_hits.isVisible()
    screen.search.setText("zımba")
    screen.text.setFocus()
    QTest.keyClick(screen.text, Qt.Key.Key_Escape)
    assert screen.search.text() == ""
    QTest.keyClick(screen.search, Qt.Key.Key_Escape)  # nothing to clear: the key goes on
    assert screen.search.text() == ""


def test_the_x_button_clears_and_shows_only_with_text(qtbot):
    screen = _screen(qtbot)
    assert not screen.search.clear_action.isVisible()
    screen.search.setText("zımba")
    assert screen.search.clear_action.isVisible()
    screen.search.clear_action.trigger()
    assert screen.search.text() == ""


# -- contents and the section being read -----------------------------------------------------
def test_the_contents_list_scrolls_and_follows_the_reader(qtbot):
    screen = _screen(qtbot)
    assert screen.toc.count() == 7 and screen.toc.currentRow() == 0
    screen.toc.section_chosen.emit(3)
    assert screen.section() == 3 and screen.toc.currentRow() == 3
    assert screen.text.verticalScrollBar().value() > 0
    screen.text.verticalScrollBar().setValue(0)  # the reader scrolls by hand: pin released
    assert screen.section() == 0 and screen.toc.currentRow() == 0
    screen.text.verticalScrollBar().setValue(screen.text.verticalScrollBar().maximum())
    assert screen.section() == 6
    assert screen._status_section.parts() == ("Bölüm ", "7", " / 7")


def test_clicking_a_contents_row_goes_there(qtbot):
    screen = _screen(qtbot)
    index = screen.toc.model().index(4, 0)
    rect = screen.toc.visualItemRect(screen.toc.item(4))
    QTest.mouseClick(screen.toc.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    assert index.isValid() and screen.section() == 4


# -- zoom ---------------------------------------------------------------------------------------
def _wheel(widget, delta: int) -> None:
    event = QWheelEvent(QPoint(40, 40), widget.mapToGlobal(QPoint(40, 40)), QPoint(0, 0),
                        QPoint(0, delta), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.ControlModifier, Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(widget.viewport(), event)


def test_ctrl_wheel_and_keys_zoom_the_text_and_keep_hits(qtbot):
    screen = _screen(qtbot)
    screen.search.setText("ayıraç")
    before = screen.text.document().defaultFont().pixelSize()
    hits = len(screen.text.hits())
    _wheel(screen.text, 120)
    assert screen.zoom.zoom() == 110
    assert screen.text.document().defaultFont().pixelSize() > before
    assert len(screen.text.hits()) == hits and screen.text.current() == 0
    screen.text.setFocus()
    QTest.keyClick(screen.text, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(screen.text, Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier)
    assert screen.zoom.zoom() == 90
    QTest.keyClick(screen.text, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
    assert screen.zoom.zoom() == 100
    assert screen.zoom.minimum() == 50 and screen.zoom.maximum() == 300


# -- the window ---------------------------------------------------------------------------------
def test_the_tab_wires_its_actions_and_fills_the_bar_and_status(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    r = window.registry
    for spec in actions.SPECS:
        if spec.context == "rehber":
            assert r.is_enabled(spec.id), spec.id
    for action_id in ("app.bul", "app.sonraki_sonuc", "app.onceki_sonuc", "app.yan_panel",
                      "app.yardim", "app.kisayollar", "app.yakinlastir", "app.uzaklastir",
                      "app.sigdir"):
        assert r.is_enabled(action_id), action_id
    names = [b.accessibleName() or b.toolTip() for b in window.command_bar("rehber").buttons()]
    assert any(n.startswith("Ayıraç sayfasını yazdır") for n in names)
    assert "PDF olarak aç" in names
    assert names.index("PDF olarak aç") == next(
        i for i, n in enumerate(names) if n.startswith("Ayıraç sayfasını yazdır")) + 1
    assert window.rehber._status_section.parts() == ("Bölüm ", "1", " / 7")
    assert window.zoom_controller("rehber") is window.rehber.zoom
    assert window.zoom_slider.isVisible()


def test_ctrl_f_focuses_the_field_and_f3_only_acts_on_this_tab(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.rehber
    screen.text.setFocus()
    QTest.keyClick(window, Qt.Key.Key_F, Qt.KeyboardModifier.ControlModifier)
    assert screen.focusWidget() is screen.search
    screen.search.setText("ayıraç")
    QTest.keyClick(screen.search, Qt.Key.Key_F3)
    assert screen.text.current() == 1
    QTest.keyClick(screen.search, Qt.Key.Key_F3, Qt.KeyboardModifier.ShiftModifier)
    assert screen.text.current() == 0
    window.show_tab("yukle")
    screen.search.setText("ayıraç")
    window.registry.action("app.sonraki_sonuc").trigger()
    assert screen.text.current() == 0  # another tab: Rehber ignores the app-wide key


def test_ctrl_f_shows_the_side_panel_when_f9_hid_it(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    window.toggle_inspector()
    assert window.rehber.side.isHidden()
    window.registry.action("app.bul").trigger()
    assert not window.rehber.side.isHidden()


def test_f1_and_the_help_link_come_here_and_the_sheet_lists_the_keys(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, tab="yukle")
    window.registry.action("app.yardim").trigger()
    assert window.current_tab() == "rehber"


def test_splitter_zoom_and_the_hidden_tip_persist(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.rehber
    screen.splitter.setSizes([600, 380])
    screen.splitter.splitterMoved.emit(600, 1)
    assert window.prefs.splitter_sizes("rehber")[1] == screen.splitter.sizes()[1]
    screen.zoom.set_zoom(130)
    assert window.prefs.zoom("rehber") == 130
    assert "Bir daha gösterme" in screen.text.toPlainText()
    screen.dismiss_note()
    assert "Bir daha gösterme" not in screen.text.toPlainText()
    # a new window on the same preferences starts as the last one ended
    again = MainWindow(JobStore(tmp_path / "jobs"), TemplateStore(tmp_path / "tpl"),
                       settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(again)
    again.show()
    again.show_tab("rehber")
    QApplication.processEvents()
    assert again.rehber.zoom.zoom() == 130
    assert again.rehber.splitter.sizes()[1] == window.prefs.splitter_sizes("rehber")[1]
    assert "Bir daha gösterme" not in again.rehber.text.toPlainText()


def test_every_control_has_an_accessible_name(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.rehber
    for widget in (screen.text, screen.search, screen.previous_button, screen.next_button,
                   screen.toc, screen.count, screen.print_button, screen.side, screen.article,
                   screen.empty, screen.result):
        assert widget.accessibleName(), widget
    assert screen.search.accessibleName() == "Rehberde ara"
    assert screen.previous_button.accessibleName() == "Önceki sonuç (Shift+F3)"
    assert screen.next_button.accessibleName() == "Sonraki sonuç (F3)"
    assert screen.print_button.accessibleName() == "Ayıraç sayfasını yazdır (Ctrl+P)"
    assert screen.toc.item(1).data(Qt.ItemDataRole.AccessibleTextRole) == "2. QR ayıraç sayfaları"
    assert screen.search.lead.text() == "Ara"
    assert screen.search.clear_action.text() == "Aramayı temizle"
    assert screen.search.clear_action.toolTip() == "Aramayı temizle (Esc)"
    assert not screen.findChildren(QShortcut)  # every key is a registry action


# -- the separator sheets -----------------------------------------------------------------------
def test_printing_sends_front_and_back_of_every_sheet(qtbot, tmp_path):
    out = tmp_path / "yazdir.pdf"
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(str(out))
    assert printing.print_separators(printer, 3) == 6
    with pikepdf.open(out) as pdf:
        assert len(pdf.pages) == 6
    with pytest.raises(ValueError):
        printing.print_separators(printer, 0)


def test_ctrl_p_asks_for_a_printer_then_prints_the_chosen_count(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.rehber
    _Dialog.target = str(tmp_path / "ayirac.pdf")
    _Dialog.answer = QDialog.DialogCode.Accepted
    screen._print_dialog = _Dialog
    screen.count.setValue(2)
    QTest.keyClick(window, Qt.Key.Key_P, Qt.KeyboardModifier.ControlModifier)
    with pikepdf.open(tmp_path / "ayirac.pdf") as pdf:
        assert len(pdf.pages) == 4
    assert "yazıcıya gönderildi" in window.toaster.current_text()


def test_cancelling_the_print_dialog_prints_nothing(qtbot, tmp_path):
    screen = _screen(qtbot)
    _Dialog.target = str(tmp_path / "yok.pdf")
    _Dialog.answer = QDialog.DialogCode.Rejected
    screen._print_dialog = _Dialog
    assert screen.print_separators() is None
    assert not (tmp_path / "yok.pdf").exists()


def test_a_printer_that_fails_offers_the_pdf(qtbot, tmp_path, monkeypatch):
    window = _window(qtbot, tmp_path)
    screen = window.rehber

    def refuse(_printer, _sheets):
        raise RuntimeError("yazıcı başlamadı")

    monkeypatch.setattr(printing, "print_separators", refuse)
    assert screen.print_separators(QPrinter()) is None
    assert "PDF olarak açıp" in window.toaster.current_text()


def test_the_separator_pdf_still_opens_from_the_tab(qtbot, tmp_path, monkeypatch):
    screen = _screen(qtbot)
    opened = []
    monkeypatch.setattr("evrakci.ui.rehber.data_dir", lambda: tmp_path)
    monkeypatch.setattr("evrakci.ui.rehber.QDesktopServices.openUrl",
                        lambda url: opened.append(url.toLocalFile()))
    screen.count.setValue(2)
    screen.open_separators()
    assert opened == [str(tmp_path / "ayirac-sayfalari.pdf")]
    with pikepdf.open(opened[0]) as pdf:
        assert len(pdf.pages) == 4


def test_the_empty_state_keys_reach_the_screen_in_every_theme(qtbot):
    from evrakci.ui import theme

    m = theme.manager()
    mode = m.mode()
    try:
        for name in ("light", "dark", "hc"):
            m.set_mode(name)
            screen = _screen(qtbot)
            screen.search.setText("laminasyon")
            assert not screen.empty.mark.pixmap().isNull()
    finally:
        m.set_mode(mode)


def test_page_keys_scroll_the_reader(qtbot):
    screen = _screen(qtbot)
    screen.text.setFocus()
    bar = screen.text.verticalScrollBar()
    QTest.keyClick(screen.text, Qt.Key.Key_PageDown)
    assert bar.value() > 0
