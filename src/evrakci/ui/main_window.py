"""The main window in direction A: title band, a command bar per tab, the work layer and the
status bar, wired to the action registry. The six screens are hosted unchanged."""

from __future__ import annotations

import time
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import NamedTuple

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import QUndoStack
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci import __version__
from evrakci.pipeline.store import JobFileError, JobStore, default_root
from evrakci.pipeline.templates.model import TemplateError
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import actions, icons, kontrol_empty, motion, style, theme
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
from evrakci.ui.kontrol_actions import KontrolStatus
from evrakci.ui.palette import CommandPalette
from evrakci.ui.prefs import Prefs
from evrakci.ui.rehber import RehberScreen
from evrakci.ui.sablon import SablonScreen
from evrakci.ui.settings_dialog import SettingsDialog
from evrakci.ui.shortcut_sheet import ShortcutSheet
from evrakci.ui.taskbar import TaskbarProgress
from evrakci.ui.thumbnails import ThumbnailService, job_renderer
from evrakci.ui.titlebar import TitleBand, WindowsFrame, use_custom_frame
from evrakci.ui.yukle import YukleScreen
from evrakci.ui.zoomview import ZoomController, ZoomSlider

TAB_IDS = tuple(actions.TABS)
TAB_NAMES = list(actions.TABS.values())
LAST_JOB = "son-is.txt"
PREFS_FILE = "arayuz.ini"


class Cmd(NamedTuple):
    """One command-bar entry: a registry action, labelled or icon-only, A's icon and label;
    `hide_disabled` keeps the button out of the bar while the command cannot run."""

    id: str
    label: bool = False
    icon: str | None = None
    text: str | None = None
    hide_disabled: bool = False


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
                Cmd("kontrol.kes", True, "scissors", "Kes"), Cmd("kontrol.birlestir"),
                Cmd("kontrol.saga_dondur"), Cmd("kontrol.sil"), SEP,
                Cmd("kontrol.sablon", icon="stamp"), Cmd("kontrol.filtre"), GROW,
                Cmd("kontrol.sonraki_kontrol", True), Cmd("kontrol.sonraki_incelenmemis"),
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
TEXT_STEPS = theme.TEXT_SIZES
STATUS_INSET = 2  # QStatusBar's own item margin


def default_prefs(store: JobStore) -> Prefs:
    """The user's prefs for the real job folder; a file beside any other job folder (tests)."""
    try:
        real = store.root.resolve() == default_root().resolve()
    except OSError:
        real = False
    return Prefs() if real else Prefs(store.root.parent / PREFS_FILE)


