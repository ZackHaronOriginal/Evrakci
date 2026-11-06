"""`evrakci is ...` commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evrakci.cli.errors import UserError
from evrakci.pipeline.cuts import compute_documents
from evrakci.pipeline.job import Job, job_to_dict
from evrakci.pipeline.store import JobStore


def load_job(store: JobStore, job_id: str) -> Job:
    try:
        return store.load(job_id)
    except KeyError:
        raise UserError(f"İş bulunamadı: {job_id}") from None


def positions_text(positions: list[int]) -> str:
    return ", ".join(str(p) for p in positions)


def _progress(done: int, total: int) -> None:
    end = "\n" if done == total else ""
    print(f"\rİnceleniyor: {done}/{total} sayfa", end=end, file=sys.stderr, flush=True)


def create(args: argparse.Namespace, store: JobStore) -> int:
    job = store.create_job(args.ad, args.pdf, progress=_progress)
    print(job.id)
    return 0


def list_jobs(args: argparse.Namespace, store: JobStore) -> int:
    for job in store.list_jobs():
        print(f"{job.id}  {job.name}  {len(job.pages)} sayfa")
    return 0


def add(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    batch = store.add_batch(job, args.pdf)
    print(f"{batch.id} eklendi ({batch.page_count} sayfa)")
    return 0


def show(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    documents = compute_documents(job)
    doc_positions = [[job.position_of(pid) for pid in d.page_ids] for d in documents]
    if args.json:
        payload = {
            "job": job_to_dict(job),
            "documents": [
                {"positions": positions, "flags": sorted(d.flags)}
                for positions, d in zip(doc_positions, documents, strict=True)
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0
    print(f"{job.name} ({job.id})")
    for number, (positions, document) in enumerate(
        zip(doc_positions, documents, strict=True), start=1
    ):
        mark = "  [eksik sayfa]" if "leftover" in document.flags else ""
        print(f"{number}. belge: sayfa {positions_text(positions)}{mark}")
    qr = [job.position_of(pid) for pid in job.ordered_page_ids() if job.pages[pid].is_separator]
    print(f"QR sayfaları: {positions_text(qr) if qr else 'yok'}")
    return 0


def delete(args: argparse.Namespace, store: JobStore) -> int:
    try:
        store.delete(args.id)
    except KeyError:
        raise UserError(f"İş bulunamadı: {args.id}") from None
    print(f"İş silindi: {args.id}")
    return 0


def add_commands(commands: argparse._SubParsersAction) -> None:
    job_parser = commands.add_parser("is", help="iş oluşturur, gösterir ve düzenler")
    job_commands = job_parser.add_subparsers(dest="is_komutu", required=True, metavar="KOMUT")

    p = job_commands.add_parser("olustur", help="taranmış PDF'lerden yeni iş oluşturur")
    p.add_argument("ad", help="işin adı")
    p.add_argument("pdf", type=Path, nargs="+", help="taranmış PDF'ler, tarama sırasıyla")
    p.set_defaults(handler=create)

    p = job_commands.add_parser("listele", help="kayıtlı işleri listeler")
    p.set_defaults(handler=list_jobs)

    p = job_commands.add_parser("ekle", help="işe yeni taranmış PDF ekler")
    p.add_argument("id", help="iş numarası")
    p.add_argument("pdf", type=Path, help="eklenecek PDF")
    p.set_defaults(handler=add)

    p = job_commands.add_parser("goster", help="belgeleri ve QR sayfalarını gösterir")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--json", action="store_true", help="makine okunur çıktı")
    p.set_defaults(handler=show)

    p = job_commands.add_parser("sil", help="işi siler")
    p.add_argument("id", help="iş numarası")
    p.set_defaults(handler=delete)
