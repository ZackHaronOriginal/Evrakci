"""Helpers for tests of write-behind saving: the file is written after the edit, on another
thread, so a test lets the event loop run until the saver has written what it was given."""

from __future__ import annotations

import time

from PySide6.QtCore import QCoreApplication


def wait_saved(controller, timeout: float = 3.0):
    """Run the event loop until the controller's saver is idle; returns the controller."""
    deadline = time.monotonic() + timeout
    app = QCoreApplication.instance()
    while not controller.saver.idle:
        assert time.monotonic() < deadline, "the saver did not finish writing"
        app.processEvents()
        time.sleep(0.001)
    return controller
