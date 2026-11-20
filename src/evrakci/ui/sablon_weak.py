"""Şablonlar: the weakest examples first (I-28), after "Bütün örneklerde dene".

N / Shift+N walk the examples that have reads needing a check, worst first; Ctrl+L (or a click on
the status item "N okuma kontrol bekliyor") lists them in a popup under the example picker. The
order comes from the core (`weakest_examples`); nothing here is saved (the results stay in
memory and are dropped with the template or the job).

A mixin of `SablonScreen`.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtWidgets import QMenu

from evrakci.pipeline.templates.read import ExampleWeakness, weakest_examples
from evrakci.ui import actions, theme
from evrakci.ui.chrome import make_icon

POPUP_ROWS = 8  # more rows than this scroll
NEEDS_TRY = "Önce Ctrl+T ile örnekleri deneyin."
NONE_WEAK = "Zayıf örnek yok: hiçbir okuma kontrol gerektirmiyor."
ONLY_ONE = "Kontrol gereken tek belge bu."  # the wording Kontrol uses when N lands on itself


def row_text(weak: ExampleWeakness) -> str:
    return (f"Belge {weak.number}  {weak.flagged} kontrol  "
            f"en düşük %{round(weak.lowest_confidence * 100)}")


class _Click(QObject):
    """A press on the status item opens the list."""

    def __init__(self, target, slot) -> None:
        super().__init__(target)
        self._slot = slot
        for widget in (target, target.label, target.icon):
            widget.installEventFilter(self)
            widget.setCursor(Qt.CursorShape.PointingHandCursor)
        target.setToolTip("Zayıf örnekler (Ctrl+L)")

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if (event.type() == QEvent.Type.MouseButtonRelease
                and event.button() == Qt.MouseButton.LeftButton):
            self._slot()
            return True
        return False


class WeakExamples:
    def weak_examples(self) -> list[ExampleWeakness]:
        return weakest_examples(self.example_values) if self.tried_all else []

    def _connect_weak(self, registry) -> None:
        registry.connect("sablonlar.sonraki_zayif", lambda: self.jump_weak(1))
        registry.connect("sablonlar.onceki_zayif", lambda: self.jump_weak(-1))
        registry.connect("sablonlar.zayif_ornekler", self.show_weak_list)
        self._weak_click = _Click(self._status["check"], self.show_weak_list)

    def _sync_weak_actions(self, registry, usable: bool) -> None:
        """Off (with the reason as the tip) until "Bütün örneklerde dene" has run."""
        for action_id in ("sablonlar.sonraki_zayif", "sablonlar.onceki_zayif",
                          "sablonlar.zayif_ornekler"):
            ready = usable and self.tried_all
            registry.set_enabled(action_id, ready)
            tip = actions.tooltip_for(registry.spec(action_id))  # "Sonraki zayıf örnek (N)"
            registry.action(action_id).setToolTip(tip if ready else f"{NEEDS_TRY} ({tip})")

    def jump_weak(self, step: int) -> None:
        """N / Shift+N: the next / previous example in weakest-first order (wraps round)."""
        weak = self.weak_examples()
        if not weak:
            self.message.setText(NONE_WEAK if self.tried_all else NEEDS_TRY)
            return
        numbers = [w.number for w in weak]
        if self.example in numbers:
            target = numbers[(numbers.index(self.example) + step) % len(numbers)]
        else:
            target = numbers[0] if step > 0 else numbers[-1]
        if target == self.example:
            self.message.setText(ONLY_ONE)
            return
        self.message.setText("")
        self.set_example(target)

    def show_weak_list(self) -> None:
        """Ctrl+L: "Zayıf örnekler", under the example picker; Enter opens, Esc closes."""
        if not self.tried_all:
            self.message.setText(NEEDS_TRY)
            return
        weak = self.weak_examples()
        menu = QMenu(self)
        menu.setAccessibleName("Zayıf örnekler")
        menu.addSection("Zayıf örnekler")
        if not weak:
            menu.addAction(NONE_WEAK).setEnabled(False)
        icon = make_icon("triangle-alert", "check-text", theme.manager().size("icon-sm"))
        for item in weak:
            action = menu.addAction(icon, row_text(item))
            action.setData(item.number)
            action.triggered.connect(lambda _=False, n=item.number: self.set_example(n))
        height = theme.manager().menu_item_height()
        menu.setMaximumHeight(height * (POPUP_ROWS + 1) + theme.manager().size("s2"))
        self._weak_menu = menu
        menu.popup(self.examples.mapToGlobal(QPoint(0, self.examples.height())))
