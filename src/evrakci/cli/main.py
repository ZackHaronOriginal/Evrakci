"""Argument parsing and error handling for `evrakci`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from evrakci import __version__
from evrakci.cli import jobs
from evrakci.cli.errors import UserError
from evrakci.pipeline.analyze import BatchError
from evrakci.pipeline.separator import make_separator_pdf
from evrakci.pipeline.store import JobFileError, JobStore, default_root


def _separator(args: argparse.Namespace, store: JobStore) -> int:
    if args.adet < 1:
        raise UserError("Adet en az 1 olmalı.")
    path = make_separator_pdf(args.cikti, sheets=args.adet)
    print(f"Ayıraç dosyası yazıldı: {path} ({args.adet} yaprak)")
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
    commands = parser.add_subparsers(dest="komut", required=True, metavar="KOMUT")

    separator = commands.add_parser("ayirac", help="QR ayıraç sayfası PDF'i yazar")
    separator.add_argument("cikti", type=Path, metavar="CIKTI.pdf", help="yazılacak PDF")
    separator.add_argument("--adet", type=int, default=10, help="yaprak sayısı (varsayılan 10)")
    separator.set_defaults(handler=_separator)

    jobs.add_commands(commands)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        return int(exit_.code or 0)
    store = JobStore(args.kok if args.kok else default_root())
    try:
        return args.handler(args, store)
    except (UserError, BatchError, JobFileError) as error:
        print(str(error), file=sys.stderr)
        return 2
    except OSError as error:
        name = Path(error.filename).name if error.filename else ""
        print(f"Dosyaya erişilemedi: {name} ({error.strerror})", file=sys.stderr)
        return 2
