"""Taskbar progress (Windows ITaskbarList3) with a window-title fallback.

Raw COM vtable calls through ctypes, only on Windows; everywhere else (and on any
failure) it is a silent no-op, so callers never need a platform check.
The state machine (none / normal / indeterminate / error) is plain Python and testable.
"""

from __future__ import annotations

import os
from typing import Protocol

from PySide6.QtWidgets import QWidget

NOPROGRESS, INDETERMINATE, NORMAL, ERROR = 0x0, 0x1, 0x2, 0x4
_SET_VALUE, _SET_STATE = 9, 10  # ITaskbarList3 vtable slots (IUnknown 0-2, ITaskbarList 3-7)


class Backend(Protocol):
    """What the state machine drives; the real one is ``_Windows``."""

    def set_state(self, flag: int) -> None: ...
    def set_value(self, value: int, maximum: int) -> None: ...


class _Windows:
    """ITaskbarList3 via ctypes; every call is guarded and never raises."""

    def __init__(self, window: QWidget) -> None:
        self._window = window
        self._ptr: object | None = None
        self._failed = False

    def _method(self, slot: int, *argtypes: object):
        import ctypes

        vtbl = ctypes.cast(ctypes.cast(self._ptr, ctypes.POINTER(ctypes.c_void_p))[0],
                           ctypes.POINTER(ctypes.c_void_p))
        proto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)
        return lambda *args: proto(vtbl[slot])(self._ptr, *args)

    def _init(self) -> bool:
        if self._failed:
            return False
        if self._ptr is not None:
            return True
        try:
            import ctypes
            import uuid
            from ctypes import wintypes

            class GUID(ctypes.Structure):
                _fields_ = [("a", wintypes.DWORD), ("b", wintypes.WORD), ("c", wintypes.WORD),
                            ("d", ctypes.c_ubyte * 8)]

            def guid(text: str) -> GUID:
                u = uuid.UUID(text)
                return GUID(u.time_low, u.time_mid, u.time_hi_version,
                            (ctypes.c_ubyte * 8)(*u.bytes[8:]))

            ole32 = ctypes.windll.ole32
            ole32.CoInitialize(None)
            ptr = ctypes.c_void_p()
            hr = ole32.CoCreateInstance(
                ctypes.byref(guid("56FDF344-FD6D-11D0-958A-006097C9A090")), None, 1,
                ctypes.byref(guid("EA1AFB91-9E28-4B86-90E9-9E9F8A5EEFAF")), ctypes.byref(ptr))
            if hr != 0 or not ptr.value:
                raise OSError(hr)
            self._ptr = ptr
            self._method(3)()  # HrInit
        except Exception:  # noqa: BLE001 - taskbar progress is decoration
            self._failed = True
            return False
        return True

    def set_state(self, flag: int) -> None:
        try:
            if self._init():
                import ctypes

                self._method(_SET_STATE, ctypes.c_void_p, ctypes.c_int)(
                    int(self._window.winId()), flag)
        except Exception:  # noqa: BLE001
            self._failed = True

    def set_value(self, value: int, maximum: int) -> None:
        try:
            if self._init():
                import ctypes

                self._method(_SET_VALUE, ctypes.c_void_p, ctypes.c_ulonglong,
                             ctypes.c_ulonglong)(int(self._window.winId()), value, maximum)
        except Exception:  # noqa: BLE001
            self._failed = True


class TaskbarProgress:
    """Progress on the window's taskbar button; optional "%62 – " title prefix."""

    def __init__(self, window: QWidget, backend: Backend | None = None,
                 title_prefix: bool = False) -> None:
        self._window = window
        self._backend: Backend | None = backend
        if backend is None and os.name == "nt":
            self._backend = _Windows(window)
        self._title_prefix = title_prefix
        self._base_title: str | None = None
        self._applied = ""
        self.state = "none"
        self.value = 0
        self.maximum = 0

    def set(self, value: int, maximum: int) -> None:
        """Determinate progress; ``maximum`` <= 0 means unknown (indeterminate)."""
        if maximum <= 0:
            self.indeterminate()
            return
        value = max(0, min(int(value), int(maximum)))
        self.state, self.value, self.maximum = "normal", value, int(maximum)
        self._send(NORMAL)
        if self._backend is not None:
            self._safe(lambda: self._backend.set_value(value, int(maximum)))
        self._title(f"%{round(100 * value / maximum)} – ")

    def indeterminate(self) -> None:
        self.state, self.value, self.maximum = "indeterminate", 0, 0
        self._send(INDETERMINATE)
        self._title("")

    def error(self) -> None:
        """Red bar at the current value (a failed or stopped task)."""
        self.state = "error"
        self._send(ERROR)
        self._title("")

    def clear(self) -> None:
        self.state, self.value, self.maximum = "none", 0, 0
        self._send(NOPROGRESS)
        self._title("")

    def _send(self, flag: int) -> None:
        if self._backend is not None:
            self._safe(lambda: self._backend.set_state(flag))

    @staticmethod
    def _safe(call) -> None:
        try:
            call()
        except Exception:  # noqa: BLE001 - never raise from decoration
            pass

    def _title(self, prefix: str) -> None:
        if not self._title_prefix:
            return
        current = self._window.windowTitle()
        if self._base_title is None or current != self._applied:
            self._base_title = current  # the app changed the title meanwhile
        self._applied = prefix + self._base_title
        self._window.setWindowTitle(self._applied)
