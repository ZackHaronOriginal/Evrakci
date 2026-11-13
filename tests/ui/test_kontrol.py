import time

import pytest
from fakes import job_from_kinds
from PIL import Image
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtGui import QColor

from evrakci.pipeline.cuts import cut_kinds
from evrakci.pipeline.store import JobStore
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol import KontrolScreen
from evrakci.ui.thumbnails import ThumbnailService
from evrakci.ui.timeline import Roles, TimelineModel


class Renderer:
    def __init__(self):
        self.calls = []

    def __call__(self, pid, height):
        self.calls.append(pid)
        return Image.new("RGB", (70, height), "white")


def _controller(tmp_path, spec):
    job = job_from_kinds(spec)
    store = JobStore(tmp_path)
    store.save(job)
    return JobController(store, job)


def _screen(qtbot, ctl, renderer=None):
    service = ThumbnailService(renderer or Renderer(), height=100)
    screen = KontrolScreen(ctl, service, templates=dict)
    qtbot.addWidget(screen)
    screen.resize(1366, 640)
    return screen


def test_cut_role_matches_core_cut_kinds(qapp, tmp_path):
    ctl = _controller(tmp_path, {"a": "ppqpppep"})
    ctl.apply_filter(["a/3", "a/4", "a/5", "a/6"], 2)
    ctl.add_cut("a/7")
    model = TimelineModel(ctl)
    kinds = cut_kinds(ctl.job)
    for row, pid in enumerate(ctl.job.ordered_page_ids()):
        index = model.index(row)
        assert model.data(index, Roles.PID) == pid
        assert model.data(index, Roles.CUT) == kinds.get(pid)
    separator = model.index(2)
    assert model.data(separator, Roles.STATE) == "separator"


def test_selecting_pages_5_to_9_and_applying_a_filter(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "p" * 12})
    screen = _screen(qtbot, ctl)
    view = screen.timeline
    selection = view.selectionModel()
    for row in range(4, 9):
        selection.select(view.model().index(row), QItemSelectionModel.SelectionFlag.Select)
    screen.apply_filter(3)  # A: "Filtre uygula…" asks in a dialog; the number is passed here
    assert ctl.job.filters[-1].page_ids == {f"a/{i}" for i in range(4, 9)}
    assert ctl.job.filters[-1].every_n == 3


@pytest.mark.parametrize("spec,edit,colour", [
    ({"a": "pqpp"}, None, "qr"),
    ({"a": "pppp"}, lambda c: c.add_cut("a/2"), "manual"),
    ({"a": "pppp"}, lambda c: c.apply_filter(["a/0", "a/1", "a/2", "a/3"], 2), "filter"),
])
def test_each_cut_type_paints_its_colour(qtbot, tmp_path, spec, edit, colour):
    ctl = _controller(tmp_path, spec)
    if edit:
        edit(ctl)
    screen = _screen(qtbot, ctl)
    screen.show()
    image = screen.timeline.viewport().grab().toImage()
    wanted = QColor(theme.colour(colour)).rgb()
    found = any(
        image.pixel(x, y) == wanted
        for x in range(0, image.width(), 1)
        for y in range(0, image.height(), 3)
    )
    assert found, colour


def test_dropped_empty_page_is_marked(qapp, tmp_path):
    ctl = _controller(tmp_path, {"a": "pep"})
    ctl.set_drop_empty(True)
    model = TimelineModel(ctl)
    assert model.data(model.index(1), Roles.STATE) == "dropped"


def test_1000_pages_first_paint_is_fast_and_renders_only_visible_pages(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"b1": "p" * 1000})
    renderer = Renderer()
    started = time.perf_counter()
    screen = _screen(qtbot, ctl, renderer)
    screen.show()
    screen.timeline.viewport().repaint()
    assert time.perf_counter() - started < 1.0
    qtbot.wait(200)
    assert 0 < len(set(renderer.calls)) <= 30


def test_side_panel_shows_selected_document_and_merge_removes_manual_cut(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "pppp"})
    ctl.add_cut("a/2")
    screen = _screen(qtbot, ctl)
    screen.timeline.setCurrentIndex(screen.timeline.model().index(2))
    assert "Belge 2" in screen.side.title.text()
    screen.merge_current()  # A: M, the command bar and the inspector's "Diğer" menu
    assert ctl.job.manual_cuts == set()
