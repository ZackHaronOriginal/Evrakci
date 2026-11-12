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
        ["zorunlu değer eksik: Kayıt No", "PDF/A değil: doğrulanamadı"],
        False,
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
    assert [c.value for c in sheet[2]][:7] == [
        "101_Örnek.pdf",
        "2",
        "1, 2",
        "Deneme",
        "evet",
        "hayır",
        None,
    ]
    second = [c.value for c in sheet[3]]
    assert second[5] == "evet" and "zorunlu değer eksik: Kayıt No" in second[6]
    assert sheet.freeze_panes == "A2"


def test_formula_like_values_are_text(tmp_path):
    job, rows = items()
    path = tmp_path / "index.xlsx"
    write_index(rows, job, path)
    sheet = openpyxl.load_workbook(path)["Belgeler"]
    cell = sheet.cell(row=3, column=9)
    assert cell.value == "=1+1" and cell.data_type == "s"
    assert sheet.cell(row=3, column=10).value == "@x"


def test_turkish_headers_and_values(tmp_path):
    job, rows = items()
    path = tmp_path / "Şükrü" / "index.xlsx"
    write_index(rows, job, path)
    sheet = openpyxl.load_workbook(path)["Belgeler"]
    assert sheet.cell(row=2, column=9).value == "Örnek Şti."


def test_control_characters_do_not_break_the_index(tmp_path):
    job, rows = items()
    rows[0].values["Ünvan"] = "Örnek\x01Şti"
    write_index(rows, job, tmp_path / "index.xlsx")
    sheet = openpyxl.load_workbook(tmp_path / "index.xlsx")["Belgeler"]
    assert sheet.cell(row=2, column=9).value == "ÖrnekŞti"
