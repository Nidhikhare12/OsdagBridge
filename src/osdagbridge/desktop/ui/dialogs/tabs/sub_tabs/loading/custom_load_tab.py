from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QGraphicsView, QGraphicsScene, QPushButton, QTableWidget,
    QTableWidgetItem
)
from PySide6.QtGui import QPen, QBrush, QPainter
from PySide6.QtCore import Qt


# =========================
# CANVAS
# =========================
class LoadCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(250)
        self.setAlignment(Qt.AlignCenter)

        self.offset = 50
        self.deck_width = 500
        self.deck_y = 60

    def clear_canvas(self):
        self.scene.clear()

    def _draw_arrow(self, x, y_top, y_bottom):
        self.scene.addLine(x, y_top, x, y_bottom, QPen(Qt.red, 2))
        self.scene.addLine(x, y_bottom, x - 5, y_bottom - 10, QPen(Qt.red, 2))
        self.scene.addLine(x, y_bottom, x + 5, y_bottom - 10, QPen(Qt.red, 2))

    # -------- PLAN --------
    def draw_point_load(self, x=250, magnitude=10):
        self.clear_canvas()
        self.scene.addText("Plan View").setPos(220, 0)

        self.scene.addRect(self.offset, self.deck_y, self.deck_width, 20,
                           QPen(Qt.black), QBrush(Qt.lightGray))

        x_canvas = self.offset + x
        self._draw_arrow(x_canvas, 30, 60)

        self.scene.addText(f"x = {int(x)}").setPos(x_canvas - 20, 65)
        self.scene.addText(f"P = {int(magnitude)} kN").setPos(x_canvas - 30, 10)

    # -------- ELEVATION --------
    def draw_point_elevation(self, x, magnitude):
        self.clear_canvas()
        self.scene.addText("Elevation View").setPos(200, 0)

        self.scene.addLine(50, 100, 550, 100, QPen(Qt.black, 3))

        x_canvas = 50 + x
        self._draw_arrow(x_canvas, 50, 100)

        self.scene.addText(f"P = {int(magnitude)} kN").setPos(x_canvas - 30, 20)

    # -------- 3D --------
    def draw_point_3d(self, x, magnitude):
        self.clear_canvas()
        self.scene.addText("3D View").setPos(220, 0)

        self.scene.addLine(50, 100, 550, 100, QPen(Qt.black, 3))
        self.scene.addLine(70, 80, 570, 80, QPen(Qt.gray, 2))

        for i in range(5):
            self.scene.addLine(50 + i * 100, 100, 70 + i * 100, 80, QPen(Qt.gray))

        x_canvas = 50 + x
        self._draw_arrow(x_canvas, 40, 100)

        self.scene.addText(f"P = {int(magnitude)} kN").setPos(x_canvas - 30, 10)


# =========================
# MAIN TAB
# =========================
class CustomLoadTab(QWidget):
    def __init__(self, owner=None):
        super().__init__(owner)

        main_layout = QVBoxLayout(self)

        # ✅ NEW CANVAS WRAPPER (FIXED)
        canvas_layout = QVBoxLayout()

        # Dropdown inside canvas area
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Plan", "Elevation", "3D"])
        self.view_combo.setMaximumWidth(150)

        canvas_layout.addWidget(self.view_combo)

        # Canvas
        self.canvas = LoadCanvas()
        canvas_layout.addWidget(self.canvas)

        # Add to main layout
        main_layout.addLayout(canvas_layout)

        # FORM
        form_layout = QVBoxLayout()

        self.load_type_combo = QComboBox()
        self.load_type_combo.addItems(["Point", "Line", "Area"])

        self.point_input = QLineEdit()
        self.start_input = QLineEdit()
        self.end_input = QLineEdit()
        self.magnitude_input = QLineEdit("10")

        form_layout.addWidget(QLabel("Load Type"))
        form_layout.addWidget(self.load_type_combo)
        form_layout.addWidget(self.point_input)
        form_layout.addWidget(self.start_input)
        form_layout.addWidget(self.end_input)
        form_layout.addWidget(self.magnitude_input)

        self.save_btn = QPushButton("Save Load")
        form_layout.addWidget(self.save_btn)

        main_layout.addLayout(form_layout)

        # TABLE
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Start", "End", "Magnitude"])
        main_layout.addWidget(self.table)

        # BUTTONS
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        main_layout.addLayout(btn_layout)

        # SIGNALS
        self.view_combo.currentTextChanged.connect(self._update_canvas)
        self.load_type_combo.currentTextChanged.connect(self._update_canvas)

        self.point_input.textChanged.connect(self._update_canvas)
        self.start_input.textChanged.connect(self._update_canvas)
        self.end_input.textChanged.connect(self._update_canvas)
        self.magnitude_input.textChanged.connect(self._update_canvas)

        self.save_btn.clicked.connect(self.save_load)
        self.delete_btn.clicked.connect(self.delete_load)

        self._update_canvas()

    def save_load(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(self.load_type_combo.currentText()))
        self.table.setItem(row, 1, QTableWidgetItem(self.point_input.text()))
        self.table.setItem(row, 2, QTableWidgetItem(self.end_input.text()))
        self.table.setItem(row, 3, QTableWidgetItem(self.magnitude_input.text()))

    def delete_load(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _parse_input(self, text):
        try:
            return float(text)
        except:
            return 0

    def _get_magnitude(self):
        try:
            return float(self.magnitude_input.text())
        except:
            return 10

    def _update_canvas(self):
        print("VIEW =", self.view_combo.currentText())

        mag = self._get_magnitude()
        view = self.view_combo.currentText()
        x = self._parse_input(self.point_input.text())

        if view == "Plan":
            self.canvas.draw_point_load(x, mag)
        elif view == "Elevation":
            self.canvas.draw_point_elevation(x, mag)
        else:
            self.canvas.draw_point_3d(x, mag)