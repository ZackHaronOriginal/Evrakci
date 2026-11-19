"""The command palette (Ctrl+K, or a click on the title-band search): spec state kontrol-palette.

A frameless popup under the title band: a search field, the commands of "app" plus the current
tab (Turkish case folding), keys right-aligned, disabled commands greyed with their reason.
Enter runs the QAction, Esc closes. The most recent commands come first.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QModelIndex, QPoint, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, icons, theme

ID_ROLE = Qt.ItemDataRole.UserRole
KEYS_ROLE = Qt.ItemDataRole.UserRole + 1
HEADER_ROLE = Qt.ItemDataRole.UserRole + 2
REASON_ROLE = Qt.ItemDataRole.UserRole + 3
MARGIN = 24  # room around the card for its shadow
RECENT_MAX = 5
_recent: list[str] = []  # newest first, shared by every palette of the process


def remember(action_id: str) -> None:
    """Put a command at the front of the recent list."""
    if action_id in _recent:
        _recent.remove(action_id)
    _recent.insert(0, action_id)
    del _recent[RECENT_MAX:]


def recent_ids() -> list[str]:
    return list(_recent)


class _Delegate(QStyledItemDelegate):
    """Group headers and command rows drawn with the theme's tokens."""

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        m = theme.manager()
        height = m.size("fs-caption") + m.size("s3") + m.size("s1") if index.data(HEADER_ROLE) \
            else m.menu_item_height()
        return QSize(option.rect.width(), height)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        m = theme.manager()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect)
        pad = m.size("s3")
        if index.data(HEADER_ROLE):
            painter.setFont(m.font("caption-medium"))
            painter.setPen(m.color("text-2"))
            painter.drawText(rect.adjusted(pad, m.size("s3") - m.size("s1"), -pad, 0),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             index.data(Qt.ItemDataRole.DisplayRole))
            painter.restore()
            return
        enabled = bool(index.flags() & Qt.ItemFlag.ItemIsEnabled)
        current = bool(option.state & QStyle.StateFlag.State_Selected)
        row = rect.adjusted(0, 0, 0, 0)
        if current and enabled:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(m.color("selected"))
            painter.drawRoundedRect(row, m.size("r-control"), m.size("r-control"))
        ink = m.color("text") if enabled else m.color("text-disabled")
        glyph = "text" if enabled else "icon-disabled"
        icon_size = m.size("icon-sm")
        icon_rect = QRectF(rect.left() + pad, rect.center().y() - icon_size / 2,
                           icon_size, icon_size)
        name = index.data(Qt.ItemDataRole.DecorationRole)
        if name:
            icons.paint(painter, name, icon_rect, m.hex(glyph))
        left = icon_rect.right() + m.size("s3")
        right = rect.right() - pad
        keys = index.data(KEYS_ROLE) or []
        if keys:
            right = self._paint_keys(painter, QRectF(rect), right, keys[0], enabled)
        painter.setFont(m.font("body"))
        painter.setPen(ink)
        text = index.data(Qt.ItemDataRole.DisplayRole)
        reason = index.data(REASON_ROLE)
        text_rect = QRectF(left, rect.top(), max(0.0, right - left - m.size("s2")), rect.height())
        fm = painter.fontMetrics()
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                         fm.elidedText(text, Qt.TextElideMode.ElideRight, int(text_rect.width())))
        if reason:
            painter.setFont(m.font("caption"))
            painter.setPen(m.color("text-disabled"))
            x = left + fm.horizontalAdvance(text) + m.size("s2")
            painter.drawText(QRectF(x, rect.top(), max(0.0, right - x), rect.height()),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, reason)
        painter.restore()

    def _paint_keys(self, painter: QPainter, rect: QRectF, right: float, keys: str,
                    enabled: bool) -> float:
        """A key rider at the right edge; returns the x where it starts."""
        m = theme.manager()
        painter.setFont(m.font("caption-medium"))
        width = painter.fontMetrics().horizontalAdvance(keys) + 2 * m.size("s2")
        chip = QRectF(right - width, rect.center().y() - m.size("rider-h") / 2,
                      width, m.size("rider-h"))
        painter.setPen(m.color("stroke-soft"))
        painter.setBrush(m.color("well"))
        painter.drawRoundedRect(chip, m.size("r-control") - 1, m.size("r-control") - 1)
        painter.setPen(m.color("text-2") if enabled else m.color("text-disabled"))
        painter.drawText(chip, Qt.AlignmentFlag.AlignCenter, keys)
        return chip.left()


