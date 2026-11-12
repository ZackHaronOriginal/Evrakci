"""Screenshots of every tab with invented demo data (never real documents).

    QT_QPA_PLATFORM=offscreen python tools/screenshots.py OUT_DIR

Builds a throwaway job (fake scanned pages, QR separators, two templates, some values that
need a check) in a temp folder and saves one 1366x768 PNG per tab.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from fakes import empty_page, make_pdf, qr_page, text_page  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from evrakci.app import configure_application  # noqa: E402
from evrakci.pipeline.cuts import record_values  # noqa: E402
from evrakci.pipeline.store import JobStore  # noqa: E402
from evrakci.pipeline.templates.model import Section  # noqa: E402
from evrakci.pipeline.templates.store import TemplateStore  # noqa: E402
from evrakci.pipeline.templates.values import VariableValue  # noqa: E402
from evrakci.ui.main_window import TAB_NAMES, MainWindow  # noqa: E402

SLUGS = ["yukle", "kontrol", "sablonlar", "degerler", "disa-aktar", "rehber"]


def build(root: Path) -> MainWindow:
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


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/screenshots")
    out.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    configure_application(app)
    with tempfile.TemporaryDirectory() as tmp:
        window = build(Path(tmp))
        window.resize(1366, 768)
        window.show()
        for index, slug in enumerate(SLUGS):
            window.tabs.setCurrentIndex(index)
            for _ in range(30):
                app.processEvents()
            window.grab().save(str(out / f"{slug}.png"))
            print(out / f"{slug}.png", TAB_NAMES[index])
        window.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
