"""Kontrol's saved-filter chips (I-07): what KontrolScreen does with `kontrol_chips.ChipRow`.

The row shows the chips of the template in the inspector (`_template_for_selection`). Turned-on
chips are one `select.select_pages` call (AND), the same call `is sec --sablon` makes; the
pages it gives become the timeline selection and the row's count line says how many filters
are on and how many pages they give. Turning every chip off clears only a selection the chips
made. "Kayıtlı filtrelere ekle…" appears while the selection is exactly what a "select by"
result chose; saving, renaming and deleting are edits of the template (an undo step on the
Şablonlar stack, a toast with Geri al).

A mixin, so kontrol.py stays about the timeline.
"""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import QTimer
from PySide6.QtGui import QUndoStack

from evrakci.pipeline.select import Criterion, kinds, select_pages
from evrakci.pipeline.templates.model import Template, TemplateError, template_to_dict
from evrakci.ui.feedback import undo_last
from evrakci.ui.kontrol_chips import (
    NO_TEMPLATE,
    NOT_KNOWN_TIP,
    ChipInfo,
    ChipRow,
    SaveFilterDialog,
    count_text,
)
from evrakci.ui.kontrol_dialogs import SelectDialog

ADD_STEP = "Kayıtlı filtre ekle"
DELETED = "Kayıtlı filtre silindi"
RENAME_STEP = "Yeniden adlandır"
KIND_NAMES = {kind: label for kind, label, _hint in SelectDialog.ROWS}


