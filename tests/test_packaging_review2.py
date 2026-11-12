"""Plan 6 second fresh review (2026-11-09): every finding that can be tested here, red first."""

import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))


def fake_lib(lib, *names):
    """A lib/ folder holding one real file of each distribution, as cx_Freeze would."""
    from importlib import metadata

    for name in names:
        for file in metadata.distribution(name).files:
            text = str(file)
            if ".dist-info" not in text and "__pycache__" not in text and not text.endswith(
                    ".pyi") and "/" in text and not text.startswith(".."):
                target = Path(lib) / text
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("x")
                break
    return Path(lib)


def touch(path: Path, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


# --- 1: GPL-only libraries from the Tesseract build ------------------------------------------

@pytest.mark.parametrize("name", ["libjbig-0.dll", "libjbig.so.2", "jbig.dll", "libjbig85.dll"])
def test_jbig_kit_is_refused(tmp_path, name):
    import gpl_check

    path = touch(tmp_path / "tesseract" / name)
    assert gpl_check.forbidden_libraries(tmp_path) == [path]


# --- 1, 2, 3: Tesseract built by vcpkg, staged with an allow-list and every licence ------------

def fake_vcpkg(root: Path, ports: list[str]) -> Path:
    installed = root / "x64-windows-static-release"
    info = root / "vcpkg" / "info"  # vcpkg's own record of what it installed
    for port in ports:
        touch(info / f"{port}_1.0_x64-windows-static-release.list")
    touch(info / "vcpkg-cmake_2024_x64-windows.list")  # a build helper, for the build machine
    touch(installed / "tools" / "tesseract" / "tesseract.exe", "MZ")
    touch(installed / "share" / "tessdata" / "configs" / "hocr", "tessedit_create_hocr 1")
    touch(installed / "share" / "tessdata" / "tessconfigs" / "nobatch", "")
    for port in ports:
        touch(installed / "share" / port / "copyright", f"{port} licence text")
    for helper in ("vcpkg-cmake", "vcpkg-cmake-config"):  # build helpers: not shipped
        touch(installed / "share" / helper / "copyright", "MIT")
    return installed


def test_stage_takes_the_program_configs_and_every_licence(tmp_path):
    import stage_tesseract

    installed = fake_vcpkg(tmp_path, sorted(stage_tesseract.ALLOWED_PORTS))
    target = tmp_path / "bundle"
    stage_tesseract.stage_vcpkg(installed, target)
    assert (target / "tesseract.exe").read_text() == "MZ"
    assert (target / "tessdata" / "configs" / "hocr").is_file()
    for port in stage_tesseract.ALLOWED_PORTS:
        assert (target / "licenses" / f"{port}.txt").read_text() == f"{port} licence text"
    assert not (target / "licenses" / "vcpkg-cmake.txt").exists()


def test_stage_refuses_a_port_that_is_not_on_the_allow_list(tmp_path):
    import stage_tesseract

    installed = fake_vcpkg(tmp_path, [*sorted(stage_tesseract.ALLOWED_PORTS), "jbigkit"])
    with pytest.raises(SystemExit):
        stage_tesseract.stage_vcpkg(installed, tmp_path / "bundle")


def test_stage_refuses_a_port_without_a_licence(tmp_path):
    import stage_tesseract

    installed = fake_vcpkg(tmp_path, sorted(stage_tesseract.ALLOWED_PORTS))
    (installed / "share" / "tiff" / "copyright").unlink()
    with pytest.raises(SystemExit):
        stage_tesseract.stage_vcpkg(installed, tmp_path / "bundle")


def test_allowed_ports_are_permissive_and_in_the_notice():
    import stage_tesseract

    notice = (ROOT / "packaging" / "licenses" / "NOTICE.txt").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "dependency-licenses.md").read_text(encoding="utf-8")
    for port, licence in stage_tesseract.ALLOWED_PORTS.items():
        assert not re.search(r"\bGPL", licence.replace("LGPL", "")), (port, licence)
        assert port in notice and port in docs, port


