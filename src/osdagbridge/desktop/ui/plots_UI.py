import sys
import os
import json

# Performance Flags: Tuned for Screen Recording / Meetings on Windows
os.environ["QT_OPENGL"] = "software"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--ignore-gpu-blocklist "
    "--enable-gpu-rasterization "
    "--enable-webgl "
    "--enable-transparent-visuals "
    "--disable-software-rasterizer "
    "--disable-gpu-driver-bug-workarounds"
    "--use-angle=d3d11 "
)

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QDialog
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, Qt, QPoint, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel

# --- IMPORT THE BACKEND LOGIC ---
from osdagbridge.core.bridge_types.plate_girder.plots_widget import (
    build_figure_sfd,
    build_figure_sfd_contour,
    build_figure_bmd,
    build_figure_bmd_contour,
    FORCE_MAP,
)

# =========================================================
# THE RAM-ONLY FRONTEND
# =========================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        body { margin: 0; padding: 0; background-color: white; overflow: hidden; }
        #plot_div { width: 100vw; height: 100vh; }
    </style>
</head>
<body>
    <div id="plot_div"></div>

    <script>
        var pyBackend = null;

        // Initialize QWebChannel
        new QWebChannel(qt.webChannelTransport, function(channel) {
            pyBackend = channel.objects.backend;

            // Listen for data from Python
            pyBackend.newPlotData.connect(function(jsonString) {
                renderPlot(jsonString);
            });

            // Tell Python the page is ready
            pyBackend.pageReady();
        });

        function renderPlot(jsonString) {
            var figure = JSON.parse(jsonString);
            var config = { displayModeBar: true, responsive: true };

            Plotly.react('plot_div', figure.data, figure.layout, config).then(function() {
                var targetDiv = document.getElementById('plot_div');
                Plotly.Plots.resize(targetDiv);

                if (!targetDiv.hasRelayoutListener) {
                    targetDiv.on('plotly_relayout', function(eventdata) {
                        var eventString = JSON.stringify(eventdata);
                        if (eventString && eventString.includes('SHOW_SUMMARY')) {
                            // Call Python natively! No console hacks.
                            pyBackend.requestSummaryDialog();
                            setTimeout(function() {
                                Plotly.relayout('plot_div', {meta: "CLEAR"});
                            }, 100);
                        }
                    });
                    targetDiv.hasRelayoutListener = true;
                }
            });
        }
    </script>
</body>
</html>
"""

class BridgeBackend(QObject):
    """The QWebChannel translator between Python and JavaScript."""
    
    # Signal: Python uses this to push JSON data to JavaScript
    newPlotData = Signal(str)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

    @Slot()
    def pageReady(self):
        """JavaScript calls this when the page is fully loaded."""
        self.main_app.update_plot()

    @Slot()
    def requestSummaryDialog(self):
        """JavaScript calls this when the 'SUMMARY' button is clicked."""
        self.main_app.show_summary_dialog()


class SummaryDialog(QDialog):
    """A floating tool palette that hovers over the main UI without disturbing it."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extreme Values")
        
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.resize(350, 250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Girder", "Max (N mm)", "Min (N mm)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def update_data(self, stats):
        self.table.setRowCount(len(stats))
        for row, (girder, vals) in enumerate(stats.items()):
            item_girder = QTableWidgetItem(girder)
            item_max = QTableWidgetItem(f"{vals['max']:.2f}")
            item_min = QTableWidgetItem(f"{vals['min']:.2f}")
            
            item_max.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_min.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 0, item_girder)
            self.table.setItem(row, 1, item_max)
            self.table.setItem(row, 2, item_min)


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Girder Results")

        self._ds_all = None
        self._nodes = {}
        self._members = {}
        self._available_loadcases = []
        self._available_girders = ["All"]
        self._output_dock = None
        self._external_controls_bound = False
        self._state = {
            "loadcase": "",
            "force_key": "Fy",
            "show_grid": True,
            "scale_factor": 1.0,
            "isolated_girder": "All",
            "show_contour": False,
            "show_max": False,
            "show_min": False,
        }

        layout = QVBoxLayout(self)
        self.control_panel = QWidget()
        top = QHBoxLayout(self.control_panel)
        top.setContentsMargins(0, 0, 0, 0)

        top.addWidget(QLabel("Load case:"))
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self._on_internal_control_changed)
        top.addWidget(self.combo)

        top.addWidget(QLabel("Force:"))
        self.force_combo = QComboBox()
        self.force_combo.addItems(list(FORCE_MAP.keys()))
        self.force_combo.setCurrentText("Fy")
        self.force_combo.currentTextChanged.connect(self._on_internal_control_changed)
        top.addWidget(self.force_combo)

        self.contour = QCheckBox("Contour (Fy)")
        self.contour.stateChanged.connect(self._on_internal_control_changed)
        top.addWidget(self.contour)

        top.addStretch()
        layout.addWidget(self.control_panel)

        self.web = QWebEngineView()
        self.web.setAttribute(Qt.WA_OpaquePaintEvent)
        self.web.setAttribute(Qt.WA_NoSystemBackground)
        self.web.page().setBackgroundColor(Qt.white)

        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self.web)

        self.stats_dict = {}
        self.summary_dialog = SummaryDialog(self)

        self.channel = QWebChannel()
        self.backend = BridgeBackend(self)
        self.channel.registerObject("backend", self.backend)
        self.web.page().setWebChannel(self.channel)
        self.web.setHtml(HTML_TEMPLATE, QUrl("qrc:/"))

    def bind_output_dock(self, output_dock):
        self._output_dock = output_dock
        self._external_controls_bound = True
        self.control_panel.setVisible(False)
        self._sync_output_dock_options()

    def _sync_output_dock_options(self):
        if self._output_dock is not None:
            self._output_dock.update_plot_options(
                loadcases=self._available_loadcases,
                girders=self._available_girders,
            )

    def _normalize_force_key(self, value: str) -> str:
        aliases = {"Tx": "Mx", "Vx": "Fx", "Vy": "Fy", "Vz": "Fz"}
        return aliases.get(value, value)

    def _compute_available_girders(self):
        if not self._nodes or not self._members:
            return ["All"]

        from collections import defaultdict

        z_groups = defaultdict(list)
        for _, (n1, n2) in self._members.items():
            z1 = round(float(self._nodes[n1][2]), 3)
            z2 = round(float(self._nodes[n2][2]), 3)
            if z1 == z2:
                z_groups[z1].append((n1, n2))

        return ["All"] + [f"G{i + 1}" for i, _ in enumerate(sorted(z_groups.items(), key=lambda item: item[0]))]

    def available_girders(self):
        return list(self._available_girders)

    def setup(self, ds_all, loadcases, nodes, members):
        """Populate the widget with bridge analysis results. Call after design() completes."""
        self._ds_all = ds_all
        self._nodes = nodes
        self._members = members
        self._available_loadcases = list(loadcases or [])
        self._available_girders = self._compute_available_girders()

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self._available_loadcases)
        if self._available_loadcases:
            self.combo.setCurrentIndex(0)
        self.combo.blockSignals(False)

        if self._output_dock is not None:
            self._sync_output_dock_options()

        self.update_plot()

    def _on_internal_control_changed(self, *_):
        if self._external_controls_bound:
            return
        self._state.update({
            "loadcase": self.combo.currentText(),
            "force_key": self._normalize_force_key(self.force_combo.currentText()),
            "show_contour": self.contour.isChecked(),
        })
        self.update_plot()

    def apply_output_state(self, state: dict):
        self._state.update(state or {})

        loadcase = self._state.get("loadcase", "")
        if loadcase:
            self.combo.blockSignals(True)
            self.combo.setCurrentText(loadcase)
            self.combo.blockSignals(False)

        force_key = self._normalize_force_key(self._state.get("force_key", "Fy"))
        self.force_combo.blockSignals(True)
        self.force_combo.setCurrentText(force_key)
        self.force_combo.blockSignals(False)

        contour_enabled = force_key == "Fy" or force_key.startswith("M")
        self.contour.blockSignals(True)
        self.contour.setEnabled(contour_enabled)
        self.contour.setChecked(bool(self._state.get("show_contour")) and contour_enabled)
        self.contour.blockSignals(False)

        self.update_plot()

    def show_summary_dialog(self):
        """Pops up the dialog perfectly in the top-left corner of the web view."""
        if not self.stats_dict:
            return

        self.summary_dialog.update_data(self.stats_dict)
        self.summary_dialog.show()
        self.summary_dialog.raise_()
        self.summary_dialog.activateWindow()

        top_left_corner = self.web.mapToGlobal(QPoint(15, 15))
        self.summary_dialog.move(top_left_corner)

    def _resolve_selected_state(self):
        loadcase = self._state.get("loadcase") or self.combo.currentText()
        force_key = self._normalize_force_key(self._state.get("force_key") or self.force_combo.currentText())
        show_grid = bool(self._state.get("show_grid", True))
        scale_factor = float(self._state.get("scale_factor", 1.0))
        isolated_girder = self._state.get("isolated_girder", "All")
        show_contour = bool(self._state.get("show_contour", False))
        show_max = bool(self._state.get("show_max", False))
        show_min = bool(self._state.get("show_min", False))

        if self.contour.isEnabled():
            show_contour = show_contour or self.contour.isChecked()

        if not loadcase and self._available_loadcases:
            loadcase = self._available_loadcases[0]

        return loadcase, force_key, show_grid, scale_factor, isolated_girder, show_contour, show_max, show_min

    def update_plot(self):
        if self._ds_all is None:
            return

        loadcase, force_key, show_grid, scale_factor, isolated_girder, show_contour, show_max, show_min = self._resolve_selected_state()
        if not loadcase:
            return

        ds = self._ds_all.sel(Loadcase=loadcase)
        include_controls = not self._external_controls_bound

        if force_key.startswith("F"):
            self.stats_dict = {}
            if force_key == "Fy" and show_contour:
                plot_json = build_figure_sfd_contour(
                    ds, force_key, self._nodes, self._members,
                    show_grid=show_grid, scale_factor=scale_factor,
                    isolated_girder=isolated_girder, include_controls=include_controls,
                )
            else:
                plot_json = build_figure_sfd(
                    ds, force_key, self._nodes, self._members,
                    show_grid=show_grid, scale_factor=scale_factor,
                    isolated_girder=isolated_girder, include_controls=include_controls,
                )

        elif force_key.startswith("M"):
            if show_contour:
                self.stats_dict = {}
                plot_json = build_figure_bmd_contour(
                    ds, force_key, self._nodes, self._members,
                    show_grid=show_grid, scale_factor=scale_factor,
                    isolated_girder=isolated_girder, include_controls=include_controls,
                )
            else:
                plot_json, self.stats_dict = build_figure_bmd(
                    ds, force_key, self._nodes, self._members,
                    show_grid=show_grid, scale_factor=scale_factor,
                    isolated_girder=isolated_girder, show_max=show_max, show_min=show_min,
                    include_controls=include_controls,
                )

                if self.summary_dialog.isVisible():
                    self.summary_dialog.update_data(self.stats_dict)
        else:
            raise ValueError(f"Unsupported force: {force_key}")

        self.backend.newPlotData.emit(plot_json)


# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())