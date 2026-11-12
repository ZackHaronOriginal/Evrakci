"""Read values: plain data with no imaging dependencies, so jobs can load them cheaply."""

from __future__ import annotations

from dataclasses import dataclass


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
