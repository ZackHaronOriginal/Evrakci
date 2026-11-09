"""Tesseract, run as an external program."""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from evrakci.pipeline.ocr.engine import EngineUnavailable, Reading, Word, nfc, reading_from_words
from evrakci.pipeline.ocr.models import app_dir, data_dir


@dataclass(frozen=True)
class TessDataVariant:
    url: str
    sha256: str


_RAW = "https://raw.githubusercontent.com/tesseract-ocr"
# The three official Turkish data files from the Tesseract project (unchanged upstream for years).
# Linux packages and many installers ship "fast" as plain "tur".
TESSDATA_VARIANTS = {
    "fast": TessDataVariant(
        f"{_RAW}/tessdata_fast/main/tur.traineddata",
        "7393381111e1152420fc4092cb44eef4237580d21b92bf30d7d221aad192c6b7",
    ),
    "standard": TessDataVariant(
        f"{_RAW}/tessdata/main/tur.traineddata",
        "489b9504e80d7184ed1ac9a1976647884ee71149da231ff3c2c1dc15370f2f3d",
    ),
    "best": TessDataVariant(
        f"{_RAW}/tessdata_best/main/tur.traineddata",
        "e0c3338dc17503dc7d335a507c9ae01b2b46cfd07561171e1e1ac55d85e8e438",
    ),
}
TUR_BEST_SHA256 = TESSDATA_VARIANTS["best"].sha256
TUR_BEST_URL = TESSDATA_VARIANTS["best"].url

_LIST_TIMEOUT = 60  # seconds for "tesseract --list-langs"
_READ_TIMEOUT = 300  # seconds for reading one page or box


def no_window(windows: bool | None = None) -> dict:
    """subprocess options that keep a console window from flashing up (Windows window app)."""
    windows = os.name == "nt" if windows is None else windows
    return {"creationflags": 0x08000000} if windows else {}  # CREATE_NO_WINDOW


_WINDOWS_PATHS = [
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
]


_HASHES: dict[tuple[str, int, int, int, int], str] = {}


def _file_hash(path: Path) -> str | None:
    """SHA-256 of a file, remembered until the file changes (data files are several MB)."""
    try:
        stat = path.stat()
    except OSError:
        return None
    # The file id (inode) changes when a download replaces the file, even when a coarse clock
    # gives the new file the same size and time.
    key = (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ino, stat.st_ctime_ns)
    if key not in _HASHES:
        _HASHES[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return _HASHES[key]


def _file_matches(path: Path, sha256: str) -> bool:
    return path.is_file() and _file_hash(path) == sha256


def tessdata_dir(variant: str) -> Path:
    """Where a variant's data lives.

    Order: EVRAKCI_TESSDATA_<VARIANT>, then the copy bundled with the installed app (only if it
    verifies; bundled files are never deleted), then the app data folder.
    """
    configured = os.environ.get(f"EVRAKCI_TESSDATA_{variant.upper()}")
    if configured:
        return Path(configured)
    bundle = app_dir()
    if bundle is not None:
        bundled = bundle / f"tessdata_{variant}"
        if _file_matches(bundled / "tur.traineddata", TESSDATA_VARIANTS[variant].sha256):
            return bundled
    return data_dir() / f"tessdata_{variant}"


def verify_tessdata(variant: str, folder: Path | None = None) -> bool:
    """True if the folder holds the correct tur.traineddata.

    A wrong file is deleted only in the app's own download folder; a folder an admin
    configured, or the bundled copy, is never touched.
    """
    folder = Path(folder or tessdata_dir(variant))
    path = folder / "tur.traineddata"
    if not path.is_file():
        return False
    if _file_hash(path) == TESSDATA_VARIANTS[variant].sha256:
        return True
    if folder.resolve() == (data_dir() / f"tessdata_{variant}").resolve():
        path.unlink()
    return False


def tessdata_best_dir() -> Path:
    return tessdata_dir("best")


def verify_tur_best(folder: Path) -> bool:
    return verify_tessdata("best", folder)


def _windows_short_path(path: Path) -> Path:
    """Windows' 8.3 short form of a path (ASCII when short names are enabled)."""
    import ctypes

    buffer = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer)):  # type: ignore[attr-defined]
        return Path(buffer.value)
    return path


