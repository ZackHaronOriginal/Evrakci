"""Compare the window's export with the command line's export on a folder of PDFs.

For the owner to run on their own PC with anonymised scans. It never copies or uploads
documents: the PDFs are read where they are (the job store keeps its own working copy
inside the output folder, deleted at the end unless --isi-tut), and everything written
goes to the output folder the owner chooses.

    python tools/real_scan_check.py TARAMALAR_KLASORU --cikti SONUC_KLASORU
        [--sablon ID --sablon-kok KLASOR] [--her-n N] [--ocr acik|kapali|ikisi]

Stages (each timed, with peak memory): create job, [apply template + read values], then per
OCR mode: export with the window's function (`export_job`, as the Dışa Aktar tab calls it)
and with `evrakci is disa-aktar`. The two outputs are compared: file names, page count per
file and every cell of index.xlsx. Exit 0 = all comparisons pass, 1 = a difference or an
error. The last lines are a plain-text summary that can be sent back as is.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import platform
import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


def _rss_now_mb():
    """Current RSS in MB (psutil), or None when psutil is missing."""
    try:
        import psutil

        return psutil.Process().memory_info().rss / 1e6
    except Exception:  # not installed or not allowed
        return None


def _high_water_mb():
    """Peak RSS of the whole process so far (resource), or None (Windows without psutil)."""
    try:
        import resource

        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / (1e6 if sys.platform == "darwin" else 1e3)
    except Exception:
        return None


class Stage:
    """Context manager: seconds and peak memory of one stage.

    With psutil the peak is sampled every 50 ms inside the stage. Without it, the
    process-wide high-water mark after the stage is reported (it never goes down, so
    later stages can only show the same or a higher number)."""

    def __init__(self, name: str, log: list) -> None:
        self.name, self.log = name, log

    def __enter__(self):
        self.peak = _rss_now_mb()
        self.method = "psutil" if self.peak is not None else "resource"
        self._stop = threading.Event()
        if self.peak is not None:
            def sample():
                while not self._stop.wait(0.05):
                    self.peak = max(self.peak, _rss_now_mb() or 0)

            self._thread = threading.Thread(target=sample, daemon=True)
            self._thread.start()
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        seconds = time.perf_counter() - self.t0
        self._stop.set()
        if self.method == "psutil":
            self._thread.join()
            peak = max(self.peak, _rss_now_mb() or 0)
        else:
            peak = _high_water_mb()
        self.log.append((self.name, seconds, peak, self.method))
        return False


@dataclass
class Report:
    stages: list = field(default_factory=list)
    checks: list = field(default_factory=list)  # (label, ok, detail)

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        self.checks.append((label, ok, detail))


def run_cli(argv: list[str]) -> tuple[int, str, str]:
    from evrakci.cli import main

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def page_counts(folder: Path) -> dict[str, int]:
    import pikepdf

    counts = {}
    for path in sorted(folder.glob("*.pdf")):
        with pikepdf.open(path) as pdf:
            counts[path.name] = len(pdf.pages)
    return counts


def index_rows(folder: Path) -> list[list]:
    from openpyxl import load_workbook

    path = folder / "index.xlsx"
    if not path.is_file():
        return []
    book = load_workbook(path, read_only=True)
    try:
        return [list(row) for row in book.active.iter_rows(values_only=True)]
    finally:
        book.close()


def compare_outputs(label: str, window_dir: Path, cli_dir: Path, report: Report) -> None:
    a, b = page_counts(window_dir), page_counts(cli_dir)
    report.check(f"{label}: file names", sorted(a) == sorted(b),
                 f"window {len(a)} files, CLI {len(b)} files; "
                 f"only window: {sorted(set(a) - set(b))[:5]}, "
                 f"only CLI: {sorted(set(b) - set(a))[:5]}")
    wrong = [n for n in a if n in b and a[n] != b[n]]
    same_total = sum(a.values()) == sum(b.values())
    report.check(f"{label}: page count per file", not wrong and same_total,
                 f"window {sum(a.values())} pages, CLI {sum(b.values())} pages; "
                 f"differ: {wrong[:5]}")
    ra, rb = index_rows(window_dir), index_rows(cli_dir)
    bad = [i + 1 for i, (x, y) in enumerate(zip(ra, rb, strict=False)) if x != y]
    report.check(f"{label}: index.xlsx values", ra == rb and bool(ra) == bool(a),
                 f"rows window {len(ra)}, CLI {len(rb)}; first differing rows: {bad[:5]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("taramalar", type=Path, help="folder with the PDFs (read in place)")
    parser.add_argument("--cikti", type=Path, required=True,
                        help="output folder (must be empty or new); the only place written to")
    parser.add_argument("--ocr", choices=["acik", "kapali", "ikisi"], default="ikisi",
                        help="OCR text layer on, off or both (default both)")
    parser.add_argument("--sablon", help="template id: applied to all pages, values read")
    parser.add_argument("--sablon-kok", type=Path, help="template folder (with --sablon)")
    parser.add_argument("--her-n", type=int, default=0, metavar="N",
                        help="every N pages is a document (when there are no QR separators)")
    parser.add_argument("--isi-tut", action="store_true",
                        help="keep the job working copy in the output folder")
    args = parser.parse_args(argv)

    pdfs = sorted(args.taramalar.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF found in {args.taramalar}", file=sys.stderr)
        return 2
    out = args.cikti
    if out.exists() and any(out.iterdir()):
        print(f"Output folder is not empty: {out}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    work = out / "is-kopyasi"
    # A settings file that does not exist = default retention (keep), so the CLI export
    # never deletes the job before the second export runs.
    os.environ["EVRAKCI_AYARLAR"] = str(out / "yok-ayarlar.json")

    from evrakci.pipeline.exporting import export_job
    from evrakci.pipeline.job import job_from_dict, job_to_dict
    from evrakci.pipeline.store import JobStore

    report = Report()
    base = ["--kok", str(work)]
    if args.sablon_kok:
        base += ["--sablon-kok", str(args.sablon_kok)]

    with Stage("create job", report.stages):
        code, text, err = run_cli(base + ["is", "olustur", "real-scan-check", *map(str, pdfs)])
    if code != 0:
        print(err or text, file=sys.stderr)
        return 1
    job_id = text.strip().splitlines()[-1]
    store = JobStore(work)
    job = store.load(job_id)
    total = sum(b.page_count for b in job.batches)

    if args.her_n:
        code, _, err = run_cli(base + ["is", "filtre", job_id, f"1-{total}", str(args.her_n)])
        report.check("split filter", code == 0, err.strip())
    if args.sablon:
        with Stage("apply template + read values", report.stages):
            code, _, err = run_cli(
                base + ["is", "sablon-uygula", job_id, f"1-{total}", args.sablon])
            if code == 0:
                code, _, err = run_cli(base + ["is", "oku", job_id])
        report.check("template read", code == 0, err.strip())

    # Templates exactly as the CLI loads them (also what the window gives export_job).
    from evrakci.cli.jobs import _job_templates

    ns = argparse.Namespace(sablon_kok=args.sablon_kok, kok=work)
    modes = {"acik": [True], "kapali": [False], "ikisi": [True, False]}[args.ocr]
    for with_layer in modes:
        tag = "OCR on" if with_layer else "OCR off"
        job = store.load(job_id)
        win_dir, cli_dir = out / f"pencere-{int(with_layer)}", out / f"komut-{int(with_layer)}"
        with Stage(f"export, window function, {tag}", report.stages):
            try:
                copy = job_from_dict(job_to_dict(job))  # the window exports a copy
                result = export_job(copy, store.batch_files(copy), _job_templates(ns, copy),
                                    win_dir, with_layer=with_layer)
                report.check(f"{tag}: window export ran", True,
                             f"{len(result.paths)} files, {result.needing_check} need a check")
            except Exception as error:  # report, do not stop the other comparison
                report.check(f"{tag}: window export ran", False, f"{type(error).__name__}: {error}")
        extra = [] if with_layer else ["--metin-katmani-yok"]
        with Stage(f"export, CLI, {tag}", report.stages):
            code, _, err = run_cli(
                base + ["is", "disa-aktar", job_id, "--cikti", str(cli_dir), *extra])
        last = err.strip().splitlines()[-1] if err.strip() else ""
        report.check(f"{tag}: CLI export ran", code == 0, last)
        if win_dir.is_dir() and cli_dir.is_dir():
            with Stage(f"compare outputs, {tag}", report.stages):
                compare_outputs(tag, win_dir, cli_dir, report)

    if not args.isi_tut:
        shutil.rmtree(work, ignore_errors=True)

    lines = ["REAL SCAN CHECK SUMMARY",
             f"pdfs: {len(pdfs)}, pages: {total}, python {platform.python_version()}, "
             f"{platform.system()}"]
    for name, seconds, peak, method in report.stages:
        mem = "n/a" if peak is None else f"{peak:.0f} MB"
        note = "peak" if method == "psutil" else "process high-water so far"
        lines.append(f"stage {name}: {seconds:.1f} s, memory {mem} ({note})")
    for label, ok, detail in report.checks:
        suffix = "" if ok or not detail else f" -- {detail}"
        lines.append(f"{'PASS' if ok else 'FAIL'} {label}{suffix}")
    failed = [c for c in report.checks if not c[1]]
    lines.append("RESULT: " + ("PASS" if not failed else f"FAIL ({len(failed)} checks)"))
    text = "\n".join(lines)
    print(text)
    (out / "ozet.txt").write_text(text + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
