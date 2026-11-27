"""I-21: the document travels with the user between Kontrol and Değerler (D and K)."""

from contract_helpers import press, run_via_menu
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from saving import wait_saved
from test_ledger_c import BAD, GOOD, _template, _values, _window

NO_TEMPLATE = "Bu belgenin şablonu yok; Değerler'de görünmez."


def _open(qtbot, tmp_path, templated=3):
    """Three documents (pages 1-2, 3-4, 5-6); the first `templated` have a template and a
    value, the second one is the value to check."""
    win, store, job, templates = _window(qtbot, tmp_path, kinds="pppppp", prefs=False)
    template, sicil, firma = _template(templates, "Kapasite Raporu")
    with qtbot.waitSignal(win.yukle.job_opened, timeout=10000):
        win.yukle.open_job(store.load(job.id))
    qtbot.waitUntil(lambda: win.controller() is not None)
    ctl = win.controller()
    ctl.add_cut("b1/2")
    ctl.add_cut("b1/4")
    docs = ctl.documents()
    assert len(docs) == 3
    for doc, value in list(zip(docs, (GOOD, BAD, GOOD), strict=True))[:templated]:
        ctl.apply_template(list(doc.page_ids), template.id)
        _values(ctl, template, sicil, firma, doc, value)
    ctl.job_changed.emit()
    wait_saved(ctl)
    win.resize(1366, 768)
    win.show()
    win.activateWindow()
    assert QTest.qWaitForWindowActive(win)
    return win


def test_d_on_kontrol_selects_that_document_in_degerler(qtbot, tmp_path):
    win = _open(qtbot, tmp_path)
    win.show_tab("kontrol")
    win.kontrol.go_to_document(3)
    win.kontrol.timeline.setFocus()
    press(win, "D")
    assert win.current_tab() == "degerler"
    assert win.degerler.current_value()[0] == 3
    assert QApplication.focusWidget() is win.degerler.table
    assert "Belge 3 seçildi." in win.message.text()


def test_k_on_degerler_selects_that_document_in_kontrol(qtbot, tmp_path):
    win = _open(qtbot, tmp_path)
    win.show_tab("degerler")
    assert win.degerler.select_value(3, win.degerler.rows[2].cells[0].key)
    win.degerler.table.setFocus()
    press(win, "K")
    assert win.current_tab() == "kontrol"
    assert win.kontrol.current_document() == 3
    assert QApplication.focusWidget() is win.kontrol.timeline
    assert "Belge 3 seçildi." in win.message.text()


def test_kontrolde_ac_through_menu_and_context_menu(qtbot, tmp_path):
    win = _open(qtbot, tmp_path)
    deg = win.degerler
    action = win.registry.action("degerler.kontrolde_ac")
    assert action.text().replace("&", "") == "Kontrol'de aç"
    for how in ("menu", "context"):
        win.show_tab("degerler")
        deg.select_value(2, deg.rows[1].cells[0].key)
        if how == "menu":
            run_via_menu(win, "degerler.kontrolde_ac")  # Araçlar > Kontrol'de aç
        else:
            menu = deg.context_menu(deg.table.visualRect(deg.model.index(1, 0)).center())
            assert action in menu.actions()
            action.trigger()
        assert win.current_tab() == "kontrol"
        assert win.kontrol.current_document() == 2
        assert QApplication.focusWidget() is win.kontrol.timeline
        assert "Belge 2 seçildi." in win.message.text()


def test_document_without_a_template_says_so_and_stays(qtbot, tmp_path):
    win = _open(qtbot, tmp_path, templated=2)
    win.show_tab("kontrol")
    win.kontrol.go_to_document(3)
    win.kontrol.timeline.setFocus()
    press(win, "D")
    assert win.current_tab() == "kontrol"
    assert NO_TEMPLATE in win.message.text()


def test_filtered_out_clean_document_switches_to_tumu(qtbot, tmp_path):
    win = _open(qtbot, tmp_path)
    win.show_tab("degerler")
    win.degerler.set_view("kontrol")
    assert win.degerler.model.row_of(3) < 0  # Belge 3 is clean: the view hides it
    win.show_tab("kontrol")
    win.kontrol.go_to_document(3)
    win.kontrol.timeline.setFocus()
    press(win, "D")
    assert win.current_tab() == "degerler"
    assert win.degerler.view() == "tumu"
    assert win.degerler.current_value()[0] == 3
    assert "Belge 3 seçildi." in win.message.text()

