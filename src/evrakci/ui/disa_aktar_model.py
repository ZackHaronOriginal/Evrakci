"""What the Dışa Aktar screen shows, as plain data (no widgets): the pre-flight findings graded
engel / kontrol / eksik / bilgi / tamam, the state of the target folder, and one row per file.

The wording follows the owner's vocabulary: "Kontrol" (needs a check), "Eksik", "Bilgi",
"Engel". Nothing here writes a file; the screen runs `export_job` of the core.
"""

from __future__ import annotations

import os
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from evrakci.pipeline.templates.model import TemplateError, pattern_names

FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')  # what Windows does not allow in a name
NUMBER_SUFFIX = re.compile(r" \((\d+)\)$")  # what `unique_names` adds on a clash
LEVELS = ("engel", "kontrol", "eksik", "bilgi", "tamam")
# Checks that are about a value (their sentence in the pre-flight is A's "emin olunmayan değer")
VALUE_CHECKS = ("zorunlu değer", "okunamadı", "okunmadı", "değerler okunmadı", "şablon değişti")


@dataclass(frozen=True)
class Finding:
    """One row of "Ön kontrol": a status word, a sentence, a count and one way forward."""

    level: str  # engel | kontrol | eksik | bilgi | tamam
    title: str
    detail: str = ""
    count: int | None = None
    link: str = ""
    action: str = ""  # what the link does: choose, subfolder, pattern, next_check, ...
    count_text: str = ""  # shown instead of the count (A's "–" before a job is open)


@dataclass(frozen=True)
class FolderState:
    kind: str  # none | new | ok | other | full | file | readonly | error
    text: str  # the line under the field
    tone: str  # info | ok | err
    blocks: bool = False


def folder_state(text: str) -> FolderState:
    """Say whether the folder can take the export (a folder that does not exist is made)."""
    text = text.strip()
    if not text:
        return FolderState("none", "Boş bir klasör seçin ya da yazın; yoksa oluşturulur.",
                           "info")
    path = Path(text)
    try:
        if not path.exists():
            return FolderState("new", "Klasör yok; yazarken oluşturulur.", "info")
        if not path.is_dir():
            return FolderState("file", "Bu bir dosya, klasör değil. Bir klasör seçin.", "err",
                               True)
        entries = list(path.iterdir())
        old = [p for p in entries if p.suffix.lower() == ".pdf" or p.name.lower() == "index.xlsx"]
        if old:
            return FolderState("full", "Klasör boş değil. Boş bir klasör seçin.", "err", True)
        if not os.access(path, os.W_OK):
            return FolderState("readonly", "Klasöre yazılamıyor. Başka bir klasör seçin.", "err",
                               True)
        if entries:
            return FolderState("other", "Yazılabilir; klasördeki başka dosyalara dokunulmaz.",
                               "ok")
        return FolderState("ok", "Klasör boş, yazılabilir.", "ok")
    except OSError as error:
        return FolderState("error", f"Klasöre bakılamadı: {error.strerror or error}. "
                           "Başka bir klasör seçin.", "err", True)


@dataclass(frozen=True)
class FileRow:
    """One file of the list (before writing: the name that will be written)."""

    number: int
    state: str  # kontrol | bilgi | tamam
    why: str
    pre: str  # the name before the part that was changed
    tail: str  # the part the app added or changed ("" when none), drawn in accent
    post: str  # ".pdf"
    pages: str
    template: str | None

    @property
    def name(self) -> str:
        return self.pre + self.tail + self.post


def pages_text(job, document) -> str:
    positions = [job.position_of(pid) for pid in document.page_ids]
    return f"{positions[0]}–{positions[-1]}" if len(positions) > 1 else str(positions[0])


