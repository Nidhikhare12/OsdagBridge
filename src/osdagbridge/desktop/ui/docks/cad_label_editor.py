"""
Interactive (double-click) editing of 2D CAD dimension labels.

Both 2D CAD widgets (cross-section and top view) paint their dimension text
through ``draw_text_with_background``.  While a label that represents a bridge
parameter is being painted, the widget wraps the call in
``with self.cad_label(KEY_...):`` and the mixin records the label's on-screen
rectangle together with the parameter key from ``common.py``.

On double-click:
  * an editable label is replaced in-place by a small line edit pre-filled
    with the current value. Enter / clicking elsewhere commits, Esc cancels.
    A committed value is emitted through the widget's
    ``parameter_edit_requested(key, value)`` signal; the owner validates it,
    writes it to the input dictionary and triggers the redraw.
  * a locked (derived) label is never opened for editing; a tooltip explains
    why it is read-only.

The mixin owns no data - the widget's own ``params`` dict (mm based) is the
CAD state that pre-fills the editor.
"""

from contextlib import contextmanager

from PySide6.QtCore import Qt, QRectF, QPoint, QRegularExpression
from PySide6.QtGui import QColor, QPen, QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit, QToolTip

from osdagbridge.core.utils.common import (
    KEY_CARRIAGEWAY_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_THICKNESS,
    KEY_SPAN,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
    KEY_MP_CB_SPACING,
)


# ── Parameter catalogue ────────────────────────────────────────────────────
# key -> (display name, unit shown to the user, CAD params entry, mm -> unit factor)
# The CAD widgets store geometry in mm; the input dictionary stores widths and
# span in m and the deck thickness in mm, so the factor converts CAD -> input.
CAD_EDITABLE_PARAMETERS = {
    KEY_CARRIAGEWAY_WIDTH: ("Carriageway Width", "m",  "carriageway_width", 1e-3),
    KEY_TS_GIRDER_SPACING: ("Girder Spacing",    "m",  "girder_spacing",    1e-3),
    KEY_TS_DECK_THICKNESS: ("Deck Thickness",    "mm", "deck_thickness",    1.0),
    KEY_SPAN:              ("Span Length",       "m",  "span_length",       1e-3),
}

# Derived values: shown in the CAD but intentionally not editable there.
CAD_LOCKED_PARAMETERS = {
    KEY_TS_DECK_OVERHANG: (
        "Overhang",
        "Overhang is derived from the overall width, number of girders and girder spacing.\n"
        "Edit Girder Spacing instead.",
    ),
    KEY_TS_OVERALL_WIDTH: (
        "Overall Bridge Width",
        "Overall Bridge Width is derived from the carriageway, crash barrier,\n"
        "median and footpath widths. Edit Carriageway Width instead.",
    ),
    KEY_MP_CB_SPACING: (
        "Bracing Spacing",
        "Bracing Spacing is derived from the span and the number of cross bracings.\n"
        "Change it from Additional Inputs > Member Properties.",
    ),
}

_HIGHLIGHT_EDITABLE = QColor(144, 175, 19)    # Osdag green
_HIGHLIGHT_LOCKED = QColor(160, 160, 160)


class _InlineValueEditor(QLineEdit):
    """Line edit that reports Esc as a cancel instead of losing the value."""

    def __init__(self, parent, on_commit, on_cancel):
        super().__init__(parent)
        self._on_commit = on_commit
        self._on_cancel = on_cancel
        self._finished = False
        self.editingFinished.connect(self._commit)

    def _commit(self):
        if self._finished:
            return
        self._finished = True
        self._on_commit(self.text())

    def cancel(self):
        if self._finished:
            return
        self._finished = True
        self._on_cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
            return
        super().keyPressEvent(event)


