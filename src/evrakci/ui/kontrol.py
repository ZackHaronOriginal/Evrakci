"""The Kontrol screen (direction A): check and fix how the pile was split, with the keyboard.

Above, the whole job as a row of segments with the part in view ringed (OverviewStrip). Below,
the timeline: documents under manila guide tabs, an orange rider where a human has to look
(TimelineView). On the right, the inspector of the current document (Inspector), hidden with
F9. Space opens the loupe over the timeline (the overview and the inspector stay), Esc closes it.

Keys (actions.py, context "kontrol"): K cut here, M merge, R / Shift+R rotate, Del delete or
restore (undoable, never confirmed, the label names the count), F filter, T template, Enter
approve the document and go on, N / Shift+N next / previous kontrol, U next not reviewed,
Ctrl+Right / Ctrl+Left next / previous document, Ctrl+G go to, Ctrl+A select all, Esc clear
the selection (or close the loupe), Space preview. In the timeline: arrows, Home / End,
PgUp / PgDn, Shift to extend; drag on the background for a rubber band.

The window gives the screen its command bar, status-bar slot, zoom slider (thumbnail size),
toasts and prefs once the screen is placed in it; on its own (tests) it works without them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from functools import partial

import shiboken6
from PySide6.QtCore import QEvent, QItemSelectionModel, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMenu, QSplitter, QVBoxLayout, QWidget

from evrakci.pipeline.export import plan_export
from evrakci.pipeline.templates.model import Template
from evrakci.ui import theme
from evrakci.ui.controller import JobController
from evrakci.ui.kontrol_actions import (
    KontrolBinder,
    KontrolStatus,
    context_menu,
    fallback_action,
    label_delete,
)
from evrakci.ui.kontrol_dialogs import FilterDialog, GoToDialog
from evrakci.ui.kontrol_inspector import Change, DocumentInfo, Inspector, SelectionInfo
from evrakci.ui.kontrol_overview import OverviewStrip
from evrakci.ui.kontrol_paint import CUT_ICONS, CUT_WORDS
from evrakci.ui.kontrol_review import ReviewStore
from evrakci.ui.loupe import Loupe
from evrakci.ui.thumbnails import ThumbnailService, job_renderer, to_qimage
from evrakci.ui.timeline import ZOOM_MAX, ZOOM_MIN, ZOOM_STEP, Roles, TimelineModel, TimelineView
from evrakci.ui.zoomview import ZoomController

KIND_TEXT = CUT_WORDS  # kept for callers of the old name
SPLITTER = "kontrol.govde"
ZOOM_KEY = "kontrol"
ZOOM_TARGET = "Küçük resim boyutu"
REASONS = {"qr": "QR ayıraç sayfası ayırdı.", "filter": "QR ayıraç yok, filtre kesti.",
           "manual": "Elle kesildi.", "start": "İşin ilk belgesi."}
THUMB_DELAY_MS = 150  # re-render thumbnails once zooming pauses


def _sentence(checks: list[str]) -> str:
    text = ", ".join(checks)
    return (text[:1].upper() + text[1:] + ".") if text else ""


class KontrolScreen(QWidget):
    open_values = Signal(int)  # document number

    def __init__(
        self,
        controller: JobController,
        thumbnails: ThumbnailService | None,
        templates: Callable[[], Mapping[str, Template]] = dict,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("page")
        self.setAccessibleName("Kontrol")
        self.controller = controller
        self.templates = templates
        self.thumbnails = thumbnails
        self.model = TimelineModel(controller, templates)
        self.reviews = ReviewStore(controller, self)
        self.registry = None  # the window's action registry, once the screen is placed
        self._window: QWidget | None = None
        self._every_n = 2
        self._template_choice: str | None = None
        self._history: list[tuple[int, Change]] = []
        self._loupe: Loupe | None = None
        self._hires = None
        self._kept: tuple[list[str], str | None] = ([], None)
        self._rotations = dict(controller.job.rotations)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.body = QSplitter(Qt.Orientation.Horizontal)
        self.body.setObjectName(SPLITTER)
        self.body.setChildrenCollapsible(False)
        self.body.setHandleWidth(theme.manager().size("s1"))
        work = QWidget()
        work.setObjectName("kontrolWork")
        column = QVBoxLayout(work)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(0)
        self.strip = OverviewStrip()
        self.strip.jump.connect(self.go_to_document)
        column.addWidget(self.strip)
        self.work_area = QWidget()
        area = QVBoxLayout(self.work_area)
        area.setContentsMargins(0, 0, 0, 0)
        self.timeline = TimelineView(thumbnails)
        self.timeline.setModel(self.model)
        self.timeline.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.timeline.customContextMenuRequested.connect(self._context_menu)
        self.timeline.doubleClicked.connect(lambda index: self.open_loupe(index.row()))
        area.addWidget(self.timeline)
        column.addWidget(self.work_area, 1)
        self.side = Inspector(self._fill_more)
        self.side.approve.connect(self.approve_document)
        self.side.open_values.connect(self.open_in_values)
        self.side.template_row.connect(self._template_menu)
        self.side.filter_row.connect(lambda: self.apply_filter())
        self.body.addWidget(work)
        self.body.addWidget(self.side)
        self.body.setStretchFactor(0, 1)
        self.body.setStretchFactor(1, 0)
        inspector = theme.manager().size("inspector-w")
        self.body.setSizes([max(400, 1366 - 16 - inspector), inspector])
        root.addWidget(self.body)

        self.zoom = self._make_zoom(None)
        self._thumb_timer = QTimer(self)
        self._thumb_timer.setSingleShot(True)
        self._thumb_timer.setInterval(THUMB_DELAY_MS)
        self._thumb_timer.timeout.connect(self._rerender)

        self.model.modelAboutToBeReset.connect(self._remember_selection)
        self.model.modelReset.connect(self._restore_selection)
        selection = self.timeline.selectionModel()
        selection.selectionChanged.connect(self._selection_changed)
        selection.currentChanged.connect(self._current_changed)
        self.timeline.verticalScrollBar().valueChanged.connect(self._scrolled)
        controller.job_changed.connect(self._job_changed)
        controller.undo_stack.indexChanged.connect(self._undo_moved)
        self.reviews.changed.connect(self._reviews_changed)
        if self.model.rowCount():  # focus the first page without selecting it
            selection.setCurrentIndex(self.model.index(0),
                                      QItemSelectionModel.SelectionFlag.NoUpdate)
        if thumbnails is not None:
            thumbnails.set_height(self.timeline.thumbnail_height())
        self._job_changed()
        self._built = True
        if self.reviews.error:
            controller.status.emit(self.reviews.error)

    # -- the window ---------------------------------------------------------------------------
    def event(self, event) -> bool:
        if (event.type() in (QEvent.Type.ParentChange, QEvent.Type.Show)
                and getattr(self, "_built", False)):
            self._attach()
        return super().event(event)

    def _attach(self) -> None:
        window = self.window()
        registry = getattr(window, "registry", None)
        if window is self or registry is None or self._window is window:
            return
        self._window = window
        self.registry = registry
        self.binder = KontrolBinder.for_registry(registry)
        self.binder.attach(self)
        QTimer.singleShot(0, self._sync_binder)  # once the window names this screen
        prefs = getattr(window, "prefs", None)
        if prefs is not None:
            self.zoom = self._make_zoom(prefs)
            self.timeline.set_zoom(self.zoom.zoom())
            self._rerender()
        if hasattr(window, "register_zoom"):
            window.register_zoom("kontrol", self.zoom, ZOOM_TARGET)
        if hasattr(window, "status_slot"):
            self.status = KontrolStatus.in_slot(window.status_slot("kontrol"))
        self.destroyed.connect(partial(_forget_screen, window))
        self._update_status()
        self._selection_changed()

    def _sync_binder(self) -> None:
        binder = getattr(self, "binder", None)
        if binder is not None and shiboken6.isValid(binder):
            binder.sync()
            if binder.screen() is None and self._window is not None:
                _forget_screen(self._window)  # the job was closed

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._sync_binder()

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        # closing the job hides the screen; once the window has let it go, its commands go off
        QTimer.singleShot(0, self._sync_binder)

    def _make_zoom(self, prefs) -> ZoomController:
        old = getattr(self, "zoom", None)
        if old is not None:
            self.timeline.removeEventFilter(old)
            self.timeline.viewport().removeEventFilter(old)
            old.deleteLater()
        zoom = ZoomController(self.timeline, prefs, ZOOM_KEY, ZOOM_MIN, ZOOM_MAX, ZOOM_STEP,
                              lambda: 100)
        zoom.zoom_changed.connect(self.set_zoom)
        return zoom

    def set_zoom(self, percent: int) -> None:
        """Thumbnail size (status-bar slider, Ctrl+wheel, Ctrl+plus / minus / 0)."""
        self.timeline.set_zoom(percent)
        self._thumb_timer.start()
        self._scrolled()

    def _rerender(self) -> None:
        if self.thumbnails is not None:
            self.thumbnails.set_height(self.timeline.thumbnail_height())
        self.timeline.viewport().update()

    def _toast(self, text: str, undo: bool = True) -> None:
        toaster = getattr(self._window, "toaster", None)
        if toaster is not None:
            toaster.show(text, "Geri al" if undo else None,
                         self.controller.undo if undo else None)
        else:
            self.controller.status.emit(text)

    # -- reading the state --------------------------------------------------------------------
    def selected_rows(self) -> list[int]:
        rows = sorted(i.row() for i in self.timeline.selectionModel().selectedIndexes())
        if not rows and self.timeline.currentIndex().isValid():
            rows = [self.timeline.currentIndex().row()]
        return rows

    def selected_ids(self) -> list[str]:
        return [self.model.page_id(r) for r in self.selected_rows()]

    def current_row(self) -> int:
        index = self.timeline.currentIndex()
        return index.row() if index.isValid() else -1

    def current_document(self) -> int:
        index = self.timeline.currentIndex()
        if not index.isValid():
            return 0
        number = index.data(Roles.DOC)
        if number:
            return number
        for group in self.model.groups():  # a page to delete belongs to its document
            if group.first <= index.row() <= group.last:
                return group.doc
        return 0

    def _pages(self, ids: list[str]) -> list[str]:
        job = self.controller.job
        return [pid for pid in ids if not job.pages[pid].is_separator]

    def _span(self, ids: list[str]) -> str:
        job = self.controller.job
        positions = sorted(job.position_of(pid) for pid in ids)
        if len(positions) == 1:
            return f"sayfa {positions[0]}"
        return f"sayfa {positions[0]}–{positions[-1]}"

    def _remember(self, icon: str, text: str) -> None:
        self._history.insert(0, (self.controller.undo_stack.index(),
                                 Change(icon, text, datetime.now().strftime("%H:%M"))))
        del self._history[10:]
        self.side.set_history([c for _, c in self._history])

    def _undo_moved(self, index: int) -> None:
        kept = [(i, c) for i, c in self._history if i <= index]
        if len(kept) != len(self._history):
            self._history = kept
            self.side.set_history([c for _, c in kept])

    # -- edits --------------------------------------------------------------------------------
    def apply_filter(self, every_n: int | None = None) -> None:
        """F, Filtre uygula…: asks every how many pages unless `every_n` is given."""
        ids = self._pages(self.selected_ids())
        if not ids:
            self.controller.status.emit("Önce sayfaları seçin.")
            return
        if every_n is None:
            dialog = FilterDialog(len(ids), self._every_n, self)
            if not dialog.exec():
                self.timeline.setFocus()
                return
            every_n = dialog.value()
            self.timeline.setFocus()
        self._every_n = every_n
        if self.controller.apply_filter(ids, every_n):
            self._remember("funnel", f"Filtre her {every_n} sayfa, {self._span(ids)}")

    def apply_template(self, template_id: str | None = None) -> None:
        """T: the template the inspector shows (or `template_id`) on the selected pages."""
        templates = self.templates()
        template_id = template_id or self._template_for_selection()
        ids = self.selected_ids()
        if not templates:
            self.controller.status.emit("Önce Şablonlar sekmesinde bir şablon oluşturun.")
            return
        if not template_id or template_id not in templates or not ids:
            self.controller.status.emit("Önce sayfaları ve bir şablonu seçin.")
            return
        self._template_choice = template_id
        if self.controller.apply_template(ids, template_id):
            self._remember("stamp", f"{templates[template_id].name} uygulandı, "
                                    f"{len(ids)} sayfa")

    def toggle_cut(self) -> None:
        """K: cut before the current page, or remove the cut that is there."""
        index = self.timeline.currentIndex()
        if not index.isValid():
            return
        pid = index.data(Roles.PID)
        position = index.row() + 1
        if pid in self.controller.job.manual_cuts:
            if self.controller.remove_cut(pid):
                self._remember("scissors", f"Kesim kaldırıldı, sayfa {position}")
        elif self.controller.add_cut(pid):
            self._remember("scissors", f"Kesim eklendi, sayfa {position}")

    def rotate_selected(self, degrees: int = 90) -> None:
        """R / Shift+R: rotate the selected pages; one undo step for the whole selection."""
        ids = self._pages(self.selected_ids())
        if not ids:
            return
        if self.controller.run("Döndür", lambda job: [job.rotate(pid, degrees) for pid in ids]):
            side = "sağa" if degrees > 0 else "sola"
            what = (f"Sayfa {self.controller.job.position_of(ids[0])}" if len(ids) == 1
                    else f"{len(ids)} sayfa")
            self._remember("rotate-cw" if degrees > 0 else "rotate-ccw",
                           f"{what} {side} döndürüldü")

    def toggle_delete(self) -> None:
        """Del: delete the selected pages, or restore them when all are already deleted.

        Undoable instead of confirmed; a toast offers "Geri al" and says so when a document
        loses all its pages, so nothing disappears silently."""
        ids = self._pages(self.selected_ids())
        if not ids:
            if self.selected_ids():
                self.controller.status.emit("Ayraç sayfaları zaten dışa aktarılmaz. "
                                            "Kesimi kaldırmak için M.")
            return
        job = self.controller.job
        restore = all(pid in job.deleted for pid in ids)
        if restore:
            if self.controller.run("Sayfayı geri getir",
                                   lambda j: [j.undelete_page(p) for p in ids]):
                text = (f"Sayfa {job.position_of(ids[0])} geri getirildi" if len(ids) == 1
                        else f"{len(ids)} sayfa geri getirildi")
                self._remember("undo-2", text)
            return
        targets = [pid for pid in ids if pid not in job.deleted]
        emptied = [n for n, d in enumerate(self.controller.documents(), start=1)
                   if set(d.page_ids) <= set(targets)]
        label = "Sayfayı sil" if len(targets) == 1 else f"{len(targets)} sayfayı sil"
        if not self.controller.run(label, lambda j: [j.delete_page(p) for p in targets]):
            return
        text = (f"Sayfa {job.position_of(targets[0])} silinecek" if len(targets) == 1
                else f"{len(targets)} sayfa silinecek")
        self._remember("trash-2", text)
        if emptied:
            names = ", ".join(f"Belge {n}" for n in emptied)
            self._toast(f"{names}: bütün sayfaları silinecek, belge dışa aktarılmayacak.")
        else:
            self._toast(f"{text}.")

    def merge_current(self) -> None:
        """M: join the current document to the one before (removes the cut between them)."""
        number = self.current_document()
        if not number:
            return
        document = self.controller.documents()[number - 1]
        first = document.page_ids[0]
        kind = self.controller.cut_kinds().get(first)
        done = False
        if kind == "manual":
            done = self.controller.remove_cut(first)
        elif kind == "qr":
            ordered = self.controller.job.ordered_page_ids()
            before = ordered[: ordered.index(first)]
            separator = next(pid for pid in reversed(before)
                             if self.controller.job.pages[pid].is_separator)
            done = self.controller.remove_cut(separator)
        elif kind == "filter":
            self.controller.status.emit("Bu kesimi filtre yaptı; filtreyi değiştirin (F).")
        else:
            self.controller.status.emit("İlk belgenin öncesi yok.")
        if done:
            self._remember("merge", f"Belge {number}, Belge {number - 1} ile birleşti")
            self._toast(f"Belge {number}, Belge {number - 1} ile birleştirildi.")

    def approve_document(self) -> None:
        """Enter, Belgeyi onayla: the document is İncelendi; go on to the next one."""
        number = self.current_document()
        if not number:
            self.controller.status.emit("Önce bir sayfa seçin.")
            return
        documents = self.controller.documents()
        if self.reviews.set_reviewed([documents[number - 1]]):
            self._remember("circle-check", f"Belge {number} onaylandı")
        if number < len(documents):
            self.go_to_document(number + 1)
        else:
            self.controller.status.emit(f"Belge {number} onaylandı; bu son belge.")

    def open_in_values(self) -> None:
        number = self.current_document()
        if number:
            self.open_values.emit(number)

    # -- moving around ------------------------------------------------------------------------
    def go_to_row(self, row: int) -> None:
        if not 0 <= row < self.model.rowCount():
            return
        index = self.model.index(row)
        self.timeline.setCurrentIndex(index)
        self.timeline.scrollTo(index, TimelineView.ScrollHint.EnsureVisible)
        if self._loupe is not None and self._loupe.is_open():
            self._loupe.set_index(row)

    def go_to_document(self, number: int) -> None:
        row = self.model.first_row(number)
        if row >= 0:
            self.go_to_row(row)

    def go_to_page(self, position: int) -> None:
        self.go_to_row(position - 1)

    def jump_document(self, step: int) -> None:
        """Ctrl+Right / Ctrl+Left: first page of the next / previous document."""
        count = len(self.controller.documents())
        here = self.current_document()
        if not count:
            return
        target = (1 if step > 0 else count) if not here else max(1, min(count, here + step))
        if target == here:
            edge = "son" if step > 0 else "ilk"
            self.controller.status.emit(f"Bu {edge} belge.")
            return
        self.go_to_document(target)

    def jump_to_check(self, direction: int) -> None:
        """N / Shift+N: the next / previous document that needs a check."""
        numbers = sorted(n for _row, n in self.strip.check_rows)
        if not numbers:
            self.controller.status.emit("Kontrol bekleyen belge yok.")
            return
        here = self.current_document()
        if direction > 0:
            target = next((n for n in numbers if n > here), numbers[0])
        else:
            target = next((n for n in reversed(numbers) if n < here), numbers[-1])
        self.go_to_document(target)

    def next_unreviewed(self) -> None:
        """U: the next document nobody has approved yet (wraps around)."""
        count = len(self.controller.documents())
        reviewed = self.model.reviewed
        here = self.current_document()
        order = [*range(here + 1, count + 1), *range(1, here + 1)]
        target = next((n for n in order if n not in reviewed), 0)
        if not target:
            self.controller.status.emit("Bütün belgeler incelendi.")
            return
        self.go_to_document(target)

    def go_to(self) -> None:
        """Ctrl+G: Belgeye veya sayfaya git…"""
        documents = len(self.controller.documents())
        dialog = GoToDialog(documents, self.model.rowCount(), "belge",
                            max(1, self.current_document()), self)
        if dialog.exec():
            if dialog.kind() == "belge":
                self.go_to_document(dialog.value())
            else:
                self.go_to_page(dialog.value())
        self.timeline.setFocus()

    def select_all(self) -> None:
        self.timeline.selectAll()

    def escape(self) -> None:
        """Esc: close the loupe if it is open, else clear the selection."""
        if self._loupe is not None and self._loupe.is_open():
            self.close_loupe()
            return
        self.timeline.selectionModel().clearSelection()

    # -- loupe --------------------------------------------------------------------------------
    def loupe(self) -> Loupe:
        if self._loupe is None:
            self._loupe = Loupe(self.work_area, getattr(self._window, "prefs", None))
            self._loupe.index_changed.connect(self._loupe_moved)
            self._loupe.closed.connect(self._loupe_closed)
        return self._loupe

    def toggle_loupe(self) -> None:
        """Space: the current page large, or back to the timeline."""
        if self._loupe is not None and self._loupe.is_open():
            self.close_loupe()
        else:
            self.open_loupe()

    def open_loupe(self, row: int | None = None) -> None:
        row = self.current_row() if row is None else row
        if row < 0 or not self.model.rowCount():
            return
        loupe = self.loupe()
        loupe.open(self.model.rowCount(), self._render_page, row, self._loupe_title,
                   kontrol=self._loupe_kontrol, doc_start=self._loupe_doc_start)
        if self._window is not None and hasattr(self._window, "register_zoom"):
            self._window.register_zoom("kontrol", loupe.zoom, "Önizleme")

    def close_loupe(self) -> None:
        if self._loupe is not None:
            self._loupe.close_loupe()

    def _loupe_moved(self, row: int) -> None:
        index = self.model.index(row)
        if self.timeline.currentIndex() != index:
            self.timeline.selectionModel().setCurrentIndex(
                index, QItemSelectionModel.SelectionFlag.ClearAndSelect)

    def _loupe_closed(self, row: int) -> None:
        if self._window is not None and hasattr(self._window, "register_zoom"):
            self._window.register_zoom("kontrol", self.zoom, ZOOM_TARGET)
        self.timeline.scrollTo(self.model.index(row))
        self.timeline.setFocus(Qt.FocusReason.OtherFocusReason)

    def _loupe_title(self, row: int) -> str:
        """The page's place for the loupe's head: "Belge 16, Ekspertiz Raporu, 2. sayfa"."""
        if self.model.state(row) == "separator":
            return "QR ayıraç"
        number = self.model.doc_of_row(row)
        if not number:
            return ""
        rows = self.model.document_rows(number)
        nth = sum(1 for r in rows if r <= row and self.model.state(r) != "separator")
        template = self.model.data(self.model.index(rows.start), Roles.TEMPLATE)
        return ", ".join(p for p in (f"Belge {number}", template, f"{nth}. sayfa") if p)

    def _loupe_kontrol(self, row: int) -> bool:
        """The rider in the loupe's head: the page's document needs a check."""
        return bool(self.model.data(self.model.index(row), Roles.CHECK))

    def _loupe_doc_start(self, row: int) -> bool:
        """A gap before a document's first page in the loupe's strip."""
        number = self.model.doc_of_row(row)
        return bool(number) and self.model.document_rows(number).start == row

    def _render_page(self, row: int, size: QSize) -> QPixmap:
        """A page for the loupe: the cached thumbnail for small sizes, else rendered from the
        batch PDF at the resolution `size` needs."""
        pid = self.model.page_id(row)
        image = None
        if size.height() <= 300 and self.thumbnails is not None:
            image = self.thumbnails.cache.get(pid)
        if image is None:
            try:
                if self._hires is None:
                    job, store = self.controller.job, self.controller.store
                    self._hires = job_renderer(job, lambda: store.batch_files(job))
                image = to_qimage(self._hires(pid, size.height()))
            except Exception:  # no PDF (or unreadable): the thumbnail renderer, else paper
                try:
                    if self.thumbnails is None:
                        raise LookupError(pid)
                    image = to_qimage(self.thumbnails.renderer(pid, size.height()))
                except Exception:
                    pixmap = QPixmap(size.width() or 1, size.height() or 1)
                    pixmap.fill(theme.manager().color("paper"))
                    return pixmap
        pixmap = QPixmap.fromImage(image)
        if pixmap.size() != size:
            pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
        return pixmap

    # -- menus --------------------------------------------------------------------------------
    def _action(self, action_id: str):
        if self.registry is not None:
            return self.registry.action(action_id)
        return fallback_action(self, action_id, self)

    def _context_menu(self, pos: QPoint) -> None:
        index = self.timeline.indexAt(pos)
        selection = self.timeline.selectionModel()
        if index.isValid() and not selection.isSelected(index):
            selection.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
        elif not index.isValid():
            index = self.timeline.currentIndex()
            if not index.isValid():
                return
            pos = self.timeline.visualRect(index).center()
        elif index != self.timeline.currentIndex():
            selection.setCurrentIndex(index, QItemSelectionModel.SelectionFlag.NoUpdate)
        self.menu = context_menu(self, self._action, self)
        self.menu.popup(self.timeline.viewport().mapToGlobal(pos))

    def _fill_more(self, menu: QMenu) -> None:
        for action_id in ("kontrol.birlestir", "kontrol.onceki_belge", "kontrol.sonraki_belge",
                          "kontrol.sonraki_incelenmemis"):
            menu.addAction(self._action(action_id))

    def _template_menu(self) -> None:
        menu = QMenu(self)
        menu.setAccessibleName("Şablon uygula")
        templates = sorted(self.templates().items(), key=lambda kv: kv[1].name)
        for template_id, template in templates:
            item = menu.addAction(template.name, partial(self.apply_template, template_id))
            item.setCheckable(True)
            item.setChecked(template_id == self._template_for_selection())
        if not templates:
            menu.addAction("Önce Şablonlar sekmesinde bir şablon oluşturun").setEnabled(False)
        button = self.side.template_button
        self.menu = menu
        menu.popup(button.mapToGlobal(QPoint(button.width() - menu.sizeHint().width(),
                                             button.height())))

    def _template_for_selection(self) -> str | None:
        templates = self.templates()
        if self._template_choice in templates:
            return self._template_choice
        for pid in self.selected_ids():
            for application in reversed(self.controller.job.templates):
                if pid in application.page_ids and application.template_id in templates:
                    return application.template_id
        ordered = sorted(templates.items(), key=lambda kv: kv[1].name)
        return ordered[0][0] if ordered else None

    # -- refreshing ---------------------------------------------------------------------------
    def _remember_selection(self) -> None:
        rows = sorted(i.row() for i in self.timeline.selectionModel().selectedIndexes())
        current = self.timeline.currentIndex()
        self._kept = ([self.model.page_id(r) for r in rows],
                      self.model.page_id(current.row()) if current.isValid() else None)

    def _restore_selection(self) -> None:
        selected, current = self._kept
        selection = self.timeline.selectionModel()
        flags = QItemSelectionModel.SelectionFlag.Select
        for pid in selected:
            try:
                selection.select(self.model.index(self.model.row_of(pid)), flags)
            except ValueError:
                continue  # the page is gone (its batch was removed)
        if current is not None:
            try:
                selection.setCurrentIndex(self.model.index(self.model.row_of(current)),
                                          QItemSelectionModel.SelectionFlag.NoUpdate)
            except ValueError:
                pass

    def _refresh_thumbnails(self) -> None:
        rotations = self.controller.job.rotations
        changed = {pid for pid in set(rotations) | set(self._rotations)
                   if rotations.get(pid) != self._rotations.get(pid)}
        self._rotations = dict(rotations)
        if self.thumbnails is not None:
            for pid in changed:
                self.thumbnails.invalidate(pid)

    def _job_changed(self) -> None:
        self._refresh_thumbnails()
        items = plan_export(self.controller.job, self.templates())
        checks = {item.number: item.checks for item in items if item.checks}
        self.model.set_checks(checks)
        self.strip.check_rows = [(self.model.first_row(n), n) for n in sorted(checks)]
        self._reviews_changed()

    def _reviews_changed(self) -> None:
        reviewed = self.reviews.reviewed_numbers()
        self.model.set_reviewed(reviewed)
        self.strip.set_state(len(self.controller.documents()), set(self.model.checks), reviewed)
        self._scrolled()
        self._current_changed(self.timeline.currentIndex())
        self._selection_changed()

    def _scrolled(self, *_args) -> None:
        rows = self.timeline.visible_rows()
        numbers = [n for n in (self.model.doc_of_row(r) for r in rows) if n]
        if numbers:
            self.strip.set_visible(min(numbers), max(numbers))
        else:
            self.strip.set_visible(0, 0)

    def _selection_changed(self, *_args) -> None:
        rows = self.selected_rows()
        ids = [self.model.page_id(r) for r in rows]
        if rows:
            self.side.show_selection(SelectionInfo(
                len(rows), rows[0] + 1, rows[-1] + 1,
                self._template_name(self._template_for_selection()), self._every_n))
        else:
            self.side.show_selection(None)
        job = self.controller.job
        pages = self._pages(ids)
        restore = bool(pages) and all(pid in job.deleted for pid in pages)
        label_delete(self.registry, len(pages), restore)
        self._update_status()

    def _template_name(self, template_id: str | None) -> str:
        template = self.templates().get(template_id) if template_id else None
        return template.name if template is not None else ""

    def _current_changed(self, index, *_args) -> None:
        number = self.current_document()
        documents = self.controller.documents()
        if not number or number > len(documents):
            self.side.show_nothing()
            self._update_status()
            return
        document = documents[number - 1]
        job = self.controller.job
        first = job.position_of(document.page_ids[0])
        last = job.position_of(document.page_ids[-1])
        kind = self.controller.cut_kinds().get(document.page_ids[0], "start")
        template = self.model.data(self.model.index(self.model.row_of(document.page_ids[0])),
                                   Roles.TEMPLATE)
        cut_text = CUT_WORDS.get(kind, kind)
        if kind == "filter":
            every = next((f.every_n for f in reversed(job.filters)
                          if document.page_ids[0] in f.page_ids), 0)
            cut_text = f"Filtre, her {every} sayfada" if every else "Filtre"
        icon, role = CUT_ICONS.get(kind, (None, "icon"))
        if kind == "filter":
            role = "cut-filter-text"
        previous = "Yok"
        if number > 1:
            pages = len(documents[number - 2].page_ids)
            previous = f"Belge {number - 1}, {pages} sayfa"
        checks = self.model.checks.get(number, [])
        self.side.show_document(DocumentInfo(
            number=number, template=template or "Şablon yok", first=first, last=last,
            pages=len(document.page_ids),
            reason=_sentence(checks) if checks else REASONS.get(kind, ""),
            cut_icon=icon, cut_role=role, cut_text=cut_text, previous=previous,
            check=bool(checks), reviewed=number in self.model.reviewed))
        self._update_status()

    def _update_status(self) -> None:
        status = getattr(self, "status", None)
        if status is None or not shiboken6.isValid(status):
            return
        row = self.current_row()
        status.set_counts(self.current_document(), len(self.controller.documents()),
                          row + 1 if row >= 0 else 0, self.model.rowCount(),
                          len(self.timeline.selectionModel().selectedIndexes()),
                          len(self.model.checks), len(self.model.reviewed))


def _forget_screen(window: QWidget, *_args) -> None:
    """The job's screen is gone (job closed or another opened): the status slot shows the
    empty state's line and the zoom slider no longer points at the screen's controller."""
    if not shiboken6.isValid(window) or getattr(window, "kontrol", None) is not None:
        return  # another job's screen took over and registered its own zoom
    unregister = getattr(window, "unregister_zoom", None)
    if callable(unregister):
        unregister("kontrol")
    slot = getattr(window, "status_slot", None)
    if callable(slot):
        status = slot("kontrol").findChild(KontrolStatus, KontrolStatus.NAME)
        if status is not None:
            status.set_empty()
