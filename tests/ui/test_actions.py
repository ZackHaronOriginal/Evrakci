from dataclasses import replace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, icons
from evrakci.ui.actions import MENUS, SPECS, TABS, Registry


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    win = QMainWindow()
    yield win
    win.close()
    win.deleteLater()


def _connect_all(registry: Registry) -> None:
    for spec in SPECS:
        registry.connect(spec.id, lambda *_: None)


def test_table_is_valid(app):
    assert actions.validate() == []


def test_every_action_has_text_icon_and_tooltip_with_its_key(app, window):
    registry = Registry(window)
    for spec in SPECS:
        assert actions.plain_text(spec.text).strip(), spec.id
        if spec.icon:
            icons.resolve(spec.icon)
        tip = registry.action(spec.id).toolTip()
        assert tip
        if spec.shortcuts:
            native = actions.key_text(spec.shortcuts[0])  # Space reads "Boşluk"
            assert f"({native})" in tip, (spec.id, tip)
            assert "&" not in tip.replace(f"({native})", ""), (spec.id, tip)


def test_required_keys_are_present(app):
    keys = {(s.context, k) for s in SPECS for k in s.shortcuts}
    for k in ["Ctrl+1", "Ctrl+6", "Ctrl+Tab", "Ctrl+Shift+Tab", "F6", "Shift+F6", "Ctrl+K",
              "Ctrl+Shift+P", "F1", "Shift+F1", "Ctrl+/", "?", "Ctrl+,", "Ctrl+Z", "Ctrl+Y",
              "Ctrl+Shift+Z", "Ctrl++", "Ctrl+=", "Ctrl+Num++", "Ctrl+-", "Ctrl+0", "Ctrl+G",
              "Ctrl+F", "Ctrl+N", "Ctrl+O", "Ctrl+W", "Ctrl+E", "Ctrl+S"]:
        assert ("app", k) in keys, k
    for k in ["K", "M", "R", "Shift+R", "Del", "F", "N", "Shift+N", "U", "Return", "Ctrl+A",
              "Esc", "Space", "T"]:
        assert ("kontrol", k) in keys, k
    for k in ["Return", "Ctrl+Return", "F2", "V", "N", "Shift+N", "Esc", "Tab", "Space"]:
        assert ("degerler", k) in keys, k
    for k in ["B", "G", "Ctrl+T", "Left", "Shift+Left", "Alt+Up", "Del"]:
        assert ("sablonlar", k) in keys, k
    for k in ["Alt+Up", "Alt+Down", "Del", "Ctrl+."]:
        assert ("yukle", k) in keys, k
    assert actions.spec("kontrol.sonraki_kontrol").text.replace("&", "") == "Sonraki kontrol"
    assert actions.spec("kontrol.onayla").text.replace("&", "") == "Belgeyi onayla"
    assert actions.spec("app.yardim").shortcuts == ("F1",)  # F1 is help, not the Rehber tab


@pytest.mark.parametrize("bad, problem", [
    ({"shortcuts": ("Ctrl+Ş",)}, "Turkish"),
    ({"shortcuts": ("Ctrl+I",)}, "Turkish"),
    ({"shortcuts": ("Ctrl+Alt+Q",)}, "Ctrl+Alt"),
    ({"shortcuts": ("Ctrl+N",)}, "used by"),  # app.yeni_is owns Ctrl+N everywhere
    ({"single_key": False}, "single_key"),
])
def test_validate_catches_mistakes(app, bad, problem):
    specs = tuple(replace(s, **bad) if s.id == "kontrol.kes" else s for s in SPECS)
    assert any(problem in error for error in actions.validate(specs))


def test_validate_catches_menu_access_key_clash(app):
    specs = tuple(replace(s, text="&Burada kes") if s.id == "kontrol.kes" else s for s in SPECS)
    assert any("access key B repeats" in e for e in actions.validate(specs))


