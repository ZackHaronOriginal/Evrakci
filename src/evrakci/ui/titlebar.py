"""The title band (A: logo, tabs, job switch, search, ≡, caption buttons) and its window frame.

On Windows the band replaces the system title bar: the window keeps a native thick frame
(WS_THICKFRAME | WS_CAPTION, so Snap, Aero Shake, the shadow and the animations stay), WM_NCCALCSIZE
gives the whole window to the client area, and WM_NCHITTEST says where to drag, resize and
which spot is the maximise button (HTMAXBUTTON, so Windows 11 shows Snap Layouts on hover).
Everywhere else, and when the pref Prefs.native_title_bar() is on, the system title bar stays and
the band is the window's first row without caption buttons. Every Win32 call is guarded.
"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QSpacerItem,
    QTabBar,
    QToolButton,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.chrome import CaptionButton
from evrakci.ui.prefs import Prefs
from evrakci.ui.style import FOOT, paint_title_tab

HTCLIENT, HTCAPTION, HTMAXBUTTON = 1, 2, 9
HTLEFT, HTRIGHT, HTTOP, HTTOPLEFT, HTTOPRIGHT = 10, 11, 12, 13, 14
HTBOTTOM, HTBOTTOMLEFT, HTBOTTOMRIGHT = 15, 16, 17
WM_NCCALCSIZE, WM_NCHITTEST = 0x0083, 0x0084
WM_NCMOUSEMOVE, WM_NCLBUTTONDOWN, WM_NCLBUTTONUP = 0x00A0, 0x00A1, 0x00A2
WM_MOUSEMOVE, WM_NCMOUSELEAVE = 0x0200, 0x02A2
ENV_NATIVE = "EVRAKCI_YEREL_BASLIK"  # "1": keep the system title bar


def native_title_bar(prefs: Prefs | None) -> bool:
    """The user's "native title bar" pref (Ayarlar > Görünüm) or EVRAKCI_YEREL_BASLIK=1."""
    if os.environ.get(ENV_NATIVE) == "1":
        return True
    return prefs is not None and prefs.native_title_bar()


def custom_frame_supported() -> bool:
    """True on the real Windows platform plugin (not offscreen, not other systems)."""
    app = QGuiApplication.instance()
    return sys.platform == "win32" and app is not None and app.platformName() == "windows"


def use_custom_frame(prefs: Prefs | None) -> bool:
    return custom_frame_supported() and not native_title_bar(prefs)


def hit_test(size: QSize, pos: QPoint, border: int, band_height: int, maximized: bool,
             max_button: QRect | None, draggable: bool) -> int:
    """The WM_NCHITTEST answer for `pos` (window coordinates): resize edges (not when
    maximised), the maximise button, the draggable band, else the client area."""
    x, y, w, h = pos.x(), pos.y(), size.width(), size.height()
    if not maximized:
        left, right = x < border, x >= w - border
        top, bottom = y < border, y >= h - border
        corner = 2 * border
        if top and x < corner or left and y < corner:
            return HTTOPLEFT
        if top and x >= w - corner or right and y < corner:
            return HTTOPRIGHT
        if bottom and x < corner or left and y >= h - corner:
            return HTBOTTOMLEFT
        if bottom and x >= w - corner or right and y >= h - corner:
            return HTBOTTOMRIGHT
        for hit, edge in ((HTTOP, top), (HTBOTTOM, bottom), (HTLEFT, left), (HTRIGHT, right)):
            if edge:
                return hit
    if max_button is not None and max_button.contains(pos):
        return HTMAXBUTTON
    if y < band_height and draggable:
        return HTCAPTION
    return HTCLIENT


class TitleBand(QWidget):
    """The 44 px band on `base`: logo, tabs (bottom-aligned), then the job switch, search, ≡
    and, with the custom frame, the three caption buttons (top-aligned)."""

    def __init__(self, tabs: QTabBar, job_switch: QWidget, search: QWidget, menu: QWidget,
                 caption: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titleBand")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.tabs, self.job_switch, self.search, self.menu = tabs, job_switch, search, menu
        m = theme.manager()
        self._row = QHBoxLayout(self)
        self._row.setSpacing(0)
        self._row.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)  # see minimumSizeHint
        self.logo = QLabel()
        self.logo.setAccessibleName("Evrakçı")
        self._row.addSpacing(m.size("s1"))
        self._row.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignVCenter)
        # A's .logo margin-right is s2; the selected tab's left foot hangs into it.
        self._row.addSpacing(max(0, m.size("s2") - FOOT))
        self._row.addWidget(tabs, 0, Qt.AlignmentFlag.AlignBottom)
        # Owner's option b: the tabs that do not fit are one click away in a "»" menu.
        self.overflow = QToolButton()
        self.overflow.setObjectName("tabOverflow")
        self.overflow.setText("»")
        self.overflow.setProperty("kind", "icon")
        self.overflow.setAutoRaise(True)
        self.overflow.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.overflow.setToolTip("Diğer sekmeler")
        self.overflow.setAccessibleName("Diğer sekmeler")
        self.overflow.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.overflow.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0; }")
        self._overflow_menu = QMenu(self.overflow)
        self._overflow_menu.aboutToShow.connect(self._fill_overflow)
        self.overflow.setMenu(self._overflow_menu)
        self.overflow.hide()
        # Room for the selected last tab's right foot before "»" (0 while "»" is hidden).
        self._foot_gap = QSpacerItem(0, 0, QSizePolicy.Policy.Fixed,
                                     QSizePolicy.Policy.Minimum)
        self._row.addItem(self._foot_gap)
        self._row.addWidget(self.overflow, 0, Qt.AlignmentFlag.AlignVCenter)
        self._row.addStretch(1)
        tabs.currentChanged.connect(lambda _i: QTimer.singleShot(0, self, self.fit))
        tabs.currentChanged.connect(lambda _i: self.update())  # the right foot below
        right = QHBoxLayout()
        right.setSpacing(m.size("s2"))
        for widget in (job_switch, search, menu):
            right.addWidget(widget, 0, Qt.AlignmentFlag.AlignVCenter)
        self._row.addLayout(right)
        self._full_tabs = 0  # the tabs' width with every label, and with the selected
        self._narrow_tabs = 0  # label only (both measured in refresh)
        self.caption: dict[str, CaptionButton] = {}
        if caption:
            self._row.addSpacing(m.size("s1"))
            for glyph, tip in (("min", "Simge durumuna küçült"), ("max", "Ekranı kapla"),
                               ("close", "Kapat")):
                button = CaptionButton(glyph, tip)
                self.caption[glyph] = button
                self._row.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        self.refresh()

    def refresh(self) -> None:
        """Geometry per the title-band rule (height, logo, control heights) and the logo."""
        m = theme.manager()
        band = m.title_band()
        self.setFixedHeight(band.height)
        right = 0 if self.caption else m.size("s2")
        self._row.setContentsMargins(m.size("s3"), 0, right, 0)
        self.logo.setPixmap(icons.app_icon().pixmap(band.logo, band.logo))
        self.logo.setFixedSize(band.logo, band.logo)
        for button in self.caption.values():
            button.setFixedSize(band.caption_width, band.control_height)
        self.menu.setFixedSize(band.control_height, band.control_height)  # A .iconbtn.sm
        self.overflow.setFixedSize(band.control_height, band.control_height)
        self.tabs.set_label_mode(band.tab_labels)
        self._widths = self.tabs.full_widths()
        self._full_tabs = sum(self._widths)
        self._narrow_tabs = max(self._widths, default=0) + band.control_height
        self.updateGeometry()
        self.fit()

    def _rest(self) -> int:
        """The band's minimum width without the tab strip, the "»" button and its gap."""
        shown = self.tabs.sizeHint().width()
        button = self.overflow.width() if not self.overflow.isHidden() else 0
        gap = self._foot_gap.sizeHint().width()
        return super().minimumSizeHint().width() - shown - button - gap

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        """The selected tab and "»" at least, so a long tab strip never widens the window."""
        hint = super().minimumSizeHint()
        return QSize(self._rest() + self._narrow_tabs, hint.height())

    def _name_room(self) -> int:
        """What the job switch needs beyond its minimum to show the whole job name and its
        save state with words (the band's _rest counts only its minimum)."""
        switch = self.job_switch
        save = getattr(switch, "save_state", None)
        hidden = save.text_room() if save is not None else 0
        return max(0, switch.sizeHint().width() + hidden - switch.minimumSizeHint().width())

    def fit(self) -> None:
        """Every tab with its icon and name while they fit (A's strip, unchanged at 100 %);
        otherwise as many as fit, in order and always with the selected one, and the rest in
        the "»" menu (option b). Once tabs overflow, they give way to the whole job name
        first (A's 150 % render shows it in full at 1366 px). When the name still does not
        fit, the save state drops its words, and only then does the name elide (full name
        in its tooltip and accessible name)."""
        widths = getattr(self, "_widths", None) or self.tabs.full_widths()
        room = self.width() - self._rest()
        name = self._name_room()
        count = len(widths)
        if sum(widths) <= room or count == 0:
            shown = set(range(count))
            used = sum(widths)
        else:
            room -= (self.overflow.width() or theme.manager().title_band().control_height) + FOOT
            current = max(0, self.tabs.currentIndex())
            shown: set[int] = set()
            used = widths[current]
            shown.add(current)
            for index in range(count):  # the first tabs in order, around the selected one
                if index == current:
                    continue
                if used + widths[index] + name > room:
                    break
                shown.add(index)
                used += widths[index]
        self.tabs.set_shown(shown)
        overflow = len(shown) < count
        if self._foot_gap.sizeHint().width() != (FOOT if overflow else 0):
            self._foot_gap.changeSize(FOOT if overflow else 0, 0, QSizePolicy.Policy.Fixed,
                                      QSizePolicy.Policy.Minimum)
            self._row.invalidate()
        self.overflow.setVisible(overflow)
        save = getattr(self.job_switch, "save_state", None)
        if save is not None and hasattr(save, "set_compact"):
            save.set_compact(used + name > room)
        self.update()  # the right foot follows the strip

    def _fill_overflow(self) -> None:
        """The hidden tabs, with their icons and Ctrl+number keys, in strip order."""
        from evrakci.ui.chrome import TAB_ICONS, make_icon

        menu = self._overflow_menu
        menu.clear()
        for index in self.tabs.hidden_tabs():
            label = self.tabs.label(index)
            action = menu.addAction(make_icon(TAB_ICONS[self.tabs.tab_id(index)]),
                                    f"{label}\tCtrl+{index + 1}")
            action.triggered.connect(lambda _c=False, i=index: self.tabs.setCurrentIndex(i))

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.fit()

    def paintEvent(self, event) -> None:  # noqa: N802
        """The selected last tab's right foot, which hangs past the strip into the gap before
        the job switch, as A's .tab.on::after hangs into .grow (the strip keeps no room
        for it, so the job name gets A's room)."""
        super().paintEvent(event)
        tabs, current = self.tabs, self.tabs.currentIndex()
        shown = [i for i in range(tabs.count()) if tabs.isTabVisible(i)]
        if not shown or current != shown[-1] or not tabs.isVisible():
            return
        rect = QRectF(tabs.tabRect(current)).translated(tabs.pos().x(), tabs.pos().y())
        if current == shown[0]:
            rect.adjust(FOOT, 0, 0, 0)
        strip_end = tabs.geometry().right() + 1
        painter = QPainter(self)
        painter.setClipRect(QRectF(strip_end, rect.top(), FOOT + 1, rect.height()))
        paint_title_tab(painter, rect, True, False)
        painter.end()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.LayoutRequest:  # e.g. a longer "Kaydedildi …" text
            QTimer.singleShot(0, self, self.fit)
        return super().event(event)

    def is_drag_area(self, pos: QPoint) -> bool:
        """True where a press should move the window: empty band, logo, gaps between tabs."""
        child = self.childAt(pos)
        if child is None or child is self.logo:
            return True
        if child is self.tabs:
            return self.tabs.tabAt(self.tabs.mapFrom(self, pos)) < 0
        return False


class WindowsFrame(QObject):
    """Win32 side of the custom title band; `native_event` is called from nativeEvent."""

    def __init__(self, window: QMainWindow, band: TitleBand) -> None:
        super().__init__(window)
        self.window, self.band = window, band
        self._hwnd = 0
        window.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

    def attach(self) -> None:
        """After the window has a handle: restore the thick frame and the DWM shadow."""
        try:
            import ctypes
            from ctypes import wintypes

            self._hwnd = int(self.window.winId())
            user32 = ctypes.windll.user32
            gwl_style = -16
            ws = 0x00040000 | 0x00C00000 | 0x00020000 | 0x00010000  # THICKFRAME CAPTION MIN MAX
            user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
            style = user32.GetWindowLongPtrW(wintypes.HWND(self._hwnd), gwl_style)
            user32.SetWindowLongPtrW(wintypes.HWND(self._hwnd), gwl_style, style | ws)

            class MARGINS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_int), ("r", ctypes.c_int), ("t", ctypes.c_int),
                            ("b", ctypes.c_int)]

            margins = MARGINS(-1, -1, -1, -1)
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(wintypes.HWND(self._hwnd),
                                                              ctypes.byref(margins))
            user32.SetWindowPos(wintypes.HWND(self._hwnd), None, 0, 0, 0, 0,
                                0x0001 | 0x0002 | 0x0004 | 0x0020)  # NOSIZE NOMOVE NOZORDER FRAME
        except Exception:  # noqa: BLE001 - decoration must never stop the app
            self._hwnd = 0

    def set_dark(self, dark: bool) -> None:
        """DWMWA_USE_IMMERSIVE_DARK_MODE, so the frame edge follows the theme."""
        if not self._hwnd:
            return
        try:
            import ctypes
            from ctypes import wintypes

            value = ctypes.c_int(1 if dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(wintypes.HWND(self._hwnd), 20,
                                                       ctypes.byref(value), ctypes.sizeof(value))
        except Exception:  # noqa: BLE001
            pass

    def _border(self) -> int:
        try:
            import ctypes

            user32 = ctypes.windll.user32
            physical = user32.GetSystemMetrics(32) + user32.GetSystemMetrics(92)  # FRAME+PAD
        except Exception:  # noqa: BLE001
            physical = 8
        ratio = self.window.devicePixelRatioF() or 1.0
        return max(4, round(physical / ratio))

    def _max_rect(self) -> QRect | None:
        button = self.band.caption.get("max")
        if button is None or not button.isVisible():
            return None
        return QRect(button.mapTo(self.window, QPoint(0, 0)), button.size())

    def hit(self) -> int:
        pos = self.window.mapFromGlobal(QCursor.pos())
        local = self.band.mapFrom(self.window, pos)
        drag = self.band.rect().contains(local) and self.band.is_drag_area(local)
        return hit_test(self.window.size(), pos, self._border(), self.band.height(),
                        self.window.isMaximized() or self.window.isFullScreen(),
                        self._max_rect(), drag)

    def native_event(self, message: object) -> tuple[bool, int] | None:
        """Handle one MSG; None lets Qt process it."""
        try:
            from ctypes import wintypes

            msg = wintypes.MSG.from_address(int(message))
        except Exception:  # noqa: BLE001
            return None
        button = self.band.caption.get("max")
        if msg.message == WM_NCCALCSIZE and msg.wParam:
            if self.window.isMaximized():
                self._inset_maximized(msg.lParam)
            return True, 0
        if msg.message == WM_NCHITTEST:
            return True, self.hit()
        if button is not None and msg.message in (WM_NCMOUSEMOVE, WM_NCLBUTTONDOWN,
                                                  WM_NCLBUTTONUP):
            over = msg.wParam == HTMAXBUTTON
            if msg.message == WM_NCMOUSEMOVE:
                button.set_native_state(over)
                return None
            if over and msg.message == WM_NCLBUTTONDOWN:
                button.set_native_state(True, True)
                return True, 0
            if over and msg.message == WM_NCLBUTTONUP:
                button.set_native_state(False)
                button.click()
                return True, 0
        if button is not None and msg.message in (WM_MOUSEMOVE, WM_NCMOUSELEAVE):
            button.set_native_state(False)
        return None

    def _inset_maximized(self, lparam: int) -> None:
        """A maximised window hangs its frame off-screen: keep the content on the screen."""
        try:
            from ctypes import wintypes

            rect = wintypes.RECT.from_address(lparam)
            ratio = self.window.devicePixelRatioF() or 1.0
            inset = round(self._border() * ratio)
            rect.left += inset
            rect.top += inset
            rect.right -= inset
            rect.bottom -= inset
        except Exception:  # noqa: BLE001
            pass
