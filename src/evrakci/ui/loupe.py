"""Loupe: a large page preview over the window (spec state kontrol-loupe).

Sığdır / Genişlik / %100 modes, arrows and Page keys turn pages, Esc or Space closes
and gives focus back to whoever opened it. A thumbnail strip stays at the bottom; it paints
and renders only the visible thumbnails, so a 1,000 page job stays smooth.
``render(index, size)`` returns a pixmap that fits inside ``size``.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable

import shiboken6
from PySide6.QtCore import QEvent, QObject, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPainter, QPaintEvent, QPixmap
from PySide6.QtWidgets import (
    QAbstractScrollArea,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, motion, style, theme
from evrakci.ui.prefs import Prefs
from evrakci.ui.zoomview import ZoomController, ZoomSlider

PAGE_100 = QSize(1240, 1754)  # what %100 means: an A4 page at 150 dpi
CACHE_PAGES = 400
KEY = "loupe"
MODES = (("fit", "Sığdır"), ("width", "Genişlik"), ("actual", "%100"))


class ThumbStrip(QAbstractScrollArea):
    """Horizontal strip; paints only the visible thumbnails, caches the rendered ones."""

    clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self._count = 0
        self._current = 0
        self._render: Callable[[int, QSize], QPixmap] | None = None
        self._cache: OrderedDict[int, QPixmap] = OrderedDict()
        self._thumb = QSize(m.size("thumb-w") // 2, m.size("thumb-h") // 2)
        self._gap = m.size("s2")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFixedHeight(self._thumb.height() + 2 * self._gap + 16)
        self.horizontalScrollBar().setSingleStep(self._pitch())
        self.setAccessibleName("Sayfa küçük resimleri")

    def _pitch(self) -> int:
        return self._thumb.width() + self._gap

    def setup(self, count: int, render: Callable[[int, QSize], QPixmap]) -> None:
        self._count, self._render = count, render
        self._cache.clear()
        self._update_range()
        self.viewport().update()

    def _update_range(self) -> None:
        total = self._count * self._pitch() + self._gap
        bar = self.horizontalScrollBar()
        bar.setRange(0, max(0, total - self.viewport().width()))
        bar.setPageStep(self.viewport().width())

    def set_current(self, index: int) -> None:
        self._current = index
        left, pitch = index * self._pitch() + self._gap, self._pitch()
        bar, width = self.horizontalScrollBar(), self.viewport().width()
        if left < bar.value():
            bar.setValue(left - self._gap)
        elif left + pitch > bar.value() + width:
            bar.setValue(left + pitch - width)
        self.viewport().update()

    def visible_range(self) -> range:
        first = max(0, (self.horizontalScrollBar().value() - self._gap) // self._pitch())
        last = (self.horizontalScrollBar().value() + self.viewport().width()) // self._pitch()
        return range(first, min(self._count, last + 1))

    def _rect(self, index: int) -> QRect:
        x = index * self._pitch() + self._gap - self.horizontalScrollBar().value()
        return QRect(x, self._gap, self._thumb.width(), self._thumb.height())

    def _pixmap(self, index: int) -> QPixmap | None:
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]
        if self._render is None:
            return None
        pix = self._render(index, self._thumb)
        self._cache[index] = pix
        while len(self._cache) > CACHE_PAGES:
            self._cache.popitem(last=False)
        return pix

    def resizeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_range()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(event.rect(), m.color("layer"))
        font = m.font("caption-num")
        painter.setFont(font)
        for index in self.visible_range():
            box = self._rect(index)
            pix = self._pixmap(index)
            if pix is not None and not pix.isNull():
                scaled = pix.scaled(box.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
                size = scaled.deviceIndependentSize()
                target = QRectF(box.x() + (box.width() - size.width()) / 2,
                                box.y() + (box.height() - size.height()) / 2,
                                size.width(), size.height())
                painter.drawPixmap(target, scaled, QRectF(scaled.rect()))
            painter.setPen(m.color("text-2"))
            painter.drawText(QRect(box.x(), box.bottom() + 1, box.width(), 16),
                             Qt.AlignmentFlag.AlignCenter, str(index + 1))
            if index == self._current:
                style.paint_ring(painter, QRectF(box).adjusted(-1, -1, 1, 1), m.size("r-control"))

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            index = (event.position().toPoint().x() + self.horizontalScrollBar().value()
                     - self._gap) // self._pitch()
            if 0 <= index < self._count:
                self.clicked.emit(index)


class Loupe(QWidget):
    """Overlay filling its parent window; use ``open(...)``."""

    index_changed = Signal(int)
    closed = Signal(int)

    def __init__(self, parent: QWidget | None = None, prefs: Prefs | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self._count = 0
        self._index = 0
        self._render: Callable[[int, QSize], QPixmap] | None = None
        self._title: Callable[[int], str] | None = None
        self._opener: QWidget | None = None
        self._mode = "fit"
        self._applying = False
        self._base: dict[int, QPixmap] = {}
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Sayfa büyüteci")
        self.hide()
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s4"), m.size("s3"), m.size("s4"), m.size("s3"))
        col.setSpacing(m.size("s3"))

        bar = QHBoxLayout()
        bar.setSpacing(m.size("s2"))
        self._title_label = QLabel()
        self._title_label.setFont(m.font("body-strong"))
        bar.addWidget(self._title_label, 1)
        self._mode_buttons: dict[str, QPushButton] = {}
        for key, label in MODES:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda _=False, k=key: self.set_mode(k))
            self._mode_buttons[key] = button
            bar.addWidget(button)
        self.page_view = QScrollArea()
        self.page_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.page_view.setWidgetResizable(True)
        self.page_view.setFrameShape(QFrame.Shape.NoFrame)
        self.page_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page = QLabel()
        self._page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_view.setWidget(self._page)
        self.zoom = ZoomController(self.page_view, prefs, KEY, 10, 200, 25, self._fit_percent)
        self.zoom.zoom_changed.connect(self._on_zoom)
        self._slider = ZoomSlider(self.zoom, "Büyüteç")
        bar.addWidget(self._slider)
        close = QToolButton()
        close.setProperty("kind", "icon")
        close.setIcon(icons.icon("x", m.hex("icon")))
        close.setToolTip("Kapat (Esc)")
        close.setAccessibleName("Büyüteci kapat")
        close.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close.clicked.connect(self.close_loupe)
        bar.addWidget(close)
        col.addLayout(bar)
        col.addWidget(self.page_view, 1)
        self.strip = ThumbStrip()
        self.strip.clicked.connect(self.set_index)
        col.addWidget(self.strip)
        hint = QLabel("←/→ sayfa değiştir · Boşluk veya Esc kapat · Ctrl+tekerlek yakınlaştır")
        hint.setProperty("textRole", "caption")
        col.addWidget(hint)
        if parent is not None:
            parent.installEventFilter(self)
        theme.manager().changed.connect(self._restyle)
        self._restyle()

    # -- public ---------------------------------------------------------------
    def open(self, page_count: int, render: Callable[[int, QSize], QPixmap], index: int,
             title: Callable[[int], str] | None = None) -> None:
        """Show page ``index`` of ``page_count``; remembers the focused widget."""
        if page_count <= 0:
            return
        focused = QApplication.focusWidget()
        self._opener = focused if focused is not self else None
        self._count, self._render, self._title = page_count, render, title
        self._base.clear()
        self.strip.setup(page_count, render)
        parent = self.parentWidget()
        if parent is not None:
            self.setGeometry(parent.rect())
        self._mode = "fit"
        self._index = -1
        self.raise_()
        motion.fade_in(self, motion.Duration.NORMAL)
        self.setFocus(Qt.FocusReason.PopupFocusReason)
        self.set_index(index)

    def is_open(self) -> bool:
        return self.isVisible()

    def index(self) -> int:
        return self._index

    def set_index(self, index: int) -> None:
        index = max(0, min(self._count - 1, index))
        if index == self._index:
            return
        self._index = index
        self.strip.set_current(index)
        label = self._title(index) if self._title is not None else ""
        self._title_label.setText(label or f"Sayfa {index + 1}")
        self._title_label.setAccessibleDescription(f"{index + 1} / {self._count}")
        self._apply_mode()
        self._show_page()
        self.index_changed.emit(index)

    def set_mode(self, mode: str) -> None:
        """"fit", "width" or "actual" (%100)."""
        self._mode = mode
        self._apply_mode()
        self._show_page()

    def _apply_mode(self) -> None:
        target = {"fit": self._fit_percent, "width": self._width_percent,
                  "actual": lambda: 100}.get(self._mode)
        if target is not None:
            self._applying = True
            self.zoom.set_zoom(target(), save=False)
            self._applying = False

    def close_loupe(self) -> None:
        """Hide and return focus to the opener."""
        if not self.isVisible():
            return
        index = self._index
        motion.fade_out(self, motion.Duration.FAST)
        opener = self._opener
        if opener is not None and shiboken6.isValid(opener):
            opener.setFocus(Qt.FocusReason.OtherFocusReason)
        self._base.clear()
        self.closed.emit(index)

    # -- rendering --------------------------------------------------------------
    def _base_pixmap(self) -> QPixmap | None:
        if self._render is None or not 0 <= self._index < self._count:
            return None
        if self._index not in self._base:
            if len(self._base) > 8:
                self._base.clear()
            self._base[self._index] = self._render(self._index, PAGE_100)
        return self._base[self._index]

    def _fit_percent(self) -> int:
        base = self._base_pixmap()
        if base is None or base.isNull():
            return 100
        box = self.page_view.viewport().size()
        size = base.deviceIndependentSize()
        return int(min(box.width() / size.width(), box.height() / size.height()) * 100)

    def _width_percent(self) -> int:
        base = self._base_pixmap()
        if base is None or base.isNull():
            return 100
        return int(self.page_view.viewport().width() / base.deviceIndependentSize().width() * 100)

    def _show_page(self) -> None:
        base = self._base_pixmap()
        if base is None or base.isNull():
            self._page.clear()
            return
        pct = self.zoom.zoom()
        size = QSize(round(PAGE_100.width() * pct / 100), round(PAGE_100.height() * pct / 100))
        if pct == 100:
            pix = base
        elif pct > 100 and self._render is not None:
            pix = self._render(self._index, size)
        else:
            pix = base.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        self._page.setPixmap(pix)
        self._sync_modes()

    def _on_zoom(self, pct: int) -> None:
        """The user zoomed (wheel, keys, slider): name the mode that matches, else custom."""
        if self._applying:
            return
        if pct == self._fit_percent():
            self._mode = "fit"
        elif pct == self._width_percent():
            self._mode = "width"
        else:
            self._mode = "actual" if pct == 100 else "custom"
        self._show_page()

    def _sync_modes(self) -> None:
        for key, button in self._mode_buttons.items():
            button.setChecked(self._mode == key)

    # -- events -----------------------------------------------------------------
    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Space):
            self.close_loupe()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            self.set_index(self._index + 1)
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            self.set_index(self._index - 1)
        elif key == Qt.Key.Key_Home:
            self.set_index(0)
        elif key == Qt.Key.Key_End:
            self.set_index(self._count - 1)
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and key in (
                Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_Minus, Qt.Key.Key_0):
            self.zoom.eventFilter(self.page_view, event)
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if obj is self.parentWidget() and event.type() == QEvent.Type.Resize and self.isVisible():
            self.setGeometry(self.parentWidget().rect())
        return False

    def resizeEvent(self, event: QEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._mode in ("fit", "width") and self._count:
            self._apply_mode()
            self._show_page()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        QPainter(self).fillRect(event.rect(), theme.manager().color("base"))

    def _restyle(self) -> None:
        m = theme.manager()
        palette = self.page_view.viewport().palette()
        palette.setColor(palette.ColorRole.Window, m.color("well"))
        self.page_view.viewport().setPalette(palette)
        self.page_view.viewport().setAutoFillBackground(True)
