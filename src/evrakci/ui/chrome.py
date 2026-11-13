"""Window chrome of direction A (final-a/shell.css): the parts of the title band, the per-tab
command bar, the floating menu row shown on Alt, and the About dialog.

Every colour and size comes from `theme.manager()`; the look is in the app stylesheet (objectName
titleBand, titleTabs, jobSwitch, searchBox, menuButton, commandBar; kind caption-button, command,
icon, separator) and in EvrakciStyle (A's selected title tab with its feet).
"""
from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QFont,
    QFontMetrics,
    QIcon,
    QKeyEvent,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QStyle,
    QStyleOptionToolButton,
    QStylePainter,
    QTabBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from evrakci import __version__
from evrakci.ui import actions, icons, theme
from evrakci.ui.feedback import SaveState

# A's tab icons (kontrol.html .tabs).
TAB_ICONS = {"yukle": "upload", "kontrol": "layout-grid", "sablonlar": "layout-template",
             "degerler": "table", "disa_aktar": "file-output", "rehber": "book-open"}
CAPTION_W = 46  # A .caption span


def make_icon(name: str, role: str = "icon", size: int | None = None, stroke: float = 1.75,
              selected: str | None = None) -> QIcon:
    """A Lucide icon in a theme role: Normal/Active in `role`, Selected in `selected`
    (default `role`), Disabled in icon-disabled. Stroke 1.75 at 16 px, 1.6 at 20 px (A)."""
    m = theme.manager()
    size = size or m.size("icon-sm")
    result = QIcon()
    for mode, colour in ((QIcon.Mode.Normal, role), (QIcon.Mode.Active, role),
                         (QIcon.Mode.Selected, selected or role),
                         (QIcon.Mode.Disabled, "icon-disabled")):
        result.addPixmap(icons.pixmap(name, m.hex(colour), size, 2.0, stroke), mode)
    return result


def set_action_icons(registry: actions.Registry) -> None:
    """Give every registry action its Lucide icon in the `icon` role (menus, palette); an
    action marked `danger` (A's red delete item) keeps its icon in the `danger` role."""
    for spec in actions.SPECS:
        action = registry.action(spec.id)
        name = action.property("lucide")
        if name:
            action.setIcon(make_icon(name, "danger" if action.property("danger") else "icon"))


def mark_danger(menu: QMenu, action: QAction) -> None:
    """Paint `action` in `danger` in this menu when it is marked destructive (property
    `danger`). QSS cannot select one item, so the item is the menu's default action, which the
    sheet draws in `danger` (QMenu::item:default)."""
    if action.property("danger"):
        menu.setDefaultAction(action)


