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

from collect_licenses import collect_from_build, undocumented  # noqa: E402
from gpl_check import forbidden_libraries, remove_gpl_qt  # noqa: E402
from layout import copy_python_licence, place_after_freeze, remove_unused_qt  # noqa: E402

from evrakci.pipeline.ocr.tesseract import TESSDATA_VARIANTS  # noqa: E402

STAGE = HERE / "stage"
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
    if configs is not None and tur_best is None:
        fail("--tessdata-configs yalnızca --tur-best ile birlikte kullanılır")
    if configs is not None and not (configs / "configs" / "hocr").is_file():
        fail(f"Tesseract ayar dosyaları bulunamadı (configs/hocr): {configs}")
    if check_only:
        return
    shutil.rmtree(stage, ignore_errors=True)
    stage.mkdir(parents=True)
    # Licence texts of the Python runtime's own libraries ship only in the Linux build.
    ignore = None if sys.platform.startswith("linux") else shutil.ignore_patterns("linux")
    shutil.copytree(HERE / "licenses", stage / "licenses", ignore=ignore)
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
        # Tesseract 4 (Ubuntu 22.04) lists no language unless eng sits beside tur.
        if source is not None and (source / "eng.traineddata").is_file():
            shutil.copy2(source / "eng.traineddata", best / "eng.traineddata")


def finish(build: Path, stage: Path = STAGE) -> None:
    """After cx_Freeze: add Tesseract, take out what must not ship, add every licence."""
    place_after_freeze(stage, build)
    for path in remove_gpl_qt(build):
        print(f"GPL bileşeni çıkarıldı: {path.name}")
    for path in remove_unused_qt(build):
        print(f"Kullanılmayan Qt parçası çıkarıldı: {path.name}")
    found = forbidden_libraries(build)
    if found:
        fail("Derlemede GPL kütüphanesi var: " + ", ".join(str(p) for p in found))
    shipped = collect_from_build(build / "lib", build / "licenses")
    (HERE / "shipped-packages.txt").write_text(
        "\n".join(sorted(shipped, key=str.lower)) + "\n", encoding="utf-8")
    missing = undocumented(shipped, (ROOT / "docs" / "dependency-licenses.md").read_text(
        encoding="utf-8"))
    if missing:
        fail("docs/dependency-licenses.md içinde olmayan paket: " + ", ".join(missing))
    if copy_python_licence(build / "licenses") is None:
        fail("Python'un lisans dosyası (LICENSE.txt) bulunamadı")


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
    finish(ROOT / "build" / "evrakci")
    print(f"Hazır: {ROOT / 'build' / 'evrakci'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
