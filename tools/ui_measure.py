"""Measures the real window against docs/ui-goal/rules.json (offscreen, no screen needed).

    QT_QPA_PLATFORM=offscreen python tools/ui_measure.py --out report.tsv
    ... --tab kontrol --theme dark --text 150 --size 1366x768 --fails-only
    ... --enforce      # exit 1 when a rule with "enforced": true fails (known fails tolerated)

For 6 tabs x {light, dark, hc} x {1366x768, 1920x1080} x text {100, 150} it builds the demo window
like tools/screenshots.py does (fresh in each theme and text size, custom title band forced),
and for every visible widget records: class and object name, geometry, content margins, layout
margins and spacing, gap to the nearest sibling, font (family, px size, weight), text colour,
background colour and their contrast ratio, hit area, focus ring (really focused by Tab, then
read back from the overlay in evrakci.ui.style), tooltip, accessible name and role, enabled
state. Each rule in rules.json with a
"tool:<check>" measure is one function in CHECKS; a rule whose JSON has "rows_under" shares the
check of another rule and writes no rows of its own. One TSV row per widget per rule:
tab, theme, size, text, widget path, class, rule id, value, limit, result, severity. Rows are
sorted, so two runs of one build give identical files. Rules and limits come from rules.json
only (its "params"); this file holds no number of its own.

Contrast method (known limits). Widgets paint through the stylesheet, the palette or a custom
paintEvent, so the colours are read from the rendered window, not from the style sheet:
the widget's visible rectangle (inset 4 px, 2 px for small ones, to leave borders and rounded
corners out) is cut from one window.grab(); the most common pixel colour is the background and
the pixel colour with the highest contrast ratio against it (seen at least twice) is the text.
Anti-aliased text still has full-coverage pixels, so this finds the true text colour for glyphs
of 11 px and up. Limits: a widget that draws an icon, border or image in a stronger colour than
its text reads that colour as "text"; text over a photo (thumbnail grids, scan previews) is not
measured ("skip"); text with fewer than THIN_INK (60) ink pixels (one glyph, thin ".pdf", narrow
column: B-104) takes the declared colour (palette, QSS colour, cell foreground) against the sampled
background, and with none and no real ink pixel the row is "skip", never a pass;
disabled widgets are exempt (WCAG). A QTableView is sampled per cell (its
worst cell per column is one row, "<path>[col N]", the icon part of a cell left out); headers
as one box; the icon of a button is cut from its box. Role: "secondary" for placeholder text
(by the widget) or when the sampled text colour is within 12 RGB steps of the theme's text-2
token (D10: secondary 4.5:1), otherwise "body" (body and table text, 7:1).

Other methods. Hit area is the widget's own size. "Controls in rows" are clickable widgets
inside an item view or inside a widget whose class name ends in "Row". Neighbour gap is the
pixel gap to the nearest visible sibling on the right or below that overlaps it. The ring check
focuses the widget with the Tab reason and reads EvrakciStyle's overlay (target, visible, ring
width); item views get their ring per item from the style (PE_FrameFocusRect), so they are
reported "skip". Radii are read from "border-radius" in the application's and the widgets' own
style sheets, and a radius of about half the box (indicator, scroll bar handle, the widget
itself) is a circle or pill, not a corner; painted radii are "manual". Margins and spacing are
judged only where the layout applies them: not a QStackedLayout / QStackedWidget (the page gets
the full size), not a QMainWindow, and spacing only with two or more visible items; the spacing
is the real gap between visible neighbours of a box layout (or the declared one when smaller).
A's values (2 px and 6 px gaps, 3 px radius, in rules.json params "a_values") are exceptions
named there. DEC-MOT-01 is a unit test (animations are deleted when they stop, so a window
never holds one). The focus probe puts every focus policy back, so a result does not depend on
the order of sizes or tabs. Window caption buttons and a QLineEdit's clear action are exempt
from AUD-KBD-01 ("skip"). Button height (AUD-HIT-02) uses the D5 density value, not the text
size step. The truncation check also counts cut table cells (screenshots._cells).
Each state waits 300 ms (longer than the longest D7 duration) and then until it is settled
(B-104): no pool worker runs and two grabs 40 ms apart are the same picture. A contrast row
whose text colour is hardly distinct from its background (below 1.5:1, what an unpainted or
still-loading widget measures) is measured again after a longer wait, up to twice; one that
stays that low is a real failure. Known fails (known-fails.tsv) name rule, widget and, for a
case seen on one machine only, theme, size and text scale.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import screenshots  # noqa: E402
import shiboken6  # noqa: E402
from PySide6.QtCore import (  # noqa: E402
    QPoint,
    QRect,
    Qt,
    QThreadPool,
)
from PySide6.QtGui import QAccessible, QBrush, QColor, QFontInfo, QImage  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractButton,
    QAbstractItemView,
    QAbstractScrollArea,
    QAbstractSpinBox,
    QApplication,
    QBoxLayout,
    QCheckBox,
    QComboBox,
    QFrame,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QRadioButton,
    QScrollBar,
    QSlider,
    QStackedLayout,
    QStackedWidget,
    QStyledItemDelegate,
    QTabBar,
    QTableView,
    QToolButton,
    QWidget,
)

from evrakci.app import configure_application  # noqa: E402
from evrakci.ui import style, theme  # noqa: E402
from evrakci.ui.tokens import generated as tokens  # noqa: E402

RULES_PATH = ROOT / "docs/ui-goal/rules.json"
KNOWN_FAILS_PATH = ROOT / "docs/ui-goal/baseline/known-fails.tsv"
COLUMNS = ("tab", "theme", "size", "text", "widget", "class", "rule", "value", "limit", "result",
           "severity")
SETTLE_MS = 300
IDLE_MS = 3000  # the longest wait for a settled picture
Row = tuple[str, ...]
Res = tuple[str, str, str]  # value, limit, "pass" | "fail" | "skip"


# -- rules --------------------------------------------------------------------------------

def load_rules(path: Path = RULES_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["rules"]


def measured_rules(rules: list[dict]) -> dict[str, dict]:
    """check name -> the rule that owns its rows ("tool:<check>" without "rows_under")."""
    owners: dict[str, dict] = {}
    for rule in rules:
        measure = rule.get("measure", "")
        if measure.startswith("tool:") and not rule.get("rows_under"):
            owners[measure[5:]] = rule
    return owners


# Exemptions (decisions.md, "Window-scroll rule (Q-16)", owner 2026-11-26): a page that needs to
# scroll as a whole is an exception to the window-scroll rule. The Rehber reader and the Şablonlar
# canvas (PageCanvas, painted as one surface, its inner widget has no name or ring of its own).
WINDOW_SCROLL_EXEMPT = {"Reader": "Rehber reader scrolls as a whole",
                        "PageCanvas": "Şablonlar canvas scrolls as a whole"}
CANVAS_EXEMPT_RULES = ("AUD-A11Y-01", "DEC-FOC-01")


# Owner decision Q-32 (2026-11-26): the status-bar zoom −/+ stay 24 px (Fluent 2 "small").
OWNER_EXEMPT = {("AUD-HIT-02", "statusBar/ZoomSlider/QToolButton[0]"),
                ("AUD-HIT-02", "statusBar/ZoomSlider/QToolButton[1]")}


def exempt_row(rule_id: str, path: str) -> bool:
    """True for a row the tool does not judge: the Şablonlar canvas surface (see above) and the
    owner's written exceptions (OWNER_EXEMPT)."""
    if (rule_id, path) in OWNER_EXEMPT:
        return True
    return rule_id in CANVAS_EXEMPT_RULES and "/PageCanvas/" in f"{path}/"


