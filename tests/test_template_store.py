import pytest

from evrakci.pipeline.templates.model import Section, TemplateError
from evrakci.pipeline.templates.store import TemplateStore


def test_create_save_load_list(tmp_path):
    store = TemplateStore(tmp_path / "Şablonlar")
    b = store.create("Çiftçi Kaydı")
    a = store.create("Ana Sözleşme")
    b.add_variable("Ünvan")
    b.add_section("Ünvan", Section(1, (1.0, 2.0, 3.0, 4.0)))
    store.save(b)
    assert store.load(b.id) == b
    assert [t.name for t in store.list()] == ["Ana Sözleşme", "Çiftçi Kaydı"]
    store.delete(a.id)
    with pytest.raises(KeyError):
        store.load(a.id)


def test_export_import_keeps_turkish(tmp_path):
    store = TemplateStore(tmp_path / "s")
    t = store.create("Örnek")
    t.add_variable("Kayıt No")
    store.save(t)
    path = tmp_path / "dışa.json"
    store.export(t.id, path)
    assert "Kayıt No" in path.read_bytes().decode("utf-8")
    other = TemplateStore(tmp_path / "baska")
    imported = other.import_file(path)
    assert imported.name == "Örnek" and imported.variables[0].name == "Kayıt No"


def test_import_clash_gets_new_id_and_name(tmp_path):
    store = TemplateStore(tmp_path / "s")
    t = store.create("Örnek")
    path = tmp_path / "e.json"
    store.export(t.id, path)
    again = store.import_file(path)
    assert again.id != t.id and again.name == "Örnek (2)"
    assert len(store.list()) == 2


def test_corrupt_file_reported(tmp_path):
    store = TemplateStore(tmp_path / "s")
    good = store.create("İyi")
    bad = store.create("Kötü")
    (tmp_path / "s" / f"{bad.id}.json").write_text("{", encoding="utf-8")
    with pytest.raises(TemplateError, match="Şablon dosyası okunamadı"):
        store.load(bad.id)
    seen = []
    assert [t.id for t in store.list(on_error=seen.append)] == [good.id] and seen == [bad.id]
    with pytest.raises(TemplateError):
        store.import_file(tmp_path / "s" / f"{bad.id}.json")


def test_import_never_trusts_file_id(tmp_path):
    import json

    store = TemplateStore(tmp_path / "s")
    t = store.create("Örnek")
    path = tmp_path / "e.json"
    store.export(t.id, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["id"] = "../kacak"
    path.write_text(json.dumps(data), encoding="utf-8")
    imported = store.import_file(path)
    assert imported.id != "../kacak" and len(imported.id) == 10
    assert not (tmp_path / "kacak.json").exists()


def test_import_checks_like_the_editor(tmp_path):
    import json

    store = TemplateStore(tmp_path / "s")
    t = store.create("Örnek")
    t.add_variable("Ünvan")
    store.save(t)
    path = tmp_path / "e.json"
    store.export(t.id, path)
    base = json.loads(path.read_text(encoding="utf-8"))
    for change in (
        {"min_confidence": 0},
        {"min_confidence": 5.0},
        {"min_confidence": float("nan")},
        {"filename_pattern": "{Yok}"},
    ):
        path.write_text(json.dumps({**base, **change}), encoding="utf-8")
        with pytest.raises(TemplateError):
            store.import_file(path)


def test_bom_accepted(tmp_path):
    store = TemplateStore(tmp_path / "s")
    t = store.create("Örnek")
    path = tmp_path / "e.json"
    store.export(t.id, path)
    path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
    assert store.import_file(path).name == "Örnek (2)"