def reason(check: str) -> str:
    """A check of the core, short enough for the Durum column ("Sicil no eksik")."""
    for prefix, template in (("zorunlu değer eksik: ", "{} eksik"),
                             ("zorunlu değer dosya adına uygun değil: ", "{} uygun değil"),
                             ("zorunlu değer dosya adına sığmadı: ", "{} sığmadı"),
                             ("okunamadı: ", "{} belirsiz"), ("okunmadı: ", "{} okunmadı")):
        if check.startswith(prefix):
            return template.format(check[len(prefix):])
    return check[:1].upper() + check[1:] if check else check


def _name_change(item, pattern: str, names: set[str]) -> tuple[str, str]:
    """(why, tail) when the written name differs from what the pattern asked for."""
    found = NUMBER_SUFFIX.search(item.name)
    if found and item.name[:found.start()].casefold() in names:
        return f"Ad çakışması, {found.group(0).strip()} eklendi", found.group(0)
    if item.template_name and pattern:
        try:
            used = set(pattern_names(pattern))
        except TemplateError:
            used = set()
        for variable in used:
            if FORBIDDEN.search(item.values.get(variable, "")):
                return "Geçersiz karakter silindi", ""
    return "", ""


def file_rows(job, items, patterns: Mapping[int, str] | None = None,
              names: Iterable[str] | None = None) -> list[FileRow]:
    """The rows of the list, flagged documents first (document order inside each group).
    `names` are the names actually written (a finished export), else the planned ones."""
    patterns = patterns or {}
    written = list(names) if names is not None else None
    base_names = {i.name.casefold() for i in items}
    rows = []
    for index, item in enumerate(items):
        pdfa = [c for c in item.checks if c.startswith("PDF/A değil")]
        checks = [c for c in item.checks if c not in pdfa]
        why, tail = _name_change(item, patterns.get(item.number, ""), base_names)
        state = "tamam"
        if checks:
            state, why, tail = "kontrol", reason(checks[0]), ""
        elif pdfa:
            state, why = "bilgi", "PDF/A değil"
        elif why:
            state = "bilgi"
        elif item.template_name is None:
            state, why = "bilgi", "Şablon yok, numaralı ad"
        shown = written[index] if written is not None else f"{item.name}.pdf"
        stem = shown[:-4] if shown.lower().endswith(".pdf") else shown
        if tail and stem.endswith(tail):
            pre, mid = stem[:-len(tail)], tail
        else:
            pre, mid = stem, ""
        rows.append(FileRow(item.number, state, why, pre, mid, shown[len(stem):] or ".pdf",
                            pages_text(job, item.document), item.template_name))
    rows.sort(key=lambda row: row.state != "kontrol")
    return rows


@dataclass(frozen=True)
class Summary:
    documents: int
    pages: int
    kontrol: int
    value_only: bool  # every check is about a value (A's wording fits)
    eksik: int
    eksik_vars: tuple[str, ...]
    eksik_name: str  # the name the first such document gets
    changed: int
    no_template: int


def summarize(items, rows: list[FileRow]) -> Summary:
    kontrol = [i for i in items if i.checks]
    missing = [(i, c) for i in items for c in i.checks if c.startswith("zorunlu değer")]
    variables = tuple(dict.fromkeys(c.split(": ", 1)[1] for _i, c in missing if ": " in c))
    return Summary(
        documents=len(items),
        pages=sum(len(i.document.page_ids) for i in items),
        kontrol=len(kontrol),
        value_only=all(c.startswith(VALUE_CHECKS) for i in kontrol for c in i.checks),
        eksik=len({i.number for i, _c in missing}),
        eksik_vars=variables,
        eksik_name=missing[0][0].name if missing else "",
        changed=sum(1 for r in rows if r.state == "bilgi" and r.why.startswith(
            ("Ad çakışması", "Geçersiz karakter"))),
        no_template=sum(1 for r in rows if r.state == "bilgi" and r.template is None),
    )


