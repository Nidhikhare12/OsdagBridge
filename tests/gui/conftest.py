"""
Opt-in GUI scenario tests: they drive the real OsdagBridge window off-screen
(double-clicks, key presses, dialog buttons) the way a user would.

    OSDAG_GUI_TESTS=1 QT_QPA_PLATFORM=offscreen pytest tests/gui

On Linux, OpenCascade's 3-D display needs an X server even when Qt renders
off-screen, so run them under a virtual display there:

    OSDAG_GUI_TESTS=1 QT_QPA_PLATFORM=offscreen xvfb-run -a pytest tests/gui

They are skipped by default because they need a display-capable PySide6 /
pythonOCC install and take ~30 s (the transverse-plot test runs a full
Design). The OpenGL 3-D viewer and the loading popup are stubbed out; every
CustomMessageBox is captured instead of blocking, see ``messages``.
"""

import os
import sys
import time

import pytest

if os.environ.get("OSDAG_GUI_TESTS") != "1":
    collect_ignore_glob = ["test_*.py"]

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

LOCATION = {
    "city": "Mumbai", "state": "Maharashtra",
    "weather_data": {"wind_speed": 44, "zone": "III", "max_temp": 40, "min_temp": 12},
}


def _stub_heavy_widgets():
    import OCC.Display.qtDisplay as qt_display
    import osdagbridge.desktop.ui.cad_3d as cad_3d
    import osdagbridge.desktop.ui.dialogs.loading_popup as loading_popup

    for module in (cad_3d, qt_display):
        for name in dir(module):
            obj = getattr(module, name)
            if not isinstance(obj, type):
                continue
            if hasattr(obj, "_deferred_init_driver"):
                obj._deferred_init_driver = lambda self: None
            if hasattr(obj, "InitDriver"):
                obj.InitDriver = lambda self, *a, **k: None
                obj.paintEvent = lambda self, e: None
            if hasattr(obj, "render_3d_cad"):
                obj.render_3d_cad = lambda self, *a, **k: None

    mgr = loading_popup.LoadingDialogManager
    mgr.show = lambda self: None
    mgr.hide = lambda self: None
    mgr.send_message = lambda self, m, l: None
    mgr.is_cancelled = lambda self: False
    mgr.__del__ = lambda self: None


class MessageLog(list):
    """Captured CustomMessageBox texts; ``reply`` is what exec() returns."""
    reply = None

    def since(self, n):
        return self[n:]


@pytest.fixture(scope="session")
def qapp():
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY")
                                                 or os.environ.get("WAYLAND_DISPLAY")):
        pytest.skip("No X display: OpenCascade's 3-D viewer needs one on Linux. "
                    "Run the GUI tests under xvfb-run.")
    from PySide6.QtWidgets import QApplication
    import osdagbridge.desktop.__main__ as main

    _stub_heavy_widgets()
    app = QApplication.instance() or QApplication(["osdagbridge-gui-tests"])
    app.setStyleSheet(main.load_stylesheet())
    return app


@pytest.fixture(scope="session")
def messages(qapp):
    from PySide6.QtWidgets import QLabel
    from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox

    log = MessageLog()
    original = CustomMessageBox.exec

    def fake_exec(box):
        log.append(" | ".join(l.text() for l in box.findChildren(QLabel) if l.text()))
        return log.reply if log.reply is not None else 0

    CustomMessageBox.exec = fake_exec
    yield log
    CustomMessageBox.exec = original


@pytest.fixture
def pump(qapp):
    def _pump(ms=200):
        end = time.time() + ms / 1000
        while time.time() < end:
            qapp.processEvents()
    return _pump


@pytest.fixture
def window(qapp, messages, pump):
    import osdagbridge.desktop.__main__ as main

    win = main.CustomWindow("OsdagBridge", main.PlateGirderBridge)
    win.resize(1600, 950)
    win.show()
    pump(800)
    messages.reply = None
    yield win
    win.close()
    win.deleteLater()
    pump(100)


@pytest.fixture
def type_into(pump):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    def _type(widget, text):
        widget.setFocus()
        widget.selectAll()
        QTest.keyClicks(widget, text)
        QTest.keyClick(widget, Qt.Key_Return)
        pump(100)
    return _type


@pytest.fixture
def basic_inputs(window, type_into, pump):
    """Fill the required Basic Inputs (span 35 m, carriageway 7.5 m)."""
    from PySide6.QtWidgets import QLineEdit
    from osdagbridge.core.utils.common import KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_PROJECT_LOCATION

    def field(key):
        return window.input_dock.input_widget.findChild(QLineEdit, key)

    type_into(field(KEY_SPAN), "35")
    type_into(field(KEY_CARRIAGEWAY_WIDTH), "7.5")
    window.input_dict[KEY_PROJECT_LOCATION] = LOCATION
    pump(500)
    return field
