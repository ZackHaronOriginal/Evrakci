"""index.xlsx: one row per exported document, saying which ones need a check and why."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from evrakci.pipeline.export import ExportItem
from evrakci.pipeline.job import Job

_FIXED = [
    "Belge no",
    "Dosya",
    "Sayfa sayısı",
    "Kaynak sayfalar",
    "Şablon",
    "PDF/A",
    "Kontrol gerekli",
    "Kontrol nedenleri",
]
_CHECK_FILL = PatternFill("solid", start_color="FFF4CC", end_color="FFF4CC")
_MAX_WIDTH = 60


def _set_text(cell, text: str | None) -> None:
    """Always plain text: OCR'd values starting with = + - @ must never become formulas."""
    text = ILLEGAL_CHARACTERS_RE.sub("", text or "")  # control characters break Excel files
    if not text:
        return
    cell.value = text
    cell.data_type = "s"
    cell.number_format = "@"


def format_time(moment: datetime) -> str:
    """Turkish date and time as written in the sheet: 20.11.2026 14:32."""
    return moment.strftime("%d.%m.%Y %H:%M")


def write_index(items: Sequence[ExportItem], job: Job, path: Path,
                exported_at: datetime | None = None) -> None:
    variables: list[str] = []
    for item in items:
        for name in item.values:
            if name not in variables:
                variables.append(name)

    headings = list(_FIXED)
    for name in variables:  # a variable named like a fixed column gets a mark of its own
        headings.append(f"{name} (değişken)" if name in _FIXED else name)

    book = Workbook()
    sheet = book.active
    sheet.title = "Belgeler"
    for column, title in enumerate(headings, start=1):
        cell = sheet.cell(row=1, column=column)
        _set_text(cell, title)
        cell.font = Font(bold=True)
    sheet.freeze_panes = "A2"

    for row, item in enumerate(items, start=2):
        positions = ", ".join(str(job.position_of(pid)) for pid in item.document.page_ids)
        fixed = [
            str(item.number),
            f"{item.name}.pdf",
            str(len(item.document.page_ids)),
            positions,
            item.template_name or "",
            "" if item.pdfa is None else ("evet" if item.pdfa else "hayır"),
            "evet" if item.checks else "hayır",
            "\n".join(item.checks),
        ]
        values = [item.values.get(name, "") for name in variables]
        for column, text in enumerate(fixed + values, start=1):
            cell = sheet.cell(row=row, column=column)
            _set_text(cell, text)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if item.checks:
                cell.fill = _CHECK_FILL

    _write_summary(book, items, job, exported_at or datetime.now())

    for column in range(1, len(_FIXED) + len(variables) + 1):
        letter = get_column_letter(column)
        longest = max(
            (
                max(len(line) for line in str(cell.value).splitlines() or [""])
                for cell in sheet[letter]
                if cell.value is not None
            ),
            default=8,
        )
        sheet.column_dimensions[letter].width = min(_MAX_WIDTH, longest + 2)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)


def _write_summary(book: Workbook, items: Sequence[ExportItem], job: Job,
                   exported_at: datetime) -> None:
    sheet = book.create_sheet("Özet")
    rows = [
        ("İş adı", job.name),
        ("Dışa aktarma zamanı", format_time(exported_at)),
        ("Belge sayısı", str(len(items))),
        ("Sayfa sayısı", str(sum(len(i.document.page_ids) for i in items))),
        ("Kontrol gerekli", str(sum(1 for i in items if i.checks))),
    ]
    for row, (label, value) in enumerate(rows, start=1):
        _set_text(sheet.cell(row=row, column=1), label)
        sheet.cell(row=row, column=1).font = Font(bold=True)
        _set_text(sheet.cell(row=row, column=2), value)
    sheet.column_dimensions["A"].width = 24
    sheet.column_dimensions["B"].width = min(_MAX_WIDTH, max(len(v) for _, v in rows) + 2)
