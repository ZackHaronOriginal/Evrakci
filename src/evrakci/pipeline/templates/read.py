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
from evrakci.pipeline.templates.values import SectionReading, VariableValue

__all__ = ["NO_PAGE", "OUTSIDE", "ExampleWeakness", "SectionReading", "VariableValue",
           "flagged_count", "read_document", "tried", "weakest_examples"]

NO_PAGE = "sayfa yok"
OUTSIDE = "kutu sayfa dışında"


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
    # Values are keyed by each variable's permanent key, so renaming never loses them.
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
            values[variable.key] = VariableValue(
                chosen.text, chosen.confidence, chosen.section, False, "", tuple(readings)
            )
        else:
            best = max((r for r in readings if r.text), key=lambda r: r.confidence, default=None)
            values[variable.key] = VariableValue(
                "", 0.0, None, True, best.text if best else "", tuple(readings)
            )
    return values


def tried(value: VariableValue) -> bool:
    """False for a variable nothing was read for (it has no box yet): no section was tried,
    so "Kontrol" would be a false alarm."""
    return bool(value.readings) or bool(value.value) or bool(value.suggestion)


def flagged_count(values: dict[str, VariableValue]) -> int:
    """Reads that need a check (a variable with no box was not read and is not counted)."""
    return sum(1 for v in values.values() if v.flagged and tried(v))


@dataclass(frozen=True)
class ExampleWeakness:
    """One example document that has reads needing a check."""

    number: int
    flagged: int
    lowest_confidence: float  # best reading of the least sure flagged variable (0 to 1)


def _best_confidence(value: VariableValue) -> float:
    return max((r.confidence for r in value.readings if r.text), default=0.0)


def weakest_examples(results: dict[int, dict[str, VariableValue]],
                     limit: int | None = None) -> list[ExampleWeakness]:
    """The examples with reads that need a check, worst first: most flagged reads, then the
    lowest confidence, then the example number. Examples with none are left out."""
    weak = []
    for number, values in results.items():
        flagged = [v for v in values.values() if v.flagged and tried(v)]
        if flagged:
            weak.append(ExampleWeakness(number, len(flagged),
                                        min(_best_confidence(v) for v in flagged)))
    weak.sort(key=lambda w: (-w.flagged, w.lowest_confidence, w.number))
    return weak if limit is None else weak[:limit]
