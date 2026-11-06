"""The interface every OCR engine follows."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Protocol

from PIL import Image


@dataclass(frozen=True)
class Word:
    text: str
    box: tuple[int, int, int, int]  # pixels: x0, y0, x1, y1
    confidence: float  # 0-1


@dataclass(frozen=True)
class Reading:
    text: str
    confidence: float  # 0-1


class EngineUnavailable(Exception):
    """The engine cannot run here. The message is shown to staff (Turkish)."""


class OcrEngine(Protocol):
    name: str

    def available(self) -> str | None:
        """None when usable, otherwise a Turkish reason."""

    def read_page(self, image: Image.Image) -> list[Word]: ...

    def read_region(self, image: Image.Image) -> Reading: ...


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def reading_from_words(words: list[Word]) -> Reading:
    if not words:
        return Reading("", 0.0)
    text = nfc(" ".join(w.text for w in words if w.text))
    return Reading(text, sum(w.confidence for w in words) / len(words))
