"""Saved filters as chips (I-07): the row above Kontrol's overview, the dialog that names a new
filter and the undo step of a template edit made from Kontrol.

A chip is one saved filter of the template in the inspector. On = accent fill and a check mark,
off = an outline and an empty ring (never colour alone). Turned-on chips narrow the pages (AND,
`select.select_pages`); the count line says how many filters are on and how many pages they give.
A chip whose kind this version does not know is inert and says "Tanınmıyor". The row is built
only from tokens, 32 px high at least, text 13 px or more, and wraps onto more lines when it
does not fit (150 % text, many chips).

Keys inside the row (local, like kontrol.sayfa): Left / Right move between chips, Space and Enter
turn one on or off, Del deletes it (undoable), Esc goes back to the timeline. Only one chip is
in the Tab order (the one last used), so Tab enters and leaves the row in one step.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QAction, QFontMetrics, QPainter, QPen, QUndoCommand
from PySide6.QtWidgets import (
    QAbstractButton,
    QDialog,
    QLabel,
    QLayout,
    QLayoutItem,
    QLineEdit,
    QMenu,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QWidgetItem,
)

from evrakci.pipeline.templates.model import TemplateError, validate_filter_name
from evrakci.ui import icons, theme

ROW_LABEL = "Kayıtlı filtreler"
SAVE_TEXT = "Kayıtlı filtrelere ekle…"
NOT_KNOWN = "Tanınmıyor"
NOT_KNOWN_TIP = "Bu filtreyi bu sürüm tanımıyor"
NO_TEMPLATE = "Şablon yok"
NONE_ON = "Hiçbir filtre açık değil"
CHIP_MIN_H = 32
MIN_NAME_CHARS = 12  # a name is never cut below this many characters


def count_text(filters_on: int, pages: int) -> str:
    """"3 filtre açık: 7 sayfa", or "Hiçbir filtre açık değil"."""
    return f"{filters_on} filtre açık: {pages} sayfa" if filters_on else NONE_ON


@dataclass(frozen=True)
class ChipInfo:
    name: str
    known: bool = True
    count: int | None = None  # pages this filter gives alone; None while not counted


# -- layout ---------------------------------------------------------------------------------
class FlowLayout(QLayout):
    """Left to right, wrapping onto new lines; the `trailing` item goes to the right edge of
    the last line (or onto a line of its own when it does not fit there)."""

    def __init__(self, parent: QWidget, h_gap: int, v_gap: int) -> None:
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._trailing: QLayoutItem | None = None
        self._gaps = (h_gap, v_gap)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item: QLayoutItem) -> None:  # noqa: N802
        self._items.append(item)

    def add_trailing(self, widget: QWidget) -> None:
        self.addChildWidget(widget)
        self._trailing = QWidgetItem(widget)
        self.invalidate()

    def insert_widget(self, index: int, widget: QWidget) -> None:
        self.addChildWidget(widget)
        self._items.insert(index, QWidgetItem(widget))
        self.invalidate()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:  # noqa: N802
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index: int) -> QLayoutItem | None:  # noqa: N802
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def hasHeightForWidth(self) -> bool:  # noqa: N802
        return True

    def heightForWidth(self, width: int) -> int:  # noqa: N802
        return self._place(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect: QRect) -> None:  # noqa: N802
        super().setGeometry(rect)
        self._place(rect, apply=True)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self.minimumSize()

    def minimumSize(self) -> QSize:  # noqa: N802
        size = QSize()
        for item in (*self._items, *([self._trailing] if self._trailing else [])):
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def _visible(self) -> list[QLayoutItem]:
        return [i for i in self._items if i.widget() is None or not i.widget().isHidden()]

    def _place(self, rect: QRect, apply: bool) -> int:
        margins = self.contentsMargins()
        inner = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        h_gap, v_gap = self._gaps
        lines: list[list[QLayoutItem]] = [[]]
        used = 0
        for item in self._visible():
            width = item.sizeHint().width()
            if lines[-1] and used + h_gap + width > inner.width():
                lines.append([])
                used = 0
            used += (h_gap if lines[-1] else 0) + width
            lines[-1].append(item)
        tail = self._trailing
        if tail is not None and not tail.widget().isHidden():
            if not lines[-1] or used + h_gap + tail.sizeHint().width() > inner.width():
                lines.append([])
        heights = [max((i.sizeHint().height() for i in line), default=0) for line in lines]
        if tail is not None and not tail.widget().isHidden():
            heights[-1] = max(heights[-1], tail.sizeHint().height())
        y = inner.y()
        if apply:
            for line, line_h in zip(lines, heights, strict=True):
                x = inner.x()
                for item in line:
                    size = item.sizeHint()
                    item.setGeometry(QRect(QPoint(x, y + (line_h - size.height()) // 2), size))
                    x += size.width() + h_gap
                y += line_h + v_gap
            if tail is not None:
                if tail.widget().isHidden():
                    tail.setGeometry(QRect(0, 0, 0, 0))
                else:
                    size = tail.sizeHint()
                    line_y = y - v_gap - heights[-1]
                    tail.setGeometry(QRect(
                        QPoint(inner.right() + 1 - size.width(),
                               line_y + (heights[-1] - size.height()) // 2), size))
        total = sum(heights) + v_gap * (len(heights) - 1) if any(heights) else 0
        return total + margins.top() + margins.bottom()


# -- the chip -------------------------------------------------------------------------------
class FilterChip(QAbstractButton):
    """One saved filter. Checkable; an unknown kind stays unchecked and says why."""

    delete_requested = Signal(str)
    menu_requested = Signal(str, QPoint)

    PAD = 12
    ICON = 16
    GAP = 6
    CLOSE = 24

    def __init__(self, info: ChipInfo, row: ChipRow) -> None:
        super().__init__(row)
        self.info = info
        self.row = row
        self.setCheckable(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setProperty("focusRadius", CHIP_MIN_H // 2)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._hover = False
        self._over_close = False
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(
            lambda pos: self.menu_requested.emit(self.info.name, self.mapToGlobal(pos)))
        self.refresh()
        theme.follow(self, self.refresh)

    # -- state --------------------------------------------------------------------------------
    def refresh(self) -> None:
        self._describe()
        self._tooltip()
        self.updateGeometry()
        self.update()

    def _tooltip(self) -> None:
        """"Bu filtreyi bu sürüm tanımıyor" for an unknown kind; the whole name when it is cut."""
        if not self.info.known:
            self.setToolTip(NOT_KNOWN_TIP)
        else:
            self.setToolTip(self.info.name if self._text_room() < self._text_width() else "")

    def _text_room(self) -> int:
        return self.width() - (self.PAD + self.ICON + self.GAP) - self.GAP - self.CLOSE \
            - self._tail_width()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._tooltip()

    def _describe(self) -> None:
        state = ", açık" if self.isChecked() else ""
        self.setAccessibleName(f"{self.info.name}{state}")
        self.setAccessibleDescription(
            NOT_KNOWN_TIP if not self.info.known else (
                "0 sayfa" if self.info.count == 0 else ""))

    def nextCheckState(self) -> None:  # noqa: N802
        if not self.info.known:
            self.row.inert_pressed.emit(self.info.name)  # never silent
            return
        super().nextCheckState()

    def checkStateSet(self) -> None:  # noqa: N802
        self._describe()

    def tail_text(self) -> str:
        if not self.info.known:
            return NOT_KNOWN
        return "0" if self.info.count == 0 else ""

    # -- size and paint -----------------------------------------------------------------------
    def _font(self):
        return theme.manager().font("body-medium")

    def _text_width(self, limit: int | None = None) -> int:
        metrics = QFontMetrics(self._font())
        width = metrics.horizontalAdvance(self.info.name) + 2  # slack: kerning in the cut
        if limit is not None and width > limit:
            width = max(limit, metrics.horizontalAdvance(self.info.name[:MIN_NAME_CHARS]))
        return width

    def _tail_width(self) -> int:
        text = self.tail_text()
        return (self.GAP + QFontMetrics(self._font()).horizontalAdvance(text)) if text else 0

    def _fixed_width(self) -> int:
        return self.PAD + self.ICON + self.GAP + self.GAP + self.CLOSE

    def _height(self) -> int:
        return max(CHIP_MIN_H, QFontMetrics(self._font()).height() + 2 * theme.manager().size("s2"))

    def sizeHint(self) -> QSize:  # noqa: N802
        room = self.row.chip_room() - self._fixed_width() - self._tail_width()
        return QSize(self._fixed_width() + self._tail_width() + self._text_width(max(room, 0)),
                     self._height())

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self.sizeHint()

    def _close_rect(self) -> QRectF:
        return QRectF(self.width() - self.PAD // 2 - self.CLOSE, (self.height() - self.CLOSE) / 2,
                      self.CLOSE, self.CLOSE)

    def _shows_close(self) -> bool:
        return self.info.known and (self._hover or self.hasFocus())

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        inert = not self.info.known
        on = self.isChecked() and not inert
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2
        if on:
            fill, edge, text, icon = ("accent-hover" if self._hover else "accent"), "accent", \
                "text-on-accent", "text-on-accent"
        elif inert:
            fill, edge, text, icon = None, "stroke-soft", "text-disabled", "icon-disabled"
        else:
            fill, edge, text, icon = ("hover" if self._hover else None), "stroke", "text", "icon"
        painter.setPen(QPen(m.color(edge), 1))
        painter.setBrush(m.color(fill) if fill else Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
        mid = self.height() / 2
        icon_rect = QRectF(self.PAD, mid - self.ICON / 2, self.ICON, self.ICON)
        if on:
            icons.paint(painter, "check", icon_rect, m.hex(icon), 2.0)
        else:  # off: an empty ring, so the state is not told by colour alone
            painter.setPen(QPen(m.color(icon), 1.75))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(icon_rect.adjusted(1.5, 1.5, -1.5, -1.5))
        x = self.PAD + self.ICON + self.GAP
        tail = self.tail_text()
        room = self._text_room()
        painter.setFont(self._font())
        painter.setPen(m.color(text))
        metrics = QFontMetrics(self._font())
        shown = metrics.elidedText(self.info.name, Qt.TextElideMode.ElideRight, max(0, room))
        painter.drawText(QRectF(x, 0, room, self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, shown)
        if tail:
            tail_x = x + min(room, metrics.horizontalAdvance(shown)) + self.GAP
            painter.setPen(m.color("text-on-accent" if on else "text-2"))  # the word is read
            painter.drawText(QRectF(tail_x, 0, self.width() - tail_x, self.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, tail)
        if self._shows_close():
            close = self._close_rect()
            if self._over_close:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(m.color("pressed" if not on else "accent-hover"))
                painter.drawEllipse(close.adjusted(2, 2, -2, -2))
            icons.paint(painter, "x", close.adjusted(5, 5, -5, -5), m.hex(icon), 2.0)

    # -- mouse --------------------------------------------------------------------------------
    def enterEvent(self, event) -> None:  # noqa: N802
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover, self._over_close = False, False
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        over = self._shows_close() and self._close_rect().contains(event.position())
        if over != self._over_close:
            self._over_close = over
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if (event.button() == Qt.MouseButton.LeftButton and self._shows_close()
                and self._close_rect().contains(event.position())):
            self.setDown(False)
            self.delete_requested.emit(self.info.name)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def hitButton(self, pos) -> bool:  # noqa: N802
        return self.rect().contains(pos) and not (
            self._shows_close() and self._close_rect().contains(QPointF(pos)))

    def focusInEvent(self, event) -> None:  # noqa: N802
        super().focusInEvent(event)
        self.row.set_current(self)
        self.update()

    def focusOutEvent(self, event) -> None:  # noqa: N802
        super().focusOutEvent(event)
        self.update()

    # -- keys ---------------------------------------------------------------------------------
    LOCAL = (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Space, Qt.Key.Key_Return,
             Qt.Key.Key_Enter, Qt.Key.Key_Delete, Qt.Key.Key_Escape)

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.ShortcutOverride:
            # Del, Esc, Enter, Space belong to the row here, not to the page commands
            if event.key() in self.LOCAL and not event.modifiers():
                event.accept()
                return True
        return super().event(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        key = event.key()
        if not event.modifiers() and self.row.handle_key(self, key):
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Space and not event.modifiers():
            event.accept()  # Space already acted on press (the base class would click twice)
            return
        super().keyReleaseEvent(event)


# -- the row --------------------------------------------------------------------------------
class ChipRow(QWidget):
    """The label, the chips, "Kayıtlı filtrelere ekle…", a note ("Şablon yok") and the count."""

    changed = Signal()  # a chip was turned on or off
    delete_requested = Signal(str)
    rename_requested = Signal(str)
    save_requested = Signal()
    escape_requested = Signal()
    inert_pressed = Signal(str)

    NAME = "kayitliFiltreler"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(self.NAME)
        self.setAccessibleName(ROW_LABEL)
        self.chips: list[FilterChip] = []
        self._current = 0
        m = theme.manager()
        self.flow = FlowLayout(self, m.size("s2"), m.size("s2"))
        self.label = QLabel(ROW_LABEL)
        self.label.setProperty("textRole", "secondary")
        self.note = QLabel("")
        self.note.setProperty("textRole", "secondary")
        self.save = QPushButton(SAVE_TEXT)
        self.save.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.save.clicked.connect(self.save_requested)
        self.count = QLabel("")
        self.count.setAccessibleName(ROW_LABEL)
        for widget in (self.label,):
            self.flow.addWidget(widget)
        self.flow.add_trailing(self.count)
        self.flow.addWidget(self.note)
        self.flow.addWidget(self.save)
        self.note.hide()
        self.save.hide()
        theme.follow(self, self._restyle)

    def _restyle(self) -> None:
        m = theme.manager()
        self.flow.setContentsMargins(m.size("s6"), m.size("s2"), m.size("s4"), m.size("s2"))
        self.label.setFont(m.font("body-medium"))
        self.count.setFont(m.font("body"))
        self.note.setFont(m.font("body"))
        self.flow.invalidate()

    def chip_room(self) -> int:
        """The widest a chip may be: the row without its margins."""
        margins = self.flow.contentsMargins()
        return max(self.width(), 200) - margins.left() - margins.right()

    # -- content ------------------------------------------------------------------------------
    def set_chips(self, infos: list[ChipInfo], on: set[str]) -> None:
        """Rebuild the chips (kept in the order given); `on` names the ones turned on."""
        wanted = [(i, i.known and i.name in on) for i in infos]
        if wanted == [(c.info, c.isChecked()) for c in self.chips]:
            return  # nothing to redraw (the selection moved, the filters did not)
        focused = next((c.info.name for c in self.chips if c.hasFocus()), None)
        for chip in self.chips:
            self.flow.removeWidget(chip)
            chip.hide()
            chip.setParent(None)
            chip.deleteLater()
        self.chips = []
        for info in infos:
            chip = FilterChip(info, self)
            chip.setChecked(info.known and info.name in on)
            chip.toggled.connect(lambda _on, c=chip: self._toggled(c))
            chip.delete_requested.connect(self.delete_requested)
            chip.menu_requested.connect(self._menu)
            chip.show()
            self.flow.insert_widget(1 + len(self.chips), chip)  # after the label
            self.chips.append(chip)
        self._current = min(self._current, max(0, len(self.chips) - 1))
        self._roving()
        if focused is not None:
            target = next((c for c in self.chips if c.info.name == focused), None)
            if target is not None:
                target.setFocus(Qt.FocusReason.OtherFocusReason)
        self.flow.invalidate()
        self.updateGeometry()

    def on_names(self) -> list[str]:
        return [c.info.name for c in self.chips if c.isChecked()]

    def _toggled(self, chip: FilterChip) -> None:
        chip._describe()
        chip.update()
        self.changed.emit()

    def set_count_text(self, text: str) -> None:
        self.count.setText(text)
        self.count.setAccessibleDescription(text)
        self.flow.invalidate()

    def set_note(self, text: str) -> None:
        self.note.setText(text)
        self.note.setVisible(bool(text))
        self.flow.invalidate()

    def set_can_save(self, can: bool) -> None:
        self.save.setVisible(can)
        self.flow.invalidate()

    # -- keyboard -----------------------------------------------------------------------------
    def set_current(self, chip: FilterChip) -> None:
        if chip in self.chips:
            self._current = self.chips.index(chip)
            self._roving()

    def _roving(self) -> None:
        """Only the current chip is a Tab stop (arrows move inside the row, HIG-FOC-08)."""
        for number, chip in enumerate(self.chips):
            chip.setFocusPolicy(Qt.FocusPolicy.StrongFocus if number == self._current
                                else Qt.FocusPolicy.ClickFocus)

    def focus_row(self) -> bool:
        """Put focus on the current chip (or the save button when there are no chips)."""
        if self.chips:
            self.chips[min(self._current, len(self.chips) - 1)].setFocus(
                Qt.FocusReason.ShortcutFocusReason)
            return True
        if not self.save.isHidden():
            self.save.setFocus(Qt.FocusReason.ShortcutFocusReason)
            return True
        return False

    def handle_key(self, chip: FilterChip, key: int) -> bool:
        number = self.chips.index(chip) if chip in self.chips else -1
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            target = number + (1 if key == Qt.Key.Key_Right else -1)
            if 0 <= target < len(self.chips):
                self.chips[target].setFocus(Qt.FocusReason.TabFocusReason)
            return True
        if key in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            chip.click()
            return True
        if key == Qt.Key.Key_Delete:
            self.delete_requested.emit(chip.info.name)
            return True
        if key == Qt.Key.Key_Escape:
            self.escape_requested.emit()
            return True
        return False

    # -- context menu -------------------------------------------------------------------------
    def _menu(self, name: str, where: QPoint) -> None:
        menu = QMenu(self)
        menu.setAccessibleName(name)
        rename = QAction("Yeniden adlandır", menu)
        rename.triggered.connect(lambda: self.rename_requested.emit(name))
        delete = QAction("Sil", menu)
        delete.triggered.connect(lambda: self.delete_requested.emit(name))
        menu.addAction(rename)
        menu.addAction(delete)
        self.menu = menu
        menu.popup(where)


# -- the dialog -----------------------------------------------------------------------------
class SaveFilterDialog(QDialog):
    """"Kayıtlı filtrelere ekle…" (and "Yeniden adlandır"): one field, Enter saves."""

    def __init__(self, title: str, taken: set[str], text: str = "",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        from evrakci.ui.kontrol_dialogs import _buttons

        m = theme.manager()
        self._taken = taken
        self.setWindowTitle(title)
        self.setAccessibleName(title)
        col = QVBoxLayout(self)
        col.setContentsMargins(*(m.size("s6"),) * 4)
        col.setSpacing(m.size("s2"))
        label = QLabel("Filtrenin adı")
        self.field = QLineEdit(text)
        self.field.setAccessibleName("Filtrenin adı")
        label.setBuddy(self.field)
        self.error = QLabel("")
        self.error.setWordWrap(True)
        self.error.setProperty("textRole", "danger")
        self.error.setAccessibleName("")
        self.error.hide()
        for widget in (label, self.field, self.error):
            col.addWidget(widget)
        col.addSpacing(m.size("s4"))
        row, self.ok = _buttons(self, "Kaydet")
        col.addLayout(row)
        self.setMinimumWidth(m.size("s12") * 8)
        self.field.setFocus(Qt.FocusReason.OtherFocusReason)
        self.field.selectAll()

    def name(self) -> str:
        return validate_filter_name(self.field.text())

    def accept(self) -> None:
        try:
            name = self.name()
            if name in self._taken:
                raise TemplateError(f"Bu adla bir filtre zaten var: {name}")
        except TemplateError as error:
            self.error.setText(str(error))
            self.error.setAccessibleName(str(error))
            self.error.show()
            self.field.setFocus(Qt.FocusReason.OtherFocusReason)
            return
        super().accept()


# -- undo -----------------------------------------------------------------------------------
class TemplateStep(QUndoCommand):
    """One change of a template made from Kontrol, on the Şablonlar undo stack. `apply(data)`
    puts a template dict back (the open editor, or the file)."""

    def __init__(self, text: str, before: dict, after: dict,
                 apply: Callable[[dict], None]) -> None:
        super().__init__(text)
        self.before, self.after, self._apply, self._first = before, after, apply, True

    def redo(self) -> None:
        if self._first:
            self._first = False
            return
        self._apply(self.after)

    def undo(self) -> None:
        self._apply(self.before)


__all__ = ["NONE_ON", "NOT_KNOWN", "NOT_KNOWN_TIP", "NO_TEMPLATE", "ROW_LABEL", "SAVE_TEXT",
           "ChipInfo", "ChipRow", "FilterChip", "FlowLayout", "SaveFilterDialog", "TemplateStep",
           "count_text"]
