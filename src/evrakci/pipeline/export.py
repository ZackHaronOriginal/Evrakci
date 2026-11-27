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
from evrakci.pipeline.job import Job, parse_page_id
from evrakci.pipeline.naming import FORBIDDEN, build_name_kept, unique_names
from evrakci.pipeline.templates.model import (
    Template,
    TemplateError,
    pattern_names,
    template_revision,
)

NOTE_INVALID = "Geçersiz karakter silindi"
NOTE_SHORTENED = "Dosya adı kısaltıldı (klasör yolu uzun)"
CHECK_SUBFOLDER = "Kontrol gerekenler"  # subfolder of the export folder for documents to check


@dataclass
class ExportItem:
    number: int
    document: Document
    name: str  # without .pdf
    template_name: str | None
    values: dict[str, str] = field(default_factory=dict)  # by variable name, for the index
    checks: list[str] = field(default_factory=list)
    pdfa: bool | None = None
    pdfa_note: str = ""  # why the file is not PDF/A; Bilgi, kept out of `checks` (B-003)
    keep: int = 0  # characters of `name` that must stay so required values survive
    sources: list[str] = field(default_factory=list)  # scan files of the pages, in order, once
    name_note: str = ""  # "" or why the written name differs from the pattern (I-39)
    folder: str = ""  # "" or the subfolder of the export folder this file goes into

    @property
    def relative(self) -> str:
        """The file's path below the export folder, with "/" ("Kontrol gerekenler/ad.pdf")."""
        return f"{self.folder}/{self.name}.pdf" if self.folder else f"{self.name}.pdf"


def sources_text(sources) -> str:
    """The Kaynak cell: the first scan file, "tarama_01.pdf +1" when the document spans more."""
    if not sources:
        return ""
    return sources[0] + (f" +{len(sources) - 1}" if len(sources) > 1 else "")


PREVIEW_HEADER = "Kaynak\tYazılacak dosya adı\tNot"


def preview_line(source: str, name: str, note: str) -> str:
    """One line of the name list (window clipboard and `--onizle`): tab separated, for Excel."""
    return f"{source}\t{name}\t{note}"


def clash_note(suffix: str) -> str:
    return f"Ad çakışması, {suffix.strip()} eklendi"


def _numbered(number: int) -> str:
    return f"belge_{number:03d}"


def plan_export(job: Job, templates: Mapping[str, Template | None]) -> list[ExportItem]:
    items = []
    file_of = {batch.id: batch.file_name for batch in job.batches}
    invalid: set[int] = set()  # documents whose pattern values lost a forbidden character
    for number, document in enumerate(compute_documents(job), start=1):
        item = ExportItem(number, document, _numbered(number), None)
        item.sources = list(dict.fromkeys(
            file_of.get(parse_page_id(pid)[0], "") for pid in document.page_ids))
        item.sources = [name for name in item.sources if name]
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
            if _lost_character(item, templates.get(template_id)):
                invalid.add(number)
        items.append(item)
    # Numbered names go first, so `belge_002` always stays document 2's own name.
    order = sorted(range(len(items)), key=lambda i: items[i].name != _numbered(i + 1))
    names = unique_names([items[i].name for i in order])
    for i, name in zip(order, names, strict=True):
        before = items[i].name
        items[i].name = name
        if name != before:
            items[i].name_note = clash_note(name[len(before):])
        elif items[i].number in invalid:
            items[i].name_note = NOTE_INVALID
    return items


def _lost_character(item: ExportItem, template) -> bool:
    """A value of the pattern held a character Windows does not allow (the name drops it)."""
    if template is None or not item.template_name or not template.filename_pattern:
        return False
    try:
        used = set(pattern_names(template.filename_pattern))
    except TemplateError:
        return False
    return any(FORBIDDEN.search(item.values.get(variable, "")) for variable in used)


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
