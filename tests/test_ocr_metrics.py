import pytest

from evrakci.pipeline.ocr.metrics import box_hit, cer, exact, turkish_char_errors


def test_turkish_case_never_folded():
    assert not exact("İstanbul", "istanbul") and not exact("ığdır", "iğdir")
    assert turkish_char_errors("ığdır", "iğdir") == (2, 3)


def test_nfc():
    assert exact("İ", "İ")


def test_whitespace_collapsed():
    assert exact("Kayıt  2026 ", "Kayıt 2026")


def test_empty_reading():
    assert cer("abc", "") == 1.0 and not exact("abc", "") and cer("", "") == 0.0


def test_cer_counts_edits():
    assert cer("Çağrı", "Cagri") == pytest.approx(3 / 5)


def test_box_hit():
    assert box_hit((0, 0, 10, 10), (4, 4, 8, 8))
    assert not box_hit((0, 0, 10, 10), (12, 0, 20, 5))
