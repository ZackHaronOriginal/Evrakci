"""The main window in direction A: title band, a command bar per tab, the work layer and the
status bar, wired to the action registry. The six screens are hosted unchanged."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import NamedTuple

import shiboken6
from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci import __version__
from evrakci.pipeline.store import JobFileError, JobStore, default_root
from evrakci.pipeline.templates.model import TemplateError, template_from_dict, template_to_dict
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions, icons, kontrol_empty, motion, ocr_engine, refusals, style, theme
from evrakci.ui.chrome import (
    AboutDialog,
    CommandBar,
    JobSwitch,
    MenuRow,
    SearchBox,
    TitleTabs,
    make_icon,
    set_action_icons,
)
from evrakci.ui.controller import JobController
from evrakci.ui.degerler import DegerlerScreen
from evrakci.ui.disa_aktar import DisaAktarScreen
from evrakci.ui.feedback import Toaster
from evrakci.ui.kontrol import KontrolScreen
from evrakci.ui.kontrol_actions import DIMMABLE, NO_JOB_TEXT, KontrolStatus, menu_bar_entry
from evrakci.ui.kontrol_chips import SAVE_FAILED, TemplateStep
from evrakci.ui.loading import LoadingCard
from evrakci.ui.palette import CommandPalette
from evrakci.ui.prefs import Prefs
from evrakci.ui.rehber import RehberScreen
from evrakci.ui.sablon import SablonScreen
from evrakci.ui.settings_dialog import CHARACTER_KEYS, SettingsDialog
from evrakci.ui.shortcut_sheet import ShortcutSheet
from evrakci.ui.taskbar import TaskbarProgress
from evrakci.ui.thumbnails import ThumbnailService, job_renderer
from evrakci.ui.titlebar import TitleBand, WindowsFrame, use_custom_frame
from evrakci.ui.widgets import StatusPart
from evrakci.ui.workers import BUSY_REASON, Background, Task, run_background, start
from evrakci.ui.yukle import YukleScreen
from evrakci.ui.yukle_parts import ago
from evrakci.ui.zoomview import ZoomController, ZoomSlider

TAB_IDS = tuple(actions.TABS)
TAB_NAMES = list(actions.TABS.values())
LAST_JOB = "son-is.txt"
PREFS_FILE = "arayuz.ini"
FILL_CARD_MS = 1500  # reading an older job's page sizes: the loading card only if it is slow


class Cmd(NamedTuple):
    """One command-bar entry: a registry action, labelled or icon-only, A's icon and label;
    `hide_disabled` keeps the button out of the bar while the command cannot run."""

    id: str
    label: bool = False
    icon: str | None = None
    text: str | None = None
    hide_disabled: bool = False
    optional_label: str | None = None  # a label shown only while the bar has room (K-8)


SEP, GROW = "|", "->"
# A's command bars (final-a/<tab>.html); commands without a registry action are left for Phase 3.
COMMANDS: dict[str, tuple[Cmd | str, ...]] = {
    "yukle": (Cmd("app.geri_al"), Cmd("app.yinele"), SEP,
              Cmd("app.dosya_ekle", True, "file-up", "Dosya ekle…"),
              Cmd("yukle.klasor_ekle", icon="folder-plus"),
              Cmd("app.yeni_is", icon="file-plus"), SEP,
              Cmd("yukle.yukari"), Cmd("yukle.asagi"), Cmd("yukle.cikar"), SEP,
              Cmd("yukle.gezginde_goster", icon="external-link"), GROW,
              Cmd("yukle.iptal", True, "circle-x", "İptal et", hide_disabled=True),
              Cmd("app.sekme.kontrol", True, "arrow-right-to-line", "Kontrol'e geç"), SEP,
              Cmd("app.yan_panel")),
    "kontrol": (Cmd("app.geri_al"), Cmd("app.yinele"), SEP,
                Cmd("kontrol.kes", True, "scissors", "Kes"),
                Cmd("kontrol.birlestir", optional_label="Birleştir"),
                Cmd("kontrol.saga_dondur"), Cmd("kontrol.sil", optional_label="Sil"), SEP,
                Cmd("kontrol.sablon", icon="stamp"), Cmd("kontrol.filtre"),
                Cmd("kontrol.sec", icon="list-checks"), GROW,
                Cmd("kontrol.sonraki_kontrol", True),
                Cmd("kontrol.sonraki_incelenmemis", optional_label="Sonraki incelenmemiş"),
                Cmd("app.git"), SEP, Cmd("kontrol.onizle"), Cmd("app.yan_panel")),
    "sablonlar": (Cmd("app.geri_al"), Cmd("app.yinele"), SEP,
                  Cmd("sablonlar.kutu_ciz", True, "square-dashed", "Kutu çiz"),
                  Cmd("sablonlar.izgara"), Cmd("sablonlar.kutu_cogalt", icon="copy"),
                  Cmd("sablonlar.kutu_sil"), SEP, Cmd("sablonlar.degisken_ekle"), GROW,
                  Cmd("sablonlar.dene", True, "play", "Bütün örneklerde dene"),
                  Cmd("sablonlar.okumalari_goster"), SEP, Cmd("app.yan_panel")),
    "degerler": (Cmd("app.geri_al"), Cmd("app.yinele"), SEP,
                 Cmd("degerler.oku", True, "scan-text", "Değerleri oku"),
                 Cmd("degerler.eksikleri_oku"), SEP,
                 Cmd("degerler.tumunu_incele"), Cmd("degerler.ornek_kontrol"), GROW,
                 Cmd("degerler.onceki_kontrol", icon="chevron-up"),
                 Cmd("degerler.sonraki_kontrol", True), Cmd("degerler.secilenleri_onayla"), SEP,
                 Cmd("app.yan_panel")),
    "disa_aktar": (Cmd("app.geri_al"), Cmd("app.yinele"), SEP,
                   Cmd("app.disa_aktar", True, "download", "Dışa aktar"),
                   Cmd("disa_aktar.durdur", icon="circle-x"), SEP,
                   Cmd("app.yenile", True, "refresh-cw", "Yenile"), Cmd("disa_aktar.yazdir"),
                   GROW, Cmd("disa_aktar.index_ac", icon="sheet"),
                   Cmd("disa_aktar.gezginde_goster", icon="folder-open"), SEP,
                   Cmd("app.yan_panel")),
    "rehber": (Cmd("app.bul"), Cmd("app.onceki_sonuc"), Cmd("app.sonraki_sonuc"), SEP,
               Cmd("rehber.yazdir"), Cmd("rehber.pdf_ac", icon="external-link"), GROW,
               Cmd("app.kisayollar", True, "keyboard", "Kısayollar"),
               Cmd("app.yardim", icon="help-circle"), SEP, Cmd("app.yan_panel")),
}
# A's aria-label of the panel-right button per tab: "<panel> gizle (F9)".
PANEL_NAMES = {"yukle": "Ayrıntı panelini", "kontrol": "Ayrıntı panelini",
               "sablonlar": "Ayrıntı panelini", "degerler": "Kaynak panelini",
               "disa_aktar": "Ayarlar panelini", "rehber": "Yan paneli"}

# Tabs whose status line starts with the window's own job counts ("96 belge  640 sayfa
# ⚠ 7 belge kontrol bekliyor"); every other tab's mockup draws its own line instead.
STATUS_COUNTS = frozenset({"disa_aktar"})
NO_GO_TO_TABS = ("yukle", "rehber")  # no document list: Ctrl+G says where to go
JOB_TABS = ("yukle", "kontrol", "degerler", "disa_aktar")
TEXT_STEPS = theme.TEXT_SIZES
STATUS_INSET = 2  # QStatusBar's own item margin


def default_prefs(store: JobStore) -> Prefs:
    """The user's prefs for the real job folder; a file beside any other job folder (tests)."""
    try:
        real = store.root.resolve() == default_root().resolve()
    except OSError:
        real = False
    return Prefs() if real else Prefs(store.root.parent / PREFS_FILE)


def _accepts_tab(widget: QWidget) -> bool:
    return (widget.isVisible() and widget.isEnabled()
            and bool(widget.focusPolicy().value & Qt.FocusPolicy.TabFocus.value))


def first_focusable(region: QWidget) -> QWidget | None:
    """The first widget inside `region` (or itself) that Tab would stop on, in reading order."""
    if _accepts_tab(region):
        return region
    order = reading_order(region)
    return order[0] if order else None


# Composite widgets whose inner parts are not Tab stops of their own.
_COMPOSITES = (QAbstractSpinBox, QComboBox, QAbstractItemView, QTextEdit, QGraphicsView)


def _tab_stops(region: QWidget) -> list[QWidget]:
    stops = []
    for widget in region.findChildren(QWidget):
        if (not _accepts_tab(widget) or widget.focusProxy() is not None or widget.isWindow()
                or isinstance(widget, QScrollArea)):  # a frame around controls, not a stop
            continue
        parent = widget.parentWidget()
        inside = False
        while parent is not None and parent is not region:
            if isinstance(parent, _COMPOSITES) or parent.isWindow():
                inside = True
                break
            parent = parent.parentWidget()
        if not inside:
            stops.append(widget)
    return stops


def _rows(widgets: list[QWidget], origin: QWidget) -> list[QWidget]:
    """Reading order: top to bottom, and left to right inside a row (a widget whose middle
    lies within the row's height belongs to the row)."""
    placed = []
    for widget in widgets:
        top_left = widget.mapTo(origin, QPoint(0, 0))
        placed.append((top_left.y(), top_left.y() + widget.height(), top_left.x(), widget))
    placed.sort(key=lambda item: (item[0], item[2]))
    ordered: list[QWidget] = []
    row: list[tuple[int, int, int, QWidget]] = []
    bottom = None
    for item in placed:
        middle = (item[0] + item[1]) / 2
        if row and bottom is not None and middle < bottom:
            row.append(item)
            bottom = max(bottom, item[1])
            continue
        ordered.extend(w for *_, w in sorted(row, key=lambda r: r[2]))
        row, bottom = [item], item[1]
    ordered.extend(w for *_, w in sorted(row, key=lambda r: r[2]))
    return ordered