def test_vcpkg_manifest_builds_tesseract_without_curl_or_libarchive():
    import json

    manifest = json.loads((ROOT / "packaging" / "vcpkg" / "vcpkg.json").read_text())
    [tesseract] = [d for d in manifest["dependencies"] if d["name"] == "tesseract"]
    assert tesseract["default-features"] is False and not tesseract.get("features")
    assert re.fullmatch(r"[0-9a-f]{40}", manifest["builtin-baseline"])
    triplet = (ROOT / "packaging" / "vcpkg" / "triplets" / "x64-windows-static-release.cmake")
    text = triplet.read_text()
    assert "VCPKG_LIBRARY_LINKAGE static" in text and "VCPKG_BUILD_TYPE release" in text


# --- 4: licences of what is really in the build -------------------------------------------------

def test_licences_come_from_the_build_folder_not_from_metadata(tmp_path):
    import collect_licenses

    lib = fake_lib(tmp_path / "lib", "pypdfium2", "pikepdf", "jsonschema", "pillow")
    out = tmp_path / "licenses"
    shipped = collect_licenses.collect_from_build(lib, out, own="evrakci")
    names = {d.lower() for d in shipped}
    assert {"pypdfium2", "pikepdf", "jsonschema", "pillow"} <= names
    versions = (out / "VERSIONS.txt").read_text(encoding="utf-8").lower()
    assert "jsonschema==" in versions
    # Licence files listed as License-File, not only names like LICENSE: PDFium's own.
    assert list((out / "python" / "pypdfium2").rglob("BSD-3-Clause*"))
    assert not list(out.rglob("LicenseRef-Qt-Commercial*"))


def test_a_shipped_package_without_a_licence_file_stops_the_build(tmp_path, monkeypatch):
    import collect_licenses

    lib = fake_lib(tmp_path / "lib", "pikepdf")
    monkeypatch.setattr(collect_licenses, "_licence_files", lambda dist: [])
    with pytest.raises(SystemExit):
        collect_licenses.collect_from_build(lib, tmp_path / "out", own="evrakci")


def test_undocumented_packages_are_found():
    import collect_licenses

    doc = "| pikepdf | MPL-2.0 |"
    assert collect_licenses.undocumented(["pikepdf", "rpds-py", "jsonschema"], doc) == [
        "jsonschema", "rpds-py"]


def test_every_package_in_a_real_build_listing_is_documented():
    import collect_licenses

    listing = (ROOT / "packaging" / "shipped-packages.txt").read_text(encoding="utf-8")
    shipped = [line.split("==")[0] for line in listing.splitlines() if line.strip()]
    doc = (ROOT / "docs" / "dependency-licenses.md").read_text(encoding="utf-8")
    assert collect_licenses.undocumented(shipped, doc) == []


# --- 5, 8, 11: what goes where in the build ---------------------------------------------------

def test_tesseract_is_placed_after_the_freeze_never_scanned_by_cx_freeze(tmp_path):
    import layout

    stage = tmp_path / "stage"
    touch(stage / "tesseract" / "tesseract.exe")
    touch(stage / "licenses" / "NOTICE.txt")
    touch(stage / "tessdata_best" / "tur.traineddata")
    entries = {Path(target).parts[0] for _, target in layout.freeze_include_files(stage)}
    assert "tesseract" not in entries and {"licenses", "tessdata_best"} <= entries
    build = tmp_path / "build"
    build.mkdir()
    layout.place_after_freeze(stage, build)
    assert (build / "tesseract" / "tesseract.exe").is_file()


def test_unused_qt_pdf_parts_are_removed(tmp_path):
    import layout

    keep = touch(tmp_path / "lib/PySide6/plugins/imageformats/qjpeg.dll")
    gone = [touch(tmp_path / "lib/PySide6/plugins/imageformats/qpdf.dll"),
            touch(tmp_path / "lib/PySide6/Qt6Pdf.dll"),
            touch(tmp_path / "lib/PySide6/Qt/lib/libQt6Pdf.so.6"),
            touch(tmp_path / "lib/PySide6/Qt/plugins/imageformats/libqpdf.so")]
    removed = layout.remove_unused_qt(tmp_path)
    assert sorted(removed) == sorted(gone) and keep.exists()


