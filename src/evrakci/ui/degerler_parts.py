"""Pieces of the Değerler table card and status bar (final-a/degerler.html): A's view switch
(Fluent SelectorBar), the empty state, the card head that wraps at large text, and one
status-bar count."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QFontMetrics, QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.degerler_model import VIEW_NAMES
from evrakci.ui.widgets import StatusPart


# -- pieces of the table card ---------------------------------------------------------------
class SelectorItem(QAbstractButton):
    """One item of A's view switch (Fluent SelectorBar): label, quiet count, and a 16 × 3 accent
    pill under the selected one."""

    def __init__(self, view: str, parent=None) -> None:
        super().__init__(parent)
        self.view = view
        self.count = 0
        self.setText(VIEW_NAMES[view])
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.toggled.connect(lambda _on: self.update())

    def set_count(self, value: int) -> None:
        self.count = value
        self.setAccessibleName(f"{self.text()}: {value} değer")
        self.setToolTip(f"{self.text()}: {value} değer")
        self.updateGeometry()
        self.update()

    def _fonts(self):
        m = theme.manager()
        return (m.font("body-strong" if self.isChecked() else "body-medium"),
                m.font("caption-num"))

    def sizeHint(self) -> QSize:  # noqa: N802
        m = theme.manager()
        label, number = self._fonts()
        bold = m.font("body-strong")  # room for the semibold label, so nothing shifts
        width = (2 * m.size("s3") + max(self.fontMetrics().horizontalAdvance(self.text()),
                                        _advance(bold, self.text()))
                 + m.size("s2") + _advance(number, str(self.count)))
        return QSize(width, m.size("control-h"))

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.underMouse() and not self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(m.color("hover"))
            painter.drawRoundedRect(self.rect().adjusted(0, 8, 0, -8), 4, 4)
        label, number = self._fonts()
        x = m.size("s3")
        painter.setFont(label)
        painter.setPen(m.color("text" if self.isChecked() else "text-2"))
        text_rect = self.rect().adjusted(x, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         self.text())
        x += _advance(label, self.text()) + m.size("s2")
        painter.setFont(number)
        painter.setPen(m.color("text-2"))
        painter.drawText(self.rect().adjusted(x, 0, 0, 0),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         str(self.count))
        if self.isChecked():
            centre = m.size("s3") + _advance(label, self.text()) / 2
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(m.color("accent"))
            painter.drawRoundedRect(int(centre - 8), self.height() - 8 - 3, 16, 3, 2, 2)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)


def _advance(font, text: str) -> int:
    return QFontMetrics(font).horizontalAdvance(text)


class ViewSelector(QWidget):
    """Kontrol gerekenler / İncelenmemiş / Tümü (and Örnek while the sample is open).
    Left/Right move between the items (one Tab stop)."""

    changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Görünüm")
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(2)
        self.items: dict[str, SelectorItem] = {}
        for view in VIEW_NAMES:
            item = SelectorItem(view)
            item.clicked.connect(lambda _c=False, v=view: self.changed.emit(v))
            item.installEventFilter(self)
            row.addWidget(item)
            self.items[view] = item
        self.items["ornek"].hide()

    def set_view(self, view: str) -> None:
        self.items["ornek"].setVisible(view == "ornek")
        self.items[view].setChecked(True)
        for name, item in self.items.items():
            item.setFocusPolicy(Qt.FocusPolicy.TabFocus if name == view
                                else Qt.FocusPolicy.ClickFocus)
            item.updateGeometry()

    def view(self) -> str:
        return next(v for v, item in self.items.items() if item.isChecked())

    def set_counts(self, counts: dict[str, int]) -> None:
        for view, value in counts.items():
            self.items[view].set_count(value)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() == QEvent.Type.KeyPress and isinstance(event, QKeyEvent) and \
                event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            shown = [v for v, i in self.items.items() if i.isVisible()]
            here = shown.index(obj.view) if obj.view in shown else 0
            step = 1 if event.key() == Qt.Key.Key_Right else -1
            target = shown[(here + step) % len(shown)]
            self.items[target].setFocus(Qt.FocusReason.TabFocusReason)
            self.changed.emit(target)
            return True
        return False


class EmptyState(QWidget):
    """A's empty state: a 48 px mark, one heading, one sentence, a primary and a secondary
    action, and a quiet note."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s6"), 0, m.size("s6"), m.size("s8"))
        col.setSpacing(0)
        col.addStretch(1)
        self.mark = QLabel()
        self.mark.setFixedSize(48, 48)
        self.mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mark.setProperty("kind", "card")
        col.addWidget(self.mark, 0, Qt.AlignmentFlag.AlignHCenter)
        col.addSpacing(m.size("s4"))
        self.title = QLabel()
        self.title.setProperty("textRole", "panel")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text = QLabel()
        self.text.setProperty("textRole", "secondary")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text.setWordWrap(True)
        col.addWidget(self.title)
        col.addSpacing(m.size("s1"))
        col.addWidget(self.text)
        col.addSpacing(m.size("s6"))
        buttons = QHBoxLayout()
        buttons.setSpacing(m.size("s2"))
        buttons.addStretch(1)
        self.primary = QPushButton()
        self.primary.setProperty("variant", "primary")
        self.secondary = QPushButton()
        for button in (self.primary, self.secondary):
            button.setProperty("sizeVariant", "lg")
            buttons.addWidget(button)
        buttons.addStretch(1)
        col.addLayout(buttons)
        col.addSpacing(m.size("s3"))
        self.note = QLabel()
        self.note.setProperty("textRole", "caption")
        self.note.setProperty("kind", "inspector-key")
        self.note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self.note)
        col.addStretch(1)
        self._actions: dict[QPushButton, Callable[[], None] | None] = {}
        self._icons: dict[QPushButton, str] = {}
        self._mark = "scan-text"
        for button in (self.primary, self.secondary):
            button.clicked.connect(lambda _c=False, b=button: self._run(b))
        theme.follow(self, self._restyle, "degerler-empty")

    def _run(self, button: QPushButton) -> None:
        action = self._actions.get(button)
        if action is not None:
            action()

    def _restyle(self) -> None:
        m = theme.manager()
        self.mark.setPixmap(make_icon(self._mark, size=24).pixmap(24, 24))
        for button, icon in self._icons.items():
            role = "text-on-accent" if button is self.primary else "icon"
            button.setIcon(make_icon(icon, role, m.size("icon-sm")) if icon else make_icon(
                "check", role, 1))
            button.setMinimumHeight(m.size("lg-h"))

    def show_state(self, mark: str, title: str, text: str,
                   primary: tuple[str, str, Callable[[], None]] | None = None,
                   secondary: tuple[str, str, Callable[[], None]] | None = None,
                   note: str = "") -> None:
        self._mark = mark
        self.title.setText(title)
        self.text.setText(text)
        self.note.setText(note)
        self.note.setVisible(bool(note))
        self.setAccessibleName(title)
        for button, spec in ((self.primary, primary), (self.secondary, secondary)):
            button.setVisible(spec is not None)
            if spec is not None:
                label, icon, action = spec
                button.setText(f" {label}")  # Qt's icon gap + a space = A's s2
                button.setAccessibleName(label)
                self._actions[button] = action
                self._icons[button] = icon
        self._restyle()


