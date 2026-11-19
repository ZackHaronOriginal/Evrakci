"""Şablonlar' rows of the shortcut contract (Phase 3, step 3D): steps and plans, registered into
`contract_helpers.HELPERS` and `contract_helpers.PLANS`.

The tests of this tab share one demo window ("job_sablon") with the template "Kapasite Raporu"
open: Sicil_No (one box at 20,30 - 90,42 mm) and Firma_Adi (one box), example 1, page 1. Every
test puts the template back through the undo stack. The no-template, no-page case is the
window with no job ("empty").
"""
from __future__ import annotations

import re

from conftest import needs_tesseract
from contract_helpers import (
    PLANS,
    Ctx,
    Plan,
    _says,
    assert_focus_ring,
    heard,
    helper,
    on_modal,
    plain,
    said,
    settle,
    slot_texts,
    wait_until,
)
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

P_NO_PAGE_B = "Kutu çizmek için bir şablon ve bir örnek sayfa gerekir."  # PROPOSED (Q-08)
P_NO_PAGE_G = "Izgara için bir şablon ve bir örnek sayfa gerekir."  # PROPOSED (Q-08)
P_NOTHING_CHOSEN = "Önce bir değişken ya da kutu seçin."  # PROPOSED (Q-08)
P_NO_BOX = "Önce bir kutu seçin."  # PROPOSED (Q-08)
P_NO_TEMPLATE = "Önce bir şablon seçin ya da oluşturun."  # PROPOSED (Q-08)
P_FIRST = "Zaten ilk sırada."  # PROPOSED (Q-08)
P_LAST = "Zaten son sırada."  # PROPOSED (Q-08)
NO_PAGE_DENE = "Denemek için bir şablon ve açık bir iş gerekir."
for _name, _text in (("no_page_b", P_NO_PAGE_B), ("no_page_g", P_NO_PAGE_G),
                     ("nothing_chosen", P_NOTHING_CHOSEN), ("no_box", P_NO_BOX),
                     ("no_template", P_NO_TEMPLATE), ("first_place", P_FIRST),
                     ("last_place", P_LAST), ("no_page_dene", NO_PAGE_DENE)):
    _says(f"sablon_{_name}", _text)


def _s(c: Ctx):
    return c.win.sablon


def _quiet(c: Ctx) -> None:
    s = _s(c)
    s._read_timer.stop()  # the read the last edit asked for is not wanted: only a running one
    s._save_timer.stop()  # is waited for, so no worker outlives the test
    wait_until(lambda: s._read_task is None)
    if s._dirty:
        s._flush_save()


def ensure_template(c: Ctx) -> None:
    """Kapasite Raporu open on example 1 with nothing chosen; the edits of the test are undone
    when it ends (and the live read of the last edit is waited for)."""
    s = _s(c)
    if s.template is None or s.template.name != "Kapasite Raporu":
        tid = next(t.id for t in c.win.template_store.list() if t.name == "Kapasite Raporu")
        s.open_template(tid)
        settle()
    c.undo.append(lambda: _quiet(c))
    stack = s.undo_stack
    base = stack.index()
    c.undo.append(lambda: (stack.setIndex(base), settle()))
    assert s.canvas.has_page() and s.example == 1


def _sections(c: Ctx, name: str) -> int:
    return len(_s(c).template.variable(name).sections)


def _names(c: Ctx) -> list[str]:
    return [v.name for v in _s(c).template.variables]


def _box(c: Ctx, name: str = "Sicil_No", index: int = 0) -> tuple:
    return tuple(_s(c).template.variable(name).sections[index].box_mm)


def choose(c: Ctx, name: str, index: int | None, focus: str = "canvas") -> None:
    s = _s(c)
    if index is None:
        s.select_variable(name)
    else:
        s.select_section(name, index)
    getattr(s, focus).setFocus()
    settle()
    assert QApplication.focusWidget() is getattr(s, focus)


def _snap(c: Ctx) -> dict:
    s = _s(c)
    if s.template is None:
        return {"status": c.win.message.text()}
    from evrakci.pipeline.templates.model import template_to_dict

    return {"template": template_to_dict(s.template), "index": s.undo_stack.index(),
            "variable": s.variable_name, "section": s.section_index,
            "drawing": s.is_drawing(), "snap": s.is_snapping(),
            "status": c.win.message.text()}


helper("snap.sablon")(_snap)


def _unchanged(c: Ctx) -> None:
    now = _snap(c)
    for name in ("template", "index"):
        assert now.get(name) == c.snap.get(name), f"{name} changed"


def _toast_undo(c: Ctx) -> bool:
    toast = c.win.toaster._current
    return toast is not None and any(b.text() == "Geri al" for b in toast.findChildren(QPushButton))


def _bar_button(c: Ctx, action_id: str):
    return c.win.command_bar("sablonlar").button_for(action_id)


# -- B, G -------------------------------------------------------------------------------------
@helper("pre.sablon_page")
def _pre_page(c: Ctx) -> None:
    ensure_template(c)
    s = _s(c)
    c.undo.append(lambda: (s.set_drawing(False), s.set_snap(bool(c.data.get("snap0")))))
    c.data["snap0"] = s.is_snapping()
    choose(c, "Sicil_No", None)
    s.set_drawing(False)


@helper("effect.sablon_drawing_on")
def _effect_drawing_on(c: Ctx) -> None:
    assert _s(c).is_drawing() and _s(c).canvas.drawing


@helper("feedback.sablon_drawing_on")
def _feedback_drawing_on(c: Ctx) -> None:
    win = c.win
    assert win.registry.action("sablonlar.kutu_ciz").isChecked()
    button = _bar_button(c, "sablonlar.kutu_ciz")
    assert button is not None and button.isChecked(), "the bar button does not show the check"
    assert _s(c).canvas.viewport().cursor().shape() == Qt.CursorShape.CrossCursor
    assert_focus_ring(win)


@helper("effect.sablon_snap_flipped")
def _effect_snap_flipped(c: Ctx) -> None:
    now = _s(c).is_snapping()
    assert now == (not c.snap["snap"])
    assert c.win.prefs.flag("sablonlar.izgara", False) == now, "the setting was not remembered"


@helper("feedback.sablon_snap_flipped")
def _feedback_snap_flipped(c: Ctx) -> None:
    now = _s(c).is_snapping()
    assert c.win.registry.action("sablonlar.izgara").isChecked() == now
    button = _bar_button(c, "sablonlar.izgara")
    assert button is not None and button.isChecked() == now
    assert _s(c).canvas.snap == now


# -- Ctrl+T -----------------------------------------------------------------------------------
@helper("pre.sablon_dene")
def _pre_dene(c: Ctx) -> None:
    ensure_template(c)
    s = _s(c)
    wait_until(lambda: s._read_task is None)
    choose(c, "Sicil_No", None)

    def forget() -> None:
        s.example_values = {}
        s._mark_example_checks()

    c.undo.append(forget)


@helper("effect.sablon_dene")
def _effect_dene(c: Ctx) -> None:
    s = _s(c)
    assert wait_until(lambda: s._all_task is None, 60000), "the read did not finish"
    assert set(s.example_values) == {1, 2, 3}, s.example_values.keys()


@helper("feedback.sablon_dene")
def _feedback_dene(c: Ctx) -> None:
    win, s = c.win, _s(c)
    toast = win.toaster.current_text()
    assert re.fullmatch(r"3 örnekte denendi\. (\d+ okuma kontrol bekliyor|Kontrol gerektiren "
                        r"okuma yok)\.", toast), toast
    flagged = re.search(r"(\d+) okuma kontrol bekliyor", toast)
    if flagged:
        assert f"{flagged.group(1)} okuma kontrol bekliyor" in slot_texts(win, "sablonlar")
        assert any("kontrol" in s.examples.itemText(r).split("·")[-1]
                   for r in range(s.examples.count())), "no example is marked"


