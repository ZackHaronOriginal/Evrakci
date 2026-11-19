"""Shortcut audit table, built from the real registry (src/evrakci/ui/actions.py).

    QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py
    ... --tab kontrol          # one tab only
    ... --divergent            # only keys that mean different things on different tabs
    ... --check                # exit 1 on any problem (see below)
    ... --contract FILE.tsv    # also compare docs/ui-goal/shortcut-contract.tsv with the registry

Columns: tab, key, action id, label, local/typing flags, "tests" (test files that carry a
marker for the action id: `@pytest.mark.action("<id>")` or a `# action: <id>` comment) and
"text" (test files that merely mention the id or the Qt.Key name; a hint, never a pass).

--check fails on: validate() problems; a key that is not Turkish-Q safe; a key with different
labels on different tabs that is not documented in the page-specific section of
docs/ui-goal/shortcuts.md (or is documented as MISMATCH); a binding with no marker test;
with --contract, missing, extra or untested contract rows.

Page-specific section format (docs/ui-goal/shortcuts.md), between the two HTML comments:
    <!-- page-specific:start -->
    - `Del`: page-specific: delete the selected thing on each tab
    - `Space`: MISMATCH: reason it looks like a bug
    <!-- page-specific:end -->
Read-only; imports the app, runs no UI.
"""

from __future__ import annotations

import argparse
import csv
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

TESTS_DIR = ROOT / "tests"
SHORTCUTS_DOC = ROOT / "docs" / "ui-goal" / "shortcuts.md"
_QT_NAME = {"Return": "Key_Return", "Enter": "Key_Enter", "Del": "Key_Delete",
            "Esc": "Key_Escape", "Space": "Key_Space", "PgUp": "Key_PageUp",
            "PgDown": "Key_PageDown", "PgDn": "Key_PageDown"}
_MARK_RE = re.compile(r"""mark\.action\(\s*["']([^"']+)["']""")
_COMMENT_RE = re.compile(r"#\s*action:\s*([\w.,\s]+)")
_TURKISH = set("ÇŞĞİÖÜçşğıöü")
_ALIASES = {"return": "enter", "delete": "del", "escape": "esc", "pgdown": "pgdn",
            "pageup": "pgup", "pagedown": "pgdn"}


def portable(key) -> str:
    return actions.key_sequence(key).toString(QKeySequence.SequenceFormat.PortableText)


def test_files(tests_dir: Path = TESTS_DIR) -> list[Path]:
    """Every tests/**/*.py except this script's own test (it holds sample markers)."""
    return sorted(p for p in tests_dir.rglob("*.py") if p.name != "test_audit_shortcuts.py")


def markers(tests_dir: Path = TESTS_DIR) -> dict[str, set[str]]:
    """action id -> test file names that carry a marker or `# action:` comment for it."""
    found: dict[str, set[str]] = defaultdict(set)
    for path in test_files(tests_dir):
        text = path.read_text(encoding="utf-8")
        for m in _MARK_RE.finditer(text):
            found[m.group(1)].add(path.name)
        for m in _COMMENT_RE.finditer(text):
            for action_id in re.split(r"[,\s]+", m.group(1).strip()):
                if action_id:
                    found[action_id].add(path.name)
    return found


def text_mentions(spec: actions.ActionSpec, key: str, tests_dir: Path = TESTS_DIR) -> list[str]:
    """Fallback hint: test files naming the action id or pressing the key's main Qt.Key."""
    main = key.split("+")[-1]
    qt_key = _QT_NAME.get(main, f"Key_{main}")
    found = []
    for path in test_files(tests_dir):
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


def page_specific(doc: Path = SHORTCUTS_DOC) -> dict[str, tuple[str, str]]:
    """key -> (kind, why) from the marked section of shortcuts.md; kind is
    'page-specific' or 'MISMATCH'. Missing section or file gives an empty map."""
    if not doc.exists():
        return {}
    text = doc.read_text(encoding="utf-8")
    m = re.search(r"<!--\s*page-specific:start\s*-->(.*?)<!--\s*page-specific:end\s*-->",
                  text, re.S)
    notes: dict[str, tuple[str, str]] = {}
    for line in (m.group(1) if m else "").splitlines():
        n = re.match(r"\s*[-*]\s*`([^`]+)`\s*:\s*(page-specific|MISMATCH)\s*:\s*(.+?)\s*$", line)
        if n:
            notes[n.group(1)] = (n.group(2), n.group(3))
    return notes


def turkish_q_problems(table) -> list[str]:
    """Keys that break on a Turkish Q keyboard: Turkish letters, the letter I, Ctrl+Alt."""
    out = []
    for key in sorted({k for _, k, _ in table}):
        parts = key.split("+")
        mods, main = set(parts[:-1]), parts[-1] if parts[-1] else "+"
        if any(c in _TURKISH for c in key):
            out.append(f"{key}: Turkish letter in a shortcut")
        if main.upper() == "I" and len(main) == 1:
            out.append(f"{key}: letter I is layout-dependent on Turkish Q")
        if {"Ctrl", "Alt"} <= mods:
            out.append(f"{key}: Ctrl+Alt is AltGr on Turkish keyboards")
    return out


