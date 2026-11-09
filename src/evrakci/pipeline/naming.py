"""Safe Windows file names, built from a template's file-name pattern."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from pathlib import Path

from evrakci.pipeline.templates.model import pattern_names
from evrakci.pipeline.templates.values import VariableValue

MAX_LENGTH = 120
# Windows' classic path limit, with a little room; ".pdf.gecici" is the text-layer temp file.
PATH_LIMIT = 250
_LONGEST_SUFFIX = " (999).pdf.gecici"
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_DEVICES = ["con", "prn", "aux", "nul", "conin$", "conout$"]
_NUMBERED = [f"{p}{n}" for p in ("com", "lpt") for n in [*range(1, 10), "¹", "²", "³"]]
_RESERVED = set(_DEVICES + _NUMBERED)
_SEPARATORS = "_-. "
_REPEATED_SEPARATORS = re.compile(r"(\s*[_\-.]\s*){2,}|\s{2,}")


def _clean_text(text: str) -> str:
    """NFC, every kind of space as one space, characters Windows forbids removed."""
    name = unicodedata.normalize("NFC", text)
    name = re.sub(r"\s", " ", name)  # tabs and line breaks become spaces first
    return _FORBIDDEN.sub("", name)


def _finish(name: str) -> tuple[str, int | None]:
    """Cut to the length limit, trim the end, and make a device name safe.

    Returns the name and where an underscore was inserted (or None). Windows treats
    `AUX`, `AUX.anything` and `AUX .x` as the device, so the part before the first dot
    is checked, without trailing spaces.
    """
    name = name[:MAX_LENGTH].rstrip(". ")
    base, dot, rest = name.partition(".")
    if base.rstrip(" ").casefold() in _RESERVED:
        at = len(base.rstrip(" "))
        return base.rstrip(" ") + "_" + dot + rest, at
    return name, None


def safe_filename(text: str) -> str:
    """A name Windows accepts. Turkish letters are kept; may return an empty string."""
    return _finish(" ".join(_clean_text(text).split()))[0]


def _tidy_separators(name: str) -> str:
    """Collapse separators left doubled by empty values, and trim them from the ends."""

    def keep_first(match: re.Match) -> str:
        found = match.group(0).strip()
        return found[0] if found else " "

    return _REPEATED_SEPARATORS.sub(keep_first, name).strip(_SEPARATORS)


def build_name(
    pattern: str, values: Mapping[str, VariableValue], required: set[str]
) -> tuple[str | None, list[str]]:
    """The file name (without .pdf), or None when a required value can't be used.

    A value counts only if something is left of it after making it Windows-safe.
    """
    name, checks, _keep = build_name_kept(pattern, values, required)
    return name, checks


def _assemble(marked: str, order: list[str], cleaned: Mapping[str, str]):
    """The name from the marked pattern, with where each value landed in it."""
    spans: dict[str, list[tuple[int, int]]] = {}
    expanded = ""
    for part in re.split("(\ue000\\d+\ue001)", marked):
        if part.startswith("\ue000"):
            variable = order[int(part[1:-1])]
            text = cleaned[variable]
            spans.setdefault(variable, []).append((len(expanded), len(expanded) + len(text)))
            expanded += text
        else:
            # The pattern's own text is cleaned here, so value positions stay right.
            literal = re.sub(" {2,}", " ", _clean_text(part))
            if expanded.endswith(" ") or not expanded:
                literal = literal.lstrip(" ")
            expanded += literal
    final, inserted = _finish(expanded)
    if inserted is not None:
        spans = {v: [(a + (a >= inserted), b + (b > inserted)) for a, b in places]
                 for v, places in spans.items()}
    return final, spans, len(expanded.rstrip(". ")) > len(final) - (inserted is not None)


def build_name_kept(
    pattern: str, values: Mapping[str, VariableValue], required: set[str]
) -> tuple[str | None, list[str], int]:
    """Like build_name, plus how many characters must stay so every required value survives.

    When the name is too long, optional values are shortened first; a name that was cut is
    marked.
    """
    checks: list[str] = []
    problems: list[str] = []
    cleaned: dict[str, str] = {}
    marked = pattern
    order = list(dict.fromkeys(pattern_names(pattern)))
    for number, variable in enumerate(order):
        value = values.get(variable)
        raw = value.value.strip() if value is not None and not value.flagged else ""
        text = safe_filename(raw) if raw else ""
        if not text:
            if variable in required:
                reason = "eksik" if not raw else "dosya adına uygun değil"
                problems.append(f"zorunlu değer {reason}: {variable}")
            elif raw:
                checks.append(f"dosya adına uygun değil: {variable}")
            elif value is not None and value.flagged:
                checks.append(f"okunamadı: {variable}")
        cleaned[variable] = text
        # Markers keep each value's own place through the separator clean-up.
        marked = marked.replace(f"{{{variable}}}", f"\ue000{number}\ue001" if text else "")
    if problems:
        return None, problems, 0
    marked = _tidy_separators(marked)
    final, spans, shortened = _assemble(marked, order, cleaned)

    def surviving(variable: str) -> bool:
        return any(final[a:b] == cleaned[variable] for a, b in spans.get(variable, []))

    cut = [v for v in required if spans.get(v) and not surviving(v)]
    optional = sorted((v for v in order if v not in required and cleaned[v]),
                      key=lambda v: -len(cleaned[v]))
    while cut and optional:  # give way: shorten the longest optional value and try again
        excess = sum(len(cleaned[v]) for v in order) - MAX_LENGTH + 10
        longest = optional.pop(0)
        cleaned[longest] = cleaned[longest][: max(1, len(cleaned[longest]) - excess)].rstrip()
        final, spans, _ = _assemble(marked, order, cleaned)
        shortened = True
        cut = [v for v in required if spans.get(v) and not surviving(v)]
    if cut:
        return None, [f"zorunlu değer dosya adına sığmadı: {v}" for v in sorted(cut)], 0
    keep = max((min(b for a, b in spans[v] if final[a:b] == cleaned[v])
                for v in required if spans.get(v)), default=0)
    if shortened:
        checks.append("dosya adı kısaltıldı")
    return final, checks, keep


def name_key(name: str) -> str:
    """How Windows compares names: case-insensitive, and ı/I/i fold together."""
    return name.upper().casefold()


def unique_names(names: Sequence[str]) -> list[str]:
    """Add (2), (3), ... until every name is free, compared as Windows does."""
    used: set[str] = set()
    result = []
    for name in names:
        candidate, number = name, 1
        while name_key(candidate) in used:
            number += 1
            candidate = f"{name} ({number})"
        used.add(name_key(candidate))
        result.append(candidate)
    return result


def fit_names(names: Sequence[str], out_dir: Path) -> list[str]:
    """Shorten names so every full path stays within Windows' path limit."""
    budget = PATH_LIMIT - _units(str(Path(out_dir).resolve())) - len(_LONGEST_SUFFIX) - 1
    if budget < 12:
        raise ValueError("Çıktı klasörünün yolu çok uzun; daha kısa bir klasör seçin.")
    return [_cut_units(name, budget) for name in names]


def _units(text: str) -> int:
    """Length as Windows counts it (UTF-16 code units)."""
    return len(text.encode("utf-16-le")) // 2


def _cut_units(name: str, budget: int) -> str:
    while _units(name) > budget:
        name = name[:-1]
    return name.rstrip(". ")
