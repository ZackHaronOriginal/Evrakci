"""Değerler data without widgets: one row per document, one cell per variable value.

Everything the table, the inspector and the status bar say about a value comes from here:
its Güven level (Emin / Orta / Kontrol / Okunamadı), the percentage, whether it was
reviewed (İncelendi), which characters are uncertain and what the suggestion changes.

"İncelendi" is the core's `edited` flag: a person typed the value, accepted the suggestion
or confirmed what was read. Such a value is kept on re-reading (pipeline.review), so no new
core field is needed.
"""

from __future__ import annotations

import random
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from difflib import SequenceMatcher

from evrakci.pipeline import review
from evrakci.pipeline.cuts import (
    Document,
    current_read_error,
    current_values,
    document_template,
)
from evrakci.pipeline.job import Job
from evrakci.pipeline.templates.model import Template, Variable
from evrakci.pipeline.templates.values import VariableValue

EMIN_AT = 0.90  # at or above: Emin; below (and not flagged): Orta
SAMPLE_SIZE = 20  # Örnek kontrol: how many Emin values are checked by hand
CONFUSABLE = "OoIlBSZG"  # letters OCR mixes up with digits (0, 1, 8, 5, 2, 6)

# Güven levels: (Lucide icon, colour role, word, semibold). Status is never colour alone.
LEVELS: dict[str, tuple[str, str, str, bool]] = {
    "emin": ("signal-high", "ok", "Emin", False),
    "orta": ("signal-medium", "text-2", "Orta", False),
    "kontrol": ("triangle-alert", "check-text", "Kontrol", True),
    "okunamadi": ("circle-x", "danger", "Okunamadı", True),
    "okunmadi": ("clock", "text-2", "Okunmadı", False),
}
RANK = {"emin": 0, "orta": 1, "okunmadi": 2, "kontrol": 3, "okunamadi": 4}
NEEDS_CHECK = ("kontrol", "okunamadi")

VIEWS = ("kontrol", "incelenmemis", "tumu", "ornek")
VIEW_NAMES = {"kontrol": "Kontrol gerekenler", "incelenmemis": "İncelenmemiş", "tumu": "Tümü",
              "ornek": "Örnek"}

_NUMBER = re.compile(r"^[\d.,\s]+$")
_DATE = re.compile(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$")


# Text helpers
def display_name(name: str) -> str:
    """A variable name as a column title: "Sicil_No" -> "Sicil No"."""
    return name.replace("_", " ").strip()


def tr_lower(text: str) -> str:
    """Lower case the Turkish way (I -> ı, İ -> i)."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def joined(names: list[str]) -> str:
    """"a", "a ve b", "a, b ve c"."""
    if len(names) <= 1:
        return "".join(names)
    return f"{', '.join(names[:-1])} ve {names[-1]}"


def section_name(section: int | None) -> str:
    """Section 0 is the template's own box; later ones are its variants (as in Şablonlar)."""
    return "Bölüm 1" if not section else f"Varyant {section + 1}"


def page_range(first: int, last: int) -> str:
    return f"{first}–{last}" if first != last else str(first)


def column_kind(texts: Iterable[str]) -> str:
    """How a variable column is set: "number" (right, tabular), "date" (tabular),
    "code" (OCR value font) or "text" (body font)."""
    shown = [t for t in texts if t]
    if not shown:
        return "code"
    if all(_DATE.match(t) for t in shown):
        return "date"
    if all(_NUMBER.match(t) for t in shown) and any("." in t or "," in t for t in shown):
        return "number"  # amounts ("1.250"); bare digit runs ("48190") read as codes
    if all(any(c.isdigit() for c in t) and " " not in t for t in shown):
        return "code"
    return "text"


# Uncertain characters
def uncertain_positions(text: str, others: Iterable[str], flagged: bool) -> tuple[int, ...]:
    """Characters of `text` the reader was not sure of: where other readings of the same box
    disagree, else (for a flagged value) letters OCR confuses with a neighbouring digit."""
    found: set[int] = set()
    for other in others:
        if not other or other == text:
            continue
        matcher = SequenceMatcher(None, text, other, autojunk=False)
        for tag, i1, i2, _j1, _j2 in matcher.get_opcodes():
            if tag in ("replace", "delete"):
                found.update(range(i1, i2))
    if flagged and not found:
        for i, char in enumerate(text):
            if char in CONFUSABLE and any(
                    0 <= j < len(text) and text[j].isdigit() for j in (i - 1, i + 1)):
                found.add(i)
    return tuple(sorted(found))


def changed_positions(old: str, new: str) -> tuple[int, ...]:
    """Characters of `new` that differ from `old` (what the suggestion changes)."""
    if not old or old == new:
        return ()
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    found: set[int] = set()
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "insert"):
            found.update(range(j1, j2))
    return tuple(sorted(found))


