"""Pack the Linux folder build into evrakci-<sürüm>-linux-x86_64.tar.gz (+ .sha256).

    python packaging/linux_package.py [--build build/evrakci] [--cikti dist] [--surum X]

The tarball has one top folder with kur.sh, kaldir.sh, BENIOKU.txt, the menu icon and the build
in uygulama/. With SOURCE_DATE_EPOCH set, every file gets that time, so the same build always
gives the same tarball.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = HERE / "linux"
PROGRAMS = ("evrakci", "evrakci-arayuz")
EXECUTABLE = (*PROGRAMS, "kur.sh", "kaldir.sh")
sys.path.insert(0, str(HERE))

from gpl_check import forbidden_libraries  # noqa: E402


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def package(build_dir: Path, out_dir: Path, version: str) -> Path:
    build_dir, out_dir = Path(build_dir), Path(out_dir)
    missing = [name for name in PROGRAMS if not (build_dir / name).is_file()]
    if missing:
        fail(f"Derleme eksik ({', '.join(missing)}): {build_dir}")
    gpl = forbidden_libraries(build_dir)
    if gpl:
        fail("Derlemede GPL bileşeni var: " + ", ".join(str(p) for p in gpl))
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    mtime = int(epoch) if epoch else None
    top = f"evrakci-{version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    tarball = out_dir / f"{top}-linux-x86_64.tar.gz"
    partial = tarball.with_name(tarball.name + ".gecici")

    def normalise(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        if mtime is not None:
            info.mtime = mtime
        if info.isfile():
            executable = info.name.rsplit("/", 1)[-1] in EXECUTABLE or info.mode & 0o100
            info.mode = 0o755 if executable else 0o644
        elif info.isdir():
            info.mode = 0o755
        return info

    try:
        with open(partial, "wb") as raw, \
                gzip.GzipFile(fileobj=raw, mode="wb", mtime=mtime or 0, filename="") as packed, \
                tarfile.open(fileobj=packed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            top_info = tarfile.TarInfo(top)
            top_info.type = tarfile.DIRTYPE
            top_info.mtime = mtime if mtime is not None else int(build_dir.stat().st_mtime)
            archive.addfile(normalise(top_info))
            for name in ("kur.sh", "kaldir.sh", "BENIOKU.txt", "evrakci.svg"):
                archive.add(SCRIPTS / name, arcname=f"{top}/{name}", filter=normalise)
            archive.add(build_dir, arcname=f"{top}/uygulama", filter=normalise)
        partial.replace(tarball)
    finally:
        partial.unlink(missing_ok=True)
    digest = hashlib.sha256(tarball.read_bytes()).hexdigest()
    tarball.with_name(tarball.name + ".sha256").write_text(f"{digest}  {tarball.name}\n")
    return tarball


def main() -> int:
    import argparse

    sys.path.insert(0, str(ROOT / "src"))
    from evrakci import __version__

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / "build" / "evrakci")
    parser.add_argument("--cikti", type=Path, default=ROOT / "dist")
    parser.add_argument("--surum", default=__version__.split("+")[0])
    args = parser.parse_args()
    print(f"Hazır: {package(args.build, args.cikti, args.surum)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
