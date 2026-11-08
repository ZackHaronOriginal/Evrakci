"""`evrakci sablon ...` commands: make and edit templates from the command line."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pypdfium2 as pdfium

from evrakci.cli.errors import UserError
from evrakci.pipeline.ocr.tesseract import default_engine
from evrakci.pipeline.render import PageRenderer
from evrakci.pipeline.templates.model import (
    Section,
    Template,
    TemplateError,
    template_to_dict,
)
from evrakci.pipeline.templates.read import read_document
from evrakci.pipeline.templates.store import TemplateStore, default_template_root


def template_store(args: argparse.Namespace) -> TemplateStore:
    return TemplateStore(args.sablon_kok or default_template_root())


def load_template(store: TemplateStore, template_id: str) -> Template:
    try:
        return store.load(template_id)
    except KeyError:
        raise UserError(f"Şablon bulunamadı: {template_id}") from None
    except TemplateError as error:
        raise UserError(str(error)) from None


def page_text(page: int) -> str:
    return "son" if page == -1 else f"sondan {-page}." if page < 0 else str(page)


def parse_page(text: str) -> int:
    if text.strip().casefold() == "son":
        return -1
    try:
        page = int(text)
    except ValueError:
        raise UserError(f"Geçersiz sayfa: {text} (1, 2, ... veya son)") from None
    if page == 0:
        raise UserError("Sayfa 0 olamaz: 1 ilk sayfa, son veya -1 son sayfadır.")
    return page


def parse_box(text: str) -> tuple[float, float, float, float]:
    try:
        values = tuple(float(v.replace(" ", "")) for v in text.split(","))
    except ValueError:
        raise UserError(f"Geçersiz kutu: {text} (x0,y0,x1,y1 milimetre)") from None
    if len(values) != 4:
        raise UserError(f"Geçersiz kutu: {text} (4 sayı gerekli: x0,y0,x1,y1)")
    return values  # type: ignore[return-value]


def _edit(args: argparse.Namespace, change) -> int:
    store = template_store(args)
    template = load_template(store, args.id)
    try:
        message = change(template)
    except TemplateError as error:
        raise UserError(str(error)) from None
    store.save(template)
    print(message)
    return 0


def create(args, _jobs) -> int:
    try:
        template = template_store(args).create(args.ad)
    except TemplateError as error:
        raise UserError(str(error)) from None
    print(f"Şablon oluşturuldu: {template.name}")
    print(template.id)
    return 0


def list_templates(args, _jobs) -> int:
    def unreadable(template_id: str) -> None:
        import sys

        print(f"Okunamayan şablon: {template_id}", file=sys.stderr)

    for template in template_store(args).list(on_error=unreadable):
        print(f"{template.id}  {template.name}  {len(template.variables)} değişken")
    return 0


def show(args, _jobs) -> int:
    template = load_template(template_store(args), args.id)
    if args.json:
        print(json.dumps(template_to_dict(template), ensure_ascii=False, indent=1))
        return 0
    print(f"{template.name} ({template.id})")
    print(f"Dosya adı kalıbı: {template.filename_pattern or '(yok)'}")
    print(f"Güven eşiği: {template.min_confidence}")
    for variable in template.variables:
        mark = " (zorunlu)" if variable.required else ""
        print(f"- {variable.name}{mark}")
        if not variable.sections:
            print("    bölüm yok")
        for number, section in enumerate(variable.sections, start=1):
            box = ", ".join(f"{v:g}" for v in section.box_mm)
            example = f", örnek: {section.example}" if section.example else ""
            print(f"    {number}. sayfa {page_text(section.page)}, kutu {box} mm{example}")
    return 0


def delete(args, _jobs) -> int:
    try:
        template_store(args).delete(args.id)
    except KeyError:
        raise UserError(f"Şablon bulunamadı: {args.id}") from None
    print(f"Şablon silindi: {args.id}")
    return 0


def add_variable(args, _jobs) -> int:
    def change(t: Template) -> str:
        variable = t.add_variable(args.ad, required=args.zorunlu)
        return f"Değişken eklendi: {variable.name}"

    return _edit(args, change)


def remove_variable(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.remove_variable(args.ad)
        return f"Değişken silindi: {args.ad}"

    return _edit(args, change)


def rename_variable(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.rename_variable(args.eski, args.yeni)
        return f"Değişken yeniden adlandırıldı: {args.eski} → {args.yeni.strip()}"

    return _edit(args, change)


def set_required(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.set_required(args.ad, args.durum == "evet")
        return f"{args.ad}: {'zorunlu' if args.durum == 'evet' else 'isteğe bağlı'}"

    return _edit(args, change)


def add_section(args, _jobs) -> int:
    page, box = parse_page(args.sayfa), parse_box(args.kutu)

    def change(t: Template) -> str:
        example = Path(args.ornek).name if args.ornek else None
        t.add_section(args.ad, Section(page, box, example))
        count = len(t.variable(args.ad).sections)
        return f"{args.ad}: {count}. bölüm eklendi (sayfa {page_text(page)})"

    return _edit(args, change)


def remove_section(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.remove_section(args.ad, args.sira - 1)
        return f"{args.ad}: {args.sira}. bölüm silindi"

    return _edit(args, change)


def move_section(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.move_section(args.ad, args.sira - 1, args.yeni_sira - 1)
        return f"{args.ad}: {args.sira}. bölüm {args.yeni_sira}. sıraya taşındı"

    return _edit(args, change)


def set_pattern(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.set_pattern(args.kalip)
        return f"Dosya adı kalıbı: {args.kalip}"

    return _edit(args, change)


def set_threshold(args, _jobs) -> int:
    def change(t: Template) -> str:
        t.set_min_confidence(args.deger)
        return f"Güven eşiği: {args.deger}"

    return _edit(args, change)


def export(args, _jobs) -> int:
    store = template_store(args)
    load_template(store, args.id)
    store.export(args.id, args.dosya)
    print(f"Şablon dışa aktarıldı: {args.dosya}")
    return 0


def import_template(args, _jobs) -> int:
    try:
        template = template_store(args).import_file(args.dosya)
    except TemplateError as error:
        raise UserError(str(error)) from None
    print(f"Şablon içe aktarıldı: {template.name}")
    print(template.id)
    return 0


def describe_values(values: dict, names: dict[str, str], indent: str = "") -> list[str]:
    """Human-readable lines for read values: the chosen reading, then every variant."""
    lines = []
    for key, value in values.items():
        name = names.get(key, key)
        if value.flagged:
            hint = f' (öneri: "{value.suggestion}")' if value.suggestion else ""
            reason = "" if value.readings else " (bölüm yok: kutu çizilmemiş)"
            lines.append(f"{indent}{name}: OKUNAMADI{hint}{reason}")
        else:
            lines.append(
                f'{indent}{name}: "{value.value}" (bölüm {value.section + 1}, '
                f"güven %{round(value.confidence * 100)})"
            )
        for reading in value.readings:
            problem = f" [{reading.problem}]" if reading.problem else ""
            lines.append(
                f'{indent}    {reading.section + 1}. bölüm: "{reading.text}" '
                f"(güven %{round(reading.confidence * 100)}){problem}"
            )
    return lines


def test_template(args, _jobs) -> int:
    template = load_template(template_store(args), args.id)
    if not args.ornek.is_file():
        raise UserError(f"Dosya bulunamadı: {args.ornek}")
    engine = default_engine()
    reason = engine.available()
    if reason:
        raise UserError(reason)
    try:
        pdf = pdfium.PdfDocument(str(args.ornek))
        page_count = len(pdf)
        pdf.close()
    except pdfium.PdfiumError:
        raise UserError(f"PDF açılamadı: {args.ornek.name}") from None
    with PageRenderer(args.ornek) as pages:  # the PDF is opened once for every page
        values = read_document(template, page_count, pages.render, engine)
    print(f"{template.name}: {args.ornek.name} ({page_count} sayfa)")
    for line in describe_values(values, template.names_by_key()):
        print(line)
    return 0


def add_commands(commands: argparse._SubParsersAction) -> None:
    parser = commands.add_parser("sablon", help="şablon oluşturur ve düzenler")
    sub = parser.add_subparsers(dest="sablon_komutu", required=True, metavar="KOMUT")

    def command(name, handler, help_text, *arguments):
        p = sub.add_parser(name, help=help_text)
        for args, kwargs in arguments:
            p.add_argument(*args, **kwargs)
        p.set_defaults(handler=handler)
        return p

    tid = (("id",), {"help": "şablon numarası"})
    var = (("ad",), {"help": "değişken adı (boşluk varsa tırnak içinde)"})
    command("olustur", create, "yeni şablon oluşturur", (("ad",), {"help": "şablonun adı"}))
    command("listele", list_templates, "şablonları listeler")
    command("goster", show, "şablonu gösterir", tid, (("--json",), {"action": "store_true"}))
    command("sil", delete, "şablonu siler", tid)
    command(
        "degisken-ekle",
        add_variable,
        "değişken ekler",
        tid,
        var,
        (("--zorunlu",), {"action": "store_true", "help": "dosya adı için zorunlu"}),
    )
    command("degisken-sil", remove_variable, "değişkeni siler", tid, var)
    command(
        "degisken-adlandir",
        rename_variable,
        "değişkeni yeniden adlandırır",
        tid,
        (("eski",), {"help": "şimdiki ad"}),
        (("yeni",), {"help": "yeni ad"}),
    )
    command(
        "zorunlu",
        set_required,
        "değişkenin zorunlu olup olmadığını ayarlar",
        tid,
        var,
        (("durum",), {"choices": ["evet", "hayir"]}),
    )
    command(
        "bolum-ekle",
        add_section,
        "değişkene bölüm (kutu) ekler; sırayla denenir",
        tid,
        var,
        (("--sayfa",), {"required": True, "help": "1, 2, ... veya son"}),
        (("--kutu",), {"required": True, "help": "x0,y0,x1,y1 (mm, sol üst köşeden)"}),
        (("--ornek",), {"help": "kutunun çizildiği örnek belge"}),
    )
    command(
        "bolum-sil",
        remove_section,
        "bölümü siler",
        tid,
        var,
        (("sira",), {"type": int, "help": "bölüm sırası (1'den başlar)"}),
    )
    command(
        "bolum-tasi",
        move_section,
        "bölümün deneme sırasını değiştirir",
        tid,
        var,
        (("sira",), {"type": int}),
        (("yeni_sira",), {"type": int, "metavar": "YENI_SIRA"}),
    )
    command(
        "dosya-adi",
        set_pattern,
        "dosya adı kalıbını ayarlar, örn. {Kayıt No}_{Ünvan}",
        tid,
        (("kalip",), {"help": "kalıp"}),
    )
    command(
        "esik",
        set_threshold,
        "güven eşiğini ayarlar (0-1)",
        tid,
        (("deger",), {"type": float}),
    )
    command("disa-aktar", export, "şablonu dosyaya aktarır", tid, (("dosya",), {"type": Path}))
    command("ice-aktar", import_template, "şablonu dosyadan alır", (("dosya",), {"type": Path}))
    command(
        "test",
        test_template,
        "şablonu bir örnek belgede dener",
        tid,
        (("ornek",), {"type": Path, "metavar": "ORNEK.pdf"}),
    )
