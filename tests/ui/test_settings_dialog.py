import pytest
from PySide6.QtWidgets import QApplication, QMainWindow

from evrakci.pipeline.settings import DELETE_AFTER_EXPORT, KEEP, load_settings
from evrakci.ui import actions, theme
from evrakci.ui.prefs import Prefs
from evrakci.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def env(app, tmp_path):
    window = QMainWindow()
    registry = actions.Registry(window)
    ini = tmp_path / "ui.ini"
    prefs = Prefs(ini)
    path = tmp_path / "settings.json"
    box = SettingsDialog(prefs, registry, window, retention_settings_path=path)
    yield box, ini, path
    box.close()
    window.close()
    manager = theme.manager()
    manager.set_mode("system")
    manager.set_density("normal")
    manager.set_text_scale(100)
    manager.set_reduced_motion(None)


def test_look_changes_apply_and_persist(env):
    box, ini, _ = env
    box.theme_buttons["dark"].setChecked(True)
    box.density_buttons["compact"].setChecked(True)
    box.size_buttons[130].setChecked(True)
    box.motion_buttons[True].setChecked(True)
    m = theme.manager()
    assert (m.mode(), m.density(), m.text_scale(), m.reduced_motion()) == (
        "dark", "compact", 130, True)
    stored = Prefs(ini)
    assert (stored.theme(), stored.density(), stored.text_size(), stored.reduced_motion()) == (
        "dark", "compact", 130, True)


def test_reset_look(env):
    box, ini, _ = env
    box.theme_buttons["hc"].setChecked(True)
    box.size_buttons[150].setChecked(True)
    box.reset_look()
    stored = Prefs(ini)
    assert (stored.theme(), stored.text_size(), stored.density()) == ("system", 100, "normal")
    assert theme.manager().mode() == "system"


def test_retention_round_trip(env):
    box, _, path = env
    assert box.retention.currentData() == KEEP
    box.retention.setCurrentIndex(box.retention.findData("90"))
    assert load_settings(path).retention == "90"
    box.retention.setCurrentIndex(box.retention.findData(DELETE_AFTER_EXPORT))
    assert load_settings(path).retention == DELETE_AFTER_EXPORT
    box.reset_retention()
    assert load_settings(path).retention == KEEP and box.retention.currentData() == KEEP


def test_retention_loads_existing(app, tmp_path):
    path = tmp_path / "s.json"
    path.write_text('{"saklama": "30"}', encoding="utf-8")
    window = QMainWindow()
    box = SettingsDialog(Prefs(tmp_path / "u.ini"), actions.Registry(window), window, path)
    assert box.retention.currentData() == "30"


def test_bad_retention_file_shows_message(app, tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{bozuk", encoding="utf-8")
    window = QMainWindow()
    box = SettingsDialog(Prefs(tmp_path / "u.ini"), actions.Registry(window), window, path)
    assert box.retention.currentData() == KEEP
    assert "okunamadı" in box.retention_note.text()


def test_export_folder(env, monkeypatch, tmp_path):
    box, ini, _ = env
    monkeypatch.setattr("evrakci.ui.settings_dialog.QFileDialog.getExistingDirectory",
                        lambda *a, **k: str(tmp_path))
    box.choose_folder()
    assert Prefs(ini).export_folder() == str(tmp_path)
    assert box.export_folder.text() == str(tmp_path)
    box.reset_export()
    assert Prefs(ini).export_folder() == ""


def test_shortcut_list_and_sheet(env):
    box, _, _ = env
    assert box.keys_list.count() > 0
    box.show_sheet()
    assert box._sheet is not None and box._sheet.isVisible()
    box._sheet.close()


def test_native_title_bar_toggle_is_saved(env):
    box, ini, _ = env
    assert not box.native_title.isChecked()
    box.native_title.setChecked(True)
    assert Prefs(ini).native_title_bar() is True
    box.reset_look()
    assert Prefs(ini).native_title_bar() is False
