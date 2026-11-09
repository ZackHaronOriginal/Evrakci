"""Stage the Tesseract that vcpkg built for Windows: the program, its configs, every licence.

    python packaging/stage_tesseract.py --vcpkg INSTALLED_TRIPLET_DIR TARGET_DIR

Tesseract is built from source by vcpkg (pinned in packaging/vcpkg/vcpkg.json; vcpkg checks
every source download against its SHA-512) as one static tesseract.exe, without curl,
libarchive or JBIG-KIT. Every library that went into it must be on ALLOWED_PORTS with a
permissive licence, and its licence text is copied next to it.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# vcpkg port -> licence (SPDX). Anything else in the build stops it.
ALLOWED_PORTS = {
    "tesseract": "Apache-2.0",
    "leptonica": "BSD-2-Clause",
    "cpu-features": "Apache-2.0",
    "giflib": "MIT",
    "libjpeg-turbo": "IJG AND BSD-3-Clause AND Zlib",
    "libpng": "libpng-2.0",
    "libwebp": "BSD-3-Clause",
    "openjpeg": "BSD-2-Clause",
    "tiff": "libtiff",
    "liblzma": "0BSD",
    "zlib": "Zlib",
}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def installed_ports(installed: Path) -> list[str]:
    """Ports vcpkg installed for this triplet (build-machine helpers have another triplet)."""
    triplet = installed.name
    info = installed.parent / "vcpkg" / "info"
    ports = set()
    for record in info.glob("*.list"):
        name, _, rest = record.stem.partition("_")
        if rest.endswith(f"_{triplet}"):
            ports.add(name)
    if not ports:
        fail(f"vcpkg kurulum kaydı bulunamadı: {info}")
    return sorted(ports)


def stage_vcpkg(installed: Path, target: Path) -> list[str]:
    installed, target = Path(installed), Path(target)
    ports = installed_ports(installed)
    unknown = [p for p in ports if p not in ALLOWED_PORTS]
    if unknown:
        fail(f"İzin listesinde olmayan kütüphane: {', '.join(unknown)} (lisansını kontrol edin)")
    missing = [p for p in ports if not (installed / "share" / p / "copyright").is_file()]
    if missing:
        fail(f"Lisans metni yok: {', '.join(missing)}")
    tools = installed / "tools" / "tesseract"
    if not (tools / "tesseract.exe").is_file():
        fail(f"tesseract.exe bulunamadı: {tools}")
    extra = sorted(p.name for p in tools.glob("*.dll"))
    if extra:  # the static build must not need any DLL of its own
        fail(f"Beklenmeyen DLL: {', '.join(extra)}")
    configs = installed / "share" / "tessdata"
    if not (configs / "configs" / "hocr").is_file():
        fail(f"Tesseract ayar dosyaları bulunamadı: {configs}")
    shutil.rmtree(target, ignore_errors=True)
    (target / "tessdata").mkdir(parents=True)
    shutil.copy2(tools / "tesseract.exe", target / "tesseract.exe")
    for name in ("configs", "tessconfigs"):
        if (configs / name).is_dir():
            shutil.copytree(configs / name, target / "tessdata" / name)
    (target / "licenses").mkdir()
    for port in ports:
        shutil.copy2(installed / "share" / port / "copyright", target / "licenses" / f"{port}.txt")
    return ports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vcpkg", type=Path, required=True, help="vcpkg_installed/<triplet>")
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    ports = stage_vcpkg(args.vcpkg, args.target)
    print("tesseract.exe + " + ", ".join(f"{p} ({ALLOWED_PORTS[p]})" for p in ports))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