def _main_splitter(region: QWidget) -> QSplitter | None:
    """The largest visible splitter in `region` that is not inside another one."""
    best = None
    for splitter in region.findChildren(QSplitter):
        if not splitter.isVisible():
            continue
        parent = splitter.parentWidget()
        nested = False
        while parent is not None and parent is not region:
            if isinstance(parent, QSplitter):
                nested = True
                break
            parent = parent.parentWidget()
        if nested:
            continue
        area = splitter.width() * splitter.height()
        if best is None or area > best.width() * best.height():
            best = splitter
    return best


def reading_order(region: QWidget) -> list[QWidget]:
    """Tab stops of `region` in the order they are read (GOAL §3.1 "tab order = visual
    order"): a splitter's panes one after the other (the main pane before the side panel),
    each pane top to bottom and left to right."""
    stops = _tab_stops(region)
    splitter = _main_splitter(region)
    if splitter is None:
        return _rows(stops, region)
    inside = [w for w in stops if splitter.isAncestorOf(w)]
    outside = [w for w in stops if not splitter.isAncestorOf(w)]
    top = splitter.mapTo(region, QPoint(0, 0)).y()
    before = [w for w in outside
              if w.mapTo(region, QPoint(0, 0)).y() + w.height() / 2 < top]
    after = [w for w in outside if w not in before]
    ordered = _rows(before, region)
    for index in range(splitter.count()):
        pane = splitter.widget(index)
        if pane is None or not pane.isVisible():
            continue
        if _accepts_tab(pane) and pane in inside:
            ordered.append(pane)
        ordered.extend(w for w in reading_order(pane) if w in inside)
    ordered.extend(_rows(after, region))
    return ordered


def _reveal(widget: QWidget) -> None:
    """Scroll every scroll area around `widget` so it is in view."""
    parent = widget.parentWidget()
    while parent is not None and not parent.isWindow():
        if isinstance(parent, QScrollArea) and parent.widget() is not None \
                and parent.widget().isAncestorOf(widget):
            parent.ensureWidgetVisible(widget)
        parent = parent.parentWidget()


class AltMenus(QObject):
    """Alt alone shows the menu row; Alt+letter (or the letter while the row shows) opens a
    menu; Esc hides the row. Only the first receiver of a key event is looked at."""

    def __init__(self, window: MainWindow) -> None:
        super().__init__(window)
        self.window = window
        self._alone = False
        self._letters = [actions.access_key(t) for t in actions.MENUS.values()]
        QApplication.instance().installEventFilter(self)

    def _first_receiver(self, obj: QObject) -> bool:
        focus = QApplication.focusWidget()
        if focus is not None and focus.window() is self.window:
            return obj is focus
        return obj is self.window

    def _menu_for(self, event) -> int | None:
        mods = event.modifiers()
        row = self.window.menu_row.isVisible()
        alt = mods == Qt.KeyboardModifier.AltModifier
        if not (alt or row and mods == Qt.KeyboardModifier.NoModifier):
            return None
        key = event.key()
        if not Qt.Key.Key_A.value <= key <= Qt.Key.Key_Z.value:
            return None
        letter = chr(key)
        return self._letters.index(letter) if letter in self._letters else None

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        kind = event.type()
        if kind not in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease,
                        QEvent.Type.ShortcutOverride):
            if kind == QEvent.Type.MouseButtonPress:
                self._alone = False
            return False
        if not isinstance(obj, QWidget) or not self._first_receiver(obj):
            return False
        key = event.key()
        if kind == QEvent.Type.ShortcutOverride:
            if self._menu_for(event) is not None:
                event.accept()
                return True
            return False
        if kind == QEvent.Type.KeyRelease:
            if key == Qt.Key.Key_Alt and self._alone and not event.isAutoRepeat():
                self._alone = False
                self.window.toggle_menu_row()
            return False
        if key == Qt.Key.Key_Alt:
            self._alone = not event.isAutoRepeat() or self._alone
            return False
        self._alone = False
        index = self._menu_for(event)
        if index is not None:
            self.window.open_menu(index)
            return True
        if self.window.menu_row.isVisible():
            if key == Qt.Key.Key_Escape:
                self.window.hide_menu_row()
                return True
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Down):
                self.window.open_menu(0)
                return True
        return False


class _EnabledMirror(QObject):
    """Calls `apply(enabled)` now and whenever `widget` is enabled or disabled."""

    def __init__(self, widget: QWidget, apply) -> None:
        super().__init__(widget)
        self._apply = apply
        widget.installEventFilter(self)
        apply(widget.isEnabled())

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.EnabledChange:
            self._apply(obj.isEnabled())
        return False


