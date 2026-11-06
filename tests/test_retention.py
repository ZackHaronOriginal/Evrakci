import os
import sys
import time

import pytest
from fakes import make_pdf, text_page

from evrakci.cli import main
from evrakci.pipeline.settings import Settings, SettingsError, load_settings, save_settings
from evrakci.pipeline.store import JobStore


def test_settings_round_trip_and_validation(tmp_path):
    path = tmp_path / "ayarlar.json"
    assert load_settings(path) == Settings("sakla")
    save_settings(Settings("30"), path)
    assert load_settings(path).retention == "30"
    for bad in ("", "0", "-3", "bazen"):
        with pytest.raises(SettingsError):
            Settings(bad)


def test_delete_older_than_uses_mtime(tmp_path):
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    old, new = store.create_job("eski", [pdf]), store.create_job("yeni", [pdf])
    ten_days_ago = time.time() - 10 * 86400
    os.utime(tmp_path / "jobs" / old.id / "job.json", (ten_days_ago, ten_days_ago))
    assert store.delete_older_than(7) == [old.id]
    assert [j.id for j in store.list_jobs()] == [new.id]


def cli(tmp_path, *args):
    env_args = ["--kok", str(tmp_path / "jobs"), "--sablon-kok", str(tmp_path / "s")]
    return main([*env_args, *args])


def test_default_keeps_everything(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayarlar.json"))
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("eski", [pdf])
    long_ago = time.time() - 400 * 86400
    os.utime(tmp_path / "jobs" / job.id / "job.json", (long_ago, long_ago))
    assert cli(tmp_path, "is", "listele") == 0
    assert job.id in capsys.readouterr().out
    assert (
        cli(
            tmp_path,
            "is",
            "disa-aktar",
            job.id,
            "--cikti",
            str(tmp_path / "o"),
            "--metin-katmani-yok",
        )
        == 0
    )
    assert [j.id for j in store.list_jobs()] == [job.id]


def test_day_limit_applied_on_listing(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayarlar.json"))
    assert main(["ayar", "saklama", "30"]) == 0
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("eski", [pdf])
    long_ago = time.time() - 40 * 86400
    os.utime(tmp_path / "jobs" / job.id / "job.json", (long_ago, long_ago))
    capsys.readouterr()
    assert cli(tmp_path, "is", "listele") == 0
    assert f"Saklama süresi doldu, silindi: {job.id}" in capsys.readouterr().err
    assert store.list_jobs() == []


def test_delete_after_export_only_on_success(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayarlar.json"))
    assert main(["ayar", "saklama", "disa-aktarinca-sil"]) == 0
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])
    busy = tmp_path / "dolu"
    busy.mkdir()
    (busy / "eski.pdf").write_bytes(b"x")
    assert (
        cli(tmp_path, "is", "disa-aktar", job.id, "--cikti", str(busy), "--metin-katmani-yok") == 2
    )
    assert [j.id for j in store.list_jobs()] == [job.id]
    capsys.readouterr()
    assert (
        cli(
            tmp_path,
            "is",
            "disa-aktar",
            job.id,
            "--cikti",
            str(tmp_path / "o"),
            "--metin-katmani-yok",
        )
        == 0
    )
    assert f"İş silindi (saklama ayarı): {job.id}" in capsys.readouterr().out
    assert store.list_jobs() == [] and (tmp_path / "o" / "index.xlsx").is_file()


def test_ayar_goster_and_bad_value(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayarlar.json"))
    assert main(["ayar", "goster"]) == 0
    assert "Saklama: sakla" in capsys.readouterr().out
    assert main(["ayar", "saklama", "bazen"]) == 2
    assert "Geçersiz saklama" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need admin rights on Windows")
def test_retention_only_deletes_real_jobs(tmp_path):
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("eski", [pdf])
    stranger = tmp_path / "jobs" / "baska"
    stranger.mkdir()
    (stranger / "job.json").write_text("{}", encoding="utf-8")
    (stranger / "onemli.docx").write_bytes(b"x")
    real_target = tmp_path / "hedef"
    real_target.mkdir()
    (real_target / "job.json").write_text("{}", encoding="utf-8")
    (tmp_path / "jobs" / "baglanti").symlink_to(real_target, target_is_directory=True)
    old = time.time() - 50 * 86400
    for path in (
        tmp_path / "jobs" / job.id / "job.json",
        stranger / "job.json",
        real_target / "job.json",
    ):
        os.utime(path, (old, old))
    errors = []
    assert store.delete_older_than(7, on_error=errors.append) == [job.id]
    assert (stranger / "onemli.docx").exists() and real_target.exists()


def test_export_marks_job_as_used(tmp_path, monkeypatch):
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayarlar.json"))
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])
    path = tmp_path / "jobs" / job.id / "job.json"
    old = time.time() - 50 * 86400
    os.utime(path, (old, old))
    assert (
        cli(
            tmp_path,
            "is",
            "disa-aktar",
            job.id,
            "--cikti",
            str(tmp_path / "o"),
            "--metin-katmani-yok",
        )
        == 0
    )
    assert path.stat().st_mtime > time.time() - 600


def test_delete_after_export_keeps_job_needing_checks(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(tmp_path / "ayarlar.json"))
    assert main(["ayar", "saklama", "disa-aktarinca-sil"]) == 0

    pdf = make_pdf(tmp_path / "t.pdf", [text_page(), text_page(), text_page()])
    store = JobStore(tmp_path / "jobs")
    job = store.create_job("İş", [pdf])
    job.apply_filter(job.ordered_page_ids(), 2)  # leaves a short last document
    store.save(job)
    capsys.readouterr()
    assert (
        cli(
            tmp_path,
            "is",
            "disa-aktar",
            job.id,
            "--cikti",
            str(tmp_path / "o"),
            "--metin-katmani-yok",
        )
        == 0
    )
    assert "İş saklandı" in capsys.readouterr().out
    assert [j.id for j in store.list_jobs()] == [job.id]


def test_bad_settings_file_falls_back_to_keep(tmp_path, monkeypatch, capsys):
    settings = tmp_path / "ayarlar.json"
    settings.write_text("{bozuk", encoding="utf-8")
    monkeypatch.setenv("EVRAKCI_AYARLAR", str(settings))
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    assert cli(tmp_path, "is", "olustur", "İş", str(pdf)) == 0
    assert "Ayar dosyası okunamadı" in capsys.readouterr().err
