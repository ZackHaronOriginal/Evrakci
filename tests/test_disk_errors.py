"""E-3: the disk's errors reach the user as Turkish sentences, the same in the window and the
command line (both print what `export_job` raises)."""
from __future__ import annotations

import errno
from pathlib import Path

import pytest
from test_export_review2 import plain_job

from evrakci.pipeline import exporting
from evrakci.pipeline.disk_errors import disk_reason
from evrakci.pipeline.exporting import ExportError, export_job

OUT = Path("/cikti")


@pytest.mark.parametrize(("error", "text"), [
    (FileExistsError("48192_Ege Kalıp.pdf"),
     "Hedef klasörde aynı adlı dosya var: 48192_Ege Kalıp.pdf."),
    (PermissionError(errno.EACCES, "Permission denied", "/cikti/a.pdf"),
     "Klasöre yazma izni yok."),
    (OSError(errno.EROFS, "Read-only file system", "/cikti/a.pdf"), "Klasöre yazma izni yok."),
    (FileNotFoundError(errno.ENOENT, "No such file or directory", "/cikti/a.pdf"),
     "Klasör bulunamadı."),
    (FileNotFoundError(errno.ENOENT, "No such file or directory", "/is/tarama_1.pdf"),
     "Taranan dosya bulunamadı: tarama_1.pdf."),
    (OSError(errno.ENOSPC, "No space left on device"), "Diskte yer kalmadı."),
    (NotADirectoryError(errno.ENOTDIR, "Not a directory", "/cikti/x"),
     "Yolun bir bölümü klasör değil, dosya."),
    (OSError(errno.EIO, "Input/output error"), "Disk beklenmeyen bir hata verdi."),
])
def test_an_os_error_becomes_a_turkish_sentence(error, text):
    assert disk_reason(error, OUT) == text


def _fails_with(monkeypatch, error):
    def broken(*_a, **_k):
        raise error

    monkeypatch.setattr(exporting, "write_documents", broken)


@pytest.mark.parametrize(("error", "said", "advice"), [
    (PermissionError(errno.EACCES, "Permission denied"), "Klasöre yazma izni yok.",
     "Sorunu giderip"),
    (OSError(errno.ENOSPC, "No space left on device"), "Diskte yer kalmadı.", "Yer açıp"),
])
def test_export_says_why_the_files_could_not_be_written(tmp_path, monkeypatch, error, said,
                                                        advice):
    store, job = plain_job(tmp_path)
    _fails_with(monkeypatch, error)
    with pytest.raises(ExportError) as caught:
        export_job(job, store.batch_files(job), {}, tmp_path / "cikti", with_layer=False)
    text = str(caught.value)
    assert said in text and advice in text and "index.xlsx yazılmadı" in text
    assert "Permission" not in text and "No space" not in text and "Errno" not in text


def test_a_free_space_hint_is_not_given_for_a_permission_error(tmp_path, monkeypatch):
    store, job = plain_job(tmp_path)
    _fails_with(monkeypatch, PermissionError(errno.EACCES, "Permission denied"))
    with pytest.raises(ExportError) as caught:
        export_job(job, store.batch_files(job), {}, tmp_path / "cikti", with_layer=False)
    assert "yer açıp" not in str(caught.value).lower()


# -- review round 1 ------------------------------------------------------------------------
def test_a_name_too_long_uses_the_path_length_sentence():
    error = OSError(errno.ENAMETOOLONG, "File name too long", "/cikti/uzun.pdf")
    assert disk_reason(error, OUT) == "Çıktı klasörünün yolu çok uzun; daha kısa bir klasör seçin."


def test_a_file_another_program_holds_is_not_a_folder_permission_error(tmp_path):
    held = tmp_path / "acik.pdf"
    held.write_bytes(b"x")
    denied = PermissionError(errno.EACCES, "Permission denied", str(held))
    assert disk_reason(denied, tmp_path) == "Dosya başka bir programda açık olabilir: acik.pdf."
    busy = OSError(errno.EBUSY, "Device or resource busy", str(held))
    assert disk_reason(busy, tmp_path) == "Dosya başka bir programda açık olabilir: acik.pdf."
    sharing = PermissionError(errno.EACCES, "x", str(tmp_path / "yok.pdf"))
    sharing.winerror = 32
    assert disk_reason(sharing, tmp_path).startswith("Dosya başka bir programda açık")
    # a real folder permission error keeps the folder sentence
    assert disk_reason(PermissionError(errno.EACCES, "x", str(tmp_path)), tmp_path) == \
        "Klasöre yazma izni yok."


def test_a_missing_file_inside_an_existing_folder_is_not_a_missing_folder(tmp_path):
    error = FileNotFoundError(errno.ENOENT, "No such file", str(tmp_path / "a.pdf"))
    assert disk_reason(error, tmp_path) == "Taranan dosya bulunamadı: a.pdf."
    gone = FileNotFoundError(errno.ENOENT, "No such file", str(tmp_path / "yok" / "a.pdf"))
    assert disk_reason(gone, tmp_path / "yok") == "Klasör bulunamadı."


def test_an_existing_folder_with_a_file_name_is_a_clash(tmp_path):
    (tmp_path / "a.pdf").mkdir()
    error = FileExistsError(errno.EEXIST, "File exists", str(tmp_path / "a.pdf"))
    assert disk_reason(error, tmp_path) == "Bir dosya adı, aynı adlı klasörle çakışıyor: a.pdf."


def test_an_unmapped_error_keeps_its_technical_detail(tmp_path, monkeypatch):
    store, job = plain_job(tmp_path)
    _fails_with(monkeypatch, OSError(errno.EIO, "Input/output error", str(tmp_path / "x.pdf")))
    with pytest.raises(ExportError) as caught:
        export_job(job, store.batch_files(job), {}, tmp_path / "cikti", with_layer=False)
    assert "Disk beklenmeyen bir hata verdi. (EIO: x.pdf)" in str(caught.value)


def test_a_corrupt_scan_names_its_file(tmp_path):
    store, job = plain_job(tmp_path)
    files = store.batch_files(job)
    path = next(iter(files.values()))
    path.write_bytes(b"bozuk")
    with pytest.raises(ExportError) as caught:
        export_job(job, files, {}, tmp_path / "cikti", with_layer=False)
    assert f"Taranan dosya okunamadı: {path.name}." in str(caught.value)
