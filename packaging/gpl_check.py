"""Find and remove GPL-only parts that must not ship (docs/dependency-licenses.md).

GNU Readline and GDBM are GPL-3.0 and JBIG-KIT is GPL-2.0-or-later: their Python modules are
excluded at freeze time, Tesseract is built without JBIG, and a build that still holds any of
them is refused. Qt Virtual Keyboard and Qt Wayland Compositor are GPL-3.0 (not
LGPL); PySide6 brings them along, so they are deleted from the build. The app needs neither.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

GPL_LIBRARIES = ("libreadline", "libgdbm")
# JBIG-KIT (GPL-2.0-or-later), linked by some Tesseract builds through libtiff: libjbig.so.2,
# libjbig-0.dll, libjbig85.dll, jbig.dll. Not JBIG2 (jbig2dec, jbig2enc), a different format.
_JBIG_KIT = re.compile(r"(lib)?jbig(85)?([-.]\d+)*\.(dll|so(\.\d+)*|dylib)", re.IGNORECASE)
_SHARED = re.compile(r"\.(dll|so(\.\d+)*|dylib)$", re.IGNORECASE)
GPL_QT = (
    "qt6virtualkeyboard",
    "qtvirtualkeyboardplugin",
    "qt6waylandcompositor",
    "qt6waylandeglcompositor",
)
GPL_QT_FOLDERS = ("wayland-graphics-integration-server",)


def _is_gpl_qt(path: Path) -> bool:
    name = path.name.lower()
    return any(part in name for part in GPL_QT) or any(f in path.parts for f in GPL_QT_FOLDERS)


def forbidden_libraries(build_dir: Path) -> list[Path]:
    """Every file in a build that must not ship."""
    return sorted(
        p for p in Path(build_dir).rglob("*")
        if p.is_file() and (
            (p.name.startswith(GPL_LIBRARIES) and _SHARED.search(p.name))
            or _JBIG_KIT.fullmatch(p.name) or _is_gpl_qt(p)
        )
    )


def remove_gpl_qt(build_dir: Path) -> list[Path]:
    """Delete the GPL-only Qt parts from a build; returns what was removed."""
    build_dir = Path(build_dir)
    removed = []
    for folder in sorted(p for p in build_dir.rglob("*")
                         if p.is_dir() and p.name in GPL_QT_FOLDERS):
        removed.extend(p for p in folder.rglob("*") if p.is_file())
        shutil.rmtree(folder)
    for path in forbidden_libraries(build_dir):
        if _is_gpl_qt(path):
            path.unlink()
            removed.append(path)
    return removed
