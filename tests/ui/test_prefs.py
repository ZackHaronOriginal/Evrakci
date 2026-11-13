import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtWidgets import QApplication, QMainWindow

from evrakci.ui.prefs import Prefs


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def path(tmp_path, app):
    return tmp_path / "ui.ini"


def test_defaults(path):
    p = Prefs(path)
    assert (p.last_tab(), p.density(), p.text_size(), p.theme()) == (0, "normal", 100, "system")
    assert p.reduced_motion() is None
    assert p.recent_jobs() == [] and p.recent_folders() == []
    assert p.export_folder() == "" and p.thumbnail_size() == 160
    assert p.zoom("kontrol") == 100 and p.splitter_sizes("x") == []
    assert p.header_state("t").isEmpty()


def test_round_trip_every_key(path):
    p = Prefs(path)
    p.set_last_tab(3)
    p.set_splitter_sizes("kontrol", [200, 800])
    p.set_header_state("degerler", QByteArray(b"abc"))
    p.set_zoom("kontrol", 175)
    p.set_thumbnail_size(240)
    p.set_density("Geniş")
    p.set_text_size(130)
    p.set_theme("dark")
    p.set_reduced_motion(True)
    p.add_recent_job("is-1")
    p.add_recent_folder("/tmp/a")
    p.set_export_folder("/tmp/out")
    q = Prefs(path)
    assert q.last_tab() == 3
    assert q.splitter_sizes("kontrol") == [200, 800]
    assert bytes(q.header_state("degerler")) == b"abc"
    assert q.zoom("kontrol") == 175 and q.thumbnail_size() == 240
    assert q.density() == "comfortable" and q.text_size() == 130 and q.theme() == "dark"
    assert q.reduced_motion() is True
    assert q.recent_jobs() == ["is-1"] and q.recent_folders() == ["/tmp/a"]
    assert q.export_folder() == "/tmp/out"


def test_reduced_motion_false_and_none(path):
    p = Prefs(path)
    p.set_reduced_motion(False)
    assert Prefs(path).reduced_motion() is False
    p.set_reduced_motion(None)
    assert Prefs(path).reduced_motion() is None


@pytest.mark.parametrize(
    ("setter", "bad"),
    [("set_density", "dar"), ("set_text_size", 110), ("set_theme", "mor"), ("set_zoom", 5000),
     ("set_thumbnail_size", 1), ("set_last_tab", -1), ("set_reduced_motion", "evet")],
)
def test_invalid_values_rejected(path, setter, bad):
    p = Prefs(path)
    args = ("k", bad) if setter == "set_zoom" else (bad,)
    with pytest.raises(ValueError):
        getattr(p, setter)(*args)


def test_invalid_splitter_rejected(path):
    with pytest.raises(ValueError):
        Prefs(path).set_splitter_sizes("k", [-1])


def test_corrupt_file_values_fall_back(path):
    path.write_text(
        "[look]\ndensity=zzz\ntext_size=abc\ntheme=neon\nreduced_motion=maybe\n"
        "[ui]\nlast_tab=900\n[zoom]\nk=-4\n[splitters]\nk=a, b\n",
        encoding="utf-8",
    )
    p = Prefs(path)
    assert (p.density(), p.text_size(), p.theme()) == ("normal", 100, "system")
    assert p.reduced_motion() is None and p.last_tab() == 0
    assert p.zoom("k") == 100 and p.splitter_sizes("k") == []


def test_mru_dedupe_order_and_cap(path):
    p = Prefs(path)
    for i in range(12):
        p.add_recent_job(f"j{i}")
    p.add_recent_job("j5")
    jobs = Prefs(path).recent_jobs()
    assert len(jobs) == 10 and jobs[0] == "j5" and jobs.count("j5") == 1
    assert jobs[1] == "j11"
    p.add_recent_folder("/a")
    p.add_recent_folder("/b")
    p.add_recent_folder("/a")
    assert p.recent_folders() == ["/a", "/b"]
    p.clear_recent()
    assert p.recent_jobs() == [] and p.recent_folders() == []


def test_changed_signal(path):
    p = Prefs(path)
    seen: list[str] = []
    p.changed.connect(seen.append)
    p.set_theme("light")
    p.add_recent_job("x")
    assert seen == ["look/theme", "recent/jobs"]


def test_window_geometry_round_trip(path, app):
    p = Prefs(path)
    assert not p.restore_window(QMainWindow())
    w = QMainWindow()
    w.resize(777, 555)
    w.move(40, 50)
    p.save_window(w)
    w2 = QMainWindow()
    assert Prefs(path).restore_window(w2)
    assert (w2.width(), w2.height()) == (777, 555)
    assert not Prefs(path).window_maximized()
    w.setWindowState(w.windowState().WindowMaximized)
    p.save_window(w)
    assert Prefs(path).window_maximized()


def test_native_title_bar_round_trip(path):
    p = Prefs(path)
    assert p.native_title_bar() is False
    p.set_native_title_bar(True)
    assert Prefs(path).native_title_bar() is True
    p.set_native_title_bar(False)
    assert Prefs(path).native_title_bar() is False
    with pytest.raises(ValueError):
        p.set_native_title_bar("evet")
