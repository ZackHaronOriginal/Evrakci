import json

import pytest

from evrakci.pipeline.templates.model import (
    SavedFilter,
    Section,
    Template,
    TemplateError,
    pattern_names,
    template_from_dict,
    template_revision,
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


def test_rename_keeps_key_and_nfc_names():
    t = sample()
    key = t.variable("Ünvan").key
    t.rename_variable("Ünvan", "Firma")
    assert t.variable("Firma").key == key and len(key) >= 8
    t.add_variable("Ücret")  # "Ücret" typed as U + combining diaeresis
    assert t.variable("Ücret").name == "Ücret"
    t.set_pattern("{Ücret}")
    assert t.filename_pattern == "{Ücret}"


def test_old_files_without_keys_get_stable_keys():
    data = template_to_dict(sample())
    for variable in data["variables"]:
        variable.pop("key")
    assert [v.key for v in template_from_dict(data).variables] == [
        v.key for v in template_from_dict(data).variables
    ]


# I-07: saved filters
def with_filters() -> Template:
    t = sample()
    t.add_saved_filter("Boş sayfalar", "bos", {"ink": 0.005})
    t.add_saved_filter("Tek sayfalar", "tek")
    return t


def test_saved_filters_round_trip_with_and_without():
    t = with_filters()
    data = json.loads(json.dumps(template_to_dict(t), ensure_ascii=False))
    assert data["saved_filters"][0] == {"name": "Boş sayfalar", "kind": "bos",
                                        "params": {"ink": 0.005}}
    assert template_from_dict(data) == t
    assert template_from_dict(data).saved_filters == [
        SavedFilter("Boş sayfalar", "bos", {"ink": 0.005}), SavedFilter("Tek sayfalar", "tek")]
    plain = sample()
    assert template_from_dict(json.loads(json.dumps(template_to_dict(plain)))) == plain


def test_an_older_template_file_without_the_key_still_loads():
    data = template_to_dict(sample())
    del data["saved_filters"]
    loaded = template_from_dict(data)
    assert loaded.saved_filters == [] and loaded.name == "Örnek Şablon"
    assert data["version"] == 1


def test_bad_saved_filter_entries_are_refused():
    base = template_to_dict(sample())
    for bad in ("metin", [1], [{"kind": "tek"}], [{"name": "", "kind": "tek"}],
                [{"name": "A", "kind": ""}], [{"name": "A", "kind": 3}],
                [{"name": "A", "kind": "tek", "params": []}],
                [{"name": "A", "kind": "tek", "params": {"x": float("nan")}}],
                [{"name": "A\u0000", "kind": "tek"}],
                [{"name": "A", "kind": "tek"}, {"name": "A", "kind": "cift"}]):
        with pytest.raises(TemplateError):
            template_from_dict({**base, "saved_filters": bad})


def test_saved_filter_names_are_unique_nfc_and_at_most_twenty():
    t = sample()
    t.add_saved_filter("  Ça  ", "tek")
    with pytest.raises(TemplateError):
        t.add_saved_filter("Ça", "cift")
    t.add_saved_filter("é", "tek")
    assert t.saved_filters[-1].name == "é"
    with pytest.raises(TemplateError):
        t.add_saved_filter("é", "bos")
    for number in range(18):
        t.add_saved_filter(f"F{number}", "tek")
    assert len(t.saved_filters) == 20
    with pytest.raises(TemplateError):
        t.add_saved_filter("Yirmi bir", "tek")


def test_remove_and_rename_saved_filter():
    t = with_filters()
    t.rename_saved_filter("Tek sayfalar", "Tekler")
    assert [f.name for f in t.saved_filters] == ["Boş sayfalar", "Tekler"]
    with pytest.raises(TemplateError):
        t.rename_saved_filter("Tekler", "Boş sayfalar")
    t.rename_saved_filter("Tekler", "Tekler")  # the same name is no clash
    t.remove_saved_filter("Boş sayfalar")
    assert [f.name for f in t.saved_filters] == ["Tekler"]
    with pytest.raises(TemplateError):
        t.remove_saved_filter("Yok")


def test_template_revision_ignores_saved_filters():
    t = sample()
    before = template_revision(t)
    t.add_saved_filter("Boş sayfalar", "bos")
    assert template_revision(t) == before