# -- Del, Ctrl+D, Ctrl+Shift+N, Alt+Up / Alt+Down ----------------------------------------------
@helper("pre.sablon_box_chosen")
def _pre_box_chosen(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Firma_Adi", 0)


@helper("effect.sablon_box_deleted")
def _effect_box_deleted(c: Ctx) -> None:
    assert _sections(c, "Firma_Adi") == 0
    s = _s(c)
    assert s.variable_name == "Firma_Adi" and s.section_index is None, "the selection did not move"


@helper("feedback.sablon_box_deleted")
def _feedback_box_deleted(c: Ctx) -> None:
    assert c.win.toaster.current_text() == "“Firma_Adi” değişkeninin 1. bölümü silindi.", \
        heard(c.win)
    assert _toast_undo(c)
    assert _s(c).undo_stack.undoText() == "Kutuyu sil"


@helper("pre.sablon_box_one")
def _pre_box_one(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", 0)


@helper("pre.sablon_no_box_chosen")
def _pre_no_box_chosen(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", None)


@helper("effect.sablon_box_copied")
def _effect_box_copied(c: Ctx) -> None:
    assert _sections(c, "Sicil_No") == 2
    first, copy = _box(c, "Sicil_No", 0), _box(c, "Sicil_No", 1)
    assert copy != first and (copy[2] - copy[0], copy[3] - copy[1]) == (first[2] - first[0],
                                                                        first[3] - first[1])
    assert _s(c).section_index == 1


@helper("feedback.sablon_box_copied")
def _feedback_box_copied(c: Ctx) -> None:
    s = _s(c)
    texts = [plain(lb.text()) for lb in s.side.findChildren(QLabel) if lb.isVisibleTo(c.win)]
    assert "Kutu 2 / 2" in texts, texts
    item = s.canvas.selected_item()
    assert item is not None and (item.spec.name, item.spec.index) == ("Sicil_No", 1)
    assert s.undo_stack.undoText() == "Kutuyu çoğalt"


@helper("pre.sablon_add_variable")
def _pre_add_variable(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", None)

    def answer(dialog) -> None:
        c.data["title"] = dialog.windowTitle()
        dialog.setTextValue("Yeni_Deger")
        dialog.accept()

    on_modal(c, answer)


@helper("effect.sablon_variable_added")
def _effect_variable_added(c: Ctx) -> None:
    assert c.data.get("modals"), "the dialog did not open"
    assert _names(c) == ["Sicil_No", "Firma_Adi", "Yeni_Deger"]
    assert _s(c).variable_name == "Yeni_Deger"


@helper("feedback.sablon_variable_added")
def _feedback_variable_added(c: Ctx) -> None:
    s = _s(c)
    assert c.data["title"] == "Değişken ekle"
    assert s.variables.currentItem().text(0).startswith("Yeni_Deger")
    texts = [plain(lb.text()) for lb in s.side.findChildren(QLabel) if lb.isVisibleTo(c.win)]
    assert "Değişken 3 / 3" in texts, texts
    assert s.undo_stack.undoText() == "Değişken ekle"


@helper("pre.sablon_second_variable")
def _pre_second_variable(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Firma_Adi", None, "variables")


@helper("pre.sablon_first_variable")
def _pre_first_variable(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", None, "variables")


@helper("effect.sablon_moved_up")
def _effect_moved_up(c: Ctx) -> None:
    assert _names(c) == ["Firma_Adi", "Sicil_No"]


@helper("effect.sablon_moved_down")
def _effect_moved_down(c: Ctx) -> None:
    assert _names(c) == ["Firma_Adi", "Sicil_No"]


@helper("feedback.sablon_moved_up")
def _feedback_moved_up(c: Ctx) -> None:
    s = _s(c)
    assert s.variables.topLevelItem(0).text(0).startswith("Firma_Adi")
    assert s.variables.currentItem() is s.variables.topLevelItem(0), "the moved row lost focus"
    assert s.undo_stack.undoText() == "Sırayı değiştir"


@helper("feedback.sablon_moved_down")
def _feedback_moved_down(c: Ctx) -> None:
    s = _s(c)
    assert s.variables.topLevelItem(1).text(0).startswith("Sicil_No")
    assert s.variables.currentItem() is s.variables.topLevelItem(1), "the moved row lost focus"
    assert s.undo_stack.undoText() == "Sırayı değiştir"


@helper("na.sablon_stays_and_says_first")
def _na_first(c: Ctx) -> None:
    _unchanged(c)
    assert said(c.win, P_FIRST), f"nothing said: {heard(c.win)!r}"


@helper("na.sablon_stays_and_says_last")
def _na_last(c: Ctx) -> None:
    _unchanged(c)
    assert said(c.win, P_LAST), f"nothing said: {heard(c.win)!r}"


@helper("na.sablon_stays_and_says_no_box")
def _na_no_box(c: Ctx) -> None:
    _unchanged(c)
    assert said(c.win, P_NO_BOX), f"nothing said: {heard(c.win)!r}"


# -- arrows, Shift+arrows, Space (local keys of the canvas) --------------------------------------
@helper("pre.sablon_nudge")
def _pre_nudge(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", 0)
    c.data["box"] = _box(c)


def _nudged(dx: float, dy: float):
    def step(c: Ctx) -> None:
        x0, y0, x1, y1 = c.data["box"]
        assert _box(c) == (x0 + dx, y0 + dy, x1 + dx, y1 + dy), (c.data["box"], _box(c))

    return step


for _name, (_dx, _dy) in {"left": (-0.25, 0), "up": (0, -0.25), "right": (0.25, 0),
                          "down": (0, 0.25)}.items():
    helper(f"effect.sablon_nudged_{_name}")(_nudged(_dx, _dy))
for _name, (_dx, _dy) in {"left": (-1, 0), "up": (0, -1), "right": (1, 0),
                          "down": (0, 1)}.items():
    helper(f"effect.sablon_nudged_big_{_name}")(_nudged(_dx, _dy))


@helper("feedback.sablon_nudged")
def _feedback_nudged(c: Ctx) -> None:
    s = _s(c)
    x0, y0 = _box(c)[:2]
    texts = slot_texts(c.win, "sablonlar")
    fmt = lambda v: f"{v:g}".replace(".", ",")  # noqa: E731
    assert any(t.startswith(f"Kutu x {fmt(x0)}") and f"y {fmt(y0)}" in t for t in texts), texts
    assert any(t.startswith("Kaydır: ok tuşları 0,25 mm") for t in texts), texts
    assert s.undo_stack.undoText() == "Kutuyu taşı"
    assert_focus_ring(c.win)


@helper("broken.sablon_no_box_on_canvas")
def _broken_no_box_on_canvas(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", None)  # a variable, no box chosen; the canvas has focus


@helper("na.sablon_box_stays")
def _na_box_stays(c: Ctx) -> None:
    """No box chosen: the arrow does not move any box (it scrolls the view; M-40: accepted)."""
    _unchanged(c)


@helper("pre.sablon_space")
def _pre_space(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", 0)
    c.data["box"] = _box(c)


@helper("effect.sablon_hand")
def _effect_hand(c: Ctx) -> None:
    """The harness pressed and released Space (a click): nothing may stay stuck. Then Space is
    held: the cursor is the open hand and a drag pans the page, not the box."""
    s = _s(c)
    canvas = s.canvas
    assert not canvas._space
    canvas.set_zoom(400)
    settle()
    view = canvas.viewport()
    QTest.keyPress(canvas, Qt.Key.Key_Space)
    try:
        assert canvas._space
        assert view.cursor().shape() == Qt.CursorShape.OpenHandCursor
        h0, v0 = canvas.horizontalScrollBar().value(), canvas.verticalScrollBar().value()
        start = view.rect().center()
        QTest.mousePress(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start)
        QTest.mouseMove(view, start - QPoint(60, 60))
        QTest.mouseRelease(view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                           start - QPoint(60, 60))
        settle()
        assert (canvas.horizontalScrollBar().value(), canvas.verticalScrollBar().value()) \
            != (h0, v0), "the drag did not pan the page"
    finally:
        QTest.keyRelease(canvas, Qt.Key.Key_Space)
    assert _box(c) == c.data["box"], "the drag moved the box"


@helper("feedback.sablon_hand")
def _feedback_hand(c: Ctx) -> None:
    canvas = _s(c).canvas
    assert not canvas._space
    assert canvas.viewport().cursor().shape() == Qt.CursorShape.ArrowCursor, "cursor not back"


@helper("broken.sablon_focus_on_list")
def _broken_focus_on_list(c: Ctx) -> None:
    ensure_template(c)
    choose(c, "Sicil_No", None, "variables")


@helper("na.sablon_space_ignored")
def _na_space_ignored(c: Ctx) -> None:
    """Without canvas focus Space is not the hand tool."""
    canvas = _s(c).canvas
    assert not canvas._space
    assert canvas.viewport().cursor().shape() != Qt.CursorShape.OpenHandCursor
    _unchanged(c)


_M36 = "M-36 Q-08: no template or page: the key is disabled and silent; INTENDED status line"
_M35 = "M-35 Q-08: {why}: the key is disabled and silent; INTENDED status line {text!r}"


def _plan(pre, effect, feedback, **kw):
    return Plan(pre=pre, snap="snap.sablon", effect=effect, feedback=feedback,
                window="job_sablon", **kw)


PLANS["sablonlar.kutu_ciz"] = _plan(
    "pre.sablon_page", "effect.sablon_drawing_on", "feedback.sablon_drawing_on",
    na_pre="pre.none", na="na.says.sablon_no_page_b", xfail={"na": f"{_M36} {P_NO_PAGE_B!r}"})
PLANS["sablonlar.izgara"] = _plan(
    "pre.sablon_page", "effect.sablon_snap_flipped", "feedback.sablon_snap_flipped",
    na_pre="pre.none", na="na.says.sablon_no_page_g", xfail={"na": f"{_M36} {P_NO_PAGE_G!r}"})
PLANS["sablonlar.dene"] = _plan(
    "pre.sablon_dene", "effect.sablon_dene", "feedback.sablon_dene", na_pre="pre.none",
    na="na.says.sablon_no_page_dene", marks=(needs_tesseract,))
PLANS["sablonlar.kutu_sil"] = _plan(
    "pre.sablon_box_chosen", "effect.sablon_box_deleted", "feedback.sablon_box_deleted",
    na_pre="pre.none", na="na.says.sablon_nothing_chosen",
    xfail={"na": _M35.format(why="no variable chosen", text=P_NOTHING_CHOSEN)})
PLANS["sablonlar.kutu_cogalt"] = _plan(
    "pre.sablon_box_one", "effect.sablon_box_copied", "feedback.sablon_box_copied",
    na_pre="pre.sablon_no_box_chosen", na_window="job_sablon", na="na.sablon_stays_and_says_no_box",
    xfail={"na": _M35.format(why="no box chosen", text=P_NO_BOX)})
PLANS["sablonlar.degisken_ekle"] = _plan(
    "pre.sablon_add_variable", "effect.sablon_variable_added", "feedback.sablon_variable_added",
    na_pre="pre.none", na="na.says.sablon_no_template",
    xfail={"na": _M35.format(why="no template", text=P_NO_TEMPLATE)})
PLANS["sablonlar.yukari"] = _plan(
    "pre.sablon_second_variable", "effect.sablon_moved_up", "feedback.sablon_moved_up",
    na_pre="pre.sablon_first_variable", na_window="job_sablon", na="na.sablon_stays_and_says_first",
    xfail={"na": _M35.format(why="already first", text=P_FIRST)})
PLANS["sablonlar.asagi"] = _plan(
    "pre.sablon_first_variable", "effect.sablon_moved_down", "feedback.sablon_moved_down",
    na_pre="pre.sablon_second_variable", na_window="job_sablon",
    na="na.sablon_stays_and_says_last", xfail={"na": _M35.format(why="already last",
                                                                  text=P_LAST)})
for _key, _name in (("Left", "left"), ("Up", "up"), ("Right", "right"), ("Down", "down")):
    PLANS["sablonlar.kaydir", "sablonlar", _key] = _plan(
        "pre.sablon_nudge", f"effect.sablon_nudged_{_name}", "feedback.sablon_nudged",
        na_pre="pre.none", na_window="job_sablon", broken="broken.sablon_no_box_on_canvas",
        na="na.sablon_box_stays")
for _key, _name in (("Shift+Left", "left"), ("Shift+Up", "up"), ("Shift+Right", "right"),
                    ("Shift+Down", "down")):
    PLANS["sablonlar.kaydir_1mm", "sablonlar", _key] = _plan(
        "pre.sablon_nudge", f"effect.sablon_nudged_big_{_name}", "feedback.sablon_nudged",
        na_pre="pre.none", na_window="job_sablon", broken="broken.sablon_no_box_on_canvas",
        na="na.sablon_box_stays")
PLANS["sablonlar.el"] = _plan(
    "pre.sablon_space", "effect.sablon_hand", "feedback.sablon_hand", na_pre="pre.none",
    na_window="job_sablon", broken="broken.sablon_focus_on_list", na="na.sablon_space_ignored")