def load_known_fails(path: Path = KNOWN_FAILS_PATH) -> set[tuple[str, ...]]:
    """What --enforce tolerates. File columns: rule, widget, reason (every case of that widget)
    or rule, widget, theme, size, text, reason (only that case, e.g. "light 1366x768 100", so a
    regression of the widget at another theme, size or text scale still fails). Keys are
    (rule, widget) or (rule, widget, theme, size, text)."""
    if not path.exists():
        return set()
    known: set[tuple[str, ...]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or line.startswith("rule\t"):
            continue
        cols = line.split("\t")
        if len(cols) >= 6:
            known.add(tuple(cols[:5]))
        elif len(cols) >= 2:
            known.add((cols[0], cols[1]))
    return known


def known_fail_matches(key: tuple[str, ...], row: Row) -> bool:
    """True when a known-fail key covers the row (rule, widget [, theme, size, text])."""
    if key[:2] != (row[6], row[4]):
        return False
    return len(key) < 5 or key[2:5] == (row[1], row[2], row[3])


# -- colours ------------------------------------------------------------------------------

@lru_cache(maxsize=4096)
def _luminance(rgb: int) -> float:
    lin = []
    for shift in (16, 8, 0):
        c = ((rgb >> shift) & 255) / 255
        lin.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: int, b: int) -> float:
    """WCAG contrast ratio of two 0xRRGGBB colours."""
    hi, lo = sorted((_luminance(a & 0xFFFFFF), _luminance(b & 0xFFFFFF)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _hex(rgb: int) -> str:
    return f"#{rgb & 0xFFFFFF:06x}"


def _near(a: int, b: int, steps: int = 12) -> bool:
    return all(abs(((a >> s) & 255) - ((b >> s) & 255)) <= steps for s in (16, 8, 0))


# -- context and per-widget record ---------------------------------------------------------

@dataclass
class Ctx:
    root: QWidget
    theme: str
    text: int
    size: tuple[int, int]
    image: QImage
    words: memoryview
    stride: int
    params: dict[str, dict] = field(default_factory=dict)
    scale: float = 1.0
    window_checks: bool = True

    def param(self, check: str) -> dict:
        return self.params.get(check, {})


def px_round(value: float) -> int:
    return int(value + 0.5)


def visible_rect(w: QWidget, root: QWidget) -> QRect:
    """The part of `w` that shows: clipped by every ancestor and by the window."""
    rect = QRect(w.mapTo(root, QPoint(0, 0)), w.size())
    parent = w.parentWidget()
    while parent is not None and parent is not root:
        rect = rect.intersected(QRect(parent.mapTo(root, QPoint(0, 0)), parent.size()))
        parent = parent.parentWidget()
    return rect.intersected(root.rect())


def widget_path(w: QWidget, root: QWidget) -> str:
    parts = []
    while w is not root and w.parentWidget() is not None:
        parent = w.parentWidget()
        key = w.objectName() or type(w).__name__
        same = [c for c in parent.children()
                if isinstance(c, QWidget) and (c.objectName() or type(c).__name__) == key]
        parts.append(f"{key}[{same.index(w)}]" if len(same) > 1 else key)
        w = parent
    return "/".join(reversed(parts)) or type(root).__name__


def text_of(w: QWidget) -> str:
    """The text a widget draws ("" when none or not measurable)."""
    if isinstance(w, QTableView):
        model = w.model()
        return "(cells)" if model is not None and model.rowCount() else ""
    if isinstance(w, QHeaderView):
        return "(header)"
    if isinstance(w, QAbstractItemView):
        return ""
    if isinstance(w, QLineEdit):
        return w.text() or w.placeholderText()
    if isinstance(w, QComboBox):
        return w.currentText()
    if isinstance(w, QAbstractSpinBox):
        edit = w.lineEdit()
        return edit.text() if edit is not None else ""
    if isinstance(w, QTabBar):
        return " ".join(w.tabText(i) for i in range(w.count()))
    if isinstance(w, (QLabel, QAbstractButton)):
        return w.text().replace("&", "")
    getter = getattr(w, "text", None)
    if callable(getter):
        try:
            value = getter()
        except TypeError:
            return ""
        return value if isinstance(value, str) else ""
    return ""


INK_RATIO = 1.5   # a pixel this far from the background in contrast counts as glyph ink
THIN_INK = 60     # fewer ink pixels than this: the picture alone cannot name the text colour
MIN_INK = 3       # fewer than this and the picture has no text at all


def sample_colours(ctx: Ctx, rect: QRect, declared: int | None = None) -> tuple[int, int] | None:
    """(background, text) as 0xRRGGBB from the rendered window, see the module docstring.

    B-104: a one-glyph label ("3"), a narrow numeric column or thin glyphs (".pdf") have only a
    handful of ink pixels, mostly anti-aliased and each colour seen once, so the picture alone
    names a background shade as the text (1:1). With fewer than THIN_INK ink pixels the text
    colour is the declared one (palette, QSS colour, model foreground) when known; without one,
    and with no real ink pixel, there is no answer (None: the row is skipped, never passed)."""
    inset = 4 if min(rect.width(), rect.height()) >= 20 else 2
    box = rect.adjusted(inset, inset, -inset, -inset)
    if box.width() < 2 or box.height() < 2:
        box = rect
    box = box.intersected(ctx.image.rect())
    if box.isEmpty():
        return None
    hist: Counter[int] = Counter()
    for y in range(box.top(), box.bottom() + 1):
        base = y * ctx.stride
        hist.update(ctx.words[base + box.left(): base + box.right() + 1])
    if len(hist) < 2:
        return None if declared is None else (_dominant(hist), declared & 0xFFFFFF)
    background = _dominant(hist)
    ink, strongest, strongest_ratio = 0, None, INK_RATIO
    best, best_ratio = None, 1.0
    for colour, n in hist.items():
        colour &= 0xFFFFFF
        ratio = contrast(colour, background)
        if ratio >= INK_RATIO:
            ink += n
            if ratio > strongest_ratio:
                strongest, strongest_ratio = colour, ratio
        if n >= 2 and ratio > best_ratio:
            best, best_ratio = colour, ratio
    if ink >= THIN_INK and best is not None and best_ratio >= INK_RATIO:
        if declared is not None and _blend_of(best, declared & 0xFFFFFF, background):
            # thin glyphs: the most frequent ink is the declared colour mixed with the
            # background by anti-aliasing (CI fonts draw ".pdf" lighter, B-104), not a new colour
            return background, declared & 0xFFFFFF
        return background, best
    if declared is not None:
        return background, declared & 0xFFFFFF
    if ink >= MIN_INK and strongest is not None:
        return background, strongest
    return None


def _blend_of(colour: int, declared: int, background: int, slack: float = 0.12) -> bool:
    """True when `colour` lies between `background` and `declared` (an anti-aliased mix of the
    declared text colour): every channel moved the same fraction t (0 < t <= 1) of the way."""
    fractions = []
    for shift in (16, 8, 0):
        c, d, b = (colour >> shift) & 255, (declared >> shift) & 255, (background >> shift) & 255
        if abs(d - b) < 16:
            if abs(c - b) > 16:
                return False
            continue
        fractions.append((c - b) / (d - b))
    if not fractions:
        return False
    return all(0 < t <= 1 + slack for t in fractions) and max(fractions) - min(fractions) <= slack


def _dominant(hist: Counter[int]) -> int:
    return max(hist.items(), key=lambda kv: (kv[1], -kv[0]))[0] & 0xFFFFFF


def declared_colour(w: QWidget) -> int:
    """The text colour the widget declares: its palette (a style sheet "color" is applied to the
    palette when the widget is polished)."""
    w.ensurePolished()
    return w.palette().color(w.foregroundRole()).rgb() & 0xFFFFFF


def gap_to_neighbours(w: QWidget, root: QWidget) -> tuple[int | None, int | None]:
    """Pixel gap to the nearest visible sibling on the right and below (None when none)."""
    parent = w.parentWidget()
    if parent is None:
        return None, None
    mine = QWidget.geometry(w)
    right = below = None
    for other in parent.children():
        if other is w or not isinstance(other, QWidget) or not other.isVisible():
            continue
        box = QWidget.geometry(other)
        if (box.left() >= mine.right() and box.top() <= mine.bottom()
                and box.bottom() >= mine.top()):
            gap = box.left() - mine.right() - 1
            right = gap if right is None else min(right, gap)
        if (box.top() >= mine.bottom() and box.left() <= mine.right()
                and box.right() >= mine.left()):
            gap = box.top() - mine.bottom() - 1
            below = gap if below is None else min(below, gap)
    return right, below


def layout_applies(w: QWidget, layout: QLayout | None) -> bool:
    """False for layouts whose margins and spacing are not applied geometrically: a stacked
    layout puts its page at the full size, and a QMainWindow's layout only holds the bars."""
    return (layout is not None and not isinstance(layout, QStackedLayout)
            and not isinstance(w, (QStackedWidget, QMainWindow)))


def visible_items(layout: QLayout) -> int:
    """Widgets that show and nested layouts (stretches and spacers do not count)."""
    count = 0
    for n in range(layout.count()):
        item = layout.itemAt(n)
        if item.widget() is not None:
            count += 1 if item.widget().isVisible() else 0
        elif item.layout() is not None:
            count += 1
    return count


def real_gap(layout: QLayout) -> int | None:
    """The smallest pixel gap between two neighbouring visible items of a box layout (None
    for other layouts, or when a spacer or stretch sits between every pair)."""
    if not isinstance(layout, QBoxLayout):
        return None
    horizontal = layout.direction() in (QBoxLayout.Direction.LeftToRight,
                                        QBoxLayout.Direction.RightToLeft)
    gaps: list[int] = []
    prev = None
    for n in range(layout.count()):
        item = layout.itemAt(n)
        if item.spacerItem() is not None:
            prev = None
            continue
        if item.widget() is not None and not item.widget().isVisible():
            continue
        box = item.geometry()
        if prev is not None:
            if horizontal:
                gaps.append(max(box.left() - prev.right() - 1, prev.left() - box.right() - 1))
            else:
                gaps.append(max(box.top() - prev.bottom() - 1, prev.top() - box.bottom() - 1))
        prev = box
    return min(gaps) if gaps else None


def icon_width(w: QAbstractButton) -> int:
    return 0 if w.icon().isNull() else w.iconSize().width() + 6


def accessible_role(w: QWidget) -> str:
    try:
        iface = QAccessible.queryAccessibleInterface(w)
        return iface.role().name if iface is not None else ""
    except (RuntimeError, AttributeError):
        return ""


def in_row(w: QWidget) -> bool:
    parent = w.parentWidget()
    while parent is not None:
        if type(parent).__name__.endswith("Row"):
            return True
        if isinstance(parent, QAbstractScrollArea) and isinstance(parent, QAbstractItemView):
            return True
        parent = parent.parentWidget()
    return False


def is_clickable(w: QWidget) -> bool:
    if isinstance(w, QLineEdit):
        return not isinstance(w.parentWidget(), (QAbstractSpinBox, QComboBox))
    return isinstance(w, (QAbstractButton, QComboBox, QAbstractSpinBox, QSlider, QTabBar))


def cell_colour(view: QTableView, index) -> int | None:
    """The colour a cell declares: its model foreground only. The view's palette is not a
    declaration, delegates paint their own colours (muted columns, status chips)."""
    brush = index.data(Qt.ItemDataRole.ForegroundRole)
    if isinstance(brush, QBrush):
        brush = brush.color()
    if isinstance(brush, QColor) and brush.isValid() and brush.alpha() == 255:
        return brush.rgb() & 0xFFFFFF
    return None


def text_rect(view: QTableView, index, rect: QRect) -> QRect:
    """The part of a cell's rect the text occupies (B-104): a narrow column or a short value
    leaves most of the cell empty, and a column measured at another width must still hit the
    glyphs, so the box follows the text's width and the cell's alignment."""
    text = index.data()
    delegate = view.itemDelegateForColumn(index.column()) or view.itemDelegate()
    if type(delegate) is not QStyledItemDelegate or not isinstance(text, str) or not text:
        return rect  # a delegate paints its own layout (bars, chips, notes): the whole cell
    width = min(rect.width(), view.fontMetrics().horizontalAdvance(text) + 8)
    align = index.data(Qt.ItemDataRole.TextAlignmentRole)
    flags = int(align) if isinstance(align, (int, Qt.AlignmentFlag)) else 0
    if flags & int(Qt.AlignmentFlag.AlignRight.value):
        return QRect(rect.right() - width + 1, rect.top(), width, rect.height())
    if flags & int(Qt.AlignmentFlag.AlignHCenter.value):
        return QRect(rect.left() + (rect.width() - width) // 2, rect.top(), width, rect.height())
    return QRect(rect.left(), rect.top(), width, rect.height())


def sample_cells(ctx: Ctx, view: QTableView,
                 limit: int = 30) -> list[tuple[int, int, int, float | None]]:
    """The worst cell of each visible column as (column, background, text, contrast), read from
    the rendered window; the icon part of a cell (decoration) is left out of its box."""
    model = view.model()
    port = view.viewport()
    if model is None:
        return []
    origin = port.mapTo(ctx.root, QPoint(0, 0))
    clip = visible_rect(port, ctx.root)
    header = view.horizontalHeader()
    icon = view.iconSize().width() if view.iconSize().width() > 0 else 16
    first = max(0, view.rowAt(0))
    last = view.rowAt(port.height() - 1)
    last = model.rowCount() - 1 if last < 0 else last
    worst: dict[int, tuple[int, int, int, float | None]] = {}
    for row in range(first, min(last, first + limit - 1) + 1):
        for column in range(model.columnCount()):
            if view.isColumnHidden(column) or header.sectionSize(column) <= 0:
                continue
            index = model.index(row, column)
            if not isinstance(model.data(index), str) or not model.data(index):
                continue
            rect = view.visualRect(index).translated(origin)
            if model.data(index, Qt.ItemDataRole.DecorationRole) is not None:
                rect = rect.adjusted(icon + 6, 0, 0, 0)
            rect = text_rect(view, index, rect).intersected(clip)
            sampled = sample_colours(ctx, rect, cell_colour(view, index))
            if sampled is None:
                # no answer is a "skip" row, never a missing one and never a pass (B-104)
                worst.setdefault(column, (column, 0, 0, None))
                continue
            ratio = contrast(*sampled[::-1])
            if column not in worst or worst[column][3] is None or ratio < worst[column][3]:
                worst[column] = (column, sampled[0], sampled[1], ratio)
    return [worst[c] for c in sorted(worst)]


def describe(w: QWidget, ctx: Ctx) -> dict:
    """Everything the tool records about one widget."""
    root = ctx.root
    font = w.font()
    info = QFontInfo(font)
    text = text_of(w)
    rect = visible_rect(w, root)
    if isinstance(w, QAbstractScrollArea):
        sample = QRect(w.viewport().mapTo(root, QPoint(0, 0)), w.viewport().size())
        sample = sample.intersected(rect)
    else:
        sample = rect
    if isinstance(w, QAbstractButton):
        sample = sample.adjusted(icon_width(w), 0, 0, 0)  # the icon is not text
    colours = None
    cells: list[tuple[int, int, int, float | None]] = []
    if isinstance(w, QTableView) and text and w.isEnabled():
        cells = sample_cells(ctx, w)
    elif text and w.isEnabled():
        colours = sample_colours(ctx, sample, declared_colour(w))
    layout = w.layout()
    applies = layout_applies(w, layout)
    margins = w.contentsMargins()
    gap_x, gap_y = gap_to_neighbours(w, root)
    icon_only = (isinstance(w, QAbstractButton) and not w.icon().isNull() and not text)
    weight = font.weight()
    return {
        "cls": type(w).__name__, "name": w.objectName(), "enabled": w.isEnabled(),
        "geometry": (w.mapTo(root, QPoint(0, 0)).x(), w.mapTo(root, QPoint(0, 0)).y(),
                     w.width(), w.height()),
        "margins": (margins.left(), margins.top(), margins.right(), margins.bottom()),
        "layout_margins": None if not applies else (
            layout.contentsMargins().left(), layout.contentsMargins().top(),
            layout.contentsMargins().right(), layout.contentsMargins().bottom()),
        "layout_spacing": None if not applies else layout.spacing(),
        "layout_items": 0 if not applies else visible_items(layout),
        "layout_gap": None if not applies else real_gap(layout),
        "is_frame": isinstance(w, QFrame),
        "gap": (gap_x, gap_y),
        "family": font.family(), "resolved_family": info.family(),
        "px": info.pixelSize(), "weight": int(getattr(weight, "value", weight)),
        "text": text, "icon_only": icon_only,
        "placeholder": isinstance(w, QLineEdit) and not w.text() and bool(w.placeholderText()),
        "background": None if colours is None else colours[0],
        "foreground": None if colours is None else colours[1],
        "contrast": None if colours is None else contrast(colours[0], colours[1]),
        "cells": cells,
        "hit": (w.width(), w.height()),
        "tooltip": w.toolTip(), "accessible_name": w.accessibleName(),
        "role": accessible_role(w), "focus_policy": w.focusPolicy(),
        "kind": w.property("kind"), "bar_action": (isinstance(w, QToolButton)
                                                    and isinstance(w.parentWidget(), QLineEdit)),
        "stylesheet": w.styleSheet(),
        "ring": None,  # filled by probe_focus
    }


# -- focus probe --------------------------------------------------------------------------

def probe_focus(app: QApplication, widgets: list[QWidget], records: dict[QWidget, dict],
                ctx: Ctx) -> None:
    """Focus each focusable widget with the Tab reason and read the ring back: a (visible,
    ring px) pair, "view" for item views (ring per item) or "off" when no ring style runs."""
    ring = style.focus_ring()
    root = ctx.root
    # Focusing an item can change the focus policy of its neighbours (seen on the view
    # selector's items); put every policy back so that the next size or tab starts clean.
    policies = {w: w.focusPolicy() for w in widgets if shiboken6.isValid(w)}
    try:
        _probe_rings(app, widgets, records, ring, root)
    finally:
        for w, policy in policies.items():
            if shiboken6.isValid(w):
                w.setFocusPolicy(policy)


def _probe_rings(app: QApplication, widgets: list[QWidget], records: dict[QWidget, dict],
                 ring, root: QWidget) -> None:
    if ring is None:
        for w in widgets:
            records[w]["ring"] = "off"
        return
    ring.show_for(None)  # a fresh overlay: the last window took the old one with it
    root.activateWindow()
    app.processEvents()
    for w in widgets:
        info = records[w]
        if not shiboken6.isValid(w):  # an earlier focus change rebuilt part of the screen
            continue
        if info["focus_policy"] == Qt.FocusPolicy.NoFocus or not w.isEnabled():
            continue
        if isinstance(w, QAbstractItemView):
            info["ring"] = "view"
            continue
        target = style._ring_target(w)
        if target is None:
            continue
        w.setFocus(Qt.FocusReason.TabFocusReason)
        app.processEvents()
        overlay = ring.overlay
        shown = (overlay is not None and overlay.isVisible() and overlay.target() is target)
        info["ring"] = (shown, (overlay.width() - target.width()) // 2 if shown else 0)
    ring.show_for(None)
    focused = QApplication.focusWidget()
    if focused is not None:
        focused.clearFocus()
    app.processEvents()


# -- checks -------------------------------------------------------------------------------

def _res(ok: bool, value: object, limit: object) -> Res:
    return str(value), str(limit), "pass" if ok else "fail"


def _caption_floor(p: dict, ctx: Ctx) -> int:
    return px_round(p["base_px"] * ctx.scale)


def chk_type_min_size(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i["text"] or i["px"] <= 0:
        return None
    limit = _caption_floor(p, ctx)
    return _res(i["px"] >= limit, i["px"], f">={limit}")


def chk_type_ramp(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i["text"] or i["px"] <= 0:
        return None
    allowed = sorted({px_round(s * ctx.scale) for s in p["steps"]})
    return _res(i["px"] in allowed, i["px"], "|".join(map(str, allowed)))


def chk_type_family(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i["text"]:
        return None
    return _res(i["family"] in p["families"], i["family"], "|".join(p["families"]))


def chk_type_weight(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i["text"]:
        return None
    return _res(i["weight"] >= p["min"], i["weight"], f">={p['min']}")


def chk_contrast(i: dict, p: dict, ctx: Ctx, role: str) -> Res | None:
    """One check per role; the body check also reports the widgets that cannot be measured."""
    if not i["text"]:
        return None
    limit = f">={p['min']}"
    if not i["enabled"]:
        return ("disabled", limit, "skip") if role == "body" else None
    if i["contrast"] is None:
        return (("too few text pixels, no declared colour", limit, "skip")
                if role == "body" else None)
    secondary_colour = int(theme.manager().hex(p["secondary_token"]).lstrip("#"), 16)
    # Placeholder text is secondary text by role (D10, HIG-CTL-10), whatever colour it has.
    secondary = i["placeholder"] or _near(i["foreground"], secondary_colour)
    if (role == "secondary") != secondary:
        return None
    return _res(i["contrast"] >= p["min"], f"{i['contrast']:.2f}", limit)


def chk_contrast_body(i, p, ctx):
    token = ctx.param("contrast-secondary").get("secondary_token", "text-2")
    return chk_contrast(i, {**p, "secondary_token": token}, ctx, "body")


def chk_contrast_secondary(i, p, ctx):
    return chk_contrast(i, p, ctx, "secondary")


def chk_hit_min(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if isinstance(w, QScrollBar):
        return "thin scroll bar", f">={p['min']}", "skip"
    if not is_clickable(w):
        return None
    width, height = i["hit"]
    return _res(min(width, height) >= p["min"], f"{width}x{height}", f">={p['min']}")


def _d5(p: dict) -> int:
    return max(p["min"], theme.manager().size(p["d5_token"]))


def _d5_density(p: dict) -> int:
    """The D5 value of the density the user chose (Sıkı 28 / Normal 32 / Geniş 40). It does not
    follow the text size (the one-step-up at 130 % and 150 % is left out)."""
    return max(p["min"], int(tokens.SIZES[theme.manager().density()][p["d5_token"]]))


def chk_hit_button_height(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if not isinstance(w, QAbstractButton) or isinstance(w, (QCheckBox, QRadioButton)):
        return None
    limit = _d5_density(p)
    return _res(i["hit"][1] >= limit, i["hit"][1], f">={limit}")


def chk_hit_row(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if not is_clickable(w) or not in_row(w):
        return None
    limit = _d5(p)
    return _res(i["hit"][1] >= limit, i["hit"][1], f">={limit}")


def chk_kbd_focus(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if not is_clickable(w) or not i["enabled"]:
        return None
    ok = i["focus_policy"] != Qt.FocusPolicy.NoFocus
    if not ok:  # exemptions: another way to the same action exists (listed in the rule's note)
        if i["kind"] == "caption-button":
            return "NoFocus: caption button (Alt+Space window menu)", "focusable", "skip"
        if i["bar_action"]:
            return "NoFocus: line-edit clear action (Esc, Delete)", "focusable", "skip"
    return _res(ok, "focusable" if ok else "NoFocus", "focusable")


def _named(i: dict) -> str:
    return (i["accessible_name"] or i["text"] or i["tooltip"]).strip()


def chk_a11y_name(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if i["focus_policy"] == Qt.FocusPolicy.NoFocus or not i["enabled"]:
        return None
    if isinstance(w, QLineEdit) and isinstance(w.parentWidget(), (QAbstractSpinBox, QComboBox)):
        return None  # the inner editor takes its box's name
    name = _named(i)
    return _res(bool(name), name or "none", "accessibleName|text|tooltip")


def chk_icon_tooltip(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i["icon_only"]:
        return None
    has = bool(i["tooltip"].strip())
    return _res(has, i["tooltip"] if has else "none", "tooltip set")


def chk_focus_ring(i: dict, p: dict, ctx: Ctx) -> Res | None:
    ring = i["ring"]
    if ring is None:
        return None
    if ring == "off":
        return "no ring style installed", f">={p['min_px']} px", "skip"
    if ring == "view":
        return "item view: ring per item", f">={p['min_px']} px", "skip"
    shown, size = ring
    return _res(shown and size >= p["min_px"], f"{size} px" if shown else "no ring",
                f">={p['min_px']} px")


def chk_layout_margin_grid(i: dict, p: dict, ctx: Ctx) -> Res | None:
    margins = i["layout_margins"]
    if margins is None:
        return None
    stroke = p.get("stroke", 0) if i["is_frame"] else None  # a 1 px inset under a 1 px stroke
    exempt = {*p.get("a_values", []), stroke} - {None}
    ok = all(m % p["grid"] == 0 or m in exempt for m in margins)
    return _res(ok, ",".join(map(str, margins)), f"multiple of {p['grid']}")


def chk_layout_spacing(i: dict, p: dict, ctx: Ctx) -> Res | None:
    """The gap people see: the real gap between visible neighbours of a box layout (or the
    declared spacing when it is smaller, or when the layout is not a box layout)."""
    declared = i["layout_spacing"]
    if declared is None or i["layout_items"] < 2:
        return None  # no layout, or fewer than two visible items: no gap to measure
    real = i["layout_gap"]
    if real is not None:
        value = real if declared < 0 else min(real, declared)
    elif declared < 0:
        return "style default", "|".join(map(str, p["allowed"])), "skip"
    else:
        value = declared
    allowed = sorted({*p["allowed"], *p.get("a_values", [])})
    return _res(value in allowed, value, "|".join(map(str, allowed)))


RADIUS = re.compile(r"(?<![\w-])border-radius\s*:\s*([^;}]+)")
BLOCK = re.compile(r"([^{}]+)\{([^{}]*)\}")


def _radii(css: str) -> list[int]:
    return [int(n) for m in RADIUS.findall(css) for n in re.findall(r"\d+", m)]


def _px(body: str, name: str) -> int | None:
    m = re.search(rf"(?<![\w-]){name}\s*:\s*(\d+)px", body)
    return int(m.group(1)) if m else None


def _handle_extent(selector: str, body: str, blocks: list[tuple[str, str]]) -> int | None:
    """Thickness of a scroll bar handle: the bar's width (height) less the handle's margins."""
    vertical = ":vertical" in selector
    bar_selector = "QScrollBar:vertical" if vertical else "QScrollBar:horizontal"
    bar = next((b for sel, b in blocks if sel == bar_selector), "")
    thickness = _px(bar, "width" if vertical else "height")
    margin = re.search(r"(?<![\w-])margin\s*:\s*(\d+)(?:px)?\s+(\d+)(?:px)?", body)
    if thickness is None or margin is None:
        return None
    return thickness - 2 * int(margin.group(2 if vertical else 1))


def _plain(selector: str) -> str:
    """A selector without its state pseudo-classes (":hover", ":vertical"), "::sub" kept."""
    return re.sub(r"(?<!:):(?!:)[\w-]+", "", selector.strip())


def radius_split(css: str, own_extent: int | None = None) -> tuple[list[int], list[int]]:
    """(corner radii, circle and pill radii) in a style sheet. A radius of about half the box's
    smaller side or more makes a circle or pill, not a corner: the box is the width and height
    of the same selector (an indicator), a scroll bar handle (bar thickness less its margins)
    or, in a widget's own style sheet without a selector, the widget itself."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    blocks = [(sel.strip(), body) for sel, body in BLOCK.findall(css)]
    if not blocks and RADIUS.search(css):
        blocks = [("", css)]
    base: dict[str, int] = {}  # plain selector -> smaller of its declared width and height
    for selector, body in blocks:
        sides = [n for n in (_px(body, "width"), _px(body, "height")) if n is not None]
        for part in selector.split(","):
            if sides and part.strip() == _plain(part):
                base.setdefault(_plain(part), min(sides))
    corners: list[int] = []
    pills: list[int] = []
    for selector, body in blocks:
        radii = _radii(body)
        if not radii:
            continue
        if "::handle" in selector:
            extent = _handle_extent(selector, body, blocks)
        else:
            known = [base[_plain(part)] for part in selector.split(",") if _plain(part) in base]
            extent = min(known) if known else own_extent if selector == "" else None
        for r in radii:
            (pills if extent is not None and 2 * r + 1 >= extent else corners).append(r)
    return corners, pills


def chk_radius(i: dict, p: dict, ctx: Ctx) -> Res | None:
    extent = min(i["hit"])
    corners, pills = radius_split(i["stylesheet"], extent)
    if i.get("is_window"):
        more = radius_split(QApplication.instance().styleSheet())
        corners, pills = corners + more[0], pills + more[1]
    if not corners and not pills:
        return None
    allowed = sorted({*p["allowed"], *p.get("a_values", [])})
    bad = sorted({r for r in corners if r not in allowed})
    shown = ",".join(map(str, sorted(set(corners)))) or "circles and pills only"
    return _res(not bad, shown, "|".join(map(str, allowed)))


def chk_icon_size(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if not isinstance(w, QAbstractButton) or w.icon().isNull():
        return None
    size = w.iconSize().width()
    return _res(size in p["allowed"], size, "|".join(map(str, p["allowed"])))


def chk_text_elided(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if isinstance(w, QTableView):  # cells too (Apple: scrollable regions), see screenshots._cells
        cut = screenshots._cells(w, "")
        return _res(not cut, f"{len(cut)} cells elided" if cut else "whole", "whole text")
    shown = screenshots._shown_text(w)
    if shown is None:
        return None
    full, drawn, room = shown
    if not full or "\n" in full or "<" in full:
        return None
    need = w.fontMetrics().horizontalAdvance(drawn)
    elided = drawn != full or (room is not None and need > room)
    return _res(not elided, "elided" if elided else "whole", "whole text")


def chk_window_fit(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i.get("is_window"):
        return None
    w = i["widget"]
    hint = w.minimumSizeHint()
    ok = (hint.width() <= p["width"] and hint.height() <= p["height"]
          and w.width() <= ctx.size[0] and w.height() <= ctx.size[1])
    return _res(ok, f"min {hint.width()}x{hint.height()}, is {w.width()}x{w.height()}",
                f"<={p['width']}x{p['height']}")


def chk_window_scroll(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i.get("is_window"):
        return None
    w = i["widget"]
    area = w.width() * w.height()
    found = []
    for scroller in w.findChildren(QAbstractScrollArea):
        if (not scroller.isVisible() or isinstance(scroller, QAbstractItemView)
                or scroller.window() is not w or type(scroller).__name__ in WINDOW_SCROLL_EXEMPT):
            continue
        port = scroller.viewport()
        if port.width() * port.height() * 2 < area:
            continue
        for bar in (scroller.verticalScrollBar(), scroller.horizontalScrollBar()):
            if bar.isVisible() and bar.maximum() > bar.minimum():
                found.append(type(scroller).__name__)
    return _res(not found, ",".join(sorted(set(found))) or "none", "no window scroll")


CHECKS = {
    "type-min-size": chk_type_min_size, "type-ramp": chk_type_ramp,
    "type-family": chk_type_family, "type-weight": chk_type_weight,
    "text-elided": chk_text_elided,
    "contrast-body": chk_contrast_body, "contrast-secondary": chk_contrast_secondary,
    "hit-min": chk_hit_min, "hit-button-height": chk_hit_button_height, "hit-row": chk_hit_row,
    "kbd-focus": chk_kbd_focus, "a11y-name": chk_a11y_name, "icon-tooltip": chk_icon_tooltip,
    "focus-ring": chk_focus_ring,
    "layout-margin-grid": chk_layout_margin_grid, "layout-spacing": chk_layout_spacing,
    "radius": chk_radius, "icon-size": chk_icon_size,
    "window-fit": chk_window_fit, "window-scroll": chk_window_scroll,
}


CONTRAST_CHECKS = ("contrast-body", "contrast-secondary")
CONTRAST_RULES = ("DEC-CON-01", "DEC-CON-02")
CROPS: Path | None = None  # --crops DIR: save the pixels behind every failing contrast row (B-104)


def save_crop(ctx: Ctx, w: QWidget, part_path: str, rule_id: str, value: str) -> None:
    """The grabbed pixels of a widget whose contrast failed, named so CI artifacts can be
    compared with a local run (B-104: some rows fail only on the CI machine)."""
    if CROPS is None:
        return
    rect = visible_rect(w, ctx.root)
    if rect.isEmpty():
        return
    CROPS.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() else "_" for ch in part_path)[-90:]
    name = f"{rule_id}_{ctx.theme}_{ctx.size[0]}x{ctx.size[1]}_{ctx.text}_{value}_{safe}.png"
    ctx.image.copy(rect).save(str(CROPS / name))


# -- measuring ----------------------------------------------------------------------------

def make_ctx(root: QWidget, theme_name: str, text: int, size: tuple[int, int],
             rules: list[dict]) -> Ctx:
    image = root.grab().toImage().convertToFormat(QImage.Format.Format_RGB32)
    words = memoryview(image.constBits()).cast("B").cast("I")
    params = {check: rule.get("params", {}) for check, rule in measured_rules(rules).items()}
    return Ctx(root, theme_name, text, size, image, words, image.bytesPerLine() // 4, params,
               tokens.TEXT_SCALES[text])


def measure_tree(app: QApplication, ctx: Ctx, rules: list[dict], tab: str) -> list[Row]:
    """Rows for every visible widget under ctx.root (and the root itself as "window")."""
    owners = measured_rules(rules)
    widgets = [w for w in ctx.root.findChildren(QWidget)
               if w.isVisible() and w.window() is ctx.root and w.objectName() != "focusRing"
               and not visible_rect(w, ctx.root).isEmpty()]
    records = {w: describe(w, ctx) for w in widgets}
    for w, info in records.items():
        info["widget"] = w
    probe_focus(app, widgets, records, ctx)
    if ctx.window_checks:
        top = describe(ctx.root, ctx)
        top.update(widget=ctx.root, is_window=True, ring=None)
        records[ctx.root] = top
    size = f"{ctx.size[0]}x{ctx.size[1]}"
    rows: list[Row] = []
    for w, info in records.items():
        if not shiboken6.isValid(w):
            continue
        path = "(window)" if w is ctx.root else widget_path(w, ctx.root)
        columns = [(f"{path}[col {c}]", {**info, "background": bg, "foreground": fg,
                                         "contrast": ratio})
                   for c, bg, fg, ratio in info["cells"]]
        for check, rule in owners.items():
            # a table's contrast is judged per column (its worst cell), the rest as one widget
            parts = columns if columns and check in CONTRAST_CHECKS else [(path, info)]
            for part_path, part in parts:
                result = CHECKS[check](part, ctx.params.get(check, {}), ctx)
                if result is None:
                    continue
                value, limit, verdict = result
                if exempt_row(rule["id"], part_path):
                    continue
                if verdict == "fail" and rule["id"] in CONTRAST_RULES:
                    save_crop(ctx, w, part_path, rule["id"], value)
                rows.append((tab, ctx.theme, size, str(ctx.text), part_path, info["cls"],
                             rule["id"], value, limit, verdict, rule["severity"]))
    return rows


def sort_rows(rows: list[Row]) -> list[Row]:
    return sorted(rows)


def settled(app: QApplication, window: QWidget, limit_ms: int = IDLE_MS) -> bool:
    """Spin the event loop until no pool worker runs and two grabs 40 ms apart are the same
    picture (text read in a worker, a layout pass or a repaint still queued on a slow machine
    changes it). False when it never settles within `limit_ms` (a blinking cursor)."""
    pool = QThreadPool.globalInstance()
    deadline = time.monotonic() + limit_ms / 1000
    last = None
    while time.monotonic() < deadline:
        app.processEvents()
        if pool.activeThreadCount() == 0:
            image = window.grab().toImage()
            if last is not None and image == last:
                return True
            last = image
        QTest.qWait(40)
    return False


def calm(app: QApplication, window: QWidget | None = None, extra_ms: int = 0) -> None:
    """Settle the window and let every animation (longest 240 ms, D7) finish; then wait until
    nothing is still loading or repainting (see `settled`)."""
    screenshots._settle(app, window=window)
    QTest.qWait(SETTLE_MS + extra_ms)
    screenshots._settle(app, rounds=10, window=window)
    if window is not None:
        settled(app, window)


UNPAINTED = 1.5  # a text colour closer to its background than this is "not painted (yet)"
REMEASURE = 2


def unpainted(rows: list[Row]) -> list[Row]:
    """Failing contrast rows that read as an empty or not-yet-painted widget (about 1:1)."""
    return [row for row in rows if row[6] in CONTRAST_RULES and row[9] == "fail"
            and _ratio(row[7]) < UNPAINTED]


def _ratio(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return UNPAINTED


def measure_settled(app: QApplication, window: QWidget, mode: str, text: int,
                    size: tuple[int, int], rules: list[dict], slug: str) -> list[Row]:
    """Rows of one tab; when some contrast rows read as unpainted, wait longer and measure the
    tab again (the later rows replace the earlier ones)."""
    rows = measure_tree(app, make_ctx(window, mode, text, size, rules), rules, slug)
    for attempt in range(1, REMEASURE + 1):
        if not unpainted(rows):
            break
        calm(app, window, extra_ms=SETTLE_MS * attempt)
        rows = measure_tree(app, make_ctx(window, mode, text, size, rules), rules, slug)
    return rows


def run(app: QApplication, tmp: Path, rules: list[dict], tabs=screenshots.SLUGS,
        themes=screenshots.THEMES, texts=screenshots.TEXTS, sizes=screenshots.SIZES,
        progress=None) -> list[Row]:
    manager = theme.manager()
    rows: list[Row] = []
    for text in texts:
        for mode in themes:
            manager.set_text_scale(text)
            manager.set_mode(mode)
            screenshots._settle(app)
            window = screenshots.build(tmp / f"{mode}-{text}")
            window.show()
            for width, height in sizes:
                window.resize(width, height)
                for slug in tabs:
                    window.tabs.setCurrentIndex(screenshots.SLUGS.index(slug))
                    calm(app, window)
                    rows += measure_settled(app, window, mode, text, (width, height), rules,
                                            slug)
                    if progress:
                        progress(slug, mode, f"{width}x{height}", text, len(rows))
            window.close()
            window.deleteLater()
            screenshots._settle(app)
    return sort_rows(rows)


def summarize(rows: list[Row]) -> dict[str, Counter]:
    summary: dict[str, Counter] = {}
    for row in rows:
        summary.setdefault(row[6], Counter())[row[9]] += 1
    return summary


def format_summary(rows: list[Row], rules: list[dict]) -> str:
    summary = summarize(rows)
    lines = [f"{'rule':<14}{'pass':>8}{'fail':>8}{'skip':>8}  sev  enforced"]
    by_id = {r["id"]: r for r in rules}
    for rule_id in sorted(summary):
        c = summary[rule_id]
        rule = by_id.get(rule_id, {})
        lines.append(f"{rule_id:<14}{c['pass']:>8}{c['fail']:>8}{c['skip']:>8}  "
                     f"{rule.get('severity', '?'):<4} {rule.get('enforced', False)}")
    total = Counter(row[9] for row in rows)
    lines.append(f"TOTAL rows={len(rows)} pass={total['pass']} fail={total['fail']} "
                 f"skip={total['skip']}")
    return "\n".join(lines)


def enforced_fail_rows(rows: list[Row], rules: list[dict],
                       known: set[tuple[str, ...]] = frozenset()) -> list[Row]:
    """Failing rows of enforced rules that are not on the known-fail list."""
    enforced = {r["id"] for r in rules if r.get("enforced")}
    return [row for row in rows if row[6] in enforced and row[9] == "fail"
            and not any(known_fail_matches(key, row) for key in known)]


def enforced_failures(rows: list[Row], rules: list[dict],
                      known: set[tuple[str, ...]] = frozenset()) -> int:
    return len(enforced_fail_rows(rows, rules, known))


def stale_known_fails(rows: list[Row], known: set[tuple[str, ...]]) -> list[tuple[str, ...]]:
    """Known-fail entries that no longer fail (a fix landed): the list can shrink."""
    failing = [row for row in rows if row[9] == "fail"]
    return sorted(key for key in known
                  if not any(known_fail_matches(key, row) for row in failing))


def to_tsv(rows: list[Row], header: str = "") -> str:
    lines = [header] if header else []
    lines.append("\t".join(COLUMNS))
    lines += ["\t".join(c.replace("\t", " ").replace("\n", " ") for c in row) for row in rows]
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Measure the window against rules.json")
    ap.add_argument("--tab", action="append", choices=screenshots.SLUGS)
    ap.add_argument("--theme", action="append", choices=screenshots.THEMES)
    ap.add_argument("--text", action="append", type=int, choices=screenshots.TEXTS)
    ap.add_argument("--size", action="append", help="WxH, e.g. 1366x768")
    ap.add_argument("--fails-only", action="store_true")
    ap.add_argument("--crops", type=Path, help="save the pixels of failing contrast rows here")
    ap.add_argument("--enforce", action="store_true")
    ap.add_argument("--rules", type=Path, default=RULES_PATH)
    ap.add_argument("--known-fails", type=Path, default=KNOWN_FAILS_PATH,
                    help="rule/widget pairs --enforce tolerates (Q6 fixes pending)")
    ap.add_argument("--out", type=Path, help="write the TSV here (default: standard output)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    global CROPS
    args = parse_args(argv)
    CROPS = args.crops
    rules = load_rules(args.rules)
    sizes = tuple(tuple(int(n) for n in s.lower().split("x")) for s in args.size) \
        if args.size else screenshots.SIZES
    screenshots.force_custom_frame()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    configure_application(app)
    started = time.monotonic()
    with tempfile.TemporaryDirectory() as tmp:
        rows = run(app, Path(tmp), rules, tabs=args.tab or screenshots.SLUGS,
                   themes=args.theme or screenshots.THEMES, texts=args.text or screenshots.TEXTS,
                   sizes=sizes)
    shown = [r for r in rows if r[9] == "fail"] if args.fails_only else rows
    text = to_tsv(shown)
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    print(format_summary(rows, rules))
    print(f"seconds: {time.monotonic() - started:.0f}")
    if not args.enforce:
        return 0
    known = load_known_fails(args.known_fails)
    for key in stale_known_fails(rows, known) if not args.tab else []:
        print("known-fail no longer fails (remove it): " + "\t".join(key))
    failed = enforced_fail_rows(rows, rules, known)
    for row in failed[:20]:
        print(f"ENFORCED FAIL {row[6]} {row[0]}/{row[1]}/{row[2]}/{row[3]} {row[4]}: {row[7]}")
    print(f"enforced fails: {len(failed)} (tolerated known fails: {len(known)} entries)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
