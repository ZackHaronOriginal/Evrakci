import pikepdf
import pytest
from fakes import make_pdf, text_page

from evrakci.pipeline.cuts import Document
from evrakci.pipeline.writer import write_documents


def page_counts(paths):
    counts = []
    for path in paths:
        with pikepdf.open(path) as pdf:
            counts.append(len(pdf.pages))
    return counts


def test_pages_and_order(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page("A0"), text_page("A1"), text_page("A2")])
    docs = [Document(("a/2",)), Document(("a/0", "a/1"))]
    out = write_documents(docs, {"a": a}, {}, tmp_path / "out")
    assert [p.name for p in out] == ["belge_001.pdf", "belge_002.pdf"]
    assert page_counts(out) == [1, 2]


def test_rotation_adds_to_existing(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page()])
    with pikepdf.open(a, allow_overwriting_input=True) as pdf:
        pdf.pages[0].rotate(90, relative=False)
        pdf.save(a)
    out = write_documents([Document(("a/0",))], {"a": a}, {"a/0": 90}, tmp_path / "out")
    with pikepdf.open(out[0]) as pdf:
        assert pdf.pages[0].obj.Rotate == 180


def test_nothing_to_write(tmp_path):
    assert write_documents([], {}, {}, tmp_path / "out") == []


def test_refuses_folder_with_old_export(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page()])
    out = tmp_path / "out"
    write_documents([Document(("a/0",))], {"a": a}, {}, out)
    with pytest.raises(FileExistsError):
        write_documents([Document(("a/0",))], {"a": a}, {}, out)


def test_custom_names(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page(), text_page()])
    docs = [Document(("a/0",)), Document(("a/1",))]
    out = write_documents(docs, {"a": a}, {}, tmp_path / "out", names=["Örnek Şti", "belge_002"])
    assert [p.name for p in out] == ["Örnek Şti.pdf", "belge_002.pdf"]


def test_conflict_on_any_target_or_index(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page()])
    out = tmp_path / "out"
    out.mkdir()
    (out / "Örnek.pdf").write_bytes(b"x")
    with pytest.raises(FileExistsError, match="Örnek.pdf"):
        write_documents([Document(("a/0",))], {"a": a}, {}, out, names=["Örnek"])
    (out / "Örnek.pdf").unlink()
    (out / "index.xlsx").write_bytes(b"x")
    with pytest.raises(FileExistsError, match="index.xlsx"):
        write_documents([Document(("a/0",))], {"a": a}, {}, out, names=["Örnek"])
    assert sorted(p.name for p in out.iterdir()) == ["index.xlsx"]


def test_writer_refuses_duplicate_names(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page(), text_page()])
    docs = [Document(("a/0",)), Document(("a/1",))]
    with pytest.raises(ValueError):
        write_documents(docs, {"a": a}, {}, tmp_path / "out", names=["x", "X"])
    assert not (tmp_path / "out").exists()
