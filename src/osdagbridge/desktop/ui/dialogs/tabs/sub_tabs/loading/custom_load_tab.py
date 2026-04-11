from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QGraphicsView, QGraphicsScene
)
from PySide6.QtGui import QPen, QBrush, QPainter
from PySide6.QtCore import Qt


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

    def draw_bridge(self):
        self.clear_canvas()

        # Deck
        self.scene.addRect(
            self.offset, self.deck_y, self.deck_width, 20,
            QPen(Qt.black), QBrush(Qt.lightGray)
        )

        # Girders (dynamic instead of hardcoded list)
        spacing = self.deck_width // 5
        for i in range(1, 6):
            x = self.offset + i * spacing
            self.scene.addRect(
                x, self.deck_y + 20, 12, 60,
                QPen(Qt.black), QBrush(Qt.darkGray)
            )

    def draw_point_load(self, x=250):
        self.draw_bridge()

        x_canvas = self.offset + x

        self._draw_arrow(x_canvas, 30, 60)

        
        self.scene.addText(f"x = {x:.1f}").setPos(x_canvas - 20, 65)
        self.scene.addText("P = 10 kN").setPos(x_canvas - 30, 10)

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def draw_line_load(self, x1, x2):
        self.draw_bridge()

        x1_canvas = self.offset + x1
        x2_canvas = self.offset + x2
        y = 30

        self.scene.addLine(x1_canvas, y, x2_canvas, y, QPen(Qt.red, 2))

        for x in range(int(x1_canvas), int(x2_canvas), 30):
            self._draw_arrow(x, y, y + 20)

        
        self.scene.addText(f"x1 = {x1:.1f}").setPos(x1_canvas, 65)
        self.scene.addText(f"x2 = {x2:.1f}").setPos(x2_canvas - 40, 65)
        self.scene.addText("w = 5 kN/m").setPos((x1_canvas + x2_canvas) / 2 - 30, 10)

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def draw_area_load(self, x1, x2):
        self.draw_bridge()

        x1_canvas = self.offset + x1
        x2_canvas = self.offset + x2

        width = x2_canvas - x1_canvas
        y = 20
        height = 20

        self.scene.addRect(
            x1_canvas, y, width, height,
            QPen(Qt.red, 2),
            QBrush(Qt.red, Qt.Dense4Pattern)
        )

        for x in range(int(x1_canvas), int(x2_canvas), 30):
            self._draw_arrow(x, y + height, y + height + 20)

       
        self.scene.addText(f"x1 = {x1:.1f}").setPos(x1_canvas, 65)
        self.scene.addText(f"x2 = {x2:.1f}").setPos(x2_canvas - 40, 65)
        self.scene.addText("q = 8 kN/m²").setPos((x1_canvas + x2_canvas) / 2 - 40, 0)

        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)


class CustomLoadTab(QWidget):
    def __init__(self, owner=None):
        super().__init__(owner)

        self.owner = owner

        main_layout = QVBoxLayout(self)

        
        self.canvas = LoadCanvas()
        main_layout.addWidget(self.canvas)

        self.canvas.draw_point_load(250)

        form_layout = QVBoxLayout()

        # Load Type
        type_row = QHBoxLayout()
        self.load_type_combo = QComboBox()
        self.load_type_combo.addItems(["Point", "Line", "Area"])

        type_row.addWidget(QLabel("Load Type:"))
        type_row.addWidget(self.load_type_combo)
        form_layout.addLayout(type_row)

        # Point Input
        self.point_row = QHBoxLayout()
        self.point_input = QLineEdit()
        self.point_input.setPlaceholderText("Enter x (0–500)")

        self.point_row.addWidget(QLabel("Point Distance:"))
        self.point_row.addWidget(self.point_input)
        form_layout.addLayout(self.point_row)

        # Line Inputs
        self.line_row = QHBoxLayout()
        self.start_input = QLineEdit()
        self.end_input = QLineEdit()

        self.start_input.setPlaceholderText("Start x1")
        self.end_input.setPlaceholderText("End x2")

        self.line_row.addWidget(QLabel("Start:"))
        self.line_row.addWidget(self.start_input)
        self.line_row.addWidget(QLabel("End:"))
        self.line_row.addWidget(self.end_input)

        form_layout.addLayout(self.line_row)

        main_layout.addLayout(form_layout)

       
        self.load_type_combo.currentTextChanged.connect(self._on_type_change)
        self.point_input.textChanged.connect(self._update_point)
        self.start_input.textChanged.connect(self._update_line)
        self.end_input.textChanged.connect(self._update_line)

        self._on_type_change("Point")

  
    def _clamp(self, value):
        return max(0, min(500, value))

    def _parse_input(self, text):
        try:
            return self._clamp(float(text))
        except:
            return 0

    
    def _on_type_change(self, text):
        is_point = text == "Point"

        # Show/hide inputs
        for i in range(self.point_row.count()):
            self.point_row.itemAt(i).widget().setVisible(is_point)

        for i in range(self.line_row.count()):
            self.line_row.itemAt(i).widget().setVisible(not is_point)

        # Default rendering
        if text == "Point":
            self.canvas.draw_point_load(250)
        elif text == "Line":
            self.canvas.draw_line_load(100, 400)
        else:
            self.canvas.draw_area_load(100, 400)

    def _update_point(self, text):
        if self.load_type_combo.currentText() != "Point":
            return

        x = self._parse_input(text)
        self.canvas.draw_point_load(x)

    def _update_line(self, text):
        if self.load_type_combo.currentText() == "Point":
            return

        x1 = self._parse_input(self.start_input.text())
        x2 = self._parse_input(self.end_input.text())

        if x2 < x1:
            x1, x2 = x2, x1  # swap

        if self.load_type_combo.currentText() == "Line":
            self.canvas.draw_line_load(x1, x2)
        else:
            self.canvas.draw_area_load(x1, x2)