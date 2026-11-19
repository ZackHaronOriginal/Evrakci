"""What Şablonlar shows and enables, kept in step with its state: the canvas or an empty state,
the inspector, the registry actions (so none stays disabled when usable) and the status bar line
(example, cursor or box position, save state, reads that need a check).

A mixin of `SablonScreen`; every `_sync_*` reads the screen's state and changes only widgets.
"""

from __future__ import annotations

from evrakci.ui import sablon_read as reading
from evrakci.ui.sablon_canvas import fmt_mm
from evrakci.ui.sablon_inspector import InspectorState


class Syncing:
    def _sync_all(self) -> None:
        self._sync_state()
        self._sync_inspector()
        self._sync_actions()
        self._sync_status()

    def _sync_state(self) -> None:
        """Canvas, or an empty state (A `empty`; no example page is a state A does not draw)."""
        has_template = self.template is not None
        has_page = self.canvas.has_page()
        if has_page and has_template:
            self.stack.setCurrentWidget(self.well)
        else:
            self.stack.setCurrentWidget(self.empty_frame)
            controller = self.controller()
            if not has_template:
                note = (f"Örnek sayfalar açık işten gelir: {controller.job.name}."
                        if controller is not None else
                        "Örnek sayfalar için önce Yükle sekmesinden bir iş açın.")
                self.empty.show_state(
                    "layout-template", "Henüz şablon yok",
                    "Örnek bir sayfada her bilginin çevresine kutu çizin.",
                    ("Yeni şablon oluştur", "plus", self.new_template),
                    ("Rehber'i aç", "book-open", self._open_guide), note)
            else:
                self.empty.show_state(
                    "layout-template", "Örnek sayfa yok",
                    "Kutuları çizmek için bir iş açın; örnek sayfalar o işten gelir.",
                    ("Yükle'ye git", "upload", self._open_upload), None, "")
        self.bar.setVisible(has_template and has_page)
        self.side.allow(has_template)
        if hasattr(self.window_, "set_zoom_visible"):  # nothing to zoom in the empty states
            self.window_.set_zoom_visible("sablonlar", has_template and has_page)

    def _open_guide(self) -> None:
        if self.window_ is not None:
            self.window_.show_tab("rehber")

    def _open_upload(self) -> None:
        if self.window_ is not None:
            self.window_.show_tab("yukle")

    def _sync_inspector(self) -> None:
        template = self.template
        if template is None:
            return
        variable = self.current_variable()
        total = len(template.variables)
        sheet = self.canvas.page_mm() if self.canvas.has_page() else (210.0, 297.0)
        read_title = f"Okunan, örnek {self.example}" if self.example else "Okunan"
        if variable is None:
            state = InspectorState(
                "none", "", "Değişken yok" if not total else "Değişken seçilmedi",
                "Eklemek için Ctrl+Shift+N tuşlarına basın." if not total
                else "Soldaki listeden bir değişken seçin.")
        elif self.section_index is None or self.section_index >= len(variable.sections):
            count = len(variable.sections)
            shown = reading.shown_for(self.values.get(variable.key), None, self._minimum())
            state = InspectorState(
                "variable", f"Değişken {self._number_of(variable.name)} / {total}",
                variable.name, f"{count} bölüm" if count else "Henüz kutu yok",
                variable.name, variable.required, read_title=read_title,
                shown=shown if self.values else None, busy=self._busy,
                hint=("Sayfada Kutu çiz (B) ile bu değişkenin kutusunu çizin." if not count
                      else "Bir bölüm seçin ya da sayfada bir kutuya tıklayın."))
        else:
            index = self.section_index
            section = variable.sections[index]
            page = "son sayfa" if section.page == -1 else f"sayfa {section.page}"
            shown = reading.shown_for(self.values.get(variable.key), index, self._minimum())
            state = InspectorState(
                "box", f"Kutu {index + 1} / {len(variable.sections)}", variable.name,
                f"Bölüm {index + 1}, {page}", variable.name, variable.required, section.page,
                section.box_mm, sheet, read_title, shown if self.values else None, self._busy)
        self.side.show_state(state)
        extent = state.box if state.mode == "box" else None
        self.well.set_extent(extent)

    def _sync_actions(self) -> None:
        registry = self._registry()
        if registry is None:
            return
        has = self.template is not None
        page = has and self.canvas.has_page()
        has_variable = self.current_variable() is not None
        has_box = has_variable and self.section_index is not None
        busy = self._all_task is not None
        variable_count = len(self.template.variables) if has else 0
        up = down = False
        variable = self.current_variable()
        if variable is not None:  # a section moves in the try order, else the variable does
            if has_box and len(variable.sections) > 1:
                up, down = self.section_index > 0, self.section_index < len(variable.sections) - 1
            else:
                place = [v.name for v in self.template.variables].index(variable.name)
                up, down = place > 0, place < variable_count - 1
        states = {
            "sablonlar.kutu_ciz": page, "sablonlar.izgara": page,
            "sablonlar.dene": page and not busy,
            "sablonlar.kutu_sil": has_variable, "sablonlar.kutu_cogalt": has_box and page,
            "sablonlar.degisken_ekle": has, "sablonlar.yukari": up, "sablonlar.asagi": down,
            "sablonlar.okumalari_goster": page,
        }
        for action_id, enabled in states.items():
            registry.set_enabled(action_id, enabled)
        # Only this tab's route: MainWindow and the other tabs own Ctrl+S elsewhere.
        registry.set_enabled_for("app.kaydet", "sablonlar", has)
        self.side.save.setEnabled(has)

    def _sync_status(self) -> None:
        if not self._status:
            return
        s = self._status
        total = len(self._documents())
        has = self.template is not None
        page = has and self.canvas.has_page()
        s["example"].setVisible(page)
        s["example"].set("Örnek ", str(self.example), f" / {total}")
        focused = self.canvas.hasFocus() and self.canvas.selected_item() is not None
        item = self.canvas.selected_item()
        s["box"].setVisible(page and focused)
        s["hint"].setVisible(page and focused)
        s["cursor"].setVisible(page and not focused)
        if item is not None:
            x0, y0, _x1, _y1 = item.spec.box
            s["box"].set("Kutu ", f"x {fmt_mm(x0)}  y {fmt_mm(y0)}", " mm")
        s["hint"].set("Kaydır: ok tuşları ", "0,25 mm", ", Shift ", "1 mm")
        if not s["cursor"].parts:
            s["cursor"].set("İmleç ", "x —  y —", " mm")
        saved = s["saved"]
        saved.setVisible(True)
        if not has:
            saved.set_icon(None, "icon")
            saved.set("Şablon seçilmedi")
        elif self._save_error:
            saved.set_icon("circle-x", "danger")
            saved.set("Şablon kaydedilemedi")
        elif self._dirty:
            saved.set_icon("circle-dashed", "icon")
            saved.set("Şablon kaydedilmedi")
        else:
            saved.set_icon("circle-check", "ok")
            stamp = f" {self._saved_at:%H:%M}" if self._saved_at else ""
            saved.set(f"Şablon kaydedildi{stamp}")
        check = s["check"]
        if self._all_task is not None:
            return
        flagged = sum(reading.flagged_count(v) for v in self.example_values.values()) \
            if len(self.example_values) > 1 else reading.flagged_count(self.values)
        check.set_icon("triangle-alert", "rider-edge")
        check.setVisible(bool(flagged) and page)
        check.set(str(flagged), " okuma kontrol bekliyor")

    def _cursor_moved(self, point) -> None:
        if not self._status:
            return
        part = self._status["cursor"]
        if point is None:
            part.set("İmleç ", "x —  y —", " mm")
        else:
            part.set("İmleç ", f"x {fmt_mm(point[0])}  y {fmt_mm(point[1])}", " mm")
