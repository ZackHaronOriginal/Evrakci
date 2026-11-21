import json

import pikepdf
from fakes import make_pdf, qr_page, text_page

from evrakci.cli import main


def created_id(capsys) -> str:
    return capsys.readouterr().out.strip().splitlines()[-1]


def test_create_show_list_delete(tmp_path, capsys):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()] * 2 + [qr_page()] + [text_page()] * 3)
    assert main(["--kok", str(root), "is", "olustur", "Seçim", str(pdf)]) == 0
    job_id = created_id(capsys)
    assert main(["--kok", str(root), "is", "goster", job_id]) == 0
    out = capsys.readouterr().out
    assert "1. belge: sayfa 1, 2" in out and "2. belge: sayfa 4, 5, 6" in out
    assert "QR sayfaları: 3" in out
    assert main(["--kok", str(root), "is", "goster", job_id, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["documents"][1]["positions"] == [4, 5, 6]
    assert main(["--kok", str(root), "is", "sil", job_id]) == 0
    capsys.readouterr()
    assert main(["--kok", str(root), "is", "goster", job_id]) == 2
    assert "İş bulunamadı" in capsys.readouterr().err


def test_add_batch_and_list(tmp_path, capsys):
    root = tmp_path / "kok"
    two = make_pdf(tmp_path / "two.pdf", [text_page(), text_page()])
    one = make_pdf(tmp_path / "one.pdf", [text_page()])
    assert main(["--kok", str(root), "is", "olustur", "Liste", str(two)]) == 0
    job_id = created_id(capsys)
    assert main(["--kok", str(root), "is", "ekle", job_id, str(one)]) == 0
    assert "b2 eklendi (1 sayfa)" in capsys.readouterr().out
    assert main(["--kok", str(root), "is", "listele"]) == 0
    out = capsys.readouterr().out
    assert job_id in out and "Liste" in out and "3 sayfa" in out


def test_unreadable_pdf(tmp_path, capsys):
    bad = tmp_path / "bozuk.pdf"
    bad.write_bytes(b"nope")
    assert main(["--kok", str(tmp_path / "k"), "is", "olustur", "x", str(bad)]) == 2
    assert "PDF açılamadı" in capsys.readouterr().err


def test_separator_command(tmp_path):
    assert main(["ayirac", str(tmp_path / "a.pdf"), "--adet", "2"]) == 0
    with pikepdf.open(tmp_path / "a.pdf") as pdf:
        assert len(pdf.pages) == 4


def test_cli_export_counts_a_pdfa_failure_like_the_window(tmp_path, capsys, monkeypatch):
    import shutil

    from evrakci.cli import jobs as cli_jobs
    from evrakci.pipeline.ocr.textlayer import TextLayerResult
    from evrakci.pipeline.store import JobStore
    from evrakci.ui.disa_aktar_model import file_rows

    class Ok:
        def available(self):
            return None

    def not_pdfa(src, dst, tessdata=None, **kwargs):
        shutil.copy(src, dst)
        return TextLayerResult(dst, False, "PDF/A doğrulanamadı")

    monkeypatch.setattr(cli_jobs, "add_text_layer", not_pdfa)
    monkeypatch.setattr(cli_jobs, "default_engine", lambda: Ok())
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    assert main(["--kok", str(root), "is", "olustur", "Seçim", str(pdf)]) == 0
    job_id = created_id(capsys)
    assert main(["--kok", str(root), "is", "disa-aktar", job_id, "--cikti",
                 str(tmp_path / "out")]) == 0
    out = capsys.readouterr().out
    assert "kontrol:" not in out and "PDF/A doğrulanamadı" in out
    from evrakci.pipeline.export import plan_export

    job = JobStore(root).load(job_id)
    window_count = sum(r.state == "kontrol" for r in file_rows(job, plan_export(job, {})))
    assert f"{window_count} belge kontrol gerektiriyor" in out


def test_cli_export_names_the_check_sheet_only_when_something_needs_a_check(
        tmp_path, capsys, monkeypatch):
    import openpyxl

    from evrakci.pipeline import export as export_module

    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), qr_page(), text_page()])
    assert main(["--kok", str(root), "is", "olustur", "Seçim", str(pdf)]) == 0
    job_id = created_id(capsys)
    line = "Kontrol listesi: index.xlsx, sayfa 'Kontrol gerekenler'."
    assert main(["--kok", str(root), "is", "disa-aktar", job_id, "--cikti",
                 str(tmp_path / "temiz"), "--metin-katmani-yok"]) == 0
    assert line not in capsys.readouterr().out

    real = export_module.plan_export

    def flagged(*args, **kwargs):
        items = real(*args, **kwargs)
        items[0].checks.append("değerler okunmadı")
        return items

    monkeypatch.setattr("evrakci.pipeline.exporting.plan_export", flagged)
    assert main(["--kok", str(root), "is", "disa-aktar", job_id, "--cikti",
                 str(tmp_path / "isaretli"), "--metin-katmani-yok"]) == 0
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert "1 belge kontrol gerektiriyor" in out and lines[-1] == line
    sheet = openpyxl.load_workbook(tmp_path / "isaretli" / "index.xlsx")["Kontrol gerekenler"]
    assert [c.value for c in sheet[2]][3] == "değerler okunmadı"
