"""tools/ui_measure.py: it flags a deliberately broken widget on each planted defect, passes a
correct one, reads a well-formed rules.json and gives the same rows twice (synthetic data only)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt, QTimer
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
    _results.rows = {(row[4], row[6]): row for row in rows}  # the whole row, for messages
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


ENFORCED_IDS = {"DEC-TYP-01", "DEC-TYP-02", "DEC-TYP-03", "DEC-CON-01", "DEC-CON-02",
                "AUD-HIT-01", "AUD-HIT-02", "AUD-HIT-03", "AUD-A11Y-01", "DEC-FOC-01"}


def _row(rule, widget="w", result="fail"):
    return ("kontrol", "light", "1366x768", "100", widget, "QWidget", rule, "v", "l", result, "S3")


def test_enforce_fails_on_a_new_violation_and_tolerates_known_fails():
    rules = um.load_rules()
    known = {("AUD-HIT-02", "statusBar/ZoomSlider/QToolButton[0]")}
    today = [_row("AUD-HIT-02", "statusBar/ZoomSlider/QToolButton[0]"),
             _row("DEC-TYP-01", "ok", "pass"), _row("DEC-LAY-01", "grid")]  # LAY is report-only
    assert um.enforced_failures(today, rules, known) == 0
    assert um.enforced_failures(today, rules) == 1  # without the list the same row fails
    for rule in ("DEC-TYP-01", "DEC-CON-01", "AUD-A11Y-01", "DEC-FOC-01", "AUD-HIT-01"):
        assert um.enforced_failures(today + [_row(rule, "new")], rules, known) == 1
    # a known-fail entry is for that widget only
    assert um.enforced_failures([_row("AUD-HIT-02", "statusBar/Other")], rules, known) == 1
    assert um.stale_known_fails([_row("AUD-HIT-01", "x")], known) == sorted(known)


def test_known_fails_file_is_dated_and_every_row_has_a_reason():
    path = um.KNOWN_FAILS_PATH
    assert "2026-11-26" in path.read_text(encoding="utf-8").splitlines()[0]
    rows = [ln.split("\t") for ln in path.read_text(encoding="utf-8").splitlines()
            if ln and not ln.startswith("#") and not ln.startswith("rule\t")]
    # rule, widget, reason (every case) or rule, widget, theme, size, text, reason (one case)
    assert rows and all(len(r) in (3, 6) and r[-1] for r in rows)
    # a waiver for a case seen on one machine names the case (B-104, R-O-5): never every case
    assert all(len(r) == 6 and r[2] in ("light", "dark", "hc") and r[4] in ("100", "150")
               for r in rows if r[0] == "DEC-CON-01")
    assert {r[0] for r in rows} <= ENFORCED_IDS
    assert len(um.load_known_fails(path)) == len(rows)
    assert um.load_known_fails(path / "missing") == set()


def test_narrow_known_fail_covers_only_its_theme_size_and_text(tmp_path):
    path = tmp_path / "known.tsv"
    path.write_text("rule\twidget\treason\nDEC-CON-01\tw\tlight\t1366x768\t100\tCI\n"
                    "AUD-HIT-02\tz\tevery case\n", encoding="utf-8")
    known = um.load_known_fails(path)
    assert known == {("DEC-CON-01", "w", "light", "1366x768", "100"), ("AUD-HIT-02", "z")}
    rules = um.load_rules()

    def row(theme_, size="1366x768", text="100", widget="w", rule="DEC-CON-01"):
        return ("tab", theme_, size, text, widget, "QWidget", rule, "1.01", "7", "fail", "S3")
    assert um.enforced_failures([row("light")], rules, known) == 0
    for other in (row("dark"), row("light", "1920x1080"), row("light", text="150"),
                  row("light", widget="other")):
        assert um.enforced_failures([other], rules, known) == 1
    assert um.enforced_failures([row("hc", rule="AUD-HIT-02", widget="z")], rules, known) == 0
    # stale: the narrow entry is stale unless that very case fails
    assert ("DEC-CON-01", "w", "light", "1366x768", "100") in um.stale_known_fails(
        [row("dark")], known)
    assert ("DEC-CON-01", "w", "light", "1366x768", "100") not in um.stale_known_fails(
        [row("light")], known)


def test_unpainted_rows_are_the_contrast_fails_near_one():
    near = _row("DEC-CON-01")[:7] + ("1.01", "7", "fail", "S3")
    low = _row("DEC-CON-01")[:7] + ("6.91", "7", "fail", "S3")
    other = _row("DEC-TYP-01")[:7] + ("1.01", "7", "fail", "S3")
    assert um.unpainted([near, low, other, _row("DEC-CON-01", result="pass")]) == [near]


def test_measure_waits_for_text_that_paints_late(light_100):
    """B-104: text that is not painted yet (a worker's result, a late layout pass) reads about
    1:1 and failed only on a slow machine; the tool waits until the picture is settled and
    measures again."""
    qapp = light_100
    root = QWidget()
    root.setObjectName("late")
    layout = QVBoxLayout(root)
    label = QLabel("Belge 3")
    label.setObjectName("lateLabel")
    ink = QPalette(label.palette())
    ink.setColor(QPalette.ColorRole.WindowText, QColor("#fefefe"))  # as if not painted yet
    label.setPalette(ink)
    layout.addWidget(label)
    root.resize(300, 120)
    root.show()

    def paint_text() -> None:
        ink.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
        label.setPalette(ink)

    early = um.measure_tree(qapp, um.make_ctx(root, "light", 100, (300, 120), um.load_rules()),
                            um.load_rules(), "late")
    assert um.unpainted(early)  # the probe reads as unpainted before the late change
    QTimer.singleShot(700, paint_text)
    rules = um.load_rules()
    rows = um.measure_settled(qapp, root, "light", 100, (300, 120), rules, "late")
    mine = [r for r in rows if r[4].endswith("lateLabel") and r[6] in ("DEC-CON-01", "DEC-CON-02")]
    assert mine and all(r[9] == "pass" for r in mine), mine
    assert not um.unpainted(rows)


def test_settled_reports_a_picture_that_never_stops_changing(light_100):
    qapp = light_100
    root = QWidget()
    label = QLabel("0")
    QVBoxLayout(root).addWidget(label)
    root.resize(200, 80)
    root.show()
    count = iter(range(1, 10**6))
    timer = QTimer(root)
    timer.timeout.connect(lambda: label.setText(str(next(count))))
    timer.start(10)
    assert um.settled(qapp, root, limit_ms=400) is False
    timer.stop()
    assert um.settled(qapp, root, limit_ms=1000) is True


def test_canvas_and_reader_exemptions():
    assert um.exempt_row("AUD-A11Y-01", "a/PageCanvas/QWidget")
    assert um.exempt_row("DEC-FOC-01", "a/PageCanvas/QWidget")
    assert not um.exempt_row("AUD-HIT-01", "a/PageCanvas/QWidget")
    assert not um.exempt_row("AUD-A11Y-01", "a/QWidget")
    assert set(um.WINDOW_SCROLL_EXEMPT) == {"Reader", "PageCanvas"}


def test_rules_json_is_well_formed():
    rules = um.load_rules()
    ids = [r["id"] for r in rules]
    assert len(ids) == len(set(ids)) > 90
    for rule in rules:
        assert rule["id"] and rule["source"] and rule["severity"] in {"S1", "S2", "S3", "S4"}
        # only the owner-approved rule families (Q-03) are enforced, and only if enforceable
        assert rule["enforced"] is (rule["id"] in ENFORCED_IDS)
        if rule["enforced"]:
            assert rule["enforceable"] and rule["measure"].startswith("tool:")
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
    # read-only: no blinking text cursor, which the pixel colour reading can take for the text
    # colour when the grab catches it (B-092: failed in CI only, by the blink phase)
    field.setReadOnly(True)
    ink = QPalette(field.palette())
    # about 6.2:1 on white: a margin over 4.5, because thin anti-aliased glyphs (the app font an
    # earlier module leaves) read lighter than their colour (B-092: #707070 read as 4.12 in CI)
    ink.setColor(QPalette.ColorRole.PlaceholderText, QColor("#616161"))
    ink.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
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
    assert found[("probeField", "DEC-CON-02")] == "pass", (  # placeholder: secondary, 4.5:1
        " | ".join(map(str, (_results.rows.get(("probeField", "DEC-CON-02")) or ())[7:])))
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


def test_a_failing_contrast_row_saves_its_pixels_for_comparison(qtbot, tmp_path, monkeypatch):
    """--crops (B-104): the pixels behind a failing contrast row are written as a PNG."""
    from types import SimpleNamespace

    import ui_measure
    from PySide6.QtWidgets import QLabel, QWidget

    root = QWidget()
    qtbot.addWidget(root)
    root.resize(200, 80)
    label = QLabel("Belge", root)
    label.setGeometry(10, 10, 100, 30)
    root.show()
    image = root.grab().toImage()
    ctx = SimpleNamespace(root=root, theme="light", size=(1366, 768), text=100, image=image)
    monkeypatch.setattr(ui_measure, "CROPS", tmp_path / "crops")
    ui_measure.save_crop(ctx, label, "x/QLabel[0]", "DEC-CON-01", "1.01")
    files = list((tmp_path / "crops").glob("*.png"))
    assert len(files) == 1 and files[0].name.startswith("DEC-CON-01_light_1366x768_100_1.01_")
    monkeypatch.setattr(ui_measure, "CROPS", None)
    ui_measure.save_crop(ctx, label, "x/QLabel[0]", "DEC-CON-01", "1.01")  # off: nothing more
    assert len(list((tmp_path / "crops").glob("*.png"))) == 1
