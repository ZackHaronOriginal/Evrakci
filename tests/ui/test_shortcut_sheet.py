import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from evrakci.ui import actions
from evrakci.ui.shortcut_sheet import ShortcutSheet


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def sheet(app):
    window = QMainWindow()
    registry = actions.Registry(window)
    box = ShortcutSheet(registry, window)
    yield box
    box.close()
    window.close()


def test_only_current_tab_keys(sheet):
    sheet.show_for("kontrol")
    groups = {g for g, _, _ in sheet.visible_rows()}
    assert "Kontrol" in groups
    assert not groups & {"Yükle", "Şablonlar", "Değerler", "Dışa Aktar", "Rehber"}
    rows = {(g, t) for g, t, _ in sheet.visible_rows()}
    assert rows == {(r.group, r.text) for r in actions.shortcut_sheet("kontrol")}


def test_other_tab_differs(sheet):
    sheet.show_for("degerler")
    groups = {g for g, _, _ in sheet.visible_rows()}
    assert "Kontrol" not in groups and "Değerler" in groups


def test_search_filters_with_turkish_folding(sheet):
    sheet.show_for("kontrol")
    total = len(sheet.visible_rows())
    sheet.search.setText("SİL")
    rows = sheet.visible_rows()
    assert rows and len(rows) < total
    assert all("sil" in actions.fold(f"{g} {t} {k}") for g, t, k in rows)
    sheet.search.setText("zzzzqq")
    assert sheet.visible_rows() == [] and not sheet.empty.isHidden()


def test_escape_closes(sheet):
    sheet.show_for("kontrol")
    QTest.keyClick(sheet, Qt.Key.Key_Escape)
    assert not sheet.isVisible()
