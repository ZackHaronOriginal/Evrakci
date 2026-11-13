"""Screenshots of every tab with invented demo data (never real documents).

    QT_QPA_PLATFORM=offscreen python tools/screenshots.py OUT_DIR  # README
    QT_QPA_PLATFORM=offscreen python tools/screenshots.py matrix OUT_DIR  # full matrix
    QT_QPA_PLATFORM=offscreen python tools/screenshots.py matrix --allow OUT_DIR  # report only

Builds a throwaway job (fake scanned pages, QR separators, two templates, some values that
need a check) in a temp folder. The matrix mode saves OUT_DIR/<tab>-<theme>-<w>x<h>-<text>.png
for 6 tabs x {light, dark, hc} x {1366x768, 1920x1080} x text {100, 150}; each theme and text
size gets a window built fresh in it (the shots never show a runtime switch). It prints a
clipping report (elided text: drawn "…", text wider than its room, combo boxes against their
edit field; widgets outside the window) and exits 1 when anything is found, unless --allow.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from fakes import empty_page, make_pdf, qr_page, text_page  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractButton,
    QAbstractScrollArea,
    QApplication,
    QComboBox,
    QLabel,
    QStyle,
    QStyleOptionComboBox,
    QToolButton,
    QWidget,
)

from evrakci.app import configure_application  # noqa: E402
from evrakci.pipeline.cuts import record_values  # noqa: E402
from evrakci.pipeline.store import JobStore  # noqa: E402
from evrakci.pipeline.templates.model import Section  # noqa: E402
from evrakci.pipeline.templates.store import TemplateStore  # noqa: E402
from evrakci.pipeline.templates.values import VariableValue  # noqa: E402
from evrakci.ui import theme  # noqa: E402
from evrakci.ui.main_window import TAB_NAMES, MainWindow  # noqa: E402

SLUGS = ["yukle", "kontrol", "sablonlar", "degerler", "disa-aktar", "rehber"]


def build(root: Path) -> MainWindow:
    root.mkdir(parents=True, exist_ok=True)
    pages = [text_page("A"), text_page(), text_page(), qr_page(), text_page("B"), text_page(),
             text_page(), empty_page(), text_page("C"), text_page(), text_page("D"),
             qr_page(), text_page("E"), text_page(), text_page()]
    pdf = make_pdf(root / "tarama-2026-11-04-0912.pdf", pages)
    pdf2 = make_pdf(root / "tarama-2026-11-04-1047.pdf", [text_page("F"), text_page()])
    store = JobStore(root / "jobs")
    templates = TemplateStore(root / "tpl")
    template = templates.create("Kapasite Raporu")
    sicil = template.add_variable("Sicil_No", required=True)
    firma = template.add_variable("Firma_Adi")
    template.add_section("Sicil_No", Section(1, (20, 30, 90, 42)))
    template.add_section("Firma_Adi", Section(1, (20, 50, 140, 62)))
    template.set_pattern("{Sicil_No}_{Firma_Adi}")
    templates.save(template)
    other = templates.create("Faaliyet Belgesi")
    other.add_variable("Sicil_No", required=True)
    templates.save(other)

    job = store.create_job("Kasım 2026 – Faaliyet belgeleri", [pdf])
    store.create_job("Ekim 2026 – Kapasite raporları", [pdf2])
    window = MainWindow(store, templates, settings_path=root / "ayar.json")
    window.yukle.open_job(store.load(job.id))
    ctl = window.controller()
    ids = ctl.job.ordered_page_ids()
    ctl.apply_template(ids, template.id)
    names = ["Ege Kalıp San. Ltd.", "Akçay Tekstil San. ve Tic. Ltd. Şti.", "Doğan Tekstil Ltd."]
    for n, doc in enumerate(ctl.documents()):
        if n == 1:
            values = {sicil.key: VariableValue("48Z13", 0.41, 0, True, "48213", (), False),
                      firma.key: VariableValue(names[1], 0.9, 0, False)}
        else:
            values = {sicil.key: VariableValue(f"4819{n}", 0.95, 0, False),
                      firma.key: VariableValue(names[n % 3], 0.92, 0, False)}
        record_values(ctl.job, doc, template.id, values)
    ctl.job_changed.emit()
    return window


THEMES = ("light", "dark", "hc")
SIZES = ((1366, 768), (1920, 1080))
TEXTS = (100, 150)
ELLIPSES = ("…", "...")


def _settle(app: QApplication, rounds: int = 30) -> None:
    for _ in range(rounds):
        app.processEvents()


def _shown_text(w: QWidget) -> tuple[str, str, int | None] | None:
    """(full text, text as drawn, room in px or None when the widget elides by itself) of a
    one-line text widget, else None."""
    if isinstance(w, QComboBox):
        option = QStyleOptionComboBox()
        w.initStyleOption(option)
        field = w.style().subControlRect(QStyle.ComplexControl.CC_ComboBox, option,
                                         QStyle.SubControl.SC_ComboBoxEditField, w)
        return w.currentText(), w.currentText(), field.width()
    if hasattr(w, "displayed_text") and hasattr(w, "is_elided"):  # ElidedLabel, KeyHintButton
        full = w.full_text() if hasattr(w, "full_text") else w.text()
        return full, w.displayed_text() if w.is_elided() else full, None
    if (isinstance(w, QToolButton)
            and w.toolButtonStyle() == Qt.ToolButtonStyle.ToolButtonIconOnly):
        return None  # its text is a name (tooltip, line-edit action), never drawn
    if isinstance(w, (QLabel, QAbstractButton)):
        if isinstance(w, QLabel) and w.wordWrap():
            return None
        text = w.text().replace("&", "")
        return text, text, w.contentsRect().width()
    return None


def _scrolled(widget: QWidget) -> bool:
    """True inside a scroll area's viewport: scrolled out of view is not clipped."""
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QAbstractScrollArea) and parent.viewport().isAncestorOf(widget):
            return True
        parent = parent.parentWidget()
    return False


