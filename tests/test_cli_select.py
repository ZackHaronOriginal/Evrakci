"""`evrakci is sec`: the same pages as pipeline/select.py (and so as the window's dialog)."""

from fakes import make_pdf, qr_page, text_page

from evrakci.cli import main
from evrakci.pipeline.select import Criterion, evaluate
from evrakci.pipeline.store import JobStore

PAGES = [text_page()] * 4 + [qr_page()] + [text_page()] * 3 + [qr_page()] + [text_page()] * 2


def setup_job(tmp_path, capsys):
    root = tmp_path / "kok"
    pdf = make_pdf(tmp_path / "t.pdf", PAGES)
    assert main(["--kok", str(root), "is", "olustur", "Seç", str(pdf)]) == 0
    job_id = capsys.readouterr().out.strip().splitlines()[-1]

    def run(*args):
        return main(["--kok", str(root), *args])

    return run, JobStore(root), job_id


def printed_positions(out: str) -> list[int]:
    line = next(x for x in out.splitlines() if x.startswith("sayfa "))
    return [int(n) for n in line.removeprefix("sayfa ").split(", ")]


def test_cli_gives_the_pages_the_core_gives(tmp_path, capsys):
    run, store, job_id = setup_job(tmp_path, capsys)
    job = store.load(job_id)
    order = job.ordered_page_ids()
    cases = [("tek", {}, []), ("cift", {}, []), ("belge", {"number": 2}, ["--numara", "2"])]
    for kind, params, extra in cases:
        assert run("is", "sec", job_id, kind, *extra) == 0
        out = capsys.readouterr().out
        match = evaluate(job, Criterion(kind, params))
        assert f"{match.count()} sayfa seçildi." in out
        assert printed_positions(out) == [order.index(pid) + 1 for pid in match.page_ids]
    assert printed_positions_of(run, capsys, job_id, "tek") == [1, 3, 6, 8, 10]
    assert printed_positions_of(run, capsys, job_id, "cift") == [2, 4, 7, 11]


def printed_positions_of(run, capsys, job_id, kind):
    assert run("is", "sec", job_id, kind) == 0
    return printed_positions(capsys.readouterr().out)


def test_sil_deletes_the_selected_pages_like_del(tmp_path, capsys):
    run, store, job_id = setup_job(tmp_path, capsys)
    assert run("is", "sec", job_id, "cift", "--sil") == 0
    assert "Sayfa 2, 4, 7, 11 silindi" in capsys.readouterr().out
    job = store.load(job_id)
    assert {job.page_at(n) for n in (2, 4, 7, 11)} == job.deleted
    run("is", "goster", job_id)
    assert "1. belge: sayfa 1, 3" in capsys.readouterr().out


def test_nothing_matches_and_errors(tmp_path, capsys):
    run, _store, job_id = setup_job(tmp_path, capsys)
    assert run("is", "sec", job_id, "belge", "--numara", "9") == 0
    assert "Eşleşen sayfa yok." in capsys.readouterr().out
    assert run("is", "sec", job_id, "belge") == 2
    assert "--numara" in capsys.readouterr().err  # argparse's own "required" message
    assert run("is", "sec", "yok", "tek") == 2
    assert "İş bulunamadı" in capsys.readouterr().err
    assert run("is", "sec", job_id, "yok") == 2


def saved_filters(tmp_path, capsys):
    """The job of PAGES, a template with three saved filters and a runner for both roots."""
    run, store, job_id = setup_job(tmp_path, capsys)
    templates = str(tmp_path / "sablonlar")

    def sablon(*args):
        return main(["--sablon-kok", templates, "sablon", *args])

    assert sablon("olustur", "Süzgeç") == 0
    template_id = capsys.readouterr().out.strip().splitlines()[-1]
    assert sablon("filtre-ekle", template_id, "Tekler", "tek") == 0
    assert sablon("filtre-ekle", template_id, "Boşlar", "bos") == 0
    assert sablon("filtre-ekle", template_id, "İkinci", "belge", "--ayar", "number=2") == 0
    capsys.readouterr()

    def secs(*args):
        return main(["--kok", str(tmp_path / "kok"), "--sablon-kok", templates, "is", "sec",
                     job_id, *args])

    return secs, store, job_id, template_id, templates


