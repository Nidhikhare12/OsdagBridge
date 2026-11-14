"""
Interactive CAD Parameter Manager for OsdagBridge 2D CAD views.
Enables dynamic, double-click editing of fundamental bridge parameters directly
within the 2D CAD canvas and provides read-only feedback for derived parameters.
"""

from PySide6.QtWidgets import QWidget, QLineEdit
from PySide6.QtCore import Qt, QObject, QRectF, QPoint, Signal, QEvent
from PySide6.QtGui import QCursor
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
        is_editable: bool = True
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
        })

    def handle_mouse_move(self, event) -> bool:
        """
        Update the mouse cursor when hovering over interactive labels.
        Returns True if hovering over an interactive CAD label.
        """
        if self._active_editor is not None and self._active_editor.isVisible():
            return False

        pos = event.position() if hasattr(event, 'position') else event.pos()
        for item in self.labels:
            if item['rect'].contains(pos):
                if item['editable']:
                    self.canvas.setCursor(Qt.PointingHandCursor)
                else:
                    self.canvas.setCursor(Qt.ForbiddenCursor)
                return True

        return False

    def handle_mouse_press(self, event) -> bool:
        """
        Commit active editor if clicking outside its area.
        Returns True if handled.
        """
        if self._active_editor is not None and self._active_editor.isVisible():
            pos = event.position() if hasattr(event, 'position') else event.pos()
            if not self._active_editor.geometry().contains(pos.toPoint()):
                self.commit_editor()
                return True
        return False

    def handle_double_click(self, event) -> bool:
        """
        Handle double-click event on the canvas.
        Returns True if a registered label was hit.
        """
        pos = event.position() if hasattr(event, 'position') else event.pos()
        for item in self.labels:
            if item['rect'].contains(pos):
                if not item['editable']:
                    # Derived / Read-only parameter
                    CustomMessageBox(
                        title="Read-Only Parameter",
                        text=(
                            f"'{item['name']}' is a derived parameter (Read-Only).\n\n"
                            f"It is determined automatically to prevent mathematical conflicts."
                        ),
                        dialogType=MessageBoxType.Information
                    ).exec()
                    return True
                else:
                    # Editable parameter: spawn in-place editor
                    self.spawn_editor(item)
                    return True

        return False

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

        # Center the editor over the drawn text rectangle
        draw_rect = item['draw_rect'].toRect()
        w = max(draw_rect.width() + 16, 75)
        h = max(draw_rect.height() + 8, 24)
        x = draw_rect.center().x() - w // 2
        y = draw_rect.center().y() - h // 2

        # Keep editor within canvas bounds
        x = max(2, min(x, self.canvas.width() - w - 2))
        y = max(2, min(y, self.canvas.height() - h - 2))
        editor.setGeometry(x, y, w, h)

        editor.setAlignment(Qt.AlignCenter)
        editor.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #000000;
                border: 2px solid #90AF13;
                border-radius: 3px;
                font-family: Arial;
                font-size: 11px;
                font-weight: bold;
                padding: 1px 2px;
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

