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
    QHeaderView, QPushButton, QDialog, QSlider
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, Qt, QPoint, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel

# --- IMPORT THE BACKEND LOGIC ---
from osdagbridge.core.bridge_types.plate_girder.plots_widget import (
    build_figure_sfd,
    build_figure_bmd,
    build_figure_bmd_contour,
    build_figure_sfd_contour,
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

                // Reset cached aspect ratio when a new plot is loaded
                targetDiv._baseAspect = null;

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

                    // Custom legend click handler - Plotly's built-in toggle
                    // doesn't always work for Surface traces in a legendgroup,
                    // so we manually set visibility for all traces in the group.
                    targetDiv.on('plotly_legendclick', function(eventdata) {
                        var clickedGroup = eventdata.data[eventdata.curveNumber].legendgroup;
                        if (!clickedGroup) return true;  // let Plotly handle non-grouped traces

                        var plotDiv = document.getElementById('plot_div');
                        var isCurrentlyVisible = (eventdata.data[eventdata.curveNumber].visible !== 'legendonly');

                        // Toggle all traces sharing this legendgroup
                        var indices = [];
                        for (var i = 0; i < plotDiv.data.length; i++) {
                            if (plotDiv.data[i].legendgroup === clickedGroup) {
                                indices.push(i);
                            }
                        }
                        var newVis = isCurrentlyVisible ? 'legendonly' : true;
                        Plotly.restyle('plot_div', {'visible': newVis}, indices);

                        return false;  // prevent Plotly's default legend click
                    });

                    targetDiv.hasRelayoutListener = true;
                }
            });
        }

        // ---- Grid visibility toggle ----
        function toggleGrid(show) {
            Plotly.relayout('plot_div', {
                'scene.xaxis.showgrid': show,
                'scene.zaxis.showgrid': show
            });
        }

        // ---- Scale adjustment via aspect ratio ----
        // Captures the initial data-driven aspect ratio on first call,
        // then scales the Y axis relative to that baseline.
        function setScale(factor) {
            var plotDiv = document.getElementById('plot_div');
            if (!plotDiv._fullLayout || !plotDiv._fullLayout.scene) return;

            if (!plotDiv._baseAspect) {
                var scene = plotDiv._fullLayout.scene;
                plotDiv._baseAspect = {
                    x: scene.aspectratio.x,
                    y: scene.aspectratio.y,
                    z: scene.aspectratio.z
                };
            }

            Plotly.relayout('plot_div', {
                'scene.aspectmode': 'manual',
                'scene.aspectratio.x': plotDiv._baseAspect.x,
                'scene.aspectratio.y': plotDiv._baseAspect.y * factor,
                'scene.aspectratio.z': plotDiv._baseAspect.z
            });
        }

        // ---- Isolate a single girder by legendgroup ----
        // "All" restores every trace; otherwise only traces matching
        // the given girder name stay visible.
        function isolateGirder(girderName) {
            var plotDiv = document.getElementById('plot_div');
            if (!plotDiv.data) return;

            var visibility = [];
            for (var i = 0; i < plotDiv.data.length; i++) {
                var trace = plotDiv.data[i];
                // Shared traces (grillage background, triad) have no legendgroup
                if (!trace.legendgroup) {
                    visibility.push(true);
                } else if (girderName === 'All') {
                    visibility.push(true);
                } else {
                    visibility.push(trace.legendgroup === girderName);
                }
            }
            Plotly.restyle('plot_div', {'visible': visibility});
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

        # Populated by setup() after bridge analysis completes
        self._ds_all = None
        self._nodes = {}
        self._members = {}

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        # Force black text on all plot controls - the parent window's stylesheet
        # sets a global background that can leave text invisible without this.
        self.setStyleSheet("""
            QLabel { color: #1a1a2e; font-size: 12px; }
            QComboBox { color: #1a1a2e; background: #f5f5f5; border: 1px solid #ccc;
                        padding: 2px 6px; min-width: 80px; }
            QComboBox QAbstractItemView { color: #1a1a2e; background: white; }
            QCheckBox { color: #1a1a2e; spacing: 4px; }
            QSlider::groove:horizontal { height: 6px; background: #ddd; border-radius: 3px; }
            QSlider::handle:horizontal { width: 14px; margin: -4px 0;
                                          background: #4a90d9; border-radius: 7px; }
        """)

        # ---------- CONTOUR CHECKBOX ----------
        # Supports Fy shear contour in addition to moments
        self.contour = QCheckBox("Contour")
        self.contour.stateChanged.connect(self.update_plot)
        top.addWidget(self.contour)

        # ---------- GRID VISIBILITY ----------
        self.grid_cb = QCheckBox("Grid")
        self.grid_cb.setChecked(True)
        self.grid_cb.stateChanged.connect(self._toggle_grid)
        top.addWidget(self.grid_cb)

        # ---------- SCALE SLIDER ----------
        top.addWidget(QLabel("Scale:"))
        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(1, 20)
        self.scale_slider.setValue(10)          # 10 = 1.0x (default)
        self.scale_slider.setFixedWidth(100)
        self.scale_slider.valueChanged.connect(self._set_scale)
        top.addWidget(self.scale_slider)

        # ---------- ISOLATE GIRDER ----------
        top.addWidget(QLabel("Girder:"))
        self.girder_combo = QComboBox()
        self.girder_combo.addItem("All")
        self.girder_combo.currentTextChanged.connect(self._isolate_girder)
        top.addWidget(self.girder_combo)

        top.addStretch()
        layout.addLayout(top)

        # ---------- MAIN BROWSER AREA ----------
        self.web = QWebEngineView()
        
        # Stops Qt from painting a blank background behind the web viewer
        self.web.setAttribute(Qt.WA_OpaquePaintEvent)
        self.web.setAttribute(Qt.WA_NoSystemBackground)
        self.web.page().setBackgroundColor(Qt.white)

        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self.web)

        # ---------- INITIALIZATION & QWEBCHANNEL ----------
        self.stats_dict = {}  
        self.summary_dialog = SummaryDialog(self)

        self.channel = QWebChannel()
        self.backend = BridgeBackend(self)
        
        self.channel.registerObject("backend", self.backend)
        self.web.page().setWebChannel(self.channel)

        # Inject HTML directly into memory
        self.web.setHtml(HTML_TEMPLATE, QUrl("qrc:/"))

    def setup(self, ds_all, loadcases, nodes, members):
        """Populate the widget with bridge analysis results. Call after design() completes."""
        self._ds_all = ds_all
        self._loadcases = loadcases
        self._nodes = nodes
        self._members = members

        # Default to first loadcase and Fy force
        self._current_loadcase = loadcases[0] if loadcases else ""
        self._current_force = "Fy"

        # Populate the girder isolation dropdown based on the model
        self._populate_girder_combo()

        # Push loadcase names to the output dock's Load Combination combobox
        # so users can switch loadcases from the output panel.
        # self.window() reaches the CustomWindow (top-level), not just the splitter.
        main_window = self.window()
        if main_window and hasattr(main_window, "output_dock") and main_window.output_dock:
            main_window.output_dock.populate_loadcases(loadcases)

    def _populate_girder_combo(self):
        """Fill the girder combobox with names derived from the model geometry."""
        # Count longitudinal members (same Z for both end nodes) to find girders
        z_vals = set()
        for ele_tag, (n1, n2) in self._members.items():
            z1 = round(self._nodes[n1][2], 3)
            z2 = round(self._nodes[n2][2], 3)
            if z1 == z2:
                z_vals.add(z1)

        self.girder_combo.blockSignals(True)
        self.girder_combo.clear()
        self.girder_combo.addItem("All")
        for i in range(len(sorted(z_vals))):
            self.girder_combo.addItem(f"G{i+1}")
        self.girder_combo.blockSignals(False)

    # ---- JS-driven controls (no figure rebuild needed) ----

    def _toggle_grid(self, state):
        """Show or hide grid lines on the 3D plot axes."""
        show = "true" if state else "false"
        self.web.page().runJavaScript(f"toggleGrid({show})")

    def _set_scale(self, value):
        """Scale the force diagram height. Slider 1-20 maps to 0.1x - 2.0x."""
        factor = value / 10.0
        self.web.page().runJavaScript(f"setScale({factor})")

    def _isolate_girder(self, girder_name):
        """Show only the selected girder, or 'All' to restore everything."""
        self.web.page().runJavaScript(f"isolateGirder('{girder_name}')")

    # ---- Summary dialog ----

    def show_summary_dialog(self):
        """Pops up the dialog perfectly in the top-left corner of the web view."""
        if not self.stats_dict:
            return

        self.summary_dialog.update_data(self.stats_dict)
        self.summary_dialog.show()
        self.summary_dialog.raise_()
        self.summary_dialog.activateWindow()

        # Calculate exactly where the top-left of the 3D plot is on the screen
        top_left_corner = self.web.mapToGlobal(QPoint(15, 15))
        self.summary_dialog.move(top_left_corner)

    # ---- Public setters (called by output dock) ----

    def set_loadcase(self, loadcase_name):
        """Set the active load case and refresh the plot."""
        if loadcase_name and loadcase_name != self._current_loadcase:
            self._current_loadcase = loadcase_name
            self.update_plot()

    def set_force(self, force_key):
        """Set the active force component and refresh the plot."""
        if force_key and force_key != self._current_force:
            self._current_force = force_key
            self.update_plot()

    # ---- Main plot update ----

    def update_plot(self):
        if self._ds_all is None:
            return

        loadcase = self._current_loadcase
        force_key = self._current_force

        if not loadcase or loadcase not in self._ds_all.Loadcase.values:
            return

        ds = self._ds_all.sel(Loadcase=loadcase)

        is_force = force_key.startswith("F") 
        is_moment = force_key.startswith("M")

        if is_force:
            if force_key == "Fy":
                # Fy supports contour mode - keep checkbox enabled
                self.contour.setEnabled(True)

                if self.contour.isChecked():
                    plot_json = build_figure_sfd_contour(ds, force_key, self._nodes, self._members)
                    self.stats_dict = {}
                else:
                    self.stats_dict = {}
                    plot_json = build_figure_sfd(ds, force_key, self._nodes, self._members)
            else:
                # Other forces (Fx, Fz) - no contour support
                self.contour.blockSignals(True)
                self.contour.setChecked(False)
                self.contour.setEnabled(False)
                self.contour.blockSignals(False)

                self.stats_dict = {}
                plot_json = build_figure_sfd(ds, force_key, self._nodes, self._members)

        elif is_moment:
            self.contour.setEnabled(True)

            if self.contour.isChecked():
                plot_json = build_figure_bmd_contour(ds, force_key, self._nodes, self._members)
                self.stats_dict = {}
            else:
                plot_json, self.stats_dict = build_figure_bmd(ds, force_key, self._nodes, self._members)
                
                if self.summary_dialog.isVisible():
                    self.summary_dialog.update_data(self.stats_dict)

        else:
            return  # unsupported force key, just skip

        # Emits the raw JSON string to the web view via QWebChannel
        self.backend.newPlotData.emit(plot_json)

        # Reset the girder isolator to "All" so the new plot shows everything
        self.girder_combo.blockSignals(True)
        self.girder_combo.setCurrentText("All")
        self.girder_combo.blockSignals(False)

        # Reset the scale slider to default (1.0x)
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(10)
        self.scale_slider.blockSignals(False)


# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())