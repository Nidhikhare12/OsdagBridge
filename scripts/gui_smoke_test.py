"""Offscreen GUI smoke test for the OsdagBridge desktop application.

When PySide6 is unavailable (e.g. a minimal CI/headless machine with only
PyQt5 installed), this script installs a thin compatibility layer that maps
the PySide6 modules used by the desktop UI onto PyQt5, then starts the real
``CustomWindow`` and exercises the report widgets.

Run:
    QT_QPA_PLATFORM=offscreen PYTHONPATH=src python scripts/gui_smoke_test.py
"""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import importlib.util
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if os.environ.get("GUI_VISIBLE") != "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# Force Matplotlib's Qt backend onto the installed PyQt5 binding.
os.environ.setdefault("QT_API", "pyqt5")


def install_occ_stub() -> None:
    """Provide inert OCC modules when pythonocc-core is not installed.

    The 3-D viewer is not exercised by this smoke test, so imports only need
    to succeed; real CAD work still requires pythonocc-core.
    """
    try:
        import OCC  # noqa: F401
        return
    except ImportError:
        pass

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return _Dummy()

        def __getattr__(self, name):
            return _Dummy()

    class _OccLoader(importlib.abc.Loader):
        def create_module(self, spec):
            module = types.ModuleType(spec.name)
            module.__getattr__ = lambda name: _Dummy
            if spec.name.endswith("backend"):
                module.load_backend = lambda *a, **k: None
            return module

        def exec_module(self, module):
            pass

    class _OccFinder(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname == "OCC" or fullname.startswith("OCC."):
                return importlib.machinery.ModuleSpec(fullname, _OccLoader())
            return None

    sys.meta_path.insert(0, _OccFinder())

    # qtViewer3d must be a real QWidget subclass so the viewer can host Qt
    # children (timers, overlays) during the smoke test.
    try:
        import OCC.Display.qtDisplay as qtdisplay
        try:
            from PySide6.QtWidgets import QWidget
        except Exception:
            from PyQt5.QtWidgets import QWidget

        class _ViewerStub(QWidget):
            def __getattr__(self, item):
                return lambda *a, **k: None

        qtdisplay.qtViewer3d = _ViewerStub
    except Exception:
        pass


def install_pyside6_shim() -> bool:
    """Return True when a real PySide6 was found, False when shimmed via PyQt5."""
    try:
        from PySide6.QtWidgets import QApplication  # noqa: F401
        return True
    except Exception:
        pass

    install_module_stub("shiboken6")

    import PyQt5.QtCore as qc
    import PyQt5.QtGui as qg
    import PyQt5.QtWidgets as qw
    import PyQt5.QtNetwork as qn
    import PyQt5.QtSvg as qsvg
    import PyQt5.QtWebChannel as qwebch

    # Common PySide6 -> PyQt5 API differences.
    qc.Signal = qc.pyqtSignal
    qc.Slot = qc.pyqtSlot
    qc.Property = qc.pyqtProperty
    qc.QEnum = type("QEnum", (), {})
    # Classes that live in QtGui under PySide6 but QtWidgets under PyQt5.
    qg.QAction = qw.QAction
    qg.QShortcut = qw.QShortcut

    pkg = types.ModuleType("PySide6")
    pkg.__version__ = "6.12.0"
    modules = {
        "QtCore": qc,
        "QtGui": qg,
        "QtWidgets": qw,
        "QtNetwork": qn,
        "QtSvg": qsvg,
        "QtWebChannel": qwebch,
    }
    for name, module in modules.items():
        setattr(pkg, name, module)
        sys.modules[f"PySide6.{name}"] = module

    # QtWebEngine is not needed for the report path; provide a minimal
    # QWidget-based stand-in so imports succeed.
    web_widgets = types.ModuleType("PySide6.QtWebEngineWidgets")
    web_core = types.ModuleType("PySide6.QtWebEngineCore")

    class QWebEngineView(qw.QLabel):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.page = lambda: types.SimpleNamespace(
                setWebChannel=lambda *a, **k: None,
                load=lambda *a, **k: None,
            )

        def load(self, *args, **kwargs):
            pass

        def setUrl(self, *args, **kwargs):
            pass

    class QWebEngineSettings:
        @staticmethod
        def globalSettings():
            return types.SimpleNamespace(setAttribute=lambda *a, **k: None)

    web_widgets.QWebEngineView = QWebEngineView
    web_core.QWebEngineSettings = QWebEngineSettings
    pkg.QtWebEngineWidgets = web_widgets
    pkg.QtWebEngineCore = web_core
    sys.modules["PySide6.QtWebEngineWidgets"] = web_widgets
    sys.modules["PySide6.QtWebEngineCore"] = web_core

    svg_widgets = types.ModuleType("PySide6.QtSvgWidgets")
    svg_widgets.QSvgWidget = getattr(qw, "QSvgWidget", getattr(qsvg, "QSvgWidget", qw.QLabel))
    pkg.QtSvgWidgets = svg_widgets
    sys.modules["PySide6.QtSvgWidgets"] = svg_widgets

    sys.modules["PySide6"] = pkg
    return False


def install_opensees_stub() -> None:
    """Report/GUI smoke test does not run an OpenSees analysis."""
    try:
        import openseespy  # noqa: F401
        return
    except ImportError:
        pass
    pkg = types.ModuleType("openseespy")
    ops = types.ModuleType("openseespy.opensees")
    pkg.opensees = ops
    sys.modules.setdefault("openseespy", pkg)
    sys.modules.setdefault("openseespy.opensees", ops)


def install_module_stub(name: str) -> None:
    """Install a permissive dummy module for optional analysis-only deps."""
    try:
        __import__(name)
        return
    except ImportError:
        pass

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            return _Dummy()

        def __getattr__(self, item):
            return _Dummy()

    module = types.ModuleType(name)
    module.__path__ = []
    module.__getattr__ = lambda item: _Dummy
    sys.modules[name] = module


def install_navcube_stub() -> None:
    try:
        import navcube  # noqa: F401
        return
    except ImportError:
        pass
    module = types.ModuleType("navcube")
    module.__path__ = []
    class _Signal:
        def __call__(self, *args, **kwargs):
            return self

        def connect(self, *args, **kwargs):
            pass

        def emit(self, *args, **kwargs):
            pass

    class _NavDummy:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, item):
            return _Signal()

    module.NavCubeOverlay = _NavDummy
    module.NavCubeStyle = _NavDummy
    connectors = types.ModuleType("navcube.connectors")
    connectors.__path__ = []
    occ = types.ModuleType("navcube.connectors.occ")
    occ.OCCNavCubeSync = type("OCCNavCubeSync", (), {})
    connectors.occ = occ
    module.connectors = connectors
    sys.modules["navcube"] = module
    sys.modules["navcube.connectors"] = connectors
    sys.modules["navcube.connectors.occ"] = occ


