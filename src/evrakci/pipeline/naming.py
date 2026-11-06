"""Safe Windows file names, built from a template's file-name pattern."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence

from evrakci.pipeline.templates.model import pattern_names
from evrakci.pipeline.templates.read import VariableValue

MAX_LENGTH = 120
_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {"con", "prn", "aux", "nul"} | {f"{p}{n}" for p in ("com", "lpt") for n in range(1, 10)}
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
    """The file name (without .pdf), or None when a required value is missing or unsure."""
    checks: list[str] = []
    missing_required = []
    name = pattern
    for variable in dict.fromkeys(pattern_names(pattern)):
        value = values.get(variable)
        usable = value is not None and not value.flagged and value.value.strip()
        if not usable:
            if variable in required:
                missing_required.append(variable)
            elif value is not None and value.flagged:
                checks.append(f"okunamadı: {variable}")
        text = safe_filename(value.value) if usable else ""
        name = name.replace(f"{{{variable}}}", text)
    if missing_required:
        return None, [f"zorunlu değer eksik: {v}" for v in missing_required]
    return safe_filename(_tidy_separators(name)), checks


def unique_names(names: Sequence[str]) -> list[str]:
    """Add (2), (3), ... to names that clash, comparing as Windows does (ignoring case)."""
    seen: dict[str, int] = {}
    result = []
    for name in names:
        key = name.casefold()
        count = seen.get(key, 0) + 1
        seen[key] = count
        result.append(name if count == 1 else f"{name} ({count})")
    return result
