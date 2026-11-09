"""Plan an export: each document's file name, its values and why it may need a check."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from evrakci.pipeline.cuts import (
    Document,
    compute_documents,
    current_read_error,
    current_values,
    document_template,
)
from evrakci.pipeline.job import Job
from evrakci.pipeline.naming import build_name_kept, unique_names
from evrakci.pipeline.templates.model import Template, template_revision


@dataclass
class ExportItem:
    number: int
    document: Document
    name: str  # without .pdf
    template_name: str | None
    values: dict[str, str] = field(default_factory=dict)  # by variable name, for the index
    checks: list[str] = field(default_factory=list)
    pdfa: bool | None = None
    keep: int = 0  # characters of `name` that must stay so required values survive


def _numbered(number: int) -> str:
    return f"belge_{number:03d}"


def plan_export(job: Job, templates: Mapping[str, Template | None]) -> list[ExportItem]:
    items = []
    for number, document in enumerate(compute_documents(job), start=1):
        item = ExportItem(number, document, _numbered(number), None)
        if "leftover" in document.flags:
            item.checks.append("eksik sayfa")
        template_id, _ = document_template(job, document)
        if "mixed_templates" in document.flags:
            item.checks.append("karışık şablon" if template_id is not None
                               else "karışık şablon (ilk sayfada şablon yok)")
        error = current_read_error(job, document)
        if error:
            item.checks.append(error)
        if template_id is not None:
            _apply_template(item, job, document, templates.get(template_id))
        items.append(item)
    # Numbered names go first, so `belge_002` always stays document 2's own name.
    order = sorted(range(len(items)), key=lambda i: items[i].name != _numbered(i + 1))
    names = unique_names([items[i].name for i in order])
    for i, name in zip(order, names, strict=True):
        items[i].name = name
    return items


def _apply_template(item: ExportItem, job: Job, document: Document, template) -> None:
    if template is None:
        item.checks.append("şablon bulunamadı")
        return
    item.template_name = template.name
    stored = current_values(job, document)
    if stored is None:
        item.checks.append("değerler okunmadı")
        return
    source = job.value_sources.get(document.page_ids[0])
    if source is not None and source.revision and source.revision != template_revision(template):
        item.checks.append("şablon değişti; yeniden okunmalı")
    by_name = {v.name: stored[v.key] for v in template.variables if v.key in stored}
    item.values = {
        v.name: by_name[v.name].value if v.name in by_name else "" for v in template.variables
    }
    required = {v.name for v in template.variables if v.required}
    name, checks, keep = build_name_kept(template.filename_pattern, by_name, required)
    in_pattern = set(checks)
    # Required or unsure variables outside the pattern still need a look.
    for variable in template.variables:
        value = by_name.get(variable.name)
        missing = value is None or value.flagged or not value.value.strip()
        if variable.required and missing:
            reason = f"zorunlu değer eksik: {variable.name}"
            if reason not in in_pattern:
                checks.append(reason)
            name = None
        elif value is None:  # added to the template after this document was read
            checks.append(f"okunmadı: {variable.name}")
        elif value.flagged and f"okunamadı: {variable.name}" not in in_pattern:
            checks.append(f"okunamadı: {variable.name}")
    item.checks.extend(checks)
    if not template.filename_pattern.strip():
        item.checks.append("dosya adı kalıbı yok")
    elif name == "":
        item.checks.append("dosya adı boş kaldı")
    if name:
        item.name = name
        item.keep = keep
