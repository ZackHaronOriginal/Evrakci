"""Plan 3 second fresh review (2026-11-09): every finding, red first."""

import json
import os

import pypdfium2 as pdfium
import pytest
from fakes import a4_300, make_pdf
from PIL import Image, ImageDraw

from evrakci.cli import main
from evrakci.pipeline.cuts import (
    compute_documents,
    current_read_error,
    current_values,
    document_template,
    record_read_error,
)
from evrakci.pipeline.export import plan_export
from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.render import mm_box_to_pixels, render_page
from evrakci.pipeline.review import needs_reading, set_value, store_reading
from evrakci.pipeline.templates.model import (
    Section,
    Template,
    TemplateError,
    pattern_names,
    template_from_dict,
    template_revision,
    template_to_dict,
    validate_name,
)
from evrakci.pipeline.templates.read import read_document
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue


def value(text, edited=False):
    return VariableValue(text, 0.9, 0, False, "", (), edited) if edited else VariableValue(
        text, 0.9, 0, False, "", ())


# --- 1: a file whose inner id differs from its file name ---------------------------------

def test_template_id_comes_from_the_file_name(tmp_path):
    store = TemplateStore(tmp_path)
    original = store.create("Deneme")
    copy = tmp_path / "abcdef.json"
    copy.write_text((tmp_path / f"{original.id}.json").read_text(encoding="utf-8"),
                    encoding="utf-8")
    template = store.load("abcdef")
    assert template.id == "abcdef"
    template.add_variable("X")
    store.save(template)
    assert store.load(original.id).variables == []  # the original was not overwritten
    assert [v.name for v in store.load("abcdef").variables] == ["X"]
    assert sorted(t.id for t in store.list()) == sorted([original.id, "abcdef"])


def test_a_hostile_inner_id_cannot_break_edits(tmp_path):
    store = TemplateStore(tmp_path)
    template = store.create("A")
    data = json.loads((tmp_path / f"{template.id}.json").read_text(encoding="utf-8"))
    data["id"] = "../kotu"
    (tmp_path / "bb.json").write_text(json.dumps(data), encoding="utf-8")
    loaded = store.load("bb")
    loaded.add_variable("X")
    store.save(loaded)
    assert not (tmp_path.parent / "kotu.json").exists()


# --- 2: a failed re-read keeps the values and the user's corrections -------------------

@pytest.fixture
def job_and_document(tmp_path):
    from evrakci.pipeline.store import JobStore

    scan = make_pdf(tmp_path / "t.pdf", [a4_300([]), a4_300([])], dpi=72)
    store = JobStore(tmp_path / "isler")
    job = store.create_job("İş", [scan])
    job.apply_template(job.ordered_page_ids(), "t1")
    return job, compute_documents(job)[0]


def test_failed_reread_keeps_the_users_correction(job_and_document):
    job, document = job_and_document
    store_reading(job, document, "t1", {"k": value("OKUNAN")})
    set_value(job, document, "k", "Elle düzeltildi")
    record_read_error(job, document, "t1", "Tesseract çalışmadı")
    assert current_values(job, document)["k"].value == "Elle düzeltildi"
    assert current_read_error(job, document) == "Tesseract çalışmadı"
    store_reading(job, document, "t1", {"k": value("YENİ")})
    kept = current_values(job, document)["k"]
    assert kept.value == "Elle düzeltildi" and kept.edited
    assert current_read_error(job, document) is None


def test_failed_read_of_a_changed_document_still_drops_old_values(job_and_document):
    job, document = job_and_document
    store_reading(job, document, "t1", {"k": value("OKUNAN")})
    record_read_error(job, document, "t2", "Şablon bulunamadı: t2")  # another template now
    job.apply_template(job.ordered_page_ids(), "t2")
    assert current_values(job, document) is None
    assert current_read_error(job, document) == "Şablon bulunamadı: t2"


# --- 3, 6: hostile or wrongly typed template files ----------------------------------------