class MainWindow(QMainWindow):
    loading_card: LoadingCard  # over the tab body; run_background shows it for a loading job
    _background: Background | None = None  # the one loading job of this window
    _closed = False  # set when the close is accepted: late results are dropped (rule 6)
    recent_changed = Signal()  # the recent-jobs list was fetched anew
    _recent: list[tuple[object, str]] = []  # the last list a worker fetched (never mutated)
    _recent_run = 0

    def __init__(
        self,
        store: JobStore,
        templates: TemplateStore,
        settings_path: Path | None = None,
        prefs: Prefs | None = None,
    ) -> None:
        super().__init__()
        self.store = store
        self.template_store = templates
        self.settings_path = settings_path
        self.prefs = prefs if prefs is not None else default_prefs(store)
        self.setWindowTitle(f"Evrakçı {__version__}")
        self.setWindowIcon(icons.app_icon())
        self.resize(1366, 768)
        self.setMinimumSize(1024, 600)
        self.kontrol: KontrolScreen | None = None
        self.thumbnails: ThumbnailService | None = None
        self.settings_dialog: SettingsDialog | None = None
        self.about_dialog: AboutDialog | None = None
        self._closing = False
        self._close_warned = False  # a failed save already blocked one close (B-035)
        self._discard_ok = False  # the owner answered Yes: the unsaved edits may be dropped
        self._save_waiting = False  # Ctrl+S is waiting for its write (one answer, not a pile)
        self._restoring = True
        self._zoom: dict[str, tuple[ZoomController, str]] = {}
        self._zoom_hidden: set[str] = set()
        self._zoom_watched: set[tuple[str, int]] = set()
        self._status_counts: dict[str, bool] = {tab: tab in STATUS_COUNTS for tab in TAB_IDS}
        self._splitters: set[int] = set()
        self._wired: JobController | None = None  # the controller whose signals are connected

        self.registry = actions.Registry(self)
        self.registry.install_text_guard()
        self.registry.set_character_keys(self.prefs.flag(CHARACTER_KEYS, True))
        self._settings_opener: QWidget | None = None
        self._build_screens()
        self._build_title_band()
        self._build_body()
        self._build_status_bar()
        self._build_menus()
        self._wire_actions()
        self._fill_command_bars()
        set_action_icons(self.registry)

        self.toaster = Toaster(self)
        self.taskbar = TaskbarProgress(self)
        self.command_palette = CommandPalette(self.registry, self)
        self.shortcut_sheet = ShortcutSheet(self.registry, self)
        self.alt_menus = AltMenus(self)
        theme.manager().changed.connect(self._restyle)
        # The screens hook their own commands, status items and zoom now (each attach runs
        # once), so everything works before the event loop first spins.
        for screen in (self.yukle, self.sablon, self.degerler, self.disa_aktar, self.rehber):
            screen.attach(self)

        # A key that cannot act says why (Q-09): the texts are in refusals.py.
        self.registry.refused.connect(self._refused)
        self.registry.set_reason_source(partial(refusals.reason, self))
        self._restore_state()
        self._restoring = False
        self._tab_changed(self.tabs.currentIndex())
        self._loading_tips: dict[str, str] = {}
        self._open_last_job()
        self.refresh_recent_jobs()
        QTimer.singleShot(0, ocr_engine.warm_up)  # the engine probe, off the window thread

    # -- building -------------------------------------------------------------------------
    def _build_screens(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().hide()  # the title band's TitleTabs drive it
        # The hidden tab bar is the QTabWidget's focus proxy; left as a Tab stop it swallows
        # Tab (focus never leaves the title band). TitleTabs is the tab strip's Tab stop.
        self.tabs.tabBar().setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabs.setFocusProxy(None)
        self.tabs.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.yukle = YukleScreen(self.store)
        self.yukle.job_opened.connect(self._job_opened)
        self.yukle.can_switch = self._switch_refusal
        self.yukle.settle = self._settle_job
        self.sablon = SablonScreen(self.template_store, self.controller)
        self.degerler = DegerlerScreen(self.controller, self.template_map)
        self.degerler.draw_variant.connect(self._draw_variant)
        self.degerler.open_kontrol.connect(self._open_in_kontrol)
        self.disa_aktar = DisaAktarScreen(self.controller, self.template_map, self.settings_path)
        self.disa_aktar.job_deleted.connect(self._job_deleted)
        self.rehber = RehberScreen()
        self.disa_aktar.finished.connect(self._work_stopped)
        self.yukle.task_finished.connect(self._work_stopped)
        self.degerler.finished.connect(self._work_stopped)
        self._kontrol_placeholder = kontrol_empty.for_window(self)
        for name, widget in zip(TAB_NAMES, (self.yukle, self._kontrol_placeholder, self.sablon,
                                            self.degerler, self.disa_aktar, self.rehber),
                                strict=True):
            self.tabs.addTab(widget, name)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.loading_card = LoadingCard(self.tabs, dim=True)
        for widget in (self.yukle, self.sablon, self.degerler, self.disa_aktar, self.rehber):
            self._track_splitters(widget)

    def _build_title_band(self) -> None:
        self.title_tabs = TitleTabs([(t, actions.TABS[t]) for t in TAB_IDS])
        for index, tab in enumerate(TAB_IDS):
            self.title_tabs.setTabToolTip(index, self.registry.action(f"app.sekme.{tab}").toolTip())
        self.title_tabs.currentChanged.connect(self.tabs.setCurrentIndex)
        self.job_switch = JobSwitch()
        self.job_switch.clicked.connect(self.open_job_switcher)
        self.search = SearchBox()
        self.search.clicked.connect(self.open_palette)
        self.menu_button = QToolButton()
        self.menu_button.setObjectName("menuButton")
        self.menu_button.setProperty("kind", "icon")
        self.menu_button.setProperty("sizeVariant", "sm")
        self.menu_button.setAutoRaise(True)
        self.menu_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.menu_button.setToolTip("Menü (Alt)")
        self.menu_button.setAccessibleName("Menü (Alt)")
        self.menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        custom = use_custom_frame(self.prefs)
        self.title_band = TitleBand(self.title_tabs, self.job_switch, self.search,
                                    self.menu_button, caption=custom)
        self.frame = WindowsFrame(self, self.title_band) if custom else None
        caption = self.title_band.caption
        if caption:
            caption["min"].clicked.connect(self.showMinimized)
            caption["max"].clicked.connect(self.toggle_maximized)
            caption["close"].clicked.connect(self.close)
        self.setMenuWidget(self.title_band)

    def _build_body(self) -> None:
        m = theme.manager()
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(m.size("s2"), 0, m.size("s2"), 0)
        outer.setSpacing(0)
        self.layer = QFrame()
        self.layer.setObjectName("layer")
        inner = QVBoxLayout(self.layer)
        inner.setContentsMargins(1, 1, 1, 1)
        inner.setSpacing(0)
        self.command_bars = QStackedWidget()
        self._bars: dict[str, CommandBar] = {}
        for tab in TAB_IDS:
            bar = CommandBar(actions.TABS[tab])
            self._bars[tab] = bar
            self.command_bars.addWidget(bar)
        inner.addWidget(self.command_bars)
        inner.addWidget(self.tabs, 1)
        outer.addWidget(self.layer)
        self.setCentralWidget(central)

    def _build_status_bar(self) -> None:
        m = theme.manager()
        bar = QStatusBar()
        bar.setObjectName("statusBar")
        bar.setSizeGripEnabled(False)
        self.setStatusBar(bar)
        left = QWidget()
        row = QHBoxLayout(left)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(m.size("s6"))
        self.counts = StatusPart()  # A: the numbers in bold ("3 belge  15 sayfa")
        self.pages = StatusPart()
        self.check_icon = QLabel()
        self.checks = QLabel("")
        check = QHBoxLayout()
        check.setSpacing(6)  # A .statusbar .warn gap
        check.addWidget(self.check_icon)
        check.addWidget(self.checks)
        self.check_icon.hide()
        self.status_slots = QStackedWidget()
        self._slots: dict[str, QWidget] = {}
        for tab in TAB_IDS:
            # The stacked page holds the tab's slot and a trailing stretch, so a slot's items
            # sit at the left even while the stack is as wide as the widest tab's line.
            page = QWidget()
            page_row = QHBoxLayout(page)
            page_row.setContentsMargins(0, 0, 0, 0)
            page_row.setSpacing(0)
            slot = QWidget(page)
            slot.setObjectName(f"statusSlot.{tab}")
            slot_row = QHBoxLayout(slot)
            slot_row.setContentsMargins(0, 0, 0, 0)
            slot_row.setSpacing(m.size("s6"))
            page_row.addWidget(slot)
            page_row.addStretch(1)
            self._slots[tab] = slot
            self.status_slots.addWidget(page)
        self.message = QLabel("")
        row.addWidget(self.counts)
        row.addWidget(self.pages)
        row.addLayout(check)
        row.addWidget(self.status_slots)
        self.export_status = StatusPart("loader-circle", "icon")  # an export runs (other tabs)
        self.export_status.set("Dışa aktarılıyor")
        self.export_status.hide()
        row.addWidget(self.export_status)
        row.addWidget(self.message, 1)
        bar.addWidget(left, 1)
        self.zoom_slider = ZoomSlider()
        self.zoom_slider.hide()
        bar.addPermanentWidget(self.zoom_slider)
        self.yukle.refused.connect(self.message.setText)
        self._pad_status_bar()
        KontrolStatus.in_slot(self._slots["kontrol"]).set_empty()

    def _pad_status_bar(self) -> None:
        """A .statusbar padding 0 s4 0 s6 (QStatusBar ignores QSS padding for its items)."""
        m = theme.manager()
        self.statusBar().setContentsMargins(m.size("s6") - STATUS_INSET, 0,
                                            m.size("s4") - STATUS_INSET, 0)

    def _build_menus(self) -> None:
        """The six menus twice: the Alt row and A's ≡ menu (each filled when it opens)."""
        self.menu_row = MenuRow(self)
        self.app_menu = QMenu(self)
        self.app_menu.setAccessibleName("Menü")
        for key, title in actions.MENUS.items():
            menu = self.menu_row.bar.addMenu(title)
            menu.aboutToShow.connect(partial(self._fill_menu, menu, title))
            menu.aboutToHide.connect(lambda: QTimer.singleShot(0, self, self._row_menu_closed))
            sub = QMenu(actions.plain_text(title), self.app_menu)
            sub.aboutToShow.connect(partial(self._fill_menu, sub, title))
            item = self.app_menu.addMenu(sub)
            item.setText(f"{title}\tAlt+{actions.access_key(title)}")
            item.setObjectName(f"menu.{key}")
        self.menu_button.setMenu(self.app_menu)
        self.menu_row.bar.installEventFilter(self)

    def _fill_menu(self, menu: QMenu, title: str) -> None:
        menu.clear()
        menu.setToolTipsVisible(True)  # a greyed item's tooltip is the reason (Q-09)
        self.registry.refresh_reasons()
        items = dict(actions.menu_structure(self.registry.context))[title]
        for item in items:
            if item is None:
                menu.addSeparator()
            else:
                entry = self.registry.action(item)
                if item in DIMMABLE and self.registry.context == "kontrol":
                    entry = menu_bar_entry(self.kontrol, entry, menu)
                menu.addAction(entry)
            if item == "app.yinele":  # Düzen: the visible undo history right under Yinele
                menu.addMenu(self._history_menu(menu))

    def undo_history(self) -> list[tuple[int, str, bool]]:
        """(index, step name, done) of every step of the current undo history, oldest first;
        `done` is False for the steps that were undone (Yinele brings them back)."""
        stack = self._undo_stack()
        if stack is None:
            return []
        try:
            return [(i, stack.text(i), i < stack.index()) for i in range(stack.count())]
        except RuntimeError:  # the job's stack is already gone while closing
            return []

    def _history_menu(self, parent: QMenu) -> QMenu:
        """Düzen > Geri alma geçmişi: every step by name, newest first; choosing one takes the
        job (or the template on Şablonlar) back to just after it. Undone steps are greyed
        with "(geri alındı)" and can be chosen to redo up to them."""
        menu = QMenu("Geri alma &geçmişi", parent)
        menu.setAccessibleName("Geri alma geçmişi")
        menu.setIcon(make_icon("history"))
        history = self.undo_history()
        menu.setEnabled(bool(history))
        start = menu.addAction("Başlangıç (hiçbir değişiklik yok)")
        start.triggered.connect(partial(self._undo_to, 0))
        for index, text, done in reversed(history[-30:]):
            label = text.replace("&", "&&") + ("" if done else "  (geri alındı)")
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(index + 1 == self._undo_index())
            action.triggered.connect(partial(self._undo_to, index + 1))
        if not history:
            start.setEnabled(False)
        return menu

    def _undo_index(self) -> int:
        stack = self._undo_stack()
        return stack.index() if stack is not None else 0

    def _undo_to(self, index: int, *_args) -> None:
        stack = self._undo_stack()
        controller = self.controller()
        if stack is not None and not (controller is not None and controller.frozen):
            stack.setIndex(index)

    def _fill_command_bars(self) -> None:
        for tab, entries in COMMANDS.items():
            bar = self._bars[tab]
            for entry in entries:
                if entry == SEP:
                    bar.add_separator()
                elif entry == GROW:
                    bar.add_stretch()
                else:
                    bar.add_action(self.registry.action(entry.id), entry.label, entry.icon,
                                   entry.text, entry.hide_disabled, entry.optional_label,
                                   tip_on_focus=tab == "kontrol")
            bar.add_more(partial(self._fill_more, tab))

    def _fill_more(self, tab: str, menu: QMenu) -> None:
        """Diğer komutlar: this tab's menu commands that are not on its bar."""
        shown = {e.id for e in COMMANDS[tab] if isinstance(e, Cmd)}
        for _title, items in actions.menu_structure(tab):
            ids = [i for i in items if i and i not in shown
                   and self.registry.spec(i).context == tab]
            if ids and not menu.isEmpty():
                menu.addSeparator()
            for item in ids:
                menu.addAction(self.registry.action(item))
        if menu.isEmpty():
            menu.addAction("Başka komut yok").setEnabled(False)

    def command_bar(self, tab: str) -> CommandBar:
        """The command bar of a tab (yukle, kontrol, sablonlar, degerler, disa_aktar, rehber)."""
        return self._bars[tab]

    def status_slot(self, tab: str) -> QWidget:
        """The tab's own area in the status bar (an empty QHBoxLayout to fill)."""
        return self._slots[tab]

    # -- actions --------------------------------------------------------------------------
    def _wire_actions(self) -> None:
        r = self.registry
        for tab in TAB_IDS:
            r.connect(f"app.sekme.{tab}", partial(self._show_tab_slot, tab))
        r.connect("app.sonraki_sekme", lambda: self.cycle_tab(1, focus=True))
        r.connect("app.onceki_sekme", lambda: self.cycle_tab(-1, focus=True))
        r.connect("app.sonraki_bolge", lambda: self.focus_region(1))
        r.connect("app.onceki_bolge", lambda: self.focus_region(-1))
        # Ctrl+F on every tab, each finding what that tab lists (no new fields, A's look):
        # Değerler and Rehber their search fields (their own routes), Yükle the job list's
        # search, Kontrol "Belgeye veya sayfaya git", Şablonlar the variable list (type to
        # jump), Dışa Aktar the file list (type a file name to jump).
        r.connect_tab("app.bul", "yukle", self.yukle.show_job_list)
        r.connect_tab("app.bul", "kontrol", self._find_in_kontrol)
        r.connect_tab("app.bul", "sablonlar", self.sablon.find_variable)
        r.connect_tab("app.bul", "disa_aktar", self._find_in_disa_aktar)
        # Ctrl+G on every tab (M-01, B-027): Kontrol and Değerler open the go-to dialog on
        # their own list, Şablonlar picks the Örnek, Dışa Aktar the file row; Yükle and Rehber
        # have no document list and say where to go (no job: what to do first).
        r.connect_tab("app.git", "sablonlar", self.sablon.go_to_example)
        r.connect_tab("app.git", "disa_aktar", self.disa_aktar.go_to_file)
        for tab in NO_GO_TO_TABS:
            r.connect_tab("app.git", tab, self._say_go_to_elsewhere)
        r.connect("app.yeni_is", self._new_job)
        r.connect("app.dosya_ekle", self._add_files)
        # Ctrl+S answers on every tab that has something to save: Şablonlar saves the
        # template, the job tabs write the job now and say so (it is saved after every edit
        # anyway). Rehber has nothing to save, so the key is off there.
        r.connect_tab("app.kaydet", "sablonlar", lambda: self.sablon.save())
        for tab in JOB_TABS:
            r.connect_tab("app.kaydet", tab, self.save_job)
        r.connect("app.disa_aktar", self._export)
        r.connect("app.isi_kapat", self.close_job)
        r.connect("app.cikis", self.close)
        r.connect("app.geri_al", self.undo)
        r.connect("app.yinele", self.redo)
        r.connect("app.yakinlastir", lambda: self._zoom_call("zoom_in"))
        r.connect("app.uzaklastir", lambda: self._zoom_call("zoom_out"))
        r.connect("app.sigdir", lambda: self._zoom_call("fit"))
        r.connect("app.yazi_buyut", lambda: self.step_text_size(1))
        r.connect("app.yazi_kucult", lambda: self.step_text_size(-1))
        r.connect("app.tam_ekran", self.set_full_screen)
        r.connect("app.yenile", self._refresh_key)
        for tab in ("kontrol", "rehber"):  # nothing to refresh there: off, with its reason (M-22)
            r.set_enabled_for("app.yenile", tab, False)
        r.connect("app.ayarlar", self.open_settings)
        r.connect("app.yardim", self._show_guide)
        r.connect("app.kisayollar", self.open_shortcut_sheet)
        r.connect("app.komut_ara", self.open_palette)
        r.connect("app.hakkinda", self.open_about)
        # Yükle, Şablonlar, Değerler, Dışa Aktar: the screens' own slots
        r.connect("yukle.yukari", lambda: self.yukle.move_batch(-1))
        r.connect("yukle.asagi", lambda: self.yukle.move_batch(1))
        r.connect("yukle.iptal", self.yukle.cancel)
        r.connect("sablonlar.kutu_ciz", lambda on=None: self.sablon.set_drawing(
            not self.sablon.is_drawing() if on is None else on))
        r.connect("sablonlar.izgara", lambda on=None: self.sablon.set_snap(
            not self.sablon.is_snapping() if on is None else on))
        r.connect("sablonlar.dene", self.sablon.read_all_examples)
        self.sablon.drawing_changed.connect(partial(self._mirror_check, "sablonlar.kutu_ciz"))
        self.sablon.snap_changed.connect(partial(self._mirror_check, "sablonlar.izgara"))
        self._mirror_check("sablonlar.kutu_ciz", self.sablon.is_drawing())
        self._mirror_check("sablonlar.izgara", self.sablon.is_snapping())
        r.connect("degerler.onayla", self.degerler.accept_current)
        r.connect("degerler.okunanla_onayla", self.degerler.accept_read)
        r.connect("degerler.elle_yaz", self.degerler.type_current)
        r.connect("degerler.okunana_don", self.degerler.revert_current)
        r.connect("degerler.varyant", lambda: self.degerler.side.variant_button.click())
        # a lambda: triggered(checked) would arrive as next_check's `step` (0 = from the top)
        r.connect("degerler.sonraki_kontrol", lambda: self.degerler.next_check(1))
        r.connect("degerler.kontrolde_ac", self.degerler.open_in_kontrol)
        r.connect("degerler.durdur", self._stop_on_degerler)
        # The screen's two (hidden) read buttons hold the enabled state; the bar's commands
        # click them.
        for action_id, button in (("degerler.oku", self.degerler.read_button),
                                  ("degerler.eksikleri_oku", self.degerler.missing_button)):
            r.connect(action_id, button.click)
            _EnabledMirror(button, partial(self.registry.set_enabled, action_id))
        r.connect("app.yan_panel", self.toggle_inspector)
        r.connect("disa_aktar.durdur", self._stop_on_disa_aktar)
        # Kontrol's commands are routed by kontrol_actions.KontrolBinder to the open job's screen.
        self._sync_job_actions()
        self.sablon.undo_stack.indexChanged.connect(self._sync_undo)

    def inspector(self, tab: str | None = None) -> QWidget | None:
        """The tab's side panel (a screen's `side`), or None while the screen has none."""
        screens = {"yukle": self.yukle, "kontrol": self.kontrol, "sablonlar": self.sablon,
                   "degerler": self.degerler, "disa_aktar": self.disa_aktar,
                   "rehber": self.rehber}
        side = getattr(screens[tab or self.current_tab()], "side", None)
        return side if isinstance(side, QWidget) else None

    def toggle_inspector(self, *_args) -> None:
        """F9: hide or show the current tab's side panel."""
        side = self.inspector()
        if side is None:
            self.say_no_job()
        else:
            side.setVisible(side.isHidden())
        self._sync_inspector()

    def _sync_inspector(self) -> None:
        tab = self.current_tab()
        side = self.inspector(tab)
        self.registry.set_enabled("app.yan_panel", side is not None)
        verb = "göster" if side is not None and side.isHidden() else "gizle"
        key = actions.key_text("F9")
        self.registry.action("app.yan_panel").setToolTip(f"{PANEL_NAMES[tab]} {verb} ({key})")

    def _mirror_check(self, action_id: str, checked: bool) -> None:
        action = self.registry.action(action_id)
        action.blockSignals(True)
        action.setChecked(checked)
        action.blockSignals(False)
        action.changed.emit()

    def _refused(self, _action_id: str, text: str) -> None:
        """The key of a greyed command was pressed: the status bar says why."""
        self.message.setText(text)

    def say_no_job(self) -> None:
        """A key that needs an open job says what to do first instead of staying silent."""
        self.message.setText(NO_JOB_TEXT)

    def _say_go_to_elsewhere(self) -> None:
        if self.controller() is None:
            self.say_no_job()
        else:
            self.message.setText(refusals.GO_TO_ELSEWHERE)

    def _find_in_kontrol(self) -> None:
        if self.kontrol is None:
            self.say_no_job()
        else:
            self.kontrol.go_to()

    def _find_in_disa_aktar(self) -> None:
        if self.controller() is None:
            self.say_no_job()
        else:
            self.disa_aktar.find_file()

    def _sync_job_actions(self) -> None:
        # Ctrl+S, Ctrl+F and Ctrl+E stay on with no job: their handlers say so. Ctrl+W stays
        # off (M-15: the effect test of Ctrl+W asserts the item is disabled after closing).
        self.registry.set_enabled("app.isi_kapat", self.controller() is not None)
        self._sync_export_action()
        self._sync_undo()

    def _sync_export_action(self, *_args) -> None:
        """app.disa_aktar has one owner: on with no job (_export says to open one); with a job
        on Dışa Aktar only while that screen can start an export (not blocked, not running)."""
        on_tab = hasattr(self, "tabs") and self.current_tab() == "disa_aktar"
        can = getattr(self.disa_aktar, "can_export", lambda: True)()
        self.registry.set_enabled("app.disa_aktar", not self.loading() and (
            self.controller() is None or not on_tab or can))

    def save_job(self) -> None:
        """Ctrl+S on a job tab: write the job now and confirm it (edits are saved as they
        happen, so this only reassures). The write is the saver's; the title band says
        "Kaydediliyor…" until it is on disk, then "Kaydedildi"."""
        controller = self.controller()
        if controller is None:
            self.say_no_job()
            return
        if controller.frozen:  # the job is being deleted: nothing is written
            return
        controller.save_now()
        if self._save_waiting:  # a press is already waiting: it answers for both
            return
        self._save_waiting = True

        def written(ok: bool, error: str) -> None:
            self._save_waiting = False
            if not shiboken6.isValid(self) or self._closed or self.controller() is not controller:
                return
            if ok:
                now = datetime.now()
                self.toaster.show(f"İş kaydedildi {now:%H:%M}. Değişiklikler zaten kendiliğinden "
                                  "kaydedilir.", kind="success")
            else:  # the title band already shows "Kaydedilemedi" and its retry
                self.toaster.show(f"İş kaydedilemedi: {error}", kind="error")

        controller.saver.when_idle(written)

    def _show_tab_slot(self, tab: str, *_args) -> None:
        self.show_tab(tab)
        self.focus_work_area()

    def show_tab(self, tab: str) -> None:
        self.tabs.setCurrentIndex(TAB_IDS.index(tab))

    def current_tab(self) -> str:
        return TAB_IDS[self.tabs.currentIndex()]

    def cycle_tab(self, step: int, focus: bool = False) -> None:
        self.tabs.setCurrentIndex((self.tabs.currentIndex() + step) % len(TAB_IDS))
        if focus:
            self.focus_work_area()

    def regions(self) -> list[QWidget]:
        """F6's regions, in reading order: title band, command bar, work area, status bar."""
        return [self.title_band, self.command_bars.currentWidget(),
                self.tabs.currentWidget(), self.statusBar()]

    def tab_order(self) -> list[QWidget]:
        """Every Tab stop of the window in reading order, region by region; anything else
        that takes Tab (a toast's Geri al) comes last."""
        ordered: list[QWidget] = []
        for region in self.regions():
            if region is not None and region.isVisible():
                ordered.extend(w for w in reading_order(region) if w not in ordered)
        seen = set(map(id, ordered))
        ordered.extend(w for w in _rows(_tab_stops(self), self) if id(w) not in seen)
        return ordered

    def focusNextPrevChild(self, next: bool) -> bool:  # noqa: N802, A002
        """Tab and Shift+Tab follow tab_order(), so focus never sticks in a region and the
        command bar comes before the work area, the side panel after the main pane."""
        order = self.tab_order()
        if not order:
            return super().focusNextPrevChild(next)
        focus = QApplication.focusWidget()
        index = next_index = -1
        for i, widget in enumerate(order):
            if focus is widget or (focus is not None and widget.isAncestorOf(focus)):
                index = i
        if index < 0:
            next_index = 0 if next else len(order) - 1
        else:
            next_index = (index + (1 if next else -1)) % len(order)
        target = order[next_index]
        reason = (Qt.FocusReason.TabFocusReason if next
                  else Qt.FocusReason.BacktabFocusReason)
        target.setFocus(reason)
        _reveal(target)
        return True

    def focus_work_area(self, reason: Qt.FocusReason = Qt.FocusReason.ShortcutFocusReason) -> None:
        """Ctrl+1…6 and Ctrl+Tab put focus on the tab's main region (the timeline, the
        values table, the canvas, the batch or file list, the guide text), so arrows,
        Home/End and PgDn act there at once; an empty state's first control otherwise."""
        area = self.tabs.currentWidget()
        if area is None:
            return
        order = reading_order(area)
        views = [w for w in order if isinstance(w, QAbstractScrollArea)
                 and not isinstance(w, QScrollArea)]
        target = max(views, key=lambda w: w.width() * w.height()) if views else (
            order[0] if order else None)
        if target is not None:
            target.setFocus(reason)
            _reveal(target)

    def focus_region(self, step: int) -> None:
        """F6 / Shift+F6: title band, command bar, work area, status bar."""
        regions = self.regions()
        focus = QApplication.focusWidget()
        current = next((i for i, r in enumerate(regions)
                        if focus is not None and (focus is r or r.isAncestorOf(focus))), -1)
        for offset in range(1, len(regions) + 1):
            region = regions[(current + step * offset) % len(regions)]
            target = first_focusable(region)
            if target is not None:
                target.setFocus(Qt.FocusReason.TabFocusReason)
                _reveal(target)
                return

    def _new_job(self) -> None:
        if self.loading():
            self.message.setText(BUSY_REASON)
            return
        self.show_tab("yukle")
        self.yukle.choose_new_job()

    def _add_files(self) -> None:
        if self.loading():
            self.message.setText(BUSY_REASON)
            return
        self.show_tab("yukle")
        self.yukle.choose_batch()

    def _export(self) -> None:
        if self.loading():
            self.message.setText(BUSY_REASON)
        elif self.controller() is None:
            self.say_no_job()
        elif self.current_tab() == "disa_aktar":
            self.disa_aktar.export()
        else:
            self.show_tab("disa_aktar")

    def _show_guide(self) -> None:
        """F1: the guide, with focus on its text (also when Rehber is already shown)."""
        self.show_tab("rehber")
        self.rehber.text.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _refresh_key(self) -> None:
        """F5: Dışa Aktar with no job open says what to do first (M-23)."""
        if self.current_tab() == "disa_aktar" and self.controller() is None:
            self.say_no_job()
        self.refresh_current()

    def refresh_current(self) -> None:
        tab = self.current_tab()
        if tab == "yukle":
            self.yukle.refresh_jobs()
        elif tab == "sablonlar":
            self.sablon.refresh_templates()
        elif tab == "degerler":
            self.degerler.refresh()
        elif tab == "disa_aktar":
            self.disa_aktar.refresh()

    def open_palette(self) -> None:
        self.command_palette.open_for(self.current_tab())

    def open_shortcut_sheet(self) -> None:
        self.shortcut_sheet.show_for(self.current_tab())

    def open_settings(self) -> None:
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self.prefs, self.registry, self,
                                                  retention_settings_path=self.settings_path)
            self.settings_dialog.finished.connect(self._settings_closed)
        opener = QApplication.focusWidget()
        if opener is not None and not self.settings_dialog.isAncestorOf(opener):
            self._settings_opener = opener
        self.settings_dialog.open()

    def _settings_closed(self, *_args) -> None:
        """Esc or Kapat in Ayarlar puts focus back where it was opened from."""
        opener, self._settings_opener = self._settings_opener, None
        if opener is not None and shiboken6.isValid(opener) and opener.isVisible():
            self.activateWindow()
            opener.setFocus(Qt.FocusReason.OtherFocusReason)

    def open_about(self) -> None:
        if self.about_dialog is None:
            self.about_dialog = AboutDialog(self)
        self.about_dialog.open()

    def step_text_size(self, step: int) -> None:
        m = theme.manager()
        index = TEXT_STEPS.index(m.text_scale()) + step
        if 0 <= index < len(TEXT_STEPS):
            m.set_text_scale(TEXT_STEPS[index])

    def set_full_screen(self, on: bool) -> None:
        if on:
            self._was_maximized = self.isMaximized()
            self.showFullScreen()
        elif getattr(self, "_was_maximized", False):
            self.showMaximized()
        else:
            self.showNormal()

    def toggle_maximized(self) -> None:
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def busy(self, delay_ms: int = motion.BUSY_DELAY_MS):
        """Wait cursor for a block that keeps the event loop running (motion.busy_cursor)."""
        return motion.busy_cursor(delay_ms)

    # Undo / redo: the job's stack, or the template editor's on Şablonlar
    def _undo_stack(self) -> QUndoStack | None:
        tab = self.current_tab()
        if tab == "sablonlar":
            return self.sablon.undo_stack
        if tab == "rehber":  # shows nothing of the job: Ctrl+Z must not act unseen (B-055)
            return None
        controller = self.controller()
        return controller.undo_stack if controller is not None else None

    def undo(self) -> None:
        stack = self._undo_stack()
        if stack is not None and stack.canUndo() and not self.degerler.busy():
            stack.undo()

    def redo(self) -> None:
        stack = self._undo_stack()
        if stack is not None and stack.canRedo() and not self.degerler.busy():
            stack.redo()

    def _sync_undo(self, *_args) -> None:
        """Geri al / Yinele name the step they act on, in the Düzen menu, the command bar's
        tooltip and the palette: "Geri al: Kesim ekle (Ctrl+Z)"."""
        stack = self._undo_stack()
        # a read in progress would be made stale by an undo: no Geri al / Yinele until it ends
        reading = self.degerler.busy() if getattr(self, "degerler", None) is not None else False
        for action_id, can, what in (("app.geri_al", "canUndo", "undoText"),
                                     ("app.yinele", "canRedo", "redoText")):
            try:
                enabled = stack is not None and getattr(stack, can)() and not reading
                detail = getattr(stack, what)() if enabled else ""
            except RuntimeError:  # the job's stack is already gone while closing
                return
            self.registry.set_enabled(action_id, enabled)
            spec = self.registry.spec(action_id)
            base = actions.plain_text(spec.text)
            key = actions.key_text(spec.shortcuts[0])
            action = self.registry.action(action_id)
            action.setText(f"{spec.text}: {detail.replace('&', '&&')}" if detail else spec.text)
            action.setToolTip(f"{base}: {detail} ({key})" if detail else f"{base} ({key})")

    # Zoom
    def register_zoom(self, tab: str, controller: ZoomController | None,
                      target: str = "Görünüm") -> None:
        """Let the status bar slider and Ctrl+plus/minus/0 drive `controller` on `tab`; None
        unregisters it. A controller that is destroyed is dropped by itself."""
        if controller is None:
            self.unregister_zoom(tab)
            return
        self._zoom[tab] = (controller, target)
        key = (tab, id(controller))
        if key not in self._zoom_watched:  # one connection per controller and tab, ever
            self._zoom_watched.add(key)
            controller.destroyed.connect(partial(self._zoom_gone, tab, id(controller)))
        if tab == self.current_tab():
            self._sync_zoom()

    def unregister_zoom(self, tab: str) -> None:
        """`tab` has no zoom any more (its view went away)."""
        if self._zoom.pop(tab, None) is not None and tab == self.current_tab():
            self._sync_zoom()

    def set_zoom_visible(self, tab: str, visible: bool) -> None:
        """Hide the slider (and Ctrl+plus/minus/0) on `tab` while it has nothing to zoom, e.g.
        an empty state, keeping its controller registered."""
        (self._zoom_hidden.discard if visible else self._zoom_hidden.add)(tab)
        if tab == self.current_tab():
            self._sync_zoom()

    def _zoom_gone(self, tab: str, key: int, *_args) -> None:
        self._zoom_watched.discard((tab, key))
        entry = self._zoom.get(tab)
        if entry is None or id(entry[0]) != key:
            return
        self._zoom.pop(tab, None)
        try:
            if not self._closing and tab == self.current_tab():
                self._sync_zoom()
        except RuntimeError:  # the window itself is being destroyed
            pass

    def zoom_controller(self, tab: str | None = None) -> ZoomController | None:
        tab = tab or self.current_tab()
        entry = self._zoom.get(tab)
        return entry[0] if entry and tab not in self._zoom_hidden else None

    def _zoom_call(self, method: str) -> None:
        controller = self.zoom_controller()
        if controller is not None:
            getattr(controller, method)()

    def _sync_zoom(self) -> None:
        tab = self.current_tab()
        entry = self._zoom.get(tab) if tab not in self._zoom_hidden else None
        self.zoom_slider.bind(entry[0] if entry else None, entry[1] if entry else None)
        self.zoom_slider.setVisible(entry is not None)
        for action_id in ("app.yakinlastir", "app.uzaklastir", "app.sigdir"):
            self.registry.set_enabled(action_id, entry is not None)

    # -- menus and the job switcher -------------------------------------------------------
    def toggle_menu_row(self) -> None:
        self.hide_menu_row() if self.menu_row.isVisible() else self.show_menu_row()

    def show_menu_row(self) -> None:
        m = theme.manager()
        self.menu_row.move(m.size("s2"), self.title_band.height())
        self.menu_row.show_row()
        self._set_underlines(True)

    def hide_menu_row(self) -> None:
        self.menu_row.hide()
        self._set_underlines(False)

    def open_menu(self, index: int) -> None:
        """Alt+D/E/G/T/A/Y: show the row with that menu open."""
        self.show_menu_row()
        self.menu_row.open_menu(index)

    def _row_menu_closed(self) -> None:
        popup = QApplication.activePopupWidget()
        if popup is None or popup not in self.menu_row.menus():
            self.hide_menu_row()

    def _set_underlines(self, on: bool) -> None:
        installed = style.installed_style()
        if installed is not None:
            installed.set_show_underlines(on)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if (obj is self.menu_row.bar and event.type() == QEvent.Type.FocusOut
                and event.reason() != Qt.FocusReason.PopupFocusReason):
            QTimer.singleShot(0, self, self._row_menu_closed)
        return False

    def open_job_switcher(self) -> None:
        """A's job switch: the open job, recent jobs, Yeni iş oluştur…, Tüm işler…"""
        if self.loading():
            self.message.setText(BUSY_REASON)
            return
        menu = QMenu(self)
        menu.setAccessibleName("İş değiştir")
        self._fill_switcher(menu)
        menu.popup(self.job_switch.mapToGlobal(QPoint(0, self.job_switch.height())))
        self.job_menu = menu
        self.refresh_recent_jobs()  # the menu shows the last list; a newer one replaces it

    def _fill_switcher(self, menu: QMenu) -> None:
        controller = self.controller()
        if controller is not None:
            menu.addSection("Açık iş")
            pages = sum(b.page_count for b in controller.job.batches)
            current = menu.addAction(make_icon("check"), f"{controller.job.name}\t{pages} sayfa")
            current.setEnabled(False)
        recent = self.recent_jobs()
        if recent:
            menu.addSection("Son işler")
            for job, when in recent:
                item = menu.addAction(make_icon("folder"), f"{job.name}\t{when}")
                item.triggered.connect(partial(self.yukle.open_job, job))
        menu.addSeparator()
        menu.addAction(self.registry.action("app.yeni_is"))
        every = menu.addAction(make_icon("folder-open"), "Tüm işler…")
        every.triggered.connect(self._show_all_jobs)

    def _recent_arrived(self) -> None:
        menu = getattr(self, "job_menu", None)
        if menu is not None and shiboken6.isValid(menu) and menu.isVisible():
            menu.clear()
            self._fill_switcher(menu)
        self.recent_changed.emit()

    def _show_all_jobs(self) -> None:
        self.show_tab("yukle")
        self.yukle.show_job_list()

    def recent_jobs(self) -> list[tuple[object, str]]:
        """(job, "3 gün önce") for the remembered jobs, open job left out: the list the last
        `refresh_recent_jobs` fetched (it is read in a worker, never on the window thread)."""
        controller = self.controller()
        open_id = controller.job.id if controller is not None else None
        return [(job, when) for job, when in self._recent if job.id != open_id][:5]

    def refresh_recent_jobs(self) -> None:
        """Fetch the remembered jobs in a worker; `recent_changed` fires when they are here."""
        ids = list(self.prefs.recent_jobs())
        store = self.store
        self._recent_run = run = self._recent_run + 1

        def work(_progress):
            found = []
            for job_id in ids:
                try:
                    job = store.load(job_id)
                except (KeyError, JobFileError, OSError):
                    continue
                try:
                    path = store._job_file(job_id)
                    age = time.time() - path.stat().st_mtime if path.is_file() else 0
                except OSError:
                    age = 0
                found.append((job, ago(age)))
            return found

        def done(found) -> None:
            if shiboken6.isValid(self) and run == self._recent_run and not self._closed:
                self._recent = found
                self._recent_arrived()

        task = Task(work)
        task.signals.done.connect(done, Qt.ConnectionType.QueuedConnection)
        pending = self.__dict__.setdefault("_recent_tasks", set())
        pending.add(task)  # kept until it answered: a newer run must not free it
        task.signals.done.connect(lambda _r, t=task: pending.discard(t),
                                  Qt.ConnectionType.QueuedConnection)
        task.signals.failed.connect(lambda _m, t=task: pending.discard(t),
                                    Qt.ConnectionType.QueuedConnection)
        start(task)

    # -- shared state ---------------------------------------------------------------------
    def controller(self) -> JobController | None:
        return self.yukle.controller

    def template_map(self) -> dict:
        found = {}
        damaged: list[str] = []
        for template in self.template_store.list(damaged.append):
            found[template.id] = template
        if damaged:  # a file that cannot be read is named, not skipped in silence (B-017)
            self.message.setText("Şablon dosyası okunamadı: " + ", ".join(sorted(damaged)))
        return found

    def template_undo_stack(self) -> QUndoStack:
        """The Şablonlar undo stack: Kontrol's saved-filter edits are steps on it."""
        return self.sablon.undo_stack

    def edit_template(self, template_id: str, text: str, change) -> bool:
        """Change one template for Kontrol (saved filters) and keep an undo step on the
        Şablonlar stack. The open template of Şablonlar is edited there; any other is changed
        in its file (a few hundred bytes: the write is short, so it stays on this thread).
        A TemplateError from `change` goes to the caller."""
        if self.sablon.template is not None and self.sablon.template.id == template_id:
            change(template_from_dict(template_to_dict(self.sablon.template)))  # a trial run
            done = self.sablon._edit(text, change)
            if done and self.sablon._save_error:  # the editor kept the edit but could not write
                raise OSError(self.sablon._save_error)
            return done
        try:
            template = self.template_store.load(template_id)
        except KeyError:
            raise TemplateError(f"Şablon dosyası okunamadı: {template_id}") from None
        before = template_to_dict(template)
        change(template)
        self.template_store.save(template)  # OSError goes to the caller

        def apply(data: dict) -> None:
            """Undo or redo: only the saved filters of the file as it is now are put back."""
            try:
                if self.sablon.template is not None and self.sablon.template.id == template_id:
                    self.sablon._restore(data)
                else:
                    current = self.template_store.load(template_id)
                    current.saved_filters[:] = template_from_dict(data).saved_filters
                    self.template_store.save(current)
            except (KeyError, TemplateError, OSError) as error:
                self.message.setText(
                    SAVE_FAILED if isinstance(error, OSError)
                    else f"Şablon dosyası okunamadı: {template_id}")

        self.sablon.undo_stack.push(TemplateStep(text, before, template_to_dict(template), apply))
        return True

    def _open_last_job(self) -> None:
        path = self.store.root / LAST_JOB
        try:
            job_id = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
        except OSError:
            return
        if job_id:
            self.yukle.open_job_id(job_id, quiet=True)  # loaded in a worker; a failure is silent

    # -- the loading job ------------------------------------------------------------------
    def loading(self) -> bool:
        """True while a loading job (a job open, a job delete) runs in a worker."""
        job = self._background
        return job is not None and job.running

    def loading_cancellable(self) -> bool:
        job = self._background
        return job is not None and job.running and job.cancellable

    def start_loading(self, work, **options) -> Background | None:
        """`run_background` for this window; None (nothing started) while another job loads."""
        handle = run_background(self, work, **options)
        if handle is not None:
            handle.finished.connect(self._sync_loading)
            self._sync_loading()
        return handle

    def _stop_on_degerler(self) -> None:
        """Ctrl+. on Değerler: a loading job first (it blocks the read), else the read."""
        if self.loading_cancellable():
            self.cancel_loading()
        else:
            self.degerler.cancel()

    def _stop_on_disa_aktar(self) -> None:
        if self.loading_cancellable():
            self.cancel_loading()
        else:
            self.disa_aktar.cancel()

    def cancel_loading(self) -> None:
        job = self._background
        if job is not None:
            job.cancel()

    def _sync_loading(self) -> None:
        """Commands that would start or show another job are off while one loads, each with
        the reason as its tooltip; they come back when the job ends."""
        loading = self.loading()
        for action_id in ("app.yeni_is", "app.dosya_ekle"):
            action = self.registry.action(action_id)
            if loading and action_id not in self._loading_tips:
                self._loading_tips[action_id] = action.toolTip()
            self.registry.set_enabled(action_id, not loading)
            if loading:
                action.setToolTip(BUSY_REASON)
            elif action_id in self._loading_tips:
                action.setToolTip(self._loading_tips.pop(action_id))
        for action_id in ("degerler.oku", "degerler.eksikleri_oku", "sablonlar.dene"):
            action = self.registry.action(action_id)  # their screens switch them off (reason: tip)
            if loading and action_id not in self._loading_tips:
                self._loading_tips[action_id] = action.toolTip()
            if loading:
                action.setToolTip(BUSY_REASON)
            elif action_id in self._loading_tips:
                action.setToolTip(self._loading_tips.pop(action_id))
        for button in (self.degerler.read_button, self.degerler.missing_button):
            key = "button:" + button.property("action_id")
            if loading and key not in self._loading_tips:
                self._loading_tips[key] = button.toolTip()
            if loading:
                button.setToolTip(BUSY_REASON)
            elif key in self._loading_tips:
                button.setToolTip(self._loading_tips.pop(key))
        action = self.registry.action("app.disa_aktar")
        if loading and "app.disa_aktar" not in self._loading_tips:
            self._loading_tips["app.disa_aktar"] = action.toolTip()
        self._sync_export_action()
        if loading:
            action.setToolTip(BUSY_REASON)
        elif "app.disa_aktar" in self._loading_tips:
            action.setToolTip(self._loading_tips.pop("app.disa_aktar"))
        self.yukle._sync_actions()
        self.degerler._sync_actions()
        self.sablon._sync_actions()
        self.disa_aktar._sync_actions()
        self.registry.refresh_reasons()  # the reasons read "loading": tooltips follow

    def _retire_thumbnails(self) -> None:
        """Stop and release the old job's thumbnail service (no callback into a dead view)."""
        old, self.thumbnails = self.thumbnails, None
        if self.kontrol is not None:
            self.kontrol.detach_thumbnails()  # the old screen must not call the retired service
        if old is not None:
            old.retire()  # deleted only once no render is running

    def _job_opened(self, job) -> None:
        controller = self.controller()
        self.store.root.mkdir(parents=True, exist_ok=True)
        (self.store.root / LAST_JOB).write_text(job.id, encoding="utf-8")
        self.prefs.add_recent_job(job.id)
        self.refresh_recent_jobs()
        self._retire_thumbnails()  # the previous job's renders are no longer wanted
        self.thumbnails = ThumbnailService(
            job_renderer(job, lambda: self.store.batch_files(job)), height=110, parent=self)
        kontrol = KontrolScreen(controller, self.thumbnails, self.template_map)
        kontrol.open_values.connect(self._open_in_degerler)
        self._set_kontrol_page(kontrol)
        self._track_splitters(kontrol)
        self._wire_controller(controller)
        self.setWindowTitle(f"Evrakçı {__version__} – {job.name}")
        self.job_switch.set_job(job.name)
        path = self._job_file(job.id)
        self._saved(datetime.fromtimestamp(path.stat().st_mtime) if path.is_file() else None)
        self._update_counts()
        self._sync_job_actions()
        self._fill_page_sizes(controller)

    def _fill_page_sizes(self, controller: JobController) -> None:
        """A job made before page sizes were kept has pages of unknown size: read them once from
        the batch files (no rendering) in a worker, then store them as housekeeping (no undo
        step; the job is saved). The loading card shows only if it takes long."""
        store, job_id = self.store, controller.job.id
        requests = store.size_requests(controller.job)
        if not requests:
            return
        text = "Sayfa boyutları okunuyor"

        def work(progress):
            return store.read_sizes(requests, progress)  # plain data in, plain data out

        def finish() -> None:
            if self.message.text() == text:
                self.message.setText("")

        def done(sizes) -> None:
            finish()
            current = self.controller()
            if current is controller and current.job.id == job_id:  # not another job's result
                controller.fill_page_sizes(sizes)

        handle = self.start_loading(work, title=text, name=controller.job.name, on_done=done,
                                    on_failed=lambda _message: finish(), on_cancelled=finish,
                                    cancellable=False, show_after_ms=FILL_CARD_MS,
                                    inherit_card=False)
        if handle is not None:
            self.message.setText(text)

    def _wire_controller(self, controller: JobController) -> None:
        """Connect the open job's signals once, and drop the previous job's."""
        unique = Qt.ConnectionType.UniqueConnection
        if self._wired is not controller:
            self._unwire_controller()
        self._wired = controller
        controller.status.connect(self.message.setText, unique)
        controller.job_changed.connect(self._update_counts, unique)
        controller.saving.connect(self._saving, unique)
        controller.saved.connect(self._saved_now, unique)
        controller.save_failed.connect(self._save_failed, unique)
        controller.undo_stack.indexChanged.connect(self._sync_undo, unique)
        controller.undo_stack.indexChanged.connect(self._job_stack_changed, unique)

    def _job_stack_changed(self, *_args) -> None:
        """An edit, undo or redo changed the job: Dışa Aktar plans again at once, so the
        names it shows (and writes) are current (F-disa-aktar-01)."""
        if self._closing or self.current_tab() != "disa_aktar":
            return
        try:
            self.disa_aktar.refresh()
        except RuntimeError:  # the window is being torn down
            pass

    def _unwire_controller(self) -> None:
        old, self._wired = self._wired, None
        if old is None:
            return
        for signal, slot in ((old.status, self.message.setText),
                             (old.job_changed, self._update_counts),
                             (old.saving, self._saving),
                             (old.saved, self._saved_now),
                             (old.save_failed, self._save_failed),
                             (old.undo_stack.indexChanged, self._sync_undo),
                             (old.undo_stack.indexChanged, self._job_stack_changed)):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    def _job_file(self, job_id: str) -> Path:
        """The job's job.json (JobStore's own path; pipeline is left as it is, D13)."""
        return self.store._job_file(job_id)

    def _set_kontrol_page(self, page: QWidget) -> None:
        """Swap the Kontrol tab's widget, keeping the current tab where it was."""
        current = self.tabs.currentIndex()
        self._restoring = True
        old = self.tabs.widget(1)
        self.tabs.removeTab(1)
        self.tabs.insertTab(1, page, TAB_NAMES[1])
        self.tabs.setCurrentIndex(current)
        self._restoring = False
        if old is not self._kontrol_placeholder and old is not page:
            old.deleteLater()
        self.kontrol = page if isinstance(page, KontrolScreen) else None
        self._tab_changed(self.tabs.currentIndex())

    def close_job(self) -> None:
        """İşi kapat (Ctrl+W): back to "İş açılmadı"; the job stays in the job list."""
        controller = self.controller()
        if controller is None:
            return
        reason = self._switch_refusal()
        if reason:
            self.message.setText(reason)
            return

        def leave(ok: bool) -> None:  # the job's changes are on disk (or the failure is shown)
            if ok and self.controller() is controller:
                self._close_open_job()

        self._settle_job(leave)

    def _close_open_job(self) -> None:
        self._close_warned = False
        self._discard_ok = False
        self._unwire_controller()
        self.yukle._close_now()  # the screen's own reset (its close_job comes back here)
        self._retire_thumbnails()
        self._set_kontrol_page(self._kontrol_placeholder)
        (self.store.root / LAST_JOB).unlink(missing_ok=True)
        self.setWindowTitle(f"Evrakçı {__version__}")
        self.job_switch.set_job(None)
        self._update_counts()
        self._sync_job_actions()
        self.refresh_current()

    def _job_deleted(self) -> None:
        """The job's files are gone (delete after export): close it, so nothing writes its
        job.json back (F-disa-aktar-03, B-008)."""
        self._close_open_job()

    def _saved(self, when: datetime | None = None) -> None:
        self._close_warned = False
        self._discard_ok = False
        self.job_switch.save_state.set_saved(when or datetime.now())

    def _save_failed(self, error: str) -> None:
        self._close_warned = False  # a new failed edit: the next close warns again
        self._discard_ok = False
        self.job_switch.save_state.set_failed(f"Kaydedilemedi: {error}", self.save_job)

    def _saved_now(self, *_args) -> None:
        self._saved()

    def _saving(self) -> None:
        """A write is pending (the saver's queue is not empty): "Kaydediliyor…"."""
        self.job_switch.save_state.set_saving()

    def set_status_counts(self, tab: str, visible: bool) -> None:
        """Show or hide the window's own job counts at the start of `tab`'s status line
        (by default only where the mockup draws them, STATUS_COUNTS)."""
        self._status_counts[tab] = bool(visible)
        if tab == self.current_tab():
            self._sync_status_counts()

    def set_export_running(self, running: bool) -> None:
        """"Dışa aktarılıyor" in the status bar while an export writes, on every tab but Dışa
        Aktar (that tab's own line has the count)."""
        self._export_running = bool(running)
        self._sync_export_status()

    def _sync_export_status(self) -> None:
        item = getattr(self, "export_status", None)
        if item is not None:
            item.setVisible(getattr(self, "_export_running", False)
                            and self.current_tab() != "disa_aktar")

    def status_counts_shown(self, tab: str | None = None) -> bool:
        return self._status_counts.get(tab or self.current_tab(), False)

    def _sync_status_counts(self) -> None:
        if not hasattr(self, "counts"):
            return
        shown = self.status_counts_shown()
        for label in (self.counts, self.pages):
            label.setVisible(shown and bool(label.text()))
        checks = shown and bool(self.checks.text())
        self.checks.setVisible(checks)
        self.check_icon.setVisible(checks)

    def _update_counts(self) -> None:
        controller = self.controller()
        if controller is None:
            self.counts.set()
            self.pages.set()
            self.checks.setText("")
            self._sync_status_counts()
            return
        job = controller.job
        pages = sum(b.page_count for b in job.batches)
        documents = len(controller.documents())
        checks = len(self.kontrol.strip.check_rows) if self.kontrol else 0
        self.counts.set("", str(documents), " belge")
        self.pages.set("", str(pages), " sayfa")
        self.checks.setText(f"{checks} belge kontrol bekliyor" if checks else "")
        self._sync_status_counts()

    def _tab_changed(self, index: int) -> None:
        if not hasattr(self, "registry") or not hasattr(self, "title_tabs") or index < 0:
            return
        tab = TAB_IDS[index]
        if self.title_tabs.currentIndex() != index:
            self.title_tabs.blockSignals(True)
            self.title_tabs.setCurrentIndex(index)
            self.title_tabs.blockSignals(False)
            self.title_tabs.refresh()
            if hasattr(self, "title_band"):  # its currentChanged hook was blocked above:
                self.title_band.fit()  # show the new tab (option b keeps it in the strip)
                self.title_band.update()  # and its right foot
        self.registry.set_context(tab)
        self._sync_tab_labels(tab)
        self._sync_export_action()
        if hasattr(self, "command_bars"):
            self.command_bars.setCurrentIndex(index)
        if hasattr(self, "status_slots"):
            self.status_slots.setCurrentIndex(index)
            self._sync_export_status()
            self._sync_zoom()
            self._sync_status_counts()
        self._sync_undo()
        self._sync_inspector()
        if self._restoring:
            return
        self.prefs.set_last_tab(index)
        if tab == "sablonlar":
            self.sablon.refresh_templates()
        elif tab == "degerler":
            self.degerler.refresh()
        elif tab == "disa_aktar":
            self.disa_aktar.refresh()

    def _sync_tab_labels(self, tab: str) -> None:
        """Two app-wide items say what they do on this tab (M-03, M-20): Ctrl+F opens the go-to
        dialog on Kontrol, and Ctrl+0 puts thumbnails and guide text back to the default size."""
        registry = self.registry
        for action_id, tabs, text, tip in (
                ("app.bul", ("kontrol",), "&Belgeye veya sayfaya git…",
                 "Belgeye veya sayfaya git"),
                ("app.sigdir", ("kontrol", "rehber"), "&Varsayılan boyut",
                 "Varsayılan boyuta dön")):
            action, spec = registry.action(action_id), registry.spec(action_id)
            if tab in tabs:
                action.setText(text)
                action.setToolTip(f"{tip} ({actions.key_text(spec.shortcuts[0])})")
            else:
                action.setText(spec.text)
                action.setToolTip(actions.tooltip_for(spec))

    def _open_in_degerler(self, number: int) -> None:
        """Kontrol's "Değerlerde aç": Değerler with that document selected, focus in its table."""
        if not self.degerler.has_document(number):
            return
        self.show_tab("degerler")
        self.degerler.select_document(number)
        self.focus_work_area()

    def _open_in_kontrol(self, number: int) -> None:
        """Değerler's "Kontrol'de aç": Kontrol with that document current, focus in its timeline."""
        if self.kontrol is None:
            return
        self.show_tab("kontrol")
        self.kontrol.go_to_document(number)
        self.focus_work_area()
        if self.kontrol.current_document() == number:
            self.controller().status.emit(f"Belge {number} seçildi.")

    def _draw_variant(self, document: int, variable: str) -> None:
        self.show_tab("sablonlar")
        controller = self.controller()
        template_id = None
        if controller is not None:
            from evrakci.pipeline.cuts import document_template

            template_id, _ = document_template(controller.job,
                                               controller.documents()[document - 1])
        if template_id:
            try:
                self.sablon.open_template(template_id)
            except (KeyError, TemplateError):
                return
            self.sablon.select_variable(variable)
            self.sablon.set_example(document)
            self.sablon.set_drawing(True)

    # -- persistence ----------------------------------------------------------------------
    def _restore_state(self) -> None:
        self.prefs.restore_window(self)
        index = self.prefs.last_tab()
        self.tabs.setCurrentIndex(index if 0 <= index < len(TAB_IDS) else 0)

    def _track_splitters(self, root: QWidget) -> None:
        """Restore and remember the sizes of every named QSplitter under `root`."""
        for splitter in root.findChildren(QSplitter):
            name = splitter.objectName()
            if not name or id(splitter) in self._splitters:
                continue
            self._splitters.add(id(splitter))
            sizes = self.prefs.splitter_sizes(name)
            if len(sizes) == splitter.count():
                splitter.setSizes(sizes)
            splitter.splitterMoved.connect(partial(self._splitter_moved, splitter))

    def _splitter_moved(self, splitter: QSplitter, *_args) -> None:
        self.prefs.set_splitter_sizes(splitter.objectName(), splitter.sizes())

    # -- look -----------------------------------------------------------------------------
    def _restyle(self) -> None:
        """After a theme, density or text-size switch: icons and title-band geometry."""
        set_action_icons(self.registry)
        self.title_tabs.refresh()
        self.title_band.refresh()
        self.job_switch.refresh()
        self.search.refresh()
        self.menu_button.setIcon(make_icon("menu"))
        for bar in self._bars.values():
            bar.refresh()
        self._pad_status_bar()
        m = theme.manager()
        size = m.inline_icon()
        self.check_icon.setFixedSize(size, size)
        self.check_icon.setPixmap(icons.pixmap("triangle-alert", m.hex("rider-edge"), size))
        if self.frame is not None:
            self.frame.set_dark(m.theme() == "dark")

    def showEvent(self, event) -> None:  # noqa: N802
        if not getattr(self, "_styled", False):
            self._styled = True
            self._restyle()
            if self.frame is not None:
                self.frame.attach()
                self.frame.set_dark(theme.manager().theme() == "dark")
            # A fresh window starts in its work area, not on the title tabs, where the focus
            # would sit with no ring (a window becoming active shows none; D11, Q-16). The
            # reason is the window's own, so no ring appears either.
            self.focus_work_area(Qt.FocusReason.ActiveWindowFocusReason)
        super().showEvent(event)

    def changeEvent(self, event) -> None:  # noqa: N802
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "title_band"):
            button = self.title_band.caption.get("max")
            if button is not None:
                button.restored = self.isMaximized()
                button.setToolTip("Önceki boyutuna getir" if self.isMaximized()
                                  else "Ekranı kapla")
                button.update()
        super().changeEvent(event)

    def nativeEvent(self, event_type, message):  # noqa: N802
        if self.frame is not None:
            handled = self.frame.native_event(message)
            if handled is not None:
                return handled
        return super().nativeEvent(event_type, message)

    # -- closing --------------------------------------------------------------------------
    def _switch_refusal(self) -> str | None:
        if self.loading() or self.yukle.swapping:
            return BUSY_REASON
        if self._busy_screens():
            return "Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın."
        return None

    def _unsaved_pending(self) -> bool:
        """Whether leaving the job (close, Ctrl+W, a job switch) must first wait for the saver:
        something is queued, or the last write failed (B-035): every attempt retries the save, and
        only the owner's Yes to the close question (`_discard_ok`) lets unsaved edits go."""
        controller = self.controller()
        if controller is None or controller.frozen or controller.saver.clean:
            return False
        saver = controller.saver
        return not (self._discard_ok and (saver.idle or saver.stalled))

    def _settle_job(self, then: Callable[[bool], None]) -> None:
        """Make the file on disk equal the open job, then call `then(True)`; at once when it is
        already so. After a failed write the save is tried again first; when that fails too (or
        the write we waited for failed) the status says "Kaydedilemedi: ..." (B-035), the next
        attempt goes ahead, and `then(False)` is called: the job stays open. The window thread
        never blocks: the call comes back from the event loop."""
        controller = self.controller()
        if controller is None or not self._unsaved_pending():
            then(True)
            return
        if self._question_open():  # the question is already up: it is the only way on
            then(False)
            return
        saver = controller.saver
        if saver.idle:  # the last write failed: write the job again now
            controller.save_now()

        def written(ok: bool, error: str) -> None:
            if not shiboken6.isValid(self):
                return
            if ok:
                then(True)
                return
            self._close_warned = True  # after the saver's own signal reset it
            self.message.setText(f"Kaydedilemedi: {error}")
            then(False)
            self._ask_close_unsaved(then)  # Yes drops the edits and goes on, No stays

        saver.when_idle(written)

    def _busy_screens(self) -> list:
        return [s for s in (self.disa_aktar, self.yukle, self.degerler) if s.busy()]

    def closeEvent(self, event) -> None:  # noqa: N802
        busy = self._busy_screens()
        if busy and not self._closing:
            answer = QMessageBox.question(
                self, "Evrakçı",
                "Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._closing = True
            for screen in busy:
                screen.cancel()
        if busy:  # close once the work has stopped (see _work_stopped)
            self.message.setText("Durduruluyor… Pencere iş durunca kapanır.")
            event.ignore()
            return
        if self._question_open():  # the question is the only way out
            event.ignore()
            return
        if self._unsaved_pending():  # write what is queued first, then close from the event loop
            def written(ok: bool) -> None:
                if ok:
                    QTimer.singleShot(0, self, self.close)  # also after the question's Yes
                else:  # the close is refused: later edits and tasks go on as usual
                    self._closing = False  # _settle_job has asked the question

            self._settle_job(written)
            event.ignore()
            return
        self.cancel_loading()  # the close goes ahead: the loading job first, its late result drops
        self._closed = True
        self.prefs.save_window(self)
        QApplication.instance().removeEventFilter(self.alt_menus)
        event.accept()

    def _question_open(self) -> bool:
        dialog = getattr(self, "_close_question", None)
        return dialog is not None and shiboken6.isValid(dialog) and dialog.isVisible()

    def _question_answered(self, code: int, then: Callable[[bool], None]) -> None:
        if code == QMessageBox.StandardButton.Yes and shiboken6.isValid(self):
            self._discard_ok = True  # only this answer lets the edits go
            then(True)

    def _ask_close_unsaved(self, then: Callable[[bool], None]) -> None:
        """The save failed again: Yes closes anyway (the last changes are lost), No keeps the job
        open. The question does not block the event loop, so a close can never get stuck (B-035);
        the status line keeps the reason and a second close attempt also goes ahead."""
        if self._question_open():
            return
        dialog = QMessageBox(
            QMessageBox.Icon.Question, "Evrakçı",
            "Değişiklikler kaydedilemedi. Yine de kapatılsın mı? Son değişiklikler kaybolur.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.finished.connect(lambda code: self._question_answered(code, then))
        self._close_question = dialog
        dialog.open()

    def _work_stopped(self) -> None:
        if self._closing and not self._busy_screens():
            QTimer.singleShot(0, self, self.close)


__all__ = ["COMMANDS", "LAST_JOB", "TAB_IDS", "TAB_NAMES", "Cmd", "MainWindow", "default_prefs",
           "first_focusable"]
