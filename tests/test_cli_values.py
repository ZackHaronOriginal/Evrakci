from fakes import make_pdf, text_page

from evrakci.cli import main
from evrakci.pipeline.cuts import compute_documents, record_values
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue


def setup(tmp_path, capsys):
    jobs, templates = tmp_path / "isler", tmp_path / "sablonlar"
    template = TemplateStore(templates).create("Deneme")
    template.add_variable("Ünvan", required=True)
    template.add_variable("Kayıt No")
    TemplateStore(templates).save(template)
    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page()])
    store = JobStore(jobs)
    job = store.create_job("İş", [pdf])
    job.manual_cuts.add("b1/1")
    job.apply_template(job.ordered_page_ids(), template.id)
    first, second = compute_documents(job)
    unvan, kayit = (v.key for v in template.variables)
    record_values(
        job,
        first,
        template.id,
        {
            unvan: VariableValue("Örnek", 0.9, 0, False),
            kayit: VariableValue("", 0.0, None, True, "77"),
        },
    )
    record_values(
        job,
        second,
        template.id,
        {
            unvan: VariableValue("Başka", 0.9, 0, False),
            kayit: VariableValue("88", 0.9, 0, False),
        },
    )
    store.save(job)

    def run(*args):
        return main(["--kok", str(jobs), "--sablon-kok", str(templates), "is", *args])

    return run, job.id


def test_cli_list_and_fix(tmp_path, capsys):
    run, job = setup(tmp_path, capsys)
    assert run("degerler", job) == 0
    out = capsys.readouterr().out
    assert "1. belge (Deneme) sayfa 1" in out and "Kayıt No: [okunamadı, öneri: 77]" in out
    assert "2. belge (Deneme)" in out
    assert run("degerler", job, "--kontrol") == 0
    out = capsys.readouterr().out
    assert "1. belge" in out and "2. belge" not in out
    assert run("deger", job, "1", "Kayıt No", "--oneri") == 0
    assert run("deger", job, "2", "Ünvan", "Başka Şti.") == 0
    capsys.readouterr()
    run("degerler", job)
    out = capsys.readouterr().out
    assert "Kayıt No: 77 [düzeltildi]" in out and "Ünvan: Başka Şti. [düzeltildi]" in out


def test_cli_errors(tmp_path, capsys):
    run, job = setup(tmp_path, capsys)
    assert run("deger", job, "9", "Ünvan", "x") == 2
    assert run("deger", job, "1", "Yok", "x") == 2
    assert run("deger", job, "2", "Kayıt No", "--oneri") == 2
    err = capsys.readouterr().err
    assert "Belge yok: 9" in err and "Değişken yok: Yok" in err and "öneri yok" in err
