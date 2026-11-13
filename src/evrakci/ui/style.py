"""EvrakciStyle: Fusion plus what QSS cannot do (D11 focus ring, A's title tabs, metrics).

- Focus (D11): a 2 px outer + 1 px inner ring in focus-outer / focus-inner, 1 px outside the
  control and following its radius. A `FocusRing` overlay draws it around the keyboard-focused
  widget (never hidden, also on widgets Fusion does not frame); item views get it per item via
  PE_FrameFocusRect. A mouse click on a field shows the accent edge only (Fluent).
- Title tabs (QTabBar#titleTabs): A's filled tab, 8 px top corners, 1 px stroke and the two
  8 px reverse "feet" into the work layer; hover fill on the others.
- Metrics: icons 16 (small) / 20 (tool bars), the 9 px scrollbar, menu item height, tab size.
- Access keys: SH_UnderlineShortcut is off; underlines appear while Alt is held (A §5.1).
"""
from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QRectF, QSize, Qt
from PySide6.QtGui import QFont, QFontMetrics, QIcon, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFocusFrame,
    QMenu,
    QProxyStyle,
    QStyle,
    QStyleFactory,
    QStyleOptionTab,
    QWidget,
)

from evrakci.ui import motion, theme

RING = 3  # 1 px inner + 2 px outer, outside the control (Fluent FocusVisualMargin 1 + 2)
TITLE_TABS = "titleTabs"
_P = QStyle.PixelMetric


def paint_ring(painter: QPainter, rect: QRectF, radius: float) -> None:
    """The D11 ring inside `rect` (its outer edge): 2 px focus-outer, then 1 px focus-inner."""
    m = theme.manager()
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(QPen(m.color("focus-outer"), 2))
    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius + 2, radius + 2)
    painter.setPen(QPen(m.color("focus-inner"), 1))
    painter.drawRoundedRect(rect.adjusted(2.5, 2.5, -2.5, -2.5), radius + 0.5, radius + 0.5)
    painter.restore()


def paint_title_tab(painter: QPainter, rect: QRectF, selected: bool, hovered: bool) -> None:
    """A's title-band tab: selected = layer fill, stroke on three sides, 8 px top corners and
    8 px reverse feet at the bottom corners; unselected = hover fill only."""
    m = theme.manager()
    r = float(m.size("r-layer"))
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    left, right, top, bottom = rect.left(), rect.right() + 1, rect.top(), rect.bottom() + 1
    body = QPainterPath()
    body.moveTo(left, bottom)
    body.lineTo(left, top + r)
    body.arcTo(QRectF(left, top, 2 * r, 2 * r), 180, -90)
    body.lineTo(right - r, top)
    body.arcTo(QRectF(right - 2 * r, top, 2 * r, 2 * r), 90, -90)
    body.lineTo(right, bottom)
    if not selected:
        if hovered:
            painter.fillPath(body, m.color("hover"))
        painter.restore()
        return
    layer, stroke = m.color("layer"), QPen(m.color("stroke"), 1)
    feet = QPainterPath()
    feet.moveTo(left - r, bottom)
    feet.arcTo(QRectF(left - 2 * r, bottom - 2 * r, 2 * r, 2 * r), 270, 90)
    feet.lineTo(left, bottom)
    feet.closeSubpath()
    feet.moveTo(right, bottom)
    feet.lineTo(right, bottom - r)
    feet.arcTo(QRectF(right, bottom - 2 * r, 2 * r, 2 * r), 180, 90)
    feet.closeSubpath()
    painter.fillPath(body, layer)
    painter.fillPath(feet, layer)
    edge = QPainterPath()
    edge.moveTo(left - r, bottom - 0.5)
    edge.arcTo(QRectF(left - 2 * r - 0.5, bottom - 2 * r - 0.5, 2 * r, 2 * r), 270, 90)
    edge.lineTo(left + 0.5, top + r)
    edge.arcTo(QRectF(left + 0.5, top + 0.5, 2 * r, 2 * r), 180, -90)
    edge.lineTo(right - r - 0.5, top + 0.5)
    edge.arcTo(QRectF(right - 2 * r - 0.5, top + 0.5, 2 * r, 2 * r), 90, -90)
    edge.lineTo(right - 0.5, bottom - r)
    edge.arcTo(QRectF(right + 0.5, bottom - 2 * r - 0.5, 2 * r, 2 * r), 180, 90)
    painter.strokePath(edge, stroke)
    painter.restore()


