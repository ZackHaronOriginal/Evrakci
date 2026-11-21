---
name: shortcut-audit
description: Use when adding, changing or reviewing any Evrakçı keyboard shortcut, or when asked to check that shortcuts are consistent across the six tabs. Builds a shortcut -> action -> test table from the action registry, finds conflicts and gaps, and writes the missing tests in tests/ui.
---

# Shortcut audit

Source of truth is `src/evrakci/ui/actions.py` (`SPECS`, `MENU_LAYOUT`, `Registry`, `validate()`).
`docs/ui-goal/shortcuts.md` is the hand-written map. If they disagree the code wins and the doc
gets fixed. (Its "Status: Phase 2 groundwork" line is stale: `MainWindow` already builds the
`Registry`, see `src/evrakci/ui/main_window.py`.) Product rule: every frequent action is reachable
by keyboard, and the Turkish Q keyboard must work (`docs/ui-goal/shortcuts.md`, PRODUCT.md
"Accessibility & Inclusion").

## The rule

A key does the same thing on every tab, or it is page-specific and says so. Page-specific reuse
is legal because `Registry.set_context(tab)` activates only "app" actions plus the current tab's.
Today's intended reuse: Del, Enter, Esc, Space, N / Shift+N, F2, Alt+Up/Down, Ctrl+.,
Ctrl+P, Ctrl+Shift+O, Ctrl+A. "Same meaning" for these means the same verb on the selected thing
(delete the selection, confirm and move on, dismiss). A key that changes verb (not just object)
between tabs is a bug, unless documented.

## Steps

1. Build the table from the registry (no UI is started):

   ```bash
   QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py > /tmp/shortcuts.md
   QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py --tab kontrol
   QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py --divergent
   QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py --check   # exit 1 on problems
   ```

   Columns: tab, key, action id, label, flags (`local`, `typing`, `checkable`), test files that
   mention the id or press the key. Write the result as a table `shortcut | expected action | test`
   per tab in your report (one section per tab: yukle, kontrol, sablonlar, degerler, disa_aktar,
   rehber). This raw table is a working file (scratchpad); the contract below is the one that is
   committed.

## The contract: what the key does and what the user sees

A binding is not checked until both its **effect** and its **feedback** are tested. The contract
lives in `docs/ui-goal/shortcut-contract.tsv`, one row per binding per tab where it is active:

| Column | Meaning |
|---|---|
| tab, key, action_id, label | from the registry |
| precondition | what must be true: job loaded, selection, which widget has focus |
| effect | the exact change in data or state, read from the job, model or controller (never from UI text) |
| feedback | what the user sees: status-bar text, toast text and its Undo, focus move, selection or highlight change, undo-stack entry name, or "disabled: <reason in tooltip>" |
| not_applicable | what happens when the precondition is false: disabled with a reason, or a status message; never silent |
| undo | what Ctrl+Z restores and the undo entry's name |
| same_as | for a key active on several tabs: the row it must behave like, or "page-specific: <why>" (must also be in `shortcuts.md`) |
| test | the test id that covers the row |

Rules:
- Same key, same verb on every tab where it is active; a different verb is a bug unless
  `same_as` says page-specific and `shortcuts.md` documents it.
- Menu, command-bar button, command palette and key must give the same effect and feedback.
- A key that does nothing visible is a bug (for example F5 enabled with no action, B-028).
- Feedback text uses the project vocabulary (Kontrol, Emin / Orta / Kontrol / Okunamadı,
  İncelendi / İncelenmedi). New Turkish text goes to the owner before it ships.

Tests are data-driven: one parametrized test in `tests/ui/test_shortcut_contract.py` reads the TSV
and, per row, (1) builds the demo window, goes to the tab, sets the precondition, sends the real key
with `QTest` to the focus widget, asserts the effect and the feedback; (2) breaks the precondition,
sends the key, asserts the `not_applicable` behaviour; (3) triggers the same action through the
menu or palette and asserts the same result. Effect and feedback checks are small named helpers
(`effect_cut_added`, `feedback_toast(text)`, `feedback_focus(widget)`, ...), so a row names them
instead of carrying code. Mark each test with the action id (`@pytest.mark.action("kontrol.cut")`)
so `audit_shortcuts.py` can match tests by id instead of by text search.

