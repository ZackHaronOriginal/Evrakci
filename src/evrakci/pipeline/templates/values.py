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