def good_dict():
    template = Template("ab", "A")
    template.add_variable("X")
    template.add_section("X", Section(1, (1, 1, 5, 5), "örnek"))
    return template_to_dict(template)


def broken(change):
    data = good_dict()
    change(data)
    return data


BAD_FILES = {
    "page overflow": '{"format": "evrakci-sablon", "version": 1, "id": "a", "name": "A", '
                     '"variables": [{"name": "X", "sections": [{"page": 1e400, '
                     '"box_mm": [1, 1, 2, 2]}]}]}',
    "deep nesting": "[" * 100000 + "]" * 100000,
}


@pytest.mark.parametrize("content", BAD_FILES.values(), ids=BAD_FILES.keys())
def test_hostile_files_are_reported_not_crashing(tmp_path, content):
    store = TemplateStore(tmp_path)
    store.create("İyi")
    (tmp_path / "cc.json").write_text(content, encoding="utf-8")
    bad = []
    assert [t.name for t in store.list(on_error=bad.append)] == ["İyi"]
    assert bad == ["cc"]
    with pytest.raises(TemplateError):
        store.import_file(tmp_path / "cc.json")


def set_in(path, new):
    def change(data):
        target = data
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = new
    return change


WRONG_TYPES = {
    "required as text": (["variables", 0, "required"], "false"),
    "box as text": (["variables", 0, "sections", 0, "box_mm"], "1234"),
    "box with a bool": (["variables", 0, "sections", 0, "box_mm"], [True, 1, 5, 5]),
    "keywords as text": (["keywords"], "abc"),
    "page as bool": (["variables", 0, "sections", 0, "page"], True),
    "page as float": (["variables", 0, "sections", 0, "page"], 1.9),
    "example as dict": (["variables", 0, "sections", 0, "example"], {"x": [1]}),
    "name as number": (["name"], 12),
    "variable name as list": (["variables", 0, "name"], ["X"]),
    "version as bool": (["version"], True),
    "threshold as text": (["min_confidence"], "0.7"),
    "pattern as number": (["filename_pattern"], 5),
}


@pytest.mark.parametrize("path,new", WRONG_TYPES.values(), ids=WRONG_TYPES.keys())
def test_wrong_types_are_refused(path, new):
    with pytest.raises(TemplateError):
        template_from_dict(broken(set_in(path, new)))


def test_template_names_are_nfc(tmp_path):
    store = TemplateStore(tmp_path)
    first = store.create("Ünvan")  # composed
    second = store.create("Ünvan")  # decomposed: the same name
    assert first.name == "Ünvan" and second.name == "Ünvan (2)"


# --- 4, 5, 12: export -----------------------------------------------------------------------

def run_cli(tmp_path, *args):
    return main(["--kok", str(tmp_path / "isler"), "--sablon-kok", str(tmp_path / "s"), *args])


def test_cli_export_onto_an_existing_file_is_a_clear_error(tmp_path, capsys):
    template = TemplateStore(tmp_path / "s").create("A")
    target = tmp_path / "var.json"
    target.write_text("önemli", encoding="utf-8")
    assert run_cli(tmp_path, "sablon", "disa-aktar", template.id, str(target)) == 2
    assert "zaten var" in capsys.readouterr().err
    assert target.read_text(encoding="utf-8") == "önemli"


@pytest.mark.skipif(os.name == "nt", reason="POSIX file modes")
def test_exported_file_is_readable_by_others_per_umask(tmp_path):
    store = TemplateStore(tmp_path / "s")
    template = store.create("A")
    old = os.umask(0o022)
    try:
        store.export(template.id, tmp_path / "paylas.json")
    finally:
        os.umask(old)
    assert (tmp_path / "paylas.json").stat().st_mode & 0o777 == 0o644


def test_export_needs_an_existing_folder(tmp_path):
    store = TemplateStore(tmp_path / "s")
    template = store.create("A")
    with pytest.raises(TemplateError):
        store.export(template.id, tmp_path / "yok" / "a.json")
    assert not (tmp_path / "yok").exists()


