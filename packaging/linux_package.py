"""Pack the Linux folder build into evrakci-<sürüm>-linux-x86_64.tar.gz.

    python packaging/linux_package.py [--build build/evrakci] [--cikti dist] [--surum X]

The tarball has one top folder with kur.sh, kaldir.sh, BENIOKU.txt and the build in uygulama/.
"""

from __future__ import annotations

import argparse
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = HERE / "linux"
PROGRAMS = ("evrakci", "evrakci-arayuz")


def package(build_dir: Path, out_dir: Path, version: str) -> Path:
    build_dir, out_dir = Path(build_dir), Path(out_dir)
    missing = [name for name in PROGRAMS if not (build_dir / name).is_file()]
    if missing:
        print(f"Derleme eksik ({', '.join(missing)}): {build_dir}", file=sys.stderr)
        raise SystemExit(1)
    top = f"evrakci-{version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    tarball = out_dir / f"{top}-linux-x86_64.tar.gz"
    partial = tarball.with_name(tarball.name + ".gecici")

    def executable(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        if info.isfile() and info.name.rsplit("/", 1)[-1] in (*PROGRAMS, "kur.sh", "kaldir.sh"):
            info.mode |= 0o755
        return info

    with tarfile.open(partial, "w:gz") as archive:
        for name in ("kur.sh", "kaldir.sh", "BENIOKU.txt"):
            archive.add(SCRIPTS / name, arcname=f"{top}/{name}", filter=executable)
        archive.add(build_dir, arcname=f"{top}/uygulama", filter=executable)
    partial.replace(tarball)
    return tarball


def main() -> int:
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
