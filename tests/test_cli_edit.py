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
