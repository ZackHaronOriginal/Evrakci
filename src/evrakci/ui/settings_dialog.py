"""The settings dialog: Görünüm, Kısayollar, Saklama, Dışa aktarma.

Every change applies at once (theme through `theme.manager()`, then saved in prefs), so there
is only Kapat, and each section has its own "Varsayılanlara dön".
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from evrakci.pipeline.settings import (
    DELETE_AFTER_EXPORT,
    KEEP,
    Settings,
    SettingsError,
    load_settings,
    save_settings,
)
from evrakci.ui import actions, theme
from evrakci.ui.prefs import DENSITIES, TEXT_SIZES, Prefs
from evrakci.ui.shortcut_sheet import ShortcutSheet

CHARACTER_KEYS = "tek_tuslu_kisayollar"
SECTIONS = ("Görünüm", "Kısayollar", "Saklama", "Dışa aktarma")
MODES = (("Sistem", "system"), ("Açık", "light"), ("Koyu", "dark"), ("Yüksek karşıtlık", "hc"))
MOTION = (("Sistem", None), ("Açık", True), ("Kapalı", False))
RETENTION = (
    (KEEP, "Süresiz"), (DELETE_AFTER_EXPORT, "Tam dışa aktarınca sil"),
    ("30", "30 gün"), ("90", "90 gün"),
)


class SettingsDialog(QDialog):
    """Changes apply live; Kapat only closes."""

    def __init__(self, prefs: Prefs, registry: actions.Registry, parent: QWidget | None = None,
                 retention_settings_path: Path | str | None = None) -> None:
        super().__init__(parent)
        self._prefs = prefs
        self._registry = registry
        self._retention_path = Path(retention_settings_path) if retention_settings_path else None
        self._sheet: ShortcutSheet | None = None
        self.setObjectName("settingsDialog")
        self.setWindowTitle("Ayarlar")
        self.setAccessibleName("Ayarlar")
        self.setMinimumSize(640, 460)
        m = theme.manager()

        root = QVBoxLayout(self)
        root.setContentsMargins(*(m.size("s6"),) * 4)
        root.setSpacing(m.size("s4"))
        body = QHBoxLayout()
        body.setSpacing(m.size("s6"))
        self.nav = QListWidget()
        self.nav.setProperty("kind", "nav-list")
        self.nav.setAccessibleName("Ayar bölümleri")
        self.nav.setFixedWidth(160)
        self.nav.addItems(SECTIONS)
        body.addWidget(self.nav)
        self.pages = QStackedWidget()
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)

        self.pages.addWidget(self._look_page())
        self.pages.addWidget(self._keys_page())
        self.pages.addWidget(self._retention_page())
        self.pages.addWidget(self._export_page())
        self.nav.setCurrentRow(0)

        bottom = QHBoxLayout()
        note = QLabel("Değişiklikler hemen uygulanır.")
        note.setProperty("textRole", "caption")
        bottom.addWidget(note, 1)
        close = QPushButton("Kapat")
        close.setObjectName("primary")
        close.setDefault(True)
        close.clicked.connect(self.close)
        bottom.addWidget(close)
        root.addLayout(bottom)

    # Building blocks
    def _page(self, title: str, reset=None) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(theme.manager().size("s4"))
        head = QLabel(title)
        head.setProperty("textRole", "panel")
        head.setAccessibleName(title)
        box.addWidget(head)
        page.reset_button = None  # type: ignore[attr-defined]
        if reset is not None:
            button = QPushButton("Varsayılanlara dön")
            button.setProperty("variant", "link")
            button.setAccessibleName(f"{title} ayarlarını varsayılanlara döndür")
            button.clicked.connect(reset)
            page.reset_button = button  # type: ignore[attr-defined]
        return page, box

    def _finish(self, page: QWidget, box: QVBoxLayout) -> QWidget:
        box.addStretch(1)
        if page.reset_button is not None:  # type: ignore[attr-defined]
            row = QHBoxLayout()
            row.addWidget(page.reset_button)  # type: ignore[attr-defined]
            row.addStretch(1)
            box.addLayout(row)
        return page

    def _choice(self, label: str, options, current) -> tuple[QWidget, dict[object, QRadioButton]]:
        """A labelled row of radio buttons; returns the row and {value: button}."""
        row = QWidget()
        box = QVBoxLayout(row)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(theme.manager().size("s2"))
        caption = QLabel(label)
        caption.setProperty("textRole", "secondary")
        box.addWidget(caption)
        line = QHBoxLayout()
        line.setSpacing(theme.manager().size("s6"))
        group = QButtonGroup(row)
        buttons: dict[object, QRadioButton] = {}
        for text, value in options:
            button = QRadioButton(text)
            button.setAccessibleName(f"{label}: {text}")
            button.setChecked(value == current)
            group.addButton(button)
            line.addWidget(button)
            buttons[value] = button
        line.addStretch(1)
        box.addLayout(line)
        row.group = group  # type: ignore[attr-defined]
        return row, buttons

    # Görünüm
    def _look_page(self) -> QWidget:
        page, box = self._page("Görünüm", self.reset_look)
        row, self.theme_buttons = self._choice("Tema", MODES, self._prefs.theme())
        box.addWidget(row)
        row, self.size_buttons = self._choice(
            "Yazı boyutu", [(f"%{n}", n) for n in TEXT_SIZES], self._prefs.text_size())
        box.addWidget(row)
        row, self.density_buttons = self._choice(
            "Yoğunluk", list(DENSITIES.items()), self._prefs.density())
        box.addWidget(row)
        row, self.motion_buttons = self._choice(
            "Hareketi azalt", MOTION, self._prefs.reduced_motion())
        box.addWidget(row)
        self.native_title = QCheckBox("Sistem başlık çubuğunu kullan")
        self.native_title.setAccessibleName("Sistem başlık çubuğunu kullan")
        self.native_title.setChecked(self._prefs.native_title_bar())
        self.native_title.toggled.connect(self._prefs.set_native_title_bar)
        note = QLabel("Windows'ta Evrakçı'nın başlık bandı yerine sistemin başlık çubuğu "
                      "kullanılır. Evrakçı yeniden açılınca uygulanır.")
        note.setProperty("textRole", "secondary")
        note.setWordWrap(True)
        box.addWidget(self.native_title)
        box.addWidget(note)
        for value, button in self.theme_buttons.items():
            button.toggled.connect(lambda on, v=value: on and self.set_theme(v))
        for value, button in self.size_buttons.items():
            button.toggled.connect(lambda on, v=value: on and self.set_text_size(v))
        for value, button in self.density_buttons.items():
            button.toggled.connect(lambda on, v=value: on and self.set_density(v))
        for value, button in self.motion_buttons.items():
            button.toggled.connect(lambda on, v=value: on and self.set_reduced_motion(v))
        return self._finish(page, box)

    def set_theme(self, mode: str) -> None:
        theme.manager().set_mode(mode)
        self._prefs.set_theme(mode)

    def set_text_size(self, percent: int) -> None:
        theme.manager().set_text_scale(percent)
        self._prefs.set_text_size(percent)

    def set_density(self, density: str) -> None:
        theme.manager().set_density(density)
        self._prefs.set_density(density)

    def set_reduced_motion(self, value: bool | None) -> None:
        theme.manager().set_reduced_motion(value)
        self._prefs.set_reduced_motion(value)

    def reset_look(self) -> None:
        """Sistem, %100, Normal, hareket sistemden, Evrakçı başlık bandı."""
        self.native_title.setChecked(False)
        for buttons, value in ((self.theme_buttons, "system"), (self.size_buttons, 100),
                               (self.density_buttons, "normal"), (self.motion_buttons, None)):
            buttons[value].setChecked(True)

    # Kısayollar
    def _keys_page(self) -> QWidget:
        page, box = self._page("Kısayollar")
        note = QLabel("Genel kısayollar. Sekmeye özel olanlar kısayol penceresinde.")
        note.setProperty("textRole", "secondary")
        note.setWordWrap(True)
        box.addWidget(note)
        self.character_keys = QCheckBox("Tek tuşlu kısayollar")
        self.character_keys.setAccessibleName("Tek tuşlu kısayollar")
        self.character_keys.setChecked(self._prefs.flag(CHARACTER_KEYS, True))
        self.character_keys.toggled.connect(self.set_character_keys)
        box.addWidget(self.character_keys)
        keys_note = QLabel("Kapalıyken K, M, R, N, U gibi tek harfli kısayollar çalışmaz; "
                           "komutlar düğmelerden, menülerden ve Ctrl+K'dan açılır. Enter, "
                           "Boşluk, Del ve oklar çalışmaya devam eder.")
        keys_note.setProperty("textRole", "secondary")
        keys_note.setWordWrap(True)
        box.addWidget(keys_note)
        self.keys_list = QListWidget()
        self.keys_list.setAccessibleName("Genel kısayollar")
        self.keys_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for row in actions.shortcut_sheet("app"):
            self.keys_list.addItem(f"{row.text}    {'  /  '.join(row.keys)}")
        box.addWidget(self.keys_list, 1)
        link = QPushButton("Tüm kısayolları göster")
        link.setProperty("variant", "link")
        link.clicked.connect(self.show_sheet)
        row = QHBoxLayout()
        row.addWidget(link)
        row.addStretch(1)
        box.addLayout(row)
        return self._finish(page, box)

    def set_character_keys(self, on: bool) -> None:
        self._prefs.set_flag(CHARACTER_KEYS, bool(on))
        self._registry.set_character_keys(bool(on))

    def show_sheet(self) -> None:
        if self._sheet is None:
            self._sheet = ShortcutSheet(self._registry, self)
        self._sheet.show_for(self._registry.context)

    # Saklama
    def _retention_page(self) -> QWidget:
        page, box = self._page("Saklama", self.reset_retention)
        form = QFormLayout()
        self.retention = QComboBox()
        self.retention.setAccessibleName("İşi sakla")
        for value, text in RETENTION:
            self.retention.addItem(text, value)
        form.addRow("İşi sakla", self.retention)
        box.addLayout(form)
        self.retention_note = QLabel()
        self.retention_note.setProperty("textRole", "secondary")
        self.retention_note.setWordWrap(True)
        box.addWidget(self.retention_note)
        self._load_retention()
        self.retention.currentIndexChanged.connect(self._save_retention)
        return self._finish(page, box)

    def _load_retention(self) -> None:
        value = KEEP
        self.retention_note.setText("Dışa aktarılan iş bu bilgisayarda ne kadar saklansın.")
        try:
            value = load_settings(self._retention_path).retention
        except SettingsError as error:
            self.retention_note.setText(f"{error}. Süresiz saklama gösteriliyor.")
        index = self.retention.findData(value)
        if index < 0:
            self.retention.addItem(f"{value} gün", value)
            index = self.retention.count() - 1
        self.retention.blockSignals(True)
        self.retention.setCurrentIndex(index)
        self.retention.blockSignals(False)

    def _save_retention(self) -> None:
        try:
            save_settings(Settings(self.retention.currentData()), self._retention_path)
        except (OSError, SettingsError) as error:
            self.retention_note.setText(f"Ayar kaydedilemedi: {error}")
            return
        self.retention_note.setText("Dışa aktarılan iş bu bilgisayarda ne kadar saklansın.")

    def reset_retention(self) -> None:
        self.retention.setCurrentIndex(self.retention.findData(KEEP))
        self._save_retention()  # saves even when it was already Süresiz

    # Dışa aktarma
    def _export_page(self) -> QWidget:
        page, box = self._page("Dışa aktarma", self.reset_export)
        label = QLabel("Varsayılan dışa aktarma klasörü")
        label.setProperty("textRole", "secondary")
        box.addWidget(label)
        row = QHBoxLayout()
        self.export_folder = QLineEdit(self._prefs.export_folder())
        self.export_folder.setReadOnly(True)
        self.export_folder.setPlaceholderText("Seçilmedi")
        self.export_folder.setAccessibleName("Varsayılan dışa aktarma klasörü")
        label.setBuddy(self.export_folder)
        row.addWidget(self.export_folder, 1)
        choose = QPushButton("Klasör seç…")
        choose.clicked.connect(self.choose_folder)
        row.addWidget(choose)
        box.addLayout(row)
        return self._finish(page, box)

    def choose_folder(self) -> None:
        start = self.export_folder.text() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Dışa aktarma klasörünü seç", start)
        if folder:
            self.set_export_folder(folder)

    def set_export_folder(self, folder: str) -> None:
        self._prefs.set_export_folder(folder)
        self.export_folder.setText(folder)

    def reset_export(self) -> None:
        self.set_export_folder("")