def test_same_key_on_two_tabs_is_allowed(app):
    owners = {s.context for s in SPECS if "N" in s.shortcuts}
    assert owners == {"kontrol", "degerler"}


def test_unconnected_actions_are_disabled(app, window):
    registry = Registry(window)
    registry.set_context("kontrol")
    assert not registry.is_enabled("kontrol.kes")
    registry.connect("kontrol.kes", lambda: None)
    assert registry.is_enabled("kontrol.kes")
    registry.set_enabled("kontrol.kes", False)
    assert not registry.is_enabled("kontrol.kes")
    registry.set_enabled("kontrol.kes", True)
    assert registry.is_enabled("kontrol.kes")


def test_context_switch_enables_only_app_and_current_tab(app, window):
    registry = Registry(window)
    _connect_all(registry)
    for tab in TABS:
        registry.set_context(tab)
        for spec in SPECS:
            expected = spec.context in ("app", tab)
            assert registry.is_enabled(spec.id) == expected, (tab, spec.id)
            assert registry.action(spec.id).isVisible() == expected
    with pytest.raises(ValueError):
        registry.set_context("yok")


def test_triggering_runs_the_connected_slot(app, window):
    registry = Registry(window)
    calls = []
    registry.connect("app.geri_al", lambda: calls.append("undo"))
    registry.connect("sablonlar.izgara", lambda checked: calls.append(checked))
    registry.set_context("sablonlar")
    registry.action("app.geri_al").trigger()
    registry.action("sablonlar.izgara").trigger()
    assert calls == ["undo", True]


def test_local_keys_are_not_bound(app, window):
    registry = Registry(window)
    _connect_all(registry)
    registry.set_context("degerler")
    assert registry.live_keys("degerler.sonraki_deger") == []
    assert "Tab" in registry.action("degerler.sonraki_deger").toolTip()


def _shown(window, *widgets):
    body = QWidget()
    layout = QVBoxLayout(body)
    for widget in widgets:
        layout.addWidget(widget)
    window.setCentralWidget(body)
    window.show()
    window.activateWindow()
    assert QTest.qWaitForWindowActive(window)


def test_same_key_fires_the_current_tabs_action(app, window):
    registry = Registry(window)
    calls = []
    registry.connect("kontrol.sonraki_kontrol", lambda: calls.append("kontrol"))
    registry.connect("degerler.sonraki_kontrol", lambda: calls.append("degerler"))
    button = QPushButton("x")
    _shown(window, button)
    button.setFocus()
    registry.set_context("kontrol")
    QTest.keyClick(button, Qt.Key.Key_N)
    registry.set_context("degerler")
    QTest.keyClick(button, Qt.Key.Key_N)
    registry.set_context("yukle")
    QTest.keyClick(button, Qt.Key.Key_N)
    assert calls == ["kontrol", "degerler"]


def test_text_focus_guard_drops_typing_keys(app, window):
    registry = Registry(window)
    calls = []
    _connect_all(registry)
    registry.connect("kontrol.kes", lambda: calls.append("kes"))
    registry.set_context("kontrol")
    field, button = QLineEdit(), QPushButton("x")
    _shown(window, field, button)
    registry.install_text_guard(app)
    button.setFocus()
    app.processEvents()
    assert registry.live_keys("kontrol.kes") == ["K"]
    QTest.keyClick(button, Qt.Key.Key_K)
    assert calls == ["kes"]

    field.setFocus()
    app.processEvents()
    assert app.focusWidget() is field
    assert registry.live_keys("kontrol.kes") == []
    assert registry.live_keys("kontrol.onayla") == []
    assert registry.live_keys("app.kisayollar") == ["Shift+F1", "Ctrl+/"]  # "?" dropped
    assert registry.live_keys("app.geri_al") == ["Ctrl+Z"]
    assert registry.is_enabled("kontrol.kes")  # its button still works, only the key is off
    QTest.keyClicks(field, "kmn")
    assert field.text() == "kmn" and calls == ["kes"]

    button.setFocus()
    app.processEvents()
    assert registry.live_keys("kontrol.kes") == ["K"]


