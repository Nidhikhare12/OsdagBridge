"""Run the desktop design and report actions with scripted dialog responses."""
import argparse
import json
import logging
import subprocess
import sys
import traceback
from collections.abc import Mapping
from datetime import date
from importlib.metadata import version
from pathlib import Path


def json_value(value):
    if isinstance(value, Mapping):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [json_value(v) for v in value]
    if hasattr(value, "tolist"):
        return json_value(value.tolist())
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return repr(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("design", type=Path)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--report-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--reapply-live-load-inputs", action="store_true",
                        help="Enter the OSI live-load choices in the Additional Inputs dialog.")
    args = parser.parse_args()
    design, pdf = args.design.resolve(), args.pdf.resolve()
    if pdf.exists():
        parser.error("Choose a fresh output filename or directory.")
    pdf.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QLineEdit
    from osdagbridge.desktop.__main__ import CustomWindow, PlateGirderBridge, load_stylesheet
    from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox
    from osdagbridge.desktop.ui.dialogs.report_options import ReportOptionsDialog

    print("Python:", sys.version)
    print("Git commit:", subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
    for package in ("PySide6", "matplotlib", "numpy", "openseespy"):
        print(f"{package}={version(package)}")

    app = QApplication([])
    app.setStyleSheet(load_stylesheet())
    window = CustomWindow("OsdagBridge report verification", PlateGirderBridge)
    window.showMaximized()

    # Script only the dialog boundary. Loading, validation, Qt design worker,
    # figure capture, report request and report worker run through the desktop.
    QFileDialog.getOpenFileName = lambda *a, **kw: (str(design), "Input Files (*.osi)")
    CustomMessageBox.exec = lambda self: print("Application dialog:", self.windowTitle()) or 0

    def select_report(dialog):
        dialog.project_name.setText("OsdagBridge test design")
        dialog.request = dialog.build_request(str(pdf))
        dialog.request.metadata.report_date = args.report_date.isoformat()
        print("Report options:", dialog.request.options)
        return QDialog.DialogCode.Accepted

    ReportOptionsDialog.exec = select_report
    stage = "design"
    timer = QTimer()
    timer.setInterval(500)

    def check_progress():
        nonlocal stage
        try:
            if stage == "design" and not getattr(window, "_design_running", False):
                backend = window.backend
                if not backend.output_dict.get("design_results"):
                    raise RuntimeError("Desktop analysis did not return design results")
                for name, data in (("inputs", backend.input_dict), ("outputs", backend.output_dict)):
                    pdf.with_suffix(f".{name}.json").write_text(
                        json.dumps(json_value(data), ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                window.output_dock._on_report_clicked()
                if not hasattr(window, "_report_thread"):
                    raise RuntimeError("Desktop report worker did not start")
                stage = "report"
            elif stage == "report" and not window._report_thread.isRunning():
                result = 0 if pdf.is_file() else 1
                window.close()
                app.exit(result)
        except Exception:
            traceback.print_exc()
            app.exit(1)

    def reapply_live_load_inputs():
        import yaml

        saved = yaml.safe_load(design.read_text(encoding="utf-8"))
        window.update_cad_from_inputs()
        window._show_additional_inputs("Live Load")
        additional = window._additional_inputs_dialog
        keys = [key for key in saved if key.startswith("loading.live_load.irc.")]
        for key in keys:
            additional.findChild(QCheckBox, key).setChecked(saved[key])
        mode_key = "loading.live_load.footpath_pressure.mode"
        value_key = "loading.live_load.footpath_pressure.value"
        additional.findChild(QComboBox, mode_key).setCurrentText(saved[mode_key])
        value = additional.findChild(QLineEdit, value_key)
        value.setText(str(saved[value_key]))
        value.editingFinished.emit()
        additional.save_button.click()
        additional.hide()
        for key in keys + [mode_key]:
            if window.input_dict.get(key) != saved[key]:
                raise RuntimeError(f"Additional Inputs did not retain {key}")
        if float(window.input_dict[value_key]) != float(saved[value_key]):
            raise RuntimeError("Additional Inputs did not retain the custom footpath pressure")

    def start():
        try:
            window.loadOSI_inputs()
            if args.reapply_live_load_inputs:
                reapply_live_load_inputs()
            window.common_design_func("Design")
            if not getattr(window, "_design_running", False):
                raise RuntimeError("Desktop design worker did not start")
            timer.start()
        except Exception:
            traceback.print_exc()
            app.exit(1)

    timer.timeout.connect(check_progress)
    QTimer.singleShot(0, start)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
