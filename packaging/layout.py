"""Where things go in the folder build, and what is taken out of it after cx_Freeze."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

# Copied in after the freeze: cx_Freeze must not scan tesseract.exe and copy its libraries
# into lib/ a second time.
AFTER_FREEZE = ("tesseract",)


def freeze_include_files(stage: Path) -> list[tuple[str, str]]:
    stage = Path(stage)
    if not stage.is_dir():
        return []
    return [(str(p), p.name) for p in sorted(stage.iterdir()) if p.name not in AFTER_FREEZE]


def place_after_freeze(stage: Path, build: Path) -> None:
    for name in AFTER_FREEZE:
        if (Path(stage) / name).is_dir():
            shutil.copytree(Path(stage) / name, Path(build) / name, dirs_exist_ok=True)


def _unused_qt(path: Path) -> bool:
    name = path.name.lower()
    # Qt's PDF image plugin pulls in Qt Pdf (its own PDFium) and Qml/Quick; the app uses none.
    return ("qpdf" in name and path.parent.name == "imageformats") or "qt6pdf" in name


def remove_unused_qt(build: Path) -> list[Path]:
    removed = [p for p in Path(build).rglob("*") if p.is_file() and _unused_qt(p)]
    for path in removed:
        path.unlink()
    return removed


def python_licence_candidates() -> list[Path]:
    base = Path(sys.base_prefix)
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    return [base / "LICENSE.txt", base / "lib" / version / "LICENSE.txt",
            base / "share" / "doc" / version / "LICENSE.txt"]


def copy_python_licence(licenses: Path) -> Path | None:
    """Python's licence, which also carries the notices of the libraries built into it."""
    for candidate in python_licence_candidates():
        if candidate.is_file():
            Path(licenses).mkdir(parents=True, exist_ok=True)
            target = Path(licenses) / "Python-LICENSE.txt"
            shutil.copy2(candidate, target)
            return target
    return None
