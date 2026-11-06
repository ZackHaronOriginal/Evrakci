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
from evrakci.pipeline.writer import write_documents


def load_job(store: JobStore, job_id: str) -> Job:
    try:
        return store.load(job_id)
    except KeyError:
        raise UserError(f"İş bulunamadı: {job_id}") from None


def positions_text(positions: list[int]) -> str:
    return ", ".join(str(p) for p in positions)


_progress_line_open = False


def _progress(done: int, total: int) -> None:
    global _progress_line_open
    finished = done == total
    end = "\n" if finished else ""
    print(f"\rİnceleniyor: {done}/{total} sayfa", end=end, file=sys.stderr, flush=True)
    _progress_line_open = not finished


def finish_progress_line() -> None:
    """End an unfinished progress line, so an error message starts on its own line."""
    global _progress_line_open
    if _progress_line_open:
        print(file=sys.stderr)
        _progress_line_open = False


def create(args: argparse.Namespace, store: JobStore) -> int:
    job = store.create_job(args.ad, args.pdf, progress=_progress)
    print(job.id)
    return 0


def list_jobs(args: argparse.Namespace, store: JobStore) -> int:
    def unreadable(job_id: str) -> None:
        print(f"Okunamayan iş: {job_id}", file=sys.stderr)

    for job in store.list_jobs(on_error=unreadable):
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


def page_id_at(job: Job, position: int) -> str:
    try:
        return job.page_at(position)
    except IndexError:
        raise UserError(f"Sayfa yok: {position}") from None


def parse_range(text: str) -> tuple[int, int]:
    """`BAS-SON`, or a single page number."""
    start, dash, end = text.partition("-")
    if not dash:
        end = start
    if not start.isdigit() or not end.isdigit() or int(start) > int(end):
        raise UserError(f"Geçersiz aralık: {text}")
    return int(start), int(end)


