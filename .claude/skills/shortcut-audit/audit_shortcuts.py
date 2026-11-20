"""Shortcut audit table, built from the real registry (src/evrakci/ui/actions.py).

    QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py
    ... --tab kontrol          # one tab only
    ... --divergent            # only keys that mean different things on different tabs
    ... --check                # exit 1 on any problem (see below)
    ... --contract FILE.tsv    # also compare docs/ui-goal/shortcut-contract.tsv with the registry
    ... --paths                # write docs/ui-goal/action-paths.tsv: where each action is reachable
    ... --paths --check        # same, writes nothing, exit 1 on a key-only action or a stale file

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
Without --paths it is read-only, imports the app and runs no UI. --paths starts the real main
window offscreen with the synthetic demo job (tools/screenshots.py build) and is described below.

--paths: every command must also have a mouse path, never only a key. For each tab it collects,
per registry action and per contract row, where the action can be reached without its key:
menu bar (every QMenuBar menu walked, submenus too), buttons (command bar, side panels,
"Diğer" menus; a QAction identity, or the BUTTONS table below for buttons that call a slot) and
context menus (each tab's builders run on a representative target with QMenu.popup/exec patched
to capture the menu). The command palette is listed but does not count: it is a keyboard path.
Status: ok, key-only (a key, no mouse path), palette-only (no key and no mouse path), or
exempt:<reason> from EXEMPT / LOCAL_KEYS (pure navigation keys; every entry has a reason).
--paths --check fails on key-only / palette-only rows (except PROPOSED ones, which wait for the
owner in docs/ui-goal/audit/<tab>-proposals.md), on BUTTONS entries that match no button
(the table cannot rot), on contract rows the output does not cover, and on a committed TSV whose
statuses differ from the live window.
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


# -- --paths: mouse paths of every action ------------------------------------------------------
PATHS_TSV = ROOT / "docs" / "ui-goal" / "action-paths.tsv"
CONTRACT_TSV = ROOT / "docs" / "ui-goal" / "shortcut-contract.tsv"
PATH_COLUMNS = ("tab", "key", "action_id", "label", "menu_path", "button", "context_menu",
                "palette", "status")

# Keys that are universal navigation or editing behaviour, so no menu entry or button is needed.
# Anything that performs a document or job operation never goes here. One reason per action id.
EXEMPT = {
    "app.sonraki_bolge": "F6 moves focus between regions like Tab; the mouse clicks to focus",
    "app.onceki_bolge": "Shift+F6 moves focus between regions like Shift+Tab; the mouse clicks",
    "kontrol.sayfa": "Left/Right arrows step through the page list; a click picks a page",
    "kontrol.ilk_son": "Home/End jump inside the page list; the scroll bar and a click do it",
    "kontrol.ekran": "PgUp/PgDn scroll the page list; the scroll bar and the wheel do it",
    "kontrol.secimi_genislet": "Shift+arrows extend a list selection; click and Shift+click do it",
    "sablonlar.el": "holding Space pans the sheet view; scroll bars and the wheel pan it",
    "degerler.sonraki_deger": "Tab/Shift+Tab move between table cells; a click picks a cell",
}

# Keys read in keyPressEvent overrides that are not in SPECS: (tab, key, id, label, reason).
# `exempt` is a reason (universal navigation, never an operation); `via` is the text of a context
# menu or button action that gives the same result with the mouse (checked against the live
# window); with neither, the row is key-only.
LOCAL_KEYS = (
    ("sablonlar", "Ctrl+Arrows", "local.kutu_boyutu", "Resize the selected box (sablon_canvas.py)",
     None, None),
    ("sablonlar", "Enter", "local.kutu_yerlestir", "Place a default box while drawing "
     "(sablon_canvas.py)", None, None),
    ("sablonlar", "Esc", "local.cizimi_birak", "Leave drawing / deselect the box (sablon.py, "
     "sablon_canvas.py)", "Esc dismisses the current mode like Esc in a dialog; a click on the "
     "empty sheet deselects", None),
    ("degerler", "Enter", "local.tablo_enter", "Enter in the values table (degerler_table.py)",
     "Enter in a field or table confirms the cell; the Onayla button is the mouse path", None),
    ("disa_aktar", "Ctrl+C", "local.dosya_adi_kopyala", "Copy the file names "
     "(disa_aktar_table.py)", None, "Dosya adını kopyala"),
    ("yukle", "Esc", "local.liste_kapat", "End the job search list (yukle.py, yukle_parts.py)",
     "Esc clears or leaves a field", None),
    ("kontrol", "Esc / Space", "local.lupa_kapat", "Close the loupe (loupe.py)", None, "Kapat"),
    ("kontrol", "Arrows / Home / End / PgUp / PgDn", "local.lupa_gezin", "Page through the "
     "loupe (loupe.py)", "arrow, Home/End and PgUp/PgDn navigation inside one view", None),
)

# Key-only rows that need a new label or a look change, so they wait for the owner: the check
# reports them but does not fail on them. Each names its proposal; remove the entry when fixed.
PROPOSED = {
    ("sablonlar", "sablonlar.kaydir"): "docs/ui-goal/audit/sablonlar-proposals.md",
    ("sablonlar", "sablonlar.kaydir_1mm"): "docs/ui-goal/audit/sablonlar-proposals.md",
    ("sablonlar", "local.kutu_boyutu"): "docs/ui-goal/audit/sablonlar-proposals.md",
    ("sablonlar", "local.kutu_yerlestir"): "docs/ui-goal/audit/sablonlar-proposals.md",
}

# Buttons that call a slot instead of triggering a QAction, so no identity links them to the
# action: (tab, action id, widget class name, text start of its text / tooltip / row label).
# The tool fails when an entry matches no button on that tab, so the table cannot go stale.
BUTTONS = (
    ("yukle", "app.yeni_is", "QPushButton", "Yeni iş oluştur"),
    ("yukle", "app.dosya_ekle", "QPushButton", "Dosya ekle"),
    ("yukle", "app.sekme.kontrol", "GapButton", "Kontrol'e geç"),
    ("yukle", "app.isi_kapat", "GapButton", "İşi kapat"),
    ("kontrol", "kontrol.onayla", "GapButton", "Belgeyi onayla"),
    ("kontrol", "kontrol.degerlerde_ac", "GapButton", "Değerlerde aç"),
    ("kontrol", "kontrol.sablon", "ActionRow", "Şablon uygula"),
    ("kontrol", "kontrol.filtre", "ActionRow", "Filtre uygula"),
    ("sablonlar", "app.kaydet", "QPushButton", "Şablonu kaydet"),
    ("sablonlar", "sablonlar.degisken_ekle", "QToolButton", "Değişken ekle"),
    ("sablonlar", "app.sekme.yukle", "QPushButton", "Yükle'ye git"),
    ("sablonlar", "app.sekme.rehber", "QPushButton", "Rehber'i aç"),
    ("degerler", "degerler.durdur", "QPushButton", "Okumayı durdur"),
    ("degerler", "degerler.oku", "QPushButton", "Değerleri oku"),
    ("degerler", "degerler.eksikleri_oku", "QPushButton", "Yalnızca eksikleri oku"),
    ("degerler", "app.uzaklastir", "QToolButton", "Uzaklaştır"),
    ("degerler", "app.yakinlastir", "QToolButton", "Yakınlaştır"),
    ("degerler", "degerler.tum_sayfa", "QToolButton", "Sayfanın tamamı"),
    ("degerler", "degerler.onayla", "_OnceButton", "Onayla ve sonrakine geç"),
    ("degerler", "degerler.elle_yaz", "_OnceButton", "Elle yaz"),
    ("degerler", "degerler.varyant", "_OnceButton", "Yeni kutu çiz"),
    ("degerler", "app.sekme.yukle", "QPushButton", "Yükle'ye git"),
    ("disa_aktar", "app.disa_aktar", "PartsButton", "Dışa aktar"),
    ("disa_aktar", "disa_aktar.index_ac", "PartsButton", "index.xlsx'i aç"),
    ("disa_aktar", "disa_aktar.gezginde_goster", "PartsButton", "Dosya Gezgini'nde göster"),
    ("disa_aktar", "app.sekme.degerler", "QPushButton", "Değerler'e git"),
    ("disa_aktar", "app.sekme.yukle", "PartsButton", "Yükle'ye git"),
    ("rehber", "app.onceki_sonuc", "QToolButton", "Önceki sonuç"),
    ("rehber", "app.sonraki_sonuc", "QToolButton", "Sonraki sonuç"),
    ("rehber", "rehber.yazdir", "PartsButton", "Yazdır"),
    ("rehber", "rehber.aramayi_temizle", "QToolButton", "Aramayı temizle"),
    ("rehber", "app.bul", "QToolButton", "Ara"),
    ("rehber", "app.kisayollar", "PartsButton", "Kısayolları göster"),
)


def _build_window():
    """The real main window with the synthetic demo job (tools/screenshots.py), offscreen."""
    import tempfile

    sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests")]
    import screenshots
    from PySide6.QtWidgets import QApplication

    from evrakci.app import configure_application

    app = QApplication.instance() or QApplication(sys.argv[:1])
    configure_application(app)
    tmp = tempfile.TemporaryDirectory()
    window = screenshots.build(Path(tmp.name))
    window.resize(1366, 768)
    window.show()
    window._paths_tmp = tmp  # kept alive with the window
    return app, window


def _walk_menu(menu, trail, found, emit=True):
    """Registry action ids in `menu` (submenus too) -> list of 'A > B > label' trails."""
    from evrakci.ui import actions as reg

    if emit:
        menu.aboutToShow.emit()  # the app fills its menus here
    title = reg.plain_text(menu.title()).rstrip("…").strip()
    here = [*trail, title] if title else list(trail)
    for item in menu.actions():
        if item.menu() is not None:
            _walk_menu(item.menu(), here, found, emit)
        elif item.objectName() in reg._BY_ID:
            found.setdefault(item.objectName(), set()).add(
                " > ".join([*here, reg.plain_text(item.text()).split("\t")[0].rstrip("…")]))
        elif item.text() and not item.isSeparator():
            found.setdefault("text:" + reg.plain_text(item.text()).split("\t")[0], set()).add(
                " > ".join(here))
    return found


def _button_texts(button) -> list[str]:
    texts = [button.text().strip(), button.toolTip().strip(), button.accessibleName().strip()]
    label = getattr(button, "label", None)
    if label is not None and hasattr(label, "text"):
        texts.append(label.text().strip())
    return [t for t in texts if t]


def _capture_menus(call):
    """Run `call()` (a context-menu builder) and return the registry actions of every menu it
    shows (popup or a blocking exec: a timer reads and closes the popup) or returns, as a list
    of `_walk_menu` results."""
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMenu

    caught: list[dict] = []

    def grab() -> None:
        popup = QApplication.activePopupWidget()
        if isinstance(popup, QMenu):
            caught.append(_walk_menu(popup, [], {}, emit=False))
            popup.close()

    timer = QTimer()
    timer.setInterval(5)
    timer.timeout.connect(grab)
    timer.start()
    try:
        result = call()
        for _ in range(5):
            QApplication.processEvents()
            grab()
    finally:
        timer.stop()
    if isinstance(result, QMenu):
        caught.append(_walk_menu(result, [], {}))
    return caught


def _context_targets(window, app):
    """(tab, target description, menus) for each tab's context-menu builders on a target."""
    from PySide6.QtCore import QItemSelectionModel, QPoint

    out = []

    def run(tab, target, call):
        try:
            menus = _capture_menus(call)
        except Exception as error:  # a builder that cannot run is reported, never hidden
            out.append((tab, target, error))
            return
        out.append((tab, target, menus))

    window.show_tab("yukle")
    table = window.yukle.table
    row = next((n for n, item in enumerate(window.yukle.model.items) if item.kind == "batch"), 0)
    pos = table.visualRect(window.yukle.model.index(row, 0)).center()
    run("yukle", "batch row", lambda: window.yukle._context_menu(pos))

    window.show_tab("kontrol")
    app.processEvents()
    screen = window.kontrol
    index = screen.timeline.model().index(1, 0)
    screen.timeline.selectionModel().select(
        index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
    pos = screen.timeline.visualRect(index).center()
    run("kontrol", "page", lambda: screen._context_menu(pos))

    window.show_tab("sablonlar")
    sablon = window.sablon
    template_id = next(iter(window.template_store.list()), None)
    template_id = getattr(template_id, "id", template_id)
    if template_id:
        sablon.open_template(template_id)
        app.processEvents()
    run("sablonlar", "variable row", lambda: sablon._variable_menu(QPoint(5, 5)))
    run("sablonlar", "box menu", lambda: sablon.box_menu())
    run("sablonlar", "page menu", lambda: sablon.box_menu(sablon_page_menu()))

    window.show_tab("degerler")
    app.processEvents()
    degerler = window.degerler
    pos = degerler.table.visualRect(degerler.table.model().index(0, 0)).center()
    run("degerler", "value row", lambda: degerler.context_menu(pos))

    window.show_tab("disa_aktar")
    app.processEvents()
    results = window.disa_aktar.results
    if results.model() is not None and results.model().rowCount() > 0:
        pos = results.visualRect(results.model().index(0, 0)).center()
        run("disa_aktar", "result row", lambda: window.disa_aktar._row_menu(pos))
    return out


def sablon_page_menu():
    from evrakci.ui import sablon

    return sablon.PAGE_MENU


def collect_paths_in_new_window():
    """collect_paths() on a freshly built demo window (the window is closed afterwards)."""
    app, window = _build_window()
    try:
        return collect_paths(window, app)
    finally:
        window.close()


def collect_paths(window=None, app=None):
    """-> (rows, problems). One row per tab x action x key (contract rows) plus the
    LOCAL_KEYS rows; see the module docstring for the columns."""
    from PySide6.QtWidgets import QAbstractButton, QToolButton

    from evrakci.ui import actions as reg
    from evrakci.ui.chrome import ActionButton

    if window is None:
        app, window = _build_window()
    problems: list[str] = []
    menu_of: dict[str, dict[str, set[str]]] = {}
    button_of: dict[str, dict[str, set[str]]] = {}
    context_of: dict[str, dict[str, set[str]]] = {}
    texts_in: dict[str, dict[str, set[str]]] = {}  # tab -> non-registry button/menu text -> where
    for tab in reg.TABS:
        window.show_tab(tab)
        app.processEvents()
        menu, button, texts = {}, {}, {}
        for item in window.menu_row.bar.actions():
            if item.menu() is not None:
                _walk_menu(item.menu(), [], menu)
        bar = window.command_bar(tab)
        page = window.tabs.currentWidget()
        for widget in bar.buttons():
            if isinstance(widget, ActionButton):
                button.setdefault(widget.action_.objectName(), set()).add("bar")
            elif isinstance(widget, QToolButton) and widget.menu() is not None:
                more = _walk_menu(widget.menu(), [], {})
                for action_id, trails in more.items():
                    button.setdefault(action_id, set()).add("bar Diğer komutlar")
                    del trails
        if tab == "kontrol" and window.kontrol is not None:
            window.kontrol.open_loupe(1)  # the loupe is built on first use; its buttons count
            app.processEvents()
        buttons = page.findChildren(QAbstractButton)
        if tab == "kontrol" and window.kontrol is not None:
            window.kontrol.close_loupe()
        for widget in buttons:
            default = widget.defaultAction() if hasattr(widget, "defaultAction") else None
            if default is not None and default.objectName() in reg._BY_ID:
                button.setdefault(default.objectName(), set()).add("panel")
            if isinstance(widget, QToolButton) and widget.menu() is not None:
                more = _walk_menu(widget.menu(), [], {})
                for action_id in more:
                    button.setdefault(action_id, set()).add(
                        "panel " + (widget.toolTip() or "Diğer"))
            for text in _button_texts(widget):
                texts.setdefault(text, set()).add(type(widget).__name__)
        for btab, action_id, cls, start in BUTTONS:
            if btab != tab:
                continue
            hits = [w for w in buttons if type(w).__name__ == cls
                    and any(t.startswith(start) for t in _button_texts(w))]
            if not hits:
                problems.append(f"BUTTONS entry matches no button: {tab} {cls} '{start}' "
                                f"({action_id})")
            else:
                button.setdefault(action_id, set()).add(f"{cls} {start}")
        menu_of[tab], button_of[tab], texts_in[tab] = menu, button, texts
    context_texts: dict[str, set[str]] = {}
    for tab, target, menus in _context_targets(window, app):
        context_of.setdefault(tab, {})
        if isinstance(menus, Exception):
            problems.append(f"context menu builder failed: {tab} {target}: {menus!r}")
            continue
        if not menus:
            problems.append(f"context menu builder gave no menu: {tab} {target}")
        for found in menus:
            for action_id in found:
                if action_id.startswith("text:"):
                    context_texts.setdefault(tab, set()).add(action_id[5:])
                else:
                    context_of[tab].setdefault(action_id, set()).add(target)

    table = []
    for tab in reg.TABS:
        for spec in reg.SPECS:
            if not reg._active(spec, tab):
                continue
            ids = spec.id
            menu_path = sorted(menu_of[tab].get(ids, ()))
            buttons_p = sorted(button_of[tab].get(ids, ()))
            context_p = sorted(context_of.get(tab, {}).get(ids, ()))
            keys = [portable(k) for k in spec.shortcuts] or [""]
            if menu_path or buttons_p or context_p:
                status = "ok"
            elif ids in EXEMPT:
                status = f"exempt:{EXEMPT[ids]}"
            elif not window.registry._handled(ids, tab):
                status = "exempt:inert on this tab (no handler, the key does nothing)"
            elif spec.shortcuts:
                status = "key-only"
            else:
                status = "palette-only"
            for key in keys:
                table.append((tab, key, ids, reg.plain_text(spec.text), " | ".join(menu_path),
                              " | ".join(buttons_p), " | ".join(context_p),
                              "yes" if spec.palette else "no", status))
    for tab, key, ids, label, exempt, via in LOCAL_KEYS:
        mouse = ""
        if via:
            in_context = via in context_texts.get(tab, ())
            in_button = any(t.startswith(via) for t in texts_in[tab])
            mouse = "context menu" if in_context else "button" if in_button else ""
            if not mouse:
                problems.append(f"LOCAL_KEYS 'via' not found: {tab} {ids} '{via}'")
        status = "ok" if mouse else f"exempt:{exempt}" if exempt else "key-only"
        table.append((tab, key, ids, label, "", f"{via}" if mouse == "button" else "",
                      f"{via}" if mouse == "context menu" else "", "no", status))
    return table, problems


def _tsv(table) -> str:
    lines = ["\t".join(PATH_COLUMNS)]
    lines += ["\t".join(row) for row in table]
    return "\n".join(lines) + "\n"


def _status_map(text: str) -> dict:
    rows = list(csv.DictReader(text.splitlines(), delimiter="\t"))
    return {(r["tab"], r["key"], r["action_id"]): r["status"] for r in rows}


def paths_problems(table, collected, out: Path, contract: Path = CONTRACT_TSV) -> list[str]:
    problems = list(collected)
    problems += [f"{t} {k or '(no key)'} {a}: {s} (no menu, button or context menu path)"
                 for t, k, a, _l, _m, _b, _c, _p, s in table
                 if s in ("key-only", "palette-only") and (t, a) not in PROPOSED]
    have = {(r[0], _norm_key(r[1]), r[2]) for r in table}
    if contract.exists():
        with contract.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                row = (r["tab"].strip(), _norm_key(r["key"]), r["action_id"].strip())
                if row not in have:
                    problems.append(f"contract row has no action-paths row: {' '.join(row)}")
    return problems


def run_paths(check: bool, out: Path) -> int:
    table, collected = collect_paths()
    text = _tsv(table)
    problems = paths_problems(table, collected, out)
    counts: dict[str, int] = defaultdict(int)
    for row in table:
        counts[row[-1].split(":")[0]] += 1
    actions_n = len({(r[0], r[2]) for r in table})
    print(f"action-paths: {len(table)} rows, {actions_n} tab x action pairs; "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if check:
        if not out.exists():
            problems.append(f"{out} does not exist (run --paths without --check)")
        elif _status_map(out.read_text(encoding="utf-8")) != _status_map(text):
            problems.append(f"{out} is stale: statuses differ from the live window "
                            "(run --paths and commit the file)")
    else:
        out.write_text(text, encoding="utf-8")
        print(f"wrote {out}")
    for problem in problems:
        print("  -", problem)
    print(f"action-paths problems: {len(problems)}")
    return 1 if check and problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tab", choices=list(actions.TABS))
    parser.add_argument("--divergent", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--contract", metavar="TSV", type=Path)
    parser.add_argument("--paths", action="store_true",
                        help="mouse paths of every action (writes docs/ui-goal/action-paths.tsv)")
    parser.add_argument("--paths-out", metavar="TSV", type=Path, default=PATHS_TSV)
    args = parser.parse_args(argv)
    if args.paths:
        return run_paths(args.check, args.paths_out)

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
