"""`evrakci is ...` commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pypdfium2 as pdfium

from evrakci.cli.errors import UserError
from evrakci.pipeline.analyze import EMPTY_INK_RATIO
from evrakci.pipeline.cuts import (
    Document,
    compute_documents,
    current_values,
    document_template,
    record_read_error,
)
from evrakci.pipeline.export import PREVIEW_HEADER, plan_export, preview_line, sources_text
from evrakci.pipeline.exporting import (
    ExportError,
    export_job,
    may_delete_after_export,
    plan_names,
)
from evrakci.pipeline.job import Job, apply_page_sizes, job_to_dict, parse_page_id
from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.tesseract import default_engine, default_tessdata
from evrakci.pipeline.ocr.textlayer import add_text_layer
from evrakci.pipeline.render import render_page
from evrakci.pipeline.review import needs_reading, store_reading
from evrakci.pipeline.select import (
    FARKLI_BY,
    FARKLI_REFERENCE,
    GUVEN_CHECKS,
    GUVEN_LEVELS,
    GUVEN_WORDS,
    Criterion,
    evaluate,
    guven_text,
    reason_count_text,
    values_read,
)
from evrakci.pipeline.select import (
    select_pages as select_by_filters,
)
from evrakci.pipeline.settings import DELETE_AFTER_EXPORT, Settings, SettingsError, load_settings
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Template, TemplateError, template_revision
from evrakci.pipeline.templates.read import read_document
from evrakci.pipeline.templates.values import value_level


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


def _settings() -> Settings:
    """The settings, or the safe default (keep everything) if the file can't be read."""
    try:
        return load_settings()
    except SettingsError as error:
        print(f"{error}. Varsayılan kullanılıyor: sakla.", file=sys.stderr)
        return Settings()


def apply_retention(store: JobStore) -> None:
    """Delete jobs past the day limit, if the retention setting has one."""
    days = _settings().retention_days
    if days:

        def failed(message: str) -> None:
            print(f"Silinemedi: {message}", file=sys.stderr)

        for job_id in store.delete_older_than(days, on_error=failed):
            print(f"Saklama süresi doldu, silindi: {job_id}", file=sys.stderr)


def create(args: argparse.Namespace, store: JobStore) -> int:
    apply_retention(store)
    job = store.create_job(args.ad, args.pdf, progress=_progress)
    print(job.id)
    return 0


def list_jobs(args: argparse.Namespace, store: JobStore) -> int:
    apply_retention(store)

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


def _export_marks(job: Job, templates: dict[str, Template | None]) -> dict[str, list[str]]:
    """What export would mark, per document (keyed by its first page): one source of truth."""
    return {item.document.page_ids[0]: item.checks for item in plan_export(job, templates)}


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
    marks_of = _export_marks(job, _job_templates(args, job) if job.templates else {})
    for number, (positions, document) in enumerate(
        zip(doc_positions, documents, strict=True), start=1
    ):
        template_id, _ = document_template(job, document)
        template = f" ({names.get(template_id, template_id)})" if template_id else ""
        marks = marks_of.get(document.page_ids[0], [])
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


def remove_filter(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    start, end = parse_range(args.aralik)
    page_ids = [page_id_at(job, position) for position in range(start, end + 1)]
    filtered = {pid for f in job.filters for pid in f.page_ids}
    count = sum(1 for pid in page_ids if pid in filtered)
    if not count:
        raise UserError("Bu sayfalarda filtre yok.")
    job.remove_filter(page_ids)
    store.save(job)
    print(f"Filtre kaldırıldı, {count} sayfa.")
    return 0


def blank_percent(text: str) -> float:
    """`--esik`: a percentage, the decimal comma or point (0,3), from 0,1 to 5,0."""
    try:
        value = float(text.replace(",", "."))
    except ValueError:
        value = float("nan")
    if not 0.1 <= value <= 5.0:
        raise argparse.ArgumentTypeError("En çok mürekkep oranı: 0,1–5,0 %")
    return value


def check_sec(args: argparse.Namespace) -> None:
    """Usage errors of `is sec`, raised through argparse (exit 2, its usage text) once the
    arguments are read: --filtre needs --sablon, --sil does not go with --sablon, and without
    --sablon a criterion is still required."""
    parser = args.sec_parser
    if not args.sablon and args.filtre:
        parser.error("--filtre için --sablon gerekir.")
    if not args.sablon and not args.olcut:
        parser.error("the following arguments are required: olcut")
    if args.sablon and getattr(args, "sil", False):
        parser.error("--sil, --sablon ile birlikte kullanılamaz.")
    if args.filtre:  # a name given twice counts once
        args.filtre = list(dict.fromkeys(args.filtre))


def select_saved(args: argparse.Namespace, store: JobStore,
                 extra: Criterion | None = None) -> int:
    """`is sec --sablon ŞABLON [--filtre AD ...] [ÖLÇÜT ...]`: the pages the window's
    saved-filter chips select (AND of the filters, all of the template's when none is named,
    and of `extra`, a criterion given on the command line); one function, select_pages, for
    the window and for this command. A filter this version cannot run is refused."""
    from evrakci.cli.templates import load_template, template_store

    job = load_job(store, args.id)
    template = load_template(template_store(args), args.sablon)
    try:
        chosen = ([template.saved_filter(name) for name in args.filtre] if args.filtre
                  else list(template.saved_filters))
    except TemplateError as error:
        raise UserError(str(error)) from None
    if not chosen and extra is None:
        print("Hiçbir filtre açık değil")
        return 0
    every = {t.id: t for t in template_store(args).list()}  # what the window's chips see
    criteria = [Criterion(f.kind, f.params) for f in chosen]
    result = select_by_filters(job, [*criteria, *([extra] if extra else [])], every)
    broken = [chosen[n].name for n in result.unknown_at if n < len(chosen)]
    if broken:
        raise UserError("\n".join(f"{name}: Bu filtreyi bu sürüm tanımıyor" for name in broken))
    for item, count in zip(chosen, result.per_filter_counts, strict=False):
        print(f"{item.name}: {count} sayfa")
    if not result.page_ids:
        print("Eşleşen sayfa yok.")
        return 0
    position = {pid: n for n, pid in enumerate(job.ordered_page_ids(), start=1)}
    print(f"{len(criteria) + (1 if extra else 0)} filtre açık: {len(result.page_ids)} sayfa")
    print(f"sayfa {positions_text([position[pid] for pid in result.page_ids])}")
    return 0


def select_pages(args: argparse.Namespace, store: JobStore) -> int:
    """`is sec`: the pages the window's "Ölçüte göre seç…" would select; `--sil` deletes them."""
    job = load_job(store, args.id)
    params: dict = {}
    if args.olcut == "belge":
        params = {"number": args.numara}
    elif args.olcut == "bos":
        params = {"ink": round(args.esik / 100, 6)}
    elif args.olcut == "guven":
        if args.sablon:
            return select_saved(args, store, _guven_criterion(args))
        return select_guven(args, job)
    elif args.olcut == "farkli":
        # An older job: read the missing sizes in memory, for this count only. The file is not
        # written, so a window that has the job open is never overwritten.
        apply_page_sizes(job, store.read_sizes(store.size_requests(job)))
        by = [name for name in FARKLI_BY if getattr(args, name)] or list(FARKLI_BY)
        params = {"by": by, "reference": args.karsilastir}
    if args.sablon:
        return select_saved(args, store, Criterion(args.olcut, params))
    match = evaluate(job, Criterion(args.olcut, params))
    unknown = match.reasons.get("bilinmiyor", 0) if args.olcut == "farkli" else 0
    if not match.page_ids:
        print("Eşleşen sayfa yok.")
        if unknown:
            print(f"Boyutu bilinmiyor ({unknown})")
        return 0
    position = {pid: n for n, pid in enumerate(job.ordered_page_ids(), start=1)}
    positions = [position[pid] for pid in match.page_ids]
    print(f"{len(positions)} sayfa seçildi.")
    print(f"sayfa {positions_text(positions)}")
    if unknown:
        print(f"Boyutu bilinmiyor ({unknown})")
    if args.sil:
        for pid in match.page_ids:
            job.delete_page(pid)
        store.save(job)
        print(f"Sayfa {positions_text(positions)} silindi")
    return 0


GUVEN_NAMES = {"kontrol": "kontrol", "okunamadi": "okunamadi", "orta": "orta",
               "okunmadi": "okunmadi", "eksik-sayfa": "eksik sayfa",
               "karisik-sablon": "karışık şablon"}


def _guven_criterion(args: argparse.Namespace) -> Criterion:
    asked = [GUVEN_NAMES[name] for name in (args.neden or [
        "kontrol", "okunamadi", "okunmadi", "eksik-sayfa", "karisik-sablon"])]
    return Criterion("guven", {
        "levels": [r for r in asked if r in GUVEN_LEVELS],
        "checks": [r for r in asked if r in GUVEN_CHECKS],
        "pages": args.sayfalar})


def select_guven(args: argparse.Namespace, job: Job) -> int:
    """`is sec guven`: the window's "Kontrol gerekenler", with its reasons and counts."""
    templates = _job_templates(args, job)
    if not values_read(job):
        print("Değerler henüz okunmadı")
        return 0
    match = evaluate(job, _guven_criterion(args), templates=templates)
    for reason, n in match.reasons.items():
        print(f"{GUVEN_WORDS[reason]}  {reason_count_text(reason, n)}")
    if not match.page_ids:
        print("Eşleşen sayfa yok.")
        return 0
    position = {pid: n for n, pid in enumerate(job.ordered_page_ids(), start=1)}
    print(guven_text(match))
    print(f"{match.documents} belge, {match.count()} sayfa")
    print(f"sayfa {positions_text([position[pid] for pid in match.page_ids])}")
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
    return " (PDF/A-2b)" if pdfa else f" (normal PDF: {note or 'PDF/A doğrulanamadı'})"


def _job_templates(args: argparse.Namespace, job: Job) -> dict[str, Template | None]:
    from evrakci.cli.templates import template_store

    store_ = template_store(args)
    found: dict[str, Template | None] = {}
    for application in job.templates:
        if application.template_id and application.template_id not in found:
            try:
                found[application.template_id] = store_.load(application.template_id)
            except (KeyError, TemplateError):
                found[application.template_id] = None
    return found


def _check_subfolder(args: argparse.Namespace) -> bool:
    """Documents to check go into their own subfolder: the setting, unless --kontrol-ayri-yok."""
    return not args.kontrol_ayri_yok and _settings().check_subfolder


def preview_names(args: argparse.Namespace, store: JobStore) -> int:
    """`--onizle`: the names an export into --cikti would write (Kaynak, new name, note), the
    same lines as the window's "Ad listesini kopyala"; nothing is written."""
    job = load_job(store, args.id)
    try:
        items = plan_names(job, _job_templates(args, job), Path(args.cikti),
                           _check_subfolder(args))
    except ValueError as error:
        raise UserError(str(error)) from None
    print(PREVIEW_HEADER)
    for item in items:
        print(preview_line(sources_text(item.sources), item.relative, item.name_note))
    return 0


def export(args: argparse.Namespace, store: JobStore) -> int:
    if args.onizle:
        return preview_names(args, store)
    job = load_job(store, args.id)
    store.save(job)  # marks the job as in use, so the day limit never removes it mid-export
    with_layer = not args.metin_katmani_yok
    tessdata = None

    def progress(stage: str, done: int, total: int) -> None:
        if stage == "layer" and done < total:
            print(f"\rMetin katmanı: {done + 1}/{total} belge", end="", file=sys.stderr)

    try:
        if with_layer:
            tessdata = default_tessdata()
            label = "tur_best" if tessdata.folder else "sistem (tur)"
            print(f"Türkçe veri: {label}")
        result = export_job(
            job, store.batch_files(job), _job_templates(args, job), Path(args.cikti),
            with_layer=with_layer, progress=progress, engine=default_engine() if with_layer
            else None, add_layer=add_text_layer, tessdata=tessdata,
            check_subfolder=_check_subfolder(args),
        )
    except EngineUnavailable as error:
        raise UserError(
            f"{error}. Metin katmanı olmadan yazmak için --metin-katmani-yok kullanın."
        ) from None
    except ExportError as error:
        if job.last_export is not None:  # files and index.xlsx are on disk (text layer failed)
            store.save(job)
        raise UserError(str(error)) from None
    finally:
        if with_layer:
            print(file=sys.stderr)
    store.save(job)  # the export time (job.last_export) reaches the job file
    items, paths = result.items, result.paths
    notes = {path: _layer_note(pdfa, note) for path, (pdfa, note) in result.notes.items()}
    for path, item in zip(paths, items, strict=True):
        positions = [job.position_of(pid) for pid in item.document.page_ids]
        checks = f" [kontrol: {', '.join(item.checks)}]" if item.checks else ""
        name_note = f" [ad: {item.name_note}]" if item.name_note else ""
        print(f"{item.relative}: sayfa {positions_text(positions)}{notes.get(path, '')}"
              f"{name_note}{checks}")
    needing = result.needing_check
    listing = " Liste: index.xlsx" if paths else ""
    print(f"{len(paths)} belge yazıldı, {needing} belge kontrol gerektiriyor.{listing}")
    if needing:
        print("Kontrol listesi: index.xlsx, sayfa 'Kontrol gerekenler'.")
    if _settings().retention == DELETE_AFTER_EXPORT:
        if may_delete_after_export(result):
            store.delete(job.id)
            print(f"İş silindi (saklama ayarı): {job.id}")
        elif needing:
            print(
                f"İş saklandı: {needing} belge kontrol gerektiriyor; "
                "düzeltip yeniden dışa aktarabilirsiniz."
            )
        elif result.paths and not result.with_layer:
            print("İş saklandı: metin katmanı eklenmedi; katmanla yeniden dışa aktarabilirsiniz.")
        else:
            print("İş saklandı: hiçbir belge yazılmadı.")
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


def remove_template(args: argparse.Namespace, store: JobStore) -> int:
    job = load_job(store, args.id)
    start, end = parse_range(args.aralik)
    job.remove_template([page_id_at(job, position) for position in range(start, end + 1)])
    store.save(job)
    print(f"Şablon kaldırıldı: sayfa {start}-{end}")
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
        work = [item for item in work if _needs_reading(args, job, item[1], item[2], templates)]
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


def _load_cached(args, template_id: str, templates: dict) -> Template | str:
    """The template, or a Turkish reason it cannot be used; loaded once per run."""
    from evrakci.cli.templates import template_store

    if template_id not in templates:
        try:
            templates[template_id] = template_store(args).load(template_id)
        except KeyError:
            templates[template_id] = f"Şablon bulunamadı: {template_id}"
        except TemplateError as error:
            templates[template_id] = str(error)
    return templates[template_id]


def _needs_reading(args, job: Job, document: Document, template_id: str, templates) -> bool:
    template = _load_cached(args, template_id, templates)
    if isinstance(template, str):
        return True  # read it, so the reason is recorded and shown
    return needs_reading(job, document, template)


def _read_one(args, store, job, document, template_id, templates, engine) -> str:
    """Read one document; problems are recorded on it and never stop the run."""
    template = _load_cached(args, template_id, templates)
    if isinstance(template, str):
        record_read_error(job, document, template_id, template)
        return f": {template}"
    try:
        values = read_document(
            template, len(document.page_ids), _document_pages(store, job, document), engine
        )
    except (EngineUnavailable, OSError, pdfium.PdfiumError) as error:
        record_read_error(job, document, template_id, str(error))
        return f": {error}"
    store_reading(job, document, template.id, values, template_revision(template))
    values = current_values(job, document)
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
    marks_of = _export_marks(job, _job_templates(args, job))
    for number, document, template in _templated_documents(args, job):
        marks = marks_of.get(document.page_ids[0], [])
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
                if value_level(value) == "okunamadi":
                    print(f"  {variable.name}: [okunamadı{hint}]")
                else:
                    read = value.value or next((r.text for r in sorted(
                        value.readings, key=lambda r: r.section) if r.text), "")
                    print(f"  {variable.name}: {read + ' ' if read else ''}[kontrol{hint}]")
            else:
                mark = " [düzeltildi]" if value.edited else ""
                print(f"  {variable.name}: {value.value}{mark}")
    return 0


def fix_value(args: argparse.Namespace, store: JobStore) -> int:
    from evrakci.pipeline.review import (
        REQUIRED_EMPTY,
        accept_suggestion,
        can_revert,
        revert_value,
        set_value,
    )

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
        elif args.geri_al:
            current = current_values(job, document)
            value = current.get(key) if current is not None else None
            # only a hand-typed value with no reading has nothing to go back to; an
            # unedited value keeps the command's earlier behaviour
            if value is not None and value.edited and not can_revert(value):
                raise UserError(f"{args.ad}: Bu değer elle yazıldı; okunmuş bir değer yok.")
            revert_value(job, document, key)
        else:
            if args.deger is None:
                raise UserError("Yeni değeri yazın, ya da --oneri veya --geri-al kullanın.")
            variable = template.variable(args.ad)
            if not set_value(job, document, key, args.deger, variable.required):
                store.save(job)
                print(REQUIRED_EMPTY)
                return 0
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

    p = job_commands.add_parser("filtre-kaldir", help="Filtreyi kaldır")
    p.add_argument("id", help="iş numarası")
    p.add_argument("aralik", metavar="BAS-SON", help="sayfa aralığı, örn. 1-40")
    p.set_defaults(handler=remove_filter)

    p = job_commands.add_parser("sec", help="Ölçüte göre seç…")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--sablon", metavar="SABLON", help="Kayıtlı filtreler: şablon numarası")
    p.add_argument("--filtre", action="append", metavar="AD",
                   help="Kayıtlı filtreler: filtrenin adı (birden çok kez verilebilir; "
                        "verilmezse hepsi)")
    p.set_defaults(handler=select_saved, sec_parser=p, check=check_sec, sil=False)
    criteria = p.add_subparsers(dest="olcut", required=False)
    for name, label in (("belge", "Bu belge"), ("tek", "Tek sayfalar"), ("cift", "Çift sayfalar")):
        q = criteria.add_parser(name, help=label)
        if name == "belge":
            q.add_argument("--numara", type=int, required=True, metavar="N")
        q.add_argument("--sil", action="store_true", help="Sayfayı sil")
        q.set_defaults(handler=select_pages)
    q = criteria.add_parser("bos", help="Boş sayfalar")
    q.add_argument("--esik", type=blank_percent, default=EMPTY_INK_RATIO * 100, metavar="ORAN",
                   help="En çok mürekkep oranı: 0,1–5,0 %% (0,3)")
    q.add_argument("--sil", action="store_true", help="Sayfayı sil")
    q.set_defaults(handler=select_pages)
    q = criteria.add_parser("farkli", help="Farklı boyut veya yön")
    q.add_argument("--boyut", action="store_true", help="Boyut")
    q.add_argument("--yon", action="store_true", help="Yön")
    q.add_argument("--karsilastir", choices=FARKLI_REFERENCE, default="is",
                   help="Karşılaştır: Bütün iş / Her belge")
    q.set_defaults(handler=select_pages, sil=False)
    q = criteria.add_parser("guven", help="Kontrol gerekenler")
    q.add_argument("--neden", action="append", choices=list(GUVEN_NAMES), metavar="NEDEN",
                   help="Kontrol gerekenler: " + ", ".join(GUVEN_NAMES))
    q.add_argument("--sayfalar", choices=("deger", "belge"), default="deger",
                   help="Sayfalar: deger (Değerin sayfası), belge (Belgenin bütün sayfaları)")
    q.set_defaults(handler=select_pages)

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

    p = job_commands.add_parser("sablon-kaldir", help="seçili sayfalardaki şablonu kaldırır")
    p.add_argument("id", help="iş numarası")
    p.add_argument("aralik", metavar="BAS-SON", help="sayfa aralığı, örn. 1-40")
    p.set_defaults(handler=remove_template)

    p = job_commands.add_parser("oku", help="şablonlu belgelerdeki değişkenleri okur")
    p.add_argument("id", help="iş numarası")
    p.add_argument(
        "--sadece-eksik", action="store_true",
        help="yalnızca okunmamış, okunamamış ya da şablonu sonradan değişmiş belgeleri oku"
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
    choice = p.add_mutually_exclusive_group()
    choice.add_argument("deger", nargs="?", help="yeni değer")
    choice.add_argument("--oneri", action="store_true", help="okunan öneriyi kabul et")
    choice.add_argument("--geri-al", action="store_true",
                        help="düzeltmeyi geri al: değer yeniden kontrol bekler")
    p.set_defaults(handler=fix_value)

    p = job_commands.add_parser("disa-aktar", help="her belgeyi ayrı PDF olarak yazar")
    p.add_argument("id", help="iş numarası")
    p.add_argument("--cikti", type=Path, required=True, help="çıktı klasörü")
    p.add_argument(
        "--metin-katmani-yok",
        action="store_true",
        help="aranabilir metin katmanı ve PDF/A olmadan yaz",
    )
    p.add_argument(
        "--kontrol-ayri-yok",
        action="store_true",
        help="kontrol gerekenleri ayrı klasöre koyma",
    )
    p.add_argument(
        "--onizle",
        action="store_true",
        help="Adları karşılaştır",
    )
    p.set_defaults(handler=export)
