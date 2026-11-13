"""The app stylesheet as a template over tokens (direction A, final-a/shell.css + README §6).

Placeholders are `{{name}}`: a colour role gives its hex value, a size gives "Npx", and a few
keys give ready text (font family, icon urls). `render()` fills them; a missing name raises.
Component classes: objectName for the one-off chrome (titleBand, titleTabs, jobSwitch,
searchBox, menuButton, layer, commandBar, statusBar) and the dynamic property `kind` for
repeated ones (card, inspector-row, group-label, rider, badge, toast, infobar, ...); buttons
take `variant` (primary / secondary / subtle / link) and `size="lg"`.
"""
# ruff: noqa: E501  (stylesheet template text)
from __future__ import annotations

import re

_FIELD = re.compile(r"\{\{([a-z0-9-]+)\}\}")

BASE = """
QWidget { font-family: {{font-family}}; font-size: {{fs-body}}; color: {{text}}; }
QMainWindow, QDialog, QWidget#page { background: {{base}}; }
QToolTip { background: {{popover}}; color: {{text}}; border: 1px solid {{stroke}};
    border-radius: {{r-control}}; padding: {{s1}} {{s2}}; font-size: {{fs-caption}}; }
QMessageBox QLabel { font-size: {{fs-body}}; }
QLabel { background: transparent; }

/* High contrast (additions.css): hover = a Highlight edge, selection = Highlight fill
   (sel-bg / sel-fg / hover-edge / hover-stroke resolve to the quiet A values otherwise). */

/* ---- title band (L0): logo, tabs, job switch, search, menu, caption buttons ---- */
QWidget#titleBand { background: {{base}}; min-height: {{titlebar-h}}; max-height: {{titlebar-h}}; }
QWidget#jobSwitch { border-radius: {{r-control}}; min-height: {{tb-control-h}}; max-height: {{tb-control-h}}; }
QWidget#jobSwitch:hover { background: {{hover}}; }
QWidget#jobSwitch QLabel { font-size: {{fs-caption}}; color: {{text-2}}; }
QWidget#jobSwitch QLabel#jobName { color: {{text}}; font-weight: 600; }
QPushButton#searchBox { background: {{layer}}; color: {{text-2}}; border: 1px solid {{stroke}};
    border-radius: {{r-control}}; padding: 0 {{s3}}; text-align: left; font-size: {{fs-caption}};
    font-weight: 400; min-width: {{tb-search-w-in}}; max-width: {{tb-search-w-in}};
    min-height: {{tb-control-h-in}}; max-height: {{tb-control-h-in}}; }
QToolButton#menuButton { min-width: {{tb-control-h}}; max-width: {{tb-control-h}};
    min-height: {{tb-control-h}}; max-height: {{tb-control-h}}; }
QToolButton#menuButton::menu-indicator { image: none; width: 0; }
QToolButton[kind="caption-button"] { border-radius: 0; min-width: 46px; max-width: 46px;
    min-height: {{tb-control-h}}; max-height: {{tb-control-h}}; }
/* QTabBar#titleTabs: no ::tab rules on purpose, EvrakciStyle paints A's tabs (shape, feet,
   icon + label in 500 / 600) and sizes them per the title-band rule. */
QTabBar#titleTabs { background: transparent; qproperty-drawBase: 0; }

/* ---- tab bars of a QTabWidget (the title tabs are a standalone QTabBar#titleTabs) ---- */
QTabWidget::pane { border: 0; background: {{base}}; }
QTabWidget > QTabBar { qproperty-drawBase: 0; background: transparent; }
QTabWidget > QTabBar::tab { background: transparent; color: {{text-2}}; font-weight: 500;
    margin-right: 2px; padding: 0 {{s3}}; min-height: {{tb-tab-h}}; border: 1px solid transparent;
    border-bottom: 0; border-top-left-radius: {{r-layer}}; border-top-right-radius: {{r-layer}}; }
QTabWidget > QTabBar::tab:hover:!selected { background: {{hover}}; }
QTabWidget > QTabBar::tab:selected { background: {{layer}}; color: {{text}}; font-weight: 600;
    border-color: {{stroke}}; }
QTabWidget > QTabBar::tab:disabled { color: {{text-disabled}}; }

/* ---- L1 work layer and command bar ---- */
QFrame#layer, QWidget[kind="layer"] { background: {{layer}}; border: 1px solid {{stroke}};
    border-radius: {{r-layer}}; }
QToolBar#commandBar, QWidget#commandBar { background: {{layer}}; border: 0; spacing: 2px;
    padding: 0 {{s2}}; min-height: {{commandbar-h}}; max-height: {{commandbar-h}}; }
QToolBar#commandBar::separator { background: {{stroke}}; width: 1px; margin: {{sep-margin-v}} {{s2}}; }
QFrame[kind="separator"] { background: {{stroke}}; border: 0; min-width: 1px; max-width: 1px;
    min-height: {{sep-h}}; max-height: {{sep-h}}; margin: 0 {{s2}}; }

/* ---- icon buttons and labelled commands ---- */
QToolButton { background: transparent; color: {{text}}; border: 1px solid transparent;
    border-radius: {{r-control}}; }
QToolButton:hover { background: {{hover}}; border-color: {{hover-edge}}; }
QToolButton:pressed { background: {{pressed}}; }
QToolButton:checked { background: {{selected}}; }
QToolButton:disabled { color: {{text-disabled}}; }
QToolButton[kind="icon"], QToolBar#commandBar QToolButton, QWidget#commandBar QToolButton {
    min-width: {{icon-btn}}; min-height: {{icon-btn}}; max-height: {{icon-btn}}; padding: 0; }
QToolButton[kind="icon"][size="sm"] { min-width: {{tb-control-h}}; max-width: {{tb-control-h}};
    min-height: {{tb-control-h}}; max-height: {{tb-control-h}}; }
QToolButton[kind="command"], QToolBar#commandBar QToolButton[kind="command"] {
    padding: 0 {{s3}} 0 {{s2}}; font-weight: 500; }

/* ---- buttons: standard, primary, subtle, link ---- */
QPushButton { background: {{card}}; color: {{text}}; border: 1px solid {{stroke}};
    border-radius: {{r-control}}; padding: 0 {{s3}}; min-height: {{control-in-h}}; font-weight: 500; }
QPushButton:hover { background: {{hover}}; border-color: {{hover-stroke}}; }
QPushButton:pressed, QPushButton:checked { background: {{pressed}}; }
QPushButton:disabled { background: {{layer}}; color: {{text-disabled}}; border-color: {{stroke-soft}}; }
QPushButton[variant="primary"], QPushButton[primary="true"], QPushButton#primary {
    background: {{accent}}; color: {{text-on-accent}}; border: 1px solid {{accent}}; font-weight: 600; }
QPushButton[variant="primary"]:hover, QPushButton[primary="true"]:hover, QPushButton#primary:hover,
QPushButton[variant="primary"]:pressed, QPushButton[primary="true"]:pressed,
QPushButton[variant="primary"]:checked, QPushButton[primary="true"]:checked {
    background: {{accent-hover}}; border-color: {{accent-hover}}; }
QPushButton[variant="primary"]:disabled, QPushButton[primary="true"]:disabled,
QPushButton#primary:disabled { background: {{accent-disabled}}; border-color: {{accent-disabled}};
    color: {{on-accent-disabled}}; }
QPushButton[variant="subtle"] { background: transparent; border-color: transparent; }
QPushButton[variant="subtle"]:hover { background: {{hover}}; }
QPushButton[variant="subtle"]:pressed { background: {{pressed}}; }
QPushButton[variant="link"] { background: transparent; border-color: transparent;
    color: {{text-accent}}; font-weight: 600; }
QPushButton[variant="link"]:hover { background: {{hover}}; }
QPushButton[size="lg"] { min-height: {{lg-in-h}}; font-size: {{fs-body}}; }
QPushButton[kind="inspector-row"] { background: transparent; border: 0; text-align: left;
    padding: 0 {{s3}}; min-height: {{row-h}}; font-weight: 400; }
QPushButton[kind="inspector-row"]:hover { background: {{hover}}; }

/* ---- inputs: card fill, 3:1 bottom edge, accent edge on focus (D11 ring from the style) ---- */
QLineEdit, QAbstractSpinBox, QComboBox, QPlainTextEdit, QTextEdit {
    background: {{card}}; color: {{text}}; border: 1px solid {{stroke}}; border-bottom-color: {{edge}};
    border-radius: {{r-control}}; selection-background-color: {{accent}};
    selection-color: {{text-on-accent}}; }
QLineEdit, QAbstractSpinBox, QComboBox { padding: 0 {{s3}}; min-height: {{control-in-h}}; }
QPlainTextEdit, QTextEdit { padding: {{s1}} {{s2}}; }
QLineEdit:focus, QAbstractSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-bottom: 2px solid {{accent}}; }
QLineEdit:disabled, QAbstractSpinBox:disabled, QComboBox:disabled, QPlainTextEdit:disabled,
QTextEdit:disabled { background: {{layer}}; color: {{text-disabled}}; border-color: {{stroke-soft}}; }
QLineEdit[kind="search"] { background: {{layer}}; }
QAbstractSpinBox { padding-right: {{s6}}; }
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button { subcontrol-origin: border; width: 20px;
    border: 0; background: transparent; }
QAbstractSpinBox::up-button { subcontrol-position: top right; }
QAbstractSpinBox::down-button { subcontrol-position: bottom right; }
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover { background: {{hover}}; }
QAbstractSpinBox::up-arrow { image: url("{{icon-chevron-up}}"); width: 12px; height: 12px; }
QAbstractSpinBox::down-arrow { image: url("{{icon-chevron-down}}"); width: 12px; height: 12px; }
QComboBox { padding-right: {{s8}}; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right; width: 28px;
    border: 0; }
QComboBox::down-arrow { image: url("{{icon-chevron-down}}"); width: 16px; height: 16px; }
QComboBox QAbstractItemView { background: {{popover}}; color: {{text}}; border: 1px solid {{stroke}};
    selection-background-color: {{hover-pop}}; selection-color: {{text}}; outline: 0; padding: {{s1}}; }
QComboBox QAbstractItemView::item { min-height: {{menu-item-h}}; padding: 0 {{s3}}; }

/* ---- checkbox and radio: 20 px, 3:1 edge, accent when on ---- */
QCheckBox, QRadioButton { spacing: {{s2}}; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator { width: 18px; height: 18px; border: 1px solid {{edge}};
    background: {{card}}; }
QCheckBox::indicator { border-radius: {{r-control}}; }
QRadioButton::indicator { border-radius: 10px; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover { background: {{hover}}; }
QCheckBox::indicator:checked { background: {{accent}}; border-color: {{accent}};
    image: url("{{icon-check}}"); }
QCheckBox::indicator:indeterminate { background: {{accent}}; border-color: {{accent}};
    image: url("{{icon-minus}}"); }
QRadioButton::indicator:checked { border: 5px solid {{accent}}; background: {{text-on-accent}};
    width: 10px; height: 10px; }
QCheckBox::indicator:disabled, QRadioButton::indicator:disabled { border-color: {{stroke}};
    background: {{layer}}; }
QCheckBox::indicator:checked:disabled { background: {{accent-disabled}};
    border-color: {{accent-disabled}}; }
QCheckBox:disabled, QRadioButton:disabled { color: {{text-disabled}}; }

/* ---- tables and lists: card fill, hairline rows, selected fill ---- */
QAbstractItemView { background: {{card}}; color: {{text}}; border: 0; outline: 0;
    selection-background-color: {{sel-bg}}; selection-color: {{sel-fg}};
    alternate-background-color: {{layer}}; gridline-color: {{stroke-soft}}; }
QAbstractItemView:disabled { color: {{text-disabled}}; }
QTableView::item, QTreeView::item { padding: 0 {{s3}}; border-bottom: 1px solid {{stroke-soft}}; }
QListView::item { padding: {{s2}} {{s3}}; }
QAbstractItemView::item:hover { background: {{hover}}; }
QAbstractItemView::item:selected { background: {{sel-bg}}; color: {{sel-fg}}; }
QListView[kind="nav-list"]::item { border-radius: {{r-control}}; min-height: {{row-h}}; padding: 0 {{s3}}; }
QListView[kind="nav-list"]::item:selected { border-left: 3px solid {{accent}}; }
QHeaderView { background: {{card}}; border: 0; }
QHeaderView::section { background: {{card}}; color: {{text-2}}; font-size: {{fs-caption}};
    font-weight: 600; border: 0; border-bottom: 1px solid {{stroke}}; padding: 0 {{s3}};
    min-height: {{header-h}}; }
QHeaderView::section:hover { color: {{text}}; }
QTableCornerButton::section { background: {{card}}; border: 0; }
QScrollArea { background: transparent; border: 0; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* ---- cards, inspector, group labels ---- */
QFrame[kind="card"], QWidget[kind="card"], QFrame[kind="table-card"] { background: {{card}};
    border: 1px solid {{stroke}}; border-radius: {{r-layer}}; }
QFrame[kind="well"] { background: {{well}}; border: 0; border-radius: {{r-layer}}; }
QLabel[kind="group-label"] { color: {{text-2}}; font-size: {{fs-caption}}; font-weight: 600;
    margin: 0 0 {{s2}} {{s1}}; }
QLabel[kind="inspector-key"] { color: {{text-2}}; font-size: {{fs-caption}}; }
QLabel[kind="inspector-value"] { color: {{text}}; }
QLabel[kind="count"] { color: {{text}}; font-weight: 600; }

/* ---- text roles (D4) ---- */
QLabel[textRole="caption"] { font-size: {{fs-caption}}; }
QLabel[textRole="secondary"] { color: {{text-2}}; }
QLabel[textRole="section"] { font-size: {{fs-section}}; font-weight: 600; }
QLabel[textRole="panel"] { font-size: {{fs-panel}}; font-weight: 600; }
QLabel[textRole="page"] { font-size: {{fs-page}}; font-weight: 600; }

/* ---- status vocabulary: icon + word + colour; orange only for kontrol ---- */
QLabel[state="kontrol"] { color: {{check-text}}; font-weight: 600; }
QLabel[state="ok"] { color: {{ok}}; }
QLabel[state="orta"] { color: {{text-2}}; }
QLabel[state="bad"] { color: {{danger}}; font-weight: 600; }
QLabel[kind="rider"], QLabel[role="rider"] { background: {{rider}}; color: {{rider-ink}};
    border: {{rider-border}} solid {{rider-edge}}; border-radius: 3px; padding: 0 {{s2}} 0 6px;
    font-size: {{fs-caption}}; font-weight: 600; min-height: {{rider-in-h}}; max-height: {{rider-in-h}}; }
QLabel[kind="badge"] { background: {{accent}}; color: {{text-on-accent}}; border-radius: {{r-control}};
    padding: 0 5px; font-size: {{fs-caption}}; font-weight: 600; min-width: 10px;
    min-height: {{badge-h}}; max-height: {{badge-h}}; }

/* ---- popovers: menu, toast, InfoBar ---- */
QMenuBar { background: {{base}}; color: {{text}}; border: 0; }
QMenuBar::item { background: transparent; padding: {{s1}} {{s3}}; border-radius: {{r-control}}; }
QMenuBar::item:selected { background: {{hover}}; }
QMenuBar::item:pressed { background: {{pressed}}; }
QMenu { background: {{popover}}; color: {{text}}; border: 1px solid {{stroke}};
    border-radius: {{r-layer}}; padding: {{s1}}; }
QMenu::item { background: transparent; padding: {{menu-pad-t}} {{s6}} {{menu-pad-b}} {{s3}};
    border: 1px solid transparent; border-radius: {{r-control}}; }
QMenu::item:selected { background: {{hover-pop}}; color: {{text}}; border-color: {{hover-edge}}; }
QMenu::item:disabled { color: {{text-disabled}}; }
QMenu::separator { height: 1px; background: {{stroke-soft}}; margin: {{s1}} 0; }
QFrame[kind="toast"] { background: {{popover}}; border: 1px solid {{stroke}};
    border-radius: {{r-layer}}; min-height: {{toast-in-h}}; }
QFrame[kind="infobar"] { background: {{card}}; border: 1px solid {{stroke}}; border-radius: {{r-layer}}; }
QFrame[kind="infobar"][severity="error"] { background: {{danger-wash}}; }
QFrame[kind="infobar"][severity="kontrol"] { background: {{check-wash}}; }

/* ---- status bar (L0, Explorer style) ---- */
QStatusBar#statusBar { background: {{base}}; color: {{text-2}}; font-size: {{fs-caption}};
    min-height: {{statusbar-h}}; max-height: {{statusbar-h}}; padding: 0 {{s4}} 0 {{s6}}; }
QStatusBar#statusBar::item { border: 0; }
QStatusBar#statusBar QLabel { color: {{text-2}}; font-size: {{fs-caption}}; }
QStatusBar#statusBar QLabel[kind="count"] { color: {{text}}; font-weight: 600; }
QStatusBar QSizeGrip { width: 0; height: 0; }

/* ---- scroll bars: Windows 11 thin ---- */
QScrollBar:vertical { background: transparent; width: {{scrollbar-w}}; margin: 0; }
QScrollBar:horizontal { background: transparent; height: {{scrollbar-w}}; margin: 0; }
QScrollBar::handle:vertical { background: {{text-2}}; border-radius: 1px; min-height: 32px;
    margin: 0 3px; }
QScrollBar::handle:horizontal { background: {{text-2}}; border-radius: 1px; min-width: 32px;
    margin: 3px 0; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:vertical:pressed { margin: 0 1px;
    border-radius: 3px; background: {{text}}; }
QScrollBar::handle:horizontal:hover, QScrollBar::handle:horizontal:pressed { margin: 1px 0;
    border-radius: 3px; background: {{text}}; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; border: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ---- splitter, slider, progress ---- */
QSplitter::handle { background: transparent; }
QSplitter::handle:horizontal { width: {{s1}}; }
QSplitter::handle:vertical { height: {{s1}}; }
QSplitter::handle:hover { background: {{stroke}}; }
QSlider { background: transparent; }
QSlider::groove:horizontal { height: 4px; background: {{track}}; border-radius: 2px; }
QSlider::groove:vertical { width: 4px; background: {{track}}; border-radius: 2px; }
QSlider::sub-page:horizontal, QSlider::add-page:vertical { background: {{accent}}; border-radius: 2px; }
QSlider::add-page:horizontal, QSlider::sub-page:vertical { background: {{track}}; border-radius: 2px; }
QSlider::handle:horizontal, QSlider::handle:vertical { width: 14px; height: 14px;
    border: 1px solid {{stroke}}; border-radius: 8px; background: qradialgradient(cx:0.5, cy:0.5,
    radius:0.5, fx:0.5, fy:0.5, stop:0 {{accent}}, stop:0.5 {{accent}}, stop:0.56 {{card}},
    stop:1 {{card}}); }
QSlider::handle:horizontal { margin: -6px 0; }
QSlider::handle:vertical { margin: 0 -6px; }
QSlider::sub-page:horizontal:disabled { background: {{accent-disabled}}; }
QProgressBar { background: {{track}}; border: 0; border-radius: 2px; min-height: 4px; max-height: 4px;
    text-align: center; color: transparent; }
QProgressBar::chunk { background: {{accent}}; border-radius: 2px; }
QGroupBox { background: transparent; border: 0; margin-top: {{lh-caption}}; padding-top: {{s1}}; }
QGroupBox::title { subcontrol-origin: margin; left: {{s1}}; color: {{text-2}};
    font-size: {{fs-caption}}; font-weight: 600; }
"""