2. Conflicts. `actions.validate()` (printed by the script) already catches: duplicate ids, Turkish
   letters or I in a key, Ctrl+Alt (AltGr), a key used twice on one tab, `single_key` flag
   mismatch, menu access-key clashes. Then check by hand what it cannot:
   - `--divergent` output: every key listed must have a row in the page-specific notes of
     `docs/ui-goal/shortcuts.md` or be changed.
   - Widgets that eat a key before the action sees it: `QAbstractItemView` (arrows, Home/End,
     Enter, Space, Ctrl+A), `QLineEdit`/spin boxes (everything, handled by `TextFocusGuard`),
     buttons (Space/Enter, handled by `Registry.set_on_button`). A local key (`local=True`)
     must accept `QEvent.ShortcutOverride` if an action shares it; grep
     `grep -rn "ShortcutOverride" src/evrakci/ui`.
   - Two sources for one key: a leftover `QShortcut(` in a screen next to a registry action makes Qt
     fire neither. `grep -rn "QShortcut(" src/evrakci/ui` should show nothing for registry keys.
   - Tooltip / sheet / menu text: the key text comes from `actions.tooltip_for` and `key_text`;
     a key typed by hand into a label or tooltip string can drift from the registry.

3. Missing shortcuts. For each tab list the commands in its command bar
   (`MainWindow` builds them from the registry, `main_window.py` near the "A's command bars"
   comment) and every button in its side panel. A command with no key and no menu entry, or an
   action with `palette=False` that a user would want, is a gap. Frequent actions must have a
   key (PRODUCT.md). Check the other direction too: a registry action whose handler is never
   connected stays disabled (`Registry.connect`); find them with the test below.

4. Tests, in `tests/ui/` (there are `test_actions.py` for the registry alone with a bare
   `QMainWindow`, `test_phase4.py` for the real window; reuse its fixture). Patterns:
   - Registry-level, no window: copy `test_same_key_fires_the_current_tabs_action` in
     `tests/ui/test_actions.py` (connect two ids, `set_context`, `QTest.keyClick`).
   - Real window: tests are not importable as a package, so copy the
     `demo` fixture (`screenshots.build`, `window.show()`, `QTest.qWaitForWindowActive`) and
     parametrize over `TAB_IDS`:

     ```python
     @pytest.mark.parametrize("tab", TAB_IDS)
     def test_ctrl_g_is_enabled_and_routed_on_every_tab(demo, tab):
         demo.show_tab(tab)
         _settle()
         assert demo.registry.is_enabled("app.git"), tab
         assert "Ctrl+G" in demo.registry.live_keys("app.git")
     ```

   - Behaviour: put focus in the tab's main view, `QTest.keyClick(QApplication.focusWidget(), key)`,
     assert the effect on the controller or model, not just that a slot ran.
   - Typing guard: focus a `QLineEdit`, press a single-key shortcut, assert nothing fired
     (see `test_text_focus_guard_drops_typing_keys`).
   - One test per divergent-but-documented key that asserts the page-specific meaning.
   Run only the relevant files, never the whole suite:

   ```bash
   QT_QPA_PLATFORM=offscreen python -m pytest tests/ui/test_actions.py tests/ui/test_shortcut_sheet.py -q
   QT_QPA_PLATFORM=offscreen python -m pytest tests/ui/test_phase4.py -q -k "ctrl or key or tab"
   ```

5. Update `docs/ui-goal/shortcuts.md` (map, page-specific notes) in the same change as the
   registry. Lint: `ruff check .`.

## Mouse paths: no action only on a key

Rule: no command is reachable only through a shortcut. Every action also has a visible mouse path:
the menu bar, a button (command bar, side panel or inspector, card) or a context menu. The command
palette is a keyboard path and does not count. Only pure navigation keys (arrows, Home/End,
PgUp/PgDn, Tab, F6, Esc in a field) may be exempt, each with a one-line reason in `EXEMPT` or
`LOCAL_KEYS` in `audit_shortcuts.py`; an operation (cut, merge, delete, rotate, move a box,
refresh...) never is.

```bash
QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py --paths          # writes docs/ui-goal/action-paths.tsv
QT_QPA_PLATFORM=offscreen python .claude/skills/shortcut-audit/audit_shortcuts.py --paths --check  # exit 1 on a key-only row or a stale file
QT_QPA_PLATFORM=offscreen python -m pytest -q tests/test_action_paths.py
```

It starts the real window with the demo job, walks every menu of the menu bar, the command-bar and
panel buttons and each tab's context-menu builders, and writes one row per tab, key and action
(status `ok`, `key-only` or `exempt:<reason>`). When you add an action: put it in `MENU_LAYOUT`
(and in a context menu if it acts on an object), then rerun `--paths` and commit the TSV. A button
that calls a slot instead of a QAction goes into the `BUTTONS` table (the tool fails if an entry
matches no button). A key still key-only gets a strict xfail in `tests/test_action_paths.py`
(`KEY_ONLY`) until fixed; a fix that needs a new label or a look change becomes a line in
`docs/ui-goal/audit/<tab>-proposals.md`.

## Report format

Per tab: the table, then three lists: conflicts (with the two actions), gaps (command without
key, key without test), and fixes made. Say plainly which keys you could not test (for example
ones that need a real Turkish layout or a modal dialog).
