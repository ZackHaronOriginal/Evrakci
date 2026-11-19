"""Measures the real window against docs/ui-goal/rules.json (offscreen, no screen needed).

    QT_QPA_PLATFORM=offscreen python tools/ui_measure.py --out report.tsv
    ... --tab kontrol --theme dark --text 150 --size 1366x768 --fails-only
    ... --enforce      # exit 1 when a rule with "enforced": true fails (none is yet)

For 6 tabs x {light, dark, hc} x {1366x768, 1920x1080} x text {100, 150} it builds the demo window
like tools/screenshots.py does (fresh in each theme and text size, custom title band forced),
and for every visible widget records: class and object name, geometry, content margins, layout
margins and spacing, gap to the nearest sibling, font (family, px size, weight), text colour,
background colour and their contrast ratio, hit area, focus ring (really focused by Tab, then
read back from the overlay in evrakci.ui.style), tooltip, accessible name and role, enabled
state and the duration of every animation the widget owns. Each rule in rules.json with a
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
measured ("skip"); only QTableView cells and headers are sampled for item views; disabled
widgets are exempt (WCAG). Role: "secondary" when the sampled text colour is within 12 RGB steps
of the theme's text-2 token (D10: secondary 4.5:1), otherwise "body" (body and table text, 7:1).

Other methods. Hit area is the widget's own size. "Controls in rows" are clickable widgets
inside an item view or inside a widget whose class name ends in "Row". Neighbour gap is the
pixel gap to the nearest visible sibling on the right or below that overlaps it. The ring check
focuses the widget with the Tab reason and reads EvrakciStyle's overlay (target, visible, ring
width); item views get their ring per item from the style (PE_FrameFocusRect), so they are
reported "skip". Radii are read from "border-radius" in the application's and the widgets' own
style sheets; painted radii are "manual". Animations are the direct QPropertyAnimation /
QVariantAnimation children (looping ones, as the indeterminate bar, are skipped).
Each state waits 300 ms (longer than the longest D7 duration) before it is measured.
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
    QAbstractAnimation,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QVariantAnimation,
)
from PySide6.QtGui import QAccessible, QFontInfo, QImage  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractButton,
    QAbstractItemView,
    QAbstractScrollArea,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QRadioButton,
    QScrollBar,
    QSlider,
    QTabBar,
    QTableView,
    QWidget,
)

from evrakci.app import configure_application  # noqa: E402
from evrakci.ui import style, theme  # noqa: E402
from evrakci.ui.tokens import generated as tokens  # noqa: E402

RULES_PATH = ROOT / "docs/ui-goal/rules.json"
COLUMNS = ("tab", "theme", "size", "text", "widget", "class", "rule", "value", "limit", "result",
           "severity")
SETTLE_MS = 300
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


def sample_colours(ctx: Ctx, rect: QRect) -> tuple[int, int] | None:
    """(background, text) as 0xRRGGBB from the rendered window, see the module docstring."""
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
        return None
    background = max(hist.items(), key=lambda kv: (kv[1], -kv[0]))[0] & 0xFFFFFF
    best, best_ratio = None, 1.0
    for colour in sorted(c & 0xFFFFFF for c, n in hist.items() if n >= 2):
        ratio = contrast(colour, background)
        if ratio > best_ratio:
            best, best_ratio = colour, ratio
    return None if best is None else (background, best)


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


def accessible_role(w: QWidget) -> str:
    try:
        iface = QAccessible.queryAccessibleInterface(w)
        return iface.role().name if iface is not None else ""
    except (RuntimeError, AttributeError):
        return ""


def animation_durations(w: QWidget) -> list[int]:
    found = []
    for child in w.findChildren(QAbstractAnimation, "", Qt.FindChildOption.FindDirectChildrenOnly):
        if isinstance(child, (QPropertyAnimation, QVariantAnimation)) and child.loopCount() == 1:
            found.append(child.duration())
    return sorted(found)


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
    colours = None
    if text and w.isEnabled():
        colours = sample_colours(ctx, sample)
    layout = w.layout()
    margins = w.contentsMargins()
    gap_x, gap_y = gap_to_neighbours(w, root)
    icon_only = (isinstance(w, QAbstractButton) and not w.icon().isNull() and not text)
    weight = font.weight()
    return {
        "cls": type(w).__name__, "name": w.objectName(), "enabled": w.isEnabled(),
        "geometry": (w.mapTo(root, QPoint(0, 0)).x(), w.mapTo(root, QPoint(0, 0)).y(),
                     w.width(), w.height()),
        "margins": (margins.left(), margins.top(), margins.right(), margins.bottom()),
        "layout_margins": None if layout is None else (
            layout.contentsMargins().left(), layout.contentsMargins().top(),
            layout.contentsMargins().right(), layout.contentsMargins().bottom()),
        "layout_spacing": None if layout is None else layout.spacing(),
        "gap": (gap_x, gap_y),
        "family": font.family(), "resolved_family": info.family(),
        "px": info.pixelSize(), "weight": int(getattr(weight, "value", weight)),
        "text": text, "icon_only": icon_only,
        "background": None if colours is None else colours[0],
        "foreground": None if colours is None else colours[1],
        "contrast": None if colours is None else contrast(colours[0], colours[1]),
        "hit": (w.width(), w.height()),
        "tooltip": w.toolTip(), "accessible_name": w.accessibleName(),
        "role": accessible_role(w), "focus_policy": w.focusPolicy(),
        "animations": animation_durations(w), "stylesheet": w.styleSheet(),
        "ring": None,  # filled by probe_focus
    }


# -- focus probe --------------------------------------------------------------------------

def probe_focus(app: QApplication, widgets: list[QWidget], records: dict[QWidget, dict],
                ctx: Ctx) -> None:
    """Focus each focusable widget with the Tab reason and read the ring back: a (visible,
    ring px) pair, "view" for item views (ring per item) or "off" when no ring style runs."""
    ring = style.focus_ring()
    root = ctx.root
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
        return ("no text pixels", limit, "skip") if role == "body" else None
    secondary_colour = int(theme.manager().hex(p["secondary_token"]).lstrip("#"), 16)
    if (role == "secondary") != _near(i["foreground"], secondary_colour):
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


def chk_hit_button_height(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if not isinstance(w, QAbstractButton) or isinstance(w, (QCheckBox, QRadioButton)):
        return None
    limit = _d5(p)
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
    ok = all(m % p["grid"] == 0 for m in margins)
    return _res(ok, ",".join(map(str, margins)), f"multiple of {p['grid']}")


def chk_layout_spacing(i: dict, p: dict, ctx: Ctx) -> Res | None:
    spacing = i["layout_spacing"]
    if spacing is None:
        return None
    if spacing < 0:
        return "style default", "|".join(map(str, p["allowed"])), "skip"
    return _res(spacing in p["allowed"], spacing, "|".join(map(str, p["allowed"])))


RADIUS = re.compile(r"border-radius\s*:\s*([^;}]+)")


def _radii(css: str) -> list[int]:
    return [int(n) for m in RADIUS.findall(css) for n in re.findall(r"\d+", m)]


def chk_radius(i: dict, p: dict, ctx: Ctx) -> Res | None:
    css = i["stylesheet"]
    if i.get("is_window"):
        css += "\n" + QApplication.instance().styleSheet()
    radii = _radii(css)
    if not radii:
        return None
    bad = sorted({r for r in radii if r not in p["allowed"]})
    return _res(not bad, ",".join(map(str, sorted(set(radii)))),
                "|".join(map(str, p["allowed"])))


def chk_anim_duration(i: dict, p: dict, ctx: Ctx) -> Res | None:
    if not i["animations"]:
        return None
    bad = [d for d in i["animations"] if d not in p["allowed"]]
    return _res(not bad, ",".join(map(str, i["animations"])), "|".join(map(str, p["allowed"])))


def chk_icon_size(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
    if not isinstance(w, QAbstractButton) or w.icon().isNull():
        return None
    size = w.iconSize().width()
    return _res(size in p["allowed"], size, "|".join(map(str, p["allowed"])))


def chk_text_elided(i: dict, p: dict, ctx: Ctx) -> Res | None:
    w = i["widget"]
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
                or scroller.window() is not w):
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
    "radius": chk_radius, "anim-duration": chk_anim_duration, "icon-size": chk_icon_size,
    "window-fit": chk_window_fit, "window-scroll": chk_window_scroll,
}


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
        for check, rule in owners.items():
            result = CHECKS[check](info, ctx.params.get(check, {}), ctx)
            if result is None:
                continue
            value, limit, verdict = result
            rows.append((tab, ctx.theme, size, str(ctx.text), path, info["cls"], rule["id"],
                         value, limit, verdict, rule["severity"]))
    return rows


def sort_rows(rows: list[Row]) -> list[Row]:
    return sorted(rows)


def calm(app: QApplication, window: QWidget | None = None) -> None:
    """Settle the window and let every animation (longest 240 ms, D7) finish."""
    screenshots._settle(app, window=window)
    QTest.qWait(SETTLE_MS)
    screenshots._settle(app, rounds=10, window=window)


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
                    ctx = make_ctx(window, mode, text, (width, height), rules)
                    rows += measure_tree(app, ctx, rules, slug)
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


def enforced_failures(rows: list[Row], rules: list[dict]) -> int:
    enforced = {r["id"] for r in rules if r.get("enforced")}
    return sum(1 for row in rows if row[6] in enforced and row[9] == "fail")


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
    ap.add_argument("--enforce", action="store_true")
    ap.add_argument("--rules", type=Path, default=RULES_PATH)
    ap.add_argument("--out", type=Path, help="write the TSV here (default: standard output)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
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
    return 1 if args.enforce and enforced_failures(rows, rules) else 0


if __name__ == "__main__":
    raise SystemExit(main())