def test_python_licence_is_shipped(tmp_path, monkeypatch):
    import layout

    licence = touch(tmp_path / "py" / "LICENSE.txt", "PSF and third-party notices")
    monkeypatch.setattr(layout, "python_licence_candidates", lambda: [licence])
    out = tmp_path / "licenses"
    layout.copy_python_licence(out)
    assert (out / "Python-LICENSE.txt").read_text() == "PSF and third-party notices"


def test_notice_names_windows_runtime_and_qt_third_party_parts():
    notice = (ROOT / "packaging" / "licenses" / "NOTICE.txt").read_text(encoding="utf-8")
    for text in ("Python-LICENSE.txt", "Microsoft Visual C++", "FreeType Project",
                 "harfbuzz", "libpng", "pcre2", "doc.qt.io"):
        assert text in notice, text
    docs = (ROOT / "docs" / "dependency-licenses.md").read_text(encoding="utf-8")
    assert "PySide6_Pdf" not in docs or "removed" in docs


# --- 13: the smoke test can prove which data was used, and worker processes ----------------------

def test_ocr_command_says_which_data_it_used(tmp_path, monkeypatch, capsys):
    from evrakci.cli import ocr as cli_ocr
    from evrakci.pipeline.ocr.tesseract import TessData
    from evrakci.pipeline.ocr.textlayer import TextLayerResult

    src = touch(tmp_path / "a.pdf")

    def layer(giris, cikti, tessdata=None, pdfa=True, **kwargs):
        assert tessdata.folder == tmp_path / "best"
        Path(cikti).write_bytes(b"%PDF")
        return TextLayerResult(Path(cikti), True)

    monkeypatch.setattr(cli_ocr, "add_text_layer", layer)
    monkeypatch.setattr(cli_ocr, "default_tessdata", lambda: TessData("tur", tmp_path / "best"))
    from evrakci.cli import main

    assert main(["ocr", str(src), str(tmp_path / "b.pdf")]) == 0
    assert "OCR verisi: tur_best" in capsys.readouterr().out


