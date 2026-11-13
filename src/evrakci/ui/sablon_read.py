"""Live reading for Şablonlar: what a box reads, how sure it is, and the worker that reads the
example documents with the template as it is now (the same `read_document` the export uses).

The levels are the app's one vocabulary (Emin / Orta / Kontrol / Okunamadı, plus Okunmadı while
nothing has been read): icon + word + colour, never colour alone.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from evrakci.pipeline.job import parse_page_id
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.render import render_page
from evrakci.pipeline.templates.model import Template
from evrakci.pipeline.templates.read import read_document
from evrakci.pipeline.templates.values import VariableValue

READ_DPI = 300
EMIN_AT = 0.90  # at or above (and above the template's threshold): Emin; else Orta

# level -> (Lucide icon, QLabel `state` property, word)
LEVELS = {
    "emin": ("signal-high", "ok", "Emin"),
    "orta": ("signal-medium", "orta", "Orta"),
    "kontrol": ("triangle-alert", "kontrol", "Kontrol"),
    "okunamadi": ("circle-x", "bad", "Okunamadı"),
    "okunmadi": ("clock", "orta", "Okunmadı"),
}
NEEDS_CHECK = ("kontrol", "okunamadi")


def level_of(text: str, confidence: float, minimum: float) -> str:
    """Okunamadı without text; Kontrol below the template's threshold; Emin from 90 %."""
    if not text:
        return "okunamadi"
    if confidence < minimum:
        return "kontrol"
    return "emin" if confidence >= max(EMIN_AT, minimum) else "orta"


@dataclass(frozen=True)
class Shown:
    """What the inspector's "Okunan" card shows for a box (or a whole variable)."""

    text: str
    level: str
    percent: int | None
    note: str = ""


NOT_READ = Shown("", "okunmadi", None)
NO_BOX = Shown("", "okunmadi", None, "Kutu çizilince okunur.")


def tried(value: VariableValue) -> bool:
    """False for a variable nothing was read for (it has no box yet): no section was tried,
    so "Kontrol" would be a false alarm (D1: orange only for a real check)."""
    return bool(value.readings) or bool(value.value) or bool(value.suggestion)


def shown_for(value: VariableValue | None, section: int | None, minimum: float) -> Shown:
    """The reading of one section, or of the variable when `section` is None."""
    if value is None:
        return NOT_READ
    if not tried(value):
        return NO_BOX
    if section is not None:
        reading = next((r for r in value.readings if r.section == section), None)
        if reading is None:
            return Shown("", "okunmadi", None, "Önceki bölüm emin okuduğu için denenmedi.")
        note = reading.problem or ""
        level = level_of(reading.text, reading.confidence, minimum)
        return Shown(reading.text, level, round(reading.confidence * 100) if reading.text
                     else None, note)
    if value.flagged:
        text = value.suggestion
        return Shown(text, "kontrol", None,
                     "Emin olunamadı; Değerler sekmesinde kontrol edilir.")
    return Shown(value.value, level_of(value.value, value.confidence, minimum),
                 round(value.confidence * 100))


def lines(template: Template, values: dict[str, VariableValue]) -> list[str]:
    """One line per read variable, as the live panel has always worded them."""
    out = []
    for variable in template.variables:
        value = values.get(variable.key)
        if value is None or not tried(value):
            continue
        if value.flagged:
            text = f"Kontrol · {variable.name}: emin değil"
            if value.suggestion:
                text += f" (öneri {value.suggestion})"
        else:
            section = "Bölüm 1" if not value.section else f"Varyant {value.section + 1}"
            text = f"{variable.name} · {section}: {value.value}   %{round(value.confidence * 100)}"
        out.append(text)
    return out


def flagged_count(values: dict[str, VariableValue]) -> int:
    """Reads that need a check (a variable with no box was not read and is not counted)."""
    return sum(1 for v in values.values() if v.flagged and tried(v))


@dataclass(frozen=True)
class ReadInput:
    """Everything the worker needs, copied on the window thread."""

    template: Template
    documents: dict[int, tuple[str, ...]]  # example number -> its page ids
    files: dict[str, Path]
    rotations: dict[str, int]
    engine: object


def read_examples(job: ReadInput, numbers: list[int],
                  progress: Callable[[int, int], None] | None = None
                  ) -> dict[int, dict[str, VariableValue]]:
    """Read the given examples one after the other (cancellable through `progress`)."""
    engine = job.engine
    reason = engine.available()
    if reason:
        raise EngineUnavailable(reason)
    out: dict[int, dict[str, VariableValue]] = {}
    for done, number in enumerate(numbers):
        if progress is not None:
            progress(done, len(numbers))
        page_ids = job.documents[number]

        def page_image(index: int, page_ids=page_ids):
            pid = page_ids[index]
            batch_id, page = parse_page_id(pid)
            return render_page(job.files[batch_id], page, job.rotations.get(pid, 0),
                               dpi=READ_DPI)

        out[number] = read_document(job.template, len(page_ids), page_image, engine)
    if progress is not None:
        progress(len(numbers), len(numbers))
    return out
