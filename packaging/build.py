"""Build the Windows or Linux folder build of Evrakçı with cx_Freeze.

    python packaging/build.py [--tesseract DIR] [--tur-best FILE] [--tessdata-configs DIR]
                              [--kontrol]

--tesseract         a Tesseract install folder to bundle as tesseract/ (Windows)
--tur-best          tur.traineddata to bundle as tessdata_best/ (checked against the pinned SHA-256)
--tessdata-configs  a tessdata folder whose configs/ and tessconfigs/ go into tessdata_best/
                    (Linux, where Tesseract comes from the system and is not bundled)
--kontrol           only check the inputs, do not build
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from evrakci.pipeline.ocr.tesseract import TESSDATA_VARIANTS  # noqa: E402

STAGE = HERE / "stage"
# Top-level packages in the build; their dependencies are followed automatically.
BUNDLED = [
    "evrakci",
    "ocrmypdf",
    "pikepdf",
    "pypdfium2",
    "zxing-cpp",
    "segno",
    "openpyxl",
    "platformdirs",
    "PySide6",
]  # cx_Freeze is a build tool; only its small runtime stubs ship (see NOTICE.txt)


# GNU Readline is GPL-3.0; only permissive libraries may ship (docs/dependency-licenses.md).
GPL_LIBRARIES = ("libreadline",)


def forbidden_libraries(build_dir: Path) -> list[Path]:
    """Shared libraries in a build that must not ship."""
    return sorted(p for p in Path(build_dir).rglob("*")
                  if p.is_file() and p.name.startswith(GPL_LIBRARIES))


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def stage_inputs(
    tesseract: Path | None,
    tur_best: Path | None,
    check_only: bool,
    configs: Path | None = None,
    stage: Path = STAGE,
) -> None:
    if tur_best is not None:
        digest = hashlib.sha256(tur_best.read_bytes()).hexdigest()
        if digest != TESSDATA_VARIANTS["best"].sha256:
            fail(f"tur_best doğrulanamadı: {tur_best} (SHA-256 {digest})")
    if tesseract is not None and not any(
        (tesseract / name).is_file() for name in ("tesseract.exe", "tesseract")
    ):
        fail(f"Tesseract bulunamadı: {tesseract}")
    if configs is not None and not (configs / "configs" / "hocr").is_file():
        fail(f"Tesseract ayar dosyaları bulunamadı (configs/hocr): {configs}")
    if check_only:
        return
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    shutil.copytree(HERE / "licenses", stage / "licenses")
    from collect_licenses import collect

    collect(stage / "licenses", BUNDLED)
    if tesseract is not None:
        shutil.copytree(tesseract, stage / "tesseract")
    if tur_best is not None:
        best = stage / "tessdata_best"
        best.mkdir()
        shutil.copy2(tur_best, best / "tur.traineddata")
        # The install folder is read-only, so Tesseract's output configs ship pre-copied.
        source = configs or ((tesseract / "tessdata") if tesseract else None)
        for name in ("configs", "tessconfigs"):
            if source is not None and (source / name).is_dir():
                shutil.copytree(source / name, best / name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tesseract", type=Path)
    parser.add_argument("--tur-best", type=Path)
    parser.add_argument("--tessdata-configs", type=Path)
    parser.add_argument("--kontrol", action="store_true")
    args = parser.parse_args()
    stage_inputs(args.tesseract, args.tur_best, args.kontrol, configs=args.tessdata_configs)
    if args.kontrol:
        print("Girdiler doğru.")
        return 0
    subprocess.run(
        [
            sys.executable,
            str(HERE / "freeze_setup.py"),
            "build_exe",
            "--build-exe",
            str(ROOT / "build" / "evrakci"),
        ],
        check=True,
        cwd=ROOT,
    )
    found = forbidden_libraries(ROOT / "build" / "evrakci")
    if found:
        fail("Derlemede GPL kütüphanesi var: " + ", ".join(str(p) for p in found))
    print(f"Hazır: {ROOT / 'build' / 'evrakci'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
