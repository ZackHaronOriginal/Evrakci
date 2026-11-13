"""Loupe: a large page preview over the window (spec state kontrol-loupe, final-a).

A's head row: "Sayfa 73 / 640", the page's place ("Belge 16, Ekspertiz Raporu, 2. sayfa"),
the orange Kontrol rider when the page needs a look, then the Sığdır / Genişlik / %100 switch
(16 × 3 accent pill under the chosen one) and "× Kapat". The page sits in the well with a
chevron on each side; the strip of nearby pages stays below, with a gap before each document's
first page and a ring around the current one. The window's status-bar slider drives the zoom
(the screen registers `zoom`). Arrows and Page keys turn pages, Esc or Space closes and gives
focus back to whoever opened it. The strip paints and renders only the pages it shows, so a
1,000 page job stays smooth. ``render(index, size)`` returns a pixmap that fits ``size``.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable

import shiboken6
from PySide6.QtCore import QEvent, QObject, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QFontMetrics,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPixmap,
)
from PySide6.QtWidgets import (
    QAbstractButton,
    QAbstractScrollArea,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, motion, theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.kontrol_paint import hc, paint_paper, paint_rider, rider_size
from evrakci.ui.prefs import Prefs
from evrakci.ui.zoomview import ZoomController

PAGE_100 = QSize(1240, 1754)  # what %100 means: an A4 page at 150 dpi
CACHE_PAGES = 400
KEY = "loupe"
MODES = (("fit", "Sığdır"), ("width", "Genişlik"), ("actual", "%100"))
MINI = QSize(40, 56)  # A .mini i
HEAD_H = {100: 40, 150: 52}  # A .loupe grid rows (head, strip) at 100 % and 150 % text
STRIP_H = {100: 84, 150: 92}
PAGE_PAD = 6  # room around the page for its shadow


def _rows(table: dict[int, int]) -> int:
    return table[150] if theme.manager().text_scale() >= 130 else table[100]


class ThumbStrip(QAbstractScrollArea):
    """A .lp-strip: the pages around the current one, centred on it, a gap before each
    document's first page; paints only those, caches the rendered ones."""

    clicked = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._count = 0
        self._current = 0
        self._render: Callable[[int, QSize], QPixmap] | None = None
        self._doc_start: Callable[[int], bool] = lambda _i: False
        self._cache: OrderedDict[int, QPixmap] = OrderedDict()
        self._thumb = QSize(MINI)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAccessibleName("Yakındaki sayfalar")
        self.viewport().setAutoFillBackground(False)
        self.setStyleSheet("QAbstractScrollArea { background: transparent; border: 0; }")

    def _gap(self) -> int:
        return theme.manager().size("s3")

    def _pitch(self) -> int:
        return self._thumb.width() + self._gap()

    def setup(self, count: int, render: Callable[[int, QSize], QPixmap],
              doc_start: Callable[[int], bool] | None = None) -> None:
        self._count, self._render = count, render
        self._doc_start = doc_start or (lambda _i: False)
        self._cache.clear()
        self.viewport().update()

    def set_current(self, index: int) -> None:
        self._current = index
        self.viewport().update()

    def _layout(self) -> dict[int, QRect]:
        """index -> thumbnail rect; the current page is centred and as many neighbours as fit
        sit beside it (s3 apart, s4 more before a document's first page)."""
        if not 0 <= self._current < self._count:
            return {}
        m = theme.manager()
        width, top = self.viewport().width(), m.size("s2")
        w, h, extra = self._thumb.width(), self._thumb.height(), m.size("s4")
        found = {self._current: QRect((width - w) // 2, top, w, h)}
        x = found[self._current].x()
        for index in range(self._current - 1, -1, -1):
            x -= self._pitch() + (extra if self._doc_start(index + 1) else 0)
            if x < 0:
                break
            found[index] = QRect(x, top, w, h)
        x = found[self._current].x()
        for index in range(self._current + 1, self._count):
            x += self._pitch() + (extra if self._doc_start(index) else 0)
            if x + w > width:
                break
            found[index] = QRect(x, top, w, h)
        return found

    def visible_range(self) -> range:
        shown = self._layout()
        return range(min(shown), max(shown) + 1) if shown else range(0)

    def _rect(self, index: int) -> QRect:
        return self._layout().get(index, QRect())

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

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        caption = m.font("caption-num")
        strong = m.font("caption-strong")
        line = QFontMetrics(caption).height()
        radius = m.size("r-paper")
        for index, box in sorted(self._layout().items()):
            current = index == self._current
            rect = QRectF(box)
            if current:  # A .mini.on i: 2 px of layer, then a 2 px accent ring
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(m.color("accent"))
                painter.drawRoundedRect(rect.adjusted(-4, -4, 4, 4), radius + 4, radius + 4)
                painter.setBrush(m.color("layer"))
                painter.drawRoundedRect(rect.adjusted(-2, -2, 2, 2), radius + 2, radius + 2)
            paint_paper(painter, rect)
            pix = self._pixmap(index)
            if pix is not None and not pix.isNull():
                scaled = pix.scaled(box.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                    Qt.TransformationMode.SmoothTransformation)
                size = scaled.deviceIndependentSize()
                target = QRectF(rect.x() + (rect.width() - size.width()) / 2,
                                rect.y() + (rect.height() - size.height()) / 2,
                                size.width(), size.height())
                clip = QPainterPath()
                clip.addRoundedRect(rect, radius, radius)
                painter.save()
                painter.setClipPath(clip)
                painter.drawPixmap(target, scaled, QRectF(scaled.rect()))
                painter.restore()
            painter.setFont(strong if current else caption)
            painter.setPen(m.color("text-accent" if current else "text-2"))
            label = QRect(box.x() - m.size("s2"), box.bottom() + 1 + m.size("s1"),
                          box.width() + 2 * m.size("s2"), line)
            painter.drawText(label, Qt.AlignmentFlag.AlignCenter, str(index + 1))

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            point = event.position().toPoint()
            for index, box in self._layout().items():
                if box.adjusted(-4, -4, 4, 24).contains(point):
                    self.clicked.emit(index)
                    return


class _ModeItem(QAbstractButton):
    """One item of A's .seg: the label (text-2, semibold and text when chosen) with the 16 × 3
    accent pill under the chosen one; hover fill like the command bar."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(text)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.toggled.connect(lambda _on: self.update())

    def sizeHint(self) -> QSize:  # noqa: N802
        m = theme.manager()
        bold = QFontMetrics(m.font("body-strong")).horizontalAdvance(self.text())
        return QSize(bold + 2 * m.size("s3"), m.size("control-h"))

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.underMouse() and not self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(m.color("hover"))
            painter.drawRoundedRect(QRectF(self.rect()), m.size("r-control"), m.size("r-control"))
        if self.isChecked() and hc():  # A hc: a 1 px accent outline on the chosen item
            painter.setPen(m.color("accent"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5),
                                    m.size("r-control"), m.size("r-control"))
        painter.setFont(m.font("body-strong" if self.isChecked() else "body-medium"))
        painter.setPen(m.color("text" if self.isChecked() else "text-2"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(m.color("accent"))
            painter.drawRoundedRect(QRectF(self.width() / 2 - 8, self.height() - 2 - 3, 16, 3),
                                    2, 2)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.update()
        super().leaveEvent(event)


class _Rider(QWidget):
    """The orange Kontrol rider of the head row (kontrol_paint.paint_rider)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Kontrol")
        self.setToolTip("Bu sayfanın belgesi kontrol bekliyor")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:  # noqa: N802
        return rider_size()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        size = rider_size()
        paint_rider(painter, QRectF(0, (self.height() - size.height()) / 2, size.width(),
                                    size.height()))


class _Page(QWidget):
    """The page in the well: paper, its edge and shadow, the rendered page on it."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pix = QPixmap()

    def setPixmap(self, pix: QPixmap) -> None:  # noqa: N802
        self._pix = pix
        size = pix.deviceIndependentSize().toSize() if not pix.isNull() else QSize()
        self.setMinimumSize(size + QSize(2 * PAGE_PAD, 2 * PAGE_PAD))
        self.update()

    def clear(self) -> None:
        self.setPixmap(QPixmap())

    def pixmap(self) -> QPixmap:
        return self._pix

    def page_rect(self) -> QRectF:
        """Where the page is drawn, in this widget."""
        if self._pix.isNull():
            return QRectF()
        size = self._pix.deviceIndependentSize()
        return QRectF((self.width() - size.width()) / 2, (self.height() - size.height()) / 2,
                      size.width(), size.height())

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        if self._pix.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.page_rect()
        paint_paper(painter, rect)
        painter.drawPixmap(rect, self._pix, QRectF(self._pix.rect()))


class _Stage(QWidget):
    """A .lp-stage: the well (r-layer corners; hc: a 1 px stroke) holding the page view and
    the two chevrons beside the page."""

    def __init__(self, view: QScrollArea, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.view = view
        view.setParent(self)
        self.prev = self._chevron("chevron-left", "Önceki sayfa", "Left")
        self.next = self._chevron("chevron-right", "Sonraki sayfa", "Right")
        view.horizontalScrollBar().valueChanged.connect(self.place)

    def _chevron(self, icon: str, text: str, key: str) -> QToolButton:
        button = QToolButton(self)
        button.setProperty("kind", "icon")
        button.setAutoRaise(True)
        button.setProperty("lucide", icon)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tip = f"{text} ({actions.key_text(key)})"
        button.setToolTip(tip)
        button.setAccessibleName(tip)
        return button

    def restyle(self) -> None:
        m = theme.manager()
        side = m.size("icon-btn")
        for button in (self.prev, self.next):
            button.setIcon(make_icon(button.property("lucide"), "icon", m.size("icon-md"), 1.6))
            button.setIconSize(QSize(m.size("icon-md"), m.size("icon-md")))
            button.setFixedSize(side, side)
        self.place()

    def side_room(self) -> int:
        """Room kept free left and right of a fitted page for the chevrons (A: gap s8)."""
        m = theme.manager()
        return m.size("s8") + m.size("icon-btn") + m.size("s2")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.view.setGeometry(self.rect())
        self.place()

    def place(self, *_args) -> None:
        """The chevrons s8 beside the page, kept inside the well, centred on it."""
        page = self.view.widget()
        m = theme.manager()
        side = self.prev.width()
        y = (self.height() - side) // 2
        rect = page.page_rect() if isinstance(page, _Page) else QRectF()
        if rect.isNull():
            left, right = m.size("s2"), self.width() - m.size("s2") - side
        else:
            origin = page.mapTo(self, rect.topLeft().toPoint())
            left = max(m.size("s2"), origin.x() - m.size("s8") - side)
            right = min(self.width() - m.size("s2") - side,
                        origin.x() + round(rect.width()) + m.size("s8"))
        self.prev.move(left, y)
        self.next.move(right, y)
        self.prev.raise_()
        self.next.raise_()

    def paintEvent(self, _event: QPaintEvent) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius = m.size("r-layer")
        painter.setPen(m.color("stroke") if hc() else Qt.PenStyle.NoPen)
        painter.setBrush(m.color("well"))
        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), radius,
                                radius)


class Loupe(QWidget):
    """Overlay filling its parent; use ``open(...)``."""

    index_changed = Signal(int)
    closed = Signal(int)

    def __init__(self, parent: QWidget | None = None, prefs: Prefs | None = None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self._count = 0
        self._index = 0
        self._render: Callable[[int, QSize], QPixmap] | None = None
        self._title: Callable[[int], str] | None = None
        self._kontrol: Callable[[int], bool] | None = None
        self._opener: QWidget | None = None
        self._mode = "fit"
        self._applying = False
        self._base: dict[int, QPixmap] = {}
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Önizleme")
        self.hide()
        self._col = col = QVBoxLayout(self)
        col.setSpacing(m.size("s2"))

        self.head = QWidget()
        bar = QHBoxLayout(self.head)
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(m.size("s3"))
        self._page_label = QLabel()
        self._page_label.setTextFormat(Qt.TextFormat.RichText)
        bar.addWidget(self._page_label)
        self._title_label = QLabel()  # the page's place: "Belge 16, Ekspertiz Raporu, 2. sayfa"
        self._title_label.setProperty("textRole", "secondary")
        bar.addWidget(self._title_label)
        self._rider = _Rider()
        self._rider.hide()
        bar.addWidget(self._rider)
        bar.addStretch(1)
        seg = QHBoxLayout()
        seg.setSpacing(2)
        self._mode_buttons: dict[str, _ModeItem] = {}
        for key, label in MODES:
            button = _ModeItem(label)
            button.clicked.connect(lambda _=False, k=key: self.set_mode(k))
            self._mode_buttons[key] = button
            seg.addWidget(button)
        bar.addLayout(seg)
        # The leading space gives A's 8 px icon gap (a QSS push button leaves 4 px).
        self.close_button = QPushButton(" Kapat")
        self.close_button.setProperty("variant", "subtle")
        self.close_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.close_button.setToolTip(f"Kapat ({actions.key_text('Esc')})")
        self.close_button.setAccessibleName("Önizlemeyi kapat")
        self.close_button.clicked.connect(self.close_loupe)
        bar.addWidget(self.close_button)
        col.addWidget(self.head)

        self.page_view = QScrollArea()
        self.page_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.page_view.setWidgetResizable(True)
        self.page_view.setFrameShape(QFrame.Shape.NoFrame)
        self.page_view.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget "
                                     "{ background: transparent; border: 0; }")
        self._page = _Page()
        self.page_view.setWidget(self._page)
        self.stage = _Stage(self.page_view)
        self.stage.prev.clicked.connect(lambda: self.set_index(self._index - 1))
        self.stage.next.clicked.connect(lambda: self.set_index(self._index + 1))
        self.zoom = ZoomController(self.page_view, prefs, KEY, 10, 200, 25, self._fit_percent)
        self.zoom.zoom_changed.connect(self._on_zoom)
        col.addWidget(self.stage, 1)
        self.strip = ThumbStrip()
        self.strip.clicked.connect(self.set_index)
        col.addWidget(self.strip)
        if parent is not None:
            parent.installEventFilter(self)
        theme.manager().changed.connect(self._restyle)
        self._restyle()

    # -- public ---------------------------------------------------------------
    def open(self, page_count: int, render: Callable[[int, QSize], QPixmap], index: int,
             title: Callable[[int], str] | None = None, *,
             kontrol: Callable[[int], bool] | None = None,
             doc_start: Callable[[int], bool] | None = None) -> None:
        """Show page ``index`` of ``page_count``; remembers the focused widget. ``title(i)``
        names the page's place, ``kontrol(i)`` shows the Kontrol rider, ``doc_start(i)`` puts
        a gap before a document's first page in the strip."""
        if page_count <= 0:
            return
        focused = QApplication.focusWidget()
        self._opener = focused if focused is not self else None
        self._count, self._render, self._title = page_count, render, title
        self._kontrol = kontrol
        self._base.clear()
        self.strip.setup(page_count, render, doc_start)
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
        self._sync_head()
        self._apply_mode()
        self._show_page()
        self.index_changed.emit(index)

    def _sync_head(self) -> None:
        index = self._index
        if not 0 <= index < self._count:
            return
        m = theme.manager()
        self._page_label.setText(
            f"<span style='font-weight:600'>Sayfa {index + 1}</span> "
            f"<span style='color:{m.hex('text-2')}'>/ {self._count}</span>")
        self._page_label.setAccessibleName(f"Sayfa {index + 1} / {self._count}")
        place = self._title(index) if self._title is not None else ""
        self._title_label.setText(place)
        # A at 150 %: the page's place gives way so the row keeps one line.
        self._title_label.setVisible(bool(place) and m.text_scale() < 130)
        self._rider.setVisible(bool(self._kontrol is not None and self._kontrol(index)))
        self.stage.prev.setEnabled(index > 0)
        self.stage.next.setEnabled(index < self._count - 1)

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

    def _room(self) -> QSize:
        """The well minus the chevrons' room at the sides and A's margin above and below."""
        m = theme.manager()
        box = self.stage.size()
        return QSize(max(1, box.width() - 2 * self.stage.side_room()),
                     max(1, box.height() - 2 * (m.size("s4") + m.size("s1"))))

    def _fit_percent(self) -> int:
        base = self._base_pixmap()
        if base is None or base.isNull():
            return 100
        box, size = self._room(), base.deviceIndependentSize()
        return max(1, int(min(box.width() / size.width(), box.height() / size.height()) * 100))

    def _width_percent(self) -> int:
        base = self._base_pixmap()
        if base is None or base.isNull():
            return 100
        return max(1, int(self._room().width() / base.deviceIndependentSize().width() * 100))

    def _show_page(self) -> None:
        base = self._base_pixmap()
        if base is None or base.isNull():
            self._page.clear()
            self.stage.place()
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
        self.stage.place()

    def _on_zoom(self, pct: int) -> None:
        """The user zoomed (wheel, keys, status-bar slider): name the mode that matches."""
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
            if button.isChecked() != (self._mode == key):
                button.setAutoExclusive(False)  # "custom": none of the three is chosen
                button.setChecked(self._mode == key)
                button.setAutoExclusive(True)

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
        QPainter(self).fillRect(event.rect(), theme.manager().color("layer"))

    def _restyle(self) -> None:
        """A .loupe: padding s1 s6 s3, rows 40 / 1fr / 84 (52 / 92 at 150 %), gap s2."""
        m = theme.manager()
        self._col.setContentsMargins(m.size("s6"), m.size("s1"), m.size("s6"), m.size("s3"))
        self._col.setSpacing(m.size("s2"))
        self.head.setFixedHeight(_rows(HEAD_H))
        self.strip.setFixedHeight(_rows(STRIP_H))
        self._page_label.setFont(m.font("body"))
        self.close_button.setIcon(make_icon("x"))
        self.stage.restyle()
        for button in self._mode_buttons.values():
            button.updateGeometry()
        self._sync_head()
        if self.isVisible():
            self.strip.viewport().update()
