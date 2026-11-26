"""Turkish sentences for the errors the disk gives (E-3): the window and the command line say
the same thing, never the operating system's own English text alone. The technical detail (the
errno name and the file) follows in brackets, so a rare error is still traceable."""

from __future__ import annotations

import errno
from pathlib import Path

NO_ROOM = "Diskte yer kalmadı."
NO_PERMISSION = "Klasöre yazma izni yok."
NO_FOLDER = "Klasör bulunamadı."
NOT_A_FOLDER = "Yolun bir bölümü klasör değil, dosya."
PATH_TOO_LONG = "Çıktı klasörünün yolu çok uzun; daha kısa bir klasör seçin."
UNKNOWN = "Disk beklenmeyen bir hata verdi."
BUSY_FILE = "Dosya başka bir programda açık olabilir"  # + ": <dosya>."
SHARING_VIOLATIONS = (32, 33)  # Windows: the file is in use by another program


def _inside(path: object, folder: Path | None) -> bool:
    if folder is None or not path:
        return False
    try:
        Path(str(path)).relative_to(folder)
    except ValueError:
        return False
    return True


def _filename(error: OSError) -> str:
    shown = error.filename or (error.args[0] if len(error.args) == 1
                               and isinstance(error.args[0], str) else "")
    return str(shown) if shown else ""


def _is(path: str, test: str) -> bool:
    try:
        return getattr(Path(path), test)() if path else False
    except OSError:
        return False


def disk_reason(error: OSError, folder: Path | None = None) -> str:
    """One Turkish sentence for `error`. `folder` is the export folder."""
    path = _filename(error)
    name = Path(path).name if path else ""
    code = error.errno
    if isinstance(error, FileExistsError) and code is None:  # the writer's own: an old file
        return f"Hedef klasörde aynı adlı dosya var: {name}." if name else \
            "Hedef klasörde aynı adlı dosya var."
    if code == errno.EEXIST or isinstance(error, FileExistsError):
        if _is(path, "is_dir"):
            return f"Bir dosya adı, aynı adlı klasörle çakışıyor: {name}."
        return f"Hedef klasörde aynı adlı dosya var: {name}." if name else \
            "Hedef klasörde aynı adlı dosya var."
    if code == errno.ENOSPC or code == getattr(errno, "EDQUOT", None):
        return NO_ROOM
    if code == errno.ENAMETOOLONG:
        return PATH_TOO_LONG
    busy = code == errno.EBUSY or getattr(error, "winerror", None) in SHARING_VIOLATIONS
    if busy or (code in (errno.EACCES, errno.EPERM) and _is(path, "is_file")):
        return f"{BUSY_FILE}: {name}." if name else f"{BUSY_FILE}."
    if code in (errno.EACCES, errno.EPERM, errno.EROFS):
        return NO_PERMISSION
    if code == errno.ENOENT or isinstance(error, FileNotFoundError):
        gone_folder = not path or Path(path) == folder or (
            _inside(path, folder) and not Path(path).parent.is_dir())
        if gone_folder:
            return NO_FOLDER
        return f"Taranan dosya bulunamadı: {name}."
    if code == errno.ENOTDIR or isinstance(error, NotADirectoryError):
        return NOT_A_FOLDER
    return UNKNOWN


def technical(error: BaseException) -> str:
    """"ENAMETOOLONG: dosya.pdf" or "PdfError: text": what a person can search for."""
    code = getattr(error, "errno", None)
    label = errno.errorcode.get(code) if isinstance(code, int) else None
    if isinstance(error, OSError):
        label = label or type(error).__name__
        where = _filename(error)
        return f"{label}: {Path(where).name}" if where else label
    text = str(error).strip()
    return f"{type(error).__name__}: {text}" if text else type(error).__name__


def disk_message(error: OSError, folder: Path | None = None) -> str:
    """The sentence and the technical detail in brackets."""
    return f"{disk_reason(error, folder)} ({technical(error)})"
