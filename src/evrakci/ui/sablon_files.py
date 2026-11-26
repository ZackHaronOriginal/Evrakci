"""Şablonlar: whole templates in the window (Ş-1) - rename, copy, delete, export, import.

Every file change goes through `TemplateStore` (atomic writes). A rename is an ordinary
undoable edit of the open template. A copy opens the copy. A delete keeps the file's exact
bytes and offers "Geri al": the undo writes those bytes back in one atomic step, so the
template returns as it was (same id, same file) and nothing else changes.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QFileDialog, QMenu

from evrakci.pipeline.templates.model import TemplateError

TEMPLATE_MENU = ("sablonlar.sablon_adlandir", "sablonlar.sablon_cogalt", "sablonlar.sablon_sil",
                 None, "sablonlar.sablon_disa", "sablonlar.sablon_ice")
FILE_FILTER = "Şablon dosyası (*.json)"
UNDO_MS = 15000


class TemplateFiles:
    """Mixed into SablonScreen: needs store, template, templates, message, _edit, _toast."""

    def template_context_menu(self, pos: QPoint) -> None:
        item = self.templates.itemAt(pos)
        if item is not None and item is not self.templates.currentItem():
            self.templates.setCurrentItem(item)  # the menu acts on the open template
        menu = QMenu(self)
        menu.setAccessibleName("Şablon komutları")
        self._fill_menu(menu, TEMPLATE_MENU)
        if not menu.isEmpty():
            menu.exec(self.templates.viewport().mapToGlobal(pos))
        menu.deleteLater()

    # -- rename and copy ------------------------------------------------------------
    def rename_template(self, name: str | None = None) -> None:
        """Yeniden adlandır: an undoable edit of the open template's name."""
        if self.template is None:
            return
        if name is None:
            name = self._ask_text("Şablonu yeniden adlandır", "Şablonun yeni adı", "Adlandır",
                                  self.template.name)
        if not name:
            return
        from evrakci.pipeline.templates.store import clean_name

        try:
            name = clean_name(name)
        except TemplateError as error:
            self.message.setText(str(error))
            return
        if name == self.template.name:
            return
        name = self.store.unique_name(name, exclude=self.template.id)
        if self._edit("Şablonu yeniden adlandır", lambda t: setattr(t, "name", name)):
            self.refresh_templates()  # the list is in name order

    def copy_template(self) -> None:
        """Çoğalt: a copy "Ad (kopya)" with every variable and box; the copy opens."""
        if self.template is None:
            return
        self.flush_save()
        try:
            copy = self.store.duplicate(self.template.id)
        except (TemplateError, KeyError, OSError) as error:
            self.message.setText(str(error) if isinstance(error, TemplateError)
                                 else "Şablon kopyalanamadı.")
            return
        self._show_template(copy.id)

    def _show_template(self, template_id: str) -> None:
        """Open a template that was just written: the list marks it, the screen loads it."""
        try:
            self.template = self.store.load(template_id)
        except (TemplateError, KeyError):
            self.refresh_templates()
            return
        self.refresh_templates()
        self.open_template(template_id)

    # -- delete, undoable -------------------------------------------------------------
    def delete_template(self) -> None:
        """Sil: the file goes, the toast "Geri al" brings back the very same bytes."""
        template = self.template
        if template is None:
            return
        self.flush_save()
        try:
            data = self.store.raw(template.id)
            self.store.delete(template.id)
        except (KeyError, OSError):
            self.message.setText("Şablon silinemedi.")
            return
        template_id, name = template.id, template.name
        self.template, self.variable_name, self.section_index = None, None, None
        self.undo_stack.clear()
        self.refresh_templates()  # opens the next template, or shows the empty screen

        def undo() -> None:
            self._restore_deleted(template_id, data)

        def available() -> bool:
            return not (self.store.root / f"{template_id}.json").exists()

        self._toast(f"“{name}” şablonu silindi.", "Geri al", undo, timeout_ms=UNDO_MS,
                    available=available)

    def _restore_deleted(self, template_id: str, data: bytes) -> None:
        try:
            self.store.restore(template_id, data)
        except (TemplateError, OSError) as error:
            self.message.setText(str(error) if isinstance(error, TemplateError)
                                 else "Şablon geri getirilemedi.")
            return
        self._show_template(template_id)

    # -- export and import --------------------------------------------------------------
    def export_template(self, path: str | Path | None = None) -> None:
        """Dışa aktar: one .json file anywhere; an existing file is never written over."""
        if self.template is None:
            return
        self.flush_save()
        if path is None:
            start = f"{self.template.name}.json"
            path, _ = QFileDialog.getSaveFileName(
                self, "Şablonu dışa aktar", start, FILE_FILTER,
                options=QFileDialog.Option.DontConfirmOverwrite)
            if not path:
                return
        try:
            self.store.export(self.template.id, Path(path))
        except (TemplateError, KeyError, OSError) as error:
            self.message.setText(str(error) if isinstance(error, TemplateError)
                                 else "Şablon dışa aktarılamadı.")
            return
        self.message.setText("")
        self._toast("Şablon dışa aktarıldı.", kind="success")

    def import_template(self, path: str | Path | None = None) -> None:
        """İçe aktar: a new template with a new id and a name that is not taken."""
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "Şablonu içe aktar", "", FILE_FILTER)
            if not path:
                return
        self.flush_save()
        try:
            imported = self.store.import_file(Path(path))
        except (TemplateError, OSError) as error:
            self.message.setText(str(error) if isinstance(error, TemplateError)
                                 else "Şablon içe aktarılamadı.")
            return
        self._show_template(imported.id)
        self._toast("Şablon içe aktarıldı.", kind="success")
