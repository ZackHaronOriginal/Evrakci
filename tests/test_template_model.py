import json

import pytest

from evrakci.pipeline.templates.model import (
    Section,
    Template,
    TemplateError,
    pattern_names,
    template_from_dict,
    template_to_dict,
    validate_name,
)


def sample() -> Template:
    t = Template(id="t1", name="Örnek Şablon")
    t.add_variable("Ünvan", required=True)
    t.add_variable("Kayıt No")
    t.add_section("Ünvan", Section(1, (20.0, 30.0, 150.0, 40.0), "örnek1.pdf"))
    t.add_section("Ünvan", Section(1, (20.0, 40.0, 150.0, 50.0)))
    t.add_section("Kayıt No", Section(-1, (10.0, 10.0, 60.0, 18.0)))
    t.set_pattern("{Kayıt No}_{Ünvan}")
    return t


def test_turkish_names_round_trip():
    t = sample()
    text = json.dumps(template_to_dict(t), ensure_ascii=False)
    assert "Ünvan" in text and template_from_dict(json.loads(text)) == t


def test_pattern_only_known_variables():
    with pytest.raises(TemplateError, match="Yok"):
        sample().set_pattern("{Yok}_{Ünvan}")
    assert pattern_names("A{Kayıt No}-{Ünvan}.") == ["Kayıt No", "Ünvan"]
    with pytest.raises(TemplateError):
        pattern_names("{Ünvan")


def test_rename_updates_pattern():
    t = sample()
    t.rename_variable("Ünvan", "Firma")
    assert t.filename_pattern == "{Kayıt No}_{Firma}" and t.variable("Firma").required
    with pytest.raises(TemplateError):
        t.rename_variable("Firma", "Kayıt No")  # already exists


def test_remove_variable_strips_from_pattern():
    t = sample()
    t.remove_variable("Kayıt No")
    assert t.filename_pattern == "_{Ünvan}" and [v.name for v in t.variables] == ["Ünvan"]


def test_bad_names():
    for bad in ("", "   ", "a{b", "c}d"):
        with pytest.raises(TemplateError):
            validate_name(bad)
    assert validate_name("  Kayıt No ") == "Kayıt No"
    with pytest.raises(TemplateError):
        sample().add_variable("Ünvan")


def test_bad_box_and_page():
    with pytest.raises(TemplateError):
        Section(1, (50.0, 10.0, 20.0, 30.0))
    with pytest.raises(TemplateError):
        Section(0, (1.0, 1.0, 2.0, 2.0))


def test_section_order_ops():
    t = sample()
    t.move_section("Ünvan", 1, 0)
    assert t.variable("Ünvan").sections[0].box_mm == (20.0, 40.0, 150.0, 50.0)
    t.remove_section("Ünvan", 1)
    assert len(t.variable("Ünvan").sections) == 1
    with pytest.raises(TemplateError):
        t.remove_section("Ünvan", 5)


def test_threshold_and_unknown_format():
    t = sample()
    t.set_min_confidence(0.5)
    assert t.min_confidence == 0.5
    with pytest.raises(TemplateError):
        t.set_min_confidence(0)
    with pytest.raises(TemplateError):
        template_from_dict({"format": "baska", "version": 1})
