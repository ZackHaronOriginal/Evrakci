"""Linux build: tessdata configs in the bundle, the GPL check, the tarball, kur.sh / kaldir.sh."""

import ast
import dataclasses
import hashlib
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


# --- build.py: configs for tessdata_best -------------------------------------------------

def fake_configs(folder: Path) -> Path:
    (folder / "configs").mkdir(parents=True)
    (folder / "configs" / "hocr").write_text("tessedit_create_hocr 1\n")
    (folder / "tessconfigs").mkdir()
    (folder / "tessconfigs" / "nobatch").write_text("\n")
    return folder


def run_build(*args):
    return subprocess.run([sys.executable, str(BUILD), *args, "--kontrol"],
                          capture_output=True, text=True)


def fake_tur_best(tmp_path: Path, monkeypatch) -> Path:
    import build

    data = tmp_path / "tur.traineddata"
    data.write_bytes(b"sahte veri")
    best = dataclasses.replace(build.TESSDATA_VARIANTS["best"],
                               sha256=hashlib.sha256(b"sahte veri").hexdigest())
    monkeypatch.setitem(build.TESSDATA_VARIANTS, "best", best)
    return data


def test_build_refuses_configs_folder_without_hocr(tmp_path, monkeypatch):
    import build

    data = fake_tur_best(tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        build.stage_inputs(None, data, True, configs=tmp_path / "bos")


def test_build_refuses_configs_without_tur_best(tmp_path):
    result = run_build("--tessdata-configs", str(fake_configs(tmp_path / "td")))
    assert result.returncode != 0 and "--tur-best" in result.stderr


def test_staging_copies_configs_into_tur_best(tmp_path, monkeypatch):
    import build

    data = fake_tur_best(tmp_path, monkeypatch)
    stage = tmp_path / "stage"
    build.stage_inputs(None, data, False, configs=fake_configs(tmp_path / "td"), stage=stage)
    assert (stage / "tessdata_best" / "configs" / "hocr").is_file()
    assert (stage / "tessdata_best" / "tessconfigs" / "nobatch").is_file()
    assert (stage / "tessdata_best" / "tur.traineddata").read_bytes() == b"sahte veri"


def test_linux_licence_texts_ship_only_on_linux(tmp_path, monkeypatch):
    import build

    stage = tmp_path / "stage"
    monkeypatch.setattr(build.sys, "platform", "linux")
    build.stage_inputs(None, None, False, stage=stage)
    for name in ("ICU.txt", "libffi.txt", "bzip2.txt", "mpdecimal.txt", "libuuid.txt", "xz.txt"):
        assert (stage / "licenses" / "linux" / name).is_file(), name
    monkeypatch.setattr(build.sys, "platform", "win32")
    build.stage_inputs(None, None, False, stage=stage)
    assert not (stage / "licenses" / "linux").exists()


# --- GPL parts that must not ship ----------------------------------------------------------

def touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\0")
    return path


def test_gpl_libraries_are_found_in_a_build(tmp_path):
    import gpl_check

    lib = tmp_path / "lib"
    bad = [
        touch(lib / "libreadline-2c5f7b8d.so.6.2"),
        touch(lib / "sub" / "libreadline.so.8"),
        touch(lib / "libgdbm-1a2b.so.4"),
        touch(lib / "PySide6/Qt/lib/libQt6VirtualKeyboard.so.6"),
        touch(lib / "PySide6/Qt/lib/libQt6VirtualKeyboardQml.so.6"),
        touch(lib / "PySide6/Qt/lib/libQt6WaylandCompositor.so.6"),
        touch(lib / "PySide6/Qt/lib/libQt6WaylandEglCompositorHwIntegration.so.6"),
        touch(lib / "PySide6/Qt/plugins/platforminputcontexts/libqtvirtualkeyboardplugin.so"),
        touch(lib / "PySide6/Qt/plugins/wayland-graphics-integration-server/libqt-wayland.so"),
        touch(lib / "PySide6/Qt6VirtualKeyboard.dll"),  # Windows
    ]
    good = [touch(lib / "libssl-821e5a28.so.3"), touch(lib / "readline.txt"),
            touch(lib / "PySide6/Qt/lib/libQt6WaylandClient.so.6")]
    found = gpl_check.forbidden_libraries(tmp_path)
    assert sorted(found) == sorted(bad)
    assert not set(good) & set(found)


def test_gpl_qt_parts_are_removed_and_the_rest_kept(tmp_path):
    import gpl_check

    keyboard = touch(tmp_path / "lib/PySide6/Qt/lib/libQt6VirtualKeyboard.so.6")
    server = touch(tmp_path / "lib/PySide6/Qt/plugins/wayland-graphics-integration-server/a.so")
    readline = touch(tmp_path / "lib/libreadline.so.8")
    client = touch(tmp_path / "lib/PySide6/Qt/lib/libQt6WaylandClient.so.6")
    removed = gpl_check.remove_gpl_qt(tmp_path)
    assert keyboard in removed and not keyboard.exists()
    assert not server.parent.exists()
    assert readline.exists() and client.exists()  # readline is excluded at freeze time instead
    assert gpl_check.forbidden_libraries(tmp_path) == [readline]


def freeze_excludes() -> set[str]:
    tree = ast.parse((ROOT / "packaging" / "freeze_setup.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value == "excludes":
                    return {e.value for e in value.elts if isinstance(e, ast.Constant)}
    raise AssertionError("excludes not found")


def test_freeze_leaves_out_gpl_and_unused_modules():
    assert {"readline", "curses", "_curses", "dbm.gnu", "_gdbm"} <= freeze_excludes()


# --- the tarball -------------------------------------------------------------------------------

def fake_build(folder: Path) -> Path:
    folder.mkdir(parents=True)
    for name in ("evrakci", "evrakci-arayuz"):
        program = folder / name
        program.write_text("#!/bin/sh\necho " + name + " \"$@\"\n")
        program.chmod(0o755)
    (folder / "lib").mkdir()
    (folder / "lib" / "x.so").write_bytes(b"\0")
    (folder / "lib" / "veri.txt").write_text("x")
    (folder / "lib" / "bag").symlink_to("x.so")
    return folder


def members_of(tarball: Path) -> dict[str, tarfile.TarInfo]:
    with tarfile.open(tarball) as archive:
        return {m.name: m for m in archive.getmembers()}


def test_tarball_layout(tmp_path, monkeypatch):
    import linux_package

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")
    tarball = linux_package.package(fake_build(tmp_path / "build"), tmp_path / "dist", "1.2.3")
    assert tarball.name == "evrakci-1.2.3-linux-x86_64.tar.gz"
    members = members_of(tarball)
    top = "evrakci-1.2.3"
    assert {name.split("/")[0] for name in members} == {top}
    assert members[top].isdir()
    for script in ("kur.sh", "kaldir.sh", "uygulama/evrakci", "uygulama/evrakci-arayuz"):
        assert members[f"{top}/{script}"].mode & stat.S_IXUSR, script
    for plain in ("BENIOKU.txt", "evrakci.svg", "uygulama/lib/veri.txt"):
        assert not members[f"{top}/{plain}"].mode & stat.S_IXUSR, plain
    assert members[f"{top}/uygulama/lib/bag"].issym()
    assert members[f"{top}/uygulama/lib/bag"].linkname == "x.so"
    assert all(m.uid == 0 and m.gid == 0 and m.uname == "" for m in members.values())
    assert all(m.mtime == 1767225600 for m in members.values())


def test_tarball_is_reproducible_and_has_a_checksum(tmp_path, monkeypatch):
    import linux_package

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1767225600")
    build = fake_build(tmp_path / "build")
    first = linux_package.package(build, tmp_path / "a", "1.0").read_bytes()
    tarball = linux_package.package(build, tmp_path / "b", "1.0")
    assert tarball.read_bytes() == first
    checksum = tarball.with_name(tarball.name + ".sha256").read_text()
    assert checksum == f"{hashlib.sha256(first).hexdigest()}  {tarball.name}\n"


def test_tarball_refuses_build_without_programs(tmp_path):
    import linux_package

    (tmp_path / "build").mkdir()
    with pytest.raises(SystemExit):
        linux_package.package(tmp_path / "build", tmp_path / "dist", "1.0")


def test_tarball_refuses_build_with_gpl_library(tmp_path):
    import linux_package

    build = fake_build(tmp_path / "build")
    touch(build / "lib" / "libreadline.so.8")
    with pytest.raises(SystemExit):
        linux_package.package(build, tmp_path / "dist", "1.0")
    assert not list((tmp_path / "dist").glob("*.tar.gz"))


# --- kur.sh / kaldir.sh ------------------------------------------------------------------------

def unpacked(tmp_path: Path) -> Path:
    import linux_package

    tarball = linux_package.package(fake_build(tmp_path / "build"), tmp_path / "dist", "1.0")
    where = tmp_path / "İndirilenler Şükrü"
    where.mkdir()
    with tarfile.open(tarball) as archive:
        archive.extractall(where, filter="tar")
    return where / "evrakci-1.0"


def run_script(script: Path, home: Path, path: str | None = None, root_ok: bool = True,
               cwd: Path | None = None, **extra):
    env = {"HOME": str(home), "PATH": path or os.environ["PATH"], "LANG": "C.UTF-8", **extra}
    if root_ok:  # the tests may run as root (containers); kur.sh refuses root otherwise
        env["EVRAKCI_ROOT_KURULUMU"] = "1"
    return subprocess.run(["sh", str(script)], capture_output=True, text=True, env=env,
                          cwd=cwd or home)


@pytest.fixture
def home(tmp_path):
    folder = tmp_path / "ev"
    folder.mkdir()
    return folder


@posix_only
def test_install_and_remove(tmp_path, home):
    folder = unpacked(tmp_path)
    result = run_script(folder / "kur.sh", home)
    assert result.returncode == 0, result.stderr
    app = home / ".local/share/evrakci-uygulama"
    assert (app / "evrakci-arayuz").is_file()
    assert f"Kaldırmak için: {app}/kaldir.sh" in result.stdout
    link = home / ".local/bin/evrakci"
    out = subprocess.run([str(link), "--version"], capture_output=True, text=True).stdout
    assert out.strip() == "evrakci --version"
    menu = home / ".local/share/applications/evrakci-arayuz.desktop"
    desktop = menu.read_text()
    assert f'Exec="{app}/evrakci-arayuz"' in desktop and "Name=Evrakçı" in desktop
    assert "Icon=evrakci" in desktop and "StartupWMClass=evrakci-arayuz" in desktop
    icon = home / ".local/share/icons/hicolor/scalable/apps/evrakci.svg"
    assert icon.is_file()

    # Installing again replaces the old copy; jobs and templates are not touched.
    (app / "eski-dosya").write_text("x")
    data = home / ".local/share/Evrakci/isler"
    data.mkdir(parents=True)
    assert run_script(folder / "kur.sh", home).returncode == 0
    assert not (app / "eski-dosya").exists()

    result = run_script(app / "kaldir.sh", home)
    assert result.returncode == 0, result.stderr
    assert "Evrakçı kaldırıldı" in result.stdout
    assert not app.exists() and not link.is_symlink()
    assert not (home / ".local/bin/evrakci-arayuz").is_symlink()
    assert not menu.exists() and not icon.exists()
    assert data.is_dir()


@posix_only
def test_install_into_xdg_data_home_and_remove_from_any_environment(tmp_path, home):
    folder = unpacked(tmp_path)
    data_home = tmp_path / "veri yeri"
    result = run_script(folder / "kur.sh", home, XDG_DATA_HOME=str(data_home))
    assert result.returncode == 0, result.stderr
    app = data_home / "evrakci-uygulama"
    assert (app / "evrakci").is_file()
    assert (data_home / "applications/evrakci-arayuz.desktop").is_file()
    # kaldir.sh removes what kur.sh installed, whatever XDG_DATA_HOME is now.
    result = run_script(app / "kaldir.sh", home, XDG_DATA_HOME="/baska/yer")
    assert result.returncode == 0, result.stderr
    assert not app.exists()
    assert not (data_home / "applications/evrakci-arayuz.desktop").exists()
    assert not (home / ".local/bin/evrakci").is_symlink()


@posix_only
def test_relative_xdg_data_home_is_ignored(tmp_path, home):
    folder = unpacked(tmp_path)
    result = run_script(folder / "kur.sh", home, XDG_DATA_HOME="goreli")
    assert result.returncode == 0, result.stderr
    assert (home / ".local/share/evrakci-uygulama/evrakci").is_file()
    assert not (home / "goreli").exists()


@posix_only
def test_other_programs_links_and_files_are_kept(tmp_path, home):
    folder = unpacked(tmp_path)
    bin_dir = home / ".local/bin"
    bin_dir.mkdir(parents=True)
    other = tmp_path / "pipx" / "evrakci"
    touch(other)
    (bin_dir / "evrakci").symlink_to(other)
    (bin_dir / "evrakci-arayuz").write_text("baska program")
    result = run_script(folder / "kur.sh", home)
    assert result.returncode == 0, result.stderr
    assert os.readlink(bin_dir / "evrakci") == str(other)
    assert (bin_dir / "evrakci-arayuz").read_text() == "baska program"
    assert result.stdout.count("başka bir programa ait") == 2
    app = home / ".local/share/evrakci-uygulama"
    assert run_script(app / "kaldir.sh", home).returncode == 0
    assert os.readlink(bin_dir / "evrakci") == str(other)
    assert (bin_dir / "evrakci-arayuz").read_text() == "baska program"


@posix_only
def test_dangling_link_is_replaced(tmp_path, home):
    folder = unpacked(tmp_path)
    bin_dir = home / ".local/bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "evrakci").symlink_to(tmp_path / "yok")
    assert run_script(folder / "kur.sh", home).returncode == 0
    assert os.readlink(bin_dir / "evrakci") == str(home / ".local/share/evrakci-uygulama/evrakci")


@posix_only
def test_leftovers_of_an_interrupted_install_are_cleaned(tmp_path, home):
    folder = unpacked(tmp_path)
    stale = home / ".local/share/evrakci-uygulama.yeni.12345"
    touch(stale / "yarim")
    old = home / ".local/share/evrakci-uygulama.eski.999"
    touch(old / "eski")
    assert run_script(folder / "kur.sh", home).returncode == 0
    assert not stale.exists() and not old.exists()


@posix_only
def test_menu_entry_skipped_for_a_path_it_cannot_hold(tmp_path):
    folder = unpacked(tmp_path)
    home = tmp_path / "ev$x%y"
    home.mkdir()
    result = run_script(folder / "kur.sh", home)
    assert result.returncode == 0, result.stderr
    assert "menü kaydı eklenmedi" in result.stdout
    assert not (home / ".local/share/applications/evrakci-arayuz.desktop").exists()
    assert (home / ".local/bin/evrakci").is_symlink()


@posix_only
def test_install_with_cdpath_and_a_relative_script_path(tmp_path, home):
    folder = unpacked(tmp_path)
    result = subprocess.run(
        ["sh", "evrakci-1.0/kur.sh"], capture_output=True, text=True, cwd=folder.parent,
        env={"HOME": str(home), "PATH": os.environ["PATH"], "CDPATH": str(folder.parent),
             "EVRAKCI_ROOT_KURULUMU": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert (home / ".local/share/evrakci-uygulama/evrakci").is_file()


@posix_only
def test_install_warns_without_tesseract(tmp_path, home):
    folder = unpacked(tmp_path)
    bare = tmp_path / "bos-path"
    bare.mkdir()
    for tool in ("sh", "cp", "rm", "mkdir", "ln", "cat", "dirname", "chmod", "mv", "id",
                 "readlink"):
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


@posix_only
@pytest.mark.skipif(os.name != "nt" and os.geteuid() != 0, reason="needs root to test")
def test_install_refuses_root(tmp_path, home):
    folder = unpacked(tmp_path)
    result = run_script(folder / "kur.sh", home, root_ok=False)
    assert result.returncode != 0 and "root" in result.stderr
    assert not (home / ".local").exists()


@posix_only
def test_remove_refuses_a_folder_that_is_not_an_install(tmp_path, home):
    folder = unpacked(tmp_path)  # kaldir.sh in the unpacked download, not an install
    result = run_script(folder / "kaldir.sh", home)
    assert result.returncode != 0 and "kurulum" in result.stderr
    assert folder.is_dir()


def test_window_names_its_desktop_file(qapp):
    from evrakci import app

    app.configure_application(qapp)
    assert qapp.desktopFileName() == "evrakci-arayuz"
    assert qapp.applicationName() == "Evrakçı"
