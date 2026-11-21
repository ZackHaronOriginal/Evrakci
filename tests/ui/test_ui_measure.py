"""tools/ui_measure.py: it flags a deliberately broken widget on each planted defect, passes a
correct one, reads a well-formed rules.json and gives the same rows twice (synthetic data only)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

TOOLS = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(TOOLS))
import ui_measure as um  # noqa: E402

from evrakci.ui import motion, theme  # noqa: E402
from evrakci.ui.chrome import CaptionButton  # noqa: E402


@pytest.fixture
def light_100(qapp):
    manager = theme.manager()
    before = (manager.mode(), manager.text_scale())
    manager.set_text_scale(100)
    manager.set_mode("light")
    # The probe widgets test the tool, not the app's theme: an app-wide stylesheet left by an
    # earlier test overrides their font and palette (they then pass or fail for the wrong
    # reason in the full suite), so they run without it and it is restored afterwards.
    sheet, font, palette = qapp.styleSheet(), qapp.font(), qapp.palette()
    qapp.setStyleSheet("")
    # the same holds for the palette (placeholder colour, B-092): start from the style's own
    qapp.setPalette(qapp.style().standardPalette())
    yield qapp
    qapp.setStyleSheet(sheet)
    qapp.setFont(font)
    qapp.setPalette(palette)
    manager.set_text_scale(before[1])
    manager.set_mode(before[0])


def _icon() -> QIcon:
    pixmap = QPixmap(16, 16)
    pixmap.fill(QColor("#000000"))
    return QIcon(pixmap)


def _panel(qapp: QApplication, *, broken: bool) -> QWidget:
    """A white panel with a text label, a text button and an icon-only button."""
    root = QWidget()
    palette = root.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    root.setPalette(palette)
    root.setAutoFillBackground(True)
    layout = QVBoxLayout(root)
    label = QLabel("Örnek metin Sicil No 4819")
    font = QFont(label.font())
    font.setPixelSize(11 if broken else 15)
    label.setFont(font)
    ink = QPalette(label.palette())
    ink.setColor(QPalette.ColorRole.WindowText, QColor("#b8b8b8" if broken else "#16201a"))
    label.setPalette(ink)
    label.setObjectName("probeLabel")
    icon_button = QPushButton()
    icon_button.setObjectName("probeIcon")
    icon_button.setIcon(_icon())
    side = 20 if broken else 36
    icon_button.setFixedSize(side, side)
    if not broken:
        icon_button.setToolTip("Sil")
    layout.addWidget(label)
    layout.addWidget(icon_button)
    root.resize(420, 160)
    root.show()
    for _ in range(5):
        qapp.processEvents()
    return root


def _results(qapp: QApplication, root: QWidget) -> dict[tuple[str, str], str]:
    rules = um.load_rules()
    ctx = um.make_ctx(root, "light", 100, (420, 160), rules)
    ctx.window_checks = False
    rows = um.measure_tree(qapp, ctx, rules, "probe")
    return {(row[4], row[6]): row[9] for row in rows}


def _row(qapp: QApplication, root: QWidget, widget: str, rule: str):
    rules = um.load_rules()
    ctx = um.make_ctx(root, "light", 100, (420, 160), rules)
    ctx.window_checks = False
    rows = um.measure_tree(qapp, ctx, rules, "probe")
    return [r for r in rows if r[4] == widget and r[6] == rule]


def test_broken_widget_is_flagged_on_all_four_defects(light_100):
    root = _panel(light_100, broken=True)
    found = _results(light_100, root)
    root.close()
    assert found[("probeLabel", "DEC-TYP-01")] == "fail"  # 11 px text
    assert found[("probeLabel", "DEC-CON-01")] == "fail"  # about 2:1
    assert found[("probeIcon", "AUD-A11Y-01")] == "fail"  # focusable, no name, text or tooltip
    assert found[("probeIcon", "AUD-HIT-01")] == "fail"  # 20x20


def test_correct_widget_passes_the_same_rules(light_100):
    root = _panel(light_100, broken=False)
    found = _results(light_100, root)
    root.close()
    assert found[("probeLabel", "DEC-TYP-01")] == "pass"
    assert found[("probeLabel", "DEC-CON-01")] == "pass"
    assert found[("probeIcon", "AUD-A11Y-01")] == "pass"
    assert found[("probeIcon", "AUD-HIT-01")] == "pass"
    assert found[("probeIcon", "HIG-CTL-06")] == "pass"


def test_rules_json_is_well_formed():
    rules = um.load_rules()
    ids = [r["id"] for r in rules]
    assert len(ids) == len(set(ids)) > 90
    for rule in rules:
        assert rule["id"] and rule["source"] and rule["severity"] in {"S1", "S2", "S3", "S4"}
        assert rule["enforced"] is False
        assert isinstance(rule["enforceable"], bool)
        assert rule["measure"] == "manual" or rule["measure"].startswith("tool:")
    hig = [r for r in rules if r["id"].startswith("HIG-")]
    assert len(hig) == 78
    assert all(r["source"].startswith("https://developer.apple.com/") for r in hig)
    assert sum(1 for r in hig if r["verified"]) == 77
    owners = um.measured_rules(rules)
    assert set(owners) == set(um.CHECKS)  # every check has exactly one rule that owns its rows
    shared = {r["rows_under"] for r in rules if r.get("rows_under")}
    assert shared <= set(ids)


def test_two_runs_give_identical_rows(light_100, tmp_path):
    rules = um.load_rules()
    first = um.run(light_100, tmp_path / "a", rules, tabs=("rehber",), themes=("light",),
                   texts=(100,), sizes=((1366, 768),))
    second = um.run(light_100, tmp_path / "b", rules, tabs=("rehber",), themes=("light",),
                    texts=(100,), sizes=((1366, 768),))
    assert len(first) > 100
    assert first == second
    assert um.to_tsv(first) == um.to_tsv(second)


def _extras(qapp: QApplication) -> QWidget:
    """Widgets for the false-fail fixes: a stacked page with declared margins, a box with real
    off-grid margins, a pill and a square-ish corner, placeholder text, a caption button."""
    root = QWidget()
    palette = root.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#ffffff"))
    root.setPalette(palette)
    root.setAutoFillBackground(True)
    layout = QVBoxLayout(root)
    stack = QStackedWidget()
    stack.setObjectName("probeStack")
    stack.layout().setContentsMargins(9, 9, 9, 9)  # a stacked layout never applies these
    stack.layout().setSpacing(5)
    stack.addWidget(QLabel("Sayfa"))
    box = QWidget()
    box.setObjectName("probeBox")
    inner = QHBoxLayout(box)
    inner.setContentsMargins(9, 9, 9, 9)  # applied: really off the 4 px grid
    inner.setSpacing(5)
    inner.addWidget(QLabel("a"))
    inner.addWidget(QLabel("b"))
    pill = QPushButton()
    pill.setObjectName("probePill")
    pill.setFixedSize(20, 20)
    pill.setStyleSheet("border-radius: 10px;")  # a circle: radius is half the side
    corner = QPushButton()
    corner.setObjectName("probeCorner")
    corner.setFixedSize(40, 40)
    corner.setStyleSheet("border-radius: 5px;")  # a corner radius off the scale
    field = QLineEdit()
    field.setObjectName("probeField")
    field.setPlaceholderText("Ara")
    ink = QPalette(field.palette())
    ink.setColor(QPalette.ColorRole.PlaceholderText, QColor("#707070"))  # about 5:1 on white
    field.setPalette(ink)
    grey = QLabel("Ara")  # the same colour as body text: needs 7:1
    grey.setObjectName("probeGrey")
    grey_ink = QPalette(grey.palette())
    grey_ink.setColor(QPalette.ColorRole.WindowText, QColor("#707070"))
    grey.setPalette(grey_ink)
    caption = CaptionButton("min", "Küçült")
    caption.setObjectName("probeCaption")
    stuck = QPushButton("Sabit")
    stuck.setObjectName("probeNoFocus")
    stuck.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    for widget in (stack, box, pill, corner, field, grey, caption, stuck):
        layout.addWidget(widget)
    root.resize(420, 420)
    root.show()
    for _ in range(5):
        qapp.processEvents()
    return root


def test_stacked_page_pill_placeholder_and_caption_button(light_100):
    root = _extras(light_100)
    found = _results(light_100, root)
    root.close()
    # a stacked layout does not apply its margins or spacing: no verdict, so no false fail
    assert ("probeStack", "DEC-LAY-01") not in found
    assert ("probeStack", "DEC-LAY-02") not in found
    assert found[("probeBox", "DEC-LAY-01")] == "fail"  # the same numbers on a real layout
    assert found[("probeBox", "DEC-LAY-02")] == "fail"
    assert found[("probePill", "DEC-LAY-03")] == "pass"  # radius = half the side
    assert found[("probeCorner", "DEC-LAY-03")] == "fail"  # 5 px on a 40 px box
    # B-092: in the full CI run only this probe fails; the message names the measured value
    assert found[("probeField", "DEC-CON-02")] == "pass", (  # placeholder: secondary tier, 4.5:1
        _row(light_100, root, "probeField", "DEC-CON-02"),
        light_100.palette().color(QPalette.ColorRole.PlaceholderText).name(),
        light_100.palette().color(QPalette.ColorRole.Base).name(),
        light_100.styleSheet()[:200])
    assert ("probeField", "DEC-CON-01") not in found
    assert found[("probeGrey", "DEC-CON-01")] == "fail"  # same colour as body text: 7:1
    assert found[("probeCaption", "AUD-KBD-01")] == "skip"  # exempt: Alt+Space window menu
    assert found[("probeNoFocus", "AUD-KBD-01")] == "fail"  # any other NoFocus button fails


def test_motion_duration_tokens():
    """DEC-MOT-01 (D7) is a unit check: animations are deleted when they stop, so the window
    never holds one for the tool to read."""
    assert {int(d) for d in motion.Duration} == {0, 80, 120, 180, 240}
    assert motion.MAX_DURATION == 240
    for bad in (1, 100, 200, 300, 500):
        with pytest.raises(ValueError):
            motion.duration(bad)
