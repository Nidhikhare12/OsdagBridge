import sys
import os
import json

# Performance Flags
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
    QHeaderView, QPushButton, QDialog, QSlider, QSizePolicy,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtCore import QUrl, Qt, QPoint, QObject, Slot, Signal
from PySide6.QtWebChannel import QWebChannel

from osdagbridge.core.bridge_types.plate_girder.plots_widget import (
    build_figure_sfd,
    build_figure_bmd,
    build_figure_bmd_contour,
    FORCE_MAP,
)

# =========================================================
# HTML TEMPLATE
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
        new QWebChannel(qt.webChannelTransport, function(channel) {
            pyBackend = channel.objects.backend;
            pyBackend.newPlotData.connect(function(jsonString) {
                renderPlot(jsonString);
            });
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


# =========================================================
# SIGNALS — shared between PlotWidget and OutputDock
# =========================================================
class PlotSignals(QObject):
    """
    Central signal hub so PlotWidget and OutputDock can communicate
    without circular imports.
    """
    # OutputDock → PlotWidget
    loadcase_changed  = Signal(str)
    force_changed     = Signal(str)
    max_toggled       = Signal(bool)
    min_toggled       = Signal(bool)
    axis_toggled      = Signal(bool)   # True = show axes, False = hide axes

    # PlotWidget → OutputDock (populate loadcase list after design)
    loadcases_ready   = Signal(list)


# Singleton instance — import this in output_dock.py too
plot_signals = PlotSignals()


# =========================================================
# BACKEND  (QWebChannel bridge)
# =========================================================
class BridgeBackend(QObject):
    newPlotData = Signal(str)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

    @Slot()
    def pageReady(self):
        self.main_app.update_plot()

    @Slot()
    def requestSummaryDialog(self):
        self.main_app.show_summary_dialog()


# =========================================================
# SUMMARY DIALOG
# =========================================================
class SummaryDialog(QDialog):
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
            item_g   = QTableWidgetItem(girder)
            item_max = QTableWidgetItem(f"{vals['max']:.2f}")
            item_min = QTableWidgetItem(f"{vals['min']:.2f}")
            item_max.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_min.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 0, item_g)
            self.table.setItem(row, 1, item_max)
            self.table.setItem(row, 2, item_min)


# =========================================================
# PLOT WIDGET
# =========================================================
class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plate Girder Results")

        self._ds_all   = None
        self._nodes    = {}
        self._members  = {}
        self._num_girders = 0

        layout = QVBoxLayout(self)

        # ── Top control bar ──────────────────────────────────────────────
        top = QHBoxLayout()

        # Load case dropdown (kept for standalone mode;
        # in full app the output dock drives it via signals)
        top.addWidget(QLabel("Load case:"))
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self._on_loadcase_changed)
        top.addWidget(self.combo)

        # Force dropdown
        top.addWidget(QLabel("Force:"))
        self.force_combo = QComboBox()
        self.force_combo.addItems(list(FORCE_MAP.keys()))
        self.force_combo.setCurrentText("Fy")
        self.force_combo.currentTextChanged.connect(self._on_force_changed)
        top.addWidget(self.force_combo)

        # Contour checkbox
        self.contour_cb = QCheckBox("Contour")
        self.contour_cb.setToolTip("Toggle contour colouring on the diagram surface")
        self.contour_cb.stateChanged.connect(self.update_plot)
        top.addWidget(self.contour_cb)

        top.addWidget(QLabel("|"))

        # ── Task-1 controls ──────────────────────────────────────────────

        # 1. Hide/Show Grid
        self.grid_cb = QCheckBox("Grid")
        self.grid_cb.setChecked(True)
        self.grid_cb.setToolTip("Toggle axis grid lines")
        self.grid_cb.stateChanged.connect(self.update_plot)
        top.addWidget(self.grid_cb)

        top.addWidget(QLabel("|"))

        # 2. Hide/Show Axes  (new — driven by output dock via axis_toggled signal)
        self.axis_cb = QCheckBox("Axes")
        self.axis_cb.setChecked(True)
        self.axis_cb.setToolTip("Toggle axis lines and labels")
        self.axis_cb.stateChanged.connect(self.update_plot)
        top.addWidget(self.axis_cb)

        top.addWidget(QLabel("|"))

        # 3. Scale slider
        top.addWidget(QLabel("Scale:"))

        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setMinimum(1)
        self.scale_slider.setMaximum(50)
        self.scale_slider.setValue(10)
        self.scale_slider.setFixedWidth(120)
        self.scale_slider.setToolTip("Adjust diagram scale (0.1× – 5.0×)")
        self.scale_slider.valueChanged.connect(self._on_scale_changed)

        self.scale_label = QLabel("1.0×")
        self.scale_label.setFixedWidth(36)

        scale_layout = QHBoxLayout()
        scale_layout.setSpacing(3)
        scale_layout.addWidget(self.scale_slider)
        scale_layout.addWidget(self.scale_label)
        top.addLayout(scale_layout)

        top.addWidget(QLabel("|"))

        # 4. Isolate girder
        top.addWidget(QLabel("Girder:"))
        self.girder_combo = QComboBox()
        self.girder_combo.addItem("All")
        self.girder_combo.setToolTip("Isolate a single girder")
        self.girder_combo.currentIndexChanged.connect(self.update_plot)
        top.addWidget(self.girder_combo)

        top.addStretch()
        layout.addLayout(top)

        # ── Web view ─────────────────────────────────────────────────────
        self.web = QWebEngineView()
        self.web.setAttribute(Qt.WA_OpaquePaintEvent)
        self.web.setAttribute(Qt.WA_NoSystemBackground)
        self.web.page().setBackgroundColor(Qt.white)
        settings = self.web.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        layout.addWidget(self.web)

        # ── State & dialogs ──────────────────────────────────────────────
        self.stats_dict     = {}
        self.summary_dialog = SummaryDialog(self)

        self.channel = QWebChannel()
        self.backend = BridgeBackend(self)
        self.channel.registerObject("backend", self.backend)
        self.web.page().setWebChannel(self.channel)
        self.web.setHtml(HTML_TEMPLATE, QUrl("qrc:/"))

        # ── Connect to shared signals (Task-2) ───────────────────────────
        plot_signals.loadcase_changed.connect(self._recv_loadcase)
        plot_signals.force_changed.connect(self._recv_force)
        plot_signals.max_toggled.connect(self._recv_max)
        plot_signals.min_toggled.connect(self._recv_min)
        plot_signals.axis_toggled.connect(self._recv_axis)   # new

    # ── Task-1: scale slider ─────────────────────────────────────────────
    def _on_scale_changed(self, value: int):
        factor = value / 10.0
        self.scale_label.setText(f"{factor:.1f}×")
        self.update_plot()

    def _scale_factor(self) -> float:
        return self.scale_slider.value() / 10.0

    # ── Task-1: isolate girder ───────────────────────────────────────────
    def _isolate_girder(self):
        """Return 1-based girder index, or None for All."""
        text = self.girder_combo.currentText()
        if text == "All":
            return None
        try:
            return int(text.replace("G", ""))
        except ValueError:
            return None

    # ── Local control callbacks ──────────────────────────────────────────
    def _on_loadcase_changed(self, text: str):
        # Emit to output dock so it stays in sync
        plot_signals.loadcase_changed.emit(text)
        self.update_plot()

    def _on_force_changed(self, text: str):
        plot_signals.force_changed.emit(text)
        self.update_plot()

    # ── Receive signals FROM output dock (Task-2) ────────────────────────
    @Slot(str)
    def _recv_loadcase(self, text: str):
        """Output dock changed the load case."""
        if self.combo.currentText() != text:
            self.combo.blockSignals(True)
            idx = self.combo.findText(text)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)
            self.combo.blockSignals(False)
            self.update_plot()

    @Slot(str)
    def _recv_force(self, text: str):
        """Output dock changed the force selection."""
        if self.force_combo.currentText() != text:
            self.force_combo.blockSignals(True)
            idx = self.force_combo.findText(text)
            if idx >= 0:
                self.force_combo.setCurrentIndex(idx)
            self.force_combo.blockSignals(False)
            self.update_plot()

    @Slot(bool)
    def _recv_max(self, checked: bool):
        """Output dock toggled Max — just refresh."""
        self.update_plot()

    @Slot(bool)
    def _recv_min(self, checked: bool):
        self.update_plot()

    @Slot(bool)
    def _recv_axis(self, show_axis: bool):
        """
        Output dock toggled Hide Axes.
        show_axis=True  → axes visible  (Hide Axes unchecked)
        show_axis=False → axes hidden   (Hide Axes checked)
        """
        if self.axis_cb.isChecked() != show_axis:
            self.axis_cb.blockSignals(True)
            self.axis_cb.setChecked(show_axis)
            self.axis_cb.blockSignals(False)
            self.update_plot()

    # ── Setup (called after bridge analysis) ────────────────────────────
    def setup(self, ds_all, loadcases, nodes, members):
        self._ds_all   = ds_all
        self._nodes    = nodes
        self._members  = members

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(loadcases)
        self.combo.blockSignals(False)

        # Populate girder isolate combo
        from collections import defaultdict
        import openseespy.opensees as ops
        Z_TOL = 3
        node_z = {}
        for n in ops.getNodeTags():
            z = float(ops.nodeCoord(n)[2])
            node_z[int(n)] = round(z, Z_TOL)
        girder_zs = defaultdict(list)
        for ele in ops.getEleTags():
            n1, n2 = map(int, ops.eleNodes(ele))
            z1, z2 = node_z[n1], node_z[n2]
            if z1 == z2:
                girder_zs[z1].append(ele)
        num_girders = len(girder_zs)
        self._num_girders = num_girders

        self.girder_combo.blockSignals(True)
        self.girder_combo.clear()
        self.girder_combo.addItem("All")
        for g in range(1, num_girders + 1):
            self.girder_combo.addItem(f"G{g}")
        self.girder_combo.blockSignals(False)

        # Tell output dock which loadcases are available
        plot_signals.loadcases_ready.emit(loadcases)

    # ── Summary dialog ───────────────────────────────────────────────────
    def show_summary_dialog(self):
        if not self.stats_dict:
            return
        self.summary_dialog.update_data(self.stats_dict)
        self.summary_dialog.show()
        self.summary_dialog.raise_()
        self.summary_dialog.activateWindow()
        top_left = self.web.mapToGlobal(QPoint(15, 15))
        self.summary_dialog.move(top_left)

    # ── Main render ──────────────────────────────────────────────────────
    def update_plot(self):
        if self._ds_all is None:
            return

        loadcase    = self.combo.currentText()
        force_key   = self.force_combo.currentText()
        show_grid   = self.grid_cb.isChecked()
        show_axis   = self.axis_cb.isChecked()   # new
        scale       = self._scale_factor()
        isolate     = self._isolate_girder()
        ds          = self._ds_all.sel(Loadcase=loadcase)
        

        is_force  = force_key.startswith("F")
        is_moment = force_key.startswith("M")

        if is_force:
            # Contour available only for Fy
            if force_key == "Fy":
                self.contour_cb.setEnabled(True)
            else:
                self.contour_cb.blockSignals(True)
                self.contour_cb.setChecked(False)
                self.contour_cb.setEnabled(False)
                self.contour_cb.blockSignals(False)

            self.stats_dict = {}
            plot_json = build_figure_sfd(
                ds, force_key, self._nodes, self._members,
                show_contour=self.contour_cb.isChecked(),
                scale_factor=scale,
                isolate_girder=isolate,
                show_grid=show_grid,
                show_axis=show_axis,
            )

        elif is_moment:
            self.contour_cb.setEnabled(True)

            if self.contour_cb.isChecked():
                plot_json = build_figure_bmd_contour(
                    ds, force_key, self._nodes, self._members,
                    scale_factor=scale,
                    isolate_girder=isolate,
                    show_grid=show_grid,
                    show_axis=show_axis,
                )
                self.stats_dict = {}
            else:
                plot_json, self.stats_dict = build_figure_bmd(
                    ds, force_key, self._nodes, self._members,
                    scale_factor=scale,
                    isolate_girder=isolate,
                    show_grid=show_grid,
                    show_axis=show_axis,
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