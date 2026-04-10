from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt


_STYLES = {
    "pass":    ("PASS",  "#1a7a4a", "#d4edda"),
    "fail":    ("FAIL",  "#8b0000", "#f8d7da"),
    "neutral": ("",      "#444444", "#eeeeee"),
}


class StatusBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 22)
        self.setAlignment(Qt.AlignCenter)
        self.set_neutral()

    def _apply(self, state):
        text, fg, bg = _STYLES[state]
        self.setText(text)
        self.setStyleSheet(
            f"color: {fg}; background: {bg};"
            "font-weight: bold; font-size: 10px;"
            "border-radius: 6px;"
        )

    def set_pass(self):    self._apply("pass")
    def set_fail(self):    self._apply("fail")
    def set_neutral(self): self._apply("neutral")