class HeaderBar(QWidget):
    """The card head: the view switch, then search and the template picker on the right.
    When they do not fit (large text) the picker, then the search too, move to a second
    line, as A's 150 % renders do (main: picker below; Örnek: search below)."""

    def __init__(self, selector: ViewSelector, search: QLineEdit, combo: QComboBox,
                 parent=None) -> None:
        super().__init__(parent)
        self.selector, self.search, self.combo = selector, search, combo
        self.col = QVBoxLayout(self)
        self.top = QHBoxLayout()
        self.bottom = QHBoxLayout()
        self.col.addLayout(self.top)
        self.col.addLayout(self.bottom)
        self.lines = -1  # 0: one line; 1: picker below; 2: search and picker below
        theme.follow(self, self._restyle, "degerler-headbar")

    def _restyle(self) -> None:
        m = theme.manager()
        for row in (self.col, self.top, self.bottom):
            row.setSpacing(m.size("s2"))
        self.search.setFixedWidth(280 if m.text_scale() >= 130 else 196)
        self.lines = -1
        self._place()

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(self.selector.sizeHint().width() + 2 * theme.manager().size("s3"),
                     super().minimumSizeHint().height())

    def _layout_for(self, width: int) -> int:
        m = theme.manager()
        pad = m.size("s2") + m.size("s3") + m.size("s6")  # margins + the gap before search
        selector = self.selector.sizeHint().width()
        search = self.search.width() + m.size("s2")
        combo = self._combo_width() + m.size("s2") if not self.combo.isHidden() else 0
        if width <= 0 or selector + search + combo + pad <= width:
            return 0
        if selector + search + pad <= width:
            return 1 if combo else 0
        return 2

    def _combo_width(self) -> int:
        """The picker's width with a little slack: Windows draws some fonts a pixel wider than
        QComboBox's own size hint allows, which would clip the template name."""
        return self.combo.sizeHint().width() + theme.manager().size("s1")

    def _place(self) -> None:
        m = theme.manager()
        self.combo.setMinimumWidth(self._combo_width())
        lines = self._layout_for(self.width())
        if lines != self.lines:
            self.lines = lines
            for row in (self.top, self.bottom):
                while row.count():
                    row.takeAt(0)
            self.top.addWidget(self.selector)
            self.top.addStretch(1)
            if lines < 2:
                self.top.addWidget(self.search)
            else:
                self.bottom.addWidget(self.search)
            if lines == 0:
                self.top.addWidget(self.combo)
            else:
                self.bottom.addWidget(self.combo)
                self.bottom.addStretch(1)
        one = 52 if m.text_scale() < 130 else 64
        wrapped = lines > 0
        self.setFixedHeight(one if not wrapped
                            else 2 * m.size("control-h") + 3 * m.size("s2") + 8)
        self.col.setContentsMargins(m.size("s2"), m.size("s2") if wrapped else 0, m.size("s3"),
                                    m.size("s2") if wrapped else 0)

    def refit(self) -> None:
        """Visibility of the picker changed (Örnek hides it)."""
        self.lines = -1
        self._place()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._place()


StatusItem = StatusPart  # one shared status-bar item (widgets.StatusPart)


