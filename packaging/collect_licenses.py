"""Collect licence files and exact versions of the Python packages in the build.

`collect_from_build` looks at what cx_Freeze really put in lib/, so nothing ships without its
licence: not an optional dependency, and not something that was merely installed on the build
machine.
"""

from __future__ import annotations

import re
import shutil
import sys
from importlib import metadata
from pathlib import Path

_LICENSE_NAME = re.compile(r"(licen[cs]e|copying|notice|authors)", re.IGNORECASE)


_SKIP = ("LicenseRef-Qt-Commercial",)  # PySide6's commercial terms do not apply to this build


def _licence_files(dist: metadata.Distribution) -> list:
    """Every licence file a distribution declares or ships in its dist-info."""
    get_all = getattr(dist.metadata, "get_all", None)
    declared = set((get_all("License-File") if get_all else None) or [])
    found = []
    for file in dist.files or []:
        text = str(file).replace("\\", "/")
        in_info = ".dist-info/" in text
        if (in_info and ("/licenses/" in text or "/LICENSES/" in text)) or (
            in_info and _LICENSE_NAME.search(file.name)
        ) or text.endswith(tuple("/" + d for d in declared)) or text in declared:
            if not any(skip in file.name for skip in _SKIP):
                found.append(file)
    return found


# Wheels that carry no licence file; their licence text ships in licenses/ itself.
_LICENCE_ELSEWHERE = {
    "pyside6": "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only",
    "pyside6-essentials": "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only",
    "pyside6-addons": "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only",
    "shiboken6": "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only",
}


def _in_build(file, lib: Path) -> bool:
    text = str(file).replace("\\", "/")
    if ".dist-info/" in text or "__pycache__" in text or text.endswith(".pyi"):
        return False
    path = Path(lib) / text
    return path.is_file() or (text.endswith(".py") and path.with_suffix(".pyc").is_file())


def _shipped_distributions(lib: Path, own: str) -> list[metadata.Distribution]:
    """Distributions with at least one of their own files in the build's lib/ folder."""
    tops = {p.name.split(".")[0] for p in Path(lib).iterdir()}
    owners = metadata.packages_distributions()
    names = sorted({d for top in tops for d in owners.get(top, [])} - {own})
    dists = [metadata.distribution(name) for name in names]
    owners_of: dict[str, int] = {}
    for dist in dists:
        for file in dist.files or []:
            owners_of[str(file)] = owners_of.get(str(file), 0) + 1
    # A file several distributions claim (PySide6/__init__.py) proves none of them shipped.
    return [d for d in dists
            if any(owners_of[str(f)] == 1 and _in_build(f, lib) for f in d.files or [])]


def collect_from_build(lib: Path, out_dir: Path, own: str = "evrakci") -> list[str]:
    """Licence texts and VERSIONS.txt for every Python package in the build's lib/ folder."""
    out_dir = Path(out_dir)
    lines, names, missing = [], [], []
    for dist in _shipped_distributions(lib, own):
        name, version = dist.metadata["Name"], dist.version
        licence = dist.metadata.get("License-Expression") or dist.metadata.get("License") or ""
        lines.append(f"{name}=={version}  {licence.splitlines()[0] if licence else ''}".rstrip())
        names.append(name)
        files = _licence_files(dist)
        elsewhere = _LICENCE_ELSEWHERE.get(_norm(name))
        if not files and elsewhere:
            note = out_dir / "python" / name / "LICENSE-NOTE.txt"
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(f"{name} {version}: {elsewhere}.\nThe wheel has no licence file; the "
                            "texts are in licenses/LGPL-3.0.txt and licenses/GPL-3.0.txt.\n",
                            encoding="utf-8")
        elif not files:
            missing.append(name)
        for file in files:
            source = Path(dist.locate_file(file))
            if not source.is_file():
                continue
            parts = Path(str(file)).parts
            start = next((i + 1 for i, part in enumerate(parts) if part.endswith(".dist-info")),
                         len(parts) - 1)
            target = out_dir / "python" / name / Path(*parts[start:])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    if missing:
        print(f"Lisans dosyası olmayan paket: {', '.join(missing)}", file=sys.stderr)
        raise SystemExit(1)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "VERSIONS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return names


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def undocumented(names, doc: str) -> list[str]:
    """Packages not named in docs/dependency-licenses.md."""
    text = _norm(doc)
    return sorted(n for n in names if _norm(n) not in text)