class EditableCADLabelsMixin:
    """
    Mixin for QWidget based 2D CAD canvases.

    Host class requirements:
      * a ``params`` dict (mm based CAD state)
      * a Qt Signal ``parameter_edit_requested = Signal(str, float)``
      * call ``self._begin_label_frame()`` at the start of ``paintEvent``
      * call ``self._register_label_rect(rect)`` from ``draw_text_with_background``
      * call ``self._paint_label_affordances(painter)`` at the end of painting
      * call ``self._update_label_hover(pos)`` from ``mouseMoveEvent``
    """

    def _init_label_editing(self):
        self.label_editing_enabled = False     # opt-in (main template CAD only)
        self._label_edit_guard = None          # callable -> (allowed: bool, reason: str)
        self._label_regions = []               # [(QRectF, key)] for the current frame
        self._active_label_key = None
        self._hovered_label_key = None
        self._hovered_label_rect = None
        self._label_editor = None
        self._editing_key = None

    # ── configuration ────────────────────────────────────────────────────
    def set_label_editing_enabled(self, enabled: bool, guard=None):
        """Enable double-click editing. ``guard`` may veto editing (e.g. inputs locked)."""
        self.label_editing_enabled = bool(enabled)
        self._label_edit_guard = guard
        if not enabled:
            self._close_label_editor()

    # ── painting hooks ───────────────────────────────────────────────────
    @contextmanager
    def cad_label(self, key):
        """Tag every label painted inside this block with a parameter key."""
        previous = self._active_label_key
        self._active_label_key = key
        try:
            yield
        finally:
            self._active_label_key = previous

    def _begin_label_frame(self):
        self._label_regions = []

    def _register_label_rect(self, rect: QRectF):
        if self._active_label_key is not None:
            self._label_regions.append((QRectF(rect), self._active_label_key))

    def _paint_label_affordances(self, painter):
        """Outline the hovered parameter label so it reads as clickable."""
        if not self.label_editing_enabled or self._label_editor is not None:
            return
        key = self._hovered_label_key
        if key is None:
            return
        color = _HIGHLIGHT_EDITABLE if key in CAD_EDITABLE_PARAMETERS else _HIGHLIGHT_LOCKED
        painter.save()
        pen = QPen(color, 1.2)
        if key not in CAD_EDITABLE_PARAMETERS:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        for rect, region_key in self._label_regions:
            if region_key == key:
                painter.drawRoundedRect(rect.adjusted(-2, -1, 2, 1), 3, 3)
        painter.restore()

    # ── hit testing / hover ──────────────────────────────────────────────
    def _label_at(self, pos):
        # Last painted wins: labels painted later sit on top of earlier ones.
        for rect, key in reversed(self._label_regions):
            if rect.adjusted(-2, -2, 2, 2).contains(pos):
                return rect, key
        return None, None

    def _update_label_hover(self, pos):
        if not self.label_editing_enabled:
            return
        rect, key = self._label_at(pos)
        if key != self._hovered_label_key:
            self._hovered_label_key = key
            self._hovered_label_rect = rect
            if key is None:
                self.unsetCursor()
                self.setToolTip("")
            elif key in CAD_EDITABLE_PARAMETERS:
                self.setCursor(Qt.PointingHandCursor)
                name = CAD_EDITABLE_PARAMETERS[key][0]
                self.setToolTip(f"Double-click to edit {name}")
            else:
                self.setCursor(Qt.ForbiddenCursor)
                self.setToolTip(f"{CAD_LOCKED_PARAMETERS[key][0]} is a derived value (read-only)")
            self.update()

    def leaveEvent(self, event):
        if self._hovered_label_key is not None:
            self._hovered_label_key = None
            self.unsetCursor()
            self.update()
        super().leaveEvent(event)

    # ── double click → editor ────────────────────────────────────────────
    def mouseDoubleClickEvent(self, event):
        if not self.label_editing_enabled:
            return super().mouseDoubleClickEvent(event)

        pos = event.position() if hasattr(event, "position") else event.pos()
        rect, key = self._label_at(pos)
        if key is None:
            return super().mouseDoubleClickEvent(event)

        global_pos = self.mapToGlobal(QPoint(int(pos.x()), int(pos.y())))

        if key in CAD_LOCKED_PARAMETERS:
            QToolTip.showText(global_pos, "🔒 " + CAD_LOCKED_PARAMETERS[key][1], self)
            event.accept()
            return

        if self._label_edit_guard is not None:
            allowed, reason = self._label_edit_guard()
            if not allowed:
                QToolTip.showText(global_pos, reason, self)
                event.accept()
                return

        self._open_label_editor(key, rect)
        event.accept()

    def current_parameter_value(self, key):
        """Current CAD value of ``key`` converted to input-dictionary units."""
        _, _, param_name, factor = CAD_EDITABLE_PARAMETERS[key]
        value = self.params.get(param_name)
        if value is None:
            return None
        return float(value) * factor

    @staticmethod
    def _format_value(value, unit):
        if value is None:
            return ""
        return f"{value:.0f}" if unit == "mm" else f"{value:.2f}"

    def _open_label_editor(self, key, rect: QRectF):
        self._close_label_editor()
        name, unit, _, _ = CAD_EDITABLE_PARAMETERS[key]

        editor = _InlineValueEditor(
            self,
            on_commit=lambda text, k=key: self._commit_label_editor(k, text),
            on_cancel=self._close_label_editor,
        )
        # Digits with an optional decimal point only. Every partial entry is
        # "Acceptable" so editingFinished always fires on Enter / focus-out;
        # range checks happen in the owner with the project validators.
        editor.setValidator(QRegularExpressionValidator(QRegularExpression(r"^\d{0,6}(\.\d{0,3})?$"), editor))
        editor.setText(self._format_value(self.current_parameter_value(key), unit))
        editor.setPlaceholderText(unit)
        editor.setAlignment(Qt.AlignCenter)
        editor.setToolTip(f"{name} ({unit}) - Enter to apply, Esc to cancel")
        editor.setStyleSheet(
            "QLineEdit { border: 1.5px solid #90AF13; border-radius: 3px;"
            " background: #ffffff; color: #000000; padding: 0px 3px; font: 9pt 'Arial'; }"
        )

        width = max(90, int(rect.width()) + 16)
        height = max(22, int(rect.height()) + 6)
        x = int(rect.center().x() - width / 2)
        y = int(rect.center().y() - height / 2)
        x = max(0, min(x, self.width() - width))
        y = max(0, min(y, self.height() - height))
        editor.setGeometry(x, y, width, height)

        self._label_editor = editor
        self._editing_key = key
        self._hovered_label_key = None
        self.unsetCursor()
        editor.show()
        editor.setFocus(Qt.MouseFocusReason)
        editor.selectAll()
        self.update()

    def _commit_label_editor(self, key, text):
        self._close_label_editor()
        text = (text or "").strip()
        if not text:
            return                          # empty → treated as cancel
        try:
            value = float(text)
        except ValueError:
            return
        current = self.current_parameter_value(key)
        if current is not None and abs(current - value) < 1e-9:
            return                          # unchanged
        self.parameter_edit_requested.emit(key, value)

    def _close_label_editor(self):
        editor = self._label_editor
        self._label_editor = None
        self._editing_key = None
        if editor is not None:
            editor._finished = True
            editor.hide()
            editor.deleteLater()
            self.update()

    def is_editing_label(self) -> bool:
        return self._label_editor is not None
