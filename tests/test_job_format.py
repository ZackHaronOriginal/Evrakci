import json

from fakes import job_from_kinds

from evrakci.pipeline.job import JOB_FORMAT_VERSION, LastExport, job_from_dict, job_to_dict


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


def test_a_job_never_exported_writes_no_field():
    assert "last_export" not in job_to_dict(job_from_kinds({"a": "pp"}))


def test_a_damaged_field_does_not_stop_the_job_opening():
    data = _data(2)
    data["last_export"] = {"at": "x"}
    assert job_from_dict(data).last_export is None
