"""Dışa Aktar as final-a draws it: the graded pre-flight, the file list, progress, the outcome
card, the registry actions, persistence and accessible names."""
from __future__ import annotations

import threading

import pytest
from fakes import make_pdf, qr_page, text_page
from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QAbstractButton, QCheckBox, QLineEdit

from evrakci.pipeline.cuts import record_values
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.model import Section
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.pipeline.templates.values import VariableValue
from evrakci.ui import disa_aktar as module
from evrakci.ui.controller import JobController
from evrakci.ui.disa_aktar import DisaAktarScreen
from evrakci.ui.disa_aktar_model import (
    FileRow,
    Summary,
    findings,
    folder_state,
    pattern_problem,
    reason,
)
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs


def _job(tmp_path, with_template=True, names=("Ege Kalıp", "Akdeniz", "Ege Kalıp")):
    """A job of three documents; the second has a value that needs a check."""
    pdf = make_pdf(tmp_path / "t.pdf", [text_page("A"), text_page(), qr_page(), text_page("B"),
                                        qr_page(), text_page("C")])
    store = JobStore(tmp_path / "jobs")
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Kapasite Raporu")
    sicil = template.add_variable("Sicil no", required=True)
    firma = template.add_variable("Firma")
    template.add_section("Sicil no", Section(1, (20, 30, 90, 42)))
    template.add_section("Firma", Section(1, (20, 50, 140, 62)))
    template.set_pattern("{Sicil no}_{Firma}")
    templates.save(template)
    job = store.create_job("Kasım 2026", [pdf])
    ctl = JobController(store, job)
    if with_template:
        ctl.apply_template(ctl.job.ordered_page_ids(), template.id)
        for n, doc in enumerate(ctl.documents()):
            bad = n == 1
            values = {sicil.key: VariableValue("48Z13" if bad else f"4819{n}", 0.4 if bad else 0.95,
                                               0, bad, "48213" if bad else None, (), False),
                      firma.key: VariableValue(names[n % len(names)], 0.9, 0, False)}
            record_values(ctl.job, doc, template.id, values)
    return store, templates, ctl, template


