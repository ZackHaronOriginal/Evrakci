"""Live reading in Şablonlar: the example on the canvas is read with the template as it is, a
moment after each change, and "Bütün örneklerde dene" reads every example (Esc stops it).

A mixin of `SablonScreen` (it uses the screen's template, controller and widgets). The work is
`sablon_read.read_examples` in a worker; everything the worker needs is copied on the window
thread first.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer

from evrakci.pipeline.templates.model import template_from_dict, template_to_dict
from evrakci.ui import sablon_read as reading
from evrakci.ui.workers import Task, start


class LiveReads:
    def _engine(self):
        if self.engine is not None:
            return self.engine()
        from evrakci.pipeline.ocr.tesseract import default_engine

        return default_engine()

    def _read_input(self, numbers: list[int] | None = None) -> reading.ReadInput:
        """Everything a worker needs, copied here on the window thread."""
        controller = self.controller()
        documents = self._docs
        wanted = numbers or [self.example]
        return reading.ReadInput(
            template_from_dict(template_to_dict(self.template)),
            {n: tuple(documents[n - 1].page_ids) for n in wanted},
            dict(controller.store.batch_files(controller.job)),
            dict(controller.job.rotations), self._engine())

    def read_example(self) -> None:
        """Read the example on the canvas with the template as it is; when one read is already
        running the next starts after it."""
        self._read_timer.stop()
        if self.template is None or not self.example or self.controller() is None:
            return
        if self._read_task is not None or self._all_task is not None:
            self._reread = True
            return
        job = self._read_input()
        number = self._read_number = self.example
        self._read_template = job.template
        self._read_task = Task(lambda _progress: reading.read_examples(job, [number])[number])
        self._read_task.signals.done.connect(self._show_reads)
        self._read_task.signals.failed.connect(self._read_failed)
        self._busy_timer.start()
        start(self._read_task)

    def _show_busy(self) -> None:
        if self._read_task is not None:
            self._busy = True
            self._sync_inspector()

    def _read_finished(self) -> None:
        self._read_task = None
        self._busy_timer.stop()
        self._busy = False
        if self._reread:
            self._reread = False
            self.read_example()

    def _read_failed(self, message: str) -> None:
        self.values = {}
        self.read_lines = [f"Okunamadı: {message}"]
        self._push_readings()
        self._read_finished()
        self.message.setText(f"Okuma yapılamadı: {message}")
        self._sync_all()

    def _show_reads(self, values) -> None:
        template = self._read_template
        if (self.template is None or template is None or template.id != self.template.id
                or self._read_number != self.example):
            self._reread = True  # it was another template or example: read what is shown now
            self._read_finished()
            return
        self.values = values
        self.example_values[self.example] = values
        self.read_lines = reading.lines(self._read_template, values)
        if self.message.text().startswith("Okuma yapılamadı"):
            self.message.setText("")
        self._read_finished()
        self._push_readings()
        self._sync_all()

    def reads_text(self) -> str:
        return "\n".join(self.read_lines)

    def _minimum(self) -> float:
        template = self._read_template or self.template
        return template.min_confidence if template is not None else 0.7

    def _push_readings(self) -> None:
        """The reads under their boxes ("Okumaları sayfada göster")."""
        template = self._read_template or self.template
        found: dict[tuple[str, int], tuple[str, str]] = {}
        if template is not None:
            for variable in template.variables:
                value = self.values.get(variable.key)
                for index in range(len(variable.sections)):
                    shown = reading.shown_for(value, index, template.min_confidence)
                    if value is not None:
                        found[(variable.name, index)] = (shown.text, shown.level)
        self.canvas.set_readings(found)

    def read_all_examples(self) -> None:
        """Ctrl+T: read every example with the template; Esc stops. The results mark the
        examples that need a check and are summed in the status bar and a toast."""
        if self.template is None or self.controller() is None:
            self.message.setText("Denemek için bir şablon ve açık bir iş gerekir.")
            return
        if self._all_task is not None:
            return
        numbers = list(range(1, len(self._documents()) + 1))
        if not numbers:
            return
        if self._read_task is not None:
            self._reread = False  # the live read finishes first, then this starts
            QTimer.singleShot(100, self.read_all_examples)
            return
        job = self._read_input(numbers)
        self._read_template = job.template
        task = Task(lambda progress: reading.read_examples(job, numbers, progress))
        task.signals.progress.connect(self._all_progress)
        task.signals.done.connect(self._all_done)
        task.signals.failed.connect(self._all_failed)
        task.signals.cancelled.connect(self._all_cancelled)
        self._all_task = task
        self._all_progress(0, len(numbers))
        self._sync_actions()
        start(task)

    def cancel_read(self) -> None:
        if self._all_task is not None:
            self._all_task.cancel()

    def _all_progress(self, done: int, total: int) -> None:
        part = self._status.get("check")
        if part is not None:
            part.set_icon("refresh-cw", "icon")
            part.set("Örnekler okunuyor ", str(done), f" / {total}, Esc durdurur")
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.set(done, total)

    def _all_stopped(self) -> None:
        self._all_task = None
        taskbar = getattr(self.window_, "taskbar", None)
        if taskbar is not None:
            taskbar.clear()
        self._sync_all()
        if self._reread:
            self._reread = False
            self.read_example()

    def _all_done(self, results: dict) -> None:
        self.example_values = results
        self.values = results.get(self.example, self.values)
        self.read_lines = reading.lines(self._read_template, self.values)
        self._all_stopped()
        self._mark_example_checks()
        self._push_readings()
        flagged = sum(reading.flagged_count(v) for v in results.values())
        total = len(results)
        self._toast(f"{total} örnekte denendi. " + (
            f"{flagged} okuma kontrol bekliyor." if flagged else "Kontrol gerektiren okuma yok."),
            kind="kontrol" if flagged else "success")

    def _all_failed(self, message: str) -> None:
        self._all_stopped()
        self.message.setText(f"Örnekler okunamadı: {message}")

    def _all_cancelled(self) -> None:
        self._all_stopped()
        self._toast("Deneme durduruldu.")

    def _escape(self) -> bool:
        """Esc stops "Bütün örneklerde dene" before it does anything else."""
        if self._all_task is None:
            return False
        self.cancel_read()
        return True
