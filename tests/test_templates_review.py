"""Plan 3 fresh-review findings."""

import json
import math

import pytest

from evrakci.pipeline.templates.model import Section, TemplateError, template_from_dict
from evrakci.pipeline.templates.store import TemplateStore


@pytest.mark.parametrize("content", ["[]", '"x"', "3", "null"])
def test_a_non_object_template_file_is_reported_not_crashing(tmp_path, content):
    store = TemplateStore(tmp_path)
    store.create("İyi")
    (tmp_path / "bozuk00000.json").write_text(content, encoding="utf-8")
    bad = []
    assert [t.name for t in store.list(on_error=bad.append)] == ["İyi"]
    assert bad == ["bozuk00000"]
    with pytest.raises(TemplateError):
        template_from_dict(json.loads(content))


@pytest.mark.parametrize("box", [(0, 0, math.inf, 5), (0, 0, 5, math.nan), (-math.inf, 0, 1, 1)])
def test_boxes_must_be_finite(box):
    with pytest.raises(TemplateError):
        Section(1, box)


def test_infinity_in_an_imported_file_is_refused(tmp_path):
    store = TemplateStore(tmp_path / "s")
    template = store.create("A")
    template.add_variable("X")
    template.add_section("X", Section(1, (1, 1, 2, 2)))
    store.save(template)
    path = tmp_path / "out.json"
    store.export(template.id, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["variables"][0]["sections"][0]["box_mm"][2] = math.inf
    path.write_text(json.dumps(data), encoding="utf-8")  # json writes it as Infinity
    assert "Infinity" in path.read_text(encoding="utf-8")
    with pytest.raises(TemplateError):
        store.import_file(path)


def test_new_templates_get_unique_names_like_imports(tmp_path):
    store = TemplateStore(tmp_path)
    store.create("Rapor")
    assert store.create("Rapor").name == "Rapor (2)"


def test_export_refuses_to_overwrite_a_file(tmp_path):
    store = TemplateStore(tmp_path / "s")
    template = store.create("A")
    target = tmp_path / "var.json"
    target.write_text("önemli", encoding="utf-8")
    with pytest.raises(TemplateError):
        store.export(template.id, target)
    assert target.read_text(encoding="utf-8") == "önemli"


def test_template_ids_never_reach_outside_the_folder(tmp_path):
    outside = TemplateStore(tmp_path)
    planted = outside.create("Dışarıda")
    (tmp_path / f"{planted.id}.json").rename(tmp_path / "x.json")
    store = TemplateStore(tmp_path / "s")
    (tmp_path / "s").mkdir()
    with pytest.raises(KeyError):
        store.load("../x")


def test_variable_without_sections_says_so():
    from evrakci.cli.templates import describe_values
    from evrakci.pipeline.templates.model import Template
    from evrakci.pipeline.templates.read import read_document

    template = Template("abc", "A")
    template.add_variable("Boş")

    class Engine:
        def read_region(self, image):
            raise AssertionError("no box, no reading")

    values = read_document(template, 1, lambda i: None, Engine())
    text = "\n".join(describe_values(values, template.names_by_key()))
    assert "bölüm yok" in text


def test_example_pdf_is_opened_once_for_all_pages(tmp_path, monkeypatch):
    from fakes import make_pdf, text_page

    import evrakci.pipeline.render as render

    pdf = make_pdf(tmp_path / "e.pdf", [text_page(), text_page(), text_page()])
    opened = []
    real = render.pdfium.PdfDocument
    monkeypatch.setattr(render.pdfium, "PdfDocument",
                        lambda *a, **k: opened.append(1) or real(*a, **k))
    with render.PageRenderer(pdf) as pages:
        sizes = [pages.render(i, dpi=20).size for i in range(3)]
    assert len(opened) == 1 and len(set(sizes)) == 1
