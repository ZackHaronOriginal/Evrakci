import json

from evrakci.cli import main


def runner(tmp_path):
    root = str(tmp_path / "sablonlar")

    def run(*args):
        return main(["--sablon-kok", root, "sablon", *args])

    return run


def new_template(run, capsys, name="Seçim Yetki Belgesi"):
    assert run("olustur", name) == 0
    return capsys.readouterr().out.strip().splitlines()[-1]


def test_create_edit_show(tmp_path, capsys):
    run = runner(tmp_path)
    tid = new_template(run, capsys)
    assert run("degisken-ekle", tid, "Firma Ünvanı", "--zorunlu") == 0
    assert run("degisken-ekle", tid, "Kayıt No") == 0
    assert run("bolum-ekle", tid, "Firma Ünvanı", "--sayfa", "1", "--kutu", "20,30,150,40") == 0
    assert (
        run(
            "bolum-ekle",
            tid,
            "Firma Ünvanı",
            "--sayfa",
            "1",
            "--kutu",
            "20,40,150,55",
            "--ornek",
            "uzun-unvan.pdf",
        )
        == 0
    )
    assert run("bolum-ekle", tid, "Kayıt No", "--sayfa", "son", "--kutu", "10,10,60,18") == 0
    assert run("bolum-tasi", tid, "Firma Ünvanı", "2", "1") == 0
    assert run("dosya-adi", tid, "{Kayıt No}_{Firma Ünvanı}") == 0
    assert run("esik", tid, "0.6") == 0
    capsys.readouterr()
    assert run("goster", tid, "--json") == 0
    data = json.loads(capsys.readouterr().out)
    unvan = data["variables"][0]
    assert unvan["name"] == "Firma Ünvanı" and unvan["required"] is True
    assert unvan["sections"][0]["example"] == "uzun-unvan.pdf"
    assert data["variables"][1]["sections"][0]["page"] == -1
    assert data["filename_pattern"] == "{Kayıt No}_{Firma Ünvanı}" and data["min_confidence"] == 0.6
    assert run("goster", tid) == 0
    out = capsys.readouterr().out
    assert "Firma Ünvanı (zorunlu)" in out and "sayfa son" in out
    assert run("listele") == 0
    assert "Seçim Yetki Belgesi  2 değişken" in capsys.readouterr().out


def test_rename_variable_updates_pattern(tmp_path, capsys):
    run = runner(tmp_path)
    tid = new_template(run, capsys)
    run("degisken-ekle", tid, "Ünvan")
    run("dosya-adi", tid, "{Ünvan}")
    assert run("degisken-adlandir", tid, "Ünvan", "Firma") == 0
    capsys.readouterr()
    run("goster", tid, "--json")
    assert json.loads(capsys.readouterr().out)["filename_pattern"] == "{Firma}"


def test_errors(tmp_path, capsys):
    run = runner(tmp_path)
    tid = new_template(run, capsys)
    run("degisken-ekle", tid, "Ünvan")
    assert run("bolum-ekle", tid, "Ünvan", "--sayfa", "1", "--kutu", "50,10,20,30") == 2
    assert run("bolum-ekle", tid, "Ünvan", "--sayfa", "1", "--kutu", "1,2,3") == 2
    assert run("bolum-ekle", tid, "Yok", "--sayfa", "1", "--kutu", "1,2,3,4") == 2
    assert run("dosya-adi", tid, "{Yok}") == 2
    assert run("goster", "bilinmeyen") == 2
    err = capsys.readouterr().err
    assert "Geçersiz kutu" in err and "Değişken yok: Yok" in err
    assert "Şablon bulunamadı: bilinmeyen" in err


def test_export_import_roundtrip(tmp_path, capsys):
    run = runner(tmp_path)
    tid = new_template(run, capsys)
    run("degisken-ekle", tid, "Ünvan")
    path = tmp_path / "paylas.json"
    assert run("disa-aktar", tid, str(path)) == 0
    assert run("ice-aktar", str(path)) == 0
    new_id = capsys.readouterr().out.strip().splitlines()[-1]
    assert new_id != tid
    assert run("sil", tid) == 0 and run("goster", new_id) == 0


def test_saved_filters_add_list_remove(tmp_path, capsys):
    run = runner(tmp_path)
    tid = new_template(run, capsys)
    assert run("filtreler", tid) == 0
    assert "Kayıtlı filtreler: (yok)" in capsys.readouterr().out
    assert run("filtre-ekle", tid, "Boş sayfalar", "bos", "--ayar", "ink=0.005") == 0
    assert "Kayıtlı filtre eklendi: Boş sayfalar" in capsys.readouterr().out
    assert run("filtre-ekle", tid, "Tek sayfalar", "tek") == 0
    capsys.readouterr()
    assert run("filtreler", tid) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == ['Boş sayfalar  bos  {"ink": 0.005}', "Tek sayfalar  tek  {}"]
    assert run("filtre-ekle", tid, "Tek sayfalar", "cift") == 2  # the name is taken
    assert "Bu adla bir filtre zaten var" in capsys.readouterr().err
    assert run("filtre-ekle", tid, "X", "yok-boyle-bir-olcut") == 2
    capsys.readouterr()
    assert run("filtre-ekle", tid, "X", "tek", "--ayar", "bozuk") == 2
    assert "Geçersiz ayar" in capsys.readouterr().err
    assert run("filtre-sil", tid, "Boş sayfalar") == 0
    assert "Kayıtlı filtre silindi" in capsys.readouterr().out
    assert run("filtre-sil", tid, "Boş sayfalar") == 2
    assert "Filtre yok" in capsys.readouterr().err
    assert run("filtreler", tid) == 0
    assert capsys.readouterr().out.splitlines() == ["Tek sayfalar  tek  {}"]


def test_existing_template_commands_print_what_they_printed(tmp_path, capsys):
    run = runner(tmp_path)
    tid = new_template(run, capsys, "Eski")
    assert run("degisken-ekle", tid, "Kayıt No") == 0
    capsys.readouterr()
    assert run("goster", tid) == 0
    assert capsys.readouterr().out.splitlines() == [
        f"Eski ({tid})", "Dosya adı kalıbı: (yok)", "Güven eşiği: 0.7", "- Kayıt No",
        "    bölüm yok"]
    assert run("listele") == 0
    assert capsys.readouterr().out.strip() == f"{tid}  Eski  1 değişken"