# A's .tab: padding 0 12 0 10, icon gap 6, 2 px between tabs; 8 px room for the outer feet.
TAB_PAD_L, TAB_PAD_R, TAB_ICON_GAP, TAB_GAP, FOOT = 10, 12, 6, 2, 8
_POS = QStyleOptionTab.TabPosition


def _is_title_tab(option, widget) -> bool:
    return (isinstance(option, QStyleOptionTab) and widget is not None
            and widget.objectName() == TITLE_TABS)


def _tab_font(option, widget) -> QFont:
    font = QFont(widget.font())
    selected = bool(option.state & QStyle.StateFlag.State_Selected)
    font.setWeight(QFont.Weight.DemiBold if selected else QFont.Weight.Medium)
    return font


def title_tab_shape(option) -> QRectF:
    """The drawn tab inside the tab's rect (room for the feet at the ends, the gap between)."""
    rect = QRectF(option.rect)
    first = option.position in (_POS.Beginning, _POS.OnlyOneTab)
    last = option.position in (_POS.End, _POS.OnlyOneTab)
    return rect.adjusted(FOOT if first else 0, 0, -(FOOT if last else TAB_GAP), 0)


def title_tab_size(option, widget) -> QSize:
    """Width of icon + label + A's padding (+ feet room / gap); height per title_band_rule."""
    m = theme.manager()
    width = TAB_PAD_L + TAB_PAD_R + QFontMetrics(_tab_font(option, widget)).horizontalAdvance(
        option.text)
    if not option.icon.isNull():
        width += m.size("icon-sm") + (TAB_ICON_GAP if option.text else 0)
    first = option.position in (_POS.Beginning, _POS.OnlyOneTab)
    last = option.position in (_POS.End, _POS.OnlyOneTab)
    width += (FOOT if first else 0) + (FOOT if last else TAB_GAP)
    return QSize(width, m.title_band().tab_height)


def paint_title_tab_label(painter: QPainter, option, widget) -> None:
    """Icon (Selected mode when selected: accent) + label, text-2 / text, 500 / 600."""
    m = theme.manager()
    rect = title_tab_shape(option)
    state = option.state
    selected = bool(state & QStyle.StateFlag.State_Selected)
    enabled = bool(state & QStyle.StateFlag.State_Enabled)
    x = rect.left() + TAB_PAD_L
    icon = m.size("icon-sm")
    if not option.icon.isNull():
        mode = (QIcon.Mode.Disabled if not enabled
                else QIcon.Mode.Selected if selected else QIcon.Mode.Normal)
        top = rect.top() + (rect.height() - icon) / 2
        option.icon.paint(painter, QRectF(x, top, icon, icon).toRect(),
                          Qt.AlignmentFlag.AlignCenter, mode)
        x += icon + TAB_ICON_GAP
    painter.save()
    painter.setFont(_tab_font(option, widget))
    painter.setPen(m.color("text" if selected else "text-2") if enabled
                   else m.color("text-disabled"))
    painter.drawText(QRectF(x, rect.top(), rect.right() - x, rect.height()),
                     Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, option.text)
    painter.restore()


def focus_radius(widget: QWidget | None) -> int:
    """The control radius the ring follows: `focusRadius` property, cards/layers 8, else 4."""
    m = theme.manager()
    if widget is None:
        return m.size("r-control")
    value = widget.property("focusRadius")
    if isinstance(value, int):
        return value
    if widget.property("kind") in ("card", "layer", "toast", "infobar"):
        return m.size("r-layer")
    return m.size("r-control")


