from PySide6.QtWidgets import QWidget


class UtilizationBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.setStyleSheet("background: #e0e0e0; border-radius: 5px;")

        self._fill = QWidget(self)
        self._fill.setFixedHeight(10)
        self._ratio = 0.0

    def set_ratio(self, ratio: float):
        self._ratio = ratio
        self._update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update()

    def _update(self):
        # clamp to 1.0 so fill never overflows the container
        fill_w = int(min(self._ratio, 1.0) * self.width())
        color = "#28a745" if self._ratio <= 1.0 else "#dc3545"
        self._fill.setFixedWidth(max(0, fill_w))
        self._fill.setStyleSheet(f"background: {color}; border-radius: 5px;")
