"""The loading view: `ProgressCard` (the reading progress card of Yükle) and `LoadingCard`, the same
card shown alone over the tab body while `workers.run_background` does slow work.

Everything here runs on the window thread; `assert_window_thread()` makes a call from a worker
fail loudly instead of corrupting a widget (thread-safety rule 1, see `workers`).
"""

from __future__ import annotations

import shiboken6
from PySide6.QtCore import QEvent, QObject, Qt, QThread, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, motion, theme
from evrakci.ui.chrome import ElidedLabel


def assert_window_thread() -> None:
    """Raise when called from any thread but the one that runs the widgets."""
    app = QApplication.instance()
    if app is not None and QThread.currentThread() is not app.thread():
        raise RuntimeError("Widgets may only be used on the window thread")


class ProgressCard(QFrame):
    """A .progress card: what is read, the bar, and "%62, Yaklaşık 40 sn kaldı, 3,2 sayfa/sn,
    İptal ederseniz hiçbir şey değişmez." Yükle's screen reader announcements come from the
    screen (`feedback.announce`); `add_cancel_button` puts İptal et next to what it stops."""

    stop_requested = Signal()  # the card's own İptal et (Yükle)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("kind", "card")
        self.setAccessibleName("Okuma ilerlemesi")
        m = theme.manager()
        column = QVBoxLayout(self)
        column.setContentsMargins(m.size("s4"), m.size("s4"), m.size("s4"), m.size("s4"))
        column.setSpacing(m.size("s2"))
        top = QHBoxLayout()
        top.setSpacing(m.size("s3"))
        self.icon = QLabel()
        self.icon.setFixedSize(m.size("icon-md"), m.size("icon-md"))
        self.title = QLabel("")
        self.title.setFont(m.font("body-strong"))
        self.name = ElidedLabel("", min_chars=12)
        self.name.setProperty("textRole", "secondary")
        top.addWidget(self.icon)
        top.addWidget(self.title)
        top.addWidget(self.name, 1)
        self._top = top
        self.stop_button: QPushButton | None = None
        column.addLayout(top)
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setAccessibleName("Okuma ilerlemesi")
        column.addWidget(self.bar)
        sub = QHBoxLayout()
        sub.setSpacing(m.size("s4"))
        self.percent, self.eta, self.rate, self.note = (QLabel() for _ in range(4))
        for label in (self.percent, self.eta, self.rate, self.note):
            label.setProperty("textRole", "secondary")
            sub.addWidget(label)
        sub.addStretch(1)
        self.note.setText("İptal ederseniz hiçbir şey değişmez.")
        column.addLayout(sub)
        theme.bind_style(self, lambda: (
            f"QProgressBar {{ min-height: 6px; max-height: 6px; "
            f"background: {theme.manager().hex('track')}; }}"))
        theme.follow(self, self._restyle, "yukle-progress")

    def add_cancel_button(self, key: str, action_id: str) -> QPushButton:
        """A ghost "İptal et" at the right end of the first row, the same command as the bar's
        (`action_id`, its key `key`): the cancel sits by the sentence about it (F-yukle-41)."""
        button = QPushButton("İptal et")
        button.setProperty("variant", "subtle")
        button.setProperty("action_id", action_id)
        button.setAccessibleName(f"İptal et ({key})")
        button.setToolTip(f"Okumayı iptal et ({key})")
        button.clicked.connect(self.stop_requested)
        self._top.addWidget(button)
        self.stop_button = button
        self._restyle()
        return button

    def _indeterminate(self) -> None:
        """The bar while the length is not known: it runs, or stands still and empty under
        reduced motion (a looping bar is motion; the words say what happens)."""
        if motion.reduced_motion():
            self.bar.setRange(0, 1)
            self.bar.setValue(0)
        else:
            self.bar.setRange(0, 0)

    def _restyle(self) -> None:
        m = theme.manager()
        if self.stop_button is not None:
            self.stop_button.setIcon(icons.icon("circle-x", m.hex("icon")))
        self.icon.setPixmap(icons.pixmap("scan-text", m.hex("icon"), m.size("icon-md")))
        size = f"font-size: {m.size('fs-caption')}px;"
        for label in (self.percent, self.eta, self.rate, self.note, self.name):
            label.setStyleSheet(size)
        self.percent.setFont(m.font("caption-num"))

    def show_progress(self, done: int, total: int, name: str, eta: float | None,
                      rate: float | None) -> None:
        total = max(total, 1)
        self.bar.setRange(0, total)
        self.bar.setValue(min(done, total))
        self.title.setText(f"Sayfalar okunuyor: {done} / {total}")
        self.name.setText(name)
        percent = round(100 * done / total)
        self.percent.setText(f"%{percent}")
        from evrakci.ui.yukle_parts import (  # late: yukle_parts imports this module
            eta_text,
            rate_text,
        )

        self.eta.setText(eta_text(eta))
        self.rate.setText(rate_text(rate) if rate else "")
        self.rate.setVisible(bool(rate))
        self.setAccessibleDescription(f"%{percent}, {self.eta.text()}")

    def show_waiting(self, text: str, name: str) -> None:
        """Before the first page is read: an indeterminate bar."""
        self._indeterminate()
        if self.stop_button is not None:
            self.stop_button.setEnabled(True)
        self.title.setText(text)
        self.name.setText(name)
        self.percent.setText("")
        self.eta.setText("")
        self.rate.hide()


class _Scrim(QWidget):
    """The previous screen, dimmed under the loading card (paint only; the mouse goes through)."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

    def paintEvent(self, _event) -> None:  # noqa: N802
        color = QColor(theme.manager().color("layer"))
        color.setAlpha(170)
        painter = QPainter(self)
        painter.fillRect(self.rect(), color)


class LoadingCard(ProgressCard):
    """The progress card as a loading view: a title and a name, an indeterminate bar until the
    work reports counts, and "İptal et" when the work can stop. With `dim=True` it dims the
    widget it sits in (the tab body) while it shows."""

    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None, dim: bool = False) -> None:
        super().__init__(parent)
        self.setAccessibleName("Yükleme")
        self.bar.setAccessibleName("Yükleme")
        self.setMinimumWidth(420)
        self._scrim = _Scrim(parent) if dim and parent is not None else None
        self._previous_focus: QWidget | None = None
        self.cancel_button = QPushButton("İptal et")
        self.cancel_button.clicked.connect(self.cancel_requested)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(self.cancel_button)
        self.layout().addLayout(row)
        if parent is not None:
            parent.installEventFilter(self)
        self.hide()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if obj is self.parentWidget() and event.type() == QEvent.Type.Resize and self.isVisible():
            self.place()
        return False

    def place(self) -> None:
        """Centre in the parent (the tab body); the scrim covers all of it."""
        parent = self.parentWidget()
        if parent is None:
            return
        if self._scrim is not None:
            self._scrim.setGeometry(parent.rect())
            self._scrim.show()
            self._scrim.raise_()
        # the width follows the text (at 150 % the note is wider than 420 px), within the body
        wanted = max(420, self.sizeHint().width())
        self.setFixedWidth(min(wanted, max(parent.width() - 32, 200)))
        self.move(max(0, (parent.width() - self.width()) // 2),
                  max(0, (parent.height() - self.sizeHint().height()) // 2))
        self.raise_()

    def show_loading(self, title: str, name: str = "", cancellable: bool = True) -> None:
        assert_window_thread()
        self._indeterminate()
        self.title.setText(title)
        self.name.setText(name)
        for label in (self.percent, self.eta, self.rate):
            label.setText("")
        self.rate.hide()
        self.set_cancellable(cancellable)
        focus = QApplication.focusWidget()
        if focus is not None and not self.isAncestorOf(focus) and not self.isVisible():
            self._previous_focus = focus
        self.show()
        self.place()
        if cancellable:
            self.cancel_button.setFocus()

    def set_cancellable(self, cancellable: bool) -> None:
        assert_window_thread()
        self.cancel_button.setVisible(cancellable)
        self.note.setVisible(cancellable)

    def show_cancelling(self) -> None:
        assert_window_thread()
        self.title.setText("İptal ediliyor…")
        self.cancel_button.setEnabled(False)

    def show_progress(self, done: int, total: int, *_unused) -> None:  # type: ignore[override]
        assert_window_thread()
        total = max(total, 1)
        self.bar.setRange(0, total)
        self.bar.setValue(min(done, total))
        percent = round(100 * done / total)
        self.percent.setText(f"%{percent}")
        self.setAccessibleDescription(f"%{percent}")

    def close(self) -> bool:  # type: ignore[override]
        assert_window_thread()
        had_focus = self.isAncestorOf(QApplication.focusWidget())
        self.cancel_button.setEnabled(True)
        self.hide()
        if self._scrim is not None:
            self._scrim.hide()
        previous, self._previous_focus = self._previous_focus, None
        if had_focus and previous is not None and shiboken6.isValid(previous) \
                and previous.isVisible():
            previous.setFocus(Qt.FocusReason.OtherFocusReason)
        return True
