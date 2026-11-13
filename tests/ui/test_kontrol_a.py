"""Kontrol as direction A draws it: layout, keys, selection, review, delete, loupe, overview,
inspector, status bar, empty state, persistence and accessible names."""

from fakes import job_from_kinds
from PIL import Image
from PySide6.QtCore import QEvent, QItemSelectionModel, QPoint, QRect, Qt
from PySide6.QtGui import QShortcut
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QLabel,
    QMenu,
    QWidget,
)

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import kontrol_paint, theme
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol import SPLITTER, KontrolScreen
from evrakci.ui.kontrol_actions import SCREEN_SLOTS, KontrolBinder, KontrolStatus
from evrakci.ui.kontrol_empty import KontrolEmpty
from evrakci.ui.kontrol_review import FILE_NAME, ReviewStore
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.thumbnails import ThumbnailService
from evrakci.ui.timeline import Metrics, Roles, TimelineModel, flow

# a: 3 pages | QR | 2 pages | QR | 4 pages | QR | 1 page  -> documents 1..4
SPEC = {"a": "pppqppqppppqp"}


class Renderer:
    def __init__(self):
        self.calls = []

    def __call__(self, pid, height):
        self.calls.append((pid, height))
        return Image.new("RGB", (int(height * 0.7), height), "white")


def _controller(tmp_path, spec=SPEC):
    job = job_from_kinds(spec)
    store = JobStore(tmp_path / "jobs")
    store.save(job)
    return JobController(store, job)


def _screen(qtbot, ctl, renderer=None, size=(1366, 640)):
    service = ThumbnailService(renderer or Renderer(), height=100)
    screen = KontrolScreen(ctl, service, templates=dict)
    qtbot.addWidget(screen)
    screen.resize(*size)
    screen.show()
    return screen


def _window(qtbot, tmp_path, spec=SPEC, show=True):
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds(spec)
    store.save(job)
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.resize(1366, 768)
    window.yukle.open_job(store.load(job.id))
    window.show_tab("kontrol")
    qtbot.wait(1)  # the screen takes over the commands once the window has placed it
    if show:
        window.show()
        window.activateWindow()
        assert QTest.qWaitForWindowActive(window)
    window.kontrol.timeline.setFocus()
    return window


def _key(window, key, mods=Qt.KeyboardModifier.NoModifier):
    QTest.keyClick(QApplication.focusWidget() or window, key, mods)


# -- layout ----------------------------------------------------------------------------------
def test_documents_wrap_whole_and_keep_a_s_gaps(qapp, tmp_path):
    ctl = _controller(tmp_path)
    model = TimelineModel(ctl)
    groups = model.groups()
    assert [g.kind for g in groups] == ["doc", "sep", "doc", "sep", "doc", "sep", "doc"]
    metrics = Metrics.at(100)
    assert (metrics.page_w, metrics.page_h) == (148, 209)  # A's thumbnail at %100
    rects, rows, _height = flow(groups, model._states, metrics, 1000)
    gap = rects[1].left() - rects[0].right() - 1
    assert gap == theme.manager().size("s3")  # pages of one document: 12
    assert rects[3].width() == 48  # the separator tile
    for row in rows:  # a document that fits a row is never split over two rows
        for seg in row.segments:
            group = groups[seg.group]
            if seg.start and group.last - group.first < 5:
                assert seg.first == group.first and seg.last == group.last
    assert len(rows) >= 2


def test_a_document_wider_than_a_row_goes_on_in_the_next_row(qapp, tmp_path):
    ctl = _controller(tmp_path, {"a": "p" * 20})
    model = TimelineModel(ctl)
    rects, rows, _ = flow(model.groups(), model._states, Metrics.at(100), 700)
    assert len(rows) > 1
    assert [s.start for r in rows for s in r.segments] == [True] + [False] * (len(rows) - 1)
    assert all(r.right() <= 700 for r in rects)


def test_guide_tab_sits_left_centre_right_by_cut_type(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "ppppqpppppp"})
    ctl.apply_filter(["a/5", "a/6", "a/7", "a/8"], 2)
    ctl.add_cut("a/9")
    screen = _screen(qtbot, ctl)
    kinds = {g.doc: g.cut for g in screen.model.groups() if g.kind == "doc"}
    assert set(kinds.values()) >= {"filter", "manual"}
    assert kontrol_paint.CUT_ICONS["qr"][0] == "qr-code"
    assert kontrol_paint.guide_tab_size(16, "qr", True).width() > \
        kontrol_paint.guide_tab_size(16, "qr", False).width()  # the reviewed check


# -- selection -----------------------------------------------------------------------------------
def test_rubber_band_click_shift_and_ctrl_select_pages(qtbot, tmp_path):
    ctl = _controller(tmp_path)
    screen = _screen(qtbot, ctl)
    view = screen.timeline
    first, third = view.page_rect(0), view.page_rect(2)
    view.setSelection(QRect(first.center(), third.center()),
                      QItemSelectionModel.SelectionFlag.ClearAndSelect)
    assert screen.selected_rows() == [0, 1, 2]
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=view.page_rect(4).center())
    assert screen.selected_rows() == [4]
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.ShiftModifier, view.page_rect(6).center())
    assert screen.selected_rows() == [4, 5, 6]
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.ControlModifier, view.page_rect(0).center())
    assert screen.selected_rows() == [0, 4, 5, 6]


def test_arrow_home_end_move_the_current_page(qtbot, tmp_path):
    ctl = _controller(tmp_path)
    screen = _screen(qtbot, ctl)
    view = screen.timeline
    view.setFocus()
    QTest.keyClick(view, Qt.Key.Key_Right)
    assert screen.current_row() == 1
    QTest.keyClick(view, Qt.Key.Key_End)
    assert screen.current_row() == screen.model.rowCount() - 1
    QTest.keyClick(view, Qt.Key.Key_Home)
    assert screen.current_row() == 0
    QTest.keyClick(view, Qt.Key.Key_Down)
    assert view.page_rect(screen.current_row()).top() > view.page_rect(0).top()


# -- keys through the window's registry ----------------------------------------------------------
def test_every_kontrol_command_is_wired_and_enabled_with_a_job(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=False)
    for action_id in SCREEN_SLOTS:
        assert window.registry.is_enabled(action_id), action_id
    window.close_job()
    qtbot.wait(1)  # no deleteLater needed: the screen left the tabs
    for action_id in SCREEN_SLOTS:
        if action_id.startswith("kontrol."):
            assert not window.registry.is_enabled(action_id), action_id


def test_one_binder_per_window_and_a_new_job_takes_over(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=False)
    binder = KontrolBinder.for_registry(window.registry)
    assert binder.screen() is window.kontrol
    first = window.kontrol
    window.yukle.open_job(window.store.load("test"))
    qtbot.wait(1)
    assert window.kontrol is not first
    assert KontrolBinder.for_registry(window.registry) is binder
    assert binder.screen() is window.kontrol
    calls = []
    window.kontrol.select_all = lambda: calls.append("all")
    window.registry.action("kontrol.tumunu_sec").trigger()
    assert calls == ["all"]  # one connection: the action fired once


def test_n_u_enter_and_ctrl_arrows_move_between_documents(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.model.set_checks({3: ["eksik sayfa"]})
    screen.strip.check_rows = [(screen.model.first_row(3), 3)]
    _key(window, Qt.Key.Key_N)
    assert screen.current_document() == 3
    _key(window, Qt.Key.Key_Right, Qt.KeyboardModifier.ControlModifier)
    assert screen.current_document() == 4
    _key(window, Qt.Key.Key_Left, Qt.KeyboardModifier.ControlModifier)
    assert screen.current_document() == 3
    _key(window, Qt.Key.Key_Return)  # Belgeyi onayla: reviewed, then the next document
    assert screen.current_document() == 4
    assert 3 in screen.model.reviewed
    assert "Geri al: Belgeyi onayla" in window.registry.action("app.geri_al").toolTip()
    screen.go_to_document(2)
    _key(window, Qt.Key.Key_U)  # next not reviewed after 2 is 4 (3 is reviewed)
    assert screen.current_document() == 4
    _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert 3 not in screen.model.reviewed


def test_ctrl_a_selects_all_and_esc_clears(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    _key(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert len(screen.timeline.selectionModel().selectedIndexes()) == screen.model.rowCount()
    _key(window, Qt.Key.Key_Escape)
    assert not screen.timeline.selectionModel().selectedIndexes()


def test_space_opens_the_loupe_over_the_timeline_and_esc_closes_it(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.go_to_row(4)
    _key(window, Qt.Key.Key_Space)
    loupe = screen.loupe()
    assert loupe.is_open() and loupe.index() == 4
    assert loupe.parentWidget() is screen.work_area  # overview and inspector stay
    assert screen.strip.isVisible() and screen.side.isVisible()
    assert window.zoom_controller() is loupe.zoom
    QTest.keyClick(loupe, Qt.Key.Key_Right)
    assert screen.current_row() == 5  # the timeline follows the loupe
    _key(window, Qt.Key.Key_Escape)
    qtbot.waitUntil(lambda: not loupe.isVisible(), timeout=2000)
    assert window.zoom_controller() is screen.zoom
    assert screen.timeline.selectionModel().selectedIndexes()  # Esc closed, kept selection


def test_k_r_shift_r_and_m_edit_through_keys(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.go_to_row(1)
    _key(window, Qt.Key.Key_K)
    assert "a/1" in ctl.job.manual_cuts
    assert screen.side.history_rows[0].text.text() == "Kesim eklendi, sayfa 2"
    _key(window, Qt.Key.Key_R)
    assert ctl.job.rotations["a/1"] == 90
    _key(window, Qt.Key.Key_R, Qt.KeyboardModifier.ShiftModifier)
    assert ctl.job.rotations.get("a/1", 0) == 0
    _key(window, Qt.Key.Key_M)
    assert "a/1" not in ctl.job.manual_cuts


# -- delete ----------------------------------------------------------------------------------
def test_delete_names_the_count_is_undoable_and_never_silent(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    ctl = window.controller()
    screen.timeline.select_rows(4, 5, 5)  # all of document 2
    action = window.registry.action("kontrol.sil")
    assert action.text().replace("&", "") == "2 sayfayı sil"
    assert "2 sayfayı sil" in action.toolTip()
    _key(window, Qt.Key.Key_Delete)
    assert {"a/4", "a/5"} <= ctl.job.deleted
    assert "Belge 2: bütün sayfaları silinecek" in window.toaster.current_text()
    assert action.text().replace("&", "") == "2 sayfayı geri getir"
    _key(window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert not ctl.job.deleted


def test_deleting_a_single_page_toasts_with_undo(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.go_to_row(0)
    screen.toggle_delete()
    assert window.controller().job.deleted == {"a/0"}
    assert window.toaster.current_text() == "Sayfa 1 silinecek."
    index = screen.model.index(0)
    assert index.data(Roles.STATE) == "deleted"
    assert "silinecek" in index.data(Qt.ItemDataRole.AccessibleTextRole)
    screen.toggle_delete()  # Del again restores
    assert not window.controller().job.deleted


# -- context menu --------------------------------------------------------------------------------
def test_context_menu_lists_a_s_items_with_their_keys(qtbot, tmp_path):
    window = _window(qtbot, tmp_path)
    screen = window.kontrol
    screen.timeline.select_rows(7, 9, 8)
    screen._context_menu(screen.timeline.page_rect(8).center())
    menu = screen.menu
    assert isinstance(menu, QMenu)
    texts = [a.text().replace("&", "") for a in menu.actions() if not a.isSeparator()]
    names = [t for t in texts if t]
    assert names[:2] == ["Burada kes", "Önceki belgeyle birleştir"]
    assert "Şablon uygula" in names and "Filtre uygula…" in names
    assert names[-1] == "3 sayfayı sil"
    keys = {a.text().replace("&", ""): a.shortcut().toString() for a in menu.actions()}
    assert keys["Burada kes"] == "K" and keys["3 sayfayı sil"] == "Del"
    delete = menu.actions()[-1]
    assert menu.defaultAction() is delete  # drawn in `danger` (QMenu::item:default)
    menu.setStyleSheet(theme.manager().stylesheet())  # what the app applies at start
    menu.show()
    image = menu.grab().toImage()
    rect = menu.actionGeometry(delete)
    danger = theme.manager().color("danger").name()
    assert any(image.pixelColor(x, y).name() == danger
               for y in range(rect.top(), rect.bottom()) for x in range(rect.left(), rect.right()))
    menu.close()


def test_right_click_on_an_unselected_page_selects_it(qtbot, tmp_path):
    ctl = _controller(tmp_path)
    screen = _screen(qtbot, ctl)
    screen.timeline.select_rows(0, 1, 1)
    screen._context_menu(screen.timeline.page_rect(5).center())
    assert screen.selected_rows() == [5]
    names = [a.text().split("\t")[0] for a in screen.menu.actions() if a.text()]
    assert "Sayfayı sil" in names  # without a window the menu still works
    screen.menu.close()


# -- review state --------------------------------------------------------------------------------
def test_approval_is_saved_beside_the_job_and_lost_when_pages_change(qtbot, tmp_path):
    ctl = _controller(tmp_path)
    reviews = ReviewStore(ctl)
    document = ctl.documents()[1]
    assert reviews.set_reviewed([document])
    assert (tmp_path / "jobs" / "test" / FILE_NAME).is_file()
    assert ReviewStore(ctl).reviewed_numbers() == {2}
    ctl.add_cut(document.page_ids[1])  # the document changed: not reviewed any more
    assert ReviewStore(ctl).reviewed_numbers() == set()
    ctl.undo()  # the old pages are back, and so is the approval
    assert ReviewStore(ctl).reviewed_numbers() == {2}
    ctl.undo()  # undoes the approval itself
    assert ReviewStore(ctl).reviewed_numbers() == set()


# -- inspector and status --------------------------------------------------------------------------
def test_inspector_explains_why_a_document_starts_here(qtbot, tmp_path):
    ctl = _controller(tmp_path)
    ctl.apply_filter(["a/7", "a/8", "a/9", "a/10"], 2)
    screen = _screen(qtbot, ctl)
    screen.go_to_row(9)
    side = screen.side
    number = screen.current_document()
    assert side.title.text() == f"Belge {number}"
    assert side.cut_row.value.text() == "Filtre, her 2 sayfada"
    assert side.reason.text() == "QR ayıraç yok, filtre kesti."
    assert side.previous_row.value.text().startswith(f"Belge {number - 1}, ")
    assert side.state_row.value.text() == "İncelenmedi"
    assert side.selection_label.text() == "Seçim: 1 sayfa (10)"
    assert side.filter_button.value.text() == "Her 2 sayfa"
    side.approve_button.click()
    screen.go_to_document(number)
    assert side.state_row.value.text() == "İncelendi"


def test_status_bar_shows_a_s_counts(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=False)
    screen = window.kontrol
    screen.timeline.select_rows(4, 6, 5)
    status = window.status_slot("kontrol").findChild(KontrolStatus, KontrolStatus.NAME)
    assert status.texts()[:3] == ["Belge 2 / 4", "Sayfa 6 / 13", "3 sayfa seçili"]
    assert status.texts()[-1] == "0 / 4 belge incelendi"
    window.close_job()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert status.texts() == ["İşler Yükle sekmesinde açılır (Ctrl+1)"]


def test_overview_has_a_segment_per_document_and_rings_the_view(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"a": "pq" * 120})
    screen = _screen(qtbot, ctl)
    strip = screen.strip
    assert strip.documents == 120
    assert strip.visible is not None and strip.visible[0] == 1
    assert strip.where_text().startswith("Belge 1–")
    x = strip.track_rect().right() - 1
    QTest.mouseClick(strip, Qt.MouseButton.LeftButton, pos=QPoint(int(x), strip.height() // 2))
    assert screen.current_document() == 120
    assert strip.visible[1] == 120


# -- zoom, thumbnails, persistence ---------------------------------------------------------------
def test_status_bar_zoom_sets_thumbnail_size_and_is_remembered(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=False)
    screen = window.kontrol
    assert window.zoom_controller("kontrol") is screen.zoom
    assert window.zoom_slider.isVisibleTo(window)
    window.registry.action("app.yakinlastir").trigger()
    assert screen.timeline.zoom == 110
    assert screen.timeline.metrics.page_w == round(148 * 1.1)
    qtbot.waitUntil(lambda: screen.thumbnails.height == screen.timeline.thumbnail_height(),
                    timeout=2000)
    assert window.prefs.zoom("kontrol") == 110
    window.registry.action("app.sigdir").trigger()
    assert screen.timeline.zoom == 100
    window.registry.action("app.yakinlastir").trigger()
    window.yukle.open_job(window.store.load("test"))  # a new screen starts at the saved size
    assert window.kontrol.timeline.zoom == 110


def test_splitter_is_named_and_restored(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=False)
    assert window.kontrol.body.objectName() == SPLITTER
    window.prefs.set_splitter_sizes(SPLITTER, [900, 360])
    window.yukle.open_job(window.store.load("test"))
    assert window.kontrol.body.sizes()[1] == 360 or window.kontrol.body.sizes()[1] > 300


def test_thumbnails_re_render_at_the_new_height_and_keep_the_old_meanwhile(qtbot):
    renderer = Renderer()
    service = ThumbnailService(renderer, height=100)
    service.request("a/0")
    qtbot.waitUntil(lambda: service.is_current("a/0"), timeout=5000)
    service.set_height(200)
    assert "a/0" in service.cache and not service.is_current("a/0")  # still drawable
    service.request("a/0")
    qtbot.waitUntil(lambda: service.is_current("a/0"), timeout=5000)
    assert service.cache["a/0"].height() == 200
    assert [h for _p, h in renderer.calls] == [100, 200]


def test_1000_pages_wrap_and_paint_only_what_is_in_view(qtbot, tmp_path):
    ctl = _controller(tmp_path, {"b1": ("p" * 9 + "q") * 100})
    renderer = Renderer()
    screen = _screen(qtbot, ctl, renderer)
    screen.timeline.viewport().repaint()
    qtbot.wait(200)
    assert 0 < len({p for p, _h in renderer.calls}) <= 30
    screen.go_to_row(990)
    qtbot.wait(100)
    assert screen.strip.visible[1] == 100


# -- empty state and accessible names ----------------------------------------------------------
def test_empty_state_says_what_goes_here_and_offers_the_way(qtbot):
    went, made = [], []
    page = KontrolEmpty(lambda: went.append(1), lambda: made.append(1),
                        lambda: [("Ekim işleri", "212 sayfa, dün", lambda: made.append(2))])
    qtbot.addWidget(page)
    page.show()
    assert page.title.text() == "Henüz açık iş yok"
    assert page.text.text() == "Kesimleri görmek için Yükle'den bir iş açın."
    page.go_button.click()
    page.new_button.click()
    rows = [w for w in page.card.findChildren(QAbstractButton) if w.isVisible()]
    assert len(rows) == 1 and "Ekim işleri" in rows[0].accessibleName()
    rows[0].click()
    assert went == [1] and made == [1, 2]


def test_every_control_has_an_accessible_name(qtbot, tmp_path):
    window = _window(qtbot, tmp_path, show=False)
    screen = window.kontrol
    screen.timeline.select_rows(0, 1, 1)
    for widget in screen.findChildren(QWidget):
        if not widget.isVisibleTo(screen):
            continue
        focusable = widget.focusPolicy() != Qt.FocusPolicy.NoFocus
        if isinstance(widget, QAbstractButton) or (focusable and not isinstance(widget, QLabel)
                                                   and widget.parent() is not None
                                                   and widget.objectName() not in (
                                                       "qt_scrollarea_viewport",)):
            name = widget.accessibleName() or getattr(widget, "text", lambda: "")()
            assert name, f"{type(widget).__name__} {widget.objectName()}"
    assert not screen.findChildren(QShortcut)  # every key is a registry action now
    assert screen.timeline.accessibleName() == "Sayfalar"
    assert screen.side.accessibleName() == "Belge ayrıntısı"
    assert screen.strip.accessibleName().startswith("Tüm iş: ")

