"""The Kartotek look: colour and size tokens, and the Qt stylesheet built from them.

Every colour in the window comes from TOKENS, so the look can be made configurable later.
See DESIGN.md for what each token is for.
"""

from __future__ import annotations

TOKENS: dict[str, str] = {
    # Cabinet shell
    "shell": "#3f5a4c",
    "shell_2": "#344b3f",
    "shell_3": "#5a7566",
    "on_shell": "#ffffff",
    "on_shell_2": "#cddbd2",
    # Cards and ground
    "ground": "#e6ebe7",
    "card": "#fbfaf6",
    "paper": "#ffffff",
    "ink": "#1d2a23",
    "ink_2": "#4f5d55",
    "rule": "#c9d1cb",
    "rule_strong": "#74817a",
    "control_edge": "#7f8c84",
    # Guide cards and the index rule
    "manila": "#e9d9a6",
    "manila_edge": "#b9a66a",
    "manila_ink": "#2b2410",
    "index_red": "#c8372d",
    # Signal rider: needs a check (always with an icon and text)
    "rider": "#e8731a",
    "rider_edge": "#9c4a0b",
    "rider_ink": "#2a1400",
    "check_ink": "#8a3d00",
    "check_wash": "#fde7d3",
    "row_cur": "#f3efe0",
    # Cut types: tab position and pictogram first, colour second
    "qr": "#1f5fbf",
    "filter": "#b45200",
    "manual": "#b42318",
    "ok": "#1e6b3a",
    "focus": "#1d2a23",
    # Template variables, in order
    "v1": "#0f7b78",
    "v2": "#6b3fb3",
    "v3": "#9a4a12",
    "v4": "#a3245f",
    # Key caps inside buttons, and muted text on disabled controls
    "key_cap": "#f1f3ef",
    "key_edge": "#c3cbc5",
    "key_edge_on_shell": "#6d8778",
    "disabled_ink": "#6b776f",
    "hover": "#f4f6f3",
    "rider_on_shell": "#ffb27a",
}

VARIABLE_COLOURS = ("v1", "v2", "v3", "v4")

FONT_FAMILY = "Segoe UI"  # system font; the owner has not approved bundling another
FONT_SIZE = 15  # px; nothing in the window is smaller than SMALL
SMALL = 13


def colour(name: str) -> str:
    return TOKENS[name]


def variable_colour(index: int) -> str:
    return TOKENS[VARIABLE_COLOURS[index % len(VARIABLE_COLOURS)]]


def apply_font(app) -> None:
    """The window font: Segoe UI (falls back to the system sans), 15px, tabular figures."""
    from PySide6.QtGui import QFont

    font = QFont(FONT_FAMILY)
    font.setPixelSize(FONT_SIZE)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    try:
        font.setFeature(QFont.Tag("tnum"), 1)  # Qt 6.7+
    except (AttributeError, TypeError):
        pass
    app.setFont(font)


def palette():
    """The QPalette mapping of the tokens (DESIGN.md: Qt mapping)."""
    from PySide6.QtGui import QColor, QPalette

    t = TOKENS
    p = QPalette()
    role = QPalette.ColorRole
    for name, token in [
        (role.Window, "ground"), (role.Base, "paper"), (role.AlternateBase, "card"),
        (role.WindowText, "ink"), (role.Text, "ink"), (role.ButtonText, "ink"),
        (role.PlaceholderText, "ink_2"), (role.Button, "paper"), (role.Highlight, "row_cur"),
        (role.HighlightedText, "ink"), (role.Mid, "rule"), (role.Dark, "rule_strong"),
        (role.BrightText, "on_shell"), (role.ToolTipBase, "ink"), (role.ToolTipText, "paper"),
        (role.Link, "qr"),
    ]:
        p.setColor(name, QColor(t[token]))
    for name in (role.Text, role.WindowText, role.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, name, QColor(t["disabled_ink"]))
    return p


