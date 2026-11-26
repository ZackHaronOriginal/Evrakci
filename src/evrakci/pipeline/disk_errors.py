"""Turkish sentences for the errors the disk gives (E-3): the window and the command line say
the same thing, and never the operating system's own English text."""

from __future__ import annotations

import errno
from pathlib import Path

NO_ROOM = "Diskte yer kalmadı."
NO_PERMISSION = "Klasöre yazma izni yok."
NO_FOLDER = "Klasör bulunamadı."
NOT_A_FOLDER = "Yolun bir bölümü klasör değil, dosya."
UNKNOWN = "Disk beklenmeyen bir hata verdi."


def _inside(path: object, folder: Path | None) -> bool:
    if folder is None or not path:
        return False
    try:
        Path(str(path)).relative_to(folder)
    except ValueError:
        return False
    return True


def disk_reason(error: OSError, folder: Path | None = None) -> str:
    """One Turkish sentence for `error`. `folder` is the export folder: a missing path outside
    it is a scanned file that was moved away, and its name is said."""
    if isinstance(error, FileExistsError):
        shown = error.filename or (error.args[0] if len(error.args) == 1 else "")
        name = Path(str(shown)).name if shown else ""  # the writer raises FileExistsError(name)
        return f"Hedef klasörde aynı adlı dosya var: {name}." if name else \
            "Hedef klasörde aynı adlı dosya var."
    code = error.errno
    if code == errno.ENOSPC or code == getattr(errno, "EDQUOT", None):
        return NO_ROOM
    if code in (errno.EACCES, errno.EPERM, errno.EROFS):
        return NO_PERMISSION
    if code == errno.ENOENT or isinstance(error, FileNotFoundError):
        if error.filename and folder is not None and not _inside(error.filename, folder):
            return f"Taranan dosya bulunamadı: {Path(str(error.filename)).name}."
        return NO_FOLDER
    if code == errno.ENOTDIR or isinstance(error, NotADirectoryError):
        return NOT_A_FOLDER
    return UNKNOWN
