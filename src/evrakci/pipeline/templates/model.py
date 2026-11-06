"""Templates: user-named variables, each read from one or more boxes (sections).

The code knows no fields, types or document kinds. Everything here is made by the user.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
import uuid
from dataclasses import dataclass, field

TEMPLATE_FORMAT = "evrakci-sablon"
TEMPLATE_FORMAT_VERSION = 1
DEFAULT_MIN_CONFIDENCE = 0.70

_PLACEHOLDER = re.compile(r"\{([^{}]*)\}")


class TemplateError(ValueError):
    """A mistake in a template. The message is shown to staff (Turkish)."""


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def validate_name(name: str) -> str:
    cleaned = _nfc(name).strip()
    if not cleaned:
        raise TemplateError("Değişken adı boş olamaz.")
    if "{" in cleaned or "}" in cleaned:
        raise TemplateError(f"Değişken adında {{ veya }} olamaz: {cleaned}")
    return cleaned


def pattern_names(pattern: str) -> list[str]:
    """Variable names used in a file-name pattern, in order."""
    pattern = _nfc(pattern)
    names = _PLACEHOLDER.findall(pattern)
    if "{" in _PLACEHOLDER.sub("", pattern) or "}" in _PLACEHOLDER.sub("", pattern):
        raise TemplateError(f"Dosya adı kalıbında eşleşmeyen süslü parantez: {pattern}")
    return names


@dataclass(frozen=True)
class Section:
    """Where to read a variable: a page of the document and a box in millimetres."""

    page: int  # 1, 2, ... from the first page; -1 is the last page
    box_mm: tuple[float, float, float, float]  # x0, y0, x1, y1 from the top-left
    example: str | None = None  # the example document it was drawn on

    def __post_init__(self) -> None:
        if self.page == 0:
            raise TemplateError("Sayfa 0 olamaz: 1 ilk sayfa, -1 son sayfadır.")
        x0, y0, x1, y1 = self.box_mm
        if not (x0 < x1 and y0 < y1) or min(self.box_mm) < 0:
            raise TemplateError(f"Geçersiz kutu: {list(self.box_mm)}")


def new_key() -> str:
    return uuid.uuid4().hex[:8]


def stable_key(name: str) -> str:
    """A key for variables saved before keys existed: the same name gives the same key."""
    return hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]


@dataclass
class Variable:
    name: str
    sections: list[Section] = field(default_factory=list)
    required: bool = False
    key: str = field(default_factory=new_key)  # permanent; renaming changes only the name


@dataclass
class Template:
    id: str
    name: str
    variables: list[Variable] = field(default_factory=list)
    filename_pattern: str = ""
    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    keywords: list[str] = field(default_factory=list)  # reserved for template guessing later

    def variable(self, name: str) -> Variable:
        name = _nfc(name).strip()
        for variable in self.variables:
            if variable.name == name:
                return variable
        raise TemplateError(f"Değişken yok: {name}")

    def names_by_key(self) -> dict[str, str]:
        return {v.key: v.name for v in self.variables}

    def _has(self, name: str) -> bool:
        return any(v.name == name for v in self.variables)

    def add_variable(self, name: str, required: bool = False, key: str | None = None) -> Variable:
        name = validate_name(name)
        if self._has(name):
            raise TemplateError(f"Bu adla bir değişken zaten var: {name}")
        variable = Variable(name, required=required, key=key or new_key())
        self.variables.append(variable)
        return variable

    def remove_variable(self, name: str) -> None:
        variable = self.variable(name)
        self.variables.remove(variable)
        # Separators left around the gap are tidied when file names are built.
        self.filename_pattern = self.filename_pattern.replace(f"{{{variable.name}}}", "")

    def rename_variable(self, old: str, new: str) -> None:
        variable = self.variable(old)
        old, new = variable.name, validate_name(new)
        if new != old and self._has(new):
            raise TemplateError(f"Bu adla bir değişken zaten var: {new}")
        variable.name = new
        self.filename_pattern = self.filename_pattern.replace(f"{{{old}}}", f"{{{new}}}")

    def set_required(self, name: str, required: bool) -> None:
        self.variable(name).required = required

    def add_section(self, name: str, section: Section) -> None:
        self.variable(name).sections.append(section)

    def _section_index(self, name: str, index: int) -> list[Section]:
        sections = self.variable(name).sections
        if not 0 <= index < len(sections):
            raise TemplateError(f"Bölüm yok: {name} için {index + 1}. bölüm")
        return sections

    def remove_section(self, name: str, index: int) -> None:
        del self._section_index(name, index)[index]

    def move_section(self, name: str, index: int, new_index: int) -> None:
        sections = self._section_index(name, index)
        if not 0 <= new_index < len(sections):
            raise TemplateError(f"Geçersiz sıra: {new_index + 1}")
        sections.insert(new_index, sections.pop(index))

    def set_pattern(self, pattern: str) -> None:
        unknown = [n for n in pattern_names(pattern) if not self._has(n)]
        if unknown:
            raise TemplateError(f"Kalıpta bilinmeyen değişken: {', '.join(unknown)}")
        self.filename_pattern = _nfc(pattern)

    def set_min_confidence(self, value: float) -> None:
        if math.isnan(value) or not 0 < value <= 1:
            raise TemplateError("Güven eşiği 0 ile 1 arasında olmalı (örn. 0.7).")
        self.min_confidence = value


def template_to_dict(template: Template) -> dict:
    return {
        "format": TEMPLATE_FORMAT,
        "version": TEMPLATE_FORMAT_VERSION,
        "id": template.id,
        "name": template.name,
        "filename_pattern": template.filename_pattern,
        "min_confidence": template.min_confidence,
        "keywords": list(template.keywords),
        "variables": [
            {
                "key": v.key,
                "name": v.name,
                "required": v.required,
                "sections": [
                    {"page": s.page, "box_mm": list(s.box_mm), "example": s.example}
                    for s in v.sections
                ],
            }
            for v in template.variables
        ],
    }


def template_from_dict(data: dict) -> Template:
    if data.get("format") != TEMPLATE_FORMAT or data.get("version") != TEMPLATE_FORMAT_VERSION:
        raise TemplateError("Bu dosya bir Evrakçı şablonu değil veya sürümü desteklenmiyor.")
    try:
        name = str(data["name"]).strip()
        if not name:
            raise TemplateError("Şablon adı boş olamaz.")
        # Everything goes through the same checks as the editor.
        template = Template(
            id=str(data["id"]), name=name, keywords=[str(k) for k in data.get("keywords", [])]
        )
        template.set_min_confidence(float(data.get("min_confidence", DEFAULT_MIN_CONFIDENCE)))
        for item in data["variables"]:
            variable = template.add_variable(
                item["name"],
                bool(item.get("required", False)),
                key=str(item.get("key") or stable_key(validate_name(item["name"]))),
            )
            for s in item.get("sections", []):
                box = tuple(float(v) for v in s["box_mm"])
                if len(box) != 4:
                    raise TemplateError(f"Geçersiz kutu: {s['box_mm']}")
                variable.sections.append(Section(int(s["page"]), box, s.get("example")))
        if len({v.key for v in template.variables}) != len(template.variables):
            raise TemplateError("Şablonda aynı anahtarlı iki değişken var.")
        template.set_pattern(str(data.get("filename_pattern", "")))
    except (KeyError, TypeError) as error:
        raise TemplateError(f"Şablon dosyası eksik veya bozuk ({error}).") from error
    return template