def test_is_sec_sablon_gives_the_pages_select_pages_gives(tmp_path, capsys):
    from evrakci.pipeline.select import select_pages
    from evrakci.pipeline.templates.store import TemplateStore

    secs, store, job_id, template_id, templates = saved_filters(tmp_path, capsys)
    job = store.load(job_id)
    template = TemplateStore(templates).load(template_id)
    order = job.ordered_page_ids()
    for names in (["Tekler", "İkinci"], ["Tekler"], ["İkinci"], None):
        chosen = [template.saved_filter(n) for n in names] if names else template.saved_filters
        expected = select_pages(job, [Criterion(f.kind, f.params) for f in chosen])
        args = ["--sablon", template_id]
        for name in names or ():
            args += ["--filtre", name]
        assert secs(*args) == 0
        out = capsys.readouterr().out
        if expected.page_ids:
            assert f"{len(chosen)} filtre açık: {len(expected.page_ids)} sayfa" in out
            assert printed_positions(out) == [order.index(p) + 1 for p in expected.page_ids]
        else:
            assert "Eşleşen sayfa yok." in out
    assert secs("--sablon", template_id, "--filtre", "Tekler", "--filtre", "İkinci") == 0
    out = capsys.readouterr().out
    assert "Tekler: 5 sayfa" in out and printed_positions(out) == [6, 8]


def test_is_sec_sablon_says_unknown_kinds_and_refuses_bad_use(tmp_path, capsys):
    from evrakci.pipeline.templates.store import TemplateStore

    secs, _store, _job_id, template_id, templates = saved_filters(tmp_path, capsys)
    store = TemplateStore(templates)
    template = store.load(template_id)
    template.add_saved_filter("Gelecek", "gelecek")
    store.save(template)
    assert secs("--sablon", template_id, "--filtre", "Gelecek") == 2  # refused, no count
    captured = capsys.readouterr()
    assert "Gelecek: Bu filtreyi bu sürüm tanımıyor" in captured.err
    assert "filtre açık" not in captured.out and "sayfa" not in captured.out
    assert secs("--sablon", template_id, "--filtre", "Yok") == 2
    assert "Filtre yok" in capsys.readouterr().err
    assert secs("--sablon", "ffff") == 2
    assert "Şablon bulunamadı" in capsys.readouterr().err
    assert secs() == 2  # no criterion and no template: argparse's own message
    assert "required: olcut" in capsys.readouterr().err
    assert secs("--filtre", "Tekler") == 2  # --filtre alone is not ignored
    assert "--filtre için --sablon gerekir." in capsys.readouterr().err
    assert secs("--sablon", template_id, "cift", "--sil") == 2
    assert "usage:" in capsys.readouterr().err


def test_bad_settings_of_a_known_kind_are_refused_like_an_unknown_kind(tmp_path, capsys):
    from evrakci.pipeline.templates.store import TemplateStore

    secs, _store, _job_id, template_id, templates = saved_filters(tmp_path, capsys)
    store = TemplateStore(templates)
    template = store.load(template_id)
    template.add_saved_filter("Bozuk", "farkli", {"by": 5})
    store.save(template)
    assert secs("--sablon", template_id, "--filtre", "Bozuk") == 2
    assert "Bozuk: Bu filtreyi bu sürüm tanımıyor" in capsys.readouterr().err


def test_a_criterion_after_sablon_is_anded_with_the_filters(tmp_path, capsys):
    from evrakci.pipeline.select import select_pages

    secs, store, job_id, template_id, _templates = saved_filters(tmp_path, capsys)
    job = store.load(job_id)
    assert secs("--sablon", template_id, "--filtre", "Tekler", "cift") == 0
    out = capsys.readouterr().out
    expected = select_pages(job, [Criterion("tek"), Criterion("cift")])
    assert not expected.page_ids and "Eşleşen sayfa yok." in out
    assert secs("--sablon", template_id, "--filtre", "Tekler", "--filtre", "Tekler",
                "belge", "--numara", "2") == 0
    out = capsys.readouterr().out
    expected = select_pages(job, [Criterion("tek"), Criterion("belge", {"number": 2})])
    assert "2 filtre açık: 2 sayfa" in out and len(expected.page_ids) == 2
    assert printed_positions(out) == [6, 8]


def test_a_template_without_filters_says_none_is_on(tmp_path, capsys):
    secs, _store, _job_id, _template_id, templates = saved_filters(tmp_path, capsys)
    assert main(["--sablon-kok", templates, "sablon", "olustur", "Boş"]) == 0
    empty = capsys.readouterr().out.strip().splitlines()[-1]
    assert secs("--sablon", empty) == 0
    assert capsys.readouterr().out.strip() == "Hiçbir filtre açık değil"
