"""Read values: plain data with no imaging dependencies, so jobs can load them cheaply."""

from __future__ import annotations

from dataclasses import dataclass

EMIN_AT = 0.90  # at or above: Emin; below (and not flagged): Orta


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


def value_level(value: VariableValue | None) -> str:
    """Güven level of a value: "emin", "orta", "kontrol", "okunamadi" or "okunmadi" (None)."""
    if value is None:
        return "okunmadi"
    if not value.flagged:
        return "emin" if value.edited or value.confidence >= EMIN_AT else "orta"
    if not value.suggestion and not value.value and not any(r.text for r in value.readings):
        return "okunamadi"
    return "kontrol"


def read_text(value: VariableValue) -> tuple[str, int | None]:
    """What was read for a flagged value (its text, else the first reading), and its box."""
    if value.value:
        return value.value, value.section
    for reading in sorted(value.readings, key=lambda r: r.section):
        if reading.text:
            return reading.text, reading.section
    return value.suggestion, None


def suggestion_reading(value: VariableValue) -> tuple[int | None, float | None]:
    """The box and the score the suggestion was read with (best other reading if none agree)."""
    matches = [r for r in value.readings if r.text == value.suggestion]
    if not matches:
        read = [r for r in value.readings if r.text]
        return (None, max(r.confidence for r in read)) if read else (None, None)
    best = max(matches, key=lambda r: r.confidence)
    return best.section, best.confidence


def box_section(value: VariableValue) -> int | None:
    """The section (box) the value shown on screen comes from; None when it has none."""
    if not value.flagged:
        return value.section
    if value_level(value) == "okunamadi":
        return None
    section, _ = suggestion_reading(value)
    return section if section is not None else read_text(value)[1]
