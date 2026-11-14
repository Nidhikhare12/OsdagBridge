"""
Interactive CAD Parameter Manager for OsdagBridge 2D CAD views.
Enables dynamic, double-click editing of fundamental bridge parameters directly
within the 2D CAD canvas and provides read-only feedback for derived parameters.
"""

import re
from PySide6.QtWidgets import QWidget, QLineEdit, QToolTip
from PySide6.QtCore import Qt, QObject, QRectF, QPoint, QPointF, Signal, QEvent
from PySide6.QtGui import QCursor, QFont, QFontMetrics, QPainter, QPen, QColor
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType


class InteractiveCADManager(QObject):
    """
    Manages interactive text labels on a 2D CAD QWidget canvas.
    - Tracks bounding boxes of editable and locked parameters.
    - Handles double-click events to spawn an in-place QLineEdit.
    - Provides tooltip feedback when clicking locked / derived parameters.
    - Validates positive numerical values and emits parameter_edited(key, value).
    """

    # Emitted when a parameter is successfully edited and confirmed: (key, value)
    parameter_edited = Signal(str, float)

    def __init__(self, canvas_widget: QWidget):
        super().__init__(canvas_widget)
        self.canvas = canvas_widget
        self.labels = []
        self._active_editor: QLineEdit | None = None
        self._current_item: dict | None = None

    def clear_labels(self):
        """Clear registered labels at the start of each paint cycle."""
        self.labels.clear()

    def register_label(
        self,
        rect: QRectF | None,
        param_key: str,
        param_name: str,
        current_value: float | int,
        unit: str = "m",
        is_editable: bool = True,
        full_text: str = ""
    ):
        """
        Register a parameter label's bounding box and metadata.
        """
        if rect is None or rect.isEmpty():
            return

        # Give a small padding margin around the text to make targeting easier
        hit_rect = rect.adjusted(-4, -4, 4, 4)
        self.labels.append({
            'rect': hit_rect,
            'draw_rect': rect,
            'key': param_key,
            'name': param_name,
            'value': current_value,
            'unit': unit,
            'editable': is_editable,
            'full_text': full_text,
        })

    def handle_mouse_move(self, event) -> bool:
        """
        Update mouse cursor and show informative tooltips when hovering over editable labels.
        Non-editable labels are treated as standard static text.
        """
        if self._active_editor is not None and self._active_editor.isVisible():
            return False

        pos = event.position() if hasattr(event, 'position') else event.pos()
        for item in self.labels:
            if item.get('editable', False) and item['rect'].contains(pos):
                global_pt = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
                self.canvas.setCursor(Qt.PointingHandCursor)
                QToolTip.showText(global_pt, f"✏️ Double-click to edit {item['name']}", self.canvas)
                return True

        QToolTip.hideText()
        return False

    def handle_mouse_press(self, event) -> bool:
        """
        Commit active editor if clicking outside its area.
        Returns True if handled.
        """
        QToolTip.hideText()
        if self._active_editor is not None and self._active_editor.isVisible():
            pos = event.position() if hasattr(event, 'position') else event.pos()
            if not self._active_editor.geometry().contains(pos.toPoint()):
                self.commit_editor()
                return True
        return False

    def draw_indicators(self, painter: QPainter):
        """
        Draw subtle static visual cues (dashed underline in Osdag green)
        under editable parameters to indicate they can be interacted with.
        """
        if not self.labels:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        pen = QPen(QColor(144, 175, 19, 230), 1.5)  # #90AF13 Osdag green
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([3, 2])
        painter.setPen(pen)

        for item in self.labels:
            if not item.get('editable', False):
                continue

            num_rect = self._compute_number_rect(item)
            if num_rect.isEmpty():
                continue

            # Draw dashed line 1 pixel below the bottom of the number
            y = num_rect.bottom() + 1
            x1 = num_rect.left()
            x2 = num_rect.right()

            painter.drawLine(QPointF(x1, y), QPointF(x2, y))

        painter.restore()

    def handle_double_click(self, event) -> bool:
        """
        Handle double-click event on the canvas.
        Spawns editor only for editable labels. Non-editable labels behave as normal static text.
        """
        pos = event.position() if hasattr(event, 'position') else event.pos()
        for item in self.labels:
            if item.get('editable', False) and item['rect'].contains(pos):
                self.spawn_editor(item)
                return True

        return False

    def _compute_number_rect(self, item: dict) -> QRectF:
        """
        Compute the sub-rectangle corresponding specifically to the numerical value
        within the label's drawn bounding box.
        Keeps the parameter title and unit visible on the canvas while editing.
        """
        draw_rect = item.get('draw_rect')
        if draw_rect is None or draw_rect.isEmpty():
            return draw_rect if draw_rect is not None else QRectF()

        full_text = item.get('full_text', '')
        if not full_text:
            return draw_rect

        font = QFont('Arial', 9, QFont.Normal)
        metrics = QFontMetrics(font)

        lines = full_text.split('\n')
        line_height = metrics.height()
        padding = 2  # matches padding in draw_text_with_background

        for i, line in enumerate(lines):
            match = re.search(r"[-+]?\d*\.?\d+", line)
            if match:
                prefix = line[:match.start()]
                num_str = match.group(0)

                prefix_w = metrics.horizontalAdvance(prefix) if hasattr(metrics, 'horizontalAdvance') else metrics.boundingRect(prefix).width()
                num_w = metrics.horizontalAdvance(num_str) if hasattr(metrics, 'horizontalAdvance') else metrics.boundingRect(num_str).width()

                num_x = draw_rect.x() + padding + prefix_w
                num_y = draw_rect.y() + padding + i * line_height

                return QRectF(num_x, num_y, num_w, line_height)

        return draw_rect

    def spawn_editor(self, item: dict):
        """Create and show a styled QLineEdit overlay directly on the text label."""
        self.close_editor(commit=False)
        self._current_item = item

        editor = QLineEdit(self.canvas)
        self._active_editor = editor

        # Initial text formatted without unnecessary trailing decimals
        val = item['value']
        if isinstance(val, (int, float)):
            if item['unit'] == 'mm':
                text_val = f"{round(val)}"
            else:
                formatted = f"{val:.2f}"
                text_val = formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
        else:
            text_val = str(val) if val is not None else ""

        editor.setText(text_val)

        # Locate the sub-rectangle of only the number portion
        num_rect = self._compute_number_rect(item)

        w = max(int(num_rect.width()) + 14, 48)
        h = max(int(num_rect.height()) + 4, 20)
        x = int(num_rect.center().x() - w // 2)
        y = int(num_rect.center().y() - h // 2)

        # Keep editor within canvas bounds
        x = max(2, min(x, self.canvas.width() - w - 2))
        y = max(2, min(y, self.canvas.height() - h - 2))
        editor.setGeometry(x, y, w, h)

        editor.setAlignment(Qt.AlignCenter)
        editor.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1.5px solid #90AF13;
                border-radius: 2px;
                font-family: Arial;
                font-size: 10px;
                font-weight: bold;
                padding: 0px 2px;
            }
        """)

        editor.returnPressed.connect(self.commit_editor)
        editor.installEventFilter(self)

        editor.show()
        editor.setFocus()
        editor.selectAll()

    def commit_editor(self):
        """Validate input and emit parameter_edited."""
        if self._active_editor is None or self._current_item is None:
            return

        editor = self._active_editor
        item = self._current_item
        text = editor.text().strip()

        try:
            val = float(text)
        except ValueError:
            CustomMessageBox(
                title="Invalid Input",
                text=f"Please enter a valid numeric value for {item['name']}.",
                dialogType=MessageBoxType.Warning
            ).exec()
            self.close_editor(commit=False)
            return

        if val <= 0:
            CustomMessageBox(
                title="Invalid Input",
                text=f"{item['name']} must be greater than zero.",
                dialogType=MessageBoxType.Warning
            ).exec()
            self.close_editor(commit=False)
            return

        key = item['key']
        self.close_editor(commit=False)
        self.parameter_edited.emit(key, val)

    def close_editor(self, commit: bool = False):
        """Close and cleanup the active editor widget."""
        if commit:
            self.commit_editor()
            return
        if self._active_editor is not None:
            self._active_editor.removeEventFilter(self)
            self._active_editor.hide()
            self._active_editor.deleteLater()
            self._active_editor = None
        self._current_item = None
        self.canvas.update()

    def eventFilter(self, watched, event):
        """Intercept focus-out and escape key on the temporary line-edit."""
        if watched == self._active_editor:
            if event.type() == QEvent.FocusOut:
                self.commit_editor()
                return True
            elif event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Escape:
                    self.close_editor(commit=False)
                    return True
        return super().eventFilter(watched, event)

