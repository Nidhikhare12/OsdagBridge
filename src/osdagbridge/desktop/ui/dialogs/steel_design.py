from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt

from osdagbridge.desktop.ui.dialogs.tabs.steel_design_details import SteelDesignDetailsTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_analysis import SteelDesignAnalysisTab
from osdagbridge.desktop.ui.dialogs.tabs.steel_design_check import SteelDesignCheckTab


class SteelDesign(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Steel Design")
        self.setWindowFlags(Qt.Window)
        self.setWindowModality(Qt.NonModal)

        self.resize(1024, 720)
        self.setMinimumSize(900, 520)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Tabs
        self.details_tab = SteelDesignDetailsTab(self)
        self.tabs.addTab(self.details_tab, "Details")

        self.analysis_tab = SteelDesignAnalysisTab(self)
        self.tabs.addTab(self.analysis_tab, "Analysis Results")

        self.check_tab = SteelDesignCheckTab(self)
        self.tabs.addTab(self.check_tab, "Design Check")

        layout.addWidget(self.tabs)

        # Call equation display
        self.check_tab.update_design_check(load=10, length=5)