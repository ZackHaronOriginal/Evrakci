import json

from fakes import job_from_kinds, without_sizes

from evrakci.pipeline.analyze import PageInfo
from evrakci.pipeline.job import (
    JOB_FORMAT_VERSION,
    LastExport,
    apply_page_sizes,
    carry_page_sizes,
    job_from_dict,
    job_to_dict,
)


def _data(version):
    data = json.loads(json.dumps(job_to_dict(job_from_kinds({"a": "pp"}))))
    data["version"] = version
    data.pop("last_export", None)
    return data


def test_old_files_without_the_field_open_with_none():
    assert JOB_FORMAT_VERSION == 2
    for version in (1, 2):
        assert job_from_dict(_data(version)).last_export is None


def test_last_export_round_trips_and_stays_version_2():
    job = job_from_kinds({"a": "pp"})
    job.last_export = LastExport("2026-11-20T14:32", "C:/Çıktı", 8, 2)
    data = json.loads(json.dumps(job_to_dict(job)))
    assert data["version"] == 2
    assert job_from_dict(data) == job


def test_the_export_state_round_trips_and_follows_edits():
    from evrakci.pipeline.job import job_state

    job = job_from_kinds({"a": "pp"})
    before = job_state(job)
    job.last_export = LastExport("2026-11-20T14:32", "C:/Çıktı", 8, 2, before)
    assert job_state(job) == before  # the last export is not part of the state
    assert job_from_dict(json.loads(json.dumps(job_to_dict(job)))).last_export.state == before
    job.drop_empty = not job.drop_empty
    assert job_state(job) != before


def test_a_job_never_exported_writes_no_field():
    assert "last_export" not in job_to_dict(job_from_kinds({"a": "pp"}))


def test_a_damaged_field_does_not_stop_the_job_opening():
    data = _data(2)
    data["last_export"] = {"at": "x"}
    assert job_from_dict(data).last_export is None


def test_page_sizes_round_trip_with_one_decimal_and_stay_version_2():
    job = job_from_kinds({"a": "pp"})
    job.pages["a/0"] = PageInfo(0.05, False, 210.04, 297.0)
    job.pages["a/1"] = PageInfo(0.05, False, 148.0, 210.0)
    data = json.loads(json.dumps(job_to_dict(job)))
    assert data["version"] == 2
    assert data["pages"]["a/0"]["width_mm"] == 210.0 and data["pages"]["a/0"]["height_mm"] == 297.0
    back = job_from_dict(data)
    assert (back.pages["a/1"].width_mm, back.pages["a/1"].height_mm) == (148.0, 210.0)
    assert back.pages["a/0"].width_mm == 210.0


def test_an_old_job_dict_without_the_keys_opens_with_unknown_sizes():
    data = without_sizes(json.loads(json.dumps(job_to_dict(job_from_kinds({"a": "ppq"})))))
    assert "width_mm" not in data["pages"]["a/0"]
    job = job_from_dict(data)
    assert [(i.width_mm, i.height_mm) for i in job.pages.values()] == [(0.0, 0.0)] * 3
    assert not job.pages["a/0"].has_size
    assert job.pages["a/2"].is_separator


def test_a_damaged_size_reads_as_unknown_and_never_stops_the_job():
    data = json.loads(json.dumps(job_to_dict(job_from_kinds({"a": "pppp"}))))
    data["pages"]["a/0"].update(width_mm="x", height_mm=None)
    data["pages"]["a/1"].update(width_mm=-5, height_mm=297)
    data["pages"]["a/2"].update(width_mm=float("nan"), height_mm=float("inf"))
    data["pages"]["a/3"].update(width_mm="210", height_mm=297)  # a text number is accepted
    job = job_from_dict(data)
    assert [job.pages[f"a/{i}"].has_size for i in range(4)] == [False, False, False, True]


def test_the_keys_an_older_program_reads_are_unchanged():
    job = job_from_kinds({"a": "pp"})
    job.pages["a/0"] = PageInfo(0.05, False, 210.0, 297.0)
    page = job_to_dict(job)["pages"]["a/0"]
    assert page["ink_ratio"] == 0.05 and page["is_separator"] is False


def test_apply_page_sizes_fills_only_unknown_pages():
    job = job_from_kinds({"a": "ppp"})
    job.pages["a/0"] = PageInfo(0.05, False, 210.0, 297.0)
    filled = apply_page_sizes(job, {"a/0": (1.0, 1.0), "a/1": (148.0, 210.0), "a/2": (0.0, 5.0),
                                    "x/9": (1.0, 1.0)})
    assert filled == 1
    assert (job.pages["a/0"].width_mm, job.pages["a/1"].width_mm) == (210.0, 148.0)
    assert not job.pages["a/2"].has_size


def test_carry_page_sizes_gives_a_restored_job_the_sizes_the_open_one_has():
    open_job = job_from_kinds({"a": "pp"})
    open_job.pages["a/1"] = PageInfo(0.05, False, 148.0, 210.0)
    restored = job_from_kinds({"a": "pp"})
    assert carry_page_sizes(open_job, restored) == 1
    assert restored.pages["a/1"].width_mm == 148.0