def apply_filter(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    start, end = parse_range(args.aralik)
    if args.n < 1:
        raise UserError("N en az 1 olmalı.")
    page_ids = [page_id_at(job, position) for position in range(start, end + 1)]
    job.apply_filter(page_ids, args.n)
    store.save(job)
    print(f"Filtre uygulandı: sayfa {start}-{end}, her {args.n} sayfa bir belge")
    return 0


def cut(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    pid = page_id_at(job, args.sayfa)
    if args.kaldir:
        try:
            job.remove_cut(pid)
        except ValueError:
            raise UserError(f"Bu sayfada kesim yok: {args.sayfa}") from None
        message = f"Kesim kaldırıldı: sayfa {args.sayfa}"
    else:
        try:
            job.add_cut(pid)
        except ValueError:
            raise UserError(f"Bu sayfada zaten kesim var: {args.sayfa}") from None
        message = f"Kesim eklendi: sayfa {args.sayfa} öncesi"
    store.save(job)
    print(message)
    return 0


def edit_page(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    pid = page_id_at(job, args.sayfa)
    if args.sil:
        job.delete_page(pid)
        message = f"Sayfa {args.sayfa} silindi"
    elif args.geri_al:
        job.undelete_page(pid)
        message = f"Sayfa {args.sayfa} geri alındı"
    elif args.bos_geri_al:
        job.restore_empty(pid)
        message = f"Boş sayfa {args.sayfa} geri getirildi"
    else:
        try:
            job.rotate(pid, args.dondur)
        except ValueError:
            raise UserError("Döndürme 90'ın katı olmalı (90, 180, 270).") from None
        message = f"Sayfa {args.sayfa} döndürüldü ({args.dondur}°)"
    store.save(job)
    print(message)
    return 0


def empty_pages(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    job.drop_empty = args.durum == "ac"
    store.save(job)
    print(f"Boş sayfaları atma: {'açık' if job.drop_empty else 'kapalı'}")
    return 0


def export(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    documents = compute_documents(job)
    try:
        paths = write_documents(documents, store.batch_files(job), job.rotations, args.cikti)
    except FileExistsError:
        raise UserError(
            f"Çıktı klasöründe önceki dışa aktarımdan dosyalar var: {args.cikti}. "
            "Lütfen boş bir klasör seçin."
        ) from None
    for path, document in zip(paths, documents, strict=True):
        positions = [job.position_of(pid) for pid in document.page_ids]
        print(f"{path.name}: sayfa {positions_text(positions)}")
    print(f"{len(paths)} belge yazıldı.")
    return 0


def move_batch(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    try:
        job.move_batch(args.parti, args.sira - 1)
    except KeyError:
        raise UserError(f"Parti bulunamadı: {args.parti}") from None
    except IndexError:
        raise UserError(f"Geçersiz sıra: {args.sira}") from None
    store.save(job)
    print(f"{args.parti} {args.sira}. sıraya taşındı")
    return 0


def remove_batch(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    try:
        store.remove_batch(job, args.parti)
    except KeyError:
        raise UserError(f"Parti bulunamadı: {args.parti}") from None
    print(f"{args.parti} işten çıkarıldı")
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

    p = job_commands.add_parser("parti-tasi", help="bir partinin sırasını değiştirir")
    p.add_argument("id", help="iş numarası")
    p.add_argument("parti", help="parti, örn. b2")
    p.add_argument("sira", type=int, metavar="SIRA", help="yeni sıra (1'den başlar)")
    p.set_defaults(handler=move_batch)

    p = job_commands.add_parser("parti-sil", help="bir partiyi işten çıkarır")
    p.add_argument("id", help="iş numarası")
    p.add_argument("parti", help="parti, örn. b2")
    p.set_defaults(handler=remove_batch)

    p = job_commands.add_parser("goster", help="belgeleri ve QR sayfalarını gösterir")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--json", action="store_true", help="makine okunur çıktı")
    p.set_defaults(handler=show)

    p = job_commands.add_parser("sil", help="işi siler")
    p.add_argument("id", help="iş numarası")
    p.set_defaults(handler=delete)

    p = job_commands.add_parser("filtre", help="seçili sayfalara 'her N sayfa bir belge' uygular")
    p.add_argument("id", help="iş numarası")
    p.add_argument("aralik", metavar="BAS-SON", help="sayfa aralığı, örn. 1-40")
    p.add_argument("n", type=int, metavar="N", help="kaç sayfada bir belge")
    p.set_defaults(handler=apply_filter)

    p = job_commands.add_parser("kes", help="bir sayfanın önüne kesim ekler veya kaldırır")
    p.add_argument("id", help="iş numarası")
    p.add_argument("sayfa", type=int, metavar="SAYFA", help="sayfa numarası")
    p.add_argument("--kaldir", action="store_true", help="kesimi kaldırır")
    p.set_defaults(handler=cut)

    p = job_commands.add_parser("sayfa", help="bir sayfayı siler, geri alır veya döndürür")
    p.add_argument("id", help="iş numarası")
    p.add_argument("sayfa", type=int, metavar="SAYFA", help="sayfa numarası")
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--sil", action="store_true", help="sayfayı siler")
    action.add_argument("--geri-al", action="store_true", help="silinen sayfayı geri alır")
    action.add_argument("--dondur", type=int, metavar="DERECE", help="saat yönünde döndürür")
    action.add_argument(
        "--bos-geri-al", action="store_true", help="atılan boş sayfayı geri getirir"
    )
    p.set_defaults(handler=edit_page)

    p = job_commands.add_parser("bos-sayfalar", help="boş sayfaları atmayı açar veya kapatır")
    p.add_argument("id", help="iş numarası")
    p.add_argument("durum", choices=["ac", "kapat"], help="ac veya kapat")
    p.set_defaults(handler=empty_pages)

    p = job_commands.add_parser("disa-aktar", help="her belgeyi ayrı PDF olarak yazar")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--cikti", type=Path, required=True, help="çıktı klasörü")
    p.set_defaults(handler=export)