def _tree_digest(folder: Path) -> str | None:
    """One hash over every file in a folder (names and contents), or None if it is empty."""
    folder = Path(folder)
    files = sorted(p for p in folder.rglob("*") if p.is_file())
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        content = _file_hash(path)
        if content is None:
            return None
        digest.update(f"{path.relative_to(folder).as_posix()}\0{content}\n".encode())
    return digest.hexdigest()


def _prune_copies(root: Path, keep: str) -> None:
    """Remove older data copies, and copies left half-made more than an hour ago."""
    now = time.time()
    for path in root.glob("tessdata-*"):
        try:
            stale = path.name.endswith(".tmp") and now - path.stat().st_mtime > 3600
            if path.name != keep and (stale or not path.name.endswith(".tmp")):
                shutil.rmtree(path, ignore_errors=True)
        except OSError:
            pass


def ascii_safe_dir(
    folder: Path,
    windows: bool | None = None,
    short_path=None,
    copy_root: Path | None = None,
) -> Path:
    """A path to `folder` that Windows Tesseract can open.

    Tesseract on Windows fails on data folders with non-ASCII letters (C:\\Users\\Şükrü\\...).
    Try the short 8.3 path; if that is still not ASCII, use a copy under an ASCII folder.
    A copy is used only when every file in it matches the original.
    """
    folder = Path(folder)
    windows = os.name == "nt" if windows is None else windows
    if not windows or str(folder).isascii():
        return folder
    short = (short_path or _windows_short_path)(folder)
    if str(short).isascii():
        return short
    root = copy_root or ascii_copy_root()
    digest = _tree_digest(folder) or hashlib.sha256(str(folder).encode("utf-8")).hexdigest()
    name = f"tessdata-{digest[:12]}"  # named after the data itself
    target = root / name
    if target.is_dir() and _tree_digest(target) == digest:
        return target
    shutil.rmtree(target, ignore_errors=True)  # changed or planted: never reused
    root.mkdir(parents=True, exist_ok=True)
    _prune_copies(root, keep=name)
    # Copied into a fresh private folder first, so a half-made copy is never handed out.
    partial = Path(tempfile.mkdtemp(prefix=f"{name}-", suffix=".tmp", dir=root))
    try:
        shutil.copytree(folder, partial, dirs_exist_ok=True)
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    try:
        os.rename(partial, target)
        return target
    except OSError:
        if target.is_dir() and _tree_digest(target) == digest:
            shutil.rmtree(partial, ignore_errors=True)
            return target  # another run made the same copy meanwhile
        return partial  # the name is taken by something we cannot trust: use our own copy


def _make_private_dir(path: Path) -> bool:
    """Create a folder only this user can open (owner-only on Windows with Python 3.12.4+)."""
    try:
        os.mkdir(path, 0o700)
        return True
    except FileExistsError:
        return False


def ascii_copy_root(windows: bool | None = None, short_path=None) -> Path:
    """Where ASCII-path copies and temp folders go: EVRAKCI_ASCII_KOK, or a folder of this
    user's own.

    First the user's own local app folder, through its short 8.3 path. Only when that is not
    ASCII, a private folder under ProgramData (an ASCII path): its random name is kept in the
    user's own profile, so no other user can guess it or create it in advance.
    """
    configured = os.environ.get("EVRAKCI_ASCII_KOK")
    if configured:
        return Path(configured)
    windows = os.name == "nt" if windows is None else windows
    local_root = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    local = Path(local_root) / "Evrakci" / "ascii"
    local.mkdir(parents=True, exist_ok=True)
    short = (short_path or _windows_short_path)(local) if windows else local
    if str(short).isascii():
        return short
    shared = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Evrakci"
    shared.mkdir(parents=True, exist_ok=True)
    record = local.parent / "ascii-klasoru.txt"
    try:
        name = record.read_text(encoding="utf-8").strip()
    except OSError:
        name = ""
    if re.fullmatch(r"u-[0-9a-f]{32}", name) and (shared / name).is_dir():
        return shared / name
    while True:
        name = f"u-{uuid.uuid4().hex}"
        if _make_private_dir(shared / name):
            record.write_text(name, encoding="utf-8")
            return shared / name


