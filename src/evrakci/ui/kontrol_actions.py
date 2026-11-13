"""Kontrol's commands, wired once per window, the right-click menu and the status-bar items.

`KontrolBinder` connects every Kontrol registry action to the KontrolScreen of the open job, and
disables them while no job is open, so a key never silently does nothing. A new job's screen
simply takes over. App-wide commands Kontrol answers (Ctrl+G) are routed to it only while it is
the current tab (`Registry.connect_tab`).

`context_menu()` is A's page menu (final-a/kontrol.html): "3 sayfa seçili", Burada kes,
Önceki belgeyle birleştir | Sağa / Sola döndür | Şablon uygula ›, Filtre uygula… | Önizle,
Değerlerde aç | "3 sayfayı sil". Every item is the registry action, so it shows its key.

`KontrolStatus` fills the window's Kontrol status slot as A draws it: Belge 16 / 96,
Sayfa 73 / 640, 3 sayfa seçili, ⚠ 7 belge kontrol bekliyor, ✓ 58 / 96 incelendi.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

import shiboken6
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenu, QWidget, QWidgetAction

from evrakci.ui import actions, icons, theme
from evrakci.ui.chrome import make_icon, mark_danger

# Every Kontrol command and the KontrolScreen method (+ arguments) that does it.
SCREEN_SLOTS: dict[str, tuple] = {
    "kontrol.kes": ("toggle_cut",), "kontrol.birlestir": ("merge_current",),
    "kontrol.saga_dondur": ("rotate_selected", 90), "kontrol.sola_dondur": ("rotate_selected", -90),
    "kontrol.sil": ("toggle_delete",), "kontrol.filtre": ("apply_filter",),
    "kontrol.sablon": ("apply_template",),
    "kontrol.sonraki_kontrol": ("jump_to_check", 1),
    "kontrol.onceki_kontrol": ("jump_to_check", -1),
    "kontrol.tumunu_sec": ("select_all",),
    "kontrol.secimi_kaldir": ("escape",),
    "kontrol.onayla": ("approve_document",),
    "kontrol.degerlerde_ac": ("open_in_values",),
    "kontrol.onizle": ("toggle_loupe",),
    "kontrol.sonraki_incelenmemis": ("next_unreviewed",),
    "kontrol.sonraki_belge": ("jump_document", 1),
    "kontrol.onceki_belge": ("jump_document", -1),
    "app.git": ("go_to",),
}
APP_SHARED = {"app.git"}  # app-wide commands Kontrol answers only while it is the current tab


class KontrolBinder(QObject):
    """One per registry: routes Kontrol's commands to the current KontrolScreen."""

    NAME = "kontrolBinder"

    def __init__(self, registry: actions.Registry) -> None:
        super().__init__(registry)
        self.setObjectName(self.NAME)
        self.registry = registry
        self._screen = None
        self._screen_id = 0
        self.ids = list(SCREEN_SLOTS)
        for action_id in self.ids:
            method, *args = SCREEN_SLOTS[action_id]
            slot = partial(self._call, action_id, method, *args)
            if action_id in APP_SHARED:
                registry.connect_tab(action_id, "kontrol", slot)
            else:
                registry.connect(action_id, slot)
        self._sync()

    @classmethod
    def for_registry(cls, registry: actions.Registry) -> KontrolBinder:
        found = registry.findChild(KontrolBinder, cls.NAME)
        return found if found is not None else cls(registry)

    def screen(self):
        """The open job's screen, or None once the window has let it go (job closed): it is
        the window's `kontrol`, or at least still one of its tabs."""
        screen = self._screen
        if screen is None or not shiboken6.isValid(screen):
            return None
        window = self.registry.parent()
        tabs = getattr(window, "tabs", None)
        if getattr(window, "kontrol", screen) is screen or tabs is None:
            return screen
        return screen if tabs.indexOf(screen) >= 0 else None

    def attach(self, screen) -> None:
        self._screen = screen
        self._screen_id = id(screen)
        screen.destroyed.connect(partial(self._gone, id(screen)))
        self._sync()

    def _gone(self, screen_id: int, *_args) -> None:
        if screen_id == self._screen_id:
            self._screen = None
            self._screen_id = 0
            self._sync()

    def sync(self) -> None:
        self._sync()

    def _sync(self) -> None:
        alive = self.screen() is not None
        try:
            for action_id in self.ids:
                if action_id in APP_SHARED:
                    self.registry.set_enabled_for(action_id, "kontrol", alive)
                else:
                    self.registry.set_enabled(action_id, alive)
        except RuntimeError:  # the window is being torn down
            pass

    def _call(self, action_id: str, method: str, *args) -> None:
        screen = self.screen()
        if screen is None:
            window = self.registry.parent()
            message = getattr(window, "message", None)
            if isinstance(message, QLabel):
                message.setText("Önce Yükle sekmesinden bir iş açın (Ctrl+1).")
            return
        getattr(screen, method)(*args)


