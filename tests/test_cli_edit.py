import json

from fakes import empty_page, make_pdf, qr_page, text_page

from evrakci.cli import main


def setup_job(tmp_path, capsys, pages):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", pages)
    assert main(["--kok", str(root), "is", "olustur", "Test", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]

    def run(*args):
        return main(["--kok", str(root), *args])

    return run, job_id


def test_filter_cut_and_export(tmp_path, capsys):
    pages = [text_page()] * 4 + [qr_page()] + [text_page()] * 3
    run, job_id = setup_job(tmp_path, capsys, pages)
    assert run("is", "filtre", job_id, "1-4", "2") == 0
    assert run("is", "kes", job_id, "8") == 0
    assert run("is", "disa-aktar", job_id, "--cikti", str(tmp_path / "out")) == 0
    out = capsys.readouterr().out
    assert "belge_001.pdf: sayfa 1, 2" in out and "belge_004.pdf: sayfa 8" in out
    assert "4 belge yazıldı." in out
    assert len(list((tmp_path / "out").glob("*.pdf"))) == 4


def test_drop_empty_and_page_edits(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page(), empty_page(), text_page()])
    assert run("is", "bos-sayfalar", job_id, "ac") == 0
    assert run("is", "sayfa", job_id, "1", "--sil") == 0
    capsys.readouterr()
    run("is", "goster", job_id)
    assert "1. belge: sayfa 3" in capsys.readouterr().out
    assert run("is", "sayfa", job_id, "2", "--bos-geri-al") == 0
    capsys.readouterr()
    run("is", "goster", job_id)
    assert "1. belge: sayfa 2, 3" in capsys.readouterr().out


def test_user_errors(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page(), text_page()])
    assert run("is", "filtre", job_id, "abc", "2") == 2
    assert run("is", "kes", job_id, "9") == 2
    assert run("is", "kes", job_id, "2", "--kaldir") == 2
    err = capsys.readouterr().err
    assert "Geçersiz aralık: abc" in err and "Sayfa yok: 9" in err
    assert "Bu sayfada kesim yok: 2" in err


def test_missing_file_is_turkish_error(tmp_path, capsys):
    code = main(["--kok", str(tmp_path / "k"), "is", "olustur", "x", str(tmp_path / "yok.pdf")])
    assert code == 2
    assert "Dosya bulunamadı: yok.pdf" in capsys.readouterr().err


def test_export_twice_to_same_folder(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page()])
    out = str(tmp_path / "out")
    assert run("is", "disa-aktar", job_id, "--cikti", out) == 0
    assert run("is", "disa-aktar", job_id, "--cikti", out) == 2
    assert "boş bir klasör" in capsys.readouterr().err


def test_batch_move_and_remove_commands(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page(), text_page()])
    one = make_pdf(tmp_path / "one.pdf", [text_page()])
    run("is", "ekle", job_id, str(one))
    assert run("is", "parti-tasi", job_id, "b2", "1") == 0
    capsys.readouterr()
    run("is", "goster", job_id, "--json")
    batches = json.loads(capsys.readouterr().out)["job"]["batches"]
    assert [b["id"] for b in batches] == ["b2", "b1"]
    assert run("is", "parti-sil", job_id, "b1") == 0
    capsys.readouterr()
    run("is", "listele")
    assert "1 sayfa" in capsys.readouterr().out
    assert run("is", "parti-sil", job_id, "b9") == 2
    assert "Parti bulunamadı: b9" in capsys.readouterr().err


def test_corrupt_job_listed_as_unreadable(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page()])
    (tmp_path / "kok" / job_id / "job.json").write_text("{", encoding="utf-8")
    assert run("is", "listele") == 0
    assert f"Okunamayan iş: {job_id}" in capsys.readouterr().err
    assert run("is", "goster", job_id) == 2
    assert "İş dosyası okunamadı" in capsys.readouterr().err


def test_single_page_range(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page(), text_page()])
    assert run("is", "filtre", job_id, "2", "1") == 0
    assert "sayfa 2-2" in capsys.readouterr().out


def test_cut_where_qr_already_cuts(tmp_path, capsys):
    run, job_id = setup_job(tmp_path, capsys, [text_page(), qr_page(), text_page()])
    assert run("is", "kes", job_id, "2") == 2
    assert "Bu sayfada zaten kesim var: 2" in capsys.readouterr().err


def test_error_starts_on_its_own_line(tmp_path, capsys, monkeypatch):
    import evrakci.pipeline.store as store_module
    from evrakci.pipeline.analyze import BatchError

    def half_done(path, progress=None):
        progress(1, 2)
        raise BatchError("Sayfa 2 okunamadı: t.pdf")

    monkeypatch.setattr(store_module, "analyze_pdf", half_done)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page()])
    assert main(["--kok", str(tmp_path / "k"), "is", "olustur", "x", str(pdf)]) == 2
    assert "\nSayfa 2 okunamadı: t.pdf" in capsys.readouterr().err
