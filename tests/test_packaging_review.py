"""Plan 6 review findings: licences, shared folders, GUI smoke, installer details."""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def test_every_shipped_package_is_in_the_dependency_licence_list():
    import build
    from collect_licenses import _closure

    doc = _norm((ROOT / "docs" / "dependency-licenses.md").read_text(encoding="utf-8"))
    missing = [d.metadata["Name"] for d in _closure(build.BUNDLED)
               if _norm(d.metadata["Name"]) not in doc and d.metadata["Name"] != "evrakci"]
    assert missing == []


def test_build_tool_cx_freeze_is_not_listed_as_shipped():
    import build

    assert "cx_Freeze" not in build.BUNDLED


def test_ascii_copies_live_in_a_folder_of_their_own_per_user(monkeypatch, tmp_path):
    from evrakci.pipeline.ocr.tesseract import ascii_copy_root

    monkeypatch.delenv("EVRAKCI_ASCII_KOK", raising=False)
    monkeypatch.setenv("ProgramData", str(tmp_path))
    monkeypatch.setenv("USERNAME", "Şükrü")
    first = ascii_copy_root()
    monkeypatch.setenv("USERNAME", "Ayşe")
    assert first != ascii_copy_root()
    assert first.parent == tmp_path / "Evrakci" and str(first).isascii()


def test_a_tampered_ascii_copy_is_not_reused(tmp_path):
    from evrakci.pipeline.ocr.tesseract import ascii_safe_dir

    source = tmp_path / "Veri Ğ"
    source.mkdir()
    (source / "tur.traineddata").write_bytes(b"real data")
    root = tmp_path / "ascii"
    digest = hashlib.sha256(b"real data").hexdigest()[:12]
    planted = root / f"tessdata-{digest}"
    planted.mkdir(parents=True)
    (planted / "tur.traineddata").write_bytes(b"fake")
    result = ascii_safe_dir(source, windows=True, short_path=lambda p: p, copy_root=root)
    assert (result / "tur.traineddata").read_bytes() == b"real data"


def test_the_window_can_start_and_close_itself_for_a_smoke_test(tmp_path):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", EVRAKCI_KAPAT_MS="300",
               EVRAKCI_KOK=str(tmp_path / "jobs"), EVRAKCI_SABLON_KOK=str(tmp_path / "tpl"),
               EVRAKCI_AYARLAR=str(tmp_path / "ayar.json"))
    result = subprocess.run([sys.executable, "-m", "evrakci.app"], env=env, timeout=60,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_ci_starts_the_window_and_checks_the_guide():
    workflow = (ROOT / ".github" / "workflows" / "windows-installer.yml").read_text(
        encoding="utf-8")
    assert "evrakci-arayuz.exe" in workflow and "EVRAKCI_KAPAT_MS" in workflow
    assert "tarama-rehberi.md" in workflow  # paths filter and the bundled-file check


def test_uninstall_removes_only_the_exact_path_entry():
    script = (ROOT / "packaging" / "evrakci.iss").read_text(encoding="utf-8-sig")
    assert "Folder := ';' + ExpandConstant('{app}') + ';'" in script


def test_licence_files_with_the_same_name_do_not_overwrite_each_other(tmp_path, monkeypatch):
    import collect_licenses

    class File:
        def __init__(self, path):
            self.path = Path(path)
            self.name = self.path.name
            self.parent = self.path.parent

        def __str__(self):
            return str(self.path)

    sources = tmp_path / "site"
    for rel in ("pkg-1.0.dist-info/licenses/a/LICENSE", "pkg-1.0.dist-info/licenses/b/LICENSE"):
        (sources / rel).parent.mkdir(parents=True, exist_ok=True)
        (sources / rel).write_text(rel)

    class Dist:
        metadata = {"Name": "pkg", "License-Expression": "MIT"}
        version = "1.0"
        files = [File("pkg-1.0.dist-info/licenses/a/LICENSE"),
                 File("pkg-1.0.dist-info/licenses/b/LICENSE")]

        def locate_file(self, file):
            return sources / file.path

    monkeypatch.setattr(collect_licenses, "_closure", lambda names: [Dist()])
    collect_licenses.collect(tmp_path / "out", ["pkg"])
    found = sorted(p.read_text() for p in (tmp_path / "out" / "python" / "pkg").rglob("LICENSE"))
    assert len(found) == 2


def test_notice_names_pillows_licence_as_its_metadata_does():
    notice = (ROOT / "packaging" / "licenses" / "NOTICE.txt").read_text(encoding="utf-8")
    assert re.search(r"Pillow\s+MIT-CMU", notice)


@pytest.mark.parametrize("name", ["EVRAKCI_KOK", "EVRAKCI_SABLON_KOK"])
def test_store_roots_can_be_set_by_environment(name):
    assert name in (ROOT / "src" / "evrakci" / "pipeline" / ("store.py" if name ==
                    "EVRAKCI_KOK" else "templates/store.py")).read_text(encoding="utf-8")