def clipping(window: QWidget, label: str) -> list[str]:
    """Visible text widgets that are elided ("…" drawn or text wider than its room) and
    widgets outside the window (README §3.3: nothing clipped, nothing elided)."""
    found = []
    bounds = window.rect()
    for w in window.findChildren(QWidget):
        if not w.isVisible() or w.width() <= 0 or w.height() <= 0:
            continue
        name = f"{label} {type(w).__name__}#{w.objectName() or '-'}"
        box = w.rect().translated(w.mapTo(window, w.rect().topLeft()))
        if not bounds.adjusted(-1, -1, 1, 1).contains(box) and not _scrolled(w):
            found.append(f"{name} dışarıda: {box.getRect()}")
        shown = _shown_text(w)
        if shown is None:
            continue
        full, drawn, room = shown
        if not full or "\n" in full or "<" in full:
            continue
        need = w.fontMetrics().horizontalAdvance(drawn)
        if drawn != full or any(e in drawn and e not in full for e in ELLIPSES):
            found.append(f"{name} kısaltılmış: {full!r} -> {drawn!r}")
        elif room is not None and need > room:
            found.append(f"{name} kısaltılmış: {full!r} ({need}>{room})")
        elif any(drawn.endswith(e) for e in ELLIPSES) and isinstance(w, QLabel):
            found.append(f"{name} '…' ile bitiyor: {drawn!r}")
    return found


def run_matrix(app: QApplication, tmp: Path, out: Path) -> list[str]:
    """Every shot comes from a window built fresh in its theme and text size (no runtime
    switching), resized to each window size; returns the clipping report."""
    manager = theme.manager()
    clipped: list[str] = []
    count = 0
    for text in TEXTS:
        for mode in THEMES:
            manager.set_text_scale(text)
            manager.set_mode(mode)
            _settle(app)
            window = build(tmp / f"{mode}-{text}")
            window.show()
            for width, height in SIZES:
                window.resize(width, height)
                for index, slug in enumerate(SLUGS):
                    window.tabs.setCurrentIndex(index)
                    _settle(app)
                    name = f"{slug}-{mode}-{width}x{height}-{text}"
                    window.grab().save(str(out / f"{name}.png"))
                    count += 1
                    clipped += clipping(window, name)
            window.close()
            window.deleteLater()
            _settle(app)
    for line in clipped:
        print("KIRPILMA", line)
    print(f"ÖZET: {count} görüntü, {len(clipped)} kırpılma/taşma")
    return clipped


def main() -> int:
    flags = {a for a in sys.argv[1:] if a.startswith("--") or a == "matrix"}
    args = [a for a in sys.argv[1:] if a not in flags]
    matrix = bool(flags & {"--matrix", "matrix"})
    out = Path(args[0] if args else "docs/screenshots")
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    configure_application(app)
    with tempfile.TemporaryDirectory() as tmp:
        if matrix:
            clipped = run_matrix(app, Path(tmp), out)
            return 0 if not clipped or "--allow" in flags else 1
        root = Path(tmp) / "readme"
        root.mkdir()
        window = build(root)
        window.resize(1366, 768)
        window.show()
        for index, slug in enumerate(SLUGS):
            window.tabs.setCurrentIndex(index)
            _settle(app)
            window.grab().save(str(out / f"{slug}.png"))
            print(out / f"{slug}.png", TAB_NAMES[index])
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