# Old Kartotek selectors still used by the screens until Phase 3 rebuilds them. Delete this
# block (and theme.LEGACY) once no screen sets these object names / roles any more.
LEGACY = """
QWidget#header { background: {{accent}}; border-bottom: 1px solid {{accent-hover}}; }
QWidget#header QLabel { color: {{text-on-accent}}; }
QWidget#header QLabel#app-name { color: {{text-on-accent}}; font-size: {{fs-section}}; font-weight: 600; }
QStatusBar { background: {{accent}}; color: {{text-on-accent}}; font-size: {{fs-caption}};
    min-height: {{statusbar-h}}; }
QStatusBar::item { border: 0; }
QStatusBar QLabel { color: {{text-on-accent}}; font-size: {{fs-caption}}; }
QWidget#card, QFrame#card { background: {{layer}}; }
QFrame#card[edge="left"] { border-left: 1px solid {{stroke}}; }
QFrame#card[edge="right"] { border-right: 1px solid {{stroke}}; }
QFrame[role="toolbar"] { background: {{layer}}; border-bottom: 1px solid {{stroke}}; }
QFrame[role="hrule"] { background: {{stroke}}; border: 0; }
QFrame[role="vrule"] { background: {{stroke}}; border: 0; margin: 0 3px; }
QFrame[role="index-rule"] { background: {{stroke}}; border: 0; max-height: 1px; min-height: 1px; }
QFrame[role="drop"] { background: transparent; border: 2px dashed {{edge}}; border-radius: {{r-layer}}; }
QFrame[role="drop"][hot="true"] { background: {{selected}}; border-color: {{accent}}; }
QLabel[role="heading"], QLabel[role="page-title"] { font-size: {{fs-page}}; font-weight: 600; }
QLabel[role="panel-title"] { font-size: {{fs-panel}}; font-weight: 600; }
QLabel[role="section-title"] { font-size: {{fs-section}}; font-weight: 600; }
QLabel[role="muted"] { color: {{text-2}}; }
QLabel[role="meta"], QLabel[role="hint"] { color: {{text-2}}; font-size: {{fs-caption}}; }
QLabel[role="value"] { font-weight: 600; }
QLabel[role="figure"] { font-size: {{fs-section}}; font-weight: 600; }
QLabel[role="check"] { color: {{check-text}}; font-weight: 600; }
QLabel[role="ok"] { color: {{ok}}; font-weight: 600; }
QLabel[role="mono"] { font-family: Consolas, "DejaVu Sans Mono", monospace; font-weight: 600; }
QLabel[role="bad"] { font-family: Consolas, "DejaVu Sans Mono", monospace; font-weight: 600;
    background: {{check-wash}}; color: {{check-text}}; border-radius: 3px; padding: 2px 5px; }
"""


def render(values: dict[str, str], legacy: bool = True) -> str:
    """The stylesheet with every `{{name}}` replaced from `values` (KeyError if one is missing)."""
    text = BASE + (LEGACY if legacy else "")
    return _FIELD.sub(lambda m: values[m.group(1)], text)


def fields() -> set[str]:
    """Every placeholder name the template uses."""
    return set(_FIELD.findall(BASE + LEGACY))
