"""Whole-card scrolling for the side panels (owner-approved PROPOSALS items 1 and 5).

A side panel whose cards do not fit (150 % text on a short window) scrolls card by card:

- the viewport only ever shows whole cards. It is masked just below the last card that fits
  fully, and the space left over stays empty;
- the wheel, the scroll bar, the keyboard and focus moving into a card all stop on card
  boundaries ("stops"). A stop is the top of a card's group (its group label included);
- while more content lies below, a 1 px `stroke` hairline sits above the pinned button group.

When everything fits (100 % text) there is no mask, no hairline and no scrolling, so nothing
changes. A "card" is a widget with `kind == "card"` (chrome.card); content between two cards,
such as a group label, belongs to the card below it, and content after the last card belongs
to the last card.
"""
from __future__ import annotations

import weakref

import shiboken6
from PySide6.QtCore import QEvent, QObject, QRect, Qt, QTimer
from PySide6.QtGui import QPainter, QRegion
from PySide6.QtWidgets import QApplication, QScrollArea, QWidget

from evrakci.ui import theme

WHEEL_NOTCH = 120  # one wheel notch in angleDelta units: one card
GROUP_GAP = 16  # a group label sits at most this far above its card (A: 0 to s2)

# One application-wide focusChanged hook for all panels, holding them weakly. With each panel
# connecting its own bound method, windows built after others were torn down failed to read
# their PDFs in the window tests, so no connection may outlive its panel.
_SCROLLERS: weakref.WeakSet = weakref.WeakSet()
_HOOKED = False


def _focus_changed(_old: QWidget | None, new: QWidget | None) -> None:
    if new is None:
        return
    for scroller in list(_SCROLLERS):
        if shiboken6.isValid(scroller) and shiboken6.isValid(scroller.area):
            scroller.focus_moved(new)


def _watch_focus(scroller: CardScroll) -> None:
    global _HOOKED
    _SCROLLERS.add(scroller)
    if not _HOOKED:
        QApplication.instance().focusChanged.connect(_focus_changed)
        _HOOKED = True


