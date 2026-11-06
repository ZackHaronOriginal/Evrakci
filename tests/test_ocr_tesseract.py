import pytest
from conftest import needs_tesseract
from fakes import render_line

from evrakci.pipeline.ocr.tesseract import TesseractEngine


@needs_tesseract
def test_reads_turkish_region():
    reading = TesseractEngine().read_region(render_line("İSTANBUL Şişli Çağrı Öğün ığdır"))
    assert reading.text == "İSTANBUL Şişli Çağrı Öğün ığdır" and reading.confidence > 0.5


@needs_tesseract
def test_page_words_have_boxes():
    words = TesseractEngine().read_page(render_line("Kayıt 2026"))
    assert [w.text for w in words] == ["Kayıt", "2026"]
    assert all(w.box[2] > w.box[0] and w.box[3] > w.box[1] for w in words)


def test_missing_language_reported(tmp_path):
    assert "dil" in (TesseractEngine(lang="tur", tessdata_dir=tmp_path).available() or "")


@needs_tesseract
def test_separate_tessdata_folder_with_only_the_language_file(tmp_path):
    import shutil

    from evrakci.pipeline.ocr.tesseract import system_tessdata

    shutil.copy(system_tessdata() / "tur.traineddata", tmp_path / "tur.traineddata")
    reading = TesseractEngine(tessdata_dir=tmp_path).read_region(render_line("Kayıt Şişli 2026"))
    assert reading.text == "Kayıt Şişli 2026"


def test_tessdata_best_env(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import tessdata_best_dir

    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(tmp_path))
    assert tessdata_best_dir() == tmp_path


