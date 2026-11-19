# Phase 2 review: findings and fixes

All high and medium findings and every low finding are fixed. Checks after the fixes:
`QT_QPA_PLATFORM=offscreen python3 -m pytest -q` passes in full, `ruff check .` is clean, and
`python3 tools/screenshots.py matrix docs/ui-goal/shots/phase2` renders 72 shots. Each theme and
text size now starts from a freshly built window.

| Severity | Area | Issue | What was done |
|---|---|---|---|
| high | tokens / theme (D10) | `ThemeManager.colors()` let the LEGACY alias table overwrite A's own roles `card` and `paper` (and `manila`, `rider`, `ok`, `hover`). As a result, A's white cards painted as the layer colour, and in dark and hc `paper` was no longer the light scan colour. | `_build_colors` applies an old name only when A has no role with that name. New test `test_runtime_colours_are_a_s_tokens` (light, dark, hc) compares `manager().colors()` with `g.COLORS` for every A token (hc: the system-mapped value) and runs the D10 pair check on the runtime colours. Two screen lookups that meant the old "card" (= A layer) now name `layer`: the Kontrol overview strip (`kontrol.py`) and the disabled key-hint button fill (`widgets.py`). `QListView#timeline` gets `layer` in the QSS, so Kontrol's pages sit on the layer as A draws them. |
| high | theme switching / hc contrast | The screens built per-widget sheets once, from `theme.TOKENS`. After a runtime switch, Değerler and Dışa Aktar kept a light header band, which made white-on-light-grey text in hc. The matrix built one light window and then switched it, so the shots showed that stale state. | New foundation hooks `theme.follow(owner, fn)` and `theme.bind_style(widget, build)` re-run after every `ThemeManager.changed` and are dropped together with their widget. The token-based sheets now use them: Değerler table, Dışa Aktar results, the Kontrol notice, the Şablonlar message, and `StateLabel` (icon and colour). Test `test_theme_switch_restyles_the_screens_token_sheets` switches a MainWindow to hc and checks that both header sections use the system window colour. `screenshots.py matrix` builds a fresh window for every theme and text size. |
| medium | command bar fidelity | Labelled commands had Qt's ~4 px icon–label gap instead of A's `s2` = 8 px. The width was measured with the unpolished 400-weight font. | `ActionButton` paints labelled buttons itself: the style draws the box (hover, pressed, checked, focus), the icon sits at `s2`, and the label starts at `s2 + icon + s2`. Width and painting both use the `body-medium` (500) font. Test `test_command_label_sits_two_gaps_after_its_icon` checks the geometry and the pixels (no ink in the gap; label ink right at the start). |
| medium | command bar fidelity (A as drawn) | Every bar was missing A's panel-right button (F9). Değerler was missing "Değerleri oku" and the list-filter button. Bars ended with a separator directly before "…". | New registry actions: `app.yan_panel` (F9, panel-right, Görünüm menu), `degerler.oku` (scan-text, labelled) and `degerler.eksikleri_oku` (list-filter), both in Araçlar. `COMMANDS` now follows A's order on all six tabs and ends `sep, panel-right, …`. The panel-right tooltip uses A's label for each tab ("Ayrıntı / Kaynak / Ayarlar panelini gizle (F9)", "Yan paneli gizle (F9)") and changes to "göster" once the panel is hidden. F9 toggles the screen's `side`. Screens that have no `side` yet (Yükle, Şablonlar, Dışa Aktar, Rehber) show the button disabled until Phase 3 adds one. The screen's old read buttons are hidden in the window, and the bar commands click them and mirror their enabled state. F9 and the two read commands are recorded in `shortcuts.md`. Tests: `test_command_bars_follow_a`, `test_f9_hides_and_shows_the_side_panel`. |
| medium | title band layout (Windows) | The job name could not elide, so a long name widened the band. With the caption buttons at 1366 px, 130 % did not fit at all, and the offscreen matrix could not show it. | `JobSwitch.name` is an `ElidedLabel`: it elides with "…" down to about 6 characters, and its full name is the tooltip and accessible name. `TitleBand` reports the narrow-tab minimum, so it never widens the window. When A's labelled tabs do not fit, `TitleBand.fit` applies the provisional 150 % tab rule (unselected tabs show only their icon). This logic is kept inside `theme.title_band_rule(…, fits)` so that it can be switched in one place. It is recorded under PROPOSALS item 3 for the owner. Test `test_title_band_fits_1366_with_caption_buttons_and_a_long_name` (100, 130 and 150 %, Inter loaded, caption buttons, 60+ character name) checks for no overlap, every tab whole, the name elided and the band minimum at most 1366. At 100 % the labelled tabs stay. |
| medium | gate tooling (§3.3) | `clipping()` missed text that is elided before `setText`, as well as combo boxes and key-hint buttons. The script always exited 0. | `clipping()` now flags any drawn "…"/"...". It uses `displayed_text()`/`is_elided()`, which are new on `ElidedLabel` and `KeyHintButton`, and checks a `QComboBox` against its edit-field sub-control. `matrix` exits 1 when anything is found; `--allow` reports without failing. Both `matrix` and `--matrix` are accepted. |
| low | correctness (undo sync) | `_watched_stacks` held `id(stack)`, and a reused id could skip a new stack. | Signals are now connected with `Qt.UniqueConnection`. The previous job's controller is disconnected on open and on close (`_wire_controller` / `_unwire_controller`). `_sync_undo` keeps only the RuntimeError guard. Test `test_each_job_is_wired_once_and_the_old_one_let_go`. |
| low | save state wording | A save from days ago showed only "Kaydedildi 14:32". | `feedback.saved_text`: "14:32" for today, "12 Kas 14:32" for another day this year, "12 Kas 2025 14:32" for an earlier year. The job file path comes from one `MainWindow._job_file` helper, which wraps `JobStore._job_file`. The pipeline is left untouched (D13), so no new public accessor was added. Tests: `test_saved_text_shows_the_date_when_not_today`, `test_an_old_save_shows_its_date`. |
| low | prefs API | `native_title_bar()` read the private `Prefs._s`. No UI exposed the option. | New `Prefs.native_title_bar()` / `set_native_title_bar()` (validated), used by `titlebar.native_title_bar`. New Ayarlar > Görünüm checkbox "Sistem başlık çubuğunu kullan" ("Evrakçı yeniden açılınca uygulanır"), which "Varsayılanlara dön" resets. Tests: prefs round trip, settings dialog toggle, and the updated shell test. |
| low | signal hygiene | Every open connected `status` and `job_changed` again (through a lambda) and never disconnected them. | Bound methods (`_saved_now`) are now connected with `UniqueConnection` and disconnected from the previous controller (same change as the undo-sync row). |

