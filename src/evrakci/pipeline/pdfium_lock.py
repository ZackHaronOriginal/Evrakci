"""One process-wide lock for PDFium.

PDFium (and so pypdfium2) is not thread-safe: two threads opening, rendering or closing documents
at the same time can corrupt its state, after which every later open fails ("Data format
error"). The window renders thumbnails on worker threads while the main thread analyses PDFs,
so every PDFium call in Evrakçı runs under this lock. It is re-entrant, so a locked helper may
call another.
"""

from __future__ import annotations

import threading

PDFIUM_LOCK = threading.RLock()
