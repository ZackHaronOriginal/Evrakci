"""Fixing read values: staff corrections always win over later readings."""

from __future__ import annotations

import unicodedata
from dataclasses import replace

from evrakci.pipeline.cuts import Document, current_values, record_values
from evrakci.pipeline.job import Job
from evrakci.pipeline.templates.values import VariableValue


def _values(job: Job, document: Document) -> dict[str, VariableValue]:
    values = current_values(job, document)
    if values is None:
        raise KeyError("değerler okunmadı")
    return values


def set_value(job: Job, document: Document, key: str, text: str) -> None:
    """The user's own value: confident, no longer flagged, kept on re-reading."""
    values = _values(job, document)
    if key not in values:
        raise KeyError(key)
    clean = " ".join(unicodedata.normalize("NFC", text).split())
    values[key] = VariableValue(clean, 1.0, None, False, "", (), True)


def accept_suggestion(job: Job, document: Document, key: str) -> None:
    values = _values(job, document)
    if key not in values:
        raise KeyError(key)
    value = values[key]
    if not value.flagged or not value.suggestion:
        raise ValueError("öneri yok")
    values[key] = replace(value, value=value.suggestion, confidence=1.0, flagged=False, edited=True)


def store_reading(
    job: Job, document: Document, template_id: str, values: dict[str, VariableValue]
) -> None:
    """Store freshly read values; the user's own corrections always win over a new reading."""
    values = dict(values)
    previous = current_values(job, document) or {}
    for key, old in previous.items():
        if old.edited and key in values:
            values[key] = old
    record_values(job, document, template_id, values)
