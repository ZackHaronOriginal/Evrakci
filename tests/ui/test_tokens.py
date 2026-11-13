"""Design tokens (direction A), ThemeManager and EvrakciStyle."""
import colorsys
import importlib.util
import json
import re
from pathlib import Path

import pytest
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QTabBar, QVBoxLayout, QWidget

from evrakci.ui import motion, style, theme
from evrakci.ui.prefs import Prefs
from evrakci.ui.tokens import generated as g
from evrakci.ui.tokens import qss

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "src" / "evrakci" / "ui"
SPEC = ROOT / "docs" / "ui-goal" / "mockups" / "final-a" / "tokens.css"

# D10 pairs, ported from docs/ui-goal/mockups/final-a/_contrast.py: (fg, bg, minimum).
PAIRS = [
    ("text", "base", 7), ("text", "layer", 7), ("text", "card", 7), ("text", "popover", 7),
    ("text", "hover", 7), ("text", "selected", 7), ("text", "check-wash", 7),
    ("paper-ink", "paper", 7),
    ("text-2", "base", 4.5), ("text-2", "layer", 4.5), ("text-2", "card", 4.5),
    ("text-2", "popover", 4.5), ("text-2", "selected", 4.5), ("text-2", "hover", 4.5),
    ("text-2", "well", 4.5),
    ("text-on-accent", "accent", 4.5), ("text-on-accent", "accent-hover", 4.5),
    ("text-accent", "card", 4.5), ("text-accent", "layer", 4.5), ("text-accent", "popover", 4.5),
    ("text-accent", "selected", 4.5),
    ("manila-ink", "manila", 7), ("rider-ink", "rider", 4.5),
    ("check-text", "card", 4.5), ("check-text", "layer", 4.5), ("check-text", "selected", 4.5),
    ("check-text", "check-wash", 4.5),
    ("ok", "card", 4.5), ("ok", "layer", 4.5), ("ok", "popover", 4.5),
    ("danger", "card", 4.5), ("danger", "popover", 4.5), ("danger", "layer", 4.5),
    ("edge", "card", 3), ("edge", "layer", 3), ("edge", "popover", 3),
    ("icon", "base", 3), ("icon", "layer", 3), ("icon", "card", 3), ("icon", "hover", 3),
    ("accent", "layer", 3), ("accent", "card", 3), ("accent", "track", 3),
    ("accent", "selected", 3),
    ("focus-outer", "base", 3), ("focus-outer", "layer", 3), ("focus-outer", "card", 3),
    ("focus-outer", "selected", 3), ("focus-outer", "popover", 3),
    ("rider-edge", "layer", 3), ("rider-edge", "track", 3), ("rider-edge", "card", 3),
    ("accent", "base", 3), ("manila-edge", "layer", 3),
    ("cut-qr", "manila", 3), ("cut-filter", "manila", 3), ("cut-manual", "manila", 3),
    ("on-manila-ok", "manila", 3),
    ("paper-box", "paper", 3), ("paper-mark", "paper", 3), ("paper-head", "paper", 3),
    ("cut-filter-text", "card", 3),
    ("text", "hover-pop", 7), ("danger", "hover-pop", 4.5),
]
HUE_TOKENS = ["cut-qr", "cut-filter", "cut-manual", "ok", "danger", "accent", "text-accent"]
HEX = re.compile(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?\b|#[0-9a-fA-F]{3}\b")
HEX_ALLOWED = {"tokens/generated.py", "logo_data.py"}
# Phase 3 rebuilt every screen on tokens: no file outside the token source has a hex literal.
HEX_LEGACY: dict[str, int] = {}


def _lum(value: str) -> float:
    channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _ratio(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _build_tokens_module():
    spec = importlib.util.spec_from_file_location("build_tokens", ROOT / "tools/build_tokens.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mgr(qapp):
    """A fresh ThemeManager (light, normal, 100 %), not applied to the app."""
    manager = theme.ThemeManager()
    manager.set_mode("light")
    return manager


@pytest.fixture
def applied(qapp):
    """The app-wide manager applied to the app in light mode; restored afterwards."""
    manager = theme.manager()
    manager.set_mode("light")
    manager.apply(qapp)
    yield manager
    manager.set_mode("system")
    manager.set_density("normal")
    manager.set_text_scale(100)
    manager.set_reduced_motion(None)
    manager.apply(qapp)


# -- tokens ---------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["light", "dark", "hc"])
def test_every_token_pair_meets_d10(name):
    colours = g.COLORS[name]
    failing = [(fg, bg, round(_ratio(colours[fg], colours[bg]), 2))
               for fg, bg, minimum in PAIRS if _ratio(colours[fg], colours[bg]) < minimum]
    assert not failing


@pytest.mark.parametrize("name", ["light", "dark", "hc"])
def test_runtime_colours_are_a_s_tokens(name):
    """Old alias names never overwrite A's own roles ("card", "paper", ...)."""
    manager = theme.ThemeManager()
    manager.set_mode(name)
    colours = manager.colors()
    expected = dict(g.COLORS[name])
    if name == "hc":
        if theme.system_high_contrast():
            pytest.skip("hc follows the live Windows system colours here")
        expected.update({k: g.SYSTEM_COLORS[ref] for k, ref in g.HC_SYSTEM.items()})
    assert {k: colours[k] for k in expected} == expected
    failing = [(fg, bg) for fg, bg, minimum in PAIRS
               if _ratio(colours[fg], colours[bg]) < minimum]
    assert not failing


@pytest.mark.parametrize("name", ["light", "dark"])
def test_only_kontrol_is_orange(name):
    colours = g.COLORS[name]
    rider_hue = colorsys.rgb_to_hls(*QColor(colours["rider"]).getRgbF()[:3])[0] * 360
    for token in HUE_TOKENS:
        hue, _light, sat = colorsys.rgb_to_hls(*QColor(colours[token]).getRgbF()[:3])
        gap = abs(hue * 360 - rider_hue) % 360
        assert sat < 0.2 or min(gap, 360 - gap) >= 30, token
    assert colours["danger"] != colours["rider"]


def test_hc_kontrol_ink_differs_from_links():
    assert g.COLORS["hc"]["check-text"] != g.COLORS["hc"]["text-accent"]


def test_no_hex_colour_outside_the_token_source():
    found = {}
    for path in UI.rglob("*.py"):
        rel = path.relative_to(UI).as_posix()
        if rel in HEX_ALLOWED:
            continue
        hits = HEX.findall(path.read_text(encoding="utf-8"))
        if hits:
            found[rel] = len(hits)
    assert {k: v for k, v in found.items() if k not in HEX_LEGACY} == {}
    for name, count in found.items():
        assert count <= HEX_LEGACY.get(name, 0), name


def test_generated_files_match_the_spec():
    build = _build_tokens_module()
    tree = build.build_json(SPEC.read_text(encoding="utf-8"))
    assert json.loads((UI / "tokens/tokens.json").read_text(encoding="utf-8")) == tree
    assert (UI / "tokens/tokens.json").read_text(encoding="utf-8") == build.render_json(tree)
    assert (UI / "tokens/generated.py").read_text(encoding="utf-8") == build.render_python(tree)


def test_tokens_are_dtcg():
    tree = json.loads((UI / "tokens/tokens.json").read_text(encoding="utf-8"))
    assert tree["color"]["light"]["accent"] == {"$type": "color", "$value": "#3f5a4c"}
    assert tree["color"]["hc"]["accent"]["$value"] == "{color.system.sys-highlight}"
    assert tree["size"]["normal"]["control-h"]["$value"] == {"value": 32, "unit": "px"}
    assert tree["shadow"]["light"]["shadow-float"]["$type"] == "shadow"


def test_d1_brand_and_d5_d7_values():
    assert g.COLORS["light"]["accent"] == g.COLORS["light"]["paper-box"]
    assert g.COLORS["light"]["rider"] == g.COLORS["dark"]["rider"]
    assert [g.SIZES[d]["row-h"] for d in ("compact", "normal", "comfortable")] == [32, 40, 48]
    assert [g.SIZES[d]["control-h"] for d in ("compact", "normal", "comfortable")] == [28, 32, 40]
    assert sorted(g.DURATIONS.values()) == sorted(int(d) for d in motion.Duration if d)
    assert max(g.DURATIONS.values()) <= motion.MAX_DURATION


# -- ThemeManager ---------------------------------------------------------------------------
def test_switching_theme_changes_palette_and_emits(mgr, qtbot):
    light = mgr.palette().color(QPalette.ColorRole.Window).name()
    with qtbot.waitSignal(mgr.changed, timeout=1000):
        mgr.set_mode("dark")
    assert mgr.theme() == "dark"
    assert light == g.COLORS["light"]["base"]
    assert mgr.palette().color(QPalette.ColorRole.Window).name() == g.COLORS["dark"]["base"]
    assert mgr.color("accent").name() == g.COLORS["dark"]["accent"]


def test_hc_uses_system_colours(mgr):
    mgr.set_mode("hc")
    p = mgr.palette()
    assert p.color(QPalette.ColorRole.Highlight).name() == g.SYSTEM_COLORS["sys-highlight"]
    assert p.color(QPalette.ColorRole.Window).name() == g.SYSTEM_COLORS["sys-window"]
    disabled = p.color(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text).name()
    assert disabled == g.SYSTEM_COLORS["sys-gray"]


def test_density_and_text_scale_change_sizes(mgr):
    assert (mgr.size("control-h"), mgr.size("row-h"), mgr.size("fs-body")) == (32, 40, 15)
    mgr.set_density("compact")
    assert (mgr.size("control-h"), mgr.size("row-h")) == (28, 32)
    mgr.set_density("normal")
    mgr.set_text_scale(115)
    assert mgr.effective_density() == "normal" and mgr.size("fs-body") == 17
    mgr.set_text_scale(130)  # 130 % and up: one density up
    assert mgr.effective_density() == "comfortable" and mgr.size("control-h") == 40
    mgr.set_text_scale(150)
    assert mgr.size("fs-caption") == 20 and mgr.size("icon-btn") == 44
    assert mgr.font("body").pixelSize() == mgr.size("fs-body")
    assert mgr.size("s4") == 16 and mgr.size("r-layer") == 8


def test_title_band_rule_is_provisional_at_150(mgr):
    assert mgr.title_band().tab_labels == "all" and mgr.title_band().search_width == 148
    mgr.set_text_scale(150)
    assert mgr.title_band().tab_labels == "selected" and mgr.title_band().tab_height == 44


def test_fonts_use_inter_stack_and_tabular_figures(mgr):
    font = mgr.font("value")
    assert font.families()[-1] == "Segoe UI"
    assert font.weight() == QFont.Weight.Normal
    assert mgr.font("panel").weight() == QFont.Weight.DemiBold
    assert font.featureValue(QFont.Tag("tnum")) == 1
    assert font.featureValue(QFont.Tag("zero")) == 1


def test_bad_settings_are_refused(mgr):
    for call, value in ((mgr.set_mode, "pink"), (mgr.set_density, "huge"),
                        (mgr.set_text_scale, 120)):
        with pytest.raises(ValueError):
            call(value)


def test_prefs_round_trip(mgr, tmp_path):
    prefs = Prefs(tmp_path / "ui.ini")
    prefs.set_theme("dark")
    prefs.set_text_size(130)
    mgr.bind_prefs(prefs)
    assert (mgr.mode(), mgr.text_scale()) == ("dark", 130)
    mgr.set_density("compact")
    mgr.set_reduced_motion(True)
    again = Prefs(tmp_path / "ui.ini")
    assert (again.density(), again.reduced_motion()) == ("compact", True)
    assert motion.reduced_motion() is True
    mgr.set_reduced_motion(None)


def test_stylesheet_renders_for_every_setting(mgr):
    for mode in ("light", "dark", "hc"):
        for density in ("compact", "normal", "comfortable"):
            mgr.set_mode(mode)
            mgr.set_density(density)
            css = mgr.stylesheet()
            assert "{{" not in css and "@" not in css
            assert mgr.hex("accent") in css
    assert qss.fields() <= set(mgr.qss_values())


def test_old_names_still_resolve(mgr):
    for name in theme.LEGACY:
        assert QColor(mgr.hex(name)).isValid(), name
    assert theme.TOKENS["shell"] == theme.TOKENS["accent"]
    assert theme.variable_colour(5) == theme.TOKENS["v2"]


# -- EvrakciStyle ---------------------------------------------------------------------------
def _ring_pixels(image: QImage, colour: QColor, rect) -> int:
    wanted = colour.rgb()
    xs = range(rect.left() - 3, rect.right() + 4)
    return sum(1 for x in xs for y in (rect.top() - 2, rect.bottom() + 2)
               if 0 <= x < image.width() and 0 <= y < image.height()
               and image.pixel(x, y) == wanted)


@pytest.mark.parametrize("make", [lambda: QLineEdit("1234"), lambda: QPushButton("Kes")])
def test_focus_ring_is_painted_around_the_control(applied, qtbot, make):
    box = QWidget()
    qtbot.addWidget(box)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(16, 16, 16, 16)
    control = make()
    other = QLineEdit()
    layout.addWidget(control)
    layout.addWidget(other)
    box.show()
    box.activateWindow()
    qtbot.waitUntil(lambda: QApplication.activeWindow() is box)
    other.setFocus(Qt.FocusReason.MouseFocusReason)
    control.setFocus(Qt.FocusReason.TabFocusReason)
    ring = style.focus_ring()
    qtbot.waitUntil(lambda: ring.overlay is not None and ring.overlay.target() is control)
    image = box.grab().toImage()
    outer = applied.color("focus-outer")
    assert _ring_pixels(image, outer, control.geometry()) > control.width()
    control.clearFocus()
    assert not ring.overlay.isVisible()


def test_ring_shape_is_two_outer_one_inner(applied):
    image = QImage(40, 30, QImage.Format.Format_RGB32)
    image.fill(applied.color("layer"))
    painter = QPainter(image)
    style.paint_ring(painter, QRectF(0, 0, 40, 30), 4)
    painter.end()
    middle = 15
    assert QColor(image.pixel(0, middle)) == applied.color("focus-outer")
    assert QColor(image.pixel(1, middle)) == applied.color("focus-outer")
    assert QColor(image.pixel(2, middle)) == applied.color("focus-inner")
    assert QColor(image.pixel(4, middle)) == applied.color("layer")


def test_title_tabs_are_filled_with_feet(applied, qtbot):
    box = QWidget()
    qtbot.addWidget(box)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(24, 24, 24, 24)
    tabs = QTabBar()
    tabs.setObjectName("titleTabs")
    tabs.setExpanding(False)
    for name in ("Yükle", "Kontrol", "Şablonlar"):
        tabs.addTab(name)
    tabs.setCurrentIndex(1)
    layout.addWidget(tabs)
    box.show()
    qtbot.waitExposed(box)
    assert tabs.tabRect(1).height() == applied.title_band().tab_height
    image = box.grab().toImage()
    rect = tabs.tabRect(1).translated(tabs.pos())
    layer = applied.color("layer").rgb()
    assert image.pixel(rect.center().x(), rect.bottom() - 2) == layer
    assert image.pixel(rect.left() - 2, rect.bottom()) == layer  # left foot, outside the tab
    assert image.pixel(rect.center().x(), rect.top()) != layer  # stroke on top


def test_style_metrics_and_hints(applied, qapp):
    from PySide6.QtWidgets import QStyle

    st = style.installed_style()
    assert st is not None and st.objectName() == "evrakci"
    assert st.pixelMetric(QStyle.PixelMetric.PM_SmallIconSize) == 16
    assert st.pixelMetric(QStyle.PixelMetric.PM_ToolBarIconSize) == 20
    assert st.styleHint(QStyle.StyleHint.SH_UnderlineShortcut) == 0
    applied.set_reduced_motion(True)
    assert st.styleHint(QStyle.StyleHint.SH_Widget_Animation_Duration) == 0


def test_apply_updates_app_and_old_window_sheets(applied, qapp, qtbot):
    window = QWidget()
    qtbot.addWidget(window)
    window.setStyleSheet(theme.stylesheet())  # what MainWindow does today
    applied.set_mode("dark")
    assert qapp.palette().color(QPalette.ColorRole.Window).name() == g.COLORS["dark"]["base"]
    assert g.COLORS["dark"]["accent"] in qapp.styleSheet()
    assert window.styleSheet() == qapp.styleSheet()