# --- 7: values read with an older version of the template ---------------------------------

def test_revision_changes_with_what_is_read_but_not_with_the_name():
    template = template_from_dict(good_dict())
    first = template_revision(template)
    template.name = "Yeni ad"
    template.filename_pattern = "{X}"
    assert template_revision(template) == first
    template.add_section("X", Section(1, (2, 2, 6, 6)))
    assert template_revision(template) != first


def test_values_read_with_an_older_template_are_marked_and_reread(job_and_document):
    job, document = job_and_document
    template = template_from_dict(good_dict())
    template.id = "t1"
    template.set_pattern("{X}")
    key = template.variables[0].key
    store_reading(job, document, "t1", {key: value("Ali")}, template_revision(template))
    assert not needs_reading(job, document, template)
    assert not [c for c in plan_export(job, {"t1": template})[0].checks if "şablon" in c]
    template.add_section("X", Section(1, (2, 2, 6, 6)))
    assert needs_reading(job, document, template)
    assert "şablon değişti; yeniden okunmalı" in plan_export(job, {"t1": template})[0].checks


def test_a_variable_added_after_reading_is_marked(job_and_document):
    job, document = job_and_document
    template = template_from_dict(good_dict())
    template.id = "t1"
    key = template.variables[0].key
    store_reading(job, document, "t1", {key: value("Ali")})  # an old job: no revision
    template.add_variable("Yeni")
    assert needs_reading(job, document, template)
    assert "okunmadı: Yeni" in plan_export(job, {"t1": template})[0].checks


# --- 8: a damaged page does not stop reading ---------------------------------------------------

class FakeEngine:
    name = "sahte"

    def available(self):
        return None

    def read_region(self, image):
        return Reading("x", 0.99)


def test_a_damaged_page_is_recorded_not_crashing(tmp_path, monkeypatch, capsys):
    import evrakci.cli.jobs as jobs

    template = TemplateStore(tmp_path / "s").create("A")
    scan = make_pdf(tmp_path / "t.pdf", [a4_300([])], dpi=72)
    assert run_cli(tmp_path, "is", "olustur", "İş", str(scan)) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]
    run_cli(tmp_path, "is", "sablon-uygula", job_id, "1-1", template.id)
    monkeypatch.setattr(jobs, "default_engine", FakeEngine)

    def damaged(*args, **kwargs):
        raise pdfium.PdfiumError("Failed to load page.")

    monkeypatch.setattr(jobs, "read_document", damaged)
    assert run_cli(tmp_path, "is", "oku", job_id) == 0
    assert "Failed to load page" in capsys.readouterr().out


def test_template_test_reports_a_damaged_page(tmp_path, monkeypatch, capsys):
    import evrakci.cli.templates as templates

    template = TemplateStore(tmp_path / "s").create("A")
    example = make_pdf(tmp_path / "ornek.pdf", [a4_300([])], dpi=72)
    monkeypatch.setattr(templates, "default_engine", FakeEngine)

    def damaged(*args, **kwargs):
        raise pdfium.PdfiumError("Failed to load page.")

    monkeypatch.setattr(templates, "read_document", damaged)
    assert run_cli(tmp_path, "sablon", "test", template.id, str(example)) == 2
    assert "okunamadı" in capsys.readouterr().err


# --- 9, 10: tiny boxes and boxes past the top-left edge -------------------------------------

def test_a_thin_box_inside_the_page_is_at_least_one_pixel():
    box = mm_box_to_pixels((10, 10, 10.05, 20), (2480, 3508))
    assert box is not None and box[2] - box[0] >= 1


def test_a_box_past_the_top_left_edge_is_clipped_like_the_other_edges():
    assert Section(1, (-1, -2, 10, 20)).box_mm == (0, 0, 10, 20)
    with pytest.raises(TemplateError):
        Section(1, (-5, 0, -1, 10))  # wholly outside


