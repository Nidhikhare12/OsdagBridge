"""Offscreen Qt smoke test for Report Options dialog (AUD-16).

Verifies headless instantiation, theme selector dropdown, chart toggle checkboxes,
and option propagation into the generated ReportRequest / ReportOptions dataclasses.
"""

import os
import pytest

# Ensure headless offscreen rendering for PySide6 in CI / headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PySide6.QtWidgets import QApplication
    from osdagbridge.desktop.ui.dialogs.report_options import ReportOptionsDialog
    HAS_PYSIDE6 = True
except Exception:
    HAS_PYSIDE6 = False


@pytest.mark.skipif(not HAS_PYSIDE6, reason="PySide6 GUI bindings unavailable in this environment")
def test_report_options_dialog_ui_state_and_options_propagation(tmp_path):
    """Verify ReportOptionsDialog UI elements and options serialization in offscreen Qt."""
    app = QApplication.instance() or QApplication([])
    assert app is not None

    dialog = ReportOptionsDialog()
    assert dialog.objectName() == "report_options_dialog"

    # 1. Verify theme dropdown contains registered presets
    assert hasattr(dialog, "theme_combo"), "dialog must possess theme_combo dropdown"
    themes_in_dropdown = [dialog.theme_combo.itemText(i) for i in range(dialog.theme_combo.count())]
    expected_themes = ["osdag_classic", "print_mono", "accessible"]
    for t_expected in expected_themes:
        assert t_expected in themes_in_dropdown, f"Theme '{t_expected}' missing from theme dropdown"

    # 2. Verify checkboxes for charts exist and default to checked
    assert hasattr(dialog, "chk_utilization"), "dialog must possess chk_utilization checkbox"
    assert hasattr(dialog, "chk_quantities"), "dialog must possess chk_quantities checkbox"
    assert dialog.chk_utilization.isChecked() is True, "UR charts must default to checked"
    assert dialog.chk_quantities.isChecked() is True, "Quantity charts must default to checked"

    # 3. Default options extraction via build_request
    out_pdf = str(tmp_path / "default_options.pdf")
    default_request = dialog.build_request(out_pdf)
    assert default_request.options.theme == "osdag_classic"
    assert default_request.options.include_utilization_charts is True
    assert default_request.options.include_quantity_charts is True

    # 4. Modify options and verify propagation
    dialog.theme_combo.setCurrentText("accessible")
    dialog.chk_utilization.setChecked(False)
    dialog.chk_quantities.setChecked(True)

    modified_pdf = str(tmp_path / "modified_options.pdf")
    modified_request = dialog.build_request(modified_pdf)
    assert modified_request.options.theme == "accessible", "Theme change did not propagate"
    assert modified_request.options.include_utilization_charts is False, "UR toggle did not propagate"
    assert modified_request.options.include_quantity_charts is True, "Quantity toggle did not propagate"

    # Clean up dialog widget
    dialog.close()