def test_worker_processes_can_be_asked_for(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr import textlayer

    seen = {}

    def fake_ocr(src, dst, **kwargs):
        seen.update(kwargs)
        return 0

    monkeypatch.setattr(textlayer.ocrmypdf, "ocr", fake_ocr)
    monkeypatch.setenv("EVRAKCI_OCR_SURECLER", "1")
    textlayer._run(tmp_path / "a.pdf", tmp_path / "b.pdf",
                   textlayer.TessData("tur", None), "pdf", None)
    assert seen["use_threads"] is False


# --- 15: installer script ----------------------------------------------------------------------

def iss() -> str:
    return (ROOT / "packaging" / "evrakci.iss").read_text(encoding="utf-8-sig")


def test_path_entry_is_removed_wherever_it_sits():
    text = iss()
    assert "Current := ';' + Current + ';'" in text
    assert "{olddata};{app}" not in text  # added by code, without doubled separators


def test_upgrade_clears_root_runtime_files_and_uninstall_touches_only_this_user():
    text = iss()
    assert 'Name: "{app}\\*.dll"' in text and 'Name: "{app}\\share"' in text
    assert "{commonappdata}\\Evrakci" not in text.split("[UninstallDelete]")[1].split("[")[0]
    assert "ascii-klasoru.txt" in text


# --- 10, 12, 14, 16: the workflow ---------------------------------------------------------------

def workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", ["windows-installer.yml", "linux-build.yml", "ci.yml"])
def test_actions_are_pinned_to_commits(name):
    uses = re.findall(r"uses:\s*([^\s#]+)", workflow(name))
    assert uses and all(re.search(r"@[0-9a-f]{40}$", u) for u in uses), uses


@pytest.mark.parametrize("name", ["windows-installer.yml", "linux-build.yml"])
def test_build_dependencies_are_installed_from_a_hashed_lock(name):
    text = workflow(name)
    assert "--require-hashes" in text and "requirements-build.txt" in text
    lock = (ROOT / "packaging" / "requirements-build.txt").read_text(encoding="utf-8")
    assert "--hash=sha256:" in lock and "cx-freeze==" in lock.lower()


def test_windows_workflow_runs_the_installer_and_the_real_window():
    text = workflow("windows-installer.yml")
    assert "timeout-minutes" in text
    assert "/VERYSILENT" in text and "/CURRENTUSER" in text and "unins000.exe" in text
    assert "qwindows.dll" in text
    assert "EVRAKCI_TESSDATA_BEST" in text  # tests run with tur_best, nothing skipped
    assert "vcpkg" in text and "choco install tesseract" not in text
    assert "EVRAKCI_OCR_SURECLER" in text
    assert "evrakci.__version__" in text and "GITHUB_REF_NAME" in text


def test_workflows_follow_work_branches_without_naming_one():
    for name in ("windows-installer.yml", "linux-build.yml"):
        assert "claude/intelligent-fermi-6e3g7l" not in workflow(name)


@pytest.mark.parametrize("name", ["ocrmypdf/_exec/jbig2enc.pyc", "pikepdf/jbig2.pyc",
                                  "pdfminer/jbig2.py", "libjbig2dec.so.0"])
def test_jbig2_python_modules_are_not_jbig_kit(tmp_path, name):
    import gpl_check

    touch(tmp_path / "lib" / name)
    assert gpl_check.forbidden_libraries(tmp_path) == []


def test_a_package_ships_only_when_its_own_files_are_in_the_build(tmp_path):
    import collect_licenses

    lib = tmp_path / "lib"
    (lib / "PySide6").mkdir(parents=True)
    touch(lib / "PySide6" / "QtCore.abi3.so")  # an Essentials file, not a Pdf one
    from importlib import metadata

    dists = {d.metadata["Name"] for d in collect_licenses._shipped_distributions(lib, "evrakci")}
    assert "PySide6_Essentials" in dists or not any(
        str(f).endswith("QtCore.abi3.so") for f in metadata.distribution(
            "PySide6_Essentials").files)
    assert "PySide6_Pdf" not in dists and "PySide6_WebEngine" not in dists


def test_pyside6_licence_points_to_the_shipped_lgpl_text(tmp_path):
    import collect_licenses

    lib = tmp_path / "lib"
    (lib / "shiboken6").mkdir(parents=True)
    for f in __import__("importlib.metadata").metadata.distribution("shiboken6").files:
        if str(f).startswith("shiboken6/") and not str(f).endswith(".pyi"):
            touch(lib / str(f))
            break
    collect_licenses.collect_from_build(lib, tmp_path / "out")
    note = (tmp_path / "out" / "python" / "shiboken6" / "LICENSE-NOTE.txt").read_text()
    assert "LGPL-3.0.txt" in note


def test_packages_never_needed_are_excluded_from_the_freeze():
    text = (ROOT / "packaging" / "freeze_setup.py").read_text(encoding="utf-8")
    for name in ("numpy", "requests", "yaml", "dotenv", "dateutil", "certifi", "urllib3"):
        assert f'"{name}"' in text, name


def test_scripts_print_turkish_on_a_non_utf8_console(tmp_path):
    # stdout is strict on a cp1252 console (stderr only escapes); both lines are Turkish.
    import subprocess

    env = {**os.environ, "PYTHONIOENCODING": "cp1252:strict", "PYTHONUTF8": "0"}
    build = tmp_path / "derleme"
    for name in ("evrakci", "evrakci-arayuz"):
        touch(build / name)
    for script, args in (("build.py", ["--kontrol"]),
                         ("linux_package.py", ["--build", str(build), "--cikti",
                                               str(tmp_path / "çıktı"), "--surum", "1"])):
        result = subprocess.run([sys.executable, str(ROOT / "packaging" / script), *args],
                                capture_output=True, env=env, cwd=tmp_path)
        assert result.returncode == 0, result.stderr[-600:]


def test_installer_code_uses_no_pascal_reserved_words_as_names():
    reserved = {"record", "type", "file", "set", "label", "object", "string", "array", "case",
                "class", "const", "var", "in", "of", "to", "with", "unit", "packed", "goto"}
    code = iss().split("[Code]", 1)[1]
    names = set()
    for block in re.findall(r"\bvar\b(.*?)\bbegin\b", code, re.S | re.I):
        for line in block.split(";"):
            if ":" in line:
                names |= {n.strip().lower() for n in line.split(":")[0].split(",")}
    assert not names & reserved, names & reserved