def patch_matplotlib_backend(force_qt5: bool = True) -> None:
    """Route Matplotlib's Qt backend to the same binding as the app."""
    import matplotlib

    if not force_qt5:
        os.environ["QT_API"] = "pyside6"
        return

    original_use = matplotlib.use

    def _use(name, *args, **kwargs):
        if str(name).lower() == "qtagg":
            hidden = {k: v for k, v in sys.modules.items()
                      if k == "PySide6" or k.startswith("PySide6.")}
            for key in hidden:
                del sys.modules[key]
            try:
                return original_use("Qt5Agg", *args, **kwargs)
            finally:
                sys.modules.update(hidden)
        return original_use(name, *args, **kwargs)

    matplotlib.use = _use


def main() -> int:
    install_occ_stub()
    install_opensees_stub()
    install_navcube_stub()
    install_module_stub("opsvis")
    shimmed = not install_pyside6_shim()
    patch_matplotlib_backend(force_qt5=shimmed)
    print(f"GUI binding: {'PyQt5 compatibility shim' if shimmed else 'PySide6'}")

    from PySide6.QtWidgets import QApplication
    from osdagbridge.desktop.ui.template_page import CustomWindow
    from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (
        PlateGirderBridge,
    )

    from osdagbridge.desktop.ui.cad_3d import CAD3DWindow
    # The 3-D driver is irrelevant to report generation and unavailable with
    # the OCC stub, so skip that deferred initialization cleanly.
    CAD3DWindow._complete_cad_init = lambda self: None

    app = QApplication.instance() or QApplication(sys.argv)
    window = CustomWindow("OsdagBridge", PlateGirderBridge)
    window.show()
    app.processEvents()
    print(f"Main window created: {window.windowTitle()!r}")
    print(f"Main window visible: {window.isVisible()}")
    shot = ROOT / "deliverables" / "gui_window.png"
    window.grab().save(str(shot))
    print(f"Window screenshot: {shot}")

    # The report dialog is the GUI entry point exercised by the enhanced
    # report generator.  Instantiate it directly to verify it builds.
    from osdagbridge.desktop.ui.dialogs.report_options import ReportOptionsDialog
    dialog = ReportOptionsDialog(parent=window)
    app.processEvents()
    print(f"Report options dialog created: {dialog.windowTitle()!r}")
    dialog.close()

    # Drive the real GUI report path: dialog -> QThread worker ->
    # backend.generate_design_report -> generate_report -> PDF.  The dialog's
    # modal exec() and the success message box are stubbed so this runs
    # headlessly; every other step is the production code path.
    import time
    from PySide6.QtWidgets import QDialog
    from osdagbridge.desktop.ui.dialogs import report_options as ro
    from osdagbridge.desktop.ui.dialogs import custom_messagebox as cmb
    from generate_sample_reports import (
        request_for, sample_inputs, sample_outputs,
    )
    from osdagbridge.core.reports.report_generator import (
        build_report_payload, generate_report,
    )

    out_dir = str(ROOT / "deliverables")
    stem = "Report_From_GUI"
    pdf_path = os.path.join(out_dir, stem + ".pdf")

    def _accepted_exec(self):
        self.request = request_for(out_dir, stem)
        self.is_preview = False
        return QDialog.DialogCode.Accepted

    ro.ReportOptionsDialog.exec = _accepted_exec
    cmb.CustomMessageBox.exec = lambda self, *a, **k: 0

    class _Backend:
        def generate_design_report(self, request, cad_generator, is_preview=False):
            payload = build_report_payload(
                request, sample_inputs(), sample_outputs())
            return generate_report(payload, request)

    window.backend = _Backend()
    window.open_report_dialog()

    deadline = time.time() + 120
    while time.time() < deadline and not os.path.exists(pdf_path):
        app.processEvents()
        time.sleep(0.05)

    if not os.path.exists(pdf_path):
        print("GUI report path FAILED: no PDF produced")
        window.close()
        return 1
    print(f"GUI report path PASSED: {pdf_path}")

    window.close()
    app.processEvents()
    print("GUI smoke test PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
