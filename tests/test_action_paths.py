"""Every action has a mouse path (menu bar, button or context menu), not only a key.

Runs `audit_shortcuts.py --paths` on the real main window (offscreen, synthetic demo job). A row
that is key-only today is a strict xfail in KEY_ONLY with its reason; fixing it makes the test
pass unexpectedly (XPASS) and strict mode then fails the suite until the entry is removed, so the
list can only shrink. A new key-only action has no entry and fails at once.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "audit_shortcuts", ROOT / ".claude" / "skills" / "shortcut-audit" / "audit_shortcuts.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)

def _pairs() -> list[tuple[str, str]]:
    """Every (tab, action id) of the registry and of LOCAL_KEYS, without starting a window."""
    seen = dict.fromkeys((tab, spec.id) for tab, _key, spec in audit.rows(None))
    seen.update(dict.fromkeys((tab, ids) for tab, _k, ids, *_rest in audit.LOCAL_KEYS))
    return list(seen)


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    """(rows, problems) from the live window, built once for the module."""
    patch = pytest.MonkeyPatch()
    patch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path_factory.mktemp("ui") / "ayarlar.ini"))
    try:
        yield audit.collect_paths_in_new_window()
    finally:
        patch.undo()


@pytest.mark.parametrize(("tab", "action_id"), _pairs(), ids=lambda v: str(v))
def test_action_has_a_mouse_path(paths, tab, action_id):
    table, _problems = paths
    statuses = {status for t, _k, a, *_rest, status in table if (t, a) == (tab, action_id)}
    assert statuses, f"no action-paths row for {tab} {action_id}"
    assert not statuses & {"key-only", "palette-only", "inert"}, (
        f"{tab} {action_id} is reachable only by key or palette: add it to a menu, button "
        "or context menu")


def test_the_tool_itself_finds_nothing_wrong(paths):
    table, problems = paths
    assert problems == []  # BUTTONS entries that match no button, builders that failed
    assert not [row for row in table if not row[-1]]
    assert not [row for row in table if row[-1] == "inert"]


def test_every_contract_row_and_every_action_is_covered(paths):
    table, _problems = paths
    covered = {(row[0], row[2]) for row in table}
    assert set(_pairs()) <= covered
    left = [p for p in audit.paths_problems(table, [], ROOT / "x")
            if p.startswith("contract row has no")]
    assert left == []


def test_exemptions_are_reasoned_and_only_for_navigation_keys():
    for ids, reason in audit.EXEMPT.items():
        assert len(reason.split()) >= 5, ids
    for _tab, _key, ids, _label, exempt in audit.LOCAL_KEYS:
        assert exempt is None or len(exempt.split()) >= 5, ids
    document_ops = {"kontrol.kes", "kontrol.birlestir", "kontrol.sil", "kontrol.saga_dondur",
                    "kontrol.sola_dondur", "kontrol.onayla", "sablonlar.kaydir",
                    "sablonlar.kaydir_1mm", "app.yenile"}
    assert not document_ops & set(audit.EXEMPT)


def test_committed_tsv_matches_the_live_window(paths):
    table, _problems = paths
    out = audit.PATHS_TSV
    assert out.exists(), "run audit_shortcuts.py --paths and commit docs/ui-goal/action-paths.tsv"
    assert audit._status_map(out.read_text(encoding="utf-8")) == audit._status_map(
        audit._tsv(table))


def test_a_new_key_only_action_is_reported():
    row = ("kontrol", "Ctrl+J", "kontrol.zzz", "Zzz", "", "", "", "yes", "key-only")
    problems = audit.paths_problems([row], [], ROOT / "x", ROOT / "does-not-exist.tsv")
    assert any("kontrol.zzz" in p for p in problems)
    ok = row[:-1] + ("ok",)
    assert audit.paths_problems([ok], [], ROOT / "x", ROOT / "does-not-exist.tsv") == []
