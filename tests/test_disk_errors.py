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
