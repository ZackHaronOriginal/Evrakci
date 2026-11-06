"""Read a document's variables with a template.

For each variable, sections are tried in the order the user listed them; the first
confident reading wins. If none is confident, the variable is flagged, its value is left
empty, and every reading is kept so the reviewer can choose.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image

from evrakci.pipeline.ocr.engine import OcrEngine
from evrakci.pipeline.ocr.metrics import normalize
from evrakci.pipeline.render import mm_box_to_pixels
from evrakci.pipeline.templates.model import Section, Template

NO_PAGE = "sayfa yok"
OUTSIDE = "kutu sayfa dışında"


@dataclass(frozen=True)
class SectionReading:
    section: int
    text: str
    confidence: float
    problem: str | None = None


@dataclass(frozen=True)
class VariableValue:
    value: str
    confidence: float
    section: int | None
    flagged: bool
    suggestion: str = ""
    readings: tuple[SectionReading, ...] = ()
    edited: bool = False


def _page_index(section: Section, page_count: int) -> int | None:
    index = section.page - 1 if section.page > 0 else page_count + section.page
    return index if 0 <= index < page_count else None


def read_document(
    template: Template,
    page_count: int,
    page_image: Callable[[int], Image.Image],
    engine: OcrEngine,
) -> dict[str, VariableValue]:
    images: dict[int, Image.Image] = {}

    def image(index: int) -> Image.Image:
        if index not in images:
            images[index] = page_image(index)
        return images[index]

    values = {}
    for variable in template.variables:
        readings: list[SectionReading] = []
        chosen: SectionReading | None = None
        for number, section in enumerate(variable.sections):
            index = _page_index(section, page_count)
            if index is None:
                readings.append(SectionReading(number, "", 0.0, NO_PAGE))
                continue
            page = image(index)
            box = mm_box_to_pixels(section.box_mm, page.size)
            if box is None:
                readings.append(SectionReading(number, "", 0.0, OUTSIDE))
                continue
            result = engine.read_region(page.crop(box))
            reading = SectionReading(number, normalize(result.text), result.confidence)
            readings.append(reading)
            if reading.text and reading.confidence >= template.min_confidence:
                chosen = reading
                break
        if chosen is not None:
            values[variable.name] = VariableValue(
                chosen.text, chosen.confidence, chosen.section, False, "", tuple(readings)
            )
        else:
            best = max(
                (r for r in readings if r.text), key=lambda r: r.confidence, default=None
            )
            values[variable.name] = VariableValue(
                "", 0.0, None, True, best.text if best else "", tuple(readings)
            )
    return values
