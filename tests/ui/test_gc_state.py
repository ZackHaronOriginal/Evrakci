"""R-B-6: a module that started the window-thread collector leaves no trace for the next one
(run it after tests/ui/test_workers.py in one pytest call to see the order that broke)."""

import gc

from evrakci.ui import gc_guard


def test_the_module_starts_with_the_collector_as_a_fresh_run_has_it():
    assert gc.isenabled()
    assert not gc_guard.installed()
