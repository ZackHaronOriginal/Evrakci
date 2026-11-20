"""audit_shortcuts.py: marker matching, cross-tab label rule, contract check (real registry)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "audit_shortcuts", ROOT / ".claude" / "skills" / "shortcut-audit" / "audit_shortcuts.py")
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)


def _tests_dir(tmp_path, body):
    d = tmp_path / "tests" / "ui"
    d.mkdir(parents=True)
    (d / "test_x.py").write_text(body, encoding="utf-8")
    return tmp_path / "tests"


def test_markers_read_decorator_and_comment(tmp_path):
    d = _tests_dir(tmp_path, '@pytest.mark.action("kontrol.kes")\ndef test_a():\n    pass\n'
                             "# action: app.git, app.undo\n")
    found = audit.markers(d)
    assert set(found) == {"kontrol.kes", "app.git", "app.undo"}
    assert found["kontrol.kes"] == {"test_x.py"}


def test_free_text_is_not_a_marker(tmp_path):
    d = _tests_dir(tmp_path, '"""mentions kontrol.kes and Key_Delete"""\n')
    assert audit.markers(d) == {}
    assert audit.text_mentions(audit.actions.spec("kontrol.kes"), "K", d) == ["test_x.py"]


def test_page_specific_section_parses(tmp_path):
    doc = tmp_path / "s.md"
    doc.write_text("x\n<!-- page-specific:start -->\n- `Del`: page-specific: delete\n"
                   "- `Space`: MISMATCH: odd\n<!-- page-specific:end -->\n", encoding="utf-8")
    assert audit.page_specific(doc) == {"Del": ("page-specific", "delete"),
                                        "Space": ("MISMATCH", "odd")}


def test_real_doc_documents_every_divergent_key():
    table = list(audit.rows(None))
    meaning = {}
    for _tab, key, spec in table:
        meaning.setdefault(key, set()).add(audit.actions.plain_text(spec.text))
    divergent = {k: v for k, v in meaning.items() if len(v) > 1}
    assert len(divergent) == 18  # K, N, Shift+N joined; R joined (Okunana dön on Değerler)
    assert audit.divergent_problems(divergent, audit.page_specific()) == []


def test_undocumented_and_mismatch_keys_are_problems():
    div = {"Del": {"a", "b"}, "F2": {"a", "b"}}
    notes = {"F2": ("MISMATCH", "bug")}
    out = audit.divergent_problems(div, notes)
    assert len(out) == 2 and "not documented" in out[0] and "MISMATCH" in out[1]


def test_registry_keys_are_turkish_q_safe():
    assert audit.turkish_q_problems(list(audit.rows(None))) == []
    bad = audit.turkish_q_problems([("t", "Ctrl+Alt+K", None), ("t", "I", None), ("t", "Ö", None)])
    assert len(bad) == 3


def test_contract_reports_missing_rows_and_untested(tmp_path):
    table = list(audit.rows(None))
    tab, key, spec = table[0]
    tsv = tmp_path / "c.tsv"
    tsv.write_text("tab\tkey\taction_id\ttest\n"
                   f"{tab}\t{key}\t{spec.id}\ttest_shortcut_contract.py::{spec.id}[{tab}]\n"
                   "kontrol\tCtrl+9\tbogus.id\t\n", encoding="utf-8")
    out = audit.contract_problems(table, tsv, {})
    assert any("no contract row" in p for p in out)
    assert any("matches no binding" in p for p in out)
    assert any("no action marker" in p and spec.id in p for p in out)
    assert any("has no test" in p for p in out)
    assert audit.contract_problems(table, tmp_path / "none.tsv", {})[0].endswith("does not exist")
