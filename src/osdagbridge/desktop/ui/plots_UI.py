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

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        # ---------- LOADCASE ----------
        top.addWidget(QLabel("Load case:"))
        self.combo = QComboBox()
        self.combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.combo)

        # ---------- FORCE ----------
        top.addWidget(QLabel("Force:"))
        self.force_combo = QComboBox()
        self.force_combo.addItems(list(FORCE_MAP.keys()))
        self.force_combo.setCurrentText("Vy")
        self.force_combo.currentTextChanged.connect(self.update_plot)
        top.addWidget(self.force_combo)

        # ---------- CONTOUR CHECKBOX ----------
        self.contour = QCheckBox("Contour (Moments only)")
        self.contour.stateChanged.connect(self.update_plot)
        top.addWidget(self.contour)
        
        top.addStretch()
        layout.addLayout(top)
        

        # ---------- MAIN BROWSER AREA ----------
        self.web = QWebEngineView()
        
        self.web.setAttribute(Qt.WA_OpaquePaintEvent)
        self.web.setAttribute(Qt.WA_NoSystemBackground)
        self.web.page().setBackgroundColor(Qt.white)

        settings = self.web.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self.web)

        # ---------- INITIALIZATION & QWEBCHANNEL ----------
        self.stats_dict = {}  
        self.summary_dialog = SummaryDialog(self)

        self.current_scale = 0.25     
        self.grid_visible = True       
        self.selected_girder = None    
        self.current_load = "Envelope"     
        self.current_force = "Vy"     

        self.channel = QWebChannel()
        self.backend = BridgeBackend(self)
        
        self.channel.registerObject("backend", self.backend)
        self.web.page().setWebChannel(self.channel)

        # Inject HTML directly into memory
        self.web.setHtml(HTML_TEMPLATE, QUrl("qrc:/"))

    def setup(self, ds_all, loadcases, nodes, members):
        """Populate the widget with bridge analysis results. Call after design() completes."""
        self._ds_all = ds_all
        self._nodes = nodes
        self._members = members

        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(loadcases)
        self.combo.blockSignals(False)

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

    def update_plot(self, force_key=None, loadcase=None, grid_on=None, user_scale=None, selected_girder=None):
        """
        Final Updated Update Plot: Fixes 'int' error, Scaling, and Girder Isolation.
        """
        if self._ds_all is None:
            print("DEBUG: No dataset loaded yet.")
            return

        # ---HANDLE 'INT' FORCE KEY ERROR ---
        if force_key is not None:
            if isinstance(force_key, int):
                self.current_force = self.force_combo.itemText(force_key)
            else:
                self.current_force = str(force_key)

        if not hasattr(self, 'current_force') or not self.current_force:
            self.current_force = "Vy"

        # --- UPDATE PERMANENT STATE ---
        if loadcase is not None:
            self.current_load = str(loadcase)
        elif not hasattr(self, 'current_load'):
            self.current_load = "Envelope"

        if grid_on is not None:
            self.grid_visible = bool(grid_on)

        if user_scale is not None:
            try:
                self.current_scale = float(user_scale)
            except (ValueError, TypeError):
                pass
        
        if selected_girder is not None:
            
            val = str(selected_girder).strip()
            self.current_girder = None if val in ["All", "None", ""] else val

        # --- KEY MAPPING (Internal vs UI names) ---
        f_key = self.current_force
        if "Vy" in f_key: f_key = "Fy"
        if "Vz" in f_key: f_key = "Fz"
        if "Tx" in f_key: f_key = "Mx"

        # --- FIX 4: DYNAMIC LOADCASE SAFETY ---
        available_cases = list(self._ds_all.coords["Loadcase"].values)
        if self.current_load not in available_cases:
            if available_cases:
                self.current_load = available_cases[0]
            else:
                return

        # 3. Data Slicing
        try:
            ds = self._ds_all.sel(Loadcase=self.current_load)
        except Exception as e:
            print(f"Slicing Error: {e}")
            return

        # 4. DISPATCH TO BACKEND (plots_widget.py)
        plot_json = ""
        
        u_scale = getattr(self, "current_scale", 0.25)
        g_on = getattr(self, "grid_visible", True)
        s_girder = getattr(self, "current_girder", None)

        if any(x in f_key for x in ["F", "V"]):
            # SFD Path
            plot_json = build_figure_sfd(
                ds, f_key, self._nodes, self._members, 
                user_scale= self.current_scale, 
                grid_on=g_on, 
                selected_girder=s_girder
            )
        elif any(x in f_key for x in ["M", "T"]):
            # BMD Path
            plot_json, self.stats_dict = build_figure_bmd(
                ds, f_key, self._nodes, self._members, 
                user_scale= self.current_scale, 
                grid_on=g_on,
                selected_girder=s_girder
            )
            
            # Table Refresh
            if self.summary_dialog.isVisible():
                self.summary_dialog.update_data(self.stats_dict)

        # 5. Push to Browser
        if plot_json:
            self.backend.newPlotData.emit(plot_json)

   
# ======================= MAIN
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec()) 