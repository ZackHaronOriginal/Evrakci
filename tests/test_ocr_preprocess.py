from fakes import render_line
from PIL import Image

from evrakci.pipeline.ocr.preprocess import binarize, estimate_skew, prepare_region


def test_estimate_skew_of_rotated_line():
    image = Image.new("L", (900, 300), 255)
    image.paste(render_line("Örnek Kayıt Şişli Çağrı 2026", 40), (40, 100))
    rotated = image.rotate(2.0, fillcolor=255, expand=False)
    assert abs(estimate_skew(rotated) - 2.0) < 0.4


def test_binarize_is_two_level():
    image = render_line("Kayıt", 40).point(lambda v: 60 if v < 128 else 230)
    assert set(binarize(image).tobytes()) <= {0, 255}


def test_prepare_region_keeps_size_when_straight():
    image = render_line("Kayıt 2026", 40)
    assert prepare_region(image).size == image.size