def stylesheet() -> str:
    from evrakci.ui.icons import icon_file

    t = TOKENS
    chevron = icon_file("chd", "ink_2", 2)
    up = icon_file("chu", "ink_2", 2.25)
    down = icon_file("chd", "ink_2", 2.25)
    tick = icon_file("check", "on_shell", 3)
    tick_off = icon_file("check", "on_shell", 3)
    return f"""
* {{ font-family: "{FONT_FAMILY}"; font-size: {FONT_SIZE}px; color: {t['ink']}; }}
QMainWindow, QWidget#page {{ background: {t['ground']}; }}
QWidget#card, QFrame#card {{ background: {t['card']}; }}
QFrame#card[edge="left"] {{ border-left: 1px solid {t['rule']}; }}
QFrame#card[edge="right"] {{ border-right: 1px solid {t['rule']}; }}

/* Shell: header, window tabs, status bar */
QWidget#header {{ background: {t['shell']}; border-bottom: 1px solid {t['shell_2']}; }}
QWidget#header QLabel {{ color: {t['on_shell_2']}; }}
QWidget#header QLabel#app-name {{ color: {t['on_shell']}; font-size: 17px; font-weight: 700; }}
QTabWidget::pane {{ border: 0; background: {t['ground']}; }}
QTabWidget::tab-bar {{ left: 12px; }}
QTabBar {{ background: {t['shell']}; qproperty-drawBase: 0; }}
QTabBar::tab {{ background: {t['shell']}; color: {t['on_shell_2']}; font-weight: 600;
    padding: 8px 16px 9px; margin-top: 6px; margin-right: 2px; border: 0;
    border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:hover:!selected {{ background: {t['shell_2']}; color: {t['on_shell']}; }}
QTabBar::tab:selected {{ background: {t['card']}; color: {t['ink']}; }}
QTabBar::tab:disabled {{ color: {t['shell_3']}; }}
QStatusBar {{ background: {t['shell']}; color: {t['on_shell']}; font-size: 14px;
    min-height: 30px; }}
QStatusBar::item {{ border: 0; }}
QStatusBar QLabel {{ color: {t['on_shell']}; font-size: 14px; }}
QStatusBar QLabel[role="keys"] {{ color: {t['on_shell_2']}; }}
QStatusBar QSizeGrip {{ width: 0; height: 0; }}

/* Bands and panels */
QFrame[role="toolbar"] {{ background: {t['card']}; border-bottom: 1px solid {t['rule']}; }}
QFrame[role="hrule"] {{ background: {t['rule']}; border: 0; }}
QFrame[role="vrule"] {{ background: {t['rule']}; border: 0; margin: 0 3px; }}
QFrame[role="index-rule"] {{ background: {t['index_red']}; border: 0; max-height: 1px;
    min-height: 1px; }}
QFrame[role="drop"] {{ background: transparent; border: 2px dashed {t['rule_strong']};
    border-radius: 6px; }}
QFrame[role="drop"][hot="true"] {{ background: {t['row_cur']}; border-color: {t['shell']}; }}
QSplitter::handle {{ background: {t['rule']}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QSplitter::handle:vertical {{ height: 1px; }}

/* Text roles */
QLabel[role="heading"], QLabel[role="page-title"] {{ font-size: 24px; font-weight: 700; }}
QLabel[role="panel-title"] {{ font-size: 20px; font-weight: 700; }}
QLabel[role="section-title"] {{ font-size: 17px; font-weight: 700; }}
QLabel[role="muted"] {{ color: {t['ink_2']}; }}
QLabel[role="meta"] {{ color: {t['ink_2']}; font-size: 14px; }}
QLabel[role="hint"] {{ color: {t['ink_2']}; font-size: 14px; }}
QLabel[role="value"] {{ font-weight: 600; }}
QLabel[role="figure"] {{ font-size: 17px; font-weight: 700; }}
QLabel[role="check"] {{ color: {t['check_ink']}; font-weight: 700; }}
QLabel[role="ok"] {{ color: {t['ok']}; font-weight: 600; }}
QLabel[role="mono"] {{ font-family: Consolas, "DejaVu Sans Mono", monospace; font-weight: 700; }}
QLabel[role="bad"] {{ font-family: Consolas, "DejaVu Sans Mono", monospace; font-weight: 700;
    background: {t['check_wash']}; color: #5a2a00; border-radius: 3px; padding: 2px 5px; }}
QLabel[role="rider"] {{ background: {t['rider']}; color: {t['rider_ink']}; font-weight: 700;
    font-size: {SMALL}px; border: 1px solid {t['rider_edge']}; border-radius: 3px;
    padding: 1px 6px; }}

/* Buttons (KeyHintButton paints icon, label and key cap over this frame) */
QPushButton {{ background: {t['paper']}; border: 1px solid {t['control_edge']};
    border-radius: 5px; padding: 6px 10px; font-weight: 600; min-height: 20px; }}
QPushButton:hover {{ background: {t['hover']}; border-color: {t['rule_strong']}; }}
QPushButton:pressed, QPushButton:checked {{ background: {t['row_cur']};
    border-color: {t['ink_2']}; }}
QPushButton:focus {{ border: 2px solid {t['focus']}; }}
QPushButton:disabled {{ background: {t['card']}; border-color: {t['rule']};
    color: {t['disabled_ink']}; }}
QPushButton[primary="true"] {{ background: {t['shell']}; border-color: {t['shell']};
    color: {t['on_shell']}; }}
QPushButton[primary="true"]:hover {{ background: {t['shell_2']}; border-color: {t['shell_2']}; }}
QPushButton[primary="true"]:checked {{ background: {t['shell_2']}; border-color: {t['ink']}; }}
QPushButton[primary="true"]:focus {{ border: 2px solid {t['ink']}; }}
QPushButton[primary="true"]:disabled {{ background: {t['shell_3']}; border-color: {t['shell_3']};
    color: {t['on_shell']}; }}

/* Fields */
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{ background: {t['paper']};
    border: 1px solid {t['rule_strong']}; border-radius: 4px; padding: 4px 8px; min-height: 24px;
    selection-background-color: {t['manila']}; selection-color: {t['manila_ink']}; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border: 2px solid {t['focus']}; padding: 3px 7px; }}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{ background: {t['card']};
    border-color: {t['rule']}; color: {t['disabled_ink']}; }}
QLineEdit[role="search"] {{ padding-left: 4px; }}
QSpinBox {{ font-weight: 700; padding-right: 20px; }}
QSpinBox::up-button, QSpinBox::down-button {{ subcontrol-origin: border; width: 18px;
    border: 0; border-left: 1px solid {t['rule']}; background: {t['card']}; }}
QSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 4px; }}
QSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 4px; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {t['row_cur']}; }}
QSpinBox::up-arrow {{ image: url("{up}"); width: 11px; height: 11px; }}
QSpinBox::down-arrow {{ image: url("{down}"); width: 11px; height: 11px; }}
QComboBox {{ padding-right: 28px; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: center right;
    width: 26px; border: 0; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{ background: {t['paper']}; border: 1px solid {t['rule_strong']};
    selection-background-color: {t['row_cur']}; selection-color: {t['ink']}; outline: 0;
    padding: 2px; }}
QComboBox QAbstractItemView::item {{ min-height: 30px; padding: 0 8px; }}
QCheckBox, QRadioButton {{ spacing: 8px; font-weight: 600; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1.5px solid {t['rule_strong']};
    border-radius: 3px; background: {t['paper']}; }}
QCheckBox::indicator:hover {{ border-color: {t['ink']}; }}
QCheckBox::indicator:checked {{ background: {t['shell']}; border-color: {t['shell']};
    image: url("{tick}"); }}
QCheckBox::indicator:disabled {{ background: {t['card']}; border-color: {t['rule']}; }}
QCheckBox::indicator:checked:disabled {{ background: {t['shell_3']}; border-color: {t['shell_3']};
    image: url("{tick_off}"); }}
QCheckBox:focus {{ color: {t['ink']}; text-decoration: underline; }}
QRadioButton::indicator {{ width: 16px; height: 16px; border: 1.5px solid {t['rule_strong']};
    border-radius: 9px; background: {t['paper']}; }}
QRadioButton::indicator:checked {{ border: 5px solid {t['shell']}; }}

/* Tables and lists */
QTableView, QTableWidget, QListView, QListWidget, QTreeView {{ background: {t['paper']};
    border: 0; gridline-color: {t['rule']}; selection-background-color: {t['row_cur']};
    selection-color: {t['ink']}; alternate-background-color: {t['card']}; outline: 0; }}
QTableView::item {{ padding: 0 8px; border-bottom: 1px solid {t['rule']}; }}
QTableView::item:selected {{ background: {t['row_cur']}; color: {t['ink']}; }}
QTableView::item:focus {{ border: 2px solid {t['focus']}; }}
QListView::item {{ padding: 8px 10px; border-bottom: 1px solid {t['rule']}; }}
QListView::item:hover {{ background: {t['hover']}; }}
QListView::item:selected {{ background: {t['row_cur']}; color: {t['ink']}; }}
QListView::item:selected:focus {{ border: 2px solid {t['focus']}; }}
QHeaderView {{ background: transparent; border: 0; }}
QHeaderView::section {{ background: {t['paper']}; color: {t['ink_2']}; font-size: {SMALL}px;
    font-weight: 700; border: 0; border-bottom: 1px solid {t['ink_2']}; padding: 6px 8px; }}
QHeaderView::section:hover {{ color: {t['ink']}; }}
QTableCornerButton::section {{ background: {t['paper']}; border: 0; }}

/* Scroll bars: thin, quiet, still easy to grab */
QScrollBar:vertical {{ background: transparent; width: 12px; margin: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {t['rule']}; border-radius: 4px; min-height: 32px;
    margin: 2px 3px; }}
QScrollBar::handle:horizontal {{ background: {t['rule']}; border-radius: 4px; min-width: 32px;
    margin: 3px 2px; }}
QScrollBar::handle:hover, QScrollBar::handle:pressed {{ background: {t['rule_strong']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* Progress */
QProgressBar {{ background: {t['paper']}; border: 1px solid {t['rule_strong']}; border-radius: 3px;
    max-height: 12px; min-height: 12px; text-align: center; color: transparent; }}
QProgressBar::chunk {{ background: {t['shell']}; border-radius: 2px; }}

/* Tooltips, menus and dialogs */
QToolTip {{ background: {t['ink']}; color: {t['paper']}; border: 0; padding: 5px 8px;
    font-size: 14px; }}
QMenu {{ background: {t['paper']}; border: 1px solid {t['rule_strong']}; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 12px; border-radius: 3px; }}
QMenu::item:selected {{ background: {t['row_cur']}; color: {t['ink']}; }}
QMessageBox, QInputDialog, QDialog {{ background: {t['card']}; }}
QMessageBox QLabel {{ font-size: 15px; }}
"""
