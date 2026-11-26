"""Templates on disk: one UTF-8 JSON file per template, plus import and export."""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
import unicodedata
import uuid
from collections.abc import Callable
from pathlib import Path

from evrakci.pipeline.ocr.models import data_dir
from evrakci.pipeline.templates.model import (
    Template,
    TemplateError,
    template_from_dict,
    template_to_dict,
)

_ID = re.compile(r"[0-9a-f]{1,32}")


def _umask() -> int:
    current = os.umask(0o022)
    os.umask(current)
    return current


_FILE_MODE = 0o666 & ~_umask()  # what a normal new file gets (mkstemp would give 0600)


def default_template_root() -> Path:
    configured = os.environ.get("EVRAKCI_SABLON_KOK")
    return Path(configured) if configured else data_dir() / "templates"


def _atomic(path: Path, data: bytes) -> None:
    """Write `data` to a temporary file in the same folder, then replace `path` in one step:
    a crash leaves the old file or the new one, never half of either."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".sablon-", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
        os.chmod(temporary, _FILE_MODE)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write(path: Path, template: Template) -> None:
    text = json.dumps(template_to_dict(template), ensure_ascii=False, indent=1)
    _atomic(path, text.encode("utf-8"))


TRASH = "silinenler"  # deleted templates wait here
MAX_NAME = 100
INVALID_NAME = ("Şablon adı geçersiz: en çok 100 karakter olabilir; { }, satır sonu ve "
                "denetim karakterleri olamaz.")


def clean_name(name: str) -> str:
    """The name as stored: trimmed, NFC. A control character (NUL, newline), a brace (the
    file-name pattern's own syntax) or more than MAX_NAME characters is refused (F-sablonlar-25)."""
    name = unicodedata.normalize("NFC", name or "").strip()
    if not name:
        raise TemplateError("Şablon adı boş olamaz.")
    if (len(name) > MAX_NAME or "{" in name or "}" in name
            or any(unicodedata.category(c).startswith("C") for c in name)):
        raise TemplateError(INVALID_NAME)
    return name


def _read(path: Path, label: str) -> Template:
    try:
        # utf-8-sig: files re-saved in Windows Notepad start with a byte-order mark.
        return template_from_dict(json.loads(path.read_text(encoding="utf-8-sig")))
    # TemplateError is a ValueError; huge numbers and deep nesting raise the other two.
    except (OSError, ValueError, OverflowError, RecursionError) as error:
        raise TemplateError(f"Şablon dosyası okunamadı: {label} ({error})") from error


class TemplateStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _path(self, template_id: str) -> Path:
        if not _ID.fullmatch(template_id or ""):
            raise KeyError(template_id)  # ids are hex; anything else never touches the disk
        return self.root / f"{template_id}.json"

    def unique_name(self, name: str, exclude: str | None = None) -> str:
        """`name`, or "name (2)", "name (3)"... when another template (not `exclude`) has it."""
        return self._unique_name(name, exclude)

    def _unique_name(self, name: str, exclude: str | None = None) -> str:
        name = unicodedata.normalize("NFC", name)
        names = {t.name for t in self.list() if t.id != exclude}
        if name not in names:
            return name
        number = 2
        while f"{name} ({number})" in names:
            number += 1
        return f"{name} ({number})"

    def create(self, name: str) -> Template:
        name = clean_name(name)
        template = Template(id=uuid.uuid4().hex[:10], name=self._unique_name(name))
        self.save(template)
        return template

    def save(self, template: Template) -> None:
        _write(self._path(template.id), template)

    def load(self, template_id: str) -> Template:
        path = self._path(template_id)
        if not path.is_file():
            raise KeyError(template_id)
        template = _read(path, template_id)
        # The file name is the id: a copied or renamed file must never write over another.
        template.id = template_id
        return template

    def list(self, on_error: Callable[[str], None] | None = None) -> list[Template]:
        if not self.root.is_dir():
            return []
        templates = []
        for path in self.root.glob("*.json"):
            try:
                templates.append(self.load(path.stem))
            except (TemplateError, KeyError):
                if on_error:
                    on_error(path.stem)
        return sorted(templates, key=lambda t: (t.name.casefold(), t.id))

    def rename(self, template_id: str, name: str) -> Template:
        """A new name (made unique like a new template's); everything else stays as it is."""
        name = clean_name(name)
        template = self.load(template_id)
        template.name = self._unique_name(name, exclude=template_id)
        self.save(template)
        return template

    def duplicate(self, template_id: str) -> Template:
        """A copy under a new id: "Ad (kopya)", every variable, box and setting the same."""
        source = self.load(template_id)
        copy = template_from_dict(template_to_dict(source))
        copy.id = uuid.uuid4().hex[:10]
        copy.name = self._unique_name(f"{source.name} (kopya)")
        self.save(copy)
        return copy

    def delete(self, template_id: str) -> str:
        """Move the file into the hidden "silinenler" folder (one atomic rename), never unlink
        it: nothing is gone for good. Returns the name to give `undelete`."""
        path = self._path(template_id)
        if not path.is_file():
            raise KeyError(template_id)
        trash = self.root / TRASH
        trash.mkdir(parents=True, exist_ok=True)
        token = f"{template_id}-{time.time_ns()}.json"
        os.replace(path, trash / token)
        return token

    def undelete(self, template_id: str, token: str, name: str = "") -> None:
        """Move a deleted file back, byte for byte. Never writes over a file that exists now
        (a template made meanwhile with that id keeps its place)."""
        path = self._path(template_id)
        source = self.root / TRASH / Path(token).name
        if not source.is_file():
            raise TemplateError(f"Silinen şablon bulunamadı: {name or template_id}")
        try:
            os.link(source, path)  # fails if `path` exists: no overwrite, even in a race
        except FileExistsError:
            raise TemplateError(f"Bu şablon zaten var: {name or template_id}") from None
        except OSError:  # a file system without hard links
            if path.exists():
                raise TemplateError(f"Bu şablon zaten var: {name or template_id}") from None
            os.rename(source, path)
            return
        source.unlink()

    def export(self, template_id: str, path: Path) -> None:
        """Write the template to `path` without ever replacing a file: a temporary file in the
        same folder is written whole, then linked to its name (which fails if it exists)."""
        path = Path(path)
        template = self.load(template_id)
        if not path.parent.is_dir():
            raise TemplateError(f"Klasör bulunamadı: {path.parent}")
        text = json.dumps(template_to_dict(template), ensure_ascii=False, indent=1)
        handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".sablon-", suffix=".tmp")
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as out:
                out.write(text)
            os.chmod(temporary, _FILE_MODE)
            try:
                os.link(temporary, path)
            except FileExistsError:
                raise TemplateError(
                    f"Bu adla bir dosya zaten var: {path.name}. Başka bir ad seçin.") from None
            except OSError:  # no hard links here: check, then rename
                if path.exists():
                    raise TemplateError(
                        f"Bu adla bir dosya zaten var: {path.name}. Başka bir ad seçin.") from None
                os.rename(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def import_file(self, path: Path) -> Template:
        path = Path(path)
        if not path.is_file():
            raise TemplateError(f"Dosya bulunamadı: {path.name}")
        template = _read(path, path.name)
        template.id = uuid.uuid4().hex[:10]  # never trust an id (or path) from a file
        try:
            name = clean_name(template.name)
        except TemplateError as error:
            raise TemplateError(f"{path.name}: {error}") from None
        template.name = self._unique_name(name)
        self.save(template)
        return template