def _ago(seconds: float) -> str:
    """Turkish relative time: "az önce", "3 gün önce", "2 hafta önce"..."""
    minutes = int(seconds // 60)
    for size, word in ((525600, "yıl"), (43200, "ay"), (10080, "hafta"), (1440, "gün"),
                       (60, "saat"), (1, "dakika")):
        if minutes >= size:
            count = minutes // size
            return "dün" if word == "gün" and count == 1 else f"{count} {word} önce"
    return "az önce"


def _accepts_tab(widget: QWidget) -> bool:
    return (widget.isVisible() and widget.isEnabled()
            and bool(widget.focusPolicy().value & Qt.FocusPolicy.TabFocus.value))


def first_focusable(region: QWidget) -> QWidget | None:
    """The first widget inside `region` (or itself) that Tab would stop on."""
    if _accepts_tab(region):
        return region
    widget = region.nextInFocusChain()
    for _ in range(2000):
        if widget is None or widget is region:
            return None
        if region.isAncestorOf(widget) and _accepts_tab(widget):
            return widget
        widget = widget.nextInFocusChain()
    return None


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
        self._restoring = True
        self._zoom: dict[str, tuple[ZoomController, str]] = {}
        self._zoom_hidden: set[str] = set()
        self._status_counts: dict[str, bool] = {tab: tab in STATUS_COUNTS for tab in TAB_IDS}
        self._splitters: set[int] = set()
        self._wired: JobController | None = None  # the controller whose signals are connected

        self.registry = actions.Registry(self)
        self.registry.install_text_guard()
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

        self._restore_state()
        self._restoring = False
        self._tab_changed(self.tabs.currentIndex())
        self._open_last_job()

    # -- building -------------------------------------------------------------------------
    def _build_screens(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().hide()  # the title band's TitleTabs drive it
        self.yukle = YukleScreen(self.store)
        self.yukle.job_opened.connect(self._job_opened)
        self.yukle.can_switch = self._switch_refusal
        self.sablon = SablonScreen(self.template_store, self.controller)
        self.degerler = DegerlerScreen(self.controller, self.template_map)
        self.degerler.draw_variant.connect(self._draw_variant)
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
        self.counts = QLabel("")
        self.pages = QLabel("")
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
            menu.aboutToHide.connect(lambda: QTimer.singleShot(0, self._row_menu_closed))
            sub = QMenu(actions.plain_text(title), self.app_menu)
            sub.aboutToShow.connect(partial(self._fill_menu, sub, title))
            item = self.app_menu.addMenu(sub)
            item.setText(f"{title}\tAlt+{actions.access_key(title)}")
            item.setObjectName(f"menu.{key}")
        self.menu_button.setMenu(self.app_menu)
        self.menu_row.bar.installEventFilter(self)

    def _fill_menu(self, menu: QMenu, title: str) -> None:
        menu.clear()
        items = dict(actions.menu_structure(self.registry.context))[title]
        for item in items:
            if item is None:
                menu.addSeparator()
            else:
                menu.addAction(self.registry.action(item))

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
                                   entry.text, entry.hide_disabled)
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
        r.connect("app.sonraki_sekme", lambda: self.cycle_tab(1))
        r.connect("app.onceki_sekme", lambda: self.cycle_tab(-1))
        r.connect("app.sonraki_bolge", lambda: self.focus_region(1))
        r.connect("app.onceki_bolge", lambda: self.focus_region(-1))
        r.connect("app.yeni_is", self._new_job)
        r.connect("app.dosya_ekle", self._add_files)
        r.connect("app.kaydet", lambda: self.sablon.save())
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
        r.connect("app.yenile", self.refresh_current)
        r.connect("app.ayarlar", self.open_settings)
        r.connect("app.yardim", lambda: self.show_tab("rehber"))
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
        r.connect("degerler.elle_yaz", self.degerler.type_current)
        r.connect("degerler.varyant", lambda: self.degerler.side.variant_button.click())
        r.connect("degerler.sonraki_kontrol", self.degerler.next_check)
        r.connect("degerler.durdur", self.degerler.cancel)
        # The screen's two (hidden) read buttons hold the enabled state; the bar's commands
        # click them.
        for action_id, button in (("degerler.oku", self.degerler.read_button),
                                  ("degerler.eksikleri_oku", self.degerler.missing_button)):
            r.connect(action_id, button.click)
            _EnabledMirror(button, partial(self.registry.set_enabled, action_id))
        r.connect("app.yan_panel", self.toggle_inspector)
        r.connect("disa_aktar.durdur", self.disa_aktar.cancel)
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
        if side is not None:
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

    def _sync_job_actions(self) -> None:
        has_job = self.controller() is not None
        self.registry.set_enabled("app.isi_kapat", has_job)
        self.registry.set_enabled("app.disa_aktar", has_job)
        self._sync_undo()

    def _show_tab_slot(self, tab: str, *_args) -> None:
        self.show_tab(tab)

    def show_tab(self, tab: str) -> None:
        self.tabs.setCurrentIndex(TAB_IDS.index(tab))

    def current_tab(self) -> str:
        return TAB_IDS[self.tabs.currentIndex()]

    def cycle_tab(self, step: int) -> None:
        self.tabs.setCurrentIndex((self.tabs.currentIndex() + step) % len(TAB_IDS))

    def focus_region(self, step: int) -> None:
        """F6 / Shift+F6: title band, command bar, work area, status bar."""
        regions = [self.title_band, self.command_bars.currentWidget(),
                   self.tabs.currentWidget(), self.statusBar()]
        focus = QApplication.focusWidget()
        current = next((i for i, r in enumerate(regions)
                        if focus is not None and (focus is r or r.isAncestorOf(focus))), -1)
        for offset in range(1, len(regions) + 1):
            region = regions[(current + step * offset) % len(regions)]
            target = first_focusable(region)
            if target is not None:
                target.setFocus(Qt.FocusReason.TabFocusReason)
                return

    def _new_job(self) -> None:
        self.show_tab("yukle")
        self.yukle.choose_new_job()

    def _add_files(self) -> None:
        self.show_tab("yukle")
        self.yukle.choose_batch()

    def _export(self) -> None:
        if self.current_tab() == "disa_aktar":
            self.disa_aktar.export()
        else:
            self.show_tab("disa_aktar")

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
        self.settings_dialog.open()

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
        if self.current_tab() == "sablonlar":
            return self.sablon.undo_stack
        controller = self.controller()
        return controller.undo_stack if controller is not None else None

    def undo(self) -> None:
        stack = self._undo_stack()
        if stack is not None and stack.canUndo():
            stack.undo()

    def redo(self) -> None:
        stack = self._undo_stack()
        if stack is not None and stack.canRedo():
            stack.redo()

    def _sync_undo(self, *_args) -> None:
        """Geri al / Yinele name the step they act on, in the Düzen menu, the command bar's
        tooltip and the palette: "Geri al: Kesim ekle (Ctrl+Z)"."""
        stack = self._undo_stack()
        for action_id, can, what in (("app.geri_al", "canUndo", "undoText"),
                                     ("app.yinele", "canRedo", "redoText")):
            try:
                enabled = stack is not None and getattr(stack, can)()
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
        entry = self._zoom.get(tab)
        if entry is not None and id(entry[0]) == key:
            self._zoom.pop(tab, None)
            if not self._closing and tab == self.current_tab():
                self._sync_zoom()

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
            QTimer.singleShot(0, self._row_menu_closed)
        return False

    def open_job_switcher(self) -> None:
        """A's job switch: the open job, recent jobs, Yeni iş oluştur…, Tüm işler…"""
        menu = QMenu(self)
        menu.setAccessibleName("İş değiştir")
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
        menu.popup(self.job_switch.mapToGlobal(QPoint(0, self.job_switch.height())))
        self.job_menu = menu

    def _show_all_jobs(self) -> None:
        self.show_tab("yukle")
        self.yukle.show_job_list()

    def recent_jobs(self) -> list[tuple[object, str]]:
        """(job, "3 gün önce") for the remembered jobs that still exist, open job left out."""
        controller = self.controller()
        open_id = controller.job.id if controller is not None else None
        found = []
        for job_id in self.prefs.recent_jobs():
            if job_id == open_id:
                continue
            try:
                job = self.store.load(job_id)
            except (KeyError, JobFileError, OSError):
                continue
            path = self._job_file(job_id)
            age = time.time() - path.stat().st_mtime if path.is_file() else 0
            found.append((job, _ago(age)))
        return found[:5]

    # -- shared state ---------------------------------------------------------------------
    def controller(self) -> JobController | None:
        return self.yukle.controller

    def template_map(self) -> dict:
        found = {}
        for template in self.template_store.list():
            found[template.id] = template
        return found

    def _open_last_job(self) -> None:
        path = self.store.root / LAST_JOB
        if not path.is_file():
            return
        try:
            job = self.store.load(path.read_text(encoding="utf-8").strip())
        except (KeyError, JobFileError, OSError):
            return
        self.yukle.open_job(job)

    def _job_opened(self, job) -> None:
        controller = self.controller()
        self.store.root.mkdir(parents=True, exist_ok=True)
        (self.store.root / LAST_JOB).write_text(job.id, encoding="utf-8")
        self.prefs.add_recent_job(job.id)
        if self.thumbnails is not None:
            self.thumbnails.stop()  # the previous job's renders are no longer wanted
        self.thumbnails = ThumbnailService(
            job_renderer(job, lambda: self.store.batch_files(job)), height=110, parent=self)
        kontrol = KontrolScreen(controller, self.thumbnails, self.template_map)
        kontrol.open_values.connect(lambda _n: self.show_tab("degerler"))
        self._set_kontrol_page(kontrol)
        self._track_splitters(kontrol)
        self._wire_controller(controller)
        self.setWindowTitle(f"Evrakçı {__version__} – {job.name}")
        self.job_switch.set_job(job.name)
        path = self._job_file(job.id)
        self._saved(datetime.fromtimestamp(path.stat().st_mtime) if path.is_file() else None)
        self._update_counts()
        self._sync_job_actions()

    def _wire_controller(self, controller: JobController) -> None:
        """Connect the open job's signals once, and drop the previous job's."""
        unique = Qt.ConnectionType.UniqueConnection
        if self._wired is not controller:
            self._unwire_controller()
        self._wired = controller
        controller.status.connect(self.message.setText, unique)
        controller.job_changed.connect(self._update_counts, unique)
        controller.job_changed.connect(self._saved_now, unique)
        controller.undo_stack.indexChanged.connect(self._sync_undo, unique)

    def _unwire_controller(self) -> None:
        old, self._wired = self._wired, None
        if old is None:
            return
        for signal, slot in ((old.status, self.message.setText),
                             (old.job_changed, self._update_counts),
                             (old.job_changed, self._saved_now),
                             (old.undo_stack.indexChanged, self._sync_undo)):
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
        self._unwire_controller()
        self.yukle._close_now()  # the screen's own reset (its close_job comes back here)
        if self.thumbnails is not None:
            self.thumbnails.stop()
            self.thumbnails = None
        self._set_kontrol_page(self._kontrol_placeholder)
        (self.store.root / LAST_JOB).unlink(missing_ok=True)
        self.setWindowTitle(f"Evrakçı {__version__}")
        self.job_switch.set_job(None)
        self._update_counts()
        self._sync_job_actions()
        self.refresh_current()

    def _job_deleted(self) -> None:
        (self.store.root / LAST_JOB).unlink(missing_ok=True)
        self.yukle.refresh_jobs()

    def _saved(self, when: datetime | None = None) -> None:
        self.job_switch.save_state.set_saved(when or datetime.now())

    def _saved_now(self, *_args) -> None:
        self._saved()

    def set_status_counts(self, tab: str, visible: bool) -> None:
        """Show or hide the window's own job counts at the start of `tab`'s status line
        (by default only where the mockup draws them, STATUS_COUNTS)."""
        self._status_counts[tab] = bool(visible)
        if tab == self.current_tab():
            self._sync_status_counts()

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
            for label in (self.counts, self.pages, self.checks):
                label.setText("")
            self._sync_status_counts()
            return
        job = controller.job
        pages = sum(b.page_count for b in job.batches)
        documents = len(controller.documents())
        checks = len(self.kontrol.strip.check_rows) if self.kontrol else 0
        self.counts.setText(f"{documents} belge")
        self.pages.setText(f"{pages} sayfa")
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
        self.registry.set_context(tab)
        self.registry.set_enabled("app.kaydet", tab == "sablonlar")
        if hasattr(self, "command_bars"):
            self.command_bars.setCurrentIndex(index)
        if hasattr(self, "status_slots"):
            self.status_slots.setCurrentIndex(index)
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
        self.check_icon.setPixmap(icons.pixmap("triangle-alert", m.hex("rider-edge"), 14))
        if self.frame is not None:
            self.frame.set_dark(m.theme() == "dark")

    def showEvent(self, event) -> None:  # noqa: N802
        if not getattr(self, "_styled", False):
            self._styled = True
            self._restyle()
            if self.frame is not None:
                self.frame.attach()
                self.frame.set_dark(theme.manager().theme() == "dark")
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
        if self._busy_screens():
            return "Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın."
        return None

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
        self.prefs.save_window(self)
        QApplication.instance().removeEventFilter(self.alt_menus)
        event.accept()

    def _work_stopped(self) -> None:
        if self._closing and not self._busy_screens():
            QTimer.singleShot(0, self.close)


__all__ = ["COMMANDS", "LAST_JOB", "TAB_IDS", "TAB_NAMES", "Cmd", "MainWindow", "default_prefs",
           "first_focusable"]
