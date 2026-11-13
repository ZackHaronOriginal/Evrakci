"""Whole-card scrolling of the side panels (PROPOSALS 1 and 5, approved 2026-11-13):
a panel never shows part of a card, scrolls card by card, draws the 1 px hairline above its
pinned buttons only while there is more below, and is unchanged when everything fits."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QAbstractSlider,
    QApplication,
    QFrame,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui.card_scroll import CardScroll

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import screenshots  # noqa: E402

PANELS = {  # tab -> (screen attribute, path to its CardScroll)
    "yukle": ("yukle", "side.card_scroll"),
    "kontrol": ("kontrol", "side.card_scroll"),
    "sablonlar": ("sablon", "side.card_scroll"),
    "degerler": ("degerler", "side.card_scroll"),
    "disa_aktar": ("disa_aktar", "side.card_scroll"),
    "rehber": ("rehber", "card_scroll"),
}


def _settle(rounds: int = 5) -> None:
    for _ in range(rounds):
        QApplication.processEvents()


def _cards(area: QScrollArea) -> list[QWidget]:
    body = area.widget()
    return [w for w in body.findChildren(QWidget)
            if w.property("kind") == "card" and w.isVisibleTo(body)]


def _shown(area: QScrollArea):
    port = area.viewport()
    mask = port.mask()
    return port.rect() if mask.isEmpty() else mask.boundingRect().intersected(port.rect())


def _partial_cards(area: QScrollArea) -> list[tuple]:
    """Cards of which only a part is in the shown viewport (a geometry check, not the
    screenshot tool's)."""
    port = area.viewport()
    shown = _shown(area)
    found = []
    for card in _cards(area):
        box = card.rect().translated(card.mapTo(port, QPoint(0, 0)))
        inside = shown.intersected(box)
        if not inside.isEmpty() and inside != box:
            found.append(box.getRect())
    return found


def _wheel(widget: QWidget, notches: int) -> None:
    centre = QPointF(widget.width() / 2, widget.height() / 2)
    event = QWheelEvent(centre, widget.mapToGlobal(centre), QPoint(0, 0),
                        QPoint(0, 120 * notches), Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(widget, event)


@pytest.fixture
def panel(qtbot):
    """A side panel: six cards (each with a group label and a field) in a scroll area, a
    pinned primary button under it."""
    host = QWidget()
    qtbot.addWidget(host)
    outer = QVBoxLayout(host)
    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    body = QWidget()
    column = QVBoxLayout(body)
    column.setSpacing(12)
    fields = []
    for index, height in enumerate((90, 140, 70, 120, 90, 60)):
        from PySide6.QtWidgets import QLabel

        column.addWidget(QLabel(f"Grup {index}"))
        card = QFrame()
        card.setProperty("kind", "card")
        card.setFixedHeight(height)
        field = QLineEdit(card)
        field.move(8, 8)
        fields.append(field)
        column.addWidget(card)
    column.addStretch(1)
    area.setWidget(body)
    outer.addWidget(area, 1)
    button = QPushButton("Kaydet")
    outer.addWidget(button)
    scroller = CardScroll(area, button)
    host.resize(320, 360)
    host.show()
    _settle()
    return host, area, scroller, fields


def test_the_panel_only_ever_shows_whole_cards(panel):
    host, area, scroller, fields = panel
    assert scroller.scrollable()
    bar = area.verticalScrollBar()
    seen = set()
    for _ in range(10):  # the wheel, one card per notch, to the end and past it
        assert _partial_cards(area) == []
        assert bar.value() in scroller.stops()
        seen.add(bar.value())
        _wheel(area.viewport(), -1)
        _settle()
    assert bar.value() == scroller.stops()[-1] == bar.maximum()
    assert seen == set(scroller.stops())
    for _ in range(10):  # the scroll bar's arrows and page steps, back up
        bar.triggerAction(QAbstractSlider.SliderAction.SliderSingleStepSub)
        _settle()
        assert _partial_cards(area) == [] and bar.value() in scroller.stops()
    assert bar.value() == 0
    bar.triggerAction(QAbstractSlider.SliderAction.SliderPageStepAdd)
    _settle()
    assert _partial_cards(area) == [] and bar.value() in scroller.stops() and bar.value() > 0
    bar.setValue(bar.value() + 7)  # any other way the value moves still lands on a stop
    _settle()
    assert _partial_cards(area) == [] and bar.value() in scroller.stops()


def test_the_space_under_the_last_whole_card_stays_empty(panel):
    _host, area, scroller, _fields = panel
    port = area.viewport()
    assert not port.mask().isEmpty()  # the panel scrolls, so the viewport is trimmed
    bottom = scroller.shown_bottom()
    assert _shown(area).height() == bottom - area.verticalScrollBar().value() + 1
    assert _shown(area).height() < port.height()


def test_focus_moving_into_a_hidden_card_shows_that_card_whole(panel):
    _host, area, scroller, fields = panel
    fields[-1].setFocus()
    _settle()
    assert _partial_cards(area) == []
    port = area.viewport()
    card = fields[-1].parentWidget()
    box = card.rect().translated(card.mapTo(port, QPoint(0, 0)))
    assert _shown(area).contains(box)
    fields[0].setFocus()
    _settle()
    card = fields[0].parentWidget()
    box = card.rect().translated(card.mapTo(port, QPoint(0, 0)))
    assert _shown(area).contains(box) and _partial_cards(area) == []


def test_hairline_shows_only_while_there_is_more_below(panel):
    host, area, scroller, _fields = panel
    edge = scroller.edge
    assert edge is not None and edge.isVisible() and edge.height() == 1
    button = host.findChild(QPushButton)
    assert area.geometry().bottom() < edge.y() < button.y()  # in the gap, above the buttons
    scroller.step(99)
    _settle()
    assert not scroller.more_below() and not edge.isVisible()
    scroller.step(-99)
    _settle()
    assert edge.isVisible()
    host.resize(320, 1400)  # everything fits: no scrolling, no hairline, no mask
    _settle()
    assert not scroller.scrollable() and not edge.isVisible()
    assert area.viewport().mask().isEmpty() and area.verticalScrollBar().maximum() == 0


def test_strict_clipping_reports_a_card_cut_even_with_a_scroll_bar(qtbot):
    """The screenshot check: a card cut by a scroll area's edge is clipped, scroll bar or
    not (the old exception is gone); long lists (item views) may show a part row."""
    area = QScrollArea()
    qtbot.addWidget(area)
    area.setWidgetResizable(True)
    content = QWidget()
    column = QVBoxLayout(content)
    cards = []
    for _ in range(4):
        card = QFrame()
        card.setProperty("kind", "card")
        card.setFixedHeight(90)
        column.addWidget(card)
        cards.append(card)
    area.setWidget(content)
    area.resize(300, 170)
    area.show()
    _settle()
    assert area.verticalScrollBar().isVisible()
    assert any(screenshots._cut_by_scroll_edge(c) for c in cards)
    CardScroll(area)  # whole cards only: nothing cut any more
    _settle()
    assert not any(screenshots._cut_by_scroll_edge(c) for c in cards)


def _screen_scroller(window, tab: str) -> CardScroll:
    attr, path = PANELS[tab]
    obj = getattr(window, attr)
    for part in path.split("."):
        obj = getattr(obj, part)
    return obj


@pytest.mark.parametrize("text, height", [(150, 768), (150, 560), (100, 768)])
def test_every_side_panel_at_1366_wide(qtbot, tmp_path, text, height):
    """At 150 % no panel shows part of a card, at every stop; the hairline is there exactly
    while more is below. At 100 % the panels that fit do not scroll, trim or draw a line.
    (In-process the app font differs from the screenshot matrix, so 560 px makes sure
    several panels really scroll.)"""
    from evrakci.ui import theme

    manager = theme.manager()
    manager.set_text_scale(text)
    try:
        window = screenshots.build(tmp_path / "w")
        qtbot.addWidget(window)
        window.resize(1366, height)
        window.show()
        app = QApplication.instance()
        scrolled = 0
        for tab in PANELS:
            window.show_tab(tab)
            # wait for the Kontrol thumbnails: their workers must not still be reading the PDFs
            # when the next test writes its own (PDFium is not thread-safe)
            screenshots._settle(app, window=window)
            scroller = _screen_scroller(window, tab)
            scroller.refresh()
            area = scroller.area
            if text == 100:
                assert not scroller.scrollable(), tab
                assert area.viewport().mask().isEmpty(), tab
                assert scroller.edge is None or not scroller.edge.isVisible(), tab
                continue
            scrolled += scroller.scrollable()
            for _stop in scroller.stops():
                assert _partial_cards(area) == [], tab
                if scroller.edge is not None:
                    assert scroller.edge.isVisible() == scroller.more_below(), tab
                scroller.step(1)
                _settle()
            assert _partial_cards(area) == [], tab
            scroller.step(-99)
            screenshots._settle(app, window=window)
        if height == 560:
            assert scrolled >= 3, scrolled
    finally:
        manager.set_text_scale(100)


def test_a_card_scrolls_in_with_its_group_label(panel):
    _host, area, scroller, _fields = panel
    from PySide6.QtWidgets import QLabel

    scroller.step(1)
    _settle()
    port = area.viewport()
    label = next(w for w in area.widget().findChildren(QLabel) if w.text() == "Grup 1")
    box = label.rect().translated(label.mapTo(port, QPoint(0, 0)))
    assert 0 <= box.top() <= 12  # the stop is the label's top, not its card's
    assert _shown(area).contains(box)
