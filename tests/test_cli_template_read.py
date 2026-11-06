import json

from conftest import needs_tesseract
from fakes import a4_300, make_pdf, qr_page

from evrakci.cli import main


def setup(tmp_path, capsys):
    roots = ["--kok", str(tmp_path / "isler"), "--sablon-kok", str(tmp_path / "sablonlar")]

    def run(*args):
        return main([*roots, *args])

    def last_line():
        return capsys.readouterr().out.strip().splitlines()[-1]

    assert run("sablon", "olustur", "Deneme Belgesi") == 0
    tid = last_line()
    run("sablon", "degisken-ekle", tid, "Firma Ünvanı", "--zorunlu")
    run("sablon", "bolum-ekle", tid, "Firma Ünvanı", "--sayfa", "1", "--kutu", "15,25,170,37")
    run("sablon", "bolum-ekle", tid, "Firma Ünvanı", "--sayfa", "1", "--kutu", "15,36,170,48")
    run("sablon", "degisken-ekle", tid, "Kayıt No")
    run("sablon", "bolum-ekle", tid, "Kayıt No", "--sayfa", "son", "--kutu", "15,95,120,107")
    run("sablon", "esik", tid, "0.6")
    capsys.readouterr()
    return run, last_line, tid


def layout_a(name, number):
    return a4_300([(name, (20, 28)), (number, (20, 98))])


def layout_b(name, number):  # the name sits 10 mm lower: only variant 2 sees it
    return a4_300([(name, (20, 38)), (number, (20, 98))])


@needs_tesseract
def test_template_test_command(tmp_path, capsys):
    run, _, tid = setup(tmp_path, capsys)
    example = make_pdf(tmp_path / "ornek.pdf", [layout_a("Örnek Şirketi", "123456")], dpi=300)
    assert run("sablon", "test", tid, str(example)) == 0
    out = capsys.readouterr().out
    assert 'Firma Ünvanı: "Örnek Şirketi" (bölüm 1' in out and 'Kayıt No: "123456"' in out


@needs_tesseract
def test_apply_and_read_with_variants(tmp_path, capsys):
    run, last_line, tid = setup(tmp_path, capsys)
    pages = [layout_a("Örnek Şirketi", "123456"), qr_page(), layout_b("Çağrı Ticaret", "654321")]
    scan = make_pdf(tmp_path / "tarama.pdf", [pages[0]], dpi=300)
    scan2 = make_pdf(tmp_path / "tarama2.pdf", [pages[2]], dpi=300)
    assert run("is", "olustur", "İş", str(scan), str(scan2)) == 0
    job = last_line()
    assert run("is", "kes", job, "2") == 0
    assert run("is", "sablon-uygula", job, "1-2", tid) == 0
    assert run("is", "oku", job) == 0
    out = capsys.readouterr().out
    assert "Firma Ünvanı=Örnek Şirketi" in out and "Firma Ünvanı=Çağrı Ticaret" in out
    run("is", "goster", job, "--json")
    data = json.loads(capsys.readouterr().out)
    second = data["job"]["values"]["b2/0"]["Firma Ünvanı"]
    assert second["section"] == 1 and second["value"] == "Çağrı Ticaret"


@needs_tesseract
def test_deleted_template_reported(tmp_path, capsys):
    run, last_line, tid = setup(tmp_path, capsys)
    scan = make_pdf(tmp_path / "t.pdf", [layout_a("Örnek", "1")], dpi=300)
    run("is", "olustur", "İş", str(scan))
    job = last_line()
    run("is", "sablon-uygula", job, "1-1", tid)
    run("sablon", "sil", tid)
    capsys.readouterr()
    assert run("is", "oku", job) == 0
    assert f"Şablon bulunamadı: {tid}" in capsys.readouterr().out


def test_apply_unknown_template(tmp_path, capsys):
    run, last_line, _ = setup(tmp_path, capsys)
    scan = make_pdf(tmp_path / "t.pdf", [qr_page()])
    run("is", "olustur", "İş", str(scan))
    job = last_line()
    assert run("is", "sablon-uygula", job, "1-1", "yok") == 2
    assert "Şablon bulunamadı: yok" in capsys.readouterr().err


@needs_tesseract
def test_mixed_templates_flagged(tmp_path, capsys):
    run, last_line, tid = setup(tmp_path, capsys)
    assert run("sablon", "olustur", "İkinci") == 0
    other = last_line()
    scan = make_pdf(tmp_path / "t.pdf", [layout_a("Örnek", "1"), layout_a("Örnek", "2")], dpi=300)
    run("is", "olustur", "İş", str(scan))
    job = last_line()
    run("is", "sablon-uygula", job, "1-1", tid)
    run("is", "sablon-uygula", job, "2-2", other)
    capsys.readouterr()
    run("is", "goster", job)
    assert "[kontrol: karışık şablon]" in capsys.readouterr().out
