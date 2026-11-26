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


def qt_translation_entry(pyside_dir: Path, translations: Path,
                         name: str = "qtbase_tr.qm") -> tuple[str, str]:
    """(source, target in the folder build) of Qt's Turkish dialog texts. The target keeps the
    translations folder where QLibraryInfo points for the PySide6 package (lib/PySide6/...),
    which is where the frozen app looks. A missing file stops the build: without it the
    OK / Cancel / Yes / No buttons would be English with nothing said."""
    source = Path(translations) / name
    if not source.is_file():
        raise FileNotFoundError(f"{name} not found in {translations}; the build must not ship "
                                "English dialog buttons")
    relative = source.resolve().relative_to(Path(pyside_dir).resolve())
    return str(source), (Path("lib") / "PySide6" / relative).as_posix()


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