def divergent_problems(divergent, notes) -> list[str]:
    out = []
    for key in sorted(divergent):
        kind = notes.get(key, (None, ""))[0]
        if kind is None:
            out.append(f"{key}: different labels on different tabs, not documented as "
                       "page-specific in docs/ui-goal/shortcuts.md")
        elif kind == "MISMATCH":
            out.append(f"{key}: documented MISMATCH ({notes[key][1]})")
    return out


def _norm_key(key: str) -> str:
    return "+".join(_ALIASES.get(p.strip().lower(), p.strip().lower())
                    for p in key.replace(" ", "").split("+"))


def contract_problems(table, contract: Path, marked: dict[str, set[str]]) -> list[str]:
    """Bindings without a contract row, rows without a binding, rows whose test has no marker."""
    if not contract.exists():
        return [f"contract file {contract} does not exist"]
    with contract.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        lacking = sorted({"tab", "key", "action_id", "test"} - set(reader.fieldnames or ()))
        if lacking:
            return [f"contract {contract.name}: missing columns {lacking}"]
        crows = [r for r in reader if any((v or "").strip() for v in r.values())]
    have = {(r["tab"].strip(), _norm_key(r["key"]), r["action_id"].strip()) for r in crows}
    want = {(t, _norm_key(k), s.id) for t, k, s in table}
    out = [f"no contract row: {t} {k} {a}" for t, k, a in sorted(want - have)]
    out += [f"contract row matches no binding: {t} {k} {a}" for t, k, a in sorted(have - want)]
    for r in crows:
        a, t = r["action_id"].strip(), r["test"].strip()
        label = f"{r['tab'].strip()} {r['key'].strip()} {a}"
        if not t:
            out.append(f"contract row has no test: {label}")
        elif a not in marked:
            out.append(f"contract row test has no action marker for '{a}': {label}")
        if "::" in t and not (ROOT / "tests" / "ui" / t.split("::")[0]).exists() \
                and not (ROOT / "tests" / t.split("::")[0]).exists():
            out.append(f"contract row names a missing test file: {label} -> {t}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tab", choices=list(actions.TABS))
    parser.add_argument("--divergent", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--contract", metavar="TSV", type=Path)
    args = parser.parse_args(argv)

    table = list(rows(args.tab))
    meaning: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for tab, key, spec in table:
        meaning[key][actions.plain_text(spec.text)].add(tab)
    divergent = {k: v for k, v in meaning.items() if len(v) > 1}
    notes = page_specific()
    marked = markers()

    problems = list(actions.validate())
    untested = []
    if not args.divergent:
        print("| tab | key | action id | label | flags | tests | text |")
        print("|---|---|---|---|---|---|---|")
        for tab, key, spec in table:
            flags = ",".join(f for f, on in (("local", spec.local), ("typing", spec.single_key),
                                             ("checkable", spec.checkable)) if on) or "-"
            hits = sorted(marked.get(spec.id, ()))
            if not hits:
                untested.append(f"{tab} {key} {spec.id}")
            print(f"| {tab} | {key} | {spec.id} | {actions.plain_text(spec.text)} | {flags} | "
                  f"{', '.join(hits) or 'NONE'} | {len(text_mentions(spec, key))} |")
    print("\nKeys with a different label on different tabs (must be page-specific in "
          "docs/ui-goal/shortcuts.md, or fixed):")
    for key, labels in sorted(divergent.items()):
        kind = notes.get(key, ("UNDOCUMENTED", ""))[0]
        print(f"  {key} [{kind}]: " + " | ".join(f"{label} [{','.join(sorted(t))}]"
                                                  for label, t in labels.items()))
    div_problems = divergent_problems(divergent, notes)
    tq = turkish_q_problems(table)
    stale = sorted(k for k in notes if k not in divergent and not args.tab)
    print(f"\nvalidate(): {len(problems)} problem(s)")
    for p in problems:
        print("  -", p)
    print(f"Turkish Q: {len(tq)} problem(s)")
    for p in tq:
        print("  -", p)
    print(f"Cross-tab labels: {len(div_problems)} problem(s)")
    for p in div_problems:
        print("  -", p)
    if stale:
        print("Note: documented as page-specific but no longer divergent: " + ", ".join(stale))
    if untested:
        print(f"\n{len(untested)} binding(s) with no action marker test:")
        for u in untested:
            print("  -", u)
    c_problems: list[str] = []
    if args.contract:
        c_problems = contract_problems(list(rows(None)), args.contract, marked)
        print(f"\nContract {args.contract}: {len(c_problems)} problem(s)")
        for p in c_problems:
            print("  -", p)
    bad = problems or tq or div_problems or untested or c_problems
    return 1 if args.check and bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
