"""UI-only preferences in an INI file (QSettings).

Window, view and look state only. Retention and other pipeline settings stay
in ``evrakci.pipeline.settings`` (JSON); nothing here duplicates them.
Every value is validated on read and write: bad stored values fall back to the default.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QByteArray, QObject, QSettings, Qt, Signal
from PySide6.QtWidgets import QMainWindow

ORG = "Evrakçı"
APP = "Evrakçı"

DENSITIES = {"Sıkı": "compact", "Normal": "normal", "Geniş": "comfortable"}
TEXT_SIZES = (100, 115, 130, 150)
THEMES = ("system", "light", "dark", "hc")
MRU_MAX = 10
ZOOM_RANGE = (10, 800)  # percent
THUMB_RANGE = (64, 512)  # px
VIEW_STATE_MAX = 200  # characters
NATIVE_TITLE_BAR = "native_title_bar"


def default_settings_file() -> Path:
    """INI path in the user config folder (EVRAKCI_UI_AYARLAR overrides)."""
    configured = os.environ.get("EVRAKCI_UI_AYARLAR")
    if configured:
        return Path(configured)
    base = os.environ.get("APPDATA") or os.environ.get("XDG_CONFIG_HOME")
    root = Path(base) if base else Path.home() / ".config"
    return root / ORG / f"{APP}.ini"


def _to_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _to_bool(value: object) -> bool | None:
    text = str(value).lower()
    if text in ("true", "1"):
        return True
    if text in ("false", "0"):
        return False
    return None


class Prefs(QObject):
    """Typed accessors over QSettings; emits ``changed(key)`` on every write."""

    changed = Signal(str)

    def __init__(self, path: str | Path | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        target = Path(path) if path else default_settings_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        self._s = QSettings(str(target), QSettings.Format.IniFormat)

    # -- plumbing ---------------------------------------------------------
    def _set(self, key: str, value: object) -> None:
        self._s.setValue(key, value)
        self._s.sync()
        self.changed.emit(key)

    def _int(self, key: str, default: int, lo: int, hi: int) -> int:
        value = _to_int(self._s.value(key))
        return default if value is None or not lo <= value <= hi else value

    def _list(self, key: str) -> list[str]:
        value = self._s.value(key)
        if value is None or value == "":
            return []
        items = [value] if isinstance(value, str) else list(value)
        return [str(v) for v in items if str(v)]

    def _push(self, key: str, item: str) -> None:
        item = str(item)
        if not item:
            return
        items = [item] + [v for v in self._list(key) if v != item]
        self._set(key, items[:MRU_MAX])

    # -- window -----------------------------------------------------------
    def save_window(self, window: QMainWindow) -> None:
        """Remember geometry, state and maximised."""
        self._s.setValue("window/geometry", window.saveGeometry())
        self._s.setValue("window/state", window.saveState())
        self._s.setValue("window/maximized", window.isMaximized())
        self._s.sync()
        self.changed.emit("window")

    def restore_window(self, window: QMainWindow) -> bool:
        """Apply saved geometry; False if nothing usable was stored."""
        geometry = self._s.value("window/geometry")
        if not isinstance(geometry, QByteArray) or geometry.isEmpty():
            return False
        ok = window.restoreGeometry(geometry)
        state = self._s.value("window/state")
        if isinstance(state, QByteArray) and not state.isEmpty():
            window.restoreState(state)
        if _to_bool(self._s.value("window/maximized")):
            window.setWindowState(window.windowState() | Qt.WindowState.WindowMaximized)
        return ok

    def window_maximized(self) -> bool:
        return bool(_to_bool(self._s.value("window/maximized")))

    # -- tab, splitters, headers, zoom -----------------------------------
    def last_tab(self) -> int:
        return self._int("ui/last_tab", 0, 0, 99)

    def set_last_tab(self, index: int) -> None:
        if not isinstance(index, int) or not 0 <= index <= 99:
            raise ValueError(f"Geçersiz sekme: {index!r}")
        self._set("ui/last_tab", index)

    def splitter_sizes(self, key: str) -> list[int]:
        sizes = [_to_int(v) for v in self._list(f"splitters/{key}")]
        return [] if None in sizes or any(v < 0 for v in sizes) else sizes  # type: ignore[operator]

    def set_splitter_sizes(self, key: str, sizes: list[int]) -> None:
        if not sizes or any(not isinstance(v, int) or v < 0 for v in sizes):
            raise ValueError(f"Geçersiz bölme boyutları: {sizes!r}")
        self._set(f"splitters/{key}", [str(v) for v in sizes])

    def header_state(self, key: str) -> QByteArray:
        value = self._s.value(f"headers/{key}")
        return value if isinstance(value, QByteArray) else QByteArray()

    def set_header_state(self, key: str, state: QByteArray) -> None:
        """``QHeaderView.saveState()`` holds column widths and sort."""
        self._set(f"headers/{key}", QByteArray(state))

    def zoom(self, key: str, default: int = 100) -> int:
        return self._int(f"zoom/{key}", default, *ZOOM_RANGE)

    def set_zoom(self, key: str, percent: int) -> None:
        if not isinstance(percent, int) or not ZOOM_RANGE[0] <= percent <= ZOOM_RANGE[1]:
            raise ValueError(f"Geçersiz yakınlaştırma: {percent!r}")
        self._set(f"zoom/{key}", percent)

    # -- small named view flags and choices -----------------------------------
    @staticmethod
    def _key_name(key: str) -> str:
        if not isinstance(key, str) or not key or any(c in key for c in "/\\ ="):
            raise ValueError(f"Geçersiz ayar adı: {key!r}")
        return key

    def flag(self, key: str, default: bool = False) -> bool:
        """A remembered yes/no, e.g. "Bir daha gösterme" on a tip."""
        value = _to_bool(self._s.value(f"flags/{self._key_name(key)}"))
        return default if value is None else value

    def set_flag(self, key: str, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Geçersiz değer: {value!r}")
        self._set(f"flags/{self._key_name(key)}", value)

    def view_state(self, key: str, default: str = "") -> str:
        """A remembered short choice of a view (a filter, a mode, a template id)."""
        value = self._s.value(f"views/{self._key_name(key)}")
        text = "" if value is None else str(value)
        return text if text and len(text) <= VIEW_STATE_MAX else default

    def set_view_state(self, key: str, value: str) -> None:
        if not isinstance(value, str) or len(value) > VIEW_STATE_MAX or "\n" in value:
            raise ValueError(f"Geçersiz görünüm durumu: {value!r}")
        self._set(f"views/{self._key_name(key)}", value)

    def thumbnail_size(self) -> int:
        return self._int("view/thumbnail_size", 160, *THUMB_RANGE)

    def set_thumbnail_size(self, size: int) -> None:
        if not isinstance(size, int) or not THUMB_RANGE[0] <= size <= THUMB_RANGE[1]:
            raise ValueError(f"Geçersiz küçük resim boyutu: {size!r}")
        self._set("view/thumbnail_size", size)

    # -- look ---------------------------------------------------------------
    def density(self) -> str:
        value = str(self._s.value("look/density", "normal"))
        return value if value in DENSITIES.values() else "normal"

    def set_density(self, value: str) -> None:
        """Accepts "compact"/"normal"/"comfortable" or the Turkish label."""
        value = DENSITIES.get(value, value)
        if value not in DENSITIES.values():
            raise ValueError(f"Geçersiz yoğunluk: {value!r}")
        self._set("look/density", value)

    def text_size(self) -> int:
        value = _to_int(self._s.value("look/text_size"))
        return value if value in TEXT_SIZES else 100

    def set_text_size(self, percent: int) -> None:
        if percent not in TEXT_SIZES:
            raise ValueError(f"Geçersiz yazı boyutu: {percent!r}")
        self._set("look/text_size", percent)

    def theme(self) -> str:
        value = str(self._s.value("look/theme", "system"))
        return value if value in THEMES else "system"

    def set_theme(self, value: str) -> None:
        if value not in THEMES:
            raise ValueError(f"Geçersiz tema: {value!r}")
        self._set("look/theme", value)

    def reduced_motion(self) -> bool | None:
        """None follows the system."""
        value = self._s.value("look/reduced_motion")
        return None if value in (None, "", "system") else _to_bool(value)

    def set_reduced_motion(self, value: bool | None) -> None:
        if value is not None and not isinstance(value, bool):
            raise ValueError(f"Geçersiz hareket ayarı: {value!r}")
        self._set("look/reduced_motion", "system" if value is None else value)

    def native_title_bar(self) -> bool:
        """Keep the system title bar instead of A's title band (Windows; on restart)."""
        return bool(_to_bool(self._s.value(NATIVE_TITLE_BAR)))

    def set_native_title_bar(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError(f"Geçersiz başlık çubuğu ayarı: {value!r}")
        self._set(NATIVE_TITLE_BAR, value)

    # -- recents and folders -------------------------------------------------
    def recent_jobs(self) -> list[str]:
        return self._list("recent/jobs")[:MRU_MAX]

    def add_recent_job(self, job: str) -> None:
        self._push("recent/jobs", job)

    def recent_folders(self) -> list[str]:
        return self._list("recent/folders")[:MRU_MAX]

    def add_recent_folder(self, folder: str | Path) -> None:
        self._push("recent/folders", str(folder))

    def clear_recent(self) -> None:
        self._s.remove("recent")
        self._s.sync()
        self.changed.emit("recent")

    def export_folder(self) -> str:
        return str(self._s.value("paths/export_folder", ""))

    def set_export_folder(self, folder: str | Path) -> None:
        self._set("paths/export_folder", str(folder))

    def last_export_folder(self) -> str:
        """The folder the last export went to (Ayarlar' default stays `export_folder`)."""
        return str(self._s.value("paths/last_export_folder", ""))

    def set_last_export_folder(self, folder: str | Path) -> None:
        self._set("paths/last_export_folder", str(folder))
