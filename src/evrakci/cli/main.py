"""Argument parsing and error handling for `evrakci`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from evrakci import __version__
from evrakci.cli import jobs, ocr, templates
from evrakci.cli.errors import UserError
from evrakci.pipeline.analyze import BatchError
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.separator import make_separator_pdf
from evrakci.pipeline.settings import (
    Settings,
    SettingsError,
    load_settings,
    save_settings,
    settings_path,
)
from evrakci.pipeline.store import JobFileError, JobStore, default_root
from evrakci.pipeline.templates.model import TemplateError


def _separator(args: argparse.Namespace, store: JobStore) -> int:
    if args.adet < 1:
        raise UserError("Adet en az 1 olmalı.")
    path = make_separator_pdf(args.cikti, sheets=args.adet)
    print(f"Ayıraç dosyası yazıldı: {path} ({args.adet} yaprak)")
    return 0


def _show_settings(args: argparse.Namespace, store: JobStore) -> int:
    settings = load_settings()
    print(f"Saklama: {settings.retention}")
    print(f"Ayar dosyası: {settings_path()}")
    return 0


def _set_retention(args: argparse.Namespace, store: JobStore) -> int:
    try:
        settings = Settings(args.deger)
    except SettingsError as error:
        raise UserError(str(error)) from None
    save_settings(settings)
    meaning = {
        "sakla": "işler hiçbir zaman kendiliğinden silinmez",
        "disa-aktarinca-sil": "iş, tüm dosyalar dışa aktarılınca silinir",
    }.get(settings.retention, f"{settings.retention} günden eski işler silinir")
    print(f"Saklama: {settings.retention} ({meaning})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evrakci",
        description="Evrakçı komut satırı: taranmış evrakı ayırır, adlandırır ve dışa aktarır.",
    )
    parser.add_argument("--version", action="version", version=f"evrakci {__version__}")
    parser.add_argument(
        "--kok",
        type=Path,
        default=None,
        help="işlerin saklandığı klasör (varsayılan: uygulama veri klasörü)",
    )
    parser.add_argument(
        "--sablon-kok",
        type=Path,
        default=None,
        help="şablonların saklandığı klasör (varsayılan: uygulama veri klasörü)",
    )
    commands = parser.add_subparsers(dest="komut", required=True, metavar="KOMUT")

    separator = commands.add_parser("ayirac", help="QR ayıraç sayfası PDF'i yazar")
    separator.add_argument("cikti", type=Path, metavar="CIKTI.pdf", help="yazılacak PDF")
    separator.add_argument("--adet", type=int, default=10, help="yaprak sayısı (varsayılan 10)")
    separator.set_defaults(handler=_separator)

    settings = commands.add_parser("ayar", help="uygulama ayarları")
    settings_commands = settings.add_subparsers(dest="ayar_komutu", required=True, metavar="KOMUT")
    p = settings_commands.add_parser("goster", help="ayarları gösterir")
    p.set_defaults(handler=_show_settings)
    p = settings_commands.add_parser("saklama", help="iş dosyalarının ne kadar saklanacağı")
    p.add_argument(
        "deger", metavar="sakla|disa-aktarinca-sil|GUN",
        help="saklama ayarı. GUN: son değişiklikten bu kadar gün sonra iş silinir, dışa "
             "aktarılmamış olsa da (pencere açılırken ve is listele'de)")
    p.set_defaults(handler=_set_retention)

    jobs.add_commands(commands)
    ocr.add_commands(commands)
    templates.add_commands(commands)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    from multiprocessing import freeze_support

    freeze_support()  # OCRmyPDF's worker processes in the frozen Windows app
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return int(exit_.code or 0)
    store = JobStore(args.kok if args.kok else default_root())
    try:
        return args.handler(args, store)
    except (UserError, BatchError, JobFileError, EngineUnavailable, SettingsError,
            TemplateError) as error:
        jobs.finish_progress_line()
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        jobs.finish_progress_line()
        name = Path(error.filename).name if error.filename else ""
        print(f"Dosyaya erişilemedi: {name} ({error.strerror})", file=sys.stderr)
        return 2
