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
_LONGEST_SUFFIX = " (99).pdf.gecici"
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_DEVICES = ["con", "prn", "aux", "nul", "conin$", "conout$"]
_NUMBERED = [f"{p}{n}" for p in ("com", "lpt") for n in [*range(1, 10), "¹", "²", "³"]]
_RESERVED = set(_DEVICES + _NUMBERED)
_SEPARATORS = "_-. "
_REPEATED_SEPARATORS = re.compile(r"(\s*[_\-.]\s*){2,}|\s{2,}")


def safe_filename(text: str) -> str:
    """A name Windows accepts. Turkish letters are kept; may return an empty string."""
    name = unicodedata.normalize("NFC", text)
    name = re.sub(r"\s", " ", name)  # tabs and line breaks become spaces first
    name = " ".join(_FORBIDDEN.sub("", name).split())
    name = name[:MAX_LENGTH].rstrip(". ")
    if name.split(".")[0].casefold() in _RESERVED:
        name += "_"
    return name


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
    checks: list[str] = []
    problems: list[str] = []
    cleaned: dict[str, str] = {}
    name = pattern
    for variable in dict.fromkeys(pattern_names(pattern)):
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
        name = name.replace(f"{{{variable}}}", text)
    if problems:
        return None, problems
    final = safe_filename(_tidy_separators(name))
    cut = [v for v in required if cleaned.get(v) and cleaned[v] not in final]
    if cut:
        return None, [f"zorunlu değer dosya adına sığmadı: {v}" for v in sorted(cut)]
    return final, checks


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
    budget = PATH_LIMIT - len(str(Path(out_dir).resolve())) - len(_LONGEST_SUFFIX) - 1
    if budget < 12:
        raise ValueError("Çıktı klasörünün yolu çok uzun; daha kısa bir klasör seçin.")
    return [name if len(name) <= budget else name[:budget].rstrip(". ") for name in names]
