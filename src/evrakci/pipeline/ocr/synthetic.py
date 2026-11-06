"""Synthetic Turkish test pages with known text and boxes, for comparing OCR engines.

These are benchmark generators, not document kinds: every word is invented.
"""

from __future__ import annotations

import io
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

_FONT_CANDIDATES = {
    False: [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ],
    True: [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        r"C:\Windows\Fonts\times.ttf",
        "/Library/Fonts/Times New Roman.ttf",
        "/System/Library/Fonts/Times.ttc",
    ],
}

_ONSETS = "b c ç d f g h k l m n p r s ş t v y z".split()
_VOWELS = "a e ı i o ö u ü".split()
_CODAS = ["", "", "n", "r", "l", "k", "ş", "ğ", "t", "z", "m", "y"]

Box = tuple[int, int, int, int]


def find_font(serif: bool = False) -> Path:
    for candidate in _FONT_CANDIDATES[serif]:
        if Path(candidate).is_file():
            return Path(candidate)
    raise FileNotFoundError(f"No {'serif' if serif else 'sans'} font found on {sys.platform}")


@dataclass(frozen=True)
class TruthBox:
    text: str
    box: Box


@dataclass
class SyntheticPage:
    image: Image.Image
    fields: list[TruthBox] = field(default_factory=list)
    words: list[TruthBox] = field(default_factory=list)


def _word(rng: random.Random) -> str:
    syllables = rng.randint(1, 4)
    word = "".join(
        rng.choice(_ONSETS) + rng.choice(_VOWELS) + rng.choice(_CODAS) for _ in range(syllables)
    )
    style = rng.random()
    if style < 0.2:
        return word.replace("i", "İ").replace("ı", "I").upper()  # Turkish upper case
    if style < 0.6:
        head = {"i": "İ", "ı": "I"}.get(word[0], word[0].upper())
        return head + word[1:]
    return word


def _token(rng: random.Random) -> str:
    kind = rng.random()
    if kind < 0.15:
        return str(rng.randint(10, 999999))
    if kind < 0.22:
        return f"{rng.randint(1, 28):02d}.{rng.randint(1, 12):02d}.{rng.randint(1990, 2030)}"
    if kind < 0.27:
        return f"{rng.randint(100, 999)}-{rng.randint(1000, 9999)}"
    return _word(rng)


def _rotate_box(box: Box, angle: float, size: tuple[int, int]) -> Box:
    """The bounding box of `box` after rotating the image by `angle` degrees about its centre."""
    cx, cy = size[0] / 2, size[1] / 2
    rad = math.radians(-angle)  # PIL rotates counter-clockwise for positive angles
    cos, sin = math.cos(rad), math.sin(rad)
    xs, ys = [], []
    for x, y in ((box[0], box[1]), (box[2], box[1]), (box[0], box[3]), (box[2], box[3])):
        dx, dy = x - cx, y - cy
        xs.append(cx + dx * cos - dy * sin)
        ys.append(cy + dx * sin + dy * cos)
    return (
        max(0, math.floor(min(xs))),
        max(0, math.floor(min(ys))),
        min(size[0], math.ceil(max(xs))),
        min(size[1], math.ceil(max(ys))),
    )


def make_pages(
    count: int,
    seed: int = 0,
    dpi: int = 300,
    degrade: bool = True,
    max_skew: float = 0.7,
    skew: float | None = None,
) -> list[SyntheticPage]:
    """Pages are the same for a seed whether or not they are degraded.

    `skew` fixes the rotation; otherwise it is random within `max_skew` degrees.
    """
    rng = random.Random(seed)
    width, height = round(210 / 25.4 * dpi), round(297 / 25.4 * dpi)
    mm = dpi / 25.4
    pages = []
    for index in range(count):
        image = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(image)
        page = SyntheticPage(image)
        y = round(25 * mm)
        for _ in range(rng.randint(8, 12)):
            text = " ".join(_token(rng) for _ in range(rng.randint(1, 4)))
            size_pt = rng.uniform(9, 14)
            serif = rng.random() < 0.4
            font = ImageFont.truetype(str(find_font(serif)), round(size_pt * dpi / 72))
            x = round(rng.uniform(20, 60) * mm)
            left, top, right, bottom = draw.textbbox((x, y), text, font=font)
            if right > width - 20 * mm:
                continue
            draw.text((x, y), text, fill=rng.randint(0, 50), font=font)
            pad = round(2 * mm)
            page.fields.append(TruthBox(text, (left - pad, top - pad, right + pad, bottom + pad)))
            cursor = x
            for part in text.split(" "):
                wl, wt, wr, wb = draw.textbbox((cursor, y), part, font=font)
                page.words.append(TruthBox(part, (round(wl), wt, round(wr), wb)))
                cursor += draw.textlength(part + " ", font=font)
            y = bottom + round(rng.uniform(8, 18) * mm)
            if y > height - 30 * mm:
                break
        if degrade:
            scan_rng = random.Random(f"{seed}-{index}")  # never touches the content rng
            angle = skew if skew is not None else scan_rng.uniform(-max_skew, max_skew)
            page = _degrade(page, angle)
        pages.append(page)
    return pages


def _degrade(page: SyntheticPage, angle: float) -> SyntheticPage:
    """Make a clean page look scanned: skew, noise, blur and JPEG artefacts."""
    size = page.image.size
    image = page.image.rotate(angle, resample=Image.Resampling.BICUBIC, fillcolor=255)
    image = _add_noise(image, sigma=8.0)
    image = image.filter(ImageFilter.GaussianBlur(0.6))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=60)
    buffer.seek(0)
    image = Image.open(buffer).convert("L")
    return SyntheticPage(
        image,
        [TruthBox(f.text, _rotate_box(f.box, angle, size)) for f in page.fields],
        [TruthBox(w.text, _rotate_box(w.box, angle, size)) for w in page.words],
    )


def _add_noise(image: Image.Image, sigma: float) -> Image.Image:
    """Gaussian noise around each pixel's value, clipped to 0-255."""
    noise = Image.effect_noise(image.size, sigma)  # grey noise centred on 128
    mid = Image.new("L", image.size, 128)
    lighter = ImageChops.subtract(noise, mid)
    darker = ImageChops.subtract(mid, noise)
    return ImageChops.subtract(ImageChops.add(image, lighter), darker)