class SavedFiltersMixin:
    """State and methods of the chip row; the host is a KontrolScreen."""

    def _init_saved_filters(self) -> None:
        self.chips = ChipRow(self)
        self.chips.hide()
        self.chips.changed.connect(self._chips_changed)
        self.chips.save_requested.connect(self.add_saved_filter)
        self.chips.delete_requested.connect(self.delete_saved_filter)
        self.chips.rename_requested.connect(self.rename_saved_filter)
        self.chips.escape_requested.connect(self._chips_escape)
        self.chips.inert_pressed.connect(self._chip_inert)
        self.template_undo = QUndoStack(self)  # the window's Şablonlar stack once placed
        self._chip_owner_id: str | None = None
        self._chip_on: dict[str, set[str]] = {}  # template id -> names turned on
        self._chip_selection: tuple[str, ...] | None = None  # what the chips selected
        self._result: tuple[Criterion, frozenset[str]] | None = None  # a "select by" result
        self._chip_counts: dict[tuple[str, str], int] = {}
        self._chips_busy = False
        self._chips_timer = QTimer(self)
        self._chips_timer.setSingleShot(True)
        self._chips_timer.setInterval(0)
        self._chips_timer.timeout.connect(self._chips_recount)

    # -- which template, which chips -----------------------------------------------------------
    def _chips_template(self, templates: Mapping) -> Template | None:
        """The template the row belongs to. While the chips' own selection is still the
        selection the row stays with its template (their pages may carry another one)."""
        if (self._chip_selection is not None and self._chip_owner_id in templates
                and set(self._chosen_ids()) == set(self._chip_selection)):
            return templates[self._chip_owner_id]
        template_id = self._template_for_selection(templates)
        return templates.get(template_id) if template_id else None

    def _result_pending(self) -> bool:
        return self._result is not None and set(self._chosen_ids()) == self._result[1]

    def _chips_sync(self, templates: Mapping | None = None) -> None:
        """Show, hide and fill the row for the selection and the template as they are now."""
        row = self.chips
        templates = self.templates() if templates is None else templates
        template = self._chips_template(templates)
        owner = template.id if template is not None else None
        if owner != self._chip_owner_id:
            self._chip_owner_id = owner
            self._chip_selection = None
        pending = self._result_pending()
        if not pending:
            self._result = None
        filters = list(template.saved_filters) if template is not None else []
        visible = bool(filters) or pending
        row.setVisible(visible)
        if not visible:
            return
        on = self._chip_on.get(owner or "", set())
        known = set(kinds())
        infos = [ChipInfo(f.name, f.kind in known, self._chip_counts.get((owner or "", f.name)))
                 for f in filters]
        row.set_chips(infos, {n for n in on if any(f.name == n for f in filters)})
        row.set_note("" if template is not None else NO_TEMPLATE)
        row.set_can_save(template is not None and pending)
        self._chips_summary(template, templates)
        if any(i.count is None and i.known for i in infos):
            self._chips_timer.start()

    def _chips_invalidate(self) -> None:
        """The job or the template changed: the counts are stale, count again when idle."""
        self._chip_counts.clear()
        if hasattr(self, "chips") and not self.chips.isHidden():
            self._chips_timer.start()

    def _chips_recount(self) -> None:
        """Pages each chip gives alone (a chip that gives none is marked "0"), once per change
        of the job or the template: one pass over the pages per chip."""
        templates = self.templates()
        template = self._chips_template(templates)
        if template is None:
            return
        job = self.controller.job
        for item in template.saved_filters:
            if item.kind in kinds():
                result = select_pages(job, [Criterion(item.kind, item.params)], templates)
                self._chip_counts[(template.id, item.name)] = len(result.page_ids)
        self._chips_sync()

    # -- the chips and the selection -----------------------------------------------------------
    def _chips_criteria(self, template: Template) -> list[Criterion]:
        names = set(self.chips.on_names())
        return [Criterion(f.kind, f.params) for f in template.saved_filters
                if f.name in names and f.kind in kinds()]

    def _chips_summary(self, template: Template | None, templates: Mapping) -> None:
        if template is None:
            self.chips.set_count_text("")
            return
        criteria = self._chips_criteria(template)
        if not criteria:
            self.chips.set_count_text(count_text(0, 0))
            return
        found = select_pages(self.controller.job, criteria, templates)
        self.chips.set_count_text(count_text(len(criteria), len(found.page_ids)))

    def _chips_changed(self) -> None:
        """A chip was turned on or off: the pages they give become the selection."""
        templates = self.templates()
        template = self._chips_template(templates)
        if template is None:
            return
        self._chip_on[template.id] = set(self.chips.on_names())
        criteria = self._chips_criteria(template)
        self._chips_busy = True
        try:
            if criteria:
                found = select_pages(self.controller.job, criteria, templates)
                self._chip_selection = found.page_ids
                self.timeline.select_row_set(self.model.row_of(p) for p in found.page_ids)
                self._chip_owner_id = template.id
                self.chips.set_count_text(count_text(len(criteria), len(found.page_ids)))
                if not found.page_ids:
                    self.controller.status.emit("Eşleşen sayfa yok.")
            else:
                if (self._chip_selection is not None
                        and set(self._chosen_ids()) == set(self._chip_selection)):
                    self.timeline.selectionModel().clearSelection()
                self._chip_selection = None
                self.chips.set_count_text(count_text(0, 0))
        finally:
            self._chips_busy = False

    def _chip_inert(self, _name: str) -> None:
        self.controller.status.emit(NOT_KNOWN_TIP)

    def _chips_escape(self) -> None:
        self.timeline.setFocus()

    def focus_saved_filters(self) -> None:
        """Ctrl+Shift+F, Kayıtlı filtreler: focus goes to the chip row (Esc brings it back)."""
        self._chips_sync()
        if self.chips.isHidden() or not self.chips.focus_row():
            self.controller.status.emit(count_text(0, 0))

    # -- a "select by" result can be saved -----------------------------------------------------
    def _remember_result(self, criterion: Criterion, ids) -> None:
        self._result = (criterion, frozenset(ids))
        self._chips_sync()

    def add_saved_filter(self) -> None:
        """"Kayıtlı filtrelere ekle…": name the result and keep it with the template."""
        if not self._result_pending():
            return
        templates = self.templates()
        template = self._chips_template(templates)
        if template is None:
            return
        criterion = self._result[0]
        dialog = SaveFilterDialog("Kayıtlı filtrelere ekle", {f.name for f in
                                                              template.saved_filters},
                                  KIND_NAMES.get(criterion.kind, ""), self)
        if not dialog.exec():
            self.chips.focus_row()
            return
        name = dialog.name()
        if self._edit_template(template.id, ADD_STEP, lambda t: t.add_saved_filter(
                name, criterion.kind, criterion.to_dict()["params"])):
            self._result = None
            self._chips_invalidate()
            self._chips_sync()
            self._toast_template(f"Kayıtlı filtre eklendi: {name}")
            self.chips.focus_row()

    def delete_saved_filter(self, name: str) -> None:
        template = self._chips_template(self.templates())
        if template is None or not any(f.name == name for f in template.saved_filters):
            return
        number = next(n for n, c in enumerate(self.chips.chips) if c.info.name == name)
        self._chip_on.get(template.id, set()).discard(name)
        if self._edit_template(template.id, DELETED, lambda t: t.remove_saved_filter(name)):
            had_focus = any(c.hasFocus() for c in self.chips.chips)
            self._chips_changed_after_edit()
            if had_focus and self.chips.chips:
                self.chips._current = min(number, len(self.chips.chips) - 1)
                self.chips.focus_row()
            elif had_focus:
                self.timeline.setFocus()
            self._toast_template(DELETED)

    def rename_saved_filter(self, name: str) -> None:
        template = self._chips_template(self.templates())
        if template is None:
            return
        taken = {f.name for f in template.saved_filters} - {name}
        dialog = SaveFilterDialog(RENAME_STEP, taken, name, self)
        if not dialog.exec():
            self.chips.focus_row()
            return
        new = dialog.name()
        if new == name:
            return
        on = self._chip_on.get(template.id, set())
        if name in on:
            on.discard(name)
            on.add(new)
        if self._edit_template(template.id, RENAME_STEP,
                               lambda t: t.rename_saved_filter(name, new)):
            self._chips_changed_after_edit()
            self.chips.focus_row()

    def _chips_changed_after_edit(self) -> None:
        """The template's filters changed: rebuild the row and the selection of the chips left
        on (a deleted chip no longer narrows anything)."""
        self._chips_invalidate()
        templates = self.templates()
        template = self._chips_template(templates)
        self._chips_sync()
        if template is not None and self._chip_selection is not None:
            self._chips_changed()

    def _template_edited(self) -> None:
        """The Şablonlar stack moved (an undo or a redo of a filter step): show the result."""
        if hasattr(self, "chips"):
            self._chips_invalidate()
            self._chips_sync()

    # -- editing the template ------------------------------------------------------------------
    def _edit_template(self, template_id: str, text: str, change) -> bool:
        """Change the template `template_id` (the window saves it and keeps the undo step), or
        the screen's own copy when it has no window."""
        window = self._window
        edit = getattr(window, "edit_template", None)
        try:
            if callable(edit):
                return bool(edit(template_id, text, change))
            return self._edit_in_memory(template_id, text, change)
        except TemplateError as error:
            self.controller.status.emit(str(error))
            return False

    def _edit_in_memory(self, template_id: str, text: str, change) -> bool:
        from evrakci.pipeline.templates.model import template_from_dict
        from evrakci.ui.kontrol_chips import TemplateStep

        template = self.templates().get(template_id)
        if template is None:
            return False
        before = template_to_dict(template)
        change(template)
        after = template_to_dict(template)

        def apply(data: dict) -> None:
            restored = template_from_dict(data)
            target = self.templates().get(template_id)
            if target is not None:
                target.saved_filters[:] = restored.saved_filters

        self.template_undo.push(TemplateStep(text, before, after, apply))
        return True

    def _toast_template(self, text: str) -> None:
        toaster = getattr(self._window, "toaster", None)
        stack = getattr(self._window, "template_undo_stack", lambda: self.template_undo)()
        if toaster is not None:
            callback, available = undo_last(stack)
            toaster.show(text, "Geri al", callback, available=available)
        else:
            self.controller.status.emit(text)


__all__ = ["ADD_STEP", "DELETED", "RENAME_STEP", "SavedFiltersMixin"]
