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
    QApplication, QWidget, QVBoxLayout,
    QTableWidget, QTableWidgetItem, 
    QHeaderView, QDialog
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
    FORCE_MAP,
)

# =========================================================
# THE RAM-ONLY FRONTEND
# =========================================================
HTML_TEMPLATE = '''
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
            });
        }
    </script>
</body>
</html>
'''

class BridgeBackend(QObject):
    newPlotData = Signal(str)

    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app

    @Slot()
    def pageReady(self):
        # We start with nothing until the output dock sends signals.
        pass

    @Slot()
    def requestSummaryDialog(self):
        self.main_app.show_summary_dialog()

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

        layout = QVBoxLayout(self)

        # Removed Top Layout logic with Load Case, Force, and Contour Checkbox as per Output Dock refactor

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

    def setup(self, ds_all, loadcases, nodes, members):
        self._ds_all = ds_all
        self._nodes = nodes
        self._members = members

    def show_summary_dialog(self):
        if not self.stats_dict:
            return
        self.summary_dialog.update_data(self.stats_dict)
        self.summary_dialog.show()
        self.summary_dialog.raise_()
        self.summary_dialog.activateWindow()

        top_left_corner = self.web.mapToGlobal(QPoint(15, 15))
        self.summary_dialog.move(top_left_corner)

    def update_plot_from_dock(self, loadcase, force_key, is_contour, show_max, show_min):
        if self._ds_all is None:
            return

        try:
            ds = self._ds_all.sel(Loadcase=loadcase)
        except Exception:
            return # safe fallback

        is_force = force_key[0] in ('F', 'V', 'D')
        is_moment = force_key[0] in ('M', 'T')

        if is_force:
            self.stats_dict = {}
            if is_contour:
                # Our implementation uses contour if it's force, we didn't write a separate function but
                # we integrated surface coloring inside build_figure_sfd directly. It handles it.
                pass
            plot_json = build_figure_sfd(ds, force_key, self._nodes, self._members, show_max, show_min)

        elif is_moment:
            if is_contour:
                plot_json, self.stats_dict = build_figure_bmd_contour(ds, force_key, self._nodes, self._members, show_max, show_min)
            else:
                plot_json, self.stats_dict = build_figure_bmd(ds, force_key, self._nodes, self._members, show_max, show_min)
                
            if self.summary_dialog.isVisible():
                self.summary_dialog.update_data(self.stats_dict)

        else:
            return

        self.backend.newPlotData.emit(plot_json)

# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())
