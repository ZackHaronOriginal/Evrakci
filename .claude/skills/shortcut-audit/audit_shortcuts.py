"""Shortcut audit table, built from the real registry (src/evrakci/ui/actions.py).

    QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py
    ... --tab kontrol          # one tab only
    ... --divergent            # only keys that mean different things on different tabs
    ... --check                # exit 1 when validate() fails or a key has no test mention

Columns: tab, key, action id, label, local/typing flags, and the test files whose text
mentions the action id or the key as a Qt.Key name. Read-only; imports the app, runs no UI.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from PySide6.QtGui import QKeySequence  # noqa: E402

from evrakci.ui import actions  # noqa: E402

TESTS = sorted((ROOT / "tests" / "ui").glob("*.py"))
_QT_NAME = {"Return": "Key_Return", "Enter": "Key_Enter", "Del": "Key_Delete",
            "Esc": "Key_Escape", "Space": "Key_Space", "PgUp": "Key_PageUp",
            "PgDown": "Key_PageDown", "PgDn": "Key_PageDown"}


def portable(key) -> str:
    return actions.key_sequence(key).toString(QKeySequence.SequenceFormat.PortableText)


def tests_for(spec: actions.ActionSpec, key: str) -> list[str]:
    """Test files that name the action id, or press the key's main Qt.Key."""
    main = key.split("+")[-1]
    qt_key = _QT_NAME.get(main, f"Key_{main}")
    found = []
    for path in TESTS:
        text = path.read_text(encoding="utf-8")
        if spec.id in text or re.search(rf"\b{re.escape(qt_key)}\b", text):
            found.append(path.name)
    return found


def rows(tab_filter: str | None):
    for tab in actions.TABS:
        if tab_filter and tab != tab_filter:
            continue
        for spec in actions.SPECS:
            if not actions._active(spec, tab):
                continue
            for key in spec.shortcuts:
                yield tab, portable(key), spec


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tab", choices=list(actions.TABS))
    parser.add_argument("--divergent", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    table = list(rows(args.tab))
    meaning: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for tab, key, spec in table:
        meaning[key][actions.plain_text(spec.text)].add(tab)
    divergent = {k: v for k, v in meaning.items() if len(v) > 1}

    problems = list(actions.validate())
    untested = []
    if not args.divergent:
        print("| tab | key | action id | label | flags | tests |")
        print("|---|---|---|---|---|---|")
        for tab, key, spec in table:
            flags = ",".join(f for f, on in (("local", spec.local), ("typing", spec.single_key),
                                             ("checkable", spec.checkable)) if on) or "-"
            hits = tests_for(spec, key)
            if not hits:
                untested.append(f"{tab} {key} {spec.id}")
            print(f"| {tab} | {key} | {spec.id} | {actions.plain_text(spec.text)} | {flags} | "
                  f"{', '.join(hits) or 'NONE'} |")
    print("\nKeys with a different label on different tabs (must be documented as page-specific "
          "in docs/ui-goal/shortcuts.md, or fixed):")
    for key, labels in sorted(divergent.items()):
        print(f"  {key}: " + " | ".join(f"{label} [{','.join(sorted(t))}]"
                                        for label, t in labels.items()))
    print(f"\nvalidate(): {len(problems)} problem(s)")
    for p in problems:
        print("  -", p)
    if untested:
        print(f"\n{len(untested)} binding(s) no test file mentions by id or key:")
        for u in untested:
            print("  -", u)
    return 1 if args.check and (problems or untested) else 0


if __name__ == "__main__":
    raise SystemExit(main())