# --- 11: names and patterns ------------------------------------------------------------------

@pytest.mark.parametrize("name", ["a\nb", "a\tb", "ab", "x"])
def test_control_and_private_characters_are_refused_in_names(name):
    with pytest.raises(TemplateError):
        validate_name(name)


def test_pattern_problems_are_explained():
    template = Template("ab", "A")
    template.add_variable("A")
    with pytest.raises(TemplateError, match="boş"):
        template.set_pattern("{}")
    with pytest.raises(TemplateError, match="boşluk"):
        template.set_pattern("{ A }")
    for literal in ("5{A}", "x{A}", "a\n{A}"):
        with pytest.raises(TemplateError):
            template.set_pattern(literal.replace("5", ""))
    assert pattern_names("{A}-{A}") == ["A", "A"]


# --- 13, 14: documents whose first page has no template; removing a template ----------------

def test_first_page_without_template_says_so(job_and_document):
    job, _ = job_and_document
    pages = job.ordered_page_ids()
    job.templates.clear()
    job.apply_template(pages[1:], "t1")
    item = plan_export(job, {"t1": template_from_dict(good_dict())})[0]
    assert "karışık şablon (ilk sayfada şablon yok)" in item.checks


def test_removing_a_template_from_pages(tmp_path, capsys, job_and_document):
    job, document = job_and_document
    job.remove_template(job.ordered_page_ids())
    assert document_template(job, compute_documents(job)[0]) == (None, False)


def test_cli_removes_a_template_from_pages(tmp_path, capsys):
    template = TemplateStore(tmp_path / "s").create("A")
    scan = make_pdf(tmp_path / "t.pdf", [a4_300([]), a4_300([])], dpi=72)
    run_cli(tmp_path, "is", "olustur", "İş", str(scan))
    job_id = capsys.readouterr().out.strip().splitlines()[-1]
    run_cli(tmp_path, "is", "sablon-uygula", job_id, "1-2", template.id)
    assert run_cli(tmp_path, "is", "sablon-kaldir", job_id, "2-2") == 0
    run_cli(tmp_path, "is", "goster", job_id, "--json")
    out = capsys.readouterr().out
    data = json.loads(out[out.index("{"):])
    from evrakci.pipeline.job import job_from_dict

    job = job_from_dict(data["job"])
    first, second = job.ordered_page_ids()
    from evrakci.pipeline.cuts import _template_of

    assert _template_of(job) == {first: template.id}


# --- test gaps: rotation direction, partly outside boxes, last applied wins ------------------

def test_user_rotation_turns_clockwise(tmp_path):
    page = Image.new("L", (600, 800), 255)
    ImageDraw.Draw(page).rectangle((0, 0, 99, 99), fill=0)  # a mark at the top-left
    pdf = make_pdf(tmp_path / "r.pdf", [page], dpi=72)
    turned = render_page(pdf, 0, 90, dpi=72)
    assert turned.size == (800, 600)
    # Clockwise: the top-left corner moves to the top-right.
    assert turned.getpixel((790, 10)) < 128 and turned.getpixel((10, 10)) > 128


class SizeEngine:
    name = "boyut"

    def __init__(self):
        self.sizes = []

    def available(self):
        return None

    def read_region(self, image):
        self.sizes.append(image.size)
        return Reading("metin", 0.99)


def test_a_box_partly_outside_a_smaller_page_is_read_clipped():
    template = Template("ab", "A")
    template.add_variable("X")
    template.add_section("X", Section(1, (200, 270, 215, 290)))  # past Letter's 279 mm height
    letter = Image.new("L", (2550, 3300), 255)
    engine = SizeEngine()
    values = read_document(template, 1, lambda i: letter, engine)
    assert values[template.variables[0].key].value == "metin"
    width, height = engine.sizes[0]
    assert height == 3300 - round(270 / 25.4 * 300)
