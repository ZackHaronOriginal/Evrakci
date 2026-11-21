from datetime import datetime

import openpyxl
from fakes import job_from_kinds

from evrakci.pipeline.cuts import Document
from evrakci.pipeline.export import ExportItem
from evrakci.pipeline.index import write_index


def items():
    job = job_from_kinds({"a": "pppp"})
    one = ExportItem(
        1,
        Document(("a/0", "a/1")),
        "101_Örnek",
        "Deneme",
        {"Kayıt No": "101", "Ünvan": "Örnek Şti."},
        [],
        True,
    )
    two = ExportItem(
        2,
        Document(("a/2",)),
        "belge_002",
        "Deneme",
        {"Kayıt No": "", "Ünvan": "=1+1", "Not": "@x"},
        ["zorunlu değer eksik: Kayıt No"],
        False,
        pdfa_note="PDF/A doğrulanamadı",
    )
    three = ExportItem(3, Document(("a/3",)), "belge_003", None, {}, [], True)
    return job, [one, two, three]


def test_columns_and_rows(tmp_path):
    job, rows = items()
    path = tmp_path / "index.xlsx"
    write_index(rows, job, path)
    sheet = openpyxl.load_workbook(path)["Belgeler"]
    header = [c.value for c in sheet[1]]
    assert header == [
        "Belge no",
        "Dosya",
        "Sayfa sayısı",
        "Kaynak sayfalar",
        "Şablon",
        "PDF/A",
        "Kontrol gerekli",
        "Kontrol nedenleri",
        "Kayıt No",
        "Ünvan",
        "Not",
    ]
    assert [c.value for c in sheet[2]][:8] == [
        "1",
        "101_Örnek.pdf",
        "2",
        "1, 2",
        "Deneme",
        "evet",
        "hayır",
        None,
    ]
    second = [c.value for c in sheet[3]]
    assert second[6] == "evet" and "zorunlu değer eksik: Kayıt No" in second[7]
    assert sheet.freeze_panes == "A2"


def test_formula_like_values_are_text(tmp_path):
    job, rows = items()
    path = tmp_path / "index.xlsx"
    write_index(rows, job, path)
    sheet = openpyxl.load_workbook(path)["Belgeler"]
    cell = sheet.cell(row=3, column=10)
    assert cell.value == "=1+1" and cell.data_type == "s"
    assert sheet.cell(row=3, column=11).value == "@x"


def test_turkish_headers_and_values(tmp_path):
    job, rows = items()
    path = tmp_path / "Şükrü" / "index.xlsx"
    write_index(rows, job, path)
    sheet = openpyxl.load_workbook(path)["Belgeler"]
    assert sheet.cell(row=2, column=10).value == "Örnek Şti."


def test_control_characters_do_not_break_the_index(tmp_path):
    job, rows = items()
    rows[0].values["Ünvan"] = "Örnek\x01Şti"
    write_index(rows, job, tmp_path / "index.xlsx")
    sheet = openpyxl.load_workbook(tmp_path / "index.xlsx")["Belgeler"]
    assert sheet.cell(row=2, column=10).value == "ÖrnekŞti"


def test_pdfa_failure_alone_is_not_a_check_and_the_column_says_hayir(tmp_path):
    job, rows = items()
    rows[2].pdfa, rows[2].pdfa_note = False, "PDF/A doğrulanamadı"
    write_index(rows, job, tmp_path / "index.xlsx")
    sheet = openpyxl.load_workbook(tmp_path / "index.xlsx")["Belgeler"]
    third = [c.value for c in sheet[4]]
    assert third[5] == "hayır"  # PDF/A column
    assert third[6] == "hayır" and not third[7]  # Kontrol gerekli, no reasons
    assert "PDF/A" not in (sheet.cell(row=3, column=8).value or "")


def test_belge_no_is_text_and_ties_the_row_to_the_file(tmp_path):
    job, rows = items()
    write_index(rows, job, tmp_path / "index.xlsx")
    sheet = openpyxl.load_workbook(tmp_path / "index.xlsx")["Belgeler"]
    assert [sheet.cell(row=r, column=1).value for r in (2, 3, 4)] == ["1", "2", "3"]
    assert sheet.cell(row=4, column=2).value == "belge_003.pdf"
    assert sheet.cell(row=2, column=1).data_type == "s"


def test_ozet_sheet_has_name_time_and_counts(tmp_path):
    job, rows = items()
    job.name = "=Örnek iş"
    write_index(rows, job, tmp_path / "index.xlsx", datetime(2026, 11, 20, 14, 32))
    book = openpyxl.load_workbook(tmp_path / "index.xlsx")
    assert book.sheetnames == ["Belgeler", "Özet"]
    summary = {r[0].value: r[1] for r in book["Özet"].iter_rows()}
    assert summary["İş adı"].value == "=Örnek iş" and summary["İş adı"].data_type == "s"
    assert summary["Dışa aktarma zamanı"].value == "20.11.2026 14:32"
    assert summary["Dışa aktarma zamanı"].data_type == "s"
    assert summary["Belge sayısı"].value == "3"
    assert summary["Sayfa sayısı"].value == "4"  # 2 + 1 + 1
    assert summary["Kontrol gerekli"].value == "1"


def test_variable_named_belge_no_is_marked(tmp_path):
    job, rows = items()
    rows[0].values["Belge no"] = "X-9"
    write_index(rows, job, tmp_path / "index.xlsx")
    header = [c.value for c in openpyxl.load_workbook(tmp_path / "index.xlsx")["Belgeler"][1]]
    assert header[0] == "Belge no" and "Belge no (değişken)" in header
