"""The Değerler inspector (A's "Kaynak" side): the page crop around the selected value, what
was read and the suggestion, and the three actions.

The crop is painted (no widget per box); pages render in a worker thread and are kept in a
small cache, so moving through 1,000 documents never blocks typing.
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

from PySide6.QtCore import QObject, QPointF, QRectF, QRunnable, QSize, Qt, QThreadPool, Signal
from PySide6.QtGui import QFont, QFontMetrics, QImage, QMouseEvent, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
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

from evrakci.ui import theme
from evrakci.ui.chrome import make_icon
from evrakci.ui.degerler_table import paint_level, paint_marked

SIDE_W = 368  # A: Değerler inspector
WELL_H = 168  # A: .well height at 100 % text (240 at 150 %)
BOX_AT = QPointF(96, 86)  # where the box sits on the paper (A's crop: label column, 2nd line)
CACHE = 12


def well_height() -> int:
    return min(240, round(WELL_H * theme.manager().text_scale() / 100))


# Page images, rendered off the window thread
class _Relay(QObject):
    done = Signal(str, int, QImage)


class _Render(QRunnable):
    def __init__(self, relay: _Relay, render: Callable[[str, int], QImage], pid: str,
                 dpi: int) -> None:
        super().__init__()
        self.relay, self.render, self.pid, self.dpi = relay, render, pid, dpi

    def run(self) -> None:
        try:
            image = self.render(self.pid, self.dpi)
        except Exception:  # noqa: BLE001 - a missing or broken batch file shows no crop
            image = QImage()
        self.relay.done.emit(self.pid, self.dpi, image)


class PageImages(QObject):
    """`get(pid, dpi)` returns a cached image or None and renders it in the background;
    `ready` fires when it arrives."""

    ready = Signal(str, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.render: Callable[[str, int], QImage] | None = None
        self._cache: OrderedDict[tuple[str, int], QImage] = OrderedDict()
        self._pending: set[tuple[str, int]] = set()
        self._relay = _Relay()
        self._relay.done.connect(self._done)

    def clear(self) -> None:
        self._cache.clear()

    def get(self, pid: str, dpi: int) -> QImage | None:
        key = (pid, dpi)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        if self.render is not None and key not in self._pending:
            self._pending.add(key)
            QThreadPool.globalInstance().start(_Render(self._relay, self.render, pid, dpi))
        return None

    def _done(self, pid: str, dpi: int, image: QImage) -> None:
        self._pending.discard((pid, dpi))
        self._cache[(pid, dpi)] = image
        while len(self._cache) > CACHE:
            self._cache.popitem(last=False)
        self.ready.emit(pid, dpi)


@dataclass(frozen=True)
class Crop:
    """What the source view shows: a page and the boxes on it (mm)."""

    pid: str
    box: tuple[float, float, float, float] | None
    others: tuple[tuple[str, str, tuple[float, float, float, float]], ...] = ()  # key, name, box


class SourceView(QWidget):
    """A's well with the scanned paper: the selected value's box outlined in paper-box.
    Clicking another variable's box asks for that value (`box_clicked(key)`)."""

    box_clicked = Signal(str)

    def __init__(self, images: PageImages, parent=None) -> None:
        super().__init__(parent)
        self.images = images
        self.crop: Crop | None = None
        self.zoom = 200
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(well_height())
        images.ready.connect(lambda *_: self.update())
        theme.follow(self, lambda: self.setFixedHeight(well_height()), "degerler-well")

    def set_crop(self, crop: Crop | None, description: str = "") -> None:
        self.crop = crop
        self.setAccessibleName(description or "Kaynak kesiti")
        self.update()

    def set_zoom(self, percent: int) -> None:
        self.zoom = percent
        self.update()

    def px_per_mm(self) -> float:
        return 96 / 25.4 * self.zoom / 100

    def _dpi(self) -> int:
        wanted = 96 * self.zoom / 100 * self.devicePixelRatioF()
        return int(min(400, max(48, -(-wanted // 48) * 48)))

    def paper_rect(self) -> QRectF:
        m = theme.manager()
        return QRectF(self.rect()).adjusted(m.size("s4"), m.size("s4"), 0, 0)

    def _origin(self, image: QImage | None, dpi: int) -> QPointF:
        """Top-left of the visible page area in mm: the box lands at BOX_AT on the paper."""
        if self.crop is None or self.crop.box is None:
            return QPointF(0, 0)
        scale = self.px_per_mm()
        x0, y0, _x1, y1 = self.crop.box
        x = x0 - BOX_AT.x() / scale
        y = (y0 + y1) / 2 - BOX_AT.y() / scale
        if image is not None and not image.isNull():
            paper = self.paper_rect()
            width_mm, height_mm = image.width() / dpi * 25.4, image.height() / dpi * 25.4
            x = min(x, width_mm - paper.width() / scale)
            y = min(y, height_mm - paper.height() / scale)
        return QPointF(max(0.0, x), max(0.0, y))

    def _to_view(self, box: tuple[float, float, float, float], origin: QPointF) -> QRectF:
        scale = self.px_per_mm()
        paper = self.paper_rect()
        return QRectF(paper.left() + (box[0] - origin.x()) * scale,
                      paper.top() + (box[1] - origin.y()) * scale,
                      (box[2] - box[0]) * scale, (box[3] - box[1]) * scale)

    def paintEvent(self, _event) -> None:  # noqa: N802
        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        well = QPainterPath()
        well.addRoundedRect(QRectF(self.rect()), m.size("r-control"), m.size("r-control"))
        painter.setClipPath(well)
        painter.fillRect(self.rect(), m.color("well"))
        if self.crop is None:
            return
        paper = self.paper_rect()
        dpi = self._dpi()
        image = self.images.get(self.crop.pid, dpi)
        origin = self._origin(image, dpi)
        sheet = QPainterPath()
        sheet.addRoundedRect(paper.adjusted(0, 0, 8, 8), m.size("r-paper"), m.size("r-paper"))
        painter.fillPath(sheet, m.color("paper"))
        if image is not None and not image.isNull():
            px = dpi / 25.4
            scale = self.px_per_mm()
            source = QRectF(origin.x() * px, origin.y() * px,
                            paper.width() / scale * px, paper.height() / scale * px)
            painter.save()
            painter.setClipPath(sheet, Qt.ClipOperation.IntersectClip)
            painter.drawImage(paper, image, source)
            painter.restore()
        if self.crop.box is not None:
            target = self._to_view(self.crop.box, origin).adjusted(-4, -2, 4, 2)
            painter.setPen(QPen(m.color("paper-box"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(target, 2, 2)

    def _hit(self, pos: QPointF) -> tuple[str, str] | None:
        if self.crop is None:
            return None
        image = self.images.get(self.crop.pid, self._dpi())
        origin = self._origin(image, self._dpi())
        for key, name, box in self.crop.others:
            if self._to_view(box, origin).adjusted(-4, -2, 4, 2).contains(pos):
                return key, name
        return None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        hit = self._hit(event.position())
        self.setCursor(Qt.CursorShape.PointingHandCursor if hit else Qt.CursorShape.ArrowCursor)
        self.setToolTip(f"{hit[1]} değerine git" if hit else "")

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        hit = self._hit(event.position())
        if hit is not None and event.button() == Qt.MouseButton.LeftButton:
            self.box_clicked.emit(hit[0])


class MarkedText(QWidget):
    """OCR text with tinted characters (see degerler_table.paint_marked). Text without marks
    that does not fit wraps at word breaks (A: a long firm name at 150 %)."""

    def __init__(self, role: str, style: str = "uncertain", parent=None) -> None:
        super().__init__(parent)
        self.role = role  # "read" (panel size) or "big" (page size, semibold)
        self.style = style
        self.text = ""
        self.marks: tuple[int, ...] = ()
        self.colour = "text"
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        theme.follow(self, self._resize, f"degerler-marked-{id(self)}")

    def font_(self) -> QFont:
        m = theme.manager()
        font = m.font("value")
        size, weight = {"read": ("fs-panel", QFont.Weight.Normal),
                        "big": ("fs-page", QFont.Weight.DemiBold)}[self.role]
        font.setPixelSize(m.size(size))
        font.setWeight(weight)
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 101)
        return font

    def _line(self) -> int:
        return theme.manager().size("lh-panel" if self.role == "read" else "lh-page")

    def _wraps(self, width: int) -> bool:
        metrics = QFontMetrics(self.font_())
        return not self.marks and width > 0 and metrics.horizontalAdvance(self.text) > width

    def _resize(self) -> None:
        height = self._line()
        if self._wraps(self.width()):
            flags = int(Qt.TextFlag.TextWordWrap)
            box = QFontMetrics(self.font_()).boundingRect(0, 0, self.width(), 10_000, flags,
                                                          self.text)
            lines = max(1, -(-box.height() // QFontMetrics(self.font_()).lineSpacing()))
            height = lines * self._line()
        self.setFixedHeight(height)
        self.update()

    def set(self, text: str, marks: tuple[int, ...] = (), colour: str = "text") -> None:
        self.text, self.marks, self.colour = text, marks, colour
        self.setAccessibleName(text)
        self.setToolTip(text)
        self._resize()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self.height() != self._line() or self._wraps(self.width()):
            self._resize()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(120, self.height())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        colour = theme.manager().color(self.colour)
        if self._wraps(self.width()):
            painter.setFont(self.font_())
            painter.setPen(colour)
            painter.drawText(self.rect(), int(Qt.TextFlag.TextWordWrap)
                             | int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
                             self.text)
            return
        paint_marked(painter, QRectF(self.rect()), self.text, self.font_(), colour, self.marks,
                     self.style)


class _CaptionFonts:
    def __init__(self) -> None:
        m = theme.manager()
        self.body = m.font("caption")
        self.strong = m.font("caption-strong")
        self.num = m.font("caption-num")


class LevelText(QWidget):
    """Güven in the meta row: icon + word + percent, then a quiet note ("2 karakter belirsiz")."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.level = "emin"
        self.percent: int | None = None
        self.note = ""
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        theme.follow(self, lambda: self.setFixedHeight(theme.manager().size("lh-caption") + 2),
                     f"degerler-level-{id(self)}")

    def set(self, level: str, percent: int | None, note: str = "") -> None:
        from evrakci.ui.degerler_model import LEVELS

        self.level, self.percent, self.note = level, percent, note
        word = LEVELS[level][2]
        self.setAccessibleName(" ".join(p for p in (
            f"Güven: {word}", f"%{percent}" if percent is not None else "", note) if p))
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        from evrakci.ui.degerler_table import level_width

        m = theme.manager()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fonts = _CaptionFonts()
        rect = QRectF(self.rect())
        paint_level(painter, rect, self.level, self.percent, fonts, 14)
        if self.note:
            left = level_width(self.level, self.percent, fonts) - 2 + m.size("s4")
            painter.setFont(fonts.body)
            painter.setPen(m.color("text-2"))
            painter.drawText(rect.adjusted(left, 0, 0, 0),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.note)


def _caption(text: str = "", wrap: bool = False) -> QLabel:
    label = QLabel(text)
    label.setProperty("textRole", "caption")
    label.setProperty("kind", "inspector-key")
    label.setWordWrap(wrap)
    return label


def _icon_button(icon: str, name: str, slot: Callable[[], None]) -> QToolButton:
    button = QToolButton()
    button.setProperty("kind", "icon")
    button.setProperty("sizeVariant", "sm")
    button.setAutoRaise(True)
    button.setIcon(make_icon(icon))
    button.setToolTip(name)
    button.setAccessibleName(name)
    button.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    button.clicked.connect(slot)
    theme.follow(button, lambda: button.setIcon(make_icon(icon)), f"degerler-ib-{icon}")
    return button


class SourceCard(QFrame):
    """"Sicil no / Belge 16, sayfa 72" with zoom out / in / whole page, and the crop well."""

    def __init__(self, images: PageImages, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setProperty("kind", "card")
        self.setAccessibleName("Kaynak")
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s3"), m.size("s3"), m.size("s3"), m.size("s4"))
        col.setSpacing(0)
        head = QHBoxLayout()
        head.setContentsMargins(m.size("s1"), 0, 0, m.size("s3"))
        head.setSpacing(m.size("s1"))
        words = QVBoxLayout()
        words.setSpacing(0)
        self.title = QLabel("")
        self.title.setFont(m.font("body-strong"))
        self.meta = _caption(wrap=True)
        words.addWidget(self.title)
        words.addWidget(self.meta)
        head.addLayout(words, 1)
        self.zoom_out = _icon_button("zoom-out", "Uzaklaştır (Ctrl+-)", lambda: None)
        self.zoom_in = _icon_button("zoom-in", "Yakınlaştır (Ctrl++)", lambda: None)
        self.whole = _icon_button("maximize-2", "Sayfanın tamamı (Boşluk)", lambda: None)
        for button in (self.zoom_out, self.zoom_in, self.whole):
            head.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        col.addLayout(head)
        self.view = SourceView(images)
        col.addWidget(self.view)
        # Nothing selected: A's blank well with the scan-text mark and one sentence
        self.blank = QFrame()
        self.blank.setProperty("kind", "well")
        self.blank.setFixedHeight(well_height())
        blank = QVBoxLayout(self.blank)
        blank.setContentsMargins(m.size("s6"), 0, m.size("s6"), 0)
        blank.setSpacing(m.size("s2"))
        blank.addStretch(1)
        self.blank_icon = QLabel()
        self.blank_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.blank_text = QLabel("Tablodan bir değer seçince sayfadaki yeri, okunan değer ve "
                                 "öneri burada görünür.")
        self.blank_text.setWordWrap(True)
        self.blank_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.blank_text.setProperty("textRole", "secondary")
        blank.addWidget(self.blank_icon)
        blank.addWidget(self.blank_text)
        blank.addStretch(1)
        col.addWidget(self.blank)
        theme.follow(self, self._restyle, "degerler-source")

    def _restyle(self) -> None:
        m = theme.manager()
        self.blank_icon.setPixmap(make_icon("scan-text", size=m.size("icon-md")).pixmap(
            m.size("icon-md"), m.size("icon-md")))
        self.blank.setFixedHeight(well_height())
        self.title.setFont(m.font("body-strong"))

    def show_blank(self, title: str, meta: str) -> None:
        self.title.setText(title)
        self.meta.setText(meta)
        for widget in (self.zoom_out, self.zoom_in, self.whole, self.view):
            widget.hide()
        self.blank.show()

    def show_crop(self, title: str, meta: str, crop: Crop | None, description: str) -> None:
        self.title.setText(title)
        self.meta.setText(meta)
        self.blank.hide()
        for widget in (self.zoom_out, self.zoom_in, self.whole, self.view):
            widget.show()
        self.view.set_crop(crop, description)


class ValueCard(QFrame):
    """Okunan (with uncertain characters), Öneri (with the changes marked), Güven and why."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setProperty("kind", "card")
        self.setAccessibleName("Okunan değer")
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s4"), m.size("s4"), m.size("s4"), m.size("s4"))
        col.setSpacing(0)
        self.read_label = _caption("Okunan")
        self.read = MarkedText("read")
        self.suggestion_label = _caption("Öneri")
        self.suggestion = MarkedText("big", "changed")
        self.level = LevelText()
        self.why = _caption("", wrap=True)
        col.addWidget(self.read_label)
        col.addSpacing(2)
        col.addWidget(self.read)
        self.read_gap = m.size("s3")
        col.addSpacing(self.read_gap)
        col.addWidget(self.suggestion_label)
        col.addSpacing(2)
        col.addWidget(self.suggestion)
        col.addSpacing(m.size("s3"))
        col.addWidget(self.level)
        col.addSpacing(m.size("s1"))
        col.addWidget(self.why)
        self._spacer = col.itemAt(3).spacerItem()

    def show_flagged(self, read: str, uncertain: tuple[int, ...], suggestion: str,
                     changes: tuple[int, ...]) -> None:
        self.read_label.show()
        self.read.show()
        self.read.set(read or "boş", uncertain if read else (), "text" if read else "text-2")
        self._spacer.changeSize(0, self.read_gap)
        self.suggestion_label.setVisible(bool(suggestion))
        self.suggestion.setVisible(bool(suggestion))
        self.suggestion.set(suggestion, changes)
        self.layout().invalidate()

    def show_value(self, text: str, colour: str = "text") -> None:
        """A value without a suggestion (A's Örnek card): "Okunan" + the value large."""
        self.read_label.show()
        self.read.hide()
        self._spacer.changeSize(0, 0)
        self.suggestion_label.hide()
        self.suggestion.show()
        self.suggestion.set(text, (), colour)
        self.layout().invalidate()


class _Scroll(QScrollArea):
    """Takes its content's height, so the actions follow the cards; scrolls when short."""

    def sizeHint(self) -> QSize:  # noqa: N802
        widget = self.widget()
        if widget is None:
            return super().sizeHint()
        layout = widget.layout()
        width = self.viewport().width() or widget.width()
        height = (layout.totalHeightForWidth(width) if layout.hasHeightForWidth()
                  else widget.sizeHint().height())
        return QSize(widget.sizeHint().width(), height)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(0, 0)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if event.oldSize().width() != event.size().width():
            self.updateGeometry()  # wrapped text: a new width is a new height


class SidePanel(QWidget):
    """Source card + value card, then the actions (pinned under the cards; when nothing is
    selected they sit at the bottom, as A's empty state draws them)."""

    def __init__(self, images: PageImages, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setAccessibleName("Kaynak")
        col = QVBoxLayout(self)
        col.setContentsMargins(m.size("s2"), 0, 0, 0)  # + the 4 px splitter handle = A's s3
        col.setSpacing(m.size("s3"))
        cards = QWidget()
        stack = QVBoxLayout(cards)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(m.size("s3"))
        self.source = SourceCard(images)
        self.value = ValueCard()
        stack.addWidget(self.source)
        stack.addWidget(self.value)
        stack.addStretch(1)
        self.scroll = _Scroll()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidget(cards)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        col.addWidget(self.scroll)
        col.addStretch(0)  # index 1: grows only in the blank state
        acts = QVBoxLayout()
        acts.setSpacing(m.size("s2"))
        # One space after the icon: Qt's 4 px icon gap + a space = A's s2 between them
        self.accept_button = QPushButton(" Onayla ve sonrakine geç")
        self.accept_button.setProperty("variant", "primary")
        self.accept_button.setProperty("sizeVariant", "lg")
        self.type_button = QPushButton(" Elle yaz")
        self.variant_button = QPushButton(" Yeni kutu çiz")
        pair = QHBoxLayout()
        pair.setSpacing(m.size("s2"))
        pair.addWidget(self.type_button, 1)
        pair.addWidget(self.variant_button, 1)
        acts.addWidget(self.accept_button)
        acts.addLayout(pair)
        col.addLayout(acts)
        col.addStretch(1)  # index 3: grows in the normal state
        self._icons = (("accept_button", "check", "text-on-accent"), ("type_button", "pencil",
                                                                        "icon"),
                       ("variant_button", "square", "icon"))
        self.accept_button.setToolTip("Onayla ve sonrakine geç (Enter)")
        self.type_button.setToolTip("Elle yaz (F2)")
        self.variant_button.setToolTip("Yeni kutu çiz (V)")
        for button in (self.accept_button, self.type_button, self.variant_button):
            button.setAccessibleName(button.toolTip())
        theme.follow(self, self._restyle, "degerler-side")
        self.setMinimumWidth(240 + m.size("s3"))

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(SIDE_W + theme.manager().size("s2"), super().sizeHint().height())

    def _restyle(self) -> None:
        m = theme.manager()
        for name, icon, role in self._icons:
            button: QPushButton = getattr(self, name)
            button.setIcon(make_icon(icon, role, m.size("icon-sm")))
        self.accept_button.setMinimumHeight(m.size("lg-h"))

    def set_blank(self, blank: bool) -> None:
        layout = self.layout()
        layout.setStretch(0, 1 if blank else 0)  # blank: the card on top, actions at the bottom
        layout.setStretch(1, 0)
        layout.setStretch(3, 0 if blank else 1)
        self.value.setVisible(not blank)
        self.relayout()

    def relayout(self) -> None:
        """The cards changed height: let the scroll area take their new size."""
        self.scroll.widget().adjustSize()
        self.scroll.updateGeometry()
        self.layout().invalidate()

    def set_actions(self, accept: bool, type_: bool, variant: bool) -> None:
        self.accept_button.setEnabled(accept)
        self.type_button.setEnabled(type_)
        self.variant_button.setEnabled(variant)