# -- title band parts -----------------------------------------------------------------------
class TitleTabs(QTabBar):
    """A's six title-band tabs: icon + label, the selected one filled with feet (EvrakciStyle).

    When the band is too narrow (150 % text on a 1366 px window), the tabs that do not fit are
    hidden here and listed in the band's "»" menu (owner's option b); the order and Ctrl+1–6
    stay, and the selected tab is always one of the visible ones.
    """

    def __init__(self, tabs: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titleTabs")
        self.setAccessibleName("Sekmeler")
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setUsesScrollButtons(False)
        self.setElideMode(Qt.TextElideMode.ElideNone)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._tabs = tabs  # (tab id, label)
        self._labels: str | None = None  # "all" / "selected"; None: the title-band rule
        for index, (tab, label) in enumerate(tabs):
            self.addTab(label)
            self.setAccessibleTabName(index, label)
            self.setTabData(index, tab)
        self.currentChanged.connect(lambda _i: self.refresh())
        self.refresh()

    def label(self, index: int) -> str:
        return self._tabs[index][1]

    def tab_id(self, index: int) -> str:
        return self._tabs[index][0]

    def full_widths(self) -> list[int]:
        """Each tab's width with its icon and name (measured whether or not it is shown)."""
        return [self.tabSizeHint(i).width() for i in range(self.count())]

    def set_shown(self, indices: set[int]) -> None:
        """Show these tabs, hide the rest (they are in the "»" menu)."""
        changed = False
        for index in range(self.count()):
            visible = index in indices
            if self.isTabVisible(index) != visible:
                self.setTabVisible(index, visible)
                changed = True
        if changed:
            self.updateGeometry()  # the band's layout caches the strip's size

    def hidden_tabs(self) -> list[int]:
        return [i for i in range(self.count()) if not self.isTabVisible(i)]

    def set_label_mode(self, mode: str) -> None:
        """"all" or "selected" (TitleBand decides it from the rule and its width)."""
        if mode != self._labels:
            self._labels = mode
            self.refresh()

    def label_mode(self) -> str:
        return self._labels or theme.manager().title_band().tab_labels

    def refresh(self) -> None:
        """Icons for the current theme and labels per the title-band rule."""
        only_selected = self.label_mode() == "selected"
        for index, (tab, label) in enumerate(self._tabs):
            self.setTabIcon(index, make_icon(TAB_ICONS[tab], "text-2", selected="accent"))
            show = not only_selected or index == self.currentIndex()
            if self.tabText(index) != (label if show else ""):
                self.setTabText(index, label if show else "")


class TitleSaveState(SaveState):
    """SaveState as A draws it in the job switch: the saved check in `ok` at 14 px."""

    def _refresh_icon(self) -> None:
        if not self._glyph:
            return
        role = "ok" if self._state == "saved" else self._role
        size = theme.manager().inline_icon()  # grows with the text size
        self._icon.setFixedSize(size, size)
        self._icon.setPixmap(icons.pixmap(self._glyph, theme.manager().hex(role), size))


class _Clickable(QWidget):
    """A widget that acts as a button: click, Enter or Space emits `clicked`."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
                event.position().toPoint()):
            self.clicked.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


class ElidedLabel(QLabel):
    """A one-line label that shrinks to `min_chars` characters and elides the rest with "…";
    `full_text()` is the whole text (also its tooltip)."""

    def __init__(self, text: str = "", min_chars: int = 6, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._full = ""
        self._min_chars = min_chars
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def setText(self, text: str) -> None:  # noqa: N802
        self._full = text
        super().setText(text)
        self.setToolTip(text)
        self.updateGeometry()

    def full_text(self) -> str:
        return self._full

    def displayed_text(self) -> str:
        width = self.contentsRect().width()
        return self.fontMetrics().elidedText(self._full, Qt.TextElideMode.ElideRight, width)

    def is_elided(self) -> bool:
        return self.displayed_text() != self._full

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        hint = super().minimumSizeHint()
        short = self.fontMetrics().horizontalAdvance("M" * self._min_chars + "…")
        return QSize(min(hint.width(), short), hint.height())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        self.style().drawItemText(painter, self.contentsRect(),
                                  int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                                  self.palette(), self.isEnabled(), self.displayed_text(),
                                  self.foregroundRole())


class JobSwitch(_Clickable):
    """Job name + "Kaydedildi 14:32" + chevron; a click opens the job switcher."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("jobSwitch")
        m = theme.manager()
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s3"), 0, m.size("s2"), 0)
        row.setSpacing(m.size("s2"))
        self.name = ElidedLabel("İş açılmadı")  # long names elide; the full name is the tooltip
        self.name.setObjectName("jobName")
        self.save_state = TitleSaveState()
        self.chevron = QLabel()
        for widget in (self.name, self.save_state, self.chevron):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            row.addWidget(widget)
        self.setToolTip("İş değiştir")
        self.refresh()

    def set_job(self, name: str | None) -> None:
        self.name.setText(name or "İş açılmadı")
        self.setToolTip(f"{name}. İş değiştir" if name else "İş değiştir")
        if name is None:
            self.save_state.hide()
        self.setAccessibleName(f"Açık iş: {name}. İş değiştir" if name else "İş açılmadı. İş aç")

    def refresh(self) -> None:
        m = theme.manager()
        self.chevron.setPixmap(icons.pixmap("chevron-down", m.hex("text-2"), m.size("icon-sm")))
        self.save_state._refresh_icon()


class SearchBox(QPushButton):
    """A's title-band search: "Ara" with "Ctrl+K" at the right; opens the command palette."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("searchBox")
        self.setAccessibleName("Ara (Ctrl+K)")
        self.setToolTip("Komut ara (Ctrl+K)")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        m = theme.manager()
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s3"), 0, m.size("s3"), 0)
        row.setSpacing(m.size("s2"))
        self.glyph = QLabel()
        self.word = QLabel("Ara")
        self.keys = QLabel(actions.key_text("Ctrl+K"))
        row.addWidget(self.glyph)
        row.addWidget(self.word)
        row.addStretch(1)
        row.addWidget(self.keys)
        for label in (self.glyph, self.word, self.keys):
            label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.refresh()

    def refresh(self) -> None:
        m = theme.manager()
        self.glyph.setPixmap(icons.pixmap("search", m.hex("text-2"), m.size("icon-sm")))
        self.setStyleSheet(f"QLabel {{ color: {m.hex('text-2')}; "
                           f"font-size: {m.size('fs-caption')}px; }}")
        band = m.title_band()  # after setStyleSheet, which re-applies the app's min/max size
        self.setFixedSize(band.search_width, band.control_height)  # A .search, border included


class CaptionButton(QAbstractButton):
    """Minimise / maximise / close, painted the Windows 11 way (46 x 32, 10 px glyphs)."""

    def __init__(self, glyph: str, tip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.glyph = glyph  # "min", "max", "close"
        self.setProperty("kind", "caption-button")
        self.setToolTip(tip)
        self.setAccessibleName(tip)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # the window menu (Alt+Space) has them
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.restored = False  # max glyph: two squares when the window is maximised
        self._nc_hover = False
        self._nc_down = False

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(CAPTION_W, theme.manager().title_band().control_height)

    def set_native_state(self, hover: bool, down: bool = False) -> None:
        """Hover/press reported by WM_NC* messages (the snap-layout maximise button)."""
        if (hover, down) != (self._nc_hover, self._nc_down):
            self._nc_hover, self._nc_down = hover, down
            self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        hover = self.underMouse() or self._nc_hover
        down = self.isDown() or self._nc_down
        ink = m.color("icon")
        if self.glyph == "close" and (hover or down):
            painter.fillRect(self.rect(), m.color("danger"))
            ink = m.color("text-on-accent")
        elif down:
            painter.fillRect(self.rect(), m.color("pressed"))
        elif hover:
            painter.fillRect(self.rect(), m.color("hover"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(ink, 1))
        c = QPointF(self.width() / 2, self.height() / 2)
        if self.glyph == "min":
            painter.drawLine(QPointF(c.x() - 5, c.y() + 0.5), QPointF(c.x() + 5, c.y() + 0.5))
        elif self.glyph == "max" and not self.restored:
            painter.drawRoundedRect(QRectF(c.x() - 4.5, c.y() - 4.5, 9, 9), 1, 1)
        elif self.glyph == "max":
            painter.drawRoundedRect(QRectF(c.x() - 4.5, c.y() - 2.5, 7, 7), 1, 1)
            painter.drawPolyline([QPointF(c.x() - 2.5, c.y() - 4.5), QPointF(c.x() + 4.5,
                                  c.y() - 4.5), QPointF(c.x() + 4.5, c.y() + 2.5)])
        else:
            painter.drawLine(QPointF(c.x() - 5, c.y() - 5), QPointF(c.x() + 5, c.y() + 5))
            painter.drawLine(QPointF(c.x() + 5, c.y() - 5), QPointF(c.x() - 5, c.y() + 5))


# -- command bar ----------------------------------------------------------------------------
def group_label(text: str) -> QLabel:
    """A .group-label: the small heading above a group of inspector cards."""
    label = QLabel(text)
    label.setProperty("kind", "group-label")
    return label


def card(margins: int | None = None) -> QFrame:
    """A .card frame. With `margins` (px) it also gets a QVBoxLayout with those margins and
    s2 spacing, reachable as card.layout()."""
    frame = QFrame()
    frame.setProperty("kind", "card")
    if margins is not None:
        col = QVBoxLayout(frame)
        col.setContentsMargins(margins, margins, margins, margins)
        col.setSpacing(theme.manager().size("s2"))
    return frame


class RecentJobRow(QPushButton):
    """A .recent .act .r (Yükle and Kontrol empty pages): folder icon, the job's name
    (elided with its full name in the tooltip) and "640 sayfa, dün" at the right."""

    def __init__(self, name: str, detail: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setProperty("kind", "inspector-row")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumHeight(m.size("row-h"))
        self.setAccessibleName(f"{name} işini aç, {detail}")
        self.setToolTip(f"{name} işini aç")
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s3"), 0, m.size("s3"), 0)
        row.setSpacing(m.size("s3"))
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.name = ElidedLabel(name, min_chars=12)
        self.detail = QLabel(detail)
        self.detail.setProperty("textRole", "secondary")
        for widget in (self.icon, self.name, self.detail):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        row.addWidget(self.icon)
        row.addWidget(self.name, 1)
        row.addWidget(self.detail)
        self.refresh()

    def refresh(self) -> None:
        m = theme.manager()
        self.icon.setPixmap(icons.pixmap("folder", m.hex("icon"), 16))
        self.detail.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = self.layout().sizeHint()
        return QSize(hint.width(), max(hint.height(), theme.manager().size("row-h")))


class ActionButton(QToolButton):
    """A command-bar button that mirrors a QAction (enabled, visible, checked, tooltip)."""

    def __init__(self, action: QAction, label: bool = False, icon: str | None = None,
                 text: str | None = None, parent: QWidget | None = None,
                 hide_disabled: bool = False) -> None:
        super().__init__(parent)
        self.action_ = action
        self.hide_disabled = hide_disabled  # shown only while the command can run (İptal et)
        self.icon_name = icon or action.property("lucide") or "square"
        self._gate = None  # a screen's own extra condition (see set_gate)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        if label:
            self.setProperty("kind", "command")
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.setText(text or actions.plain_text(action.text()).rstrip("…"))
        else:
            self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.clicked.connect(action.trigger)
        action.changed.connect(self._sync)
        self.refresh()
        self._sync()

    def labelled(self) -> bool:
        return self.toolButtonStyle() != Qt.ToolButtonStyle.ToolButtonIconOnly

    def label_font(self) -> QFont:
        """A's .cmd label: body size at weight 500 (measured and painted with this font)."""
        return theme.manager().font("body-medium")

    def text_rect(self) -> QRect:
        """Where the label goes: s2 + icon + s2 from the left, s3 from the right (A .cmd)."""
        m = theme.manager()
        left = 2 * m.size("s2") + self.iconSize().width()
        return QRect(left, 0, max(0, self.width() - left - m.size("s3")), self.height())

    def refresh(self) -> None:
        """Icon for the theme and A's box: 36 px square, or s2 + icon + s2 + label + s3."""
        m = theme.manager()
        size = m.size("icon-md")
        self.setIconSize(QSize(size, size))
        self.setIcon(make_icon(self.icon_name, "icon", size, 1.6))
        side = m.size("icon-btn")
        if not self.labelled():
            self.setFixedSize(side, side)
        else:
            text = QFontMetrics(self.label_font()).horizontalAdvance(self.text())
            self.setFixedSize(2 * m.size("s2") + size + text + m.size("s3"), side)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Labelled: the style draws the box (hover, pressed, focus); icon and label are
        placed here with A's 8 px gap, which ToolButtonTextBesideIcon cannot give."""
        if not self.labelled():
            super().paintEvent(event)
            return
        painter = QStylePainter(self)
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        option.text, option.icon = "", QIcon()
        painter.drawComplexControl(QStyle.ComplexControl.CC_ToolButton, option)
        m = theme.manager()
        size = self.iconSize().width()
        mode = QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled
        self.icon().paint(painter, QRect(m.size("s2"), (self.height() - size) // 2, size, size),
                          Qt.AlignmentFlag.AlignCenter, mode)
        painter.setFont(self.label_font())
        painter.setPen(m.color("text" if self.isEnabled() else "text-disabled"))
        painter.drawText(self.text_rect(), Qt.AlignmentFlag.AlignVCenter
                         | Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextSingleLine, self.text())

    def set_gate(self, gate) -> None:
        """An extra condition for this button only (Yükle's "Kontrol'e geç" is off while a
        batch is read, though Ctrl+2 still switches tabs). The button never calls
        setEnabled from outside, so an action change or a restyle cannot undo it."""
        self._gate = gate
        self._sync()

    def _sync(self) -> None:
        action = self.action_
        enabled = action.isEnabled() and (self._gate is None or bool(self._gate()))
        self.setEnabled(enabled)
        self.setVisible(action.isVisible() and (enabled or not self.hide_disabled))
        self.setCheckable(action.isCheckable())
        if action.isCheckable():
            self.setChecked(action.isChecked())
        self.setToolTip(action.toolTip())
        self.setAccessibleName(action.toolTip())


class CommandBar(QWidget):
    """A's icon-first command bar (44 px, 36 px buttons, at most three labels)."""

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("commandBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAccessibleName(f"{name} komutları")
        m = theme.manager()
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(m.size("s2"), 0, m.size("s2"), 0)
        self._row.setSpacing(2)
        self._buttons: list[QToolButton] = []

    def add_action(self, action: QAction, label: bool = False, icon: str | None = None,
                   text: str | None = None, hide_disabled: bool = False) -> ActionButton:
        """An icon button (or icon + label) that triggers `action`; `icon` overrides its Lucide
        name and `text` its label; `hide_disabled` shows it only while the action is enabled."""
        button = ActionButton(action, label, icon, text, self, hide_disabled)
        self._row.addWidget(button)
        self._buttons.append(button)
        return button

    def add_separator(self) -> QFrame:
        line = QFrame(self)
        line.setProperty("kind", "separator")
        self._row.addWidget(line)
        return line

    def add_stretch(self) -> None:
        self._row.addStretch(1)

    def add_widget(self, widget: QWidget) -> None:
        self._row.addWidget(widget)

    def add_more(self, fill: Callable[[QMenu], None]) -> QToolButton:
        """The "Diğer komutlar" (…) button; `fill` puts the items in its menu when it opens."""
        button = QToolButton(self)
        button.setObjectName("moreButton")
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        button.setToolTip("Diğer komutlar")
        button.setAccessibleName("Diğer komutlar")
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setProperty("lucide", "ellipsis")
        menu = QMenu(button)
        menu.aboutToShow.connect(lambda: (menu.clear(), fill(menu)))
        button.setMenu(menu)
        self._row.addWidget(button)
        self._buttons.append(button)
        self._refresh_more(button)
        return button

    def _refresh_more(self, button: QToolButton) -> None:
        size = theme.manager().size("icon-md")
        side = theme.manager().size("icon-btn")
        button.setFixedSize(side, side)
        button.setIconSize(QSize(size, size))
        button.setIcon(make_icon("ellipsis", "icon", size, 1.6))
        button.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0; }")

    def buttons(self) -> list[QToolButton]:
        return list(self._buttons)

    def button_for(self, action_id: str) -> ActionButton | None:
        """The bar's button of the registry action `action_id` (its objectName), or None."""
        return next((b for b in self._buttons if isinstance(b, ActionButton)
                     and b.action_.objectName() == action_id), None)

    def refresh(self) -> None:
        for button in self._buttons:
            if isinstance(button, ActionButton):
                button.refresh()
            else:
                self._refresh_more(button)


# -- the floating menu row (Alt) ------------------------------------------------------------
class MenuRow(QFrame):
    """The six menus as a row on A's popover surface; shown on Alt, never at rest."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("menuRow")
        m = theme.manager()
        layout = QHBoxLayout(self)
        pad = m.size("s1")
        layout.setContentsMargins(pad, pad, pad, pad)
        self.bar = QMenuBar(self)
        self.bar.setNativeMenuBar(False)
        self.bar.setAccessibleName("Menü çubuğu")
        self.bar.setStyleSheet("QMenuBar { background: transparent; }")
        layout.addWidget(self.bar)
        self.hide()

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(m.color("stroke"), 1))
        painter.setBrush(m.color("popover"))
        radius = m.size("r-layer")
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

    def menus(self) -> list[QMenu]:
        return [a.menu() for a in self.bar.actions() if a.menu() is not None]

    def open_menu(self, index: int) -> None:
        """Show the row with menu `index` open."""
        self.show_row()
        self.bar.setActiveAction(self.bar.actions()[index])

    def show_row(self) -> None:
        self.adjustSize()
        self.show()
        self.raise_()
        self.bar.setFocus(Qt.FocusReason.ShortcutFocusReason)


# -- About ----------------------------------------------------------------------------------
def _roots() -> list[Path]:
    here = Path(__file__).resolve()
    return [here.parents[3], Path(sys.executable).resolve().parent]


def license_files() -> list[Path]:
    """Licence texts shipped with the app (packaging/licenses, or licenses/ in the build)."""
    for root in _roots():
        for folder in (root / "packaging" / "licenses", root / "licenses"):
            if folder.is_dir():
                return sorted(folder.glob("*.txt"))
    return []


def license_rows() -> list[tuple[str, str]]:
    """(component, licence) from docs/dependency-licenses.md, when it is there."""
    for root in _roots():
        path = root / "docs" / "dependency-licenses.md"
        if path.is_file():
            break
    else:
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not line.startswith("|") or set(cells[0]) <= set("-: "):
            continue
        name = re.sub(r"\s*\(.*\)$", "", cells[0]).replace("**", "").replace("`", "")
        if name and name != "Dependency":
            rows.append((name, cells[1].replace("**", "")))
    return rows


class AboutDialog(QDialog):
    """Evrakçı hakkında: logo, version, licence and the bundled components' licences."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle("Evrakçı hakkında")
        self.setMinimumSize(520, 480)
        m = theme.manager()
        root = QVBoxLayout(self)
        root.setContentsMargins(*(m.size("s6"),) * 4)
        root.setSpacing(m.size("s4"))
        head = QHBoxLayout()
        head.setSpacing(m.size("s4"))
        logo = QLabel()
        logo.setPixmap(icons.app_icon().pixmap(64, 64))
        logo.setAccessibleName("Evrakçı logosu")
        head.addWidget(logo)
        words = QVBoxLayout()
        title = QLabel("Evrakçı")
        title.setProperty("textRole", "panel")
        self.version = QLabel(f"Sürüm {__version__}")
        self.version.setProperty("textRole", "secondary")
        licence = QLabel("Lisans: AGPL-3.0-or-later")
        licence.setProperty("textRole", "secondary")
        for widget in (title, self.version, licence):
            words.addWidget(widget)
        head.addLayout(words, 1)
        root.addLayout(head)
        label = QLabel("Kullanılan bileşenler ve lisansları")
        label.setProperty("kind", "group-label")
        root.addWidget(label)
        self.components = QTreeWidget()
        self.components.setColumnCount(2)
        self.components.setHeaderLabels(["Bileşen", "Lisans"])
        self.components.setRootIsDecorated(False)
        self.components.setAccessibleName("Bileşenler ve lisansları")
        for name, kind in license_rows():
            self.components.addTopLevelItem(QTreeWidgetItem([name, kind]))
        for path in license_files():
            self.components.addTopLevelItem(QTreeWidgetItem([f"Lisans metni: {path.stem}",
                                                             path.name]))
        self.components.resizeColumnToContents(0)
        root.addWidget(self.components, 1)
        buttons = QHBoxLayout()
        folder = QPushButton("Lisans klasörünü aç")
        files = license_files()
        folder.setEnabled(bool(files))
        if files:
            folder.clicked.connect(lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(files[0].parent))))
        buttons.addWidget(folder)
        buttons.addStretch(1)
        close = QPushButton("Kapat")
        close.setObjectName("primary")
        close.setDefault(True)
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        root.addLayout(buttons)