def pattern_problem(pattern: str, known: set[str]) -> tuple[str, list[str]]:
    """("", []) when the pattern is fine, ("brace", []) or ("unknown", names) when not."""
    try:
        used = list(dict.fromkeys(pattern_names(pattern)))
    except TemplateError:
        return "brace", []
    nfc = {unicodedata.normalize("NFC", k) for k in known}
    unknown = [n for n in used if unicodedata.normalize("NFC", n).strip() not in nfc]
    return ("unknown", unknown) if unknown else ("", [])


_ENGEL = {  # folder kind: (title, detail, link, action)
    "full": ("Hedef klasör boş değil.", "Eski dosyaların üzerine yazılmaz.",
             "Yeni alt klasör oluştur", "subfolder"),
    "file": ("Hedef bir klasör değil, bir dosya.", "Bir klasör seçin.", "Klasör seç", "choose"),
    "readonly": ("Hedef klasöre yazılamıyor.", "Başka bir klasör seçin.", "Klasör seç", "choose"),
    "error": ("Hedef klasöre bakılamadı.", "Başka bir klasör seçin.", "Klasör seç", "choose"),
}


def findings(summary: Summary, folder: FolderState,
             problem: tuple[str, list[str]] = ("", [])) -> list[Finding]:
    """The rows of "Ön kontrol", engel first. Only an engel stops the export; a kontrol never
    does (the file is written and flagged in index.xlsx)."""
    rows: list[Finding] = []
    if folder.kind in _ENGEL:
        title, detail, link, action = _ENGEL[folder.kind]
        if folder.kind == "error":
            detail = folder.text
        rows.append(Finding("engel", title, detail, 1, link, action))
    kind, unknown = problem
    if kind == "unknown":
        first = f"“{unknown[0]}”" + (f" ve {len(unknown) - 1} tane daha"
                                     if len(unknown) > 1 else "")
        rows.append(Finding("engel", f"Kalıpta bilinmeyen değişken: {first}.",
                            "Menüden bir değişken seçin.", len(unknown), "Kalıbı düzelt",
                            "pattern"))
    elif kind == "brace":
        rows.append(Finding("engel", "Kalıpta eşleşmeyen süslü parantez.",
                            "Her { için bir } olmalı.", 1, "Kalıbı düzelt", "pattern"))
    blocked = bool(rows)
    if not blocked:
        if folder.kind == "none":
            rows.append(Finding("bilgi", "Hedef klasör seçilmedi.",
                                "Dışa aktarmadan önce bir klasör seçin.", None, "Klasör seç",
                                "choose"))
        else:
            where = {"new": "Hedef klasör yazarken oluşturulur.",
                     "ok": "Hedef klasör boş ve yazılabilir."}.get(
                         folder.kind, "Hedef klasör yazılabilir.")
            rows.append(Finding("tamam", "Yazmayı engelleyen sorun yok.", where))
    if summary.kontrol:
        rows.append(Finding(
            "kontrol",
            (f"{summary.kontrol} belgede emin olunmayan değer var." if summary.value_only
             else f"{summary.kontrol} belgede kontrol gereken bir durum var."),
            "Yine de yazılır; index.xlsx'te işaretlenir.", summary.kontrol, "Sonraki kontrol",
            "next_check"))
    if summary.eksik:
        more = len(summary.eksik_vars) - 1
        which = summary.eksik_vars[0] if summary.eksik_vars else ""
        which += f" ve {more} değişken daha" if more > 0 else ""
        rows.append(Finding("eksik", f"Zorunlu değer eksik: {which}.",
                            f"Ad “{summary.eksik_name}” gibi olur.", summary.eksik,
                            "Değerler'e git", "values"))
    if summary.changed:
        rows.append(Finding("bilgi", "Dosya adı değişti.", "Geçersiz karakter ya da çakışma.",
                            summary.changed, "Adları göster", "show_names"))
    if summary.no_template:
        rows.append(Finding("bilgi", "Şablonu olmayan belge var.",
                            "Adı “belge_001” gibi numaralı olur.", summary.no_template,
                            "Kontrol'e git", "kontrol"))
    return rows