class _Edge(QWidget):
    """The 1 px hairline above the pinned buttons (A's --stroke)."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("cardScrollEdge")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.hide()

    def paintEvent(self, event) -> None:  # noqa: N802
        QPainter(self).fillRect(self.rect(), theme.manager().color("stroke"))


class CardScroll(QObject):
    """Attach to a QScrollArea (with its content set) so it scrolls whole cards only.
    `pinned` is the top widget of the button group pinned under the area, if any: the
    hairline is drawn centred in the gap between the area and it."""

    def __init__(self, area: QScrollArea, pinned: QWidget | None = None) -> None:
        super().__init__(area)
        self.area = area
        self.pinned = pinned
        self.edge: _Edge | None = None
        self._units: list[tuple[int, int]] = []  # (stop, bottom) in content coordinates
        self._end = 0  # bottom of the content
        self._busy = False
        self._wheel = 0
        self._last = 0  # the stop the panel rests on
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self.refresh)
        bar = area.verticalScrollBar()
        bar.valueChanged.connect(self._value_changed)
        bar.rangeChanged.connect(self._range_changed)
        area.installEventFilter(self)
        area.viewport().installEventFilter(self)
        if area.widget() is not None:
            area.widget().installEventFilter(self)
        if pinned is not None:
            pinned.installEventFilter(self)
        _watch_focus(self)
        self.schedule()

    # -- geometry -------------------------------------------------------------------------
    def _height(self) -> int:
        return self.area.viewport().height()

    def _measure(self) -> None:
        body = self.area.widget()
        self._units, self._end = [], 0
        if body is None:
            return
        children = [w for w in body.children()
                    if isinstance(w, QWidget) and not w.isWindow() and w.isVisibleTo(body)]
        if not children:
            return
        self._end = max(QWidget.geometry(w).bottom() for w in children)
        cards = []
        for w in body.findChildren(QWidget):
            if w.property("kind") != "card" or not w.isVisibleTo(body):
                continue
            parent = w.parentWidget()
            while parent is not None and parent is not body and parent.property("kind") != "card":
                parent = parent.parentWidget()
            if parent is body:  # not nested in another card
                top = w.mapTo(body, w.rect().topLeft()).y()
                cards.append((top, top + w.height() - 1))
        cards.sort()
        boxes = [QWidget.geometry(w) for w in children]
        for top, bottom in cards:
            stop = self._group_top(boxes, top, bottom)
            if self._units and stop <= self._units[-1][1]:
                stop = top  # never inside the card above
            self._units.append((stop, bottom))
        if self._units and self._units[0][0] > 0:  # a head above the first card: its own stop
            above = [b.bottom() for b in boxes if b.top() < self._units[0][0]]
            if above:
                self._units.insert(0, (0, min(max(above), self._units[0][0] - 1)))
            else:
                self._units[0] = (0, self._units[0][1])
        if self._units:
            last_stop, last_bottom = self._units[-1]
            self._units[-1] = (last_stop, max(last_bottom, self._end))
        else:
            self._units = [(0, self._end)]

    @staticmethod
    def _group_top(boxes: list[QRect], top: int, bottom: int) -> int:
        """Where a card's group starts: the top of the content's child that holds the card
        (a group widget), or of the group label just above it (within GROUP_GAP)."""
        holder = [b.top() for b in boxes if b.top() < top and b.bottom() >= bottom]
        if holder:
            return max(holder)
        label = [b for b in boxes if top - GROUP_GAP <= b.bottom() < top]
        return max(label, key=lambda b: b.bottom()).top() if label else top

    def scrollable(self) -> bool:
        """True when the content is taller than the viewport."""
        return self._end + 1 > self._height()

    def stops(self) -> list[int]:
        """The scroll positions the panel may rest on, from the top down to the last one
        from which every remaining card fits."""
        if not self.scrollable():
            return [0]
        height = self._height()
        found = []
        for stop, _bottom in self._units:
            found.append(stop)
            if self._end - stop + 1 <= height:
                break
        return found

    def shown_bottom(self, value: int | None = None) -> int | None:
        """The content y of the last fully shown card's bottom at scroll `value` (None when
        no card fits, then nothing is trimmed)."""
        value = self.area.verticalScrollBar().value() if value is None else value
        limit = value + self._height() - 1
        bottoms = [bottom for stop, bottom in self._units if stop >= value and bottom <= limit]
        return max(bottoms) if bottoms else None

    def more_below(self) -> bool:
        """True while content lies below what the panel shows."""
        if not self.scrollable():
            return False
        bottom = self.shown_bottom()
        return bottom is None or bottom < self._end

    # -- refreshing -----------------------------------------------------------------------
    def schedule(self) -> None:
        self._timer.start()

    def refresh(self) -> None:
        self._measure()
        bar = self.area.verticalScrollBar()
        stops = self.stops()
        self._busy = True
        try:
            if bar.maximum() != stops[-1]:
                bar.setRange(0, stops[-1])
            fits = [s for s in stops if s <= bar.value()]
            target = fits[-1] if fits else 0
            if bar.value() != target:
                bar.setValue(target)
            self._last = target
        finally:
            self._busy = False
        self._paint_state()

    def _paint_state(self) -> None:
        port = self.area.viewport()
        bottom = self.shown_bottom() if self.scrollable() else None
        if bottom is None:
            port.clearMask()
        else:
            value = self.area.verticalScrollBar().value()
            port.setMask(QRegion(QRect(0, 0, port.width(), bottom - value + 1)))
        self._place_edge()

    def _place_edge(self) -> None:
        pinned = self.pinned
        if pinned is None:
            return
        host = pinned.parentWidget()
        if host is None:
            return
        if self.edge is None or self.edge.parentWidget() is not host:
            self.edge = _Edge(host)
        area_box = QRect(self.area.mapTo(host, self.area.rect().topLeft()), self.area.size())
        top = pinned.mapTo(host, pinned.rect().topLeft()).y()
        y = (area_box.bottom() + 1 + top) // 2
        self.edge.setGeometry(area_box.left(), y, area_box.width(), 1)
        show = self.more_below() and pinned.isVisible() and self.area.isVisible()
        self.edge.setVisible(show)
        if show:
            self.edge.raise_()

    # -- scrolling ------------------------------------------------------------------------
    def _range_changed(self, _low: int, high: int) -> None:
        if self._busy:
            return
        stops = self.stops()
        if high != stops[-1]:
            self._busy = True
            try:
                self.area.verticalScrollBar().setRange(0, stops[-1])
            finally:
                self._busy = False
        self.schedule()

    def _value_changed(self, value: int) -> None:
        if not self._busy:
            target = self._snap(value)
            if target != value:
                self._busy = True
                try:
                    self.area.verticalScrollBar().setValue(target)
                finally:
                    self._busy = False
            self._last = target
        self._paint_state()

    def _snap(self, value: int) -> int:
        stops = self.stops()
        bar = self.area.verticalScrollBar()
        last = self._last
        if bar.isSliderDown():
            return min(stops, key=lambda s: abs(s - value))
        if value > last:
            return next((s for s in stops if s >= value), stops[-1])
        if value < last:
            return next((s for s in reversed(stops) if s <= value), stops[0])
        return min(stops, key=lambda s: abs(s - value))

    def step(self, cards: int) -> None:
        """Scroll `cards` stops down (negative: up)."""
        stops = self.stops()
        bar = self.area.verticalScrollBar()
        index = max(i for i, s in enumerate(stops) if s <= bar.value()) if stops else 0
        index = min(max(index + cards, 0), len(stops) - 1)
        self._busy = True
        try:
            bar.setValue(stops[index])
        finally:
            self._busy = False
        self._last = stops[index]
        self._paint_state()

    def reveal(self, widget: QWidget) -> None:
        """Scroll to the nearest stop that shows the whole card holding `widget`."""
        body = self.area.widget()
        if body is None or not body.isAncestorOf(widget) or not self.scrollable():
            return
        self._measure()
        y = widget.mapTo(body, widget.rect().topLeft()).y()
        unit = next(((s, b) for s, b in self._units if y <= b), self._units[-1])
        bar = self.area.verticalScrollBar()
        stops = self.stops()
        value = bar.value()
        bottom = self.shown_bottom(value)
        if unit[0] >= value and bottom is not None and unit[1] <= bottom:
            return  # already whole
        height = self._height()
        if unit[0] < value:
            target = max((s for s in stops if s <= unit[0]), default=stops[0])
        else:
            target = next((s for s in stops if unit[1] - s + 1 <= height), stops[-1])
            target = min(target, max((s for s in stops if s <= unit[0]), default=0))
        self._busy = True
        try:
            bar.setValue(target)
        finally:
            self._busy = False
        self._last = target
        self._paint_state()

    def focus_moved(self, new: QWidget) -> None:
        """Focus went to `new`: if it is in this panel, show its card whole (after the
        scroll area's own ensureWidgetVisible has run)."""
        body = self.area.widget()
        if body is None or not body.isAncestorOf(new):
            return
        QTimer.singleShot(0, self, lambda: self._reveal_later(new))

    def _reveal_later(self, widget: QWidget) -> None:
        if shiboken6.isValid(widget) and shiboken6.isValid(self.area):
            self.reveal(widget)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        kind = event.type()
        if kind == QEvent.Type.Wheel and obj is self.area.viewport():
            if not self.scrollable():
                return False
            self._wheel += event.angleDelta().y()
            notches = int(self._wheel / WHEEL_NOTCH)
            if notches:
                self._wheel -= notches * WHEEL_NOTCH
                self.step(-notches)
            event.accept()
            return True
        if kind in (QEvent.Type.Resize, QEvent.Type.LayoutRequest, QEvent.Type.Show,
                    QEvent.Type.Hide, QEvent.Type.Move):
            if obj is self.area.widget() and kind == QEvent.Type.Move:
                return False  # scrolling moves the content; the value handler covers it
            self.schedule()
        return False
