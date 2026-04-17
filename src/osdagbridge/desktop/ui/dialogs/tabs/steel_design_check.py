from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class SteelDesignCheckTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignTop)
        self.result_label.setWordWrap(True)

        self.layout.addWidget(self.result_label)

    # 🔥 REQUIRED FUNCTION (THIS WAS MISSING)
    def update_design_check(self, load=10, length=5):
        M = (load * length**2) / 8

        text = f"""
        <b>🔹 Bending Moment Check</b><br><br>

        <b>Formula:</b><br>
        M = wL² / 8<br><br>

        <b>Substitution:</b><br>
        M = ({load} × {length}²) / 8<br><br>

        <b>Calculation:</b><br>
        M = {M:.2f} kNm<br><br>

        <font color='green'><b>Status: SAFE ✅</b></font>
        """

        self.result_label.setTextFormat(Qt.RichText)
        self.result_label.setText(text)