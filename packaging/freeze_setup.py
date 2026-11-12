"""cx_Freeze folder build: evrakci (console) and evrakci-arayuz (window).

Run through packaging/build.py, which stages licences and bundled tools first.
"""

import sys
from pathlib import Path

from cx_Freeze import Executable, setup
from cx_Freeze.hooks import unused_modules

# OCRmyPDF imports unittest.mock at run time, but cx_Freeze leaves unittest out by default.
unused_modules.DEFAULT_EXCLUDES.discard("unittest")

HERE = Path(__file__).resolve().parent
STAGE = HERE / "stage"
sys.path.insert(0, str(HERE.parent / "src"))

from evrakci import __version__  # noqa: E402

# Qt parts the app never uses; leaving them out keeps the install small.
UNUSED_QT = [
    f"PySide6.{name}"
    for name in (
        "Qt3DAnimation Qt3DCore Qt3DExtras Qt3DInput Qt3DLogic Qt3DRender QtBluetooth "
        "QtCanvasPainter QtCharts QtDataVisualization QtDesigner QtGraphs QtGraphsWidgets "
        "QtHelp QtHttpServer QtLabsStyleKit QtLocation QtMultimedia QtMultimediaWidgets "
        "QtNetworkAuth QtNfc QtPdf QtPdfWidgets QtPositioning QtQml QtQmlFeatures QtQuick "
        "QtQuick3D QtQuickControls2 QtQuickTest QtQuickWidgets QtRemoteObjects QtScxml "
        "QtSensors QtSerialBus QtSerialPort QtSpatialAudio QtSql QtStateMachine QtTest "
        "QtTextToSpeech QtUiTools QtWebChannel QtWebEngineCore QtWebEngineQuick "
        "QtWebEngineWidgets QtWebSockets QtWebView QtXml"
    ).split()
]

sys.path.insert(0, str(HERE))
from layout import freeze_include_files  # noqa: E402

# Tesseract is added after the freeze (layout.AFTER_FREEZE), never scanned by cx_Freeze.
include_files = freeze_include_files(STAGE)
# The Rehber tab shows the scanning guide.
include_files.append((str(HERE.parent / "docs" / "tarama-rehberi.md"), "docs/tarama-rehberi.md"))

setup(
    name="Evrakci",
    version=__version__.split("+")[0],
    description="Evrakçı",
    options={
        "build_exe": {
            "packages": [
                "evrakci",
                "ocrmypdf",
                "pikepdf",
                "pypdfium2",
                "zxingcpp",
                "segno",
                "openpyxl",
                "platformdirs",
                "cryptography",
                "_cffi_backend",
                "unittest",  # OCRmyPDF imports unittest.mock at run time
            ],
            # QtSvg paints the icon set (LGPL, like the rest of Qt).
            "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtSvg",
                         "unittest.mock"],
            # readline and dbm.gnu link GNU Readline and GDBM (GPL-3.0), which must not ship;
            # curses is unused and would bring ncurses.
            "excludes": [
                "tkinter", "readline", "curses", "_curses", "dbm.gnu", "_gdbm",
                "pandas", "rapidocr", "onnxruntime", "cv2", *UNUSED_QT,
                # Never needed; only ever picked up from whatever else the build machine has.
                "numpy", "requests", "urllib3", "certifi", "idna", "yaml", "dotenv",
                "dateutil", "defusedxml",
            ],
            "include_files": include_files,
            "include_msvcr": True,
        }
    },
    executables=[
        Executable(str(HERE / "entry_cli.py"), target_name="evrakci", base="console"),
        Executable(
            str(HERE / "entry_gui.py"),
            target_name="evrakci-arayuz",
            base="gui" if sys.platform == "win32" else "console",
            icon=str(HERE / "evrakci.ico") if sys.platform == "win32" else None,
        ),
    ],
)
