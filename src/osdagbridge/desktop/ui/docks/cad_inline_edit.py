"""
Inline (double-click) editing of dimension labels on the 2D CAD canvas.

Task I - Interactive 2D CAD Parameter Editing.

How it works
------------
1. While a CAD widget paints, every label drawn by ``draw_text_with_background``
   is passed to ``_register_label``. Only labels of WRITE-ENABLED parameters are
   remembered, together with the rectangle they occupy on screen.
2. ``mouseDoubleClickEvent`` hit-tests the click against those rectangles. If a
   write-enabled label was clicked, a temporary QLineEdit is placed over it.
3. Pressing Enter or clicking outside the box commits the value. Esc cancels.
   The value (converted to input-dictionary units) is handed to
   ``self.on_param_edited(key, value)``, which BridgeDualCADWidget wires to the
   template page. The template page validates it, writes it to the input
   dictionaries and triggers the CAD redraw.

Locked (read-only) parameters - Overhang, Overall Bridge Width and Bracing
Spacing - are derived values. They are simply not in ``CAD_EDITABLE_LABELS``,
so double-clicking them does nothing.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit

from osdagbridge.core.utils.common import (
    KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_TS_GIRDER_SPACING, KEY_TS_DECK_THICKNESS,
    KEY_DISP_CAD_CARRIAGEWAY_WIDTH, KEY_DISP_CAD_GIRDER_SPACING,
    KEY_DISP_CAD_DECK_THICKNESS, KEY_DISP_CAD_SPAN_LENGTH,
)

# Label drawn on the CAD (central key from common.py) -> input dictionary key.
# The CAD widgets draw exactly these constants, so matching is exact.
# Only these labels can be edited.
CAD_EDITABLE_LABELS = {
    KEY_DISP_CAD_CARRIAGEWAY_WIDTH: KEY_CARRIAGEWAY_WIDTH,
    KEY_DISP_CAD_GIRDER_SPACING:    KEY_TS_GIRDER_SPACING,
    KEY_DISP_CAD_DECK_THICKNESS:    KEY_TS_DECK_THICKNESS,
    KEY_DISP_CAD_SPAN_LENGTH:       KEY_SPAN,
}

# Input dictionary key -> (CAD params name, CAD-mm per input unit, unit label)
# CAD params are stored in mm; the input dictionary uses m except deck thickness.
CAD_PARAM_UNITS = {
    KEY_SPAN:              ("span_length",       1000.0, "m"),
    KEY_CARRIAGEWAY_WIDTH: ("carriageway_width", 1000.0, "m"),
    KEY_TS_GIRDER_SPACING: ("girder_spacing",    1000.0, "m"),
    KEY_TS_DECK_THICKNESS: ("deck_thickness",    1.0,    "mm"),
}


def label_to_key(text: str):
    """Return the input key for a drawn label, or None if it is not editable."""
    name = " ".join(str(text).split("\n")).split(" =")[0].strip()
    name = " ".join(name.split())          # collapse double spaces
    return CAD_EDITABLE_LABELS.get(name)


class _InlineLineEdit(QLineEdit):
    """QLineEdit that reports Esc so the edit can be cancelled."""

    def __init__(self, parent, on_cancel):
        super().__init__(parent)
        self._on_cancel = on_cancel

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self._on_cancel()
            return
        super().keyPressEvent(event)


class CadInlineEditMixin:
    """
    Mixin for QWidget-based CAD canvases. Must come BEFORE QWidget in the
    class bases so its mouseDoubleClickEvent takes priority.

    Attributes set by the owner (BridgeDualCADWidget):
        inline_edit_enabled : bool       - off by default (e.g. Additional Inputs preview)
        on_param_edited     : callable   - on_param_edited(key, value_in_input_units)
        can_edit_callback   : callable   - returns False to block editing (inputs locked)
    """

    def _init_inline_edit(self):
        self.inline_edit_enabled = False
        self.on_param_edited = None
        self.can_edit_callback = None
        self._editable_label_rects = []     # list of (QRectF, key)
        self._inline_editor = None
        self._inline_key = None

    # ── Called while painting ─────────────────────────────────────────────
    def _reset_label_rects(self):
        self._editable_label_rects = []

    def _register_label(self, painter, text, rect: QRectF):
        # Ignore off-screen renders (e.g. report images painted to a QPixmap)
        if not getattr(self, "inline_edit_enabled", False) or painter.device() is not self:
            return
        key = label_to_key(text)
        if key is not None:
            screen_rect = painter.transform().mapRect(QRectF(rect))
            self._editable_label_rects.append((screen_rect, key))

    # ── Qt event ──────────────────────────────────────────────────────────
    def mouseDoubleClickEvent(self, event):
        if getattr(self, "inline_edit_enabled", False):
            pos = event.position() if hasattr(event, "position") else event.pos()
            for rect, key in self._editable_label_rects:
                if rect.adjusted(-3, -3, 3, 3).contains(pos):
                    if self.can_edit_callback is None or self.can_edit_callback():
                        self._start_inline_edit(key, rect)
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        # The canvas does not take keyboard focus, so a click on empty drawing
        # area would not end the edit by itself. Commit explicitly here.
        editor = getattr(self, "_inline_editor", None)
        if editor is not None:
            pos = event.position() if hasattr(event, "position") else event.pos()
            if not editor.geometry().contains(pos.toPoint()):
                self._commit_inline_edit()
        super().mousePressEvent(event)

    # ── Editor lifecycle ──────────────────────────────────────────────────
    def _current_input_value(self, key):
        name, scale, _ = CAD_PARAM_UNITS[key]
        try:
            return float(self.params.get(name)) / scale
        except (TypeError, ValueError):
            return None

    def _start_inline_edit(self, key, rect: QRectF):
        self._close_inline_editor()
        _, _, unit = CAD_PARAM_UNITS[key]

        editor = _InlineLineEdit(self, on_cancel=self._close_inline_editor)
        validator = QDoubleValidator(0.0, 1.0e6, 3, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        value = self._current_input_value(key)
        if value is not None:
            editor.setText(f"{value:g}")
        editor.setPlaceholderText(unit)
        editor.setToolTip(f"Enter value in {unit}. Enter = apply, Esc = cancel")
        editor.setAlignment(Qt.AlignCenter)
        editor.setStyleSheet(
            "QLineEdit { border: 1px solid #90AF13; background: #ffffff;"
            " font: 9pt 'Arial'; padding: 0px 2px; }"
        )
        width = max(int(rect.width()), 90)
        height = max(int(rect.height()), 20)
        x = int(rect.center().x() - width / 2)
        y = int(rect.center().y() - height / 2)
        editor.setGeometry(x, y, width, height)

        self._inline_editor = editor
        self._inline_key = key
        editor.editingFinished.connect(self._commit_inline_edit)   # Enter or focus lost
        editor.show()
        editor.setFocus(Qt.MouseFocusReason)
        editor.selectAll()

    def _commit_inline_edit(self):
        editor, key = self._inline_editor, self._inline_key
        if editor is None:
            return                       # already committed / cancelled
        text = editor.text().strip()
        self._close_inline_editor()
        if not text:
            return                       # empty -> treat as cancel
        try:
            value = float(text)
        except ValueError:
            return
        if callable(self.on_param_edited):
            self.on_param_edited(key, value)

    def _close_inline_editor(self):
        editor = self._inline_editor
        self._inline_editor = None
        self._inline_key = None
        if editor is not None:
            try:
                editor.editingFinished.disconnect(self._commit_inline_edit)
            except (RuntimeError, TypeError):
                pass
            editor.hide()
            editor.deleteLater()
            self.setFocus()
