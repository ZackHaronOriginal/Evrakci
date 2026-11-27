from fakes import make_pdf, text_page

from evrakci.cli import main
from evrakci.pipeline.cuts import compute_documents, record_values
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue


def _clashing_job(tmp_path):
    jobs, templates = tmp_path / "isler", tmp_path / "sablonlar"
    template = TemplateStore(templates).create("Deneme")
    template.add_variable("Ünvan", required=True)
    template.set_pattern("{Ünvan}")
    TemplateStore(templates).save(template)
    pdf = make_pdf(tmp_path / "tarama.pdf", [text_page(), text_page()])
    store = JobStore(jobs)
    job = store.create_job("İş", [pdf])
    job.manual_cuts.add("b1/1")
    job.apply_template(job.ordered_page_ids(), template.id)
    key = template.variables[0].key
    for document in compute_documents(job):
        record_values(job, document, template.id, {key: VariableValue("Örnek", 0.9, 0, False)})
    store.save(job)
    return ["--kok", str(jobs), "--sablon-kok", str(templates), "is", "disa-aktar", job.id]


def test_onizle_prints_source_name_and_note_and_writes_nothing(tmp_path, capsys):
    base = _clashing_job(tmp_path)
    out = tmp_path / "out"
    assert main([*base, "--cikti", str(out), "--onizle"]) == 0
    assert capsys.readouterr().out.split("\n")[:-1] == [
        "Kaynak\tYazılacak dosya adı\tNot",
        "tarama.pdf\tÖrnek.pdf\t",
        "tarama.pdf\tÖrnek (2).pdf\tAd çakışması, (2) eklendi",
    ]
    assert not out.exists()


def test_export_line_carries_the_name_note(tmp_path, capsys):
    base = _clashing_job(tmp_path)
    assert main([*base, "--cikti", str(tmp_path / "out"), "--metin-katmani-yok"]) == 0
    lines = capsys.readouterr().out.split("\n")
    assert "Örnek.pdf: sayfa 1" in lines[0] and "[ad:" not in lines[0]
    assert lines[1].endswith("[ad: Ad çakışması, (2) eklendi]")