class EvrakciStyle(QProxyStyle):
    """Fusion with the D11 ring, A's title tabs and the spec's metrics."""

    def __init__(self) -> None:
        super().__init__(QStyleFactory.create("Fusion"))
        self.setObjectName("evrakci")
        self._underlines = False

    def show_underlines(self) -> bool:
        return self._underlines

    def set_show_underlines(self, on: bool) -> None:
        """Access-key underlines on (while Alt is held) or off; repaints the windows."""
        if on == self._underlines:
            return
        self._underlines = on
        app = QApplication.instance()
        for window in app.topLevelWidgets() if app else []:
            if window.isVisible():
                window.update()
                for child in window.findChildren(QWidget):
                    child.update()

    def styleHint(self, hint, option=None, widget=None, data=None):  # noqa: N802
        if hint == QStyle.StyleHint.SH_UnderlineShortcut:
            return int(self._underlines)
        if hint == QStyle.StyleHint.SH_Widget_Animation_Duration and motion.reduced_motion():
            return 0
        return super().styleHint(hint, option, widget, data)

    def pixelMetric(self, metric, option=None, widget=None):  # noqa: N802
        m = theme.manager()
        if metric in (_P.PM_FocusFrameHMargin, _P.PM_FocusFrameVMargin):
            return RING
        if metric in (_P.PM_SmallIconSize, _P.PM_ButtonIconSize, _P.PM_TabBarIconSize,
                      _P.PM_ListViewIconSize):
            return m.size("icon-sm")
        if metric == _P.PM_ToolBarIconSize:
            return m.size("icon-md")
        if metric == _P.PM_ScrollBarExtent:
            return theme.SCROLLBAR_W
        return super().pixelMetric(metric, option, widget)

    def sizeFromContents(self, kind, option, size, widget=None):  # noqa: N802
        result = super().sizeFromContents(kind, option, size, widget)
        m = theme.manager()
        if kind == QStyle.ContentsType.CT_MenuItem and result.height() > 4:
            return QSize(result.width(), max(result.height(), m.menu_item_height()))
        if _is_title_tab(option, widget):
            return title_tab_size(option, widget)
        return result

    def drawPrimitive(self, element, option, painter, widget=None):  # noqa: N802
        if element == QStyle.PrimitiveElement.PE_FrameFocusRect:
            if isinstance(widget, QAbstractItemView) or widget is None:
                paint_ring(painter, QRectF(option.rect), theme.manager().size("r-control") - 1)
            return  # everything else: the FocusRing overlay draws it outside the control
        super().drawPrimitive(element, option, painter, widget)

    def drawControl(self, element, option, painter, widget=None):  # noqa: N802
        if element == QStyle.ControlElement.CE_FocusFrame:
            target = widget.widget() if isinstance(widget, QFocusFrame) else None
            paint_ring(painter, QRectF(option.rect), focus_radius(target))
            return
        if _is_title_tab(option, widget):
            if element == QStyle.ControlElement.CE_TabBarTabShape:
                state = option.state
                paint_title_tab(painter, title_tab_shape(option),
                                bool(state & QStyle.StateFlag.State_Selected),
                                bool(state & QStyle.StateFlag.State_MouseOver))
                return
            if element == QStyle.ControlElement.CE_TabBarTabLabel:
                paint_title_tab_label(painter, option, widget)
                return
        super().drawControl(element, option, painter, widget)


