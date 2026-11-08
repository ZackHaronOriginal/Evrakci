"""Plan 2 fresh-review findings."""

import pytest
from fakes import make_pdf, text_page

from evrakci.pipeline.ocr import tesseract
from evrakci.pipeline.ocr.engine import EngineUnavailable


def test_configured_data_folders_are_never_deleted(tmp_path, monkeypatch):
    folder = tmp_path / "admin-tessdata"
    folder.mkdir()
    (folder / "tur.traineddata").write_bytes(b"x")  # a different file the admin chose
    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(folder))
    assert tesseract.verify_tessdata("best", folder) is False
    assert (folder / "tur.traineddata").exists()


def test_wrong_downloads_in_the_apps_own_folder_are_removed(tmp_path, monkeypatch):
    monkeypatch.delenv("EVRAKCI_TESSDATA_BEST", raising=False)
    monkeypatch.setattr(tesseract, "data_dir", lambda: tmp_path)
    folder = tmp_path / "tessdata_best"
    folder.mkdir()
    (folder / "tur.traineddata").write_bytes(b"broken")
    assert tesseract.verify_tessdata("best", folder) is False
    assert not (folder / "tur.traineddata").exists()


def test_no_tesseract_means_system_data_not_a_configs_error(monkeypatch):
    monkeypatch.setattr(tesseract, "find_tesseract", lambda: None)
    monkeypatch.setattr(tesseract, "verify_tur_best", lambda folder: True)
    assert tesseract.default_tessdata() == tesseract.TessData("tur", None)


def test_export_without_tesseract_names_the_option_even_with_tur_best(tmp_path, capsys,
                                                                      monkeypatch):
    from evrakci.cli import jobs, main

    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    assert main(["--kok", str(root), "is", "olustur", "T", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]

    def broken():
        raise EngineUnavailable("Tesseract ayar dosyaları bulunamadı (configs)")

    class Missing:
        def available(self):
            return "Tesseract programı bulunamadı"

    monkeypatch.setattr(jobs, "default_tessdata", broken)
    monkeypatch.setattr(jobs, "default_engine", lambda: Missing())
    assert main(["--kok", str(root), "is", "disa-aktar", job_id, "--cikti",
                 str(tmp_path / "out")]) == 2
    assert "--metin-katmani-yok" in capsys.readouterr().err


def test_downloads_continue_after_one_variant_fails(tmp_path, monkeypatch, capsys):
    from evrakci.cli import ocr

    calls = []

    def flaky(variant):
        calls.append(variant)
        raise EngineUnavailable("Tesseract ayar dosyaları bulunamadı")

    monkeypatch.setattr(ocr, "verify_tessdata", lambda variant, folder: True)
    monkeypatch.setattr(ocr, "tessdata_dir", lambda variant: tmp_path / variant)
    monkeypatch.setattr(ocr, "prepare_tessdata", lambda folder: flaky(folder.name))
    results = [ocr._download_tessdata(v) for v in ("fast", "standard", "best")]
    assert results == [False, False, False] and len(calls) == 3


def test_a_download_is_checked_before_it_replaces_anything(tmp_path, monkeypatch):
    import io

    from evrakci.cli import ocr

    folder = tmp_path / "best"
    monkeypatch.setattr(ocr, "tessdata_dir", lambda variant: folder)
    monkeypatch.setattr(ocr.urllib.request, "urlopen", lambda url, timeout: io.BytesIO(b"bad"))
    moved = []
    real_replace = type(folder).replace
    monkeypatch.setattr(type(folder), "replace",
                        lambda self, target: moved.append(self.name) or real_replace(self, target))
    assert ocr._download_tessdata("best") is False
    assert not (folder / "tur.traineddata").exists()
    assert moved == []  # an unverified download never takes the real name


def test_unexpected_ocr_errors_become_a_turkish_message(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr import textlayer

    monkeypatch.setattr(textlayer, "find_tesseract", lambda: tmp_path / "tesseract")
    monkeypatch.setattr(textlayer, "default_tessdata", lambda: tesseract.TessData("tur", None))

    def boom(*args, **kwargs):
        raise RuntimeError("iç hata")

    monkeypatch.setattr(textlayer, "_run", boom)
    with pytest.raises(EngineUnavailable, match="Metin katmanı eklenemedi"):
        textlayer.add_text_layer(tmp_path / "a.pdf", tmp_path / "b.pdf")


def test_verify_uses_the_hash_cache(tmp_path, monkeypatch):
    folder = tmp_path / "best"
    folder.mkdir()
    (folder / "tur.traineddata").write_bytes(b"data")
    seen = []
    monkeypatch.setattr(tesseract, "_file_hash", lambda path: seen.append(path) or "nope")
    monkeypatch.setattr(tesseract, "data_dir", lambda: tmp_path / "elsewhere")
    tesseract.verify_tessdata("best", folder)
    assert seen


def test_ocr_overwrite_keeps_the_old_file_when_ocr_fails(tmp_path, monkeypatch):
    from evrakci.cli import main, ocr

    src = make_pdf(tmp_path / "in.pdf", [text_page()])
    out = tmp_path / "out.pdf"
    out.write_bytes(b"old output")

    def failing(source, destination, pdfa=True):
        destination.write_bytes(b"half")
        raise EngineUnavailable("Metin katmanı eklenemedi")

    monkeypatch.setattr(ocr, "add_text_layer", failing)
    assert main(["ocr", str(src), str(out), "--uzerine-yaz"]) == 2
    assert out.read_bytes() == b"old output"