# -- context menu ---------------------------------------------------------------------------
def _header(menu: QMenu, text: str) -> None:
    """A .menu .mh: a caption heading naming what the menu acts on."""
    m = theme.manager()
    label = QLabel(text)
    label.setProperty("kind", "group-label")
    label.setStyleSheet(f"margin: 0; padding: {m.size('s1') + 2}px {m.size('s3')}px "
                        f"{m.size('s1')}px {m.size('s3')}px;")
    label.setAccessibleName(text)
    item = QWidgetAction(menu)
    item.setDefaultWidget(label)
    item.setEnabled(False)
    menu.addAction(item)


def context_menu(screen, action: Callable[[str], QAction], parent: QWidget) -> QMenu:
    """A's page menu for the current selection. `action(id)` gives the command's QAction."""
    count = len(screen.selected_ids())
    menu = QMenu(parent)
    menu.setAccessibleName(f"{count} sayfa")
    _header(menu, f"{count} sayfa seçili")
    for item in ("kontrol.kes", "kontrol.birlestir", None, "kontrol.saga_dondur",
                 "kontrol.sola_dondur", None):
        if item is None:
            menu.addSeparator()
        else:
            menu.addAction(action(item))
    templates = sorted(screen.templates().items(), key=lambda kv: kv[1].name)
    sub = QMenu("Şablon uygula", menu)
    sub.setIcon(make_icon("stamp"))
    sub.setAccessibleName("Şablon uygula")
    for template_id, template in templates:
        sub.addAction(template.name, partial(screen.apply_template, template_id))
    if not templates:
        sub.addAction("Önce Şablonlar sekmesinde bir şablon oluşturun").setEnabled(False)
    menu.addMenu(sub)
    menu.addAction(action("kontrol.filtre"))
    menu.addSeparator()
    menu.addAction(action("kontrol.onizle"))
    menu.addAction(action("kontrol.degerlerde_ac"))
    menu.addSeparator()
    delete = action("kontrol.sil")
    menu.addAction(delete)
    mark_danger(menu, delete)  # A's red "3 sayfayı sil"
    return menu


def fallback_action(screen, action_id: str, parent: QObject) -> QAction:
    """A plain QAction for a screen used without a window (tests, previews)."""
    spec = actions.spec(action_id)
    keys = actions.key_text(spec.shortcuts[0]) if spec.shortcuts else ""
    text = actions.plain_text(spec.text) + (f"\t{keys}" if keys else "")
    item = QAction(text, parent)
    item.setObjectName(action_id)
    method, *args = SCREEN_SLOTS[action_id]
    item.triggered.connect(lambda *_: getattr(screen, method)(*args))
    if spec.icon:
        item.setIcon(make_icon(spec.icon))
    return item