## Handed to Phase 3 (screen content, §3.3 gate)

`screenshots.py matrix` still reports 15 distinct elisions, all of them in screen content. None
is in the title band, the command bars or the status bar:

| Tab | Text | Widget | At |
|---|---|---|---|
| Kontrol | "Filtreyi uygula", "Şablon uygula" | KeyHintButton (old screen toolbar) | 100, 150 |
| Kontrol | "Geri al", "Yinele" | KeyHintButton (old screen toolbar) | 150 |
| Kontrol | "Faaliyet Belgesi" | QComboBox (template) | 100, 150 |
| Kontrol | "Seçim yok", "sayfada bir belge" | QLabel (old toolbar) | 150 |
| Değerler | "Şablon: hepsi" | QComboBox (filter) | 100, 150 |
| Dışa Aktar | "3 belge · 13 sayfa" | QLabel | 150 |
| Şablonlar | "Seçili örnek üzerinde, kaydetmeden önce." | QLabel | 150 |
| Rehber | "Kaç adet" | QLabel | 150 |

Other notes for the tab owners:

- Each screen should expose its inspector as `side`, so that F9 and the panel-right button work.
- Remove Değerler's own read buttons; the command bar now owns those commands.
- Replace the remaining old-name lookups (`TOKENS["card"]` and the like) with A's roles.
- Use `theme.bind_style` / `theme.follow` for any sheet or pixmap built from tokens.
