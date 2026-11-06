"""Collect licence files and exact versions of the Python packages in the build."""

from __future__ import annotations

import re
import shutil
from collections.abc import Iterable
from importlib import metadata
from pathlib import Path

_LICENSE_NAME = re.compile(r"(licen[cs]e|copying|notice|authors)", re.IGNORECASE)


def _closure(names: Iterable[str]) -> list[metadata.Distribution]:
    seen: dict[str, metadata.Distribution] = {}
    pending = list(names)
    while pending:
        name = pending.pop()
        key = re.sub(r"[-_.]+", "-", name).lower()
        if key in seen:
            continue
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        seen[key] = dist
        for requirement in dist.requires or []:
            if "extra ==" in requirement:
                continue
            pending.append(re.split(r"[ ;<>=!~\[(]", requirement, maxsplit=1)[0])
    return sorted(seen.values(), key=lambda d: d.metadata["Name"].lower())


def collect(out_dir: Path, names: Iterable[str]) -> None:
    out_dir = Path(out_dir)
    lines = []
    for dist in _closure(names):
        name, version = dist.metadata["Name"], dist.version
        licence = dist.metadata.get("License-Expression") or dist.metadata.get("License") or ""
        lines.append(f"{name}=={version}  {licence.splitlines()[0] if licence else ''}".rstrip())
        for file in dist.files or []:
            if (
                _LICENSE_NAME.search(file.name)
                and "dist-info" in str(file.parent)
                or (_LICENSE_NAME.search(file.name) and "licenses" in str(file.parent))
            ):
                source = Path(dist.locate_file(file))
                if source.is_file():
                    target = out_dir / "python" / name / file.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "VERSIONS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
