"""Keyboard-only walkthrough: Tab through every region of every tab of the demo job.

    QT_QPA_PLATFORM=offscreen python .claude/skills/ui-bug-hunt/keywalk.py
    ... --tab degerler --theme dark --text 150 --size 1366x768

Builds the same invented demo job as tools/screenshots.py, focuses the title tabs, then presses
Tab up to 80 times per tab and prints each stop (region, class, object name, accessible name,
text). Reports: the work area never reached, Tab never coming back to the tabs (a trap), regions
out of reading order (title band, command bar, work area, status bar), and stops that have no
accessible name, text or tooltip. Prints "OK" per tab when clean; exits 1 when anything is found.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

import screenshots  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from evrakci.app import configure_application  # noqa: E402
from evrakci.ui import theme  # noqa: E402
from evrakci.ui.main_window import TAB_IDS  # noqa: E402

REGIONS = ("title band", "command bar", "work area", "status bar")


def label(widget: QWidget) -> str:
    text = getattr(widget, "text", None)
    text = text() if callable(text) else ""
    return (widget.accessibleName() or text or widget.toolTip() or "").strip()


def region_of(window, focus: QWidget) -> int:
    bar = window.command_bars.currentWidget()
    areas = (window.title_band, bar, window.tabs.currentWidget(), window.statusBar())
    return next((i for i, r in enumerate(areas) if r.isAncestorOf(focus) or r is focus), -1)


def walk(window, tab: str, app: QApplication) -> list[str]:
    window.show_tab(tab)
    for _ in range(5):
        app.processEvents()
    window.title_tabs.setFocus(Qt.FocusReason.TabFocusReason)
    problems, seen = [], []
    print(f"\n== {tab}")
    for step in range(1, 81):
        QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
        app.processEvents()
        focus = QApplication.focusWidget()
        if focus is None:
            problems.append(f"{tab}: focus lost at step {step}")
            break
        if focus is window.title_tabs:
            print(f"{step:3} back at the tabs")
            break
        region = region_of(window, focus)
        seen.append(region)
        name = label(focus)
        print(f"{step:3} {REGIONS[region] if region >= 0 else '?':12} "
              f"{type(focus).__name__:22} {focus.objectName() or '-':22} {name or '(no name)'}")
        if not name:
            problems.append(f"{tab}: step {step} {type(focus).__name__} "
                            f"#{focus.objectName()} has no accessible name, text or tooltip")
    else:
        problems.append(f"{tab}: Tab never returned to the tabs in 80 presses (trap?)")
    if 2 not in seen:
        problems.append(f"{tab}: Tab never reached the work area")
    if seen != sorted(seen):
        problems.append(f"{tab}: regions out of reading order: {seen}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tab", choices=TAB_IDS)
    ap.add_argument("--theme", choices=screenshots.THEMES, default="light")
    ap.add_argument("--text", type=int, choices=(100, 115, 130, 150), default=100)
    ap.add_argument("--size", default="1366x768")
    args = ap.parse_args()
    width, height = (int(v) for v in args.size.split("x"))

    screenshots.force_custom_frame()
    app = QApplication.instance() or QApplication(sys.argv)
    configure_application(app)
    theme.manager().set_text_scale(args.text)
    theme.manager().set_mode(args.theme)
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        window = screenshots.build(Path(tmp) / "demo")
        window.resize(width, height)
        window.show()
        window.activateWindow()
        QTest.qWaitForWindowActive(window)
        for tab in [args.tab] if args.tab else TAB_IDS:
            found = walk(window, tab, app)
            print("OK" if not found else "\n".join("PROBLEM " + p for p in found))
            problems += found
        window.close()
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