class CommandPalette(QDialog):
    """Ctrl+K: type to find a command, Enter to run it."""

    def __init__(self, registry: actions.Registry, parent: QWidget | None = None) -> None:
        flags = Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        super().__init__(parent, flags)
        self._registry = registry
        self._entries: list[actions.PaletteEntry] = []
        self.setObjectName("commandPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAccessibleName("Komut ara")
        self.setAccessibleDescription("Bir komut yazın, Enter ile çalıştırın, Esc ile kapatın")
        m = theme.manager()
        pad = m.size("s2")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(MARGIN + pad, MARGIN + pad, MARGIN + pad, MARGIN + pad)
        outer.setSpacing(m.size("s1"))

        self.field = QLineEdit()
        self.field.setProperty("kind", "search")
        self.field.setPlaceholderText("Komut veya belge ara")
        self.field.setClearButtonEnabled(False)
        self.field.setAccessibleName("Komut ara")
        self.field.setFixedHeight(m.size("control-h") + m.size("s2"))
        self.field.installEventFilter(self)
        self.field.textChanged.connect(self._refill)
        outer.addWidget(self.field)

        self.list = QListWidget()
        self.list.setObjectName("paletteList")
        self.list.setAccessibleName("Komutlar")
        self.list.setItemDelegate(_Delegate(self.list))
        self.list.setFrameShape(QListWidget.Shape.NoFrame)
        self.list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list.setMouseTracking(True)
        self.list.itemClicked.connect(lambda _item: self._run_current())
        self.list.itemEntered.connect(self._hover)
        outer.addWidget(self.list, 1)

        self.empty = QLabel("Eşleşen komut yok")
        self.empty.setProperty("textRole", "secondary")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setAccessibleName("Sonuç yok")
        self.empty.hide()
        outer.addWidget(self.empty)

        self.hints = QLabel()
        self.hints.setProperty("textRole", "caption")
        self.hints.setTextFormat(Qt.TextFormat.RichText)
        self.hints.setContentsMargins(m.size("s3"), m.size("s2"), m.size("s3"), m.size("s1"))
        self.hints.setAccessibleName("Klavye ipuçları: ok tuşları, Enter, Esc")
        outer.addWidget(self.hints)
        self._paint_hints()

    # Public
    def open_for(self, tab: str) -> None:
        """Show the palette for `tab`, centred under the title band of the parent window."""
        self._tab = tab
        self.field.clear()
        self._refill()
        self._place()
        self.show()
        self.raise_()
        self.activateWindow()
        self.field.setFocus()

    def entries(self) -> list[actions.PaletteEntry]:
        """The entries now shown, in order (for tests and the window)."""
        return [e for e in self._entries]

    # Content
    def _tab_name(self) -> str:
        return getattr(self, "_tab", self._registry.context)

    def _reason(self, entry: actions.PaletteEntry) -> str:
        lookup = getattr(self._registry, "disabled_reason", None)
        return str(lookup(entry.id) or "") if callable(lookup) and not entry.enabled else ""

    def _ordered(self, query: str) -> tuple[list[actions.PaletteEntry], list[actions.PaletteEntry]]:
        """(recent, others) for the query; recent commands first, as `remember` ordered them."""
        found = actions.palette_search(self._registry.palette_entries(self._tab_name()), query)
        rank = {action_id: i for i, action_id in enumerate(_recent)}
        recent = sorted((e for e in found if e.id in rank), key=lambda e: rank[e.id])
        others = [e for e in found if e.id not in rank]
        return recent, others

    def _refill(self) -> None:
        query = self.field.text().strip()
        recent, others = self._ordered(query)
        self._entries = [*recent, *others]
        self.list.clear()
        groups = ((("Son kullanılan", recent), ("Komutlar", others)) if not query
                  else (("Komutlar", recent + others),))
        for title, entries in groups:
            if entries:
                self._add_header(title)
            for entry in entries:
                self._add_entry(entry)
        self.empty.setVisible(not self._entries)
        self.list.setVisible(bool(self._entries))
        self._select_first()
        self._resize()

    def _add_header(self, title: str) -> None:
        item = QListWidgetItem(title)
        item.setData(HEADER_ROLE, True)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.list.addItem(item)

    def _add_entry(self, entry: actions.PaletteEntry) -> None:
        item = QListWidgetItem(entry.text)
        item.setData(ID_ROLE, entry.id)
        item.setData(KEYS_ROLE, entry.keys)
        item.setData(Qt.ItemDataRole.DecorationRole, self._registry.spec(entry.id).icon or "")
        reason = self._reason(entry)
        item.setData(REASON_ROLE, reason)
        keys = f", kısayol {entry.keys[0]}" if entry.keys else ""
        state = "" if entry.enabled else (f", kullanılamıyor: {reason}" if reason
                                          else ", kullanılamıyor")
        item.setData(Qt.ItemDataRole.AccessibleTextRole, f"{entry.text}{keys}{state}")
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        # A disabled command stays selectable (so its reason can be read) but never runs.
        item.setFlags(flags if entry.enabled else Qt.ItemFlag.ItemIsSelectable)
        self.list.addItem(item)

    def _select_first(self) -> None:
        for row in range(self.list.count()):
            if self.list.item(row).data(ID_ROLE):
                self.list.setCurrentRow(row)
                return

    def _paint_hints(self) -> None:
        m = theme.manager()
        ink, soft = m.hex("text"), m.hex("text-2")
        gap = "&nbsp;" * 8
        parts = [("↑ ↓", "seç"), ("Enter", "çalıştır"), ("Esc", "kapat")]
        self.hints.setText(gap.join(
            f'<b style="color:{ink}">{k}</b> <span style="color:{soft}">{v}</span>'
            for k, v in parts))

    # Navigation
    def _move(self, step: int) -> None:
        rows = [r for r in range(self.list.count()) if self.list.item(r).data(ID_ROLE)]
        if not rows:
            return
        current = self.list.currentRow()
        if current in rows:
            target = rows[(rows.index(current) + step) % len(rows)]
        else:
            target = rows[0 if step > 0 else -1]
        self.list.setCurrentRow(target)

    def _hover(self, item: QListWidgetItem) -> None:
        if item.data(ID_ROLE):
            self.list.setCurrentItem(item)

    def _run_current(self) -> None:
        item = self.list.currentItem()
        if item is None or not item.data(ID_ROLE):
            return
        action_id = item.data(ID_ROLE)
        action = self._registry.action(action_id)
        if not self._registry.is_enabled(action_id):
            return  # greyed out: nothing runs, the palette stays open
        remember(action_id)
        self.close()
        action.trigger()

    def eventFilter(self, obj, event: QEvent) -> bool:  # noqa: N802
        if obj is self.field and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                self._move(1)
            elif key == Qt.Key.Key_Up:
                self._move(-1)
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._run_current()
            elif key == Qt.Key.Key_Escape:
                self.close()
            else:
                return False
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)

    # Geometry and painting
    def _width(self) -> int:
        return (760 if theme.manager().text_scale() >= 150 else 560) + 2 * MARGIN

    def _resize(self) -> None:
        m = theme.manager()
        rows = sum(self._row_height(r) for r in range(self.list.count()))
        rows = min(rows, 9 * m.menu_item_height() + 2 * m.size("s6"))
        field = self.field.height()
        body = rows if self._entries else m.menu_item_height() * 2
        hints = self.hints.sizeHint().height()
        pad = 2 * (MARGIN + m.size("s2")) + 2 * m.size("s1")
        self.setFixedSize(self._width(), pad + field + body + hints)

    def _row_height(self, row: int) -> int:
        m = theme.manager()
        if self.list.item(row).data(HEADER_ROLE):
            return m.size("fs-caption") + m.size("s3") + m.size("s1")
        return m.menu_item_height()

    def _place(self) -> None:
        window = self.parentWidget().window() if self.parentWidget() else None
        if window is None:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.center().x() - self.width() // 2, screen.top() + 80)
            return
        band = theme.manager().title_band().height
        top = window.mapToGlobal(QPoint(0, 0))
        x = top.x() + (window.width() - self.width()) // 2
        self.move(x, top.y() + band - MARGIN + theme.manager().size("s1"))

    def paintEvent(self, _event: QEvent) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        card = QRectF(self.rect()).adjusted(MARGIN, MARGIN, -MARGIN, -MARGIN)
        radius = float(m.size("r-layer"))
        for layer in m.shadow("shadow-float"):
            if layer.inset:
                continue
            self._shadow(painter, card, radius, layer)
        path = QPainterPath()
        path.addRoundedRect(card, radius, radius)
        painter.fillPath(path, m.color("popover"))
        painter.setPen(QPen(m.color("stroke"), 1))
        painter.drawRoundedRect(card.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

    @staticmethod
    def _shadow(painter: QPainter, card: QRectF, radius: float, layer: theme.Shadow) -> None:
        """A cheap soft shadow: stacked translucent rounded rects, no blur filter."""
        steps = max(1, min(layer.blur // 2, 12))
        base = layer.color
        for i in range(steps, 0, -1):
            grow = layer.spread + i * layer.blur / (2 * steps)
            colour = QColor(base)
            colour.setAlphaF(base.alphaF() / steps * 0.6)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(colour)
            painter.drawRoundedRect(card.translated(layer.x, layer.y).adjusted(
                -grow, -grow, grow, grow), radius + grow, radius + grow)
