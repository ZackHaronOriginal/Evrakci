"""Build the Windows (or local) folder build of Evrakçı with cx_Freeze.

    python packaging/build.py [--tesseract DIR] [--tur-best FILE] [--kontrol]

--tesseract   a Tesseract install folder to bundle as tesseract/
--tur-best    tur.traineddata to bundle as tessdata_best/ (checked against the pinned SHA-256)
--kontrol     only check the inputs, do not build
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
    "cx_Freeze",
]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def stage_inputs(tesseract: Path | None, tur_best: Path | None, check_only: bool) -> None:
    if tur_best is not None:
        digest = hashlib.sha256(tur_best.read_bytes()).hexdigest()
        if digest != TESSDATA_VARIANTS["best"].sha256:
            fail(f"tur_best doğrulanamadı: {tur_best} (SHA-256 {digest})")
    if tesseract is not None and not any(
        (tesseract / name).is_file() for name in ("tesseract.exe", "tesseract")
    ):
        fail(f"Tesseract bulunamadı: {tesseract}")
    if check_only:
        return
    shutil.rmtree(STAGE, ignore_errors=True)
    STAGE.mkdir()
    shutil.copytree(HERE / "licenses", STAGE / "licenses")
    from collect_licenses import collect

    collect(STAGE / "licenses", BUNDLED)
    if tesseract is not None:
        shutil.copytree(tesseract, STAGE / "tesseract")
    if tur_best is not None:
        best = STAGE / "tessdata_best"
        best.mkdir()
        shutil.copy2(tur_best, best / "tur.traineddata")
        # The install folder is read-only, so Tesseract's output configs ship pre-copied.
        source = (tesseract / "tessdata") if tesseract else None
        for name in ("configs", "tessconfigs"):
            if source is not None and (source / name).is_dir():
                shutil.copytree(source / name, best / name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tesseract", type=Path)
    parser.add_argument("--tur-best", type=Path)
    parser.add_argument("--kontrol", action="store_true")
    args = parser.parse_args()
    stage_inputs(args.tesseract, args.tur_best, args.kontrol)
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
    print(f"Hazır: {ROOT / 'build' / 'evrakci'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
