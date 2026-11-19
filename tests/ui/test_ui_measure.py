"""tools/ui_measure.py: it flags a deliberately broken widget on each planted defect, passes a
correct one, reads a well-formed rules.json and gives the same rows twice (synthetic data only)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

TOOLS = Path(__file__).resolve().parents[2] / "tools"
sys.path.insert(0, str(TOOLS))
import ui_measure as um  # noqa: E402

from evrakci.ui import theme  # noqa: E402


@pytest.fixture
def light_100(qapp):
    manager = theme.manager()
    before = (manager.mode(), manager.text_scale())
    manager.set_text_scale(100)
    manager.set_mode("light")
    yield qapp
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
