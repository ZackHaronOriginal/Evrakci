"""I-06: the kind `guven` ("Kontrol gerekenler"): reasons, counts, value pages, parity."""

import time

from fakes import job_from_kinds

from evrakci.pipeline.cuts import compute_documents, current_values, record_values
from evrakci.pipeline.select import (
    GUVEN_REASONS,
    GUVEN_WORDS,
    Criterion,
    evaluate,
    guven_text,
    kinds,
    reason_count_text,
    value_page,
    values_read,
)
from evrakci.pipeline.templates.model import Section, Template, Variable
from evrakci.pipeline.templates.values import SectionReading, VariableValue, box_section

SICIL = Variable("Sicil_No", [Section(1, (10, 10, 60, 20))], True, key="k1")
TARIH = Variable("Tarih", [Section(-1, (10, 10, 60, 20))], False, key="k2")
TEMPLATE = Template("t1", "Rapor", [SICIL, TARIH])
TEMPLATES = {"t1": TEMPLATE}

EMIN = VariableValue("48190", 0.97, 0, False)
ORTA = VariableValue("48190", 0.80, 0, False)
KONTROL = VariableValue("", 0.0, None, True, "48213", (SectionReading(0, "482I3", 0.4),))
OKUNAMADI = VariableValue("", 0.0, None, True, "", (SectionReading(0, "", 0.0),))


def make_job(spec="pppq" * 5):
    job = job_from_kinds({"a": spec})
    job.apply_template(job.ordered_page_ids(), TEMPLATE.id)
    return job, compute_documents(job)


def read(job, document, sicil, tarih=EMIN):
    record_values(job, document, TEMPLATE.id, {"k1": sicil, "k2": tarih})


def guven(job, levels=("kontrol", "okunamadi", "okunmadi"), checks=("eksik sayfa",),
          pages="deger"):
    return evaluate(job, Criterion("guven", {"levels": list(levels), "checks": list(checks),
                                             "pages": pages}), templates=TEMPLATES)


def test_kind_is_registered_and_round_trips():
    assert "guven" in kinds()
    criterion = Criterion("guven", {"levels": ["kontrol"], "checks": [], "pages": "belge"})
    assert Criterion.from_dict(criterion.to_dict()) == criterion


def test_reasons_add_up_and_emin_is_never_selected():
    job, docs = make_job()
    read(job, docs[0], KONTROL)  # 1 kontrol
    read(job, docs[1], OKUNAMADI, ORTA)  # 1 okunamadi, 1 orta
    read(job, docs[2], EMIN)  # nothing
    # docs[3] and docs[4]: not read
    match = guven(job, levels=("kontrol", "okunamadi", "orta", "okunmadi"))
    assert match.reasons == {"kontrol": 1, "okunamadi": 1, "orta": 1, "okunmadi": 2,
                             "eksik sayfa": 0}
    assert match.documents == 4  # docs 0, 1, 3, 4: never the Emin one
    assert not set(docs[2].page_ids) & set(match.page_ids)
    only = guven(job, levels=("kontrol",), checks=())
    assert only.reasons == {"kontrol": 1} and only.documents == 1


def test_default_reasons_leave_orta_out():
    job, docs = make_job("pppq" * 2)
    read(job, docs[0], ORTA)
    read(job, docs[1], EMIN)
    match = evaluate(job, Criterion("guven"), templates=TEMPLATES)
    assert match.page_ids == () and "orta" not in match.reasons
    asked = evaluate(job, Criterion("guven", {"levels": ["orta"]}), templates=TEMPLATES)
    assert asked.documents == 1


def test_value_page_is_the_page_the_box_is_on():
    job, docs = make_job()
    read(job, docs[0], KONTROL)  # the Sicil box is on page 1
    read(job, docs[1], EMIN, VariableValue("", 0.0, None, True, "1.1.2026",
                                           (SectionReading(0, "I.1.2026", 0.3),)))
    pages = guven(job, levels=("kontrol",), checks=()).page_ids
    assert pages == (docs[0].page_ids[0], docs[1].page_ids[-1])  # Tarih is on the last page
    whole = guven(job, levels=("kontrol",), checks=(), pages="belge").page_ids
    assert whole == docs[0].page_ids + docs[1].page_ids
    assert value_page(TEMPLATE, "k2", None, 3) == 2 and value_page(TEMPLATE, "k1", 0, 3) == 0
    assert value_page(TEMPLATE, "k2", 0, 1) == 0 and value_page(None, "k1", 0, 3) == 0


def test_a_flagged_unread_and_short_document_are_all_found():
    job = job_from_kinds({"a": "p" * 7})
    job.apply_template(job.ordered_page_ids(), TEMPLATE.id)
    job.apply_filter(job.ordered_page_ids(), 3)  # 3 + 3 + 1: the last one is short
    docs = compute_documents(job)
    read(job, docs[0], KONTROL)
    match = guven(job)
    assert match.reasons == {"kontrol": 1, "okunamadi": 0, "okunmadi": 2, "eksik sayfa": 1}
    assert match.documents == 3
    assert set(docs[0].page_ids[:1]) <= set(match.page_ids)
    assert docs[2].page_ids[0] in match.page_ids  # the short document, by its first page
    assert guven_text(match) == "3 belge seçildi: Kontrol 1, Okunmadı 2, Eksik sayfa 1"


def test_nothing_read_and_values_read():
    job, docs = make_job("pppq" * 2)
    assert not values_read(job)
    read(job, docs[0], EMIN)
    assert values_read(job)


def test_words_and_count_texts():
    assert GUVEN_WORDS["okunamadi"] == "Okunamadı" and len(GUVEN_REASONS) == 6
    assert reason_count_text("kontrol", 4) == "4 değer"
    assert reason_count_text("okunmadi", 2) == "2 belge"
    assert reason_count_text("eksik sayfa", 1) == "1 belge"


def test_box_section_is_the_section_the_value_was_read_from():
    assert box_section(VariableValue("a", 0.9, 1, False)) == 1
    assert box_section(OKUNAMADI) is None
    assert box_section(KONTROL) == 0
    two = VariableValue("", 0.0, None, True, "48213", (SectionReading(0, "482I3", 0.4),
                                                       SectionReading(1, "48213", 0.55)))
    assert box_section(two) == 1


def test_values_of_a_document_that_changed_are_not_used():
    job, docs = make_job("pppq" * 2)
    read(job, docs[0], KONTROL)
    job.add_cut(docs[0].page_ids[1])  # the document is no longer the one that was read
    assert current_values(job, compute_documents(job)[0]) is None
    assert guven(job, levels=("kontrol",), checks=()).reasons == {"kontrol": 0}


def test_800_pages_is_fast():
    job, docs = make_job("pppq" * 200)
    for i, document in enumerate(docs):
        read(job, document, (KONTROL, EMIN, ORTA, OKUNAMADI)[i % 4])
    start = time.perf_counter()
    for _ in range(5):
        guven(job)
    each_ms = (time.perf_counter() - start) * 1000 / 5
    assert each_ms < 400, each_ms