def swaps(old: str, new: str) -> list[tuple[str, str]]:
    """One-for-one character changes from `old` to `new`: [("I", "1"), ("B", "8")]."""
    pairs = []
    matcher = SequenceMatcher(None, old, new, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace" and i2 - i1 == j2 - j1:
            pairs += list(zip(old[i1:i2], new[j1:j2], strict=True))
    return pairs


# Cells and rows
@dataclass(frozen=True)
class Cell:
    """One variable value of one document, as the screen shows it."""

    key: str
    name: str  # the variable's name in the template
    required: bool
    value: VariableValue | None
    text: str  # what the table shows: the value, or for a flagged one what was read
    level: str
    percent: int | None
    reviewed: bool
    uncertain: tuple[int, ...] = ()
    suggestion: str = ""
    suggestion_marks: tuple[int, ...] = ()
    source: int | None = None  # the section the shown reading came from

    @property
    def title(self) -> str:
        return display_name(self.name)

    @property
    def needs_check(self) -> bool:
        return self.level in NEEDS_CHECK

    def edit_text(self) -> str:
        """What the cell editor starts with: the suggestion of a flagged value."""
        if self.value is None:
            return ""
        if self.value.flagged:
            return self.suggestion or self.text
        return self.value.value

    def why(self) -> str:
        """The inspector's one line under the value."""
        if self.value is None:
            return "Bu değer henüz okunmadı. Değerleri oku ile okunur."
        if self.level == "okunamadi":
            return "Kutuda okunacak yazı bulunamadı: değeri elle yazın ya da yeni bir kutu çizin."
        if self.value.flagged and self.suggestion:
            parts = [f"{a} yerine {b}" for a, b in swaps(self.text, self.suggestion)]
            where = section_name(self.source)
            if parts and self.text != self.suggestion:
                return f"{where} ile okundu: {', '.join(parts)}."
            return f"{where} ile okundu; emin olunamadı."
        if self.value.edited:
            return "İncelendi: elle yazıldı ya da onaylandı; yeniden okumada korunur."
        if self.value.section:
            return f"{section_name(self.value.section)} ile okundu."
        return ""


def _okunan(value: VariableValue) -> tuple[str, int | None]:
    """What was read for a flagged value (its text, else the first reading), and its box."""
    if value.value:
        return value.value, value.section
    for reading in sorted(value.readings, key=lambda r: r.section):
        if reading.text:
            return reading.text, reading.section
    return value.suggestion, None


def _suggestion_source(value: VariableValue) -> tuple[int | None, float | None]:
    matches = [r for r in value.readings if r.text == value.suggestion]
    if not matches:
        read = [r for r in value.readings if r.text]
        return (None, max(r.confidence for r in read)) if read else (None, None)
    best = max(matches, key=lambda r: r.confidence)
    return best.section, best.confidence


def make_cell(variable: Variable, value: VariableValue | None) -> Cell:
    if value is None:
        return Cell(variable.key, variable.name, variable.required, None, "", "okunmadi",
                    None, False)
    if not value.flagged:
        level = "emin" if value.edited or value.confidence >= EMIN_AT else "orta"
        # A value a person accepted or typed is "Emin, İncelendi" with no percentage: the
        # reader's score no longer applies, and a re-scored %100 next to the row's %90
        # would be two numbers for one fact.
        percent = None if value.edited else round(value.confidence * 100)
        return Cell(variable.key, variable.name, variable.required, value, value.value, level,
                    percent, value.edited, source=value.section)
    text, source = _okunan(value)
    if not text and not value.suggestion:
        return Cell(variable.key, variable.name, variable.required, value, "", "okunamadi",
                    None, False)
    section, confidence = _suggestion_source(value)
    percent = round((confidence if confidence is not None else value.confidence) * 100)
    others = [r.text for r in value.readings] + [value.suggestion]
    return Cell(variable.key, variable.name, variable.required, value, text, "kontrol",
                percent, False, uncertain_positions(text, others, True), value.suggestion,
                changed_positions(text, value.suggestion),
                section if section is not None else source)


@dataclass
class Row:
    """One document with a template, and its values in template order."""

    number: int
    document: Document
    template_id: str
    template: Template | None
    first: int  # position of its first page in the job
    last: int
    cells: list[Cell] = field(default_factory=list)
    error: str | None = None

    @property
    def pages(self) -> str:
        return page_range(self.first, self.last)

    @property
    def read(self) -> bool:
        return any(c.value is not None for c in self.cells)

    @property
    def level(self) -> str:
        if not self.read:
            return "okunmadi"
        return max((c.level for c in self.cells if c.value is not None), key=RANK.__getitem__)

    @property
    def percent(self) -> int | None:
        level = self.level
        found = [c.percent for c in self.cells if c.level == level and c.percent is not None]
        return min(found) if found else None

    @property
    def reviewed(self) -> bool:
        return self.read and all(c.reviewed for c in self.cells if c.value is not None)

    def cell(self, key: str) -> Cell | None:
        return next((c for c in self.cells if c.key == key), None)

    def page_of(self, cell: Cell) -> int:
        """Index (in the document) of the page the cell's box is on."""
        if self.template is None:
            return 0
        variable = next((v for v in self.template.variables if v.key == cell.key), None)
        if variable is None or not variable.sections:
            return 0
        section = variable.sections[min(cell.source or 0, len(variable.sections) - 1)]
        count = len(self.document.page_ids)
        index = section.page - 1 if section.page > 0 else count + section.page
        return max(0, min(count - 1, index))


def build_rows(job: Job, documents: list[Document],
               templates: Mapping[str, Template]) -> list[Row]:
    """Every document that has a template, numbered as in the job (Belge N)."""
    position = {pid: n for n, pid in enumerate(job.ordered_page_ids(), start=1)}
    rows = []
    for number, document in enumerate(documents, start=1):
        template_id, _ = document_template(job, document)
        if template_id is None:
            continue
        template = templates.get(template_id)
        values = current_values(job, document)
        cells = []
        if template is not None:
            for variable in template.variables:
                value = values.get(variable.key) if values is not None else None
                cells.append(make_cell(variable, value))
        rows.append(Row(number, document, template_id, template,
                        position.get(document.page_ids[0], 0),
                        position.get(document.page_ids[-1], 0), cells,
                        current_read_error(job, document)))
    return rows


@dataclass(frozen=True)
class Counts:
    values: int = 0
    kontrol: int = 0
    okunamadi: int = 0
    reviewed: int = 0
    unread_documents: int = 0

    @property
    def unreviewed(self) -> int:
        return self.values - self.reviewed


def count(rows: Iterable[Row]) -> Counts:
    values = kontrol = okunamadi = reviewed = unread = 0
    for row in rows:
        if not row.read:
            unread += 1
            continue
        for cell in row.cells:
            if cell.value is None:
                continue
            values += 1
            kontrol += cell.needs_check
            okunamadi += cell.level == "okunamadi"
            reviewed += cell.reviewed
    return Counts(values, kontrol, okunamadi, reviewed, unread)


def in_view(row: Row, view: str) -> bool:
    if view == "kontrol":
        return any(c.needs_check for c in row.cells)
    if view == "incelenmemis":
        return any(c.value is not None and not c.reviewed for c in row.cells)
    return True


def matches(row: Row, query: str) -> bool:
    """Search over the row's shown values and its document number."""
    if not query:
        return True
    words = [tr_lower(c.text or c.suggestion) for c in row.cells] + [str(row.number)]
    return tr_lower(query) in " ".join(words)


# Örnek kontrol
@dataclass(frozen=True)
class SampleItem:
    first_page: str  # the document's first page id (stable while the cuts stay)
    key: str
    text: str  # the value when it was drawn: a different value later is an error found


def draw_sample(rows: list[Row], seed: str, size: int = SAMPLE_SIZE) -> list[SampleItem]:
    """Up to `size` random Emin values nobody has looked at (else any Emin value)."""
    emin = [(row, cell) for row in rows for cell in row.cells
            if cell.level == "emin" and cell.value is not None]
    fresh = [(r, c) for r, c in emin if not c.reviewed]
    pool = fresh or emin
    picked = random.Random(seed).sample(pool, min(size, len(pool)))
    order = {id(c): (r.number, i) for r, _ in picked for i, c in enumerate(r.cells)}
    picked.sort(key=lambda rc: order[id(rc[1])])
    return [SampleItem(r.document.page_ids[0], c.key, c.text) for r, c in picked]


# Edits (run inside JobController.run, so each is one undoable step)
def _stored(job: Job, document: Document) -> dict[str, VariableValue]:
    values = current_values(job, document)
    if values is None:
        raise KeyError("değerler okunmadı")
    return values


def confirm(job: Job, document: Document, key: str) -> bool:
    """Onayla: accept a flagged value's suggestion, or mark what was read as İncelendi.
    False when there is nothing to accept (an unread or empty flagged value)."""
    values = _stored(job, document)
    value = values.get(key)
    if value is None:
        return False
    if value.flagged:
        if not value.suggestion:
            return False
        review.accept_suggestion(job, document, key)
        return True
    if not value.edited:
        values[key] = replace(value, edited=True)
    return True


def flag_variable(job: Job, documents: Iterable[Document], key: str) -> int:
    """An error found in the sample: every unreviewed value of that variable needs a check.
    The value stays as the suggestion, so Enter accepts it once someone has looked."""
    flagged = 0
    for document in documents:
        values = current_values(job, document)
        value = values.get(key) if values else None
        if value is None or value.flagged or value.edited:
            continue
        values[key] = replace(value, flagged=True, suggestion=value.value or value.suggestion)
        flagged += 1
    return flagged
