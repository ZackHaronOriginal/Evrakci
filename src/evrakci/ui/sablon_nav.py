"""The left column of Şablonlar (final-a .navside): templates and variables as Settings-style
rows in cards, then the file-name pattern and a footnote.

Rows are painted by one delegate (no widget per row): the selected row is `selected` with a 3 px
`accent` bar (an `accent` fill in high contrast), a variable row has A's number badge, the
required star and "2 bölüm" at the right, a section row its grip and "Sayfa 1". The cards are as
tall as their rows; the column scrolls when text is large.
"""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.templates.model import Template
from evrakci.ui import icons, theme
from evrakci.ui.card_scroll import CardScroll
from evrakci.ui.chrome import make_icon
from evrakci.ui.sablon_parts import small_button_style
from evrakci.ui.style import paint_ring

ROLE_KIND = Qt.ItemDataRole.UserRole + 1  # "template" | "variable" | "section"
ROLE_NUMBER = Qt.ItemDataRole.UserRole + 2
ROLE_REQUIRED = Qt.ItemDataRole.UserRole + 3
ROLE_VALUE = Qt.ItemDataRole.UserRole + 4  # the quiet text at the right
USER = Qt.ItemDataRole.UserRole  # template id, variable name, section index
BADGE = 20


class NavDelegate(QStyledItemDelegate):
    """A .act .r: 40 px rows, `r-control` corners, the label left and a caption value right."""

    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        return QSize(0, theme.manager().size("row-h"))

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        m = theme.manager()
        hc = m.theme() == "hc"
        rect = QRectF(opt.rect)
        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        hover = bool(opt.state & QStyle.StateFlag.State_MouseOver)
        radius = m.size("r-control")
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        on_accent = selected and hc
        if selected:
            painter.fillPath(path, m.color("accent" if hc else "selected"))
            if not hc:
                painter.save()
                painter.setClipPath(path)
                painter.fillRect(QRectF(rect.left(), rect.top(), 3, rect.height()),
                                 m.color("accent"))
                painter.restore()
        elif hover:
            if hc:
                painter.setPen(m.color("accent"))
                painter.drawPath(path)
            else:
                painter.fillPath(path, m.color("hover"))
        ink = m.color("text-on-accent" if on_accent else "text")
        quiet = m.color("text-on-accent" if on_accent else "text-2")
        kind = index.data(ROLE_KIND)
        pad = m.size("s3")
        left, right, mid = rect.left() + pad, rect.right() - pad, rect.center().y()
        value = index.data(ROLE_VALUE) or ""
        small = m.font("caption")
        if value:
            painter.setFont(small)
            width = painter.fontMetrics().horizontalAdvance(value)
            painter.setPen(quiet)
            painter.drawText(QRectF(right - width, rect.top(), width, rect.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, value)
            right -= width + m.size("s2")
        if kind == "section":
            left += m.size("s6") - pad
            icons.paint(painter, "grip-vertical", QRectF(left, mid - 8, 16, 16),
                        "text-on-accent" if on_accent else "icon")
            left += 16 + pad
        elif kind == "variable":
            left = self._badge(painter, m, index, QRectF(left, mid - BADGE / 2, BADGE, BADGE),
                               on_accent) + pad
        painter.setFont(m.font("body"))
        label = index.data(Qt.ItemDataRole.DisplayRole) or ""
        star = " *" if index.data(ROLE_REQUIRED) else ""
        metrics = painter.fontMetrics()
        room = max(0, right - left)
        shown = metrics.elidedText(label, Qt.TextElideMode.ElideRight,
                                   int(room - metrics.horizontalAdvance(star)))
        painter.setPen(ink)
        text_rect = QRectF(left, rect.top(), room, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         shown)
        if star:
            painter.setPen(quiet)
            painter.drawText(QRectF(left + metrics.horizontalAdvance(shown), rect.top(), 40,
                                    rect.height()), Qt.AlignmentFlag.AlignVCenter
                             | Qt.AlignmentFlag.AlignLeft, star)
        painter.restore()
        if opt.state & QStyle.StateFlag.State_HasFocus:
            paint_ring(painter, rect.adjusted(-1, -1, 1, 1), radius)

    def _badge(self, painter: QPainter, m, index, rect: QRectF, on_accent: bool) -> float:
        """A's .num-badge (accent, 20 px high, `r-control`); returns its right edge."""
        text = str(index.data(ROLE_NUMBER))
        painter.setFont(m.font("caption-strong"))
        width = max(BADGE, painter.fontMetrics().horizontalAdvance(text) + 10)
        rect = QRectF(rect.left(), rect.top(), width, BADGE)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(m.color("text-on-accent" if on_accent else "accent"))
        painter.drawRoundedRect(rect, m.size("r-control"), m.size("r-control"))
        painter.setPen(m.color("accent" if on_accent else "text-on-accent"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        return rect.right()


def _row(item: QListWidgetItem | QTreeWidgetItem, kind: str, label: str, value: str = "",
         spoken: str = "") -> None:
    column = (0,) if isinstance(item, QTreeWidgetItem) else ()
    item.setText(*column, label)
    for role, data in ((ROLE_KIND, kind), (ROLE_VALUE, value),
                       (Qt.ItemDataRole.AccessibleTextRole, spoken or label),
                       (Qt.ItemDataRole.ToolTipRole, spoken or label)):
        item.setData(*column, role, data)


class TemplateList(QListWidget):
    """The templates: name left, "8 değişken" (or "kaydedilmedi") right."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setItemDelegate(NavDelegate(self))
        self.setMouseTracking(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAccessibleName("Şablonlar")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def add_template(self, template_id: str, name: str, count: int, pending: bool = False) -> None:
        item = QListWidgetItem()
        value = "kaydedilmedi" if pending else f"{count} değişken"
        _row(item, "template", name, value, f"Şablon {name}, {value}")
        item.setData(USER, template_id)
        self.addItem(item)

    def fit_height(self) -> None:
        self.setFixedHeight(max(1, self.count()) * theme.manager().size("row-h"))

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(0, max(1, self.count()) * theme.manager().size("row-h"))


class VariableTree(QTreeWidget):
    """The variables with their sections (variants), always open; sections and variables
    can be dragged to reorder (the keyboard path is Alt+Up / Alt+Down)."""

    section_moved = Signal(str, int, int)  # variable, from, to
    variable_moved = Signal(int, int)  # from, to

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHeaderHidden(True)
        self.setIndentation(0)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setExpandsOnDoubleClick(False)
        self.setUniformRowHeights(True)
        self.setMouseTracking(True)
        self.setItemDelegate(NavDelegate(self))
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setAccessibleName("Değişkenler ve bölümler")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def fill(self, template: Template | None) -> None:
        self.clear()
        if template is None:
            return
        for number, variable in enumerate(template.variables, start=1):
            count = len(variable.sections)
            # A: a variable with one box is one row; its sections are listed from two on
            value = f"{count} bölüm" if count > 1 else ("kutu yok" if not count else "")
            required = " zorunlu" if variable.required else ""
            top = QTreeWidgetItem()
            _row(top, "variable", variable.name, value,
                 f"Değişken {number}: {variable.name},{required} {value or '1 kutu'}".replace(
                     ",  ", ", "))
            top.setData(0, USER, variable.name)
            top.setData(0, ROLE_NUMBER, number)
            top.setData(0, ROLE_REQUIRED, variable.required)
            self.addTopLevelItem(top)
            if count > 1:
                for index, section in enumerate(variable.sections):
                    page = "son sayfa" if section.page == -1 else f"Sayfa {section.page}"
                    kid = QTreeWidgetItem()
                    _row(kid, "section", f"Bölüm {index + 1}", page,
                         f"{variable.name}, bölüm {index + 1}, {page.lower()}")
                    kid.setData(0, USER, index)
                    top.addChild(kid)
            top.setExpanded(True)
        self.fit_height()

    def row_count(self) -> int:
        total = 0
        for i in range(self.topLevelItemCount()):
            total += 1 + self.topLevelItem(i).childCount()
        return total

    def fit_height(self) -> None:
        self.setFixedHeight(max(1, self.row_count()) * theme.manager().size("row-h"))

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(0, max(1, self.row_count()) * theme.manager().size("row-h"))

    def dropEvent(self, event) -> None:  # noqa: N802
        """Never let Qt move the rows: work out what the drop means and ask the screen."""
        source = self.currentItem()
        target = self.itemAt(event.position().toPoint())
        position = self.dropIndicatorPosition()
        event.setDropAction(Qt.DropAction.IgnoreAction)
        event.ignore()
        if source is None or target is None:
            return
        below = position == QAbstractItemView.DropIndicatorPosition.BelowItem
        if source.parent() is not None:  # a section: only within its variable
            parent = source.parent()
            if target is parent:
                new = 0
            elif target.parent() is parent:
                new = parent.indexOfChild(target) + (1 if below else 0)
            else:
                return
            old = parent.indexOfChild(source)
            new -= 1 if old < new else 0
            if new != old:
                self.section_moved.emit(parent.data(0, USER), old, new)
            return
        owner = target.parent() or target
        new = self.indexOfTopLevelItem(owner) + (1 if below or target.parent() else 0)
        old = self.indexOfTopLevelItem(source)
        new -= 1 if old < new else 0
        if new != old:
            self.variable_moved.emit(old, new)

    def item_for(self, name: str, index: int | None = None) -> QTreeWidgetItem | None:
        """The row of a variable, or of one of its sections; a variable with a single box has
        no section rows, its own row stands for the box."""
        for i in range(self.topLevelItemCount()):
            top = self.topLevelItem(i)
            if top.data(0, USER) != name:
                continue
            if index is None:
                return top
            if top.childCount() == 0:
                return top if index == 0 else None
            return top.child(index) if 0 <= index < top.childCount() else None
        return None


class MessageLabel(QLabel):
    """An inline note under the work (A: next to the object): a danger icon and the text; hidden
    when empty. Its words carry the meaning, the icon repeats it."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWordWrap(True)
        self.setProperty("textRole", "caption")
        self.setAccessibleName("Şablon iletisi")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.hide()
        theme.follow(self, self._restyle, "sablon-message")

    def _restyle(self) -> None:
        m = theme.manager()
        self.setStyleSheet(f"color: {m.hex('danger')}; font-weight: 600; "
                           f"padding-left: {16 + m.size('s2')}px;")
        self.update()

    def setText(self, text: str) -> None:  # noqa: N802
        super().setText(text)
        self.setVisible(bool(text))

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        icons.paint(painter, "circle-x", QRectF(0, 1, 16, 16), "danger", 2.0)


class NavPane(QScrollArea):
    """The column: "Şablonlar" + card, "Değişkenler" + card, a message, a footnote."""

    add_template = Signal()
    add_variable = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("sablonNav")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAccessibleName("Şablonlar ve değişkenler")
        m = theme.manager()
        body = QWidget()
        body.setObjectName("navBody")
        col = QVBoxLayout(body)
        col.setContentsMargins(m.size("s3"), m.size("s3"), m.size("s3"), m.size("s3"))
        col.setSpacing(m.size("s3"))
        self.templates = TemplateList()
        self.variables = VariableTree()
        self.template_card = self._card(self.templates)
        self.variable_card = self._card(self.variables)
        self.add_template_button = self._plus("Şablon ekle")
        self.add_variable_button = self._plus("Değişken ekle")
        self._variable_tip = "Değişken ekle (Ctrl+Shift+N)"
        self.add_variable_button.setToolTip(self._variable_tip)
        col.addLayout(self._group("Şablonlar", self.add_template_button, self.template_card))
        col.addLayout(self._group("Değişkenler", self.add_variable_button, self.variable_card))
        self.message = MessageLabel()
        col.addWidget(self.message)
        col.addStretch(1)
        self.foot = QLabel()
        self.foot.setWordWrap(True)
        self.foot.setProperty("textRole", "caption")
        self.foot.setProperty("kind", "inspector-key")
        self.foot.setContentsMargins(m.size("s1"), 0, m.size("s1"), 0)
        col.addWidget(self.foot)
        self.setWidget(body)
        self.card_scroll = CardScroll(self)
        self.add_template_button.clicked.connect(self.add_template)
        self.add_variable_button.clicked.connect(self.add_variable)
        theme.follow(self, self._restyle, "sablon-nav")

    def _card(self, view: QWidget) -> QFrame:
        card = QFrame()
        card.setProperty("kind", "card")
        col = QVBoxLayout(card)
        col.setContentsMargins(*(theme.manager().size("s1"),) * 4)
        col.addWidget(view)
        return card

    def _plus(self, name: str) -> QToolButton:
        button = QToolButton()
        button.setProperty("kind", "icon")
        button.setProperty("sizeVariant", "sm")
        button.setAutoRaise(True)
        button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        button.setToolTip(name)
        button.setAccessibleName(name)
        return button

    def _group(self, title: str, plus: QToolButton, card: QFrame) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(theme.manager().size("s2"))
        head = QHBoxLayout()
        label = QLabel(title)
        label.setProperty("kind", "group-label")
        head.addWidget(label)
        head.addStretch(1)
        head.addWidget(plus)
        col.addLayout(head)
        col.addWidget(card)
        return col

    def _restyle(self) -> None:
        m = theme.manager()
        side = m.title_band().control_height  # A .iconbtn.sm: 32 px (40 at 150 %)
        for button in (self.add_template_button, self.add_variable_button):
            button.setIcon(make_icon("plus", "icon", m.size("icon-sm")))
            button.setStyleSheet(small_button_style(side))
        self.templates.fit_height()
        self.variables.fit_height()
        self.templates.doItemsLayout()  # the row height follows the density
        self.variables.doItemsLayout()

    def set_empty(self, empty: bool) -> None:
        """No template at all (A `empty`): the labels and plus buttons stay, the cards go."""
        self.template_card.setVisible(not empty)
        self.variable_card.setVisible(not empty)
        self.add_variable_button.setEnabled(not empty)
        self.add_variable_button.setToolTip("Önce bir şablon oluşturun" if empty
                                            else self._variable_tip)
        self.foot.setText(
            "Şablonlar bu bilgisayarda saklanır ve her işte kullanılabilir. Bir şablon seçince "
            "değişkenleri burada sıralanır." if empty else
            "* zorunlu. Bölümler yukarıdan aşağı denenir; ilk emin okuma kazanır.")
