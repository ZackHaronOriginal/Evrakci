import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from evrakci.ui import actions, palette
from evrakci.ui.palette import CommandPalette


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def setup(app):
    palette._recent.clear()
    window = QMainWindow()
    window.resize(900, 600)
    registry = actions.Registry(window)
    calls: list[str] = []
    for spec in actions.SPECS:
        registry.connect(spec.id, lambda *_a, i=spec.id: calls.append(i))
    registry.set_context("kontrol")
    box = CommandPalette(registry, window)
    window.show()
    yield box, registry, calls
    box.close()
    window.close()
    palette._recent.clear()


def _texts(box):
    return [e.text for e in box.entries()]


def test_lists_commands_of_tab_only(setup):
    box, registry, _ = setup
    box.open_for("kontrol")
    ids = {e.id for e in box.entries()}
    assert ids == {e.id for e in registry.palette_entries("kontrol")}
    assert not any(i.startswith("yukle.") for i in ids)


def test_turkish_folding_finds_sil(setup):
    box, _, _ = setup
    box.open_for("kontrol")
    box.field.setText("SİL")
    texts = _texts(box)
    assert texts
    assert any("sil" in actions.fold(t) for t in texts)
    box.field.setText("zzzzqq")
    assert box.entries() == [] and not box.empty.isHidden()


def test_enter_triggers_action_and_closes(setup):
    box, _, calls = setup
    box.open_for("kontrol")
    box.field.setText("sil")
    first = box.entries()[0].id
    QTest.keyClick(box.field, Qt.Key.Key_Return)
    assert calls == [first]
    assert not box.isVisible()


def test_down_moves_selection(setup):
    box, _, calls = setup
    box.open_for("kontrol")
    box.field.clear()
    QTest.keyClick(box.field, Qt.Key.Key_Down)
    QTest.keyClick(box.field, Qt.Key.Key_Return)
    assert calls == [box.entries()[1].id]


def test_escape_closes(setup):
    box, _, calls = setup
    box.open_for("kontrol")
    assert box.isVisible()
    QTest.keyClick(box.field, Qt.Key.Key_Escape)
    assert not box.isVisible() and calls == []


def test_recent_first(setup):
    box, registry, _ = setup
    box.open_for("kontrol")
    last = box.entries()[-1].id
    palette.remember(last)
    box.open_for("kontrol")
    assert box.entries()[0].id == last


def test_disabled_entry_does_not_run(setup):
    box, registry, calls = setup
    box.open_for("kontrol")
    target = box.entries()[0].id
    registry.set_enabled(target, False)
    box.open_for("kontrol")
    entry = next(e for e in box.entries() if e.id == target)
    assert not entry.enabled
    box.field.setText(entry.text)
    QTest.keyClick(box.field, Qt.Key.Key_Return)
    assert target not in calls and box.isVisible()


def test_accessible_names(setup):
    box, _, _ = setup
    assert box.field.accessibleName() == "Komut ara"
    assert box.list.accessibleName()