def system_tessdata() -> Path | None:
    """The language data folder of the installed Tesseract."""
    binary = find_tesseract()
    if binary is None:
        return None
    env = os.environ.copy()  # one snapshot: other threads may change os.environ meanwhile
    prefix = env.pop("TESSDATA_PREFIX", None)
    try:
        out = subprocess.run(
            [str(binary), "--list-langs"], capture_output=True, text=True, encoding="utf-8",
            errors="replace", check=False, env=env, timeout=_LIST_TIMEOUT, **no_window(),
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    return tessdata_from_list_langs(out, binary, prefix=prefix)


def tessdata_from_list_langs(output: str, binary: Path, prefix: str | None = None) -> Path | None:
    """The data folder from `tesseract --list-langs`.

    Tesseract 5 names it on the first line; Tesseract 4 (e.g. Ubuntu 22.04) does not, so then
    TESSDATA_PREFIX and the usual folders near the program are tried.
    """
    first = output.splitlines()[0] if output else ""
    if first.count('"') >= 2:
        return Path(first.split('"')[1])
    program = Path(binary).resolve().parent
    share = program.parent / "share"
    candidates = [Path(prefix), Path(prefix) / "tessdata"] if prefix else []
    candidates += [
        *sorted(share.glob("tesseract-ocr/*/tessdata"), reverse=True),
        share / "tessdata",
        share / "tesseract" / "tessdata",  # RHEL, Fedora
        program / "tessdata",  # Windows builds keep it beside the program
    ]
    return next((c for c in candidates if (c / "configs" / "hocr").is_file()), None)


_ENGLISH_TRIED: set[Path] = set()  # folders where adding eng.traineddata was tried


def prepare_tessdata(folder: Path) -> None:
    """Copy Tesseract's small output config folders into a separate data folder.

    Tesseract looks for its `hocr`, `txt` and `tsv` configs next to the language data.
    Tesseract 4 also lists no language at all unless eng.traineddata is there, so the system's
    copy is added too (best effort: a read-only bundle ships its own).
    """
    has_configs = (folder / "configs" / "hocr").is_file()
    if has_configs and ((folder / "eng.traineddata").is_file() or folder in _ENGLISH_TRIED):
        return
    _ENGLISH_TRIED.add(folder)
    source = system_tessdata()
    if source is not None:
        if not has_configs:
            for name in ("configs", "tessconfigs"):
                if (source / name).is_dir() and not (folder / name).is_dir():
                    shutil.copytree(source / name, folder / name)
        english = source / "eng.traineddata"
        if english.is_file() and not (folder / "eng.traineddata").exists():
            try:
                shutil.copy2(english, folder / "eng.traineddata")
            except OSError:
                pass
    if not (folder / "configs" / "hocr").is_file():
        raise EngineUnavailable(f"Tesseract ayar dosyaları bulunamadı (configs): {folder}")


@dataclass(frozen=True)
class TessData:
    language: str
    folder: Path | None  # None: the system folder


def default_tessdata() -> TessData:
    """tur_best when it is installed and verified, otherwise the system's tur."""
    if find_tesseract() is None:  # no program: the caller reports "Tesseract bulunamadı"
        return TessData("tur", None)
    best = tessdata_best_dir()
    # Config files are added by the text layer itself (add_text_layer), which needs them;
    # reading boxes does not, so a missing config never blocks it.
    return TessData("tur", best) if verify_tur_best(best) else TessData("tur", None)


def find_tesseract() -> Path | None:
    """EVRAKCI_TESSERACT, then the copy bundled with the app, then PATH, then usual folders."""
    configured = os.environ.get("EVRAKCI_TESSERACT")
    if configured:  # an admin's explicit choice: never silently replaced by another program
        return Path(configured) if Path(configured).is_file() else None
    bundle = app_dir()
    if bundle is not None:
        name = "tesseract.exe" if os.name == "nt" else "tesseract"
        if (bundle / "tesseract" / name).is_file():
            return bundle / "tesseract" / name
    found = shutil.which("tesseract")
    if found:
        return Path(found)
    return next((p for p in _WINDOWS_PATHS if p.is_file()), None)


class TesseractEngine:
    def __init__(
        self, lang: str = "tur", tessdata_dir: Path | None = None, name: str = "tesseract-tur"
    ) -> None:
        self.lang = lang
        self.tessdata_dir = Path(tessdata_dir) if tessdata_dir else None
        self.name = name
        self._checked = False
        self._reason: str | None = None

    def available(self) -> str | None:
        if not self._checked:
            self._reason = self._check()
            self._checked = True
        return self._reason

    def _check(self) -> str | None:
        configured = os.environ.get("EVRAKCI_TESSERACT")
        if configured and not Path(configured).is_file():
            return f"EVRAKCI_TESSERACT ayarındaki program bulunamadı: {configured}"
        binary = find_tesseract()
        if binary is None:
            return "Tesseract programı bulunamadı"
        if self.tessdata_dir is not None:
            if not (self.tessdata_dir / f"{self.lang}.traineddata").is_file():
                return f"'{self.lang}' dil verisi bulunamadı: {self.tessdata_dir}"
            return None
        try:
            result = subprocess.run(
                [str(binary), "--list-langs"], capture_output=True, text=True, encoding="utf-8",
                errors="replace", check=False, timeout=_LIST_TIMEOUT, **no_window(),
            )
        except subprocess.TimeoutExpired:
            return "Tesseract yanıt vermedi"
        except OSError as error:
            return f"Tesseract çalıştırılamadı: {error}"
        languages = result.stdout.split()
        if self.lang not in languages:
            return f"'{self.lang}' dil verisi kurulu değil"
        return None

    def _run(self, image: Image.Image, psm: int) -> list[Word]:
        reason = self.available()
        if reason:
            raise EngineUnavailable(reason)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        command = [str(find_tesseract()), "stdin", "stdout", "-l", self.lang, "--psm", str(psm)]
        if self.tessdata_dir is not None:
            command += ["--tessdata-dir", str(ascii_safe_dir(self.tessdata_dir))]
        # Pages are rendered at 300 dpi; one thread per call is much faster on small boxes.
        command += ["--dpi", "300", "-c", "tessedit_create_tsv=1"]  # no "tsv" config needed
        env = {**os.environ, "OMP_THREAD_LIMIT": "1"}
        try:
            result = subprocess.run(
                command, input=buffer.getvalue(), capture_output=True, check=False, env=env,
                timeout=_READ_TIMEOUT, **no_window(),
            )
        except subprocess.TimeoutExpired:
            raise EngineUnavailable("Tesseract yanıt vermedi") from None
        except OSError as error:
            raise EngineUnavailable(f"Tesseract çalıştırılamadı: {error}") from None
        if result.returncode != 0:
            message = result.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            raise EngineUnavailable(f"Tesseract hata verdi: {' '.join(message)}")
        rows = csv.DictReader(
            io.StringIO(result.stdout.decode("utf-8", "replace")), delimiter="\t",
            quoting=csv.QUOTE_NONE,
        )
        words = []
        for row in rows:
            text = (row.get("text") or "").strip()
            if row.get("level") != "5" or not text:
                continue
            left, top = int(row["left"]), int(row["top"])
            box = (left, top, left + int(row["width"]), top + int(row["height"]))
            words.append(Word(nfc(text), box, max(float(row["conf"]), 0.0) / 100))
        return words

    def read_page(self, image: Image.Image) -> list[Word]:
        return self._run(image, psm=3)

    def read_region(self, image: Image.Image) -> Reading:
        return reading_from_words(self._run(image, psm=6))


def default_engine() -> TesseractEngine:
    data = default_tessdata()
    name = "tesseract-tur_best" if data.folder else "tesseract-tur"
    return TesseractEngine(data.language, tessdata_dir=data.folder, name=name)
