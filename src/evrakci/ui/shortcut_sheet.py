"""The shortcut sheet (Shift+F1, Ctrl+/, ?): every key that works on the current tab, grouped."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from evrakci.ui import actions, theme


class ShortcutSheet(QDialog):
    """A searchable list of the shortcuts of "app" and one tab. Esc or Kapat closes it."""

    def __init__(self, registry: actions.Registry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._registry = registry
        self._tab = registry.context
        self.setObjectName("shortcutSheet")
        self.setWindowTitle("Klavye kısayolları")
        self.setAccessibleName("Klavye kısayolları")
        self.setMinimumSize(520, 460)
        m = theme.manager()

        root = QVBoxLayout(self)
        root.setContentsMargins(*(m.size("s6"),) * 4)
        root.setSpacing(m.size("s3"))

        self.title = QLabel()
        self.title.setProperty("textRole", "panel")
        root.addWidget(self.title)

        label = QLabel("Kısayol ara")
        label.setProperty("textRole", "caption")
        root.addWidget(label)
        self.search = QLineEdit()
        self.search.setProperty("kind", "search")
        self.search.setPlaceholderText("Komut veya tuş yazın")
        self.search.setAccessibleName("Kısayol ara")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._fill)
        label.setBuddy(self.search)
        root.addWidget(self.search)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tree.setAccessibleName("Kısayol listesi")
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, self.tree.header().ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, self.tree.header().ResizeMode.ResizeToContents)
        root.addWidget(self.tree, 1)

        self.empty = QLabel("Eşleşen kısayol yok")
        self.empty.setProperty("textRole", "secondary")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.hide()
        root.addWidget(self.empty)

        bottom = QHBoxLayout()
        hint = QLabel("Bu pencereyi Shift+F1 ile açabilirsiniz")
        hint.setProperty("textRole", "caption")
        bottom.addWidget(hint, 1)
        close = QPushButton("Kapat")
        close.setObjectName("primary")
        close.setDefault(True)
        close.clicked.connect(self.close)
        bottom.addWidget(close)
        root.addLayout(bottom)

    # Public
    def show_for(self, tab: str) -> None:
        """Fill the sheet for `tab` and show it."""
        self._tab = tab
        self.title.setText(f"Klavye kısayolları · {actions.TABS.get(tab, 'Genel')}")
        self.search.clear()
        self._fill()
        self.show()
        self.raise_()
        self.activateWindow()
        self.search.setFocus()

    def visible_rows(self) -> list[tuple[str, str, str]]:
        """(group, command, keys) of every row now listed, for tests."""
        rows = []
        for i in range(self.tree.topLevelItemCount()):
            group = self.tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                rows.append((group.text(0), child.text(0), child.text(1)))
        return rows

    # Content
    def _fill(self) -> None:
        words = actions.fold(self.search.text()).split()
        groups: dict[str, list[actions.SheetRow]] = {}
        for row in actions.shortcut_sheet(self._tab):
            haystack = actions.fold(f"{row.group} {row.text} {' '.join(row.keys)}")
            if all(w in haystack for w in words):
                groups.setdefault(row.group, []).append(row)
        self.tree.clear()
        bold = QFont(theme.manager().font("caption-strong"))
        for name, rows in groups.items():
            head = QTreeWidgetItem([name])
            head.setFlags(Qt.ItemFlag.ItemIsEnabled)
            head.setFont(0, bold)
            self.tree.addTopLevelItem(head)
            for row in rows:
                keys = "   ·   ".join(row.keys)
                item = QTreeWidgetItem([row.text, keys])
                item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                item.setData(0, Qt.ItemDataRole.AccessibleTextRole, f"{row.text}: {keys}")
                head.addChild(item)
            head.setExpanded(True)
        self.empty.setVisible(not groups)
        self.tree.setVisible(bool(groups))
