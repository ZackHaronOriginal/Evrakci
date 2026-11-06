"""Copy only what Tesseract needs from a Windows Tesseract install.

    python packaging/stage_tesseract.py SOURCE_DIR TARGET_DIR
    (e.g. SOURCE_DIR = C:\\Program Files\\Tesseract-OCR)

Bundles tesseract.exe and the DLLs it loads (found by walking PE imports with pefile, MIT,
used at build time only), plus the output configs and the licence docs. Training tools,
the uninstaller and language data are left out.
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable, Iterable
from pathlib import Path


def dll_closure(
    start: str, imports_of: Callable[[str], Iterable[str]], available: set[str]
) -> set[str]:
    """Every DLL from `available` that `start` loads, directly or indirectly."""
    by_lower = {name.lower(): name for name in available}
    found: set[str] = set()
    pending = [start]
    while pending:
        current = pending.pop()
        for name in imports_of(current):
            local = by_lower.get(name.lower())
            if local and local != start and local not in found:
                found.add(local)
                pending.append(local)
    return found


def _pe_imports(folder: Path) -> Callable[[str], list[str]]:
    import pefile

    def imports_of(name: str) -> list[str]:
        pe = pefile.PE(str(folder / name), fast_load=True)
        pe.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
        )
        return [entry.dll.decode() for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])]

    return imports_of


def stage(source: Path, target: Path) -> list[str]:
    dlls = {p.name for p in source.glob("*.dll")}
    needed = dll_closure("tesseract.exe", _pe_imports(source), dlls)
    shutil.rmtree(target, ignore_errors=True)
    (target / "tessdata").mkdir(parents=True)
    for name in ["tesseract.exe", *sorted(needed)]:
        shutil.copy2(source / name, target / name)
    for name in ("configs", "tessconfigs"):
        if (source / "tessdata" / name).is_dir():
            shutil.copytree(source / "tessdata" / name, target / "tessdata" / name)
    if (source / "doc").is_dir():
        shutil.copytree(source / "doc", target / "doc")
    return sorted(needed)


if __name__ == "__main__":
    copied = stage(Path(sys.argv[1]), Path(sys.argv[2]))
    print("tesseract.exe + " + ", ".join(copied))
