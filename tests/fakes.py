"""Synthetic pages and PDFs for tests. Never use real documents."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from evrakci.pipeline.analyze import PageInfo
from evrakci.pipeline.job import Batch, Job, page_id
from evrakci.pipeline.separator import render_separator_image

DPI = 100
A4 = (827, 1169)  # A4 at 100 dpi


def text_page(label: str = "") -> Image.Image:
    """A white page with dark blocks that look like lines of text."""
    page = Image.new("L", A4, 255)
    draw = ImageDraw.Draw(page)
    for row in range(12):
        top = 150 + row * 60
        draw.rectangle((100, top, 700 - (row % 3) * 80, top + 14), fill=30)
    if label:
        draw.text((100, 100), label, fill=0)
    return page


def empty_page(speckles: int = 30) -> Image.Image:
    """A white page with a few 1-px dots, like scanner dust."""
    page = Image.new("L", A4, 255)
    for i in range(speckles):
        page.putpixel(((i * 97) % A4[0], (i * 211) % A4[1]), 0)
    return page


def qr_page(scale: float = 1.0, angle: float = 0.0) -> Image.Image:
    """A separator page, optionally shrunk and rotated like a poor photocopy."""
    image = render_separator_image(dpi=DPI)
    if scale != 1.0:
        small = image.resize((round(A4[0] * scale), round(A4[1] * scale)))
        image = Image.new("L", A4, 255)
        image.paste(small, ((A4[0] - small.width) // 2, (A4[1] - small.height) // 2))
    if angle:
        image = image.rotate(angle, fillcolor=255)
    return image


def make_pdf(path: Path, pages: list[Image.Image]) -> Path:
    path = Path(path)
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=DPI)
    return path


_KINDS = {
    "p": PageInfo(0.05, False),
    "e": PageInfo(0.0, False),
    "q": PageInfo(0.02, True),
}


def job_from_kinds(spec: dict[str, str]) -> Job:
    """A job built without PDFs. Kinds per page: p text, e empty, q QR."""
    job = Job(id="test", name="test")
    for batch_id, kinds in spec.items():
        job.batches.append(Batch(batch_id, f"{batch_id}.pdf", len(kinds)))
        for index, kind in enumerate(kinds):
            job.pages[page_id(batch_id, index)] = _KINDS[kind]
    return job


def render_line(text: str, size: int = 40) -> Image.Image:
    """One line of text on white, like a cropped field."""
    from PIL import ImageFont

    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    left, top, right, bottom = font.getbbox(text)
    image = Image.new("L", (right - left + 40, bottom - top + 40), 255)
    ImageDraw.Draw(image).text((20 - left, 20 - top), text, fill=0, font=font)
    return image
