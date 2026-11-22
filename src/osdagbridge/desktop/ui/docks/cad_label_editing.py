"""
Double-click editing of dimension labels on the 2D CAD canvases.

Both CAD widgets (cross-section and top view) draw their labels with QPainter,
so there are no label widgets to click on. Instead, every dimension label is
"tagged" with its CAD parameter just before it is painted; the painted
background rectangle is recorded as a hit region. A double-click inside an
editable region opens a temporary QLineEdit on top of the label. Enter or
focus-out commits; Esc cancels.

The widget itself never touches the input dictionaries. It emits
``label_value_committed(param, text)`` (text in the units shown on the
label) and the template page validates the value, pushes it to the basic /
additional input dictionaries and redraws the CAD.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, QEvent, QObject
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit, QToolTip

# CAD parameter -> (display unit, CAD-mm per display unit)
EDITABLE_CAD_PARAMS = {
    "carriageway_width": ("m", 1000.0),
    "girder_spacing":    ("m", 1000.0),
    "deck_thickness":    ("mm", 1.0),
    "span_length":       ("m", 1000.0),
}

# Derived values: shown on the CAD but never editable (computed by the layout solver)
LOCKED_CAD_PARAMS = {"deck_overhang", "overall_width", "cross_bracing_spacing"}

LOCKED_TOOLTIP = "Derived value (read-only). It is recalculated from the editable parameters."
EDITABLE_TOOLTIP = "Double-click to edit"


class _EditorKeyFilter(QObject):
    """Esc on the inline editor cancels the edit."""

    def __init__(self, owner):
        super().__init__(owner)
        self._owner = owner

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape:
            self._owner._close_label_editor(commit=False)
            return True
        return False


class EditableCADLabelsMixin:
    """Mixin for QWidget CAD canvases. The class must declare
    ``label_value_committed = Signal(str, str)`` and call
    ``_init_label_editing()`` in __init__."""

    def _init_label_editing(self):
        self.label_editing_enabled = False     # only the main-window CAD turns this on
        self.label_regions: list[tuple[QRectF, str]] = []
        self._pending_label_param: str | None = None
        self._label_editor: QLineEdit | None = None
        self._label_editor_param: str | None = None
        self._editor_key_filter = None

    # ── Paint-time registration ───────────────────────────────────────────────
    def _tag_label(self, param: str) -> None:
        """Call right before the label for `param` is painted."""
        self._pending_label_param = param

    def _register_label_rect(self, painter, rect: QRectF) -> None:
        """Called by draw_text_with_background with the painted background rect."""
        param = self._pending_label_param
        if param is None:
            return
        self._pending_label_param = None
        self.label_regions.append((painter.transform().mapRect(QRectF(rect)), param))

    def _reset_label_regions(self) -> None:
        self.label_regions = []
        self._pending_label_param = None

    # ── Hit testing ───────────────────────────────────────────────────────────
    def label_param_at(self, pos) -> tuple[QRectF, str] | None:
        # Labels can overlap when zoomed out; the one painted last is on top,
        # so test in reverse paint order. Exact hits win over the 3 px margin.
        for margin in (0, 3):
            for rect, param in reversed(self.label_regions):
                if rect.adjusted(-margin, -margin, margin, margin).contains(pos):
                    return rect, param
        return None

    def _update_label_hover(self, pos) -> None:
        if not self.label_editing_enabled:
            return
        hit = self.label_param_at(pos)
        if hit and hit[1] in EDITABLE_CAD_PARAMS:
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip(EDITABLE_TOOLTIP)
        elif hit and hit[1] in LOCKED_CAD_PARAMS:
            self.setCursor(Qt.ForbiddenCursor)
            self.setToolTip(LOCKED_TOOLTIP)
        else:
            self.unsetCursor()
            self.setToolTip("")

    # ── Double-click → inline editor ──────────────────────────────────────────
    def mouseDoubleClickEvent(self, event):
        if not self.label_editing_enabled:
            return super().mouseDoubleClickEvent(event)
        pos = event.position() if hasattr(event, "position") else event.pos()
        hit = self.label_param_at(pos)
        if hit is None:
            return super().mouseDoubleClickEvent(event)
        rect, param = hit
        if param in LOCKED_CAD_PARAMS:
            QToolTip.showText(event.globalPosition().toPoint(), LOCKED_TOOLTIP, self)
            event.accept()
            return
        if param in EDITABLE_CAD_PARAMS:
            self.open_label_editor(param, rect)
            event.accept()

    def current_label_value(self, param: str) -> float:
        unit, factor = EDITABLE_CAD_PARAMS[param]
        return float(self.params.get(param, 0.0)) / factor

    def open_label_editor(self, param: str, rect: QRectF | None = None) -> QLineEdit:
        self._close_label_editor(commit=False)
        if rect is None:
            hit = next((r for r, p in self.label_regions if p == param), None)
            rect = hit or QRectF(10, 10, 120, 20)
        unit, _ = EDITABLE_CAD_PARAMS[param]

        editor = QLineEdit(self)
        editor.setObjectName(f"cad_label_editor.{param}")
        validator = QDoubleValidator(0.0, 1e6, 3 if unit == "m" else 1, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        value = self.current_label_value(param)
        editor.setText(f"{value:.2f}" if unit == "m" else f"{value:.0f}")
        editor.setPlaceholderText(unit)
        editor.setToolTip(f"Enter value in {unit}. Enter = apply, Esc = cancel")
        editor.setAlignment(Qt.AlignCenter)
        editor.setStyleSheet(
            "QLineEdit { border: 1.5px solid #90AF13; border-radius: 3px;"
            " background: #ffffff; padding: 1px 4px; font-size: 9pt; }"
        )
        width = max(int(rect.width()), 110)
        height = max(int(rect.height()) + 4, 24)
        x = int(rect.center().x() - width / 2)
        y = int(rect.center().y() - height / 2)
        editor.setGeometry(x, y, width, height)

        self._editor_key_filter = _EditorKeyFilter(self)
        editor.installEventFilter(self._editor_key_filter)
        editor.returnPressed.connect(lambda: self._close_label_editor(commit=True))
        editor.editingFinished.connect(lambda: self._close_label_editor(commit=True))

        self._label_editor = editor
        self._label_editor_param = param
        self._label_editor_initial = editor.text()
        editor.show()
        editor.selectAll()
        editor.setFocus(Qt.MouseFocusReason)
        return editor

    def _close_label_editor(self, commit: bool) -> None:
        editor, param = self._label_editor, self._label_editor_param
        if editor is None:
            return
        # Detach first so the editingFinished fired by hide()/focus loss is a no-op
        self._label_editor = None
        self._label_editor_param = None
        text = editor.text().strip()
        editor.hide()
        editor.setObjectName("")   # a pending deleteLater must not shadow the next editor
        editor.deleteLater()
        self.setFocus()
        unchanged = text == getattr(self, "_label_editor_initial", None)
        if commit and param is not None and not unchanged:
            # Value validity (range, layout feasibility) is checked by the receiver
            self.label_value_committed.emit(param, text)
        self.update()