class FocusOverlay(QWidget):
    """Transparent sibling drawn over the focused widget's edge; follows it around."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("focusRing")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for attr in (Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                     Qt.WidgetAttribute.WA_NoSystemBackground,
                     Qt.WidgetAttribute.WA_TranslucentBackground):
            self.setAttribute(attr, True)
        self._target: QWidget | None = None

    def target(self) -> QWidget | None:
        return self._target

    def set_target(self, widget: QWidget | None) -> None:
        if self._target is not None:
            self._target.removeEventFilter(self)
        self._target = widget
        if widget is None or widget.parentWidget() is None:
            self._target = None
            self.hide()
            return
        widget.installEventFilter(self)
        self.setParent(widget.parentWidget())
        self._follow()

    def _follow(self) -> None:
        widget = self._target
        if widget is None or not widget.isVisible():
            self.hide()
            return
        self.setGeometry(widget.geometry().adjusted(-RING, -RING, RING, RING))
        self.raise_()
        self.show()
        self.update()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        kind = event.type()
        if obj is self._target:
            if kind in (QEvent.Type.Move, QEvent.Type.Resize, QEvent.Type.Show,
                        QEvent.Type.ZOrderChange):
                self._follow()
            elif kind in (QEvent.Type.Hide, QEvent.Type.ParentChange):
                self.set_target(None)
        return False

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        paint_ring(painter, QRectF(self.rect()), focus_radius(self._target))


def _ring_target(widget: QWidget) -> QWidget | None:
    """The widget the ring goes around (a spin box / combo box for its inner line edit)."""
    parent = widget.parentWidget()
    from PySide6.QtWidgets import QAbstractSpinBox, QComboBox

    if isinstance(parent, (QAbstractSpinBox, QComboBox)):
        widget = parent
    if (widget.isWindow() or widget.focusPolicy() == Qt.FocusPolicy.NoFocus
            or isinstance(widget, (QAbstractItemView, QMenu, FocusOverlay))):
        return None
    return widget


# Focus that came from the keyboard or from code reacting to it shows the ring (Fluent's
# keyboard-only focus visual); a click or the window becoming active does not.
KEYBOARD_REASONS = (Qt.FocusReason.TabFocusReason, Qt.FocusReason.BacktabFocusReason,
                    Qt.FocusReason.ShortcutFocusReason, Qt.FocusReason.OtherFocusReason)


class FocusRing(QObject):
    """App event filter: moves the overlay to the keyboard-focused widget, handles Alt
    underlines and gives menus a translucent frameless window for their 8 px corners."""

    def __init__(self, style: EvrakciStyle, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.style = style
        self.overlay: FocusOverlay | None = None

    def _overlay(self) -> FocusOverlay:
        import shiboken6

        if self.overlay is None or not shiboken6.isValid(self.overlay):
            self.overlay = FocusOverlay()
        return self.overlay

    def show_for(self, widget: QWidget | None) -> None:
        """Put the ring on `widget` (None hides it)."""
        target = _ring_target(widget) if widget is not None else None
        self._overlay().set_target(target)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        kind = event.type()
        if kind == QEvent.Type.FocusIn and isinstance(obj, QWidget):
            reason = event.reason()
            if reason in KEYBOARD_REASONS:
                self.show_for(obj)
            elif reason != Qt.FocusReason.PopupFocusReason:
                self.show_for(None)
        elif kind == QEvent.Type.FocusOut and isinstance(obj, QWidget):
            overlay = self.overlay
            if (overlay is not None and event.reason() != Qt.FocusReason.PopupFocusReason
                    and overlay.target() is _ring_target(obj)):
                self.show_for(None)
        elif kind == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Alt:
                self.style.set_show_underlines(True)
            elif not event.modifiers() & Qt.KeyboardModifier.AltModifier:
                self.style.set_show_underlines(False)
        elif kind in (QEvent.Type.MouseButtonPress, QEvent.Type.ApplicationDeactivate):
            self.style.set_show_underlines(False)
        elif kind == QEvent.Type.Polish and isinstance(obj, QMenu):
            obj.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            obj.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
            obj.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        return False


_installed: tuple[QApplication, EvrakciStyle, FocusRing] | None = None


def install(app: QApplication) -> EvrakciStyle:
    """Make EvrakciStyle the app style and start the focus ring (once per app)."""
    global _installed
    if _installed is not None and _installed[0] is app:
        return _installed[1]
    style = EvrakciStyle()
    app.setStyle(style)
    ring = FocusRing(style, app)
    app.installEventFilter(ring)
    _installed = (app, style, ring)
    return style


def installed_style() -> EvrakciStyle | None:
    """The EvrakciStyle in use (None before install())."""
    return _installed[1] if _installed else None


def focus_ring() -> FocusRing | None:
    """The installed focus-ring filter (None before install())."""
    return _installed[2] if _installed else None


__all__ = ["RING", "EvrakciStyle", "FocusOverlay", "FocusRing", "focus_radius", "focus_ring",
           "install", "installed_style", "paint_ring", "paint_title_tab"]
