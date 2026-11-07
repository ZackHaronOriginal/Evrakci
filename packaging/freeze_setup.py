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

include_files = [(str(path), path.name) for path in STAGE.iterdir()] if STAGE.is_dir() else []
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
            "includes": ["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "unittest.mock"],
            "excludes": ["tkinter", "pandas", "rapidocr", "onnxruntime", "cv2", *UNUSED_QT],
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
        ),
    ],
)
