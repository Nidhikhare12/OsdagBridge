from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QGraphicsView, QGraphicsScene
)
from PySide6.QtGui import QPen, QBrush, QPainter
from PySide6.QtCore import Qt


# ================= CANVAS =================
class LoadCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(250)
        self.setAlignment(Qt.AlignCenter)

    def clear_canvas(self):
        self.scene.clear()

    def draw_bridge(self):
        self.clear_canvas()

        deck_y = 60
        deck_width = 500

        self.scene.addRect(
            50, deck_y, deck_width, 20,
            QPen(Qt.black), QBrush(Qt.lightGray)
        )

        for x in [100, 200, 300, 400, 500]:
            self.scene.addRect(
                x, deck_y + 20, 12, 60,
                QPen(Qt.black), QBrush(Qt.darkGray)
            )

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def draw_point_load(self, x=250):
        self.draw_bridge()

        x = 50 + x
        self.scene.addLine(x, 30, x, 60, QPen(Qt.red, 2))
        self.scene.addLine(x, 60, x - 5, 50, QPen(Qt.red, 2))
        self.scene.addLine(x, 60, x + 5, 50, QPen(Qt.red, 2))

    def draw_line_load(self, x1, x2):
        self.draw_bridge()

        x1 = 50 + x1
        x2 = 50 + x2
        y = 30

        self.scene.addLine(x1, y, x2, y, QPen(Qt.red, 2))

        for x in range(int(x1), int(x2), 30):
            self.scene.addLine(x, y, x, y + 20, QPen(Qt.red, 2))
            self.scene.addLine(x, y + 20, x - 5, y + 15, QPen(Qt.red, 2))
            self.scene.addLine(x, y + 20, x + 5, y + 15, QPen(Qt.red, 2))

    def draw_area_load(self, x1, x2):
        self.draw_bridge()

        x1 = 50 + x1
        x2 = 50 + x2

        width = x2 - x1
        y = 20
        height = 20

        self.scene.addRect(
            x1, y, width, height,
            QPen(Qt.red, 2),
            QBrush(Qt.red, Qt.Dense4Pattern)
        )

        for x in range(int(x1), int(x2), 30):
            self.scene.addLine(x, y + height, x, y + height + 20, QPen(Qt.red, 2))
            self.scene.addLine(x, y + height + 20, x - 5, y + height + 15, QPen(Qt.red, 2))
            self.scene.addLine(x, y + height + 20, x + 5, y + height + 15, QPen(Qt.red, 2))


# ================= TAB =================
class CustomLoadTab(QWidget):
    def __init__(self, owner=None):
        super().__init__(owner)

        self.owner = owner

        main_layout = QVBoxLayout(self)

        # 🔥 CANVAS
        self.canvas = LoadCanvas()
        main_layout.addWidget(self.canvas)

        self.canvas.draw_point_load(250)

        # ================= UI CONTROLS =================
        form_layout = QVBoxLayout()

        # Load Type
        type_row = QHBoxLayout()
        type_label = QLabel("Load Type:")
        self.load_type_combo = QComboBox()
        self.load_type_combo.addItems(["Point", "Line", "Area"])

        type_row.addWidget(type_label)
        type_row.addWidget(self.load_type_combo)
        form_layout.addLayout(type_row)

        # Point Input
        point_row = QHBoxLayout()
        point_label = QLabel("Point Distance:")
        self.point_input = QLineEdit()

        point_row.addWidget(point_label)
        point_row.addWidget(self.point_input)
        form_layout.addLayout(point_row)

        # Line Inputs
        line_row = QHBoxLayout()
        self.start_input = QLineEdit()
        self.end_input = QLineEdit()

        line_row.addWidget(QLabel("Start:"))
        line_row.addWidget(self.start_input)
        line_row.addWidget(QLabel("End:"))
        line_row.addWidget(self.end_input)

        form_layout.addLayout(line_row)

        main_layout.addLayout(form_layout)

        # ================= CONNECTIONS =================
        self.load_type_combo.currentTextChanged.connect(self._on_type_change)
        self.point_input.textChanged.connect(self._update_point)
        self.start_input.textChanged.connect(self._update_line)
        self.end_input.textChanged.connect(self._update_line)

    # 🔥 SWITCH
    def _on_type_change(self, text):
        if text == "Point":
            self.canvas.draw_point_load(250)
        elif text == "Line":
            self.canvas.draw_line_load(100, 400)
        else:
            self.canvas.draw_area_load(100, 400)

    # 🔥 POINT UPDATE
    def _update_point(self, text):
        try:
            x = float(text)
        except:
            x = 0

        if self.load_type_combo.currentText() == "Point":
            self.canvas.draw_point_load(x)

    # 🔥 LINE / AREA UPDATE
    def _update_line(self, text):
        try:
            x1 = float(self.start_input.text())
        except:
            x1 = 0

        try:
            x2 = float(self.end_input.text())
        except:
            x2 = 0

        if self.load_type_combo.currentText() == "Line":
            self.canvas.draw_line_load(x1, x2)
        else:
            self.canvas.draw_area_load(x1, x2)