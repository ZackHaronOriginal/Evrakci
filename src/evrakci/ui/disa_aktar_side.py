"""The Dışa Aktar side ("Ayarlar" panel, A's 368 px column of Settings-style cards): target
folder, file-name pattern, options, and the pinned primary action.

At large text the cards scroll in their own area above the pinned action, as the 150 % renders do.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import icons, theme
from evrakci.ui.card_scroll import CardScroll
from evrakci.ui.chrome import card, group_label, make_icon
from evrakci.ui.disa_aktar_parts import HintLine, PartsButton, scale

SIDE_W = 368  # A: the aside column at 100 % text (440 at 150 %)


def side_width() -> int:
    return SIDE_W if scale() < 1.4 else 440


def mark_invalid(widget: QLineEdit, invalid: bool) -> None:
    """A's `.fld.err`: a 2 px danger bottom edge (the focus rule shows the accent edge)."""
    widget.setProperty("invalid", invalid)
    theme.follow(widget, lambda: widget.setStyleSheet(
        f"QLineEdit {{ border-bottom: 2px solid {theme.manager().hex('danger')}; }}"
        if widget.property("invalid") else ""), "invalid")


def _card() -> tuple[QFrame, QVBoxLayout]:
    frame = card(theme.manager().size("s4"))
    return frame, frame.layout()


_group = group_label


CHARS_LOCKED = ("Windows'un kabul etmediği karakterler dosya adlarından her zaman silinir; "
                "bu seçenek kapatılamaz.")


class SidePanel(QWidget):
    """`side` of the screen: the F9 panel."""

    pattern_committed = Signal(str)
    pattern_edited = Signal()
    choose_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        m = theme.manager()
        self.setAccessibleName("Dışa aktarma ayarları")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(m.size("s3"))

        self.lock_note = QWidget()
        lock = QHBoxLayout(self.lock_note)
        lock.setContentsMargins(m.size("s1"), 0, 0, 0)
        lock.setSpacing(m.size("s2"))
        self.lock_icon = QLabel()
        self.lock_icon.setFixedSize(14, 14)
        self.lock_text = QLabel("Yazma sürerken ayarlar değiştirilemez.")
        self.lock_text.setProperty("textRole", "secondary")
        self.lock_text.setWordWrap(True)
        lock.addWidget(self.lock_icon)
        lock.addWidget(self.lock_text, 1)
        self.lock_note.setAccessibleName("Yazma sürerken ayarlar değiştirilemez.")
        self.lock_note.hide()
        outer.addWidget(self.lock_note)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.scroll.setAccessibleName("Ayrıntılar")
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: 0; }")
        self.scroll.viewport().setAutoFillBackground(False)
        body = QWidget()
        body.setAutoFillBackground(False)
        self.body = QVBoxLayout(body)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(m.size("s3"))
        self.scroll.setWidget(body)
        outer.addWidget(self.scroll, 1)

        # Hedef klasör
        group, card = self._group_card("Hedef klasör")
        line = QHBoxLayout()
        line.setSpacing(m.size("s2"))
        self.folder = QLineEdit()
        self.folder.setPlaceholderText("Klasör seçilmedi")
        self.folder.setAccessibleName("Hedef klasör")
        self.choose_button = QPushButton()
        self.choose_button.setToolTip("Klasör seç")
        self.choose_button.setAccessibleName("Klasör seç")
        self.choose_button.clicked.connect(self.choose_clicked)
        line.addWidget(self.folder, 1)
        line.addWidget(self.choose_button)
        card.addLayout(line)
        self.folder_hint = HintLine()
        card.addWidget(self.folder_hint)
        self.body.addWidget(group)

        # Dosya adı kalıbı
        group, card = self._group_card("Dosya adı kalıbı")
        self.pattern = QLineEdit()
        self.pattern.setAccessibleName("Dosya adı kalıbı")
        self.pattern.editingFinished.connect(lambda: self.pattern_committed.emit(
            self.pattern.text()))
        self.pattern.textEdited.connect(lambda _t: self.pattern_edited.emit())
        card.addWidget(self.pattern)
        line = QHBoxLayout()
        self.variable_button = PartsButton("Değişken ekle", "braces", accessible="Değişken ekle",
                                           chevron=True)
        self.variable_menu = QMenu(self.variable_button)
        self.variable_menu.aboutToShow.connect(self._fill_variables)
        self.variable_button.clicked.connect(self._open_menu)
        self.variable_button.setToolTip("Kalıba bir değişken ekle")
        line.addWidget(self.variable_button)
        line.addStretch(1)
        card.addLayout(line)
        self.pattern_hint = HintLine()
        card.addWidget(self.pattern_hint)
        self.variables: list[str] = []
        self.body.addWidget(group)

        # Seçenekler
        group = QWidget()
        col = QVBoxLayout(group)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        label = _group("Seçenekler")
        col.addWidget(label)
        col.addSpacing(m.size("s2"))
        card_frame = QFrame()
        card_frame.setProperty("kind", "card")
        self.options = QVBoxLayout(card_frame)
        self.options.setContentsMargins(0, m.size("s1"), 0, m.size("s1"))
        self.options.setSpacing(0)
        self.layer = self._option("Metin katmanı ekle (OCR)", True)
        self.index_box = self._option("index.xlsx her zaman yazılır", True)
        self.index_box.setEnabled(False)
        # A draws this one live and checked. The core always takes the characters Windows
        # refuses out of a name, so unticking it says why it stays on (PROPOSALS E2).
        self.chars_box = self._option("Geçersiz karakterleri değiştir", True)
        self.chars_box.setToolTip(CHARS_LOCKED)
        self.chars_box.setAccessibleDescription(CHARS_LOCKED)
        self.chars_box.toggled.connect(self._chars_toggled)
        self.layer.setToolTip("Her PDF'e aranabilir metin katmanı ekler (OCR, PDF/A)")
        col.addWidget(card_frame)
        self.body.addWidget(group)
        self.body.addStretch(1)

        # The pinned action
        acts = QVBoxLayout()
        acts.setSpacing(m.size("s2"))
        self.export_button = PartsButton("Dışa aktar", "download", "Ctrl+E", primary=True,
                                         large=True)
        self.export_button.setToolTip("Dışa aktar (Ctrl+E)")
        self.again_button = PartsButton("Yeniden dışa aktar…", "refresh-cw",
                                        accessible="Yeniden dışa aktar")
        self.again_button.setToolTip("Başka bir klasöre yeniden dışa aktar")
        self.again_button.hide()
        self.note = HintLine()
        self.note.hide()
        acts.addWidget(self.export_button)
        acts.addWidget(self.again_button)
        acts.addWidget(self.note, 0, Qt.AlignmentFlag.AlignHCenter)
        outer.addLayout(acts)
        self.card_scroll = CardScroll(self.scroll, self.export_button)
        theme.follow(self, self._restyle, "side")

    def _group_card(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        m = theme.manager()
        group = QWidget()
        col = QVBoxLayout(group)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(m.size("s2"))
        col.addWidget(_group(title))
        card, inner = _card()
        col.addWidget(card)
        return group, inner

    def _option(self, text: str, checked: bool) -> QCheckBox:
        m = theme.manager()
        box = QCheckBox(text)
        box.setChecked(checked)
        box.setMinimumHeight(m.size("row-h") if scale() < 1.4 else 48)
        box.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(m.size("s4"), 0, m.size("s4"), 0)
        row.addWidget(box, 1)
        self.options.addWidget(wrap)
        return box

    def _restyle(self) -> None:
        m = theme.manager()
        self.choose_button.setIcon(make_icon("folder-open", "icon", m.size("icon-sm")))
        self.choose_button.setFixedWidth(m.size("control-h") + m.size("s2"))
        self.lock_icon.setPixmap(icons.pixmap("lock", m.hex("icon"), 14))
        self.layout().setSpacing(m.size("s3"))
        self.body.setSpacing(m.size("s3"))

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(side_width(), 400)

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return QSize(min(side_width(), 320), 200)

    # -- state ----------------------------------------------------------------------------
    def set_locked(self, locked: bool) -> None:
        """Writing: the settings cannot change (A: dimmed, with a note on top)."""
        self.lock_note.setVisible(locked)
        for widget in (self.folder, self.choose_button, self.pattern, self.variable_button,
                       self.layer):
            widget.setEnabled(not locked)
        self.index_box.setEnabled(False)
        self.chars_box.setEnabled(not locked)  # A: live (it stays on; see _chars_toggled)

    def set_variables(self, names: list[str]) -> None:
        self.variables = names
        self.variable_button.setEnabled(bool(names) and self.variable_button.isEnabled())

    def _open_menu(self) -> None:
        corner = self.variable_button.rect().bottomLeft()
        self.variable_menu.popup(self.variable_button.mapToGlobal(corner))

    def _fill_variables(self) -> None:
        self.variable_menu.clear()
        for name in self.variables:
            action = self.variable_menu.addAction(name)
            action.triggered.connect(lambda _c=False, n=name: self.insert_variable(n))
        if not self.variables:
            self.variable_menu.addAction("Değişken yok").setEnabled(False)

    def insert_variable(self, name: str) -> None:
        """Put {name} at the cursor of the pattern and keep it as the user's edit."""
        self.pattern.insert("{" + name + "}")
        self.pattern.setFocus(Qt.FocusReason.OtherFocusReason)
        self.pattern.editingFinished.emit()

    def _chars_toggled(self, on: bool) -> None:
        """"Geçersiz karakterleri değiştir" cannot be switched off: tick it again and say why
        where the pointer or focus is."""
        if on:
            return
        from PySide6.QtWidgets import QToolTip

        box = self.chars_box
        box.blockSignals(True)
        box.setChecked(True)
        box.blockSignals(False)
        QToolTip.showText(box.mapToGlobal(box.rect().bottomLeft()), CHARS_LOCKED, box)
        self.chars_note = CHARS_LOCKED
