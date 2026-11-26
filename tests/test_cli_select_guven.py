"""`evrakci is sec guven`: the same reasons, counts and pages as pipeline/select.py."""

from test_cli_values import setup

from evrakci.pipeline.select import Criterion, evaluate, guven_text
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore


def core_match(tmp_path, job_id, **params):
    job = JobStore(tmp_path / "isler").load(job_id)
    templates = {t.id: t for t in TemplateStore(tmp_path / "sablonlar").list()}
    return job, evaluate(job, Criterion("guven", params), templates=templates)


def test_cli_prints_what_the_core_gives(tmp_path, capsys):
    run, job_id = setup(tmp_path, capsys)
    capsys.readouterr()
    assert run("sec", job_id, "guven") == 0
    out = capsys.readouterr().out
    job, match = core_match(tmp_path, job_id, levels=["kontrol", "okunamadi", "okunmadi"],
                            checks=["eksik sayfa", "karışık şablon"], pages="deger")
    assert match.documents == 1
    assert guven_text(match) in out
    assert "Kontrol  1 değer" in out and "Okunamadı  0 değer" in out
    assert f"{match.documents} belge, {match.count()} sayfa" in out
    order = job.ordered_page_ids()
    positions = ", ".join(str(order.index(pid) + 1) for pid in match.page_ids)
    assert f"sayfa {positions}" in out


def test_cli_reasons_and_pages_follow_the_options(tmp_path, capsys):
    run, job_id = setup(tmp_path, capsys)
    capsys.readouterr()
    assert run("sec", job_id, "guven", "--neden", "orta", "--sayfalar", "belge") == 0
    out = capsys.readouterr().out
    assert "Eşleşen sayfa yok." in out and "Orta  0 değer" in out
    assert run("sec", job_id, "guven", "--neden", "kontrol", "--neden", "okunmadi",
               "--sayfalar", "belge") == 0
    out = capsys.readouterr().out
    _job, match = core_match(tmp_path, job_id, levels=["kontrol", "okunmadi"], pages="belge")
    assert f"{match.documents} belge, {match.count()} sayfa" in out
    assert run("sec", job_id, "guven", "--neden", "yok") == 2


def test_cli_says_when_nothing_was_read(tmp_path, capsys):
    run, job_id = setup(tmp_path, capsys)
    store = JobStore(tmp_path / "isler")
    job = store.load(job_id)
    job.values.clear()
    store.save(job)
    capsys.readouterr()
    assert run("sec", job_id, "guven") == 0
    assert "Değerler henüz okunmadı" in capsys.readouterr().out


def test_help_has_no_text_outside_the_string_table(tmp_path, capsys):
    """R-A-5: the --neden help carries no "(varsayılan: ...)" suffix."""
    run, _job_id = setup(tmp_path, capsys)
    capsys.readouterr()
    run("sec", "x", "guven", "--help")
    out = capsys.readouterr().out
    assert "Kontrol gerekenler:" in out and "varsayılan" not in out
