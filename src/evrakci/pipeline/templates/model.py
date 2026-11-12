"""Templates: user-named variables, each read from one or more boxes (sections).

The code knows no fields, types or document kinds. Everything here is made by the user.
"""

from __future__ import annotations

import hashlib
import json
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


def _has_hidden_characters(text: str) -> bool:
    """Control, format, private-use or unassigned characters (Unicode category C*)."""
    return any(unicodedata.category(c).startswith("C") for c in text)


def validate_name(name: str) -> str:
    if not isinstance(name, str):
        raise TemplateError("Değişken adı metin olmalı.")
    cleaned = _nfc(name).strip()
    if not cleaned:
        raise TemplateError("Değişken adı boş olamaz.")
    if "{" in cleaned or "}" in cleaned:
        raise TemplateError(f"Değişken adında {{ veya }} olamaz: {cleaned}")
    if _has_hidden_characters(cleaned):
        raise TemplateError(f"Değişken adında görünmeyen veya özel karakter var: {cleaned!r}")
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
        if not isinstance(self.page, int) or isinstance(self.page, bool):
            raise TemplateError(f"Sayfa bir tam sayı olmalı: {self.page!r}")
        if self.page == 0:
            raise TemplateError("Sayfa 0 olamaz: 1 ilk sayfa, -1 son sayfadır.")
        box = self.box_mm
        if (
            not isinstance(box, (tuple, list)) or len(box) != 4
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in box)
        ):
            raise TemplateError(f"Geçersiz kutu: {box!r}")
        if self.example is not None and not isinstance(self.example, str):
            raise TemplateError(f"Örnek belge adı metin olmalı: {self.example!r}")
        finite = all(math.isfinite(v) for v in box)
        # Past the top or left edge is clipped, like past the right or bottom edge.
        x0, y0, x1, y1 = max(0.0, box[0]), max(0.0, box[1]), box[2], box[3]
        if not finite or not (x0 < x1 and y0 < y1):
            raise TemplateError(f"Geçersiz kutu: {list(box)}")
        object.__setattr__(self, "box_mm", (x0, y0, x1, y1) if min(box) < 0 else tuple(box))


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
        if not isinstance(pattern, str):
            raise TemplateError("Dosya adı kalıbı metin olmalı.")
        names = pattern_names(pattern)
        if any(not n for n in names):
            raise TemplateError("Kalıpta boş değişken adı var: {}")
        spaced = [n for n in names if n != n.strip()]
        if spaced:
            raise TemplateError(
                f"Süslü parantez içinde baştaki/sondaki boşluk olmamalı: {{{spaced[0]}}}")
        if _has_hidden_characters(_nfc(pattern)):
            raise TemplateError("Dosya adı kalıbında görünmeyen veya özel karakter var.")
        unknown = [n for n in names if not self._has(n)]
        if unknown:
            raise TemplateError(f"Kalıpta bilinmeyen değişken: {', '.join(unknown)}")
        self.filename_pattern = _nfc(pattern)

    def set_min_confidence(self, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TemplateError("Güven eşiği bir sayı olmalı (örn. 0.7).")
        if math.isnan(value) or not 0 < value <= 1:
            raise TemplateError("Güven eşiği 0 ile 1 arasında olmalı (örn. 0.7).")
        self.min_confidence = value


def template_revision(template: Template) -> str:
    """Changes whenever what is read changes: boxes, pages, their order, the threshold.

    The name, the file-name pattern and required marks do not change what is read.
    """
    content = [
        template.min_confidence,
        [[v.key, [[s.page, list(s.box_mm)] for s in v.sections]] for v in template.variables],
    ]
    return hashlib.sha1(json.dumps(content).encode("utf-8")).hexdigest()[:12]


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
    if not isinstance(data, dict):
        raise TemplateError("Bu dosya bir Evrakçı şablonu değil.")
    version = data.get("version")
    if (data.get("format") != TEMPLATE_FORMAT or isinstance(version, bool)
            or version != TEMPLATE_FORMAT_VERSION):
        raise TemplateError("Bu dosya bir Evrakçı şablonu değil veya sürümü desteklenmiyor.")
    def text(value, what: str) -> str:
        if not isinstance(value, str):
            raise TemplateError(f"Şablon dosyası bozuk: {what} metin olmalı.")
        return value

    def items(value, what: str) -> list:
        if not isinstance(value, list):
            raise TemplateError(f"Şablon dosyası bozuk: {what} bir liste olmalı.")
        return value

    try:
        name = _nfc(text(data["name"], "ad")).strip()
        if not name:
            raise TemplateError("Şablon adı boş olamaz.")
        # Everything goes through the same checks as the editor.
        template = Template(
            id=text(data["id"], "numara"), name=name,
            keywords=[text(k, "anahtar kelime") for k in items(data.get("keywords", []),
                                                                 "anahtar kelimeler")],
        )
        template.set_min_confidence(data.get("min_confidence", DEFAULT_MIN_CONFIDENCE))
        for item in items(data["variables"], "değişkenler"):
            if not isinstance(item, dict):
                raise TemplateError("Şablon dosyası bozuk: değişken bir nesne olmalı.")
            required = item.get("required", False)
            if not isinstance(required, bool):
                raise TemplateError("Şablon dosyası bozuk: zorunlu true veya false olmalı.")
            key = item.get("key") or stable_key(validate_name(item["name"]))
            variable = template.add_variable(item["name"], required, key=text(key, "anahtar"))
            for s in items(item.get("sections", []), "bölümler"):
                if not isinstance(s, dict):
                    raise TemplateError("Şablon dosyası bozuk: bölüm bir nesne olmalı.")
                box = s["box_mm"]
                if not isinstance(box, list):
                    raise TemplateError(f"Geçersiz kutu: {box!r}")
                variable.sections.append(Section(s["page"], tuple(box), s.get("example")))
        if len({v.key for v in template.variables}) != len(template.variables):
            raise TemplateError("Şablonda aynı anahtarlı iki değişken var.")
        template.set_pattern(data.get("filename_pattern", ""))
    except (KeyError, TypeError) as error:
        raise TemplateError(f"Şablon dosyası eksik veya bozuk ({error}).") from error
    return template
