"""Templates on disk: one UTF-8 JSON file per template, plus import and export."""

from __future__ import annotations

import json
import os
import re
import tempfile
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


def _write(path: Path, template: Template) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(template_to_dict(template), ensure_ascii=False, indent=1)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".sablon-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(text)
        os.chmod(temporary, _FILE_MODE)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


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

    def _unique_name(self, name: str) -> str:
        name = unicodedata.normalize("NFC", name)
        names = {t.name for t in self.list()}
        if name not in names:
            return name
        number = 2
        while f"{name} ({number})" in names:
            number += 1
        return f"{name} ({number})"

    def create(self, name: str) -> Template:
        name = name.strip()
        if not name:
            raise TemplateError("Şablon adı boş olamaz.")
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

    def delete(self, template_id: str) -> None:
        path = self._path(template_id)
        if not path.is_file():
            raise KeyError(template_id)
        path.unlink()

    def export(self, template_id: str, path: Path) -> None:
        path = Path(path)
        template = self.load(template_id)
        if not path.parent.is_dir():
            raise TemplateError(f"Klasör bulunamadı: {path.parent}")
        text = json.dumps(template_to_dict(template), ensure_ascii=False, indent=1)
        try:
            # "x": created only if no file has that name, even if one appears meanwhile.
            with open(path, "x", encoding="utf-8") as out:
                try:
                    out.write(text)
                except BaseException:
                    out.close()
                    path.unlink(missing_ok=True)
                    raise
        except FileExistsError:
            raise TemplateError(
                f"Bu adla bir dosya zaten var: {path.name}. Başka bir ad seçin.") from None

    def import_file(self, path: Path) -> Template:
        path = Path(path)
        if not path.is_file():
            raise TemplateError(f"Dosya bulunamadı: {path.name}")
        template = _read(path, path.name)
        template.id = uuid.uuid4().hex[:10]  # never trust an id (or path) from a file
        template.name = self._unique_name(template.name)
        self.save(template)
        return template
