from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from osdagbridge.desktop.ui.dialogs.generate_results_dialog import ExportTablePage


def _qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_export_page_keeps_selected_tables_checked(qtbot=None):
    app = _qt_app()
    page = ExportTablePage(on_back=lambda: None, on_cancel=lambda: None)
    page.load_data({
        "Bridge Data": {
            "Model Definition": {
                "Bridge Configuration Summary": {
                    "id": "bridge_configuration_summary",
                    "columns": ["Span (m)"],
                    "rows": [["30"]],
                }
            }
        }
    })

    root = page.tree.invisibleRootItem()
    main = root.child(0)
    group = main.child(0)
    leaf = group.child(0)

    assert main.checkState(0) == Qt.Checked
    assert group.checkState(0) == Qt.Checked
    assert leaf.checkState(0) == Qt.Checked

    page.deleteLater()
    app.processEvents()
