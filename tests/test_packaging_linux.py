"""Linux build: tessdata configs in the bundle, the tarball, and kur.sh / kaldir.sh."""

import os
import shutil
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "packaging" / "build.py"
sys.path.insert(0, str(ROOT / "packaging"))

posix_only = pytest.mark.skipif(os.name == "nt", reason="Linux install scripts")


def fake_configs(folder: Path) -> Path:
    (folder / "configs").mkdir(parents=True)
    (folder / "configs" / "hocr").write_text("tessedit_create_hocr 1\n")
    (folder / "tessconfigs").mkdir()
    (folder / "tessconfigs" / "nobatch").write_text("\n")
    return folder


def run_build(*args):
    return subprocess.run([sys.executable, str(BUILD), *args, "--kontrol"],
                          capture_output=True, text=True)


def test_build_refuses_configs_folder_without_hocr(tmp_path):
    result = run_build("--tessdata-configs", str(tmp_path))
    assert result.returncode != 0 and "configs" in result.stderr


def test_build_accepts_configs_folder(tmp_path):
    result = run_build("--tessdata-configs", str(fake_configs(tmp_path / "td")))
    assert result.returncode == 0, result.stderr


def test_staging_copies_configs_into_tur_best(tmp_path):
    import build
    from evrakci.pipeline.ocr.tesseract import tessdata_dir, verify_tur_best

    best = tessdata_dir("best")
    if not verify_tur_best(best):
        pytest.skip("tur_best not downloaded here")
    stage = tmp_path / "stage"
    build.stage_inputs(None, best / "tur.traineddata", False,
                       configs=fake_configs(tmp_path / "td"), stage=stage)
    assert (stage / "tessdata_best" / "configs" / "hocr").is_file()
    assert (stage / "tessdata_best" / "tessconfigs" / "nobatch").is_file()
    assert (stage / "tessdata_best" / "tur.traineddata").is_file()


def fake_build(folder: Path) -> Path:
    folder.mkdir(parents=True)
    for name in ("evrakci", "evrakci-arayuz"):
        program = folder / name
        program.write_text("#!/bin/sh\necho " + name + " \"$@\"\n")
        program.chmod(0o755)
    (folder / "lib").mkdir()
    (folder / "lib" / "x.so").write_bytes(b"\0")
    return folder


def test_tarball_layout(tmp_path):
    import linux_package

    tarball = linux_package.package(fake_build(tmp_path / "build"), tmp_path / "dist", "1.2.3")
    assert tarball.name == "evrakci-1.2.3-linux-x86_64.tar.gz"
    with tarfile.open(tarball) as archive:
        members = {m.name: m for m in archive.getmembers()}
    top = "evrakci-1.2.3"
    assert {name.split("/")[0] for name in members} == {top}
    for script in ("kur.sh", "kaldir.sh", "uygulama/evrakci", "uygulama/evrakci-arayuz"):
        assert members[f"{top}/{script}"].mode & stat.S_IXUSR, script
    assert f"{top}/BENIOKU.txt" in members
    assert f"{top}/uygulama/lib/x.so" in members


def test_tarball_refuses_build_without_programs(tmp_path):
    import linux_package

    (tmp_path / "build").mkdir()
    with pytest.raises(SystemExit):
        linux_package.package(tmp_path / "build", tmp_path / "dist", "1.0")


def unpacked(tmp_path: Path) -> Path:
    import linux_package

    tarball = linux_package.package(fake_build(tmp_path / "build"), tmp_path / "dist", "1.0")
    where = tmp_path / "İndirilenler Şükrü"
    where.mkdir()
    with tarfile.open(tarball) as archive:
        archive.extractall(where, filter="tar")
    return where / "evrakci-1.0"


def run_script(script: Path, home: Path, path: str | None = None):
    env = {"HOME": str(home), "PATH": path or os.environ["PATH"], "LANG": "C.UTF-8"}
    return subprocess.run(["sh", str(script)], capture_output=True, text=True, env=env,
                          cwd=home)


@posix_only
def test_install_and_remove(tmp_path):
    folder = unpacked(tmp_path)
    home = tmp_path / "ev"
    home.mkdir()
    result = run_script(folder / "kur.sh", home)
    assert result.returncode == 0, result.stderr
    app = home / ".local/share/evrakci-uygulama"
    assert (app / "evrakci-arayuz").is_file()
    link = home / ".local/bin/evrakci"
    out = subprocess.run([str(link), "--version"], capture_output=True, text=True).stdout
    assert out.strip() == "evrakci --version"
    desktop = (home / ".local/share/applications/evrakci.desktop").read_text()
    assert f'Exec="{app}/evrakci-arayuz"' in desktop and "Name=Evrakçı" in desktop

    # Installing again replaces the old copy; jobs and templates are not touched.
    (app / "eski-dosya").write_text("x")
    data = home / ".local/share/Evrakci/isler"
    data.mkdir(parents=True)
    assert run_script(folder / "kur.sh", home).returncode == 0
    assert not (app / "eski-dosya").exists()

    result = run_script(app / "kaldir.sh", home)
    assert result.returncode == 0, result.stderr
    assert not app.exists() and not link.is_symlink()
    assert not (home / ".local/share/applications/evrakci.desktop").exists()
    assert data.is_dir()


@posix_only
def test_install_warns_without_tesseract(tmp_path):
    folder = unpacked(tmp_path)
    home = tmp_path / "ev"
    home.mkdir()
    bare = tmp_path / "bos-path"
    bare.mkdir()
    for tool in ("sh", "cp", "rm", "mkdir", "ln", "cat", "dirname", "chmod", "mv"):
        found = shutil.which(tool)
        if found:
            (bare / tool).symlink_to(found)
    result = run_script(folder / "kur.sh", home, path=str(bare))
    assert result.returncode == 0, result.stderr
    assert "sudo apt install tesseract-ocr" in result.stdout


@posix_only
def test_install_refuses_unsafe_home(tmp_path):
    folder = unpacked(tmp_path)
    result = run_script(folder / "kur.sh", Path("/"))
    assert result.returncode != 0


def test_gpl_libraries_are_found_in_a_build(tmp_path):
    import build

    (tmp_path / "lib" / "sub").mkdir(parents=True)
    for name in ("libreadline-2c5f7b8d.so.6.2", "libssl-821e5a28.so.3", "readline.cpython.so"):
        (tmp_path / "lib" / name).write_bytes(b"\0")
    (tmp_path / "lib" / "sub" / "libreadline.so.8").write_bytes(b"\0")
    found = build.forbidden_libraries(tmp_path)
    assert sorted(p.name for p in found) == ["libreadline-2c5f7b8d.so.6.2", "libreadline.so.8"]


def test_freeze_leaves_out_readline():
    setup = (ROOT / "packaging" / "freeze_setup.py").read_text(encoding="utf-8")
    assert '"readline"' in setup