def _screen(qtbot, tmp_path, **kw):
    store, templates, ctl, template = _job(tmp_path, **kw)
    screen = DisaAktarScreen(lambda: ctl, lambda: {t.id: t for t in templates.list()},
                             settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    screen.resize(1100, 700)
    return screen, ctl, template


def _window(qtbot, tmp_path):
    store, templates, ctl, template = _job(tmp_path)
    window = MainWindow(store, templates, settings_path=tmp_path / "ayar.json",
                        prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window)
    window.show()
    window.yukle.open_job(store.load(ctl.job.id))
    window.show_tab("disa_aktar")
    return window, window.disa_aktar


# -- the data: folder, findings, reasons --------------------------------------------------
def test_folder_states(tmp_path):
    assert folder_state("").kind == "none"
    assert folder_state(str(tmp_path / "yok")).kind == "new"
    empty = tmp_path / "bos"
    empty.mkdir()
    ok = folder_state(str(empty))
    assert (ok.kind, ok.tone, ok.blocks) == ("ok", "ok", False)
    (empty / "eski.PDF").write_bytes(b"x")
    full = folder_state(str(empty))
    assert (full.kind, full.tone, full.blocks) == ("full", "err", True)
    (tmp_path / "dosya").write_text("x")
    assert folder_state(str(tmp_path / "dosya")).blocks
    other = tmp_path / "baska"
    other.mkdir()
    (other / "not.txt").write_text("x")
    assert folder_state(str(other)).kind == "other"  # other files are left alone


def test_only_an_engel_blocks_a_kontrol_never_does(tmp_path):
    summary = Summary(10, 40, 3, True, 1, ("Sicil no",), "belge_004", 2, 1)
    rows = findings(summary, folder_state(""), ("", []))
    assert [f.level for f in rows] == ["bilgi", "kontrol", "eksik", "bilgi", "bilgi"]
    assert all(f.level != "engel" for f in rows)
    assert rows[1].count == 3 and rows[1].action == "next_check"
    assert rows[2].title == "Zorunlu değer eksik: Sicil no." and "belge_004" in rows[2].detail
    ok = findings(summary, folder_state(str(tmp_path)), ("", []))
    assert ok[0].level == "tamam"


def test_engel_rows_come_first_and_replace_tamam(tmp_path):
    (tmp_path / "x.pdf").write_bytes(b"x")
    summary = Summary(2, 8, 1, True, 0, (), "", 0, 0)
    rows = findings(summary, folder_state(str(tmp_path)),
                    pattern_problem("{Firma adı}", {"Firma"}))
    assert [f.level for f in rows][:2] == ["engel", "engel"]
    assert rows[0].action == "subfolder" and rows[1].action == "pattern"
    assert "Firma adı" in rows[1].title and "tamam" not in [f.level for f in rows]


def test_pattern_problems():
    assert pattern_problem("{A}_{B}", {"A", "B"}) == ("", [])
    assert pattern_problem("{A}_{C}", {"A", "B"}) == ("unknown", ["C"])
    assert pattern_problem("{A", {"A"})[0] == "brace"


def test_reasons_are_short():
    assert reason("zorunlu değer eksik: Sicil no") == "Sicil no eksik"
    assert reason("okunamadı: Firma") == "Firma belirsiz"
    assert reason("eksik sayfa") == "Eksik sayfa"


# -- the screen, standalone ---------------------------------------------------------------
def test_main_state_grades_the_findings_and_lists_flagged_files_first(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    assert screen.state() == "main"
    levels = screen.preflight.levels()
    assert levels[0] == "tamam" and "kontrol" in levels and "eksik" in levels
    model = screen.results.model()
    first = model.row_at(0)
    assert first.state == "kontrol" and first.name.startswith("belge_002")
    assert model.data(model.index(0, 0)).startswith("Kontrol")
    assert screen.export_button.isEnabled()
    assert screen.filter_button.trail() == "1"


def test_filter_shows_only_kontrol_files(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    assert screen.results.model().rowCount() == 3
    screen.filter_button.click()
    assert screen.results.model().rowCount() == 1
    screen.filter_button.click()
    assert screen.results.model().rowCount() == 3


def test_empty_state_when_there_is_no_job(qtbot, tmp_path):
    screen = DisaAktarScreen(lambda: None, dict, settings_path=tmp_path / "ayar.json")
    qtbot.addWidget(screen)
    assert screen.state() == "empty"
    assert screen.empty.title.text() == "Dışa aktarılacak belge yok"
    assert not screen.export_button.isEnabled()
    assert screen.folder_hint_text() == "İş açılınca klasör seçilebilir."
    with qtbot.waitSignal(screen.go_tab) as seen:
        screen.empty.go.click()
    assert seen.args == ["yukle"]
    assert screen.preflight.levels() == ["bilgi"]


def test_blocked_state_disables_export_and_names_the_reason(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "eski.pdf").write_bytes(b"x")
    screen.folder.setText(str(out))
    assert screen.state() == "blocked"
    assert screen.preflight.levels()[0] == "engel"
    assert not screen.export_button.isEnabled()
    assert screen.side.note.text.text() == "Önce engeli giderin."
    assert screen.export_button.accessibleDescription() == "Önce engeli giderin."
    assert screen.folder.property("invalid") is True


def test_new_subfolder_unblocks(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "eski.pdf").write_bytes(b"x")
    screen.folder.setText(str(out))
    screen._finding_action("subfolder")
    assert (out / "Kasım 2026").is_dir()
    assert screen.folder.text() == str(out / "Kasım 2026")
    assert screen.state() == "main"


def test_an_unknown_variable_in_the_pattern_is_an_engel(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.pattern.setText("{Oda sicil no}_{Firma}")
    screen.side.pattern_committed.emit(screen.pattern.text())
    assert screen.state() == "blocked"
    assert "Oda sicil no" in screen.preflight.rows[0].finding.title
    assert screen.side.pattern_hint.tone() == "err"
    # typing clears the red edge at once; leaving the field shows it again
    screen.side.pattern_edited.emit()
    assert screen.pattern.property("invalid") is False


def test_the_pattern_edit_is_one_undoable_change_and_drives_the_names(qtbot, tmp_path):
    screen, ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    assert screen.pattern.text() == "{Sicil no}_{Firma}"
    screen.pattern.setText("{Firma}")
    screen.side.pattern_committed.emit("{Firma}")
    assert ctl.undo_stack.undoText() == "Dosya adı kalıbı"
    names = [screen.results.model().row_at(i).name for i in range(3)]
    # the second document keeps its numbered name: its required Sicil no needs a check
    assert sorted(names) == ["Ege Kalıp (2).pdf", "Ege Kalıp.pdf", "belge_002.pdf"]
    ctl.undo()
    assert screen.pattern.text() == "{Sicil no}_{Firma}"
    assert screen.pattern_text() == "{Sicil no}_{Firma}"
    ctl.redo()
    assert screen.pattern_text() == "{Firma}"


def test_the_changed_pattern_is_what_is_written(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    out = tmp_path / "out"
    screen.folder.setText(str(out))
    screen.layer.setChecked(False)
    screen.pattern.setText("{Firma}")
    screen.side.pattern_committed.emit("{Firma}")
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert {p.name for p in out.glob("*.pdf")} == {"Ege Kalıp.pdf", "belge_002.pdf",
                                                    "Ege Kalıp (2).pdf"}


def test_a_name_clash_is_a_bilgi_with_the_suffix_marked(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.pattern.setText("{Firma}")
    screen.side.pattern_committed.emit("{Firma}")
    row = next(r for r in (screen.results.model().row_at(i) for i in range(3))
               if r.tail == " (2)")
    assert (row.state, row.why) == ("bilgi", "Ad çakışması, (2) eklendi")
    assert screen.results.model().word(row) == "Bilgi"
    assert any(f.action == "show_names" for f in screen._findings)


def test_the_folder_is_empty_by_default_and_asks_on_export(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    assert screen.state() == "main"
    screen.export()
    assert screen.task is None
    assert screen.folder_hint_text() == "Bir hedef klasör seçin."
    assert screen.folder.property("invalid") is True
    screen.folder.setText(str(tmp_path / "x"))  # typing a folder takes the error away
    assert screen.folder.property("invalid") is False


def test_files_are_written_and_the_outcome_card_says_so(qtbot, tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(module, "open_path", opened.append)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    out = tmp_path / "out"
    screen.folder.setText(str(out))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert screen.state() == "done"
    card = screen.outcome
    assert card.title.text() == "3 belge yazıldı"
    assert "kontrol gerektiriyor" in card.check_text.text()
    assert card.folder_button.isVisibleTo(screen) and card.index_button.isVisibleTo(screen)
    assert screen.results.model().mode == "written"
    assert screen.results.model().data(screen.results.model().index(0, 0)).startswith("Yazıldı")
    assert screen.again_button.isVisibleTo(screen) and not screen.export_button.isVisibleTo(screen)
    card.folder_button.click()
    card.index_button.click()
    assert opened == [out, out / "index.xlsx"]
    assert screen.side.folder_hint.text.text() == "Klasörde 3 PDF ve index.xlsx var."


def test_reveal_selects_the_file_in_explorer_on_windows(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(module.sys, "platform", "win32")
    monkeypatch.setattr(module.subprocess, "Popen", lambda args: seen.append(args))
    target = tmp_path / "index.xlsx"
    target.write_text("x")
    module.reveal_path(target)
    assert seen == [["explorer", f"/select,{target}"]]
    opened = []
    monkeypatch.setattr(module, "open_path", opened.append)
    monkeypatch.setattr(module.sys, "platform", "linux")
    module.reveal_path(target)
    assert opened == [tmp_path]


def test_again_returns_to_the_preflight_with_the_full_folder_blocked(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    screen.again_button.click()
    assert screen.state() == "blocked"  # the folder just written is full: a new one is asked for
    assert screen.preflight.rows[0].finding.action == "subfolder"


def test_a_failed_export_keeps_the_settings_and_offers_a_way_out(qtbot, tmp_path, monkeypatch):
    def broken(*_a, **_k):
        raise module.ExportError("Dosyalar yazılamadı (Disk dolu). Yazılanlar: yok.")

    monkeypatch.setattr(module, "export_job", broken)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert screen.outcome.isVisibleTo(screen)
    assert screen.outcome.title.text() == "Dışa aktarma tamamlanamadı"
    assert "Disk dolu" in screen.message.text()
    assert screen.outcome.close_button.isVisibleTo(screen)
    assert screen.folder.text() == str(tmp_path / "out")  # nothing the user typed is lost
    screen.outcome.close_button.click()
    assert not screen.outcome.isVisibleTo(screen)


def test_progress_locks_the_settings_and_marks_files_as_they_are_written(qtbot, tmp_path,
                                                                         monkeypatch):
    gate = threading.Event()
    real = module.export_job

    def held(*args, progress=None, **kwargs):
        progress("write", 1, 3)
        gate.wait(10)
        return real(*args, progress=progress, **kwargs)

    monkeypatch.setattr(module, "export_job", held)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    screen.export_button.click()
    qtbot.waitUntil(lambda: screen._done_count == 1, timeout=10000)
    assert screen.state() == "running" and screen.busy()
    assert screen.run_banner.isVisibleTo(screen)
    assert screen.run_banner.count.text() == "Yazılıyor: 1 / 3"
    assert "Ctrl+." in screen.run_banner.sub.text()
    assert screen.side.lock_note.isVisibleTo(screen)
    assert not screen.folder.isEnabled() and not screen.pattern.isEnabled()
    assert not screen.layer.isEnabled() and not screen.export_button.isEnabled()
    model = screen.results.model()
    words = [model.word(model.row_at(i)) for i in range(3)]
    assert sorted(words) == ["Bekliyor", "Yazıldı", "Yazılıyor"]
    assert not screen.preflight.isVisibleTo(screen)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        gate.set()
    assert screen.state() == "done" and screen.folder.isEnabled()


def test_escape_does_not_cancel_and_no_screen_shortcuts_remain(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    assert screen.findChildren(QShortcut) == []  # Ctrl+E, Ctrl+. etc. are registry actions


def test_stopping_says_what_was_written(qtbot, tmp_path, monkeypatch):
    real = module.export_job

    def stopping(*args, progress=None, **kwargs):
        def report(stage, done, total):
            progress(stage, done, total)
            if done >= 1:
                screen.cancel()

        return real(*args, progress=report, **kwargs)

    monkeypatch.setattr(module, "export_job", stopping)
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export_button.click()
    assert screen.outcome.title.text() == "Dışa aktarma durduruldu"
    assert "index.xlsx yazılmadı" in screen.message.text()
    assert screen.outcome.close_button.isVisibleTo(screen)


def test_copy_names_and_the_printable_index(qtbot, tmp_path):
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtPrintSupport import QPrinter

    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.results.selectRow(0)
    screen.copy_names()
    assert QGuiApplication.clipboard().text() == screen.results.model().row_at(0).name
    html = screen.index_html()
    assert "Kasım 2026" in html and "belge_002.pdf" in html and "Kontrol" in html
    printer = QPrinter()
    printer.setOutputFileName(str(tmp_path / "dizin.pdf"))
    screen.print_index(printer)
    assert (tmp_path / "dizin.pdf").stat().st_size > 500


def test_every_control_has_an_accessible_name(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.show()
    for widget in screen.findChildren(QAbstractButton) + screen.findChildren(QLineEdit):
        if isinstance(widget, QCheckBox):
            assert widget.text() or widget.accessibleName()
            continue
        if widget.objectName().startswith("qt_"):
            continue
        assert widget.accessibleName() or getattr(widget, "text", lambda: "")(), \
            f"{type(widget).__name__} has no name"
    assert screen.results.accessibleName() == "Dosya adları"
    assert screen.side.accessibleName() == "Dışa aktarma ayarları"
    assert screen.run_banner.bar.accessibleName() == "Yazma ilerlemesi"
    assert screen.folder.accessibleName() == "Hedef klasör"
    assert screen.pattern.accessibleName() == "Dosya adı kalıbı"


def test_tab_order_follows_the_reading_order(qtbot, tmp_path):
    screen, _ctl, _t = _screen(qtbot, tmp_path)
    screen.show()
    order = []
    w = screen.preflight
    for _ in range(400):
        w = w.nextInFocusChain()
        if w is screen.preflight:
            break
        if w.isVisibleTo(screen) and w.focusPolicy() & Qt.FocusPolicy.TabFocus:
            order.append(w)
    names = [type(x).__name__ for x in order]
    assert order.index(screen.folder) < order.index(screen.pattern) < order.index(
        screen.export_button)
    assert screen.filter_button in order and "FilesTable" in names
    assert order.index(screen.results) < order.index(screen.folder)


# -- in the window ------------------------------------------------------------------------
def test_registry_actions_are_wired_and_enabled_when_usable(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    r = window.registry
    out = tmp_path / "out"
    screen.folder.setText(str(out))
    assert r.action("app.disa_aktar").isEnabled()
    assert not r.action("disa_aktar.durdur").isEnabled()  # nothing runs
    assert r.action("disa_aktar.yazdir").isEnabled()  # there is a list to print
    assert not r.action("disa_aktar.gezginde_goster").isEnabled()  # the folder does not exist
    out.mkdir()
    screen.folder.setText(str(out) + "/")
    screen.folder.setText(str(out))
    assert r.action("disa_aktar.gezginde_goster").isEnabled()
    assert r.action("app.yenile").isEnabled()
    (out / "eski.pdf").write_bytes(b"x")
    screen.folder.setText(str(out) + " ")  # a full folder blocks: Ctrl+E is off on this tab
    screen.folder.setText(str(out))
    assert not r.action("app.disa_aktar").isEnabled()
    window.show_tab("kontrol")
    assert r.action("app.disa_aktar").isEnabled()  # from other tabs it still brings you here


def test_command_bar_status_and_panel_button(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    screen.folder.setText(str(tmp_path / "out"))
    bar = window.command_bar("disa_aktar")
    tips = [b.toolTip() for b in bar.buttons()]
    assert "index.xlsx'i aç" in tips  # A's sheet button sits before "Dosya Gezgini'nde göster"
    assert tips.index("index.xlsx'i aç") < next(i for i, t in enumerate(tips)
                                                if t.startswith("Dosya Gezgini'nde göster"))
    sheet = next(b for b in bar.buttons() if b.toolTip() == "index.xlsx'i aç")
    assert not sheet.isEnabled()
    status = screen.status_items["state"]
    assert "yazılabilir" in status.label.text()
    assert window.inspector("disa_aktar") is screen.side
    assert window.registry.action("app.yan_panel").isEnabled()
    window.toggle_inspector()
    assert screen.side.isHidden()
    window.toggle_inspector()
    assert not screen.side.isHidden()


def test_the_window_gets_taskbar_progress_and_a_toast(qtbot, tmp_path, monkeypatch):
    window, screen = _window(qtbot, tmp_path)
    calls = []

    class Recorder:
        def indeterminate(self):
            calls.append("indeterminate")

        def set(self, value, maximum):
            calls.append(("set", value, maximum))

        def clear(self):
            calls.append("clear")

        def error(self):
            calls.append("error")

    window.taskbar = Recorder()
    screen.folder.setText(str(tmp_path / "out"))
    screen.layer.setChecked(False)
    window.show_tab("kontrol")  # the toast is for a user who is on another tab
    with qtbot.waitSignal(screen.finished, timeout=30000):
        screen.export()
    assert calls[0] == "indeterminate"
    assert any(isinstance(c, tuple) and c[0] == "set" for c in calls)
    assert calls[-1] == "clear"
    assert "3 belge yazıldı" in window.toaster.current_text()


def test_columns_and_the_splitter_are_remembered(qtbot, tmp_path):
    window, screen = _window(qtbot, tmp_path)
    header = screen.results.horizontalHeader()
    header.resizeSection(0, 300)
    screen._save_header()
    assert not window.prefs.header_state(module.HEADER_KEY).isEmpty()
    screen.splitter.setSizes([700, 420])
    window._splitter_moved(screen.splitter)
    assert window.prefs.splitter_sizes("disa_aktar") == screen.splitter.sizes()
    # a new window restores both
    window2 = MainWindow(window.store, window.template_store, settings_path=tmp_path / "ayar.json",
                         prefs=Prefs(tmp_path / "p.ini"))
    qtbot.addWidget(window2)
    window2.show()
    assert window2.disa_aktar.splitter.sizes() == window.prefs.splitter_sizes("disa_aktar")
    window2.disa_aktar._restore_header()
    assert window2.disa_aktar.results.horizontalHeader().sectionSize(0) == 300


def test_the_default_export_folder_of_ayarlar_is_offered(qtbot, tmp_path):
    prefs = Prefs(tmp_path / "p.ini")
    prefs.set_export_folder(str(tmp_path / "varsayilan"))
    store, templates, ctl, _t = _job(tmp_path)
    window = MainWindow(store, templates, settings_path=tmp_path / "ayar.json", prefs=prefs)
    qtbot.addWidget(window)
    window.show()
    window.yukle.open_job(store.load(ctl.job.id))
    window.show_tab("disa_aktar")
    assert window.disa_aktar.folder.text() == str(tmp_path / "varsayilan")
    window.disa_aktar.folder.setText(str(tmp_path / "ben"))
    window.disa_aktar.refresh()
    assert prefs.export_folder() == str(tmp_path / "varsayilan")  # exporting never overwrites it


def test_status_never_by_colour_alone():
    from evrakci.ui.disa_aktar_parts import LEVEL_LOOK
    from evrakci.ui.disa_aktar_table import LOOK

    for word, icon, _role, _strong in LEVEL_LOOK.values():
        assert word and icon
    assert all(icon for icon, _role, _strong in LOOK.values())
    assert {"Kontrol", "Yazıldı", "Yazılıyor", "Bekliyor"} <= set(LOOK)


def test_file_row_parts():
    row = FileRow(1, "bilgi", "Ad çakışması, (2) eklendi", "ad", " (2)", ".pdf", "1–2", None)
    assert row.name == "ad (2).pdf"


@pytest.mark.parametrize("mode", ["light", "dark", "hc"])
def test_the_screen_renders_in_every_theme(qtbot, tmp_path, mode):
    from evrakci.ui import theme

    m = theme.manager()
    before = m.mode()
    try:
        m.set_mode(mode)
        screen, _ctl, _t = _screen(qtbot, tmp_path)
        screen.folder.setText(str(tmp_path / "out"))
        screen.show()
        image = screen.grab()
        assert not image.isNull()
    finally:
        m.set_mode(before)


def test_no_part_of_the_screen_flashes_up_as_its_own_window(qtbot, tmp_path):
    """A link button shown before it was put in its row used to open as a top-level window
    (and took the window's activation)."""
    from PySide6.QtWidgets import QApplication, QWidget

    window, screen = _window(qtbot, tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    (out / "eski.pdf").write_bytes(b"x")
    screen.folder.setText(str(out))  # a blocked state: every kind of row is built
    screen.pattern.setText("{Yok}")
    screen.side.pattern_committed.emit("{Yok}")
    shown = [w for w in QApplication.topLevelWidgets()
             if isinstance(w, QWidget) and w.isVisible() and w is not window]
    assert shown == []