def test_is_text_input(app):
    from PySide6.QtWidgets import QComboBox, QSpinBox, QTextEdit
    combo = QComboBox()
    assert not actions.is_text_input(combo)
    combo.setEditable(True)
    assert actions.is_text_input(combo)
    assert actions.is_text_input(QSpinBox())
    text = QTextEdit()
    assert actions.is_text_input(text)
    text.setReadOnly(True)
    assert not actions.is_text_input(text)
    assert not actions.is_text_input(None)


def test_shortcut_sheet_lists_only_that_tab(app):
    for tab in TABS:
        rows = actions.shortcut_sheet(tab)
        groups = {row.group for row in rows}
        assert TABS[tab] in groups
        others = set(TABS.values()) - {TABS[tab]}
        assert not groups & others, (tab, groups & others)
        assert all(row.keys and row.text for row in rows)
    kontrol = {row.text: row.keys for row in actions.shortcut_sheet("kontrol")}
    assert kontrol["Burada kes"] == ["K"]
    assert "Kutu çiz" not in kontrol
    assert "Klavye kısayolları" in kontrol


def test_palette_search_folds_turkish_case(app, window):
    registry = Registry(window)
    _connect_all(registry)
    registry.set_context("kontrol")
    entries = registry.palette_entries()
    assert all(e.id != "app.komut_ara" for e in entries)
    found = {e.id for e in actions.palette_search(entries, "SİL")}
    assert "kontrol.sil" in found
    assert {e.id for e in actions.palette_search(entries, "sıl")} >= {"kontrol.sil"}
    assert "kontrol.kes" in {e.id for e in actions.palette_search(entries, "BURADA KES")}
    assert "app.kisayollar" in {e.id for e in actions.palette_search(entries, "KISAYOL")}
    assert "app.kisayollar" in {e.id for e in actions.palette_search(entries, "kısayol")}
    assert "sablonlar.kutu_ciz" not in {e.id for e in entries}
    sil = next(e for e in entries if e.id == "kontrol.sil")
    assert sil.enabled and sil.keys == ["Del"]
    registry.set_enabled("kontrol.sil", False)
    assert not next(e for e in registry.palette_entries() if e.id == "kontrol.sil").enabled
    assert actions.fold("İSİM ışık IĞDIR") == "isim isik igdir"


def test_menu_structure_has_six_menus_with_unique_access_keys(app):
    menus = actions.menu_structure()
    assert [title for title, _ in menus] == list(MENUS.values())
    assert [t.replace("&", "") for t, _ in menus] == [
        "Dosya", "Düzen", "Görünüm", "Git", "Araçlar", "Yardım"]
    bar_keys = [actions.access_key(t) for t, _ in menus]
    assert len(set(bar_keys)) == 6 and "I" not in bar_keys
    in_menus = {i for _, items in menus for i in items if i}
    assert in_menus == {s.id for s in SPECS if s.menu}
    for tab in TABS:
        for title, items in actions.menu_structure(tab):
            assert items and items[0] is not None and items[-1] is not None
            assert all(a or b for a, b in zip(items, items[1:], strict=False))  # no double sep
            letters = [actions.access_key(actions.spec(i).text) for i in items if i]
            assert len(letters) == len(set(letters)), (tab, title, letters)
            assert all(x and x.isascii() and x.isalpha() and x != "I" for x in letters)
            for item in filter(None, items):
                assert actions.spec(item).context in ("app", tab)


def test_menu_text_keeps_access_key_and_buttons_do_not(app, window):
    registry = Registry(window)
    assert registry.action("app.yeni_is").text() == "&Yeni iş oluştur…"
    assert registry.action("app.sonraki_bolge").text() == "Sonraki bölge"
