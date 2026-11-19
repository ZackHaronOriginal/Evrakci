import openpyxl
import pikepdf
from fakes import make_pdf, qr_page, text_page

from evrakci.cli import main
from evrakci.pipeline.store import JobStore
from evrakci.ui.controller import JobController
from evrakci.ui.disa_aktar import DisaAktarScreen
from evrakci.ui.rehber import RehberScreen


def _rows(path):
    sheet = openpyxl.load_workbook(path).active
    return [[cell.value for cell in row] for row in sheet.iter_rows()]


def test_window_export_matches_the_cli(qtbot, tmp_path, capsys):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page(), qr_page(), text_page()])
    assert main(["--kok", str(root), "is", "olustur", "Test", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]
    cli_out = tmp_path / "cli"
    assert main(["--kok", str(root), "is", "disa-aktar", job_id, "--cikti", str(cli_out),
                 "--metin-katmani-yok"]) == 0

    store = JobStore(root)
    ctl = JobController(store, store.load(job_id))
    screen = DisaAktarScreen(lambda: ctl, dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    screen.folder.setText(str(tmp_path / "ui"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    names = sorted(p.name for p in (tmp_path / "ui").iterdir())
    assert names == sorted(p.name for p in cli_out.iterdir())
    assert _rows(tmp_path / "ui" / "index.xlsx") == _rows(cli_out / "index.xlsx")
    assert screen.results.model().rowCount() == 2


def test_export_refuses_a_folder_with_an_earlier_export(qtbot, tmp_path):
    """A folder that holds an earlier export is an engel (Dışa Aktar's pre-flight): the button
    is off and says why, and nothing is written (UI change: it used to start and then fail)."""
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "kok")
    ctl = JobController(store, store.create_job("İş", [pdf]))
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "eski.pdf").write_bytes(b"x")
    screen = DisaAktarScreen(lambda: ctl, dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    assert screen.state() == "blocked"
    assert not screen.export_button.isEnabled()
    assert "boş değil" in screen.folder_hint_text()
    screen.export()  # a key press (Ctrl+E) does nothing either
    assert screen.task is None
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == ["eski.pdf"]


def test_the_retention_choice_moved_to_ayarlar(qtbot, tmp_path):
    """"İşi sakla" is in Ayarlar (A's Dışa Aktar has no such row); the export still reads it."""
    screen = DisaAktarScreen(lambda: None, dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    assert not hasattr(screen, "retention")


def test_guide_shows_the_scanning_guide_and_prints_separators(qtbot, tmp_path):
    screen = RehberScreen()
    qtbot.addWidget(screen)
    assert "QR" in screen.text.toPlainText()
    path = screen.write_separators(tmp_path / "ayirac.pdf", 3)
    with pikepdf.open(path) as pdf:
        assert len(pdf.pages) == 6  # each sheet front and back


def test_guide_is_found_next_to_the_installed_app(tmp_path, monkeypatch):
    from evrakci.ui.rehber import guide_text

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tarama-rehberi.md").write_text("# Kurulu rehber", encoding="utf-8")
    monkeypatch.setenv("EVRAKCI_UYGULAMA_KLASORU", str(tmp_path))
    assert guide_text() == "# Kurulu rehber"


def test_installer_ships_the_guide():
    from pathlib import Path

    setup = (Path(__file__).resolve().parents[2] / "packaging" / "freeze_setup.py").read_text(
        encoding="utf-8")
    assert "tarama-rehberi.md" in setup