def test_tur_best_checksum_checked(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import TUR_BEST_SHA256, verify_tur_best

    (tmp_path / "tur.traineddata").write_bytes(b"truncated")
    assert len(TUR_BEST_SHA256) == 64 and verify_tur_best(tmp_path) is False
    assert not (tmp_path / "tur.traineddata").exists()


@needs_tesseract
def test_prepare_tessdata_copies_configs(tmp_path):
    import shutil

    from evrakci.pipeline.ocr.tesseract import prepare_tessdata, system_tessdata

    shutil.copy(system_tessdata() / "tur.traineddata", tmp_path)
    prepare_tessdata(tmp_path)
    assert (tmp_path / "configs" / "hocr").is_file()


def test_default_falls_back_to_system(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import TessData, default_tessdata

    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(tmp_path / "none"))
    assert default_tessdata() == TessData("tur", None)


def test_default_engine_uses_default_tessdata(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import default_engine

    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(tmp_path / "none"))
    engine = default_engine()
    assert engine.lang == "tur" and engine.tessdata_dir is None


def test_official_variants_have_pinned_checksums():
    from evrakci.pipeline.ocr.tesseract import TESSDATA_VARIANTS

    assert set(TESSDATA_VARIANTS) == {"fast", "standard", "best"}
    for variant in TESSDATA_VARIANTS.values():
        assert len(variant.sha256) == 64 and variant.url.startswith(
            "https://raw.githubusercontent.com/tesseract-ocr/"
        )


def test_variant_dir_and_verification(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import tessdata_dir, verify_tessdata

    monkeypatch.setenv("EVRAKCI_TESSDATA_FAST", str(tmp_path))
    assert tessdata_dir("fast") == tmp_path
    (tmp_path / "tur.traineddata").write_bytes(b"x")
    assert verify_tessdata("fast") is False and not (tmp_path / "tur.traineddata").exists()


def test_comparison_lists_all_official_variants():
    from evrakci.cli.ocr import all_engines

    names = [engine.name for engine in all_engines()]
    for name in ("tesseract-tur_fast", "tesseract-tur_standard", "tesseract-tur_best"):
        assert name in names


def test_prepare_tessdata_fails_loudly(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr import tesseract
    from evrakci.pipeline.ocr.engine import EngineUnavailable

    monkeypatch.setattr(tesseract, "system_tessdata", lambda: None)
    with pytest.raises(EngineUnavailable, match="ayar dosyaları"):
        tesseract.prepare_tessdata(tmp_path)


@needs_tesseract
def test_system_tessdata_ignores_prefix(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import system_tessdata

    real = system_tessdata()
    monkeypatch.setenv("TESSDATA_PREFIX", str(tmp_path))
    assert system_tessdata() == real


def test_ascii_safe_folder_rules(tmp_path):
    from evrakci.pipeline.ocr.tesseract import ascii_safe_dir

    plain = tmp_path / "veri"
    plain.mkdir()
    assert ascii_safe_dir(plain, windows=True) == plain  # already ASCII: unchanged
    turkish = tmp_path / "Şükrü"
    turkish.mkdir()
    (turkish / "tur.traineddata").write_bytes(b"x")
    assert ascii_safe_dir(turkish, windows=False) == turkish  # only Windows needs this
    short = tmp_path / "SUKRU~1"
    assert ascii_safe_dir(turkish, windows=True, short_path=lambda p: short) == short
    copy_root = tmp_path / "ProgramData"
    copied = ascii_safe_dir(turkish, windows=True, short_path=lambda p: p, copy_root=copy_root)
    assert str(copied).isascii() and (copied / "tur.traineddata").read_bytes() == b"x"


def test_iss_installs_to_ascii_folder():
    from pathlib import Path

    iss = (Path(__file__).resolve().parents[1] / "packaging" / "evrakci.iss").read_text(
        encoding="utf-8-sig"
    )
    line = next(line for line in iss.splitlines() if line.startswith("DefaultDirName="))
    assert line.isascii()


def test_ascii_copy_is_atomic_and_follows_content(tmp_path):
    from evrakci.pipeline.ocr.tesseract import ascii_safe_dir

    source = tmp_path / "Şükrü"
    source.mkdir()
    (source / "tur.traineddata").write_bytes(b"one")
    root = tmp_path / "kok"
    (root / "tessdata-yarim.tmp").mkdir(parents=True)  # a copy that was cut off earlier
    first = ascii_safe_dir(source, windows=True, short_path=lambda p: p, copy_root=root)
    assert (first / "tur.traineddata").read_bytes() == b"one"
    assert ascii_safe_dir(source, windows=True, short_path=lambda p: p, copy_root=root) == first
    (source / "tur.traineddata").write_bytes(b"two")  # data downloaded again
    second = ascii_safe_dir(source, windows=True, short_path=lambda p: p, copy_root=root)
    assert second != first and (second / "tur.traineddata").read_bytes() == b"two"
    assert not any(
        p.name.endswith(".tmp") and p != root / "tessdata-yarim.tmp" for p in root.iterdir()
    )


def test_ascii_copy_root_override(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import ascii_copy_root

    monkeypatch.setenv("EVRAKCI_ASCII_KOK", str(tmp_path / "x"))
    assert ascii_copy_root() == tmp_path / "x"


def test_ascii_temp_dir(tmp_path):
    from evrakci.pipeline.ocr.textlayer import ascii_temp_dir

    assert ascii_temp_dir(windows=False, current=str(tmp_path / "Şükrü")) is None
    assert ascii_temp_dir(windows=True, current=str(tmp_path)) is None
    chosen = ascii_temp_dir(windows=True, current=str(tmp_path / "Şükrü"), root=tmp_path / "kok")
    assert str(chosen).isascii() and chosen.is_dir()


def test_bundled_hash_cached(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr import tesseract

    path = tmp_path / "tur.traineddata"
    path.write_bytes(b"abc")
    calls = []
    real = tesseract.hashlib.sha256

    def counting(data=b""):
        calls.append(1)
        return real(data)

    monkeypatch.setattr(tesseract.hashlib, "sha256", counting)
    tesseract._file_matches(path, "x")
    tesseract._file_matches(path, "x")
    assert len(calls) == 1