# -- status bar -----------------------------------------------------------------------------
class KontrolStatus(QWidget):
    """The Kontrol status-bar items; one per window, shared by the screen and the empty state."""

    NAME = "kontrolStatus"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(self.NAME)
        m = theme.manager()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(m.size("s6"))
        self.document = QLabel()
        self.page = QLabel()
        self.selected = QLabel()
        self.checks_icon, self.checks = QLabel(), QLabel()
        self.reviewed_icon, self.reviewed = QLabel(), QLabel()
        self.empty = QLabel("İşler Yükle sekmesinde açılır (Ctrl+1)")
        row.addWidget(self.document)
        row.addWidget(self.page)
        row.addWidget(self.selected)
        for icon, label in ((self.checks_icon, self.checks), (self.reviewed_icon, self.reviewed)):
            pair = QHBoxLayout()
            pair.setSpacing(6)  # A .statusbar .warn gap
            pair.addWidget(icon)
            pair.addWidget(label)
            row.addLayout(pair)
        row.addWidget(self.empty)
        self._values: tuple | None = None
        theme.follow(self, self.refresh)
        self.set_empty()

    @classmethod
    def in_slot(cls, slot: QWidget) -> KontrolStatus:
        found = slot.findChild(KontrolStatus, cls.NAME)
        if found is None:
            found = cls(slot)
            layout = slot.layout()
            if layout is not None:
                layout.addWidget(found)
        return found

    def _b(self, text: object) -> str:
        return (f'<b style="color:{theme.manager().hex("text")}; font-weight:600">'
                f"{text}</b>")

    def set_empty(self) -> None:
        self._values = None
        for widget in (self.document, self.page, self.selected, self.checks_icon, self.checks,
                       self.reviewed_icon, self.reviewed):
            widget.hide()
        self.empty.show()

    def set_counts(self, document: int, documents: int, page: int, pages: int, selected: int,
                   checks: int, reviewed: int) -> None:
        self._values = (document, documents, page, pages, selected, checks, reviewed)
        self.empty.hide()
        b = self._b
        self.document.setText(f"Belge {b(document)} / {documents}" if document else
                              f"{documents} belge")
        self.page.setText(f"Sayfa {b(page)} / {pages}" if page else f"{pages} sayfa")
        self.selected.setText(f"{b(selected)} sayfa seçili")
        self.checks.setText(f"{b(checks)} belge kontrol bekliyor")
        self.reviewed.setText(f"{b(reviewed)} / {documents} incelendi")
        self.document.setAccessibleName(f"Belge {document} / {documents}")
        self.page.setAccessibleName(f"Sayfa {page} / {pages}")
        self.selected.setAccessibleName(f"{selected} sayfa seçili")
        self.checks.setAccessibleName(f"{checks} belge kontrol bekliyor")
        self.reviewed.setAccessibleName(f"{reviewed} / {documents} belge incelendi")
        for widget in (self.document, self.page, self.reviewed_icon, self.reviewed):
            widget.show()
        self.selected.setVisible(selected > 0)
        self.checks_icon.setVisible(checks > 0)
        self.checks.setVisible(checks > 0)
        self.refresh(icons_only=True)

    def refresh(self, icons_only: bool = False) -> None:
        m = theme.manager()
        self.checks_icon.setPixmap(icons.pixmap("triangle-alert", m.hex("rider-edge"), 14))
        self.reviewed_icon.setPixmap(icons.pixmap("circle-check", m.hex("ok"), 14))
        if not icons_only and self._values is not None:
            self.set_counts(*self._values)

    def texts(self) -> list[str]:
        """The visible items as plain text (tests, screen readers)."""
        return [w.accessibleName() or w.text() for w in (
            self.document, self.page, self.selected, self.checks, self.reviewed, self.empty)
            if w.isVisibleTo(self)]


def label_delete(registry: actions.Registry | None, count: int, restore: bool) -> str:
    """Del's label names what it does: "Sayfayı sil", "3 sayfayı sil", "Sayfayı geri getir"."""
    if restore:
        text = "Sayfayı geri &getir" if count <= 1 else f"{count} sayfayı geri &getir"
    else:
        text = "Sayfayı &sil" if count <= 1 else f"{count} sayfayı si&l"
    if registry is not None:
        item = registry.action("kontrol.sil")
        item.setText(text)
        item.setIconText(actions.plain_text(text))
        key = actions.key_text("Del")
        item.setToolTip(f"{actions.plain_text(text)} (geri alınabilir) ({key})")
        item.setProperty("danger", not restore)
        item.setIcon(make_icon("trash-2", "danger" if not restore else "icon"))
    return actions.plain_text(text)


__all__ = ["SCREEN_SLOTS", "KontrolBinder", "KontrolStatus", "context_menu", "fallback_action",
           "label_delete"]
