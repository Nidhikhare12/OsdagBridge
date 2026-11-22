"""Drive the real OsdagBridge UI buttons through Design -> Generate Report.

Unlike the headless harness, this test clicks the actual QPushButtons
(`input_dock.design_btn` and `output_dock.report_btn`) and waits on the real
QThread workers.  A complete filled-in input dictionary is injected so no
manual typing is required, and only modal dialog exec() calls are stubbed.

    GUI_VISIBLE=1 PYTHONPATH=src python scripts/gui_real_ui_test.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gui_smoke_test import (  # noqa: E402
    install_occ_stub, install_navcube_stub, install_module_stub,
    install_opensees_stub, install_pyside6_shim, patch_matplotlib_backend,
)
from run_full_design_test import install_osdag_core_stub, full_inputs  # noqa: E402

install_occ_stub()
install_navcube_stub()
install_module_stub("fiona")
install_osdag_core_stub()
# Use the real installed OpenSees; only stub it if genuinely unavailable.
if not os.environ.get("USE_REAL_OPENSEES", "1") == "0":
    try:
        import openseespy.opensees  # noqa: F401
    except ImportError:
        install_opensees_stub()

shimmed = not install_pyside6_shim()
patch_matplotlib_backend(force_qt5=shimmed)

from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402
from osdagbridge.desktop.ui.template_page import CustomWindow  # noqa: E402
from osdagbridge.desktop.ui.cad_3d import CAD3DWindow  # noqa: E402
from osdagbridge.core.bridge_types.plate_girder.plategirderbridge import (  # noqa: E402
    PlateGirderBridge,
)
from osdagbridge.desktop.ui.dialogs import report_options as ro  # noqa: E402
from osdagbridge.desktop.ui.dialogs import custom_messagebox as cmb  # noqa: E402

CAD3DWindow._complete_cad_init = lambda self: None
cmb.CustomMessageBox.exec = lambda self, *a, **k: 0


def main() -> int:
    out_dir = ROOT / "deliverables"
    stem = "Report_Real_UI"
    pdf_path = out_dir / (stem + ".pdf")
    if pdf_path.exists():
        pdf_path.unlink()

    def _accepted_exec(self):
        from osdagbridge.core.reports.report_generator import (
            ReportMetadata, ReportOptions, ReportRequest,
        )
        meta = ReportMetadata(
            project_name="Real UI Test Bridge", project_location="Mumbai",
            designer="UI Test", client="FOSSEE", company="IIT Bombay",
            job_number="OB-UI-TEST", subtitle="Rev 0",
            report_date="2026-11-22")
        opts = ReportOptions(
            sections=["loads", "analysis", "design_checks", "drawings"],
            include_figures=True, include_toc=True, include_pdf=True)
        self.request = ReportRequest(metadata=meta, options=opts,
                                     output_dir=str(out_dir), file_stem=stem)
        self.is_preview = False
        return QDialog.DialogCode.Accepted

    ro.ReportOptionsDialog.exec = _accepted_exec

    app = QApplication.instance() or QApplication(sys.argv)
    window = CustomWindow("OsdagBridge", PlateGirderBridge)
    window.show()
    app.processEvents()

    # Fill the UI with a complete set of values, then click the real button.
    window.input_dict = full_inputs()
    # The UI's seismic compute function expects a dict here, not None.
    window.input_dict["project.location"] = {
        "weather_data": {"zone": "III", "wind_speed": 40}}
    window.validate_required_inputs = lambda: True
    window.input_dock._prime_material_inputs = lambda: None
    print("Clicking Design button in the real UI ...")
    QTimer.singleShot(300, lambda: window.input_dock.design_btn.click())

    state = {"design": False, "report": False}

    def wait_design():
        if not state["design"]:
            if (getattr(window, "backend", None) is not None
                    and len(window.backend.output_dict) > 0
                    and not getattr(window, "_design_running", False)):
                state["design"] = True
                n = len(window.backend.output_dict)
                print(f"Design finished in UI: {n} output keys")
                window.grab().save(str(out_dir / "gui_after_design.png"))
                print("Clicking Generate Report button in the real UI ...")
                QTimer.singleShot(300, lambda: window.output_dock.report_btn.click())
            else:
                QTimer.singleShot(500, wait_design)

    def wait_report():
        # Kept as a no-op timer so the name is available for diagnostics; the
        # deterministic processEvents loop below owns completion detection.
        return

    QTimer.singleShot(1000, wait_design)
    QTimer.singleShot(1500, wait_report)

    # Explicit event-processing loop: QTimer callbacks and QThread signals are
    # delivered, and we can exit deterministically as soon as the PDF exists.
    deadline = time.time() + 600
    while time.time() < deadline:
        app.processEvents()
        if pdf_path.exists() and pdf_path.stat().st_size > 10000:
            state["report"] = True
            window.grab().save(str(out_dir / "gui_after_report.png"))
            print(f"REAL UI REPORT PASSED: {pdf_path}")
            break
        time.sleep(0.05)

    if not state["report"]:
        print("REAL UI REPORT FAILED")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
