"""Plan 2 second fresh review (2026-11-09): every finding, red first."""

import http.client
import os
import subprocess
from pathlib import Path

import pytest
from conftest import needs_tesseract
from fakes import a4_300, make_pdf

from evrakci.pipeline.ocr import tesseract, textlayer
from evrakci.pipeline.ocr.engine import EngineUnavailable

posix_only = pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")


def data_folder(path: Path, tur: bytes = b"tur", hocr: str = "hocr 1") -> Path:
    (path / "configs").mkdir(parents=True)
    (path / "configs" / "hocr").write_text(hocr)
    (path / "tur.traineddata").write_bytes(tur)
    return path


# --- 1, 7: where the ASCII copies and temp folders live, and who can read them -------------

def test_ascii_root_prefers_the_users_own_local_folder(tmp_path, monkeypatch):
    monkeypatch.delenv("EVRAKCI_ASCII_KOK", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Şükrü" / "Local"))
    short = tmp_path / "SUKRU~1"
    root = tesseract.ascii_copy_root(windows=True, short_path=lambda p: short)
    assert root == short
    assert (tmp_path / "Şükrü" / "Local" / "Evrakci" / "ascii").is_dir()


@posix_only
def test_shared_fallback_folder_is_private(tmp_path, monkeypatch):
    monkeypatch.delenv("EVRAKCI_ASCII_KOK", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Şükrü"))
    monkeypatch.setenv("ProgramData", str(tmp_path / "pd"))
    root = tesseract.ascii_copy_root(windows=True, short_path=lambda p: p)  # no short names
    assert root.is_relative_to(tmp_path / "pd")
    assert root.stat().st_mode & 0o777 == 0o700


@posix_only
def test_each_ocr_run_gets_its_own_private_temp_folder(tmp_path):
    first = textlayer.ascii_temp_dir(windows=True, current="C:/Şükrü/Temp", root=tmp_path)
    second = textlayer.ascii_temp_dir(windows=True, current="C:/Şükrü/Temp", root=tmp_path)
    assert first != second
    assert first.stat().st_mode & 0o777 == 0o700


def test_temp_folder_and_environment_are_restored_even_after_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(textlayer, "ascii_temp_dir", lambda: tmp_path / "gecici-calisma")
    (tmp_path / "gecici-calisma").mkdir()
    before = {n: os.environ.get(n) for n in ("PATH", "TEMP", "TMP", "TESSDATA_PREFIX")}
    with pytest.raises(RuntimeError):
        with textlayer._tessdata_prefix(None):
            assert os.environ["TEMP"] == str(tmp_path / "gecici-calisma")
            raise RuntimeError("OCR durdu")
    assert {n: os.environ.get(n) for n in before} == before
    assert not (tmp_path / "gecici-calisma").exists()  # scans never stay behind


# --- 2: a copy that cannot be verified is never handed out ---------------------------------

def test_an_undeletable_planted_copy_is_never_used(tmp_path, monkeypatch):
    source = data_folder(tmp_path / "Şükrü")
    root = tmp_path / "kok"
    first = tesseract.ascii_safe_dir(source, windows=True, short_path=lambda p: p,
                                     copy_root=root)
    (first / "configs" / "hocr").write_text("tessedit_char_blacklist ş")  # planted config
    monkeypatch.setattr(tesseract.shutil, "rmtree", lambda *a, **k: None)  # cannot delete
    chosen = tesseract.ascii_safe_dir(source, windows=True, short_path=lambda p: p,
                                      copy_root=root)
    assert (chosen / "configs" / "hocr").read_text() == "hocr 1"


def test_old_copies_are_pruned(tmp_path):
    root = tmp_path / "kok"
    old = tesseract.ascii_safe_dir(data_folder(tmp_path / "Ş1", b"eski"), windows=True,
                                   short_path=lambda p: p, copy_root=root)
    new = tesseract.ascii_safe_dir(data_folder(tmp_path / "Ş2", b"yeni"), windows=True,
                                   short_path=lambda p: p, copy_root=root)
    assert new.is_dir() and not old.exists()


# --- 3, 8, 14: the engine reports problems instead of raising ------------------------------

def test_default_engine_never_raises_when_configs_are_missing(tmp_path, monkeypatch):
    best = tmp_path / "best"
    best.mkdir()
    monkeypatch.setattr(tesseract, "verify_tur_best", lambda folder: True)
    monkeypatch.setattr(tesseract, "tessdata_best_dir", lambda: best)
    monkeypatch.setattr(tesseract, "system_tessdata", lambda: None)
    monkeypatch.setattr(tesseract, "find_tesseract", lambda: Path("/usr/bin/tesseract"))
    engine = tesseract.default_engine()  # no exception
    assert engine.tessdata_dir == best


def test_a_blocked_tesseract_is_a_reason_not_a_crash(monkeypatch):
    monkeypatch.setattr(tesseract, "find_tesseract", lambda: Path("/usr/bin/tesseract"))

    def blocked(*args, **kwargs):
        raise PermissionError("Erişim engellendi")

    monkeypatch.setattr(tesseract.subprocess, "run", blocked)
    reason = tesseract.TesseractEngine().available()
    assert reason and "çalıştırılamadı" in reason


def test_a_hung_tesseract_times_out(monkeypatch):
    monkeypatch.setattr(tesseract, "find_tesseract", lambda: Path("/usr/bin/tesseract"))

    def hung(*args, **kwargs):
        assert kwargs.get("timeout")
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(tesseract.subprocess, "run", hung)
    assert "yanıt vermedi" in tesseract.TesseractEngine().available()


def test_a_wrong_evrakci_tesseract_setting_is_reported(tmp_path, monkeypatch):
    monkeypatch.setenv("EVRAKCI_TESSERACT", str(tmp_path / "yok.exe"))
    reason = tesseract.TesseractEngine().available()
    assert reason and "EVRAKCI_TESSERACT" in reason


# --- 4, 9, 18: how Tesseract is started ------------------------------------------------------

def test_no_console_window_flag_on_windows():
    assert tesseract.no_window(True) == {"creationflags": 0x08000000}
    assert tesseract.no_window(False) == {}


def test_every_tesseract_call_is_hidden_utf8_and_single_threaded(monkeypatch):
    from PIL import Image

    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        out = "tur\n" if "--list-langs" in command else b"level\ttext\n"
        return subprocess.CompletedProcess(command, 0, stdout=out, stderr=b"" if
                                           isinstance(out, bytes) else "")

    monkeypatch.setattr(tesseract, "find_tesseract", lambda: Path("/usr/bin/tesseract"))
    monkeypatch.setattr(tesseract, "no_window", lambda windows=None: {"creationflags": 7})
    monkeypatch.setattr(tesseract.subprocess, "run", fake_run)
    engine = tesseract.TesseractEngine()
    engine.read_region(Image.new("L", (50, 20), 255))
    tesseract.system_tessdata()
    assert calls and all(kwargs.get("creationflags") == 7 for _, kwargs in calls)
    for _command, kwargs in calls:
        if kwargs.get("text"):
            assert kwargs.get("encoding") == "utf-8" and kwargs.get("errors") == "replace"
    region = next(c for c in calls if "stdin" in c[0])
    assert region[0][region[0].index("--dpi") + 1] == "300"
    assert region[1]["env"]["OMP_THREAD_LIMIT"] == "1"


# --- 5, 12: OCRmyPDF options ----------------------------------------------------------------

def test_ocrmypdf_is_told_not_to_use_ghostscript_and_to_redo_old_text(tmp_path, monkeypatch):
    seen = {}

    def fake_ocr(src, dst, **kwargs):
        seen.update(kwargs)
        Path(dst).write_bytes(Path(src).read_bytes())
        return 0

    monkeypatch.setattr(textlayer.ocrmypdf, "ocr", fake_ocr)
    monkeypatch.setattr(textlayer, "find_tesseract", lambda: Path("/usr/bin/tesseract"))
    src = make_pdf(tmp_path / "a.pdf", [a4_300([])], dpi=72)
    textlayer.add_text_layer(src, tmp_path / "b.pdf", tessdata=tesseract.TessData("tur", None))
    assert seen["pdfa_backend"] == "internal" and seen["rasterizer"] == "pypdfium"
    assert seen["optimize"] == 0 and seen["mode"] == "redo"


@needs_tesseract
def test_ghostscript_is_never_run_even_when_installed(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "gs.log"
    gs = bin_dir / "gs"
    gs.write_text(f"#!/bin/sh\necho \"$@\" >> '{log}'\necho 10.0\n")
    gs.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    src = make_pdf(tmp_path / "a.pdf", [a4_300([("İSTANBUL IĞDIR Çağrı Güneş ılık", (20, 20))])])
    result = textlayer.add_text_layer(src, tmp_path / "b.pdf")
    assert result.pdfa
    assert not log.exists()


# --- 11: the fallback note says why -----------------------------------------------------------

def test_pdfa_fallback_note_keeps_the_reason(tmp_path, monkeypatch):
    from ocrmypdf import exceptions

    calls = []

    def fake_run(src, dst, tessdata, output_type, jobs):
        calls.append(output_type)
        if output_type == "pdfa-2":
            raise exceptions.PdfaConversionFailedError("font not embedded")
        Path(dst).write_bytes(b"%PDF")
        return 0

    monkeypatch.setattr(textlayer, "_run", fake_run)
    monkeypatch.setattr(textlayer, "find_tesseract", lambda: Path("/usr/bin/tesseract"))
    result = textlayer.add_text_layer(tmp_path / "a.pdf", tmp_path / "b.pdf",
                                      tessdata=tesseract.TessData("tur", None))
    assert not result.pdfa and "font not embedded" in result.note
    assert result.note.startswith(textlayer.PDFA_FALLBACK_NOTE)


# --- 7: more places Tesseract 4 keeps its data ---------------------------------------------------

@pytest.mark.parametrize("layout", ["exe-beside", "rhel", "prefix"])
def test_tesseract_4_data_found_in_other_layouts(tmp_path, monkeypatch, layout):
    binary = tmp_path / "usr" / "bin" / "tesseract"
    binary.parent.mkdir(parents=True)
    binary.write_text("")
    folder = {
        "exe-beside": binary.parent / "tessdata",
        "rhel": tmp_path / "usr" / "share" / "tesseract" / "tessdata",
        "prefix": tmp_path / "baska" / "tessdata",
    }[layout]
    data_folder(folder)
    prefix = str(folder) if layout == "prefix" else None
    found = tesseract.tessdata_from_list_langs("List of available languages (2):\n", binary,
                                               prefix=prefix)
    assert found == folder


# --- 6, 16: downloads ----------------------------------------------------------------------------

class CutOff:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self, *args):
        raise http.client.IncompleteRead(b"yarim")


def test_a_cut_off_tessdata_download_is_reported_and_the_next_one_tried(tmp_path, monkeypatch,
                                                                         capsys):
    from evrakci.cli import ocr as cli_ocr

    tried = []
    monkeypatch.setattr(cli_ocr, "tessdata_dir", lambda variant: tmp_path / variant)
    monkeypatch.setattr(cli_ocr, "verify_tessdata", lambda variant, folder: False)
    monkeypatch.setattr(cli_ocr.urllib.request, "urlopen",
                        lambda url, timeout: tried.append(url) or CutOff())
    assert cli_ocr._download_tessdata("fast") is False
    assert cli_ocr._download_tessdata("best") is False
    assert len(tried) == 2 and "hata" in capsys.readouterr().out
    assert not list(tmp_path.rglob("*.part"))


def test_a_cut_off_model_download_leaves_nothing_behind(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr import models

    monkeypatch.setenv("EVRAKCI_MODEL_DIR", str(tmp_path))
    monkeypatch.setattr(models.urllib.request, "urlopen", lambda url, timeout: CutOff())
    model = models.ModelFile("m", "http://x/m.onnx", "0" * 64, "m.onnx")
    with pytest.raises(EngineUnavailable):
        models.ensure_model(model)
    assert not list(tmp_path.iterdir())


def test_model_download_without_rapidocr_is_a_turkish_note(monkeypatch, capsys):
    from evrakci.cli import ocr as cli_ocr

    def no_rapidocr(*args):
        raise ModuleNotFoundError("No module named 'rapidocr'")  # as in the installed app

    monkeypatch.setattr(cli_ocr, "official_model", no_rapidocr)
    monkeypatch.setattr(cli_ocr, "_download_tessdata", lambda variant: True)
    assert cli_ocr.download_models(None, None) == 0
    out = capsys.readouterr().out
    assert "RapidOCR kurulu değil" in out and "No module" not in out


# --- 13, 17: comparison script and fonts ---------------------------------------------

def test_comparison_refuses_an_empty_pdf(tmp_path):
    import pikepdf

    from evrakci.cli.errors import UserError
    from evrakci.cli.ocr import _real_report

    empty = tmp_path / "bos.pdf"
    pdf = pikepdf.new()
    pdf.save(empty)
    with pytest.raises(UserError, match="sayfa yok|açılamadı"):  # never an IndexError
        _real_report([empty], [], [])


def test_comparison_renders_pages_one_at_a_time(tmp_path, monkeypatch):
    from evrakci.cli import ocr as cli_ocr

    pdf = make_pdf(tmp_path / "a.pdf", [a4_300([]), a4_300([]), a4_300([])], dpi=72)
    alive = []

    class Engine:
        name = "sahte"

        def available(self):
            return None

        def read_region(self, image):
            from evrakci.pipeline.ocr.engine import Reading

            return Reading("", 0.0)

        def read_page(self, image):
            alive.append(len(cli_ocr._RENDERED))
            return []

    cli_ocr._real_report([pdf], [], [Engine()])
    assert max(alive) <= 1


def test_missing_font_is_a_turkish_message(monkeypatch):
    from evrakci.pipeline.ocr import synthetic

    monkeypatch.setitem(synthetic._FONT_CANDIDATES, False, ["/yok/font.ttf"])
    with pytest.raises(EngineUnavailable, match="Yazı tipi bulunamadı"):
        synthetic.find_font()


def test_windows_fonts_come_from_windir(monkeypatch):
    from evrakci.pipeline.ocr import synthetic

    monkeypatch.setenv("WINDIR", r"D:\Win")
    assert any(c.startswith(r"D:\Win\Fonts") for c in synthetic.font_candidates(False))


def test_window_app_gives_child_programs_a_hidden_console():
    from evrakci import app

    calls = []

    class Kernel:
        def GetConsoleWindow(self):
            calls.append("get")
            return 0 if len(calls) == 1 else 42

        def AllocConsole(self):
            calls.append("alloc")
            return 1

    class User:
        def ShowWindow(self, hwnd, mode):
            calls.append(("show", hwnd, mode))

    assert app.hide_console_for_children(windows=True, frozen=True,
                                         kernel32=Kernel(), user32=User())
    assert calls == ["get", "alloc", "get", ("show", 42, 0)]
    assert not app.hide_console_for_children(windows=False, frozen=True)
    assert not app.hide_console_for_children(windows=True, frozen=False)
