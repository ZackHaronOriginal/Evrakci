"""Yükle's inspector (final-a/yukle.html .inspector): Settings-style cards about the open job.

Head: "Açık iş" with a … menu, the page count as the one page-size title, "4 parti, 96 belge
bulundu" and one sentence on how the batches will be split. Then "Ön kontrol" (QR ayıraç,
Belge, Durum) and "Tarama profili". Pinned at the bottom: the primary "Kontrol'e geç" and the
subtle "İşi kapat"; while a batch is read the primary is disabled and a note says when it opens.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QIcon, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, icons, theme
from evrakci.ui.chrome import card, group_label, make_icon
from evrakci.ui.yukle_info import JobSummary, ScanProfile

KEY_W = 76  # A .kv .r .k width


class GapButton(QPushButton):
    """A .btn: icon and label centred with A's s2 gap, which QPushButton cannot give; the
    style still draws the box (fill, hover, focus) from the stylesheet."""

    def sizeHint(self) -> QSize:  # noqa: N802
        hint = super().sizeHint()
        return QSize(hint.width() + theme.manager().size("s1"), hint.height())

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QStylePainter(self)
        option = QStyleOptionButton()
        self.initStyleOption(option)
        text, icon = self.text(), self.icon()
        option.text, option.icon = "", QIcon()
        painter.drawControl(QStyle.ControlElement.CE_PushButton, option)
        gap = theme.manager().size("s2")
        size = self.iconSize()
        width = size.width() + gap + self.fontMetrics().horizontalAdvance(text)
        x = (self.width() - width) // 2
        mode = QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled
        icon.paint(painter, QRect(x, (self.height() - size.height()) // 2, size.width(),
                                  size.height()), Qt.AlignmentFlag.AlignCenter, mode)
        group = QPalette.ColorGroup.Active if self.isEnabled() else QPalette.ColorGroup.Disabled
        painter.setPen(self.palette().color(group, QPalette.ColorRole.ButtonText))
        painter.drawText(QRect(x + size.width() + gap, 0, self.width(), self.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)


class KvRow(QWidget):
    """A .kv .r: a 76 px caption key and a value with an optional icon; 40 px high."""

    def __init__(self, key: str) -> None:
        super().__init__()
        m = theme.manager()
        self.setMinimumHeight(m.size("row-h"))
        row = QHBoxLayout(self)
        row.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        row.setSpacing(m.size("s3"))
        self.key = QLabel(key)
        self.key.setProperty("kind", "inspector-key")
        self.key.setFixedWidth(round(KEY_W * m.size("fs-body") / 15))
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        self.value = QLabel()
        self.value.setProperty("kind", "inspector-value")
        self.value.setWordWrap(True)
        self.value.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.extra = QLabel()  # "şimdilik": quiet text after the value
        self.extra.setProperty("textRole", "secondary")
        value = QHBoxLayout()
        value.setSpacing(m.size("s2"))
        value.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)
        value.addWidget(self.value)
        value.addWidget(self.extra, 1)
        row.addWidget(self.key, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(value, 1)
        self._icon: tuple[str, str] | None = None

    def set(self, text: str, icon: str | None = None, role: str = "icon",
            state: str | None = None, extra: str = "") -> None:
        self.value.setText(text)
        self.value.setProperty("state", state)
        self.value.setFont(theme.manager().font("body-strong" if state == "kontrol"
                                                else "num" if state == "num" else "body"))
        self.value.style().unpolish(self.value)
        self.value.style().polish(self.value)
        self.extra.setText(extra)
        self.extra.setVisible(bool(extra))
        self._icon = (icon, role) if icon else None
        self.icon.setVisible(bool(icon))
        self.refresh()
        self.setAccessibleName(f"{self.key.text()}: {text}{' ' + extra if extra else ''}")

    def refresh(self) -> None:
        if self._icon is not None:
            name, role = self._icon
            self.icon.setPixmap(icons.pixmap(name, theme.manager().hex(role), 16))
        self.extra.setStyleSheet(f"font-size: {theme.manager().size('fs-caption')}px;")


class ProfileRows(QFrame):
    """The "Tarama profili" card: the profile (icon, two lines) and the link row to Rehber."""

    open_guide = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setProperty("kind", "card")
        m = theme.manager()
        column = QVBoxLayout(self)
        pad = m.size("s1")
        column.setContentsMargins(pad, pad, pad, pad)
        column.setSpacing(0)
        self.tall = QWidget()
        self.tall.setMinimumHeight(56)
        row = QHBoxLayout(self.tall)
        row.setContentsMargins(m.size("s3"), 0, m.size("s3"), 0)
        row.setSpacing(m.size("s3"))
        self.icon = QLabel()
        self.icon.setFixedSize(16, 16)
        lines = QVBoxLayout()
        lines.setSpacing(0)
        self.title = QLabel()
        self.detail = QLabel()
        self.detail.setProperty("textRole", "secondary")
        self.detail.setProperty("kind", "inspector-key")
        lines.addStretch(1)
        lines.addWidget(self.title)
        lines.addWidget(self.detail)
        lines.addStretch(1)
        row.addWidget(self.icon, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addLayout(lines, 1)
        column.addWidget(self.tall)
        self.link = QPushButton("Rehber'de tarama ayarları")
        self.link.setProperty("kind", "inspector-row")
        self.link.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.link.setMinimumHeight(m.size("row-h"))
        self.link.setAccessibleName("Rehber'de tarama ayarları")
        self.link.setToolTip("Rehber sekmesinde tarama ayarlarını aç")
        self.link.clicked.connect(self.open_guide)
        self.chevron = QLabel(self.link)
        self.chevron.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.chevron.setFixedSize(16, 16)
        column.addWidget(self.link)
        self.refresh()

    def set_profile(self, profile: ScanProfile | None) -> None:
        if profile is None:
            self.title.setText("Tarama bilgisi yok")
            self.detail.setText("Dosyalarda tarama görüntüsü bulunamadı")
        else:
            self.title.setText(profile.title)
            self.detail.setText(profile.detail)
        self.tall.setAccessibleName(f"Tarama profili: {self.title.text()}, {self.detail.text()}")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        m = theme.manager()
        self.chevron.move(self.link.width() - m.size("s3") - 16,
                          (self.link.height() - 16) // 2)

    def refresh(self) -> None:
        m = theme.manager()
        self.icon.setPixmap(icons.pixmap("scan-line", m.hex("icon"), 16))
        self.chevron.setPixmap(icons.pixmap("chevron-right", m.hex("text-2"), 16))
        self.detail.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")
        self.chevron.move(max(0, self.link.width() - m.size("s3") - 16),
                          max(0, (self.link.height() - 16) // 2))


class Inspector(QWidget):
    """The side panel (F9 hides it). Buttons emit signals; the screen does the work."""

    go = Signal()
    close_job = Signal()
    open_guide = Signal()

    def __init__(self, fill_more: Callable[[QMenu], None] | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("yukleInspector")
        self.setAccessibleName("İş ayrıntısı")
        m = theme.manager()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, m.size("s3"), m.size("s4"), m.size("s3"))
        outer.setSpacing(m.size("s3"))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        body = QWidget()
        column = QVBoxLayout(body)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(m.size("s3"))
        self.scroll.setWidget(body)

        head = QWidget()
        head_col = QVBoxLayout(head)
        head_col.setContentsMargins(m.size("s1"), m.size("s1"), m.size("s1"), 0)
        head_col.setSpacing(0)
        top = QHBoxLayout()
        self.caption = QLabel("Açık iş")
        self.caption.setProperty("textRole", "secondary")
        top.addWidget(self.caption)
        top.addStretch(1)
        self.more = QToolButton()
        self.more.setProperty("kind", "icon")
        self.more.setProperty("sizeVariant", "sm")
        self.more.setAutoRaise(True)
        self.more.setToolTip("Diğer")
        self.more.setAccessibleName("Diğer iş komutları")
        self.more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.more.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0; }")
        menu = QMenu(self.more)
        if fill_more is not None:
            menu.aboutToShow.connect(lambda: (menu.clear(), fill_more(menu)))
        self.more.setMenu(menu)
        top.addWidget(self.more)
        head_col.addLayout(top)
        self.title = QLabel("İş açılmadı")
        self.title.setProperty("textRole", "page")
        self.title.setContentsMargins(0, m.size("s1"), 0, 0)
        self.sub = QLabel("")
        self.sub.setProperty("textRole", "secondary")
        self.sub.setContentsMargins(0, 2, 0, 0)
        self.reason = QLabel("")
        self.reason.setWordWrap(True)
        self.reason.setContentsMargins(0, m.size("s3"), 0, 0)
        for widget in (self.title, self.sub, self.reason):
            head_col.addWidget(widget)
        column.addWidget(head)

        group = QWidget()
        col = QVBoxLayout(group)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(group_label("Ön kontrol"))
        counts = card()
        counts_col = QVBoxLayout(counts)
        counts_col.setContentsMargins(0, m.size("s1"), 0, m.size("s1"))
        counts_col.setSpacing(0)
        self.qr_row, self.docs_row, self.state_row = (
            KvRow("QR ayıraç"), KvRow("Belge"), KvRow("Durum"))
        for row in (self.qr_row, self.docs_row, self.state_row):
            counts_col.addWidget(row)
        col.addWidget(counts)
        column.addWidget(group)

        group = QWidget()
        col = QVBoxLayout(group)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(group_label("Tarama profili"))
        self.profile = ProfileRows()
        self.profile.open_guide.connect(self.open_guide)
        col.addWidget(self.profile)
        column.addWidget(group)
        column.addStretch(1)
        outer.addWidget(self.scroll, 1)

        foot = QVBoxLayout()
        foot.setSpacing(m.size("s1"))
        self.go_button = GapButton("Kontrol'e geç")
        self.go_button.setProperty("variant", "primary")
        self.go_button.setProperty("sizeVariant", "lg")
        self.go_button.clicked.connect(self.go)
        key = actions.key_text("Ctrl+2")
        self.go_button.setAccessibleName(f"Kontrol'e geç ({key})")
        self.go_button.setToolTip(f"Kontrol sekmesine geç ({key})")
        self.close_button = GapButton("İşi kapat")
        self.close_button.setProperty("variant", "subtle")
        self.close_button.clicked.connect(self.close_job)
        key = actions.key_text("Ctrl+W")
        self.close_button.setAccessibleName(f"İşi kapat ({key})")
        self.close_button.setToolTip(f"İşi kapat ({key})")
        self.note = QLabel("Okuma bitince açılır.")
        self.note.setProperty("textRole", "secondary")
        self.note.setProperty("kind", "inspector-key")
        self.note_icon = QLabel()
        self.note_icon.setFixedSize(16, 16)
        note_row = QHBoxLayout()
        note_row.setSpacing(m.size("s2"))
        note_row.addStretch(1)
        note_row.addWidget(self.note_icon)
        note_row.addWidget(self.note)
        note_row.addStretch(1)
        self.note_box = QWidget()
        self.note_box.setLayout(note_row)
        for widget in (self.go_button, self.close_button, self.note_box):
            foot.addWidget(widget)
        outer.addLayout(foot)
        self.reading = False
        self.set_actions(False, False)
        theme.follow(self, self.refresh)
        self.refresh()

    # -- content -------------------------------------------------------------------------
    def show_job(self, info: JobSummary, profile: ScanProfile | None) -> None:
        self.reading = False
        self.title.setText(f"{info.pages} sayfa")
        self.sub.setText(f"{info.parties} parti, {info.documents} belge bulundu")
        self.reason.setText(info.reason)
        self.reason.setVisible(bool(info.reason))
        self.qr_row.set(str(info.qr), state="num")
        self.docs_row.set(str(info.documents), state="num")
        if info.checks:
            self.state_row.set(f"{info.checks} belge", "triangle-alert", "check-text", "kontrol")
        else:
            self.state_row.set("Hazır", "circle-check", "ok", "ok")
        self.profile.set_profile(profile)
        self.set_reading(False)
        self.setAccessibleDescription(
            f"{info.name}: {info.pages} sayfa, {info.parties} parti, {info.documents} belge. "
            + (f"{info.checks} belge kontrol bekliyor." if info.checks else "Hepsi hazır."))

    def show_reading(self, pages: int, parties: int, qr_so_far: int, waiting: str,
                     profile: ScanProfile | None = None) -> None:
        """While batches are read: counts so far, "…" where the answer is not known yet."""
        self.reading = True
        self.title.setText(f"{pages} sayfa")
        self.sub.setText(f"{parties} parti, okuma sürüyor")
        self.reason.setText(waiting)
        self.reason.setVisible(True)
        self.qr_row.set(str(qr_so_far), state="num", extra="şimdilik")
        self.docs_row.set("…", state="num")
        self.state_row.set("Okunuyor", "loader-circle", "text-2", "orta")
        self.profile.set_profile(profile)
        self.set_reading(True)

    def set_reading(self, reading: bool) -> None:
        """Disable the primary and swap "İşi kapat" for the note while a batch is read."""
        self.close_button.setVisible(not reading)
        self.note_box.setVisible(reading)
        self.go_button.setEnabled(self._can_go and not reading)

    def set_actions(self, can_go: bool, can_close: bool) -> None:
        self._can_go = can_go
        self.go_button.setEnabled(can_go and not self.reading)
        self.close_button.setEnabled(can_close and not self.reading)

    def refresh(self) -> None:
        m = theme.manager()
        self.more.setIcon(make_icon("ellipsis"))
        self.go_button.setIcon(make_icon("arrow-right-to-line", "text-on-accent"))
        self.close_button.setIcon(make_icon("x", "icon"))
        self.note_icon.setPixmap(icons.pixmap("info", m.hex("icon"), 16))
        self.note.setStyleSheet(f"font-size: {m.size('fs-caption')}px;")
        for row in (self.qr_row, self.docs_row, self.state_row):
            row.refresh()
        self.profile.refresh()
        self.setMinimumWidth(m.size("inspector-w") // 2)
