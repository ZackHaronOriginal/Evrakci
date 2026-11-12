import re
from pathlib import Path

from PySide6.QtGui import QFontMetrics

from evrakci.ui import icons, theme
from evrakci.ui.widgets import Heading, KeyHintButton, Rider, StateLabel, key_button

ROOT = Path(__file__).resolve().parents[2]


def test_every_icon_renders(qtbot):
    for name in icons.PATHS:
        assert not icons.pixmap(name, "ink", 18).isNull(), name
        assert not icons.icon(name, "qr").isNull(), name


def test_icon_files_for_the_stylesheet_exist(qtbot):
    css = theme.stylesheet()
    for path in re.findall(r'url\("([^"]+)"\)', css):
        assert Path(path).is_file(), path


def test_app_icon_is_the_packaged_drawing():
    packaged = (ROOT / "packaging/linux/evrakci.svg").read_text(encoding="utf-8")
    shapes = re.findall(r"<(?:rect|path)[^>]*>", re.sub(r"\s+", " ", packaged))
    assert shapes and all(shape.replace(" />", "/>") in icons.APP_ICON_SVG for shape in shapes)


def test_key_hint_button_keeps_its_plain_label(qtbot):
    button = key_button("Filtreyi uygula", "F", primary=True, icon="funnel")
    qtbot.addWidget(button)
    assert isinstance(button, KeyHintButton)
    assert button.text() == "Filtreyi uygula"
    assert button.property("primary") is True
    assert "(F)" in button.toolTip()


def test_key_hint_button_asks_for_room_for_icon_label_and_key(qtbot):
    plain = key_button("Dışa aktar")
    full = key_button("Dışa aktar", "Ctrl+E", icon="drop")
    qtbot.addWidget(plain)
    qtbot.addWidget(full)
    label = QFontMetrics(plain._label_font()).horizontalAdvance("Dışa aktar")
    assert plain.sizeHint().width() > label
    assert full.sizeHint().width() > plain.sizeHint().width() + 18
    assert full.sizeHint().height() == 34


def test_icon_only_button_is_square_and_named_in_its_tooltip(qtbot):
    button = key_button("Yinele", icon="redo", icon_only=True)
    qtbot.addWidget(button)
    assert button.sizeHint().width() == 34
    assert button.toolTip() == "Yinele"


def test_heading_rider_and_state_text(qtbot):
    heading = Heading("Belge 1 — Belge 3", "Sayfa 1–9")
    rider = Rider()
    state = StateLabel("check")
    for widget in (heading, rider, state):
        qtbot.addWidget(widget)
    heading.setText("Belge 2", "")
    assert heading.text() == "Belge 2" and heading.subtitle.isHidden()
    assert rider.text() == "Kontrol" and rider.sizeHint().height() == 21
    assert state.word.text() == "Kontrol"
    rider.grab()  # paints without errors
    heading.grab()
