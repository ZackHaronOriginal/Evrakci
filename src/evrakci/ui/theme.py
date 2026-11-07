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
}

VARIABLE_COLOURS = ("v1", "v2", "v3", "v4")

FONT_FAMILY = "Segoe UI"  # system font; the owner has not approved bundling another
FONT_SIZE = 15  # px; nothing in the window is smaller than SMALL
SMALL = 13


def colour(name: str) -> str:
    return TOKENS[name]


def variable_colour(index: int) -> str:
    return TOKENS[VARIABLE_COLOURS[index % len(VARIABLE_COLOURS)]]


def stylesheet() -> str:
    t = TOKENS
    return f"""
* {{ font-family: "{FONT_FAMILY}"; font-size: {FONT_SIZE}px; color: {t['ink']}; }}
QMainWindow, QWidget#page {{ background: {t['ground']}; }}
QWidget#card, QFrame#card {{ background: {t['card']}; }}
QTabWidget::pane {{ border: 0; background: {t['ground']}; }}
QTabBar {{ background: {t['shell']}; }}
QTabBar::tab {{ background: {t['shell']}; color: {t['on_shell_2']}; font-weight: 600;
    padding: 8px 16px 9px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {t['card']}; color: {t['ink']}; }}
QStatusBar {{ background: {t['shell']}; color: {t['on_shell']}; font-size: 14px; }}
QStatusBar QLabel {{ color: {t['on_shell']}; }}
QPushButton {{ background: {t['paper']}; border: 1px solid {t['control_edge']};
    border-radius: 5px; padding: 6px 10px; font-weight: 600; min-height: 22px; }}
QPushButton:hover {{ background: {t['card']}; border-color: {t['rule_strong']}; }}
QPushButton:focus {{ border: 2px solid {t['focus']}; }}
QPushButton:disabled {{ background: {t['card']}; border-color: {t['rule']}; color: #6b776f; }}
QPushButton[primary="true"] {{ background: {t['shell']}; border-color: {t['shell']};
    color: {t['on_shell']}; }}
QPushButton[primary="true"]:hover {{ background: {t['shell_2']}; }}
QLineEdit, QSpinBox, QComboBox {{ background: {t['paper']}; border: 1px solid {t['rule_strong']};
    border-radius: 4px; padding: 4px 8px; min-height: 22px; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 2px solid {t['focus']}; }}
QTableView, QListView, QTreeView {{ background: {t['card']}; border: 0;
    gridline-color: {t['rule']}; selection-background-color: {t['row_cur']};
    selection-color: {t['ink']}; alternate-background-color: {t['card']}; }}
QHeaderView::section {{ background: {t['card']}; color: {t['ink_2']}; font-size: {SMALL}px;
    font-weight: 700; border: 0; border-bottom: 1px solid {t['ink_2']}; padding: 4px 8px; }}
QLabel[role="heading"] {{ font-size: 24px; font-weight: 700; }}
QLabel[role="muted"] {{ color: {t['ink_2']}; }}
QLabel[role="rider"] {{ background: {t['rider']}; color: {t['rider_ink']}; font-weight: 700;
    font-size: {SMALL}px; border: 1px solid {t['rider_edge']}; border-radius: 3px;
    padding: 1px 6px; }}
QFrame[role="index-rule"] {{ background: {t['index_red']}; max-height: 1px; min-height: 1px; }}
QProgressBar {{ background: {t['paper']}; border: 1px solid {t['rule_strong']}; border-radius: 3px;
    height: 10px; text-align: center; }}
QProgressBar::chunk {{ background: {t['shell']}; }}
"""
