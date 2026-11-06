"""`evrakci is ...` commands."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from evrakci.cli.errors import UserError
from evrakci.pipeline.cuts import (
    Document,
    compute_documents,
    current_values,
    document_template,
    record_values,
)
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.index import write_index
from evrakci.pipeline.job import Job, job_to_dict, parse_page_id
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.tesseract import default_engine, default_tessdata
from evrakci.pipeline.ocr.textlayer import add_text_layer
from evrakci.pipeline.render import render_page
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Template, TemplateError
from evrakci.pipeline.templates.read import read_document
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


def _template_names(args: argparse.Namespace) -> dict[str, str]:
    from evrakci.cli.templates import template_store

    return {t.id: t.name for t in template_store(args).list()}


def _check_marks(job: Job, document: Document) -> list[str]:
    marks = []
    if "leftover" in document.flags:
        marks.append("eksik sayfa")
    if "mixed_templates" in document.flags:
        marks.append("karışık şablon")
    first = document.page_ids[0]
    if first in job.read_errors:
        marks.append(job.read_errors[first])
    values = current_values(job, document)
    if values is None and document_template(job, document)[0] and first in job.values:
        marks.append("yeniden okunmalı")
    if values and any(v.flagged for v in values.values()):
        marks.append("okunamayan değer")
    return marks


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
    names = _template_names(args) if job.templates else {}
    for number, (positions, document) in enumerate(
        zip(doc_positions, documents, strict=True), start=1
    ):
        template_id, _ = document_template(job, document)
        template = f" ({names.get(template_id, template_id)})" if template_id else ""
        marks = _check_marks(job, document)
        mark = f"  [kontrol: {', '.join(marks)}]" if marks else ""
        print(f"{number}. belge{template}: sayfa {positions_text(positions)}{mark}")
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


def _layer_note(pdfa: bool, note: str | None) -> str:
    return " (PDF/A-2b)" if pdfa else f" (normal PDF: {note})"


def _job_templates(args: argparse.Namespace, job: Job) -> dict[str, Template | None]:
    from evrakci.cli.templates import template_store

    store_ = template_store(args)
    found: dict[str, Template | None] = {}
    for application in job.templates:
        if application.template_id not in found:
            try:
                found[application.template_id] = store_.load(application.template_id)
            except (KeyError, TemplateError):
                found[application.template_id] = None
    return found


def export(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    items = plan_export(job, _job_templates(args, job))
    with_layer = not args.metin_katmani_yok
    if with_layer and items:
        reason = default_engine().available()
        if reason:
            raise UserError(
                f"{reason}. Metin katmanı olmadan yazmak için --metin-katmani-yok kullanın."
            )
    try:
        paths = write_documents(
            [i.document for i in items],
            store.batch_files(job),
            job.rotations,
            args.cikti,
            names=[i.name for i in items],
        )
    except FileExistsError as error:
        raise UserError(
            f"Çıktı klasöründe önceki bir dışa aktarımdan dosya var ({error}): {args.cikti}. "
            "Lütfen boş bir klasör seçin."
        ) from None
    notes = {}
    if with_layer and paths:
        tessdata = default_tessdata()
        label = "tur_best" if tessdata.folder else "sistem (tur)"
        print(f"Türkçe veri: {label}")
        for number, (path, item) in enumerate(zip(paths, items, strict=True), start=1):
            print(f"\rMetin katmanı: {number}/{len(paths)} belge", end="", file=sys.stderr)
            # The original stays in place until the layered copy is complete.
            layered = path.with_name(path.name + ".gecici")
            try:
                result = add_text_layer(path, layered, tessdata=tessdata)
                os.replace(layered, path)
            except (EngineUnavailable, OSError) as error:
                print(file=sys.stderr)
                done = ", ".join(p.name for p in paths[: number - 1]) or "yok"
                raise UserError(
                    f"{path.name}: {error}. Tüm belgeler yazıldı; metin katmanı eklenenler: {done}."
                ) from None
            finally:
                layered.unlink(missing_ok=True)
            item.pdfa = result.pdfa
            if not result.pdfa and result.note:
                item.checks.append(f"PDF/A değil: {result.note}")
            notes[path] = _layer_note(result.pdfa, result.note)
        print(file=sys.stderr)
    for path, item in zip(paths, items, strict=True):
        positions = [job.position_of(pid) for pid in item.document.page_ids]
        checks = f" [kontrol: {', '.join(item.checks)}]" if item.checks else ""
        print(f"{path.name}: sayfa {positions_text(positions)}{notes.get(path, '')}{checks}")
    needing = sum(1 for item in items if item.checks)
    listing = ""
    if paths:
        write_index(items, job, Path(args.cikti) / "index.xlsx")
        listing = " Liste: index.xlsx"
    print(f"{len(paths)} belge yazıldı, {needing} belge kontrol gerektiriyor.{listing}")
    return 0


def apply_template(args: argparse.Namespace, store: JobStore) -> int:
    from evrakci.cli.templates import load_template, template_store

    job = load_job(store, args.id)
    start, end = parse_range(args.aralik)
    template = load_template(template_store(args), args.sablon)
    page_ids = [page_id_at(job, position) for position in range(start, end + 1)]
    job.apply_template(page_ids, template.id)
    store.save(job)
    print(f"Şablon uygulandı: sayfa {start}-{end}, {template.name}")
    return 0


def _document_pages(store: JobStore, job: Job, document: Document):
    files = store.batch_files(job)

    def page_image(index: int):
        pid = document.page_ids[index]
        batch_id, page_index = parse_page_id(pid)
        return render_page(files[batch_id], page_index, job.rotations.get(pid, 0))

    return page_image


def read_values(args: argparse.Namespace, store: JobStore) -> int:

    job = load_job(store, args.id)
    engine = default_engine()
    reason = engine.available()
    if reason:
        raise UserError(reason)
    templates: dict[str, Template | None] = {}
    documents = compute_documents(job)
    work = [
        (number, document, document_template(job, document)[0])
        for number, document in enumerate(documents, start=1)
    ]
    work = [item for item in work if item[2] is not None]
    if args.sadece_eksik:
        work = [item for item in work if current_values(job, item[1]) is None]
    try:
        for done, (number, document, template_id) in enumerate(work, start=1):
            print(f"\rOkunuyor: {done}/{len(work)} belge", end="", file=sys.stderr, flush=True)
            line = _read_one(args, store, job, document, template_id, templates, engine)
            print(f"{number}. belge{line}")
            if done % 10 == 0:
                store.save(job)  # keep progress if the run is stopped
    finally:
        if work:
            print(file=sys.stderr)
        store.save(job)
    print(f"{len(work)} belge okundu.")
    return 0


def _read_one(args, store, job, document, template_id, templates, engine) -> str:
    """Read one document; problems are recorded on it and never stop the run."""
    from evrakci.cli.templates import template_store

    first = document.page_ids[0]
    if template_id not in templates:
        try:
            templates[template_id] = template_store(args).load(template_id)
        except KeyError:
            templates[template_id] = f"Şablon bulunamadı: {template_id}"
        except TemplateError as error:
            templates[template_id] = str(error)
    template = templates[template_id]
    if isinstance(template, str):
        job.read_errors[first] = template
        job.values.pop(first, None)
        return f": {template}"
    try:
        values = read_document(
            template, len(document.page_ids), _document_pages(store, job, document), engine
        )
    except (EngineUnavailable, OSError) as error:
        job.read_errors[first] = str(error)
        return f": {error}"
    job.read_errors.pop(first, None)
    previous = current_values(job, document) or {}
    for key, old in previous.items():
        if old.edited and key in values:
            values[key] = old  # the user's correction wins over a new reading
    record_values(job, document, template.id, values)
    names = template.names_by_key()
    summary = ", ".join(f"{names[k]}={v.value or '?'}" for k, v in values.items())
    mark = " [kontrol]" if any(v.flagged for v in values.values()) else ""
    return f" ({template.name}): {summary}{mark}"


def _templated_documents(args, job: Job):
    """(number, document, template or None) for every document that has a template."""
    from evrakci.cli.templates import template_store

    store_ = template_store(args)
    cache: dict[str, Template | None] = {}
    for number, document in enumerate(compute_documents(job), start=1):
        template_id, _ = document_template(job, document)
        if template_id is None:
            continue
        if template_id not in cache:
            try:
                cache[template_id] = store_.load(template_id)
            except (KeyError, TemplateError):
                cache[template_id] = None
        yield number, document, cache[template_id]


def list_values(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    for number, document, template in _templated_documents(args, job):
        marks = _check_marks(job, document)
        if args.kontrol and not marks:
            continue
        positions = positions_text([job.position_of(p) for p in document.page_ids])
        name = template.name if template else "şablon bulunamadı"
        print(f"{number}. belge ({name}) sayfa {positions}")
        values = current_values(job, document)
        if template is None or values is None:
            print("  değerler okunmadı")
            continue
        for variable in template.variables:
            value = values.get(variable.key)
            if value is None:
                print(f"  {variable.name}: [okunmadı]")
            elif value.flagged:
                hint = f", öneri: {value.suggestion}" if value.suggestion else ""
                print(f"  {variable.name}: [okunamadı{hint}]")
            else:
                mark = " [düzeltildi]" if value.edited else ""
                print(f"  {variable.name}: {value.value}{mark}")
    return 0


def fix_value(args: argparse.Namespace, store: JobStore) -> int:
    from evrakci.pipeline.review import accept_suggestion, set_value

    job = load_job(store, args.id)
    found = {n: (d, t) for n, d, t in _templated_documents(args, job)}
    if args.belge not in found:
        raise UserError(f"Belge yok: {args.belge} (şablonlu belge numarası, is goster)")
    document, template = found[args.belge]
    if template is None:
        raise UserError(f"{args.belge}. belgenin şablonu bulunamadı.")
    try:
        key = template.variable(args.ad).key
    except TemplateError as error:
        raise UserError(str(error)) from None
    try:
        if args.oneri:
            accept_suggestion(job, document, key)
        else:
            if args.deger is None:
                raise UserError("Yeni değeri yazın veya --oneri kullanın.")
            set_value(job, document, key, args.deger)
    except KeyError:
        raise UserError(f"{args.belge}. belgenin değerleri okunmadı (is oku).") from None
    except ValueError:
        raise UserError(f"{args.ad} için öneri yok.") from None
    store.save(job)
    print(f"{args.belge}. belge, {args.ad}: {current_values(job, document)[key].value}")
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

    p = job_commands.add_parser("sablon-uygula", help="seçili sayfalara şablon uygular")
    p.add_argument("id", help="iş numarası")
    p.add_argument("aralik", metavar="BAS-SON", help="sayfa aralığı, örn. 1-40")
    p.add_argument("sablon", metavar="SABLON", help="şablon numarası")
    p.set_defaults(handler=apply_template)

    p = job_commands.add_parser("oku", help="şablonlu belgelerdeki değişkenleri okur")
    p.add_argument("id", help="iş numarası")
    p.add_argument(
        "--sadece-eksik", action="store_true", help="yalnızca henüz okunmamış belgeleri oku"
    )
    p.set_defaults(handler=read_values)

    p = job_commands.add_parser("degerler", help="okunan değerleri listeler")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--kontrol", action="store_true", help="yalnızca kontrol gereken belgeler")
    p.set_defaults(handler=list_values)

    p = job_commands.add_parser("deger", help="bir değeri düzeltir veya öneriyi kabul eder")
    p.add_argument("id", help="iş numarası")
    p.add_argument("belge", type=int, metavar="BELGE", help="belge numarası (is goster)")
    p.add_argument("ad", help="değişken adı")
    p.add_argument("deger", nargs="?", help="yeni değer")
    p.add_argument("--oneri", action="store_true", help="okunan öneriyi kabul et")
    p.set_defaults(handler=fix_value)

    p = job_commands.add_parser("disa-aktar", help="her belgeyi ayrı PDF olarak yazar")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--cikti", type=Path, required=True, help="çıktı klasörü")
    p.add_argument(
        "--metin-katmani-yok",
        action="store_true",
        help="aranabilir metin katmanı ve PDF/A olmadan yaz",
    )
    p.set_defaults(handler=export)
