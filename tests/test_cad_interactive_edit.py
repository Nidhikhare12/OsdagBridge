import os
import sys
import pytest
from PySide6.QtWidgets import QApplication, QLineEdit
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap

from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_TS_GIRDER_SPACING,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
    KEY_MP_CB_SPACING,
)
from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget
from osdagbridge.desktop.ui.docks.cad_top_view import TopViewCADWidget
from osdagbridge.desktop.ui.docks.cad_dual_view import BridgeDualCADWidget

@pytest.fixture(scope="session")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def paint_widget(widget):
    """Helper to simulate paintEvent and populate registered_dimension_labels."""
    widget.resize(1000, 800)
    widget.show()
    pix = QPixmap(widget.size())
    widget.render(pix)
    return widget.registered_dimension_labels

def test_cross_section_label_registration(app):
    """Verify that CrossSectionCADWidget registers editable and locked labels."""
    cs = CrossSectionCADWidget()
    cs.show_dimensions = True
    cs.show_carriageway_values = True
    cs.params['carriageway_width'] = 7500
    cs.params['num_girders'] = 4
    cs.params['girder_spacing'] = 2500
    cs.params['deck_thickness'] = 220
    cs.params['deck_overhang'] = 1000
    
    labels = paint_widget(cs)
    assert len(labels) > 0, "Labels should be registered during paint"

    keys_registered = {l["key"]: l for l in labels}
    
    # Check editable parameters
    assert KEY_CARRIAGEWAY_WIDTH in keys_registered
    assert keys_registered[KEY_CARRIAGEWAY_WIDTH]["editable"] is True

    assert KEY_TS_GIRDER_SPACING in keys_registered
    assert keys_registered[KEY_TS_GIRDER_SPACING]["editable"] is True

    assert KEY_TS_DECK_THICKNESS in keys_registered
    assert keys_registered[KEY_TS_DECK_THICKNESS]["editable"] is True

    # Check locked parameters
    assert KEY_TS_OVERALL_WIDTH in keys_registered
    assert keys_registered[KEY_TS_OVERALL_WIDTH]["editable"] is False

    assert KEY_TS_DECK_OVERHANG in keys_registered
    assert keys_registered[KEY_TS_DECK_OVERHANG]["editable"] is False

def test_top_view_label_registration(app):
    """Verify that TopViewCADWidget registers editable and locked labels."""
    tv = TopViewCADWidget()
    tv.show_dimensions = True
    tv.show_span_values = True
    tv.show_carriageway_values = True
    tv.params['span_length'] = 30000
    tv.params['girder_spacing'] = 2500
    tv.params['cross_bracing_spacing'] = 3500
    
    labels = paint_widget(tv)
    assert len(labels) > 0, "Top view labels should be registered during paint"

    keys_registered = {l["key"]: l for l in labels}
    
    # Check editable parameters
    assert KEY_SPAN in keys_registered
    assert keys_registered[KEY_SPAN]["editable"] is True

    assert KEY_TS_GIRDER_SPACING in keys_registered
    assert keys_registered[KEY_TS_GIRDER_SPACING]["editable"] is True

    # Check locked parameter
    assert KEY_MP_CB_SPACING in keys_registered
    assert keys_registered[KEY_MP_CB_SPACING]["editable"] is False

def test_locked_parameters_remain_readonly(app):
    """Double-clicking locked parameters (Overhang, Overall Bridge Width, Bracing Spacing) must not open editor."""
    cs = CrossSectionCADWidget()
    cs.show_dimensions = True
    cs.show_carriageway_values = True
    paint_widget(cs)

    # Test Overall Bridge Width (locked)
    width_info = next((l for l in cs.registered_dimension_labels if l["key"] == KEY_TS_OVERALL_WIDTH), None)
    assert width_info is not None
    center = width_info["rect"].center().toPoint()
    event = QMouseEvent(QMouseEvent.MouseButtonDblClick, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    cs.mouseDoubleClickEvent(event)
    assert getattr(cs, "_editor", None) is None, "Overall Bridge Width must not spawn editor"

    # Test Overhang (locked)
    overhang_info = next((l for l in cs.registered_dimension_labels if l["key"] == KEY_TS_DECK_OVERHANG), None)
    assert overhang_info is not None
    center = overhang_info["rect"].center().toPoint()
    event = QMouseEvent(QMouseEvent.MouseButtonDblClick, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    cs.mouseDoubleClickEvent(event)
    assert getattr(cs, "_editor", None) is None, "Overhang must not spawn editor"

    # Test Bracing Spacing (locked) on TopView
    tv = TopViewCADWidget()
    tv.show_dimensions = True
    tv.show_span_values = True
    paint_widget(tv)
    cb_info = next((l for l in tv.registered_dimension_labels if l["key"] == KEY_MP_CB_SPACING), None)
    assert cb_info is not None
    center = cb_info["rect"].center().toPoint()
    event = QMouseEvent(QMouseEvent.MouseButtonDblClick, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    tv.mouseDoubleClickEvent(event)
    assert getattr(tv, "_editor", None) is None, "Bracing Spacing must not spawn editor"

def test_editable_parameter_enter_commit(app):
    """Double-clicking Carriageway Width opens editor, entering new value + Enter commits."""
    cs = CrossSectionCADWidget()
    cs.show_dimensions = True
    cs.show_carriageway_values = True
    cs.params['carriageway_width'] = 7500
    paint_widget(cs)

    cw_info = next((l for l in cs.registered_dimension_labels if l["key"] == KEY_CARRIAGEWAY_WIDTH), None)
    assert cw_info is not None

    emitted_values = []
    cs.parameter_edited.connect(lambda k, v: emitted_values.append((k, v)))

    # Double click to open editor
    center = cw_info["rect"].center().toPoint()
    event = QMouseEvent(QMouseEvent.MouseButtonDblClick, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    cs.mouseDoubleClickEvent(event)

    assert cs._editor is not None
    assert cs._editor.isVisible()
    assert float(cs._editor.text()) == 7.5

    # Change text and commit via returnPressed
    cs._editor.setText("8.5")
    cs._editor.returnPressed.emit()

    assert cs._editor is None
    assert len(emitted_values) == 1
    assert emitted_values[0] == (KEY_CARRIAGEWAY_WIDTH, 8.5)

def test_editable_parameter_click_outside_commit(app):
    """Double-clicking Girder Spacing opens editor, clicking outside commits value."""
    cs = CrossSectionCADWidget()
    cs.show_dimensions = True
    cs.show_carriageway_values = True
    cs.params['girder_spacing'] = 2500
    paint_widget(cs)

    gs_info = next((l for l in cs.registered_dimension_labels if l["key"] == KEY_TS_GIRDER_SPACING), None)
    assert gs_info is not None

    emitted_values = []
    cs.parameter_edited.connect(lambda k, v: emitted_values.append((k, v)))

    # Double click to open editor
    center = gs_info["rect"].center().toPoint()
    event = QMouseEvent(QMouseEvent.MouseButtonDblClick, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    cs.mouseDoubleClickEvent(event)

    assert cs._editor is not None
    cs._editor.setText("2.8")

    # Click outside editor geometry
    press_pos = QPoint(10, 10) # Clearly outside the editor
    assert not cs._editor.geometry().contains(press_pos)
    press_event = QMouseEvent(QMouseEvent.MouseButtonPress, press_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    cs.mousePressEvent(press_event)

    assert cs._editor is None
    assert len(emitted_values) == 1
    assert emitted_values[0] == (KEY_TS_GIRDER_SPACING, 2.8)

def test_invalid_input_validation(app, monkeypatch):
    """Entering empty, non-numeric, zero, negative, or invalid engineering values must be rejected."""
    cs = CrossSectionCADWidget()
    cs.show_dimensions = True
    cs.show_carriageway_values = True
    paint_widget(cs)

    errors_shown = []
    monkeypatch.setattr(cs, "_show_edit_error", lambda msg: errors_shown.append(msg))

    cw_info = next((l for l in cs.registered_dimension_labels if l["key"] == KEY_CARRIAGEWAY_WIDTH), None)
    assert cw_info is not None

    emitted_values = []
    cs.parameter_edited.connect(lambda k, v: emitted_values.append((k, v)))

    # 1. Non-numeric
    cs._start_in_place_edit(cw_info)
    cs._editor.setText("abc")
    cs._commit_edit()
    assert len(errors_shown) == 1
    assert "valid number" in errors_shown[-1]
    assert len(emitted_values) == 0

    # 2. Zero
    cs._start_in_place_edit(cw_info)
    cs._editor.setText("0")
    cs._commit_edit()
    assert len(errors_shown) == 2
    assert "greater than zero" in errors_shown[-1]
    assert len(emitted_values) == 0

    # 3. Negative
    cs._start_in_place_edit(cw_info)
    cs._editor.setText("-5.0")
    cs._commit_edit()
    assert len(errors_shown) == 3
    assert "greater than zero" in errors_shown[-1]
    assert len(emitted_values) == 0

    # 4. Empty
    cs._start_in_place_edit(cw_info)
    cs._editor.setText("   ")
    cs._commit_edit()
    assert len(errors_shown) == 4
    assert "cannot be empty" in errors_shown[-1]
    assert len(emitted_values) == 0

def test_span_length_editing_in_top_view(app):
    """Double-clicking Span Length in TopViewCADWidget commits valid value."""
    tv = TopViewCADWidget()
    tv.show_dimensions = True
    tv.show_span_values = True
    tv.params['span_length'] = 30000
    paint_widget(tv)

    span_info = next((l for l in tv.registered_dimension_labels if l["key"] == KEY_SPAN), None)
    assert span_info is not None

    emitted_values = []
    tv.parameter_edited.connect(lambda k, v: emitted_values.append((k, v)))

    # Double click
    center = span_info["rect"].center().toPoint()
    event = QMouseEvent(QMouseEvent.MouseButtonDblClick, center, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    tv.mouseDoubleClickEvent(event)

    assert tv._editor is not None
    assert tv._editor.isVisible()
    assert float(tv._editor.text()) == 30.0

    tv._editor.setText("35.0")
    tv._commit_edit()

    assert len(emitted_values) == 1
    assert emitted_values[0] == (KEY_SPAN, 35.0)

def test_dual_view_relay_signals(app):
    """BridgeDualCADWidget properly relays parameter_edited from child widgets."""
    dual = BridgeDualCADWidget()
    emitted = []
    dual.parameter_edited.connect(lambda k, v: emitted.append((k, v)))

    # Emit from cross section child
    dual.cross_section_widget.parameter_edited.emit(KEY_CARRIAGEWAY_WIDTH, 9.5)
    assert len(emitted) == 1
    assert emitted[0] == (KEY_CARRIAGEWAY_WIDTH, 9.5)

    # Emit from top view child
    dual.top_view_widget.parameter_edited.emit(KEY_SPAN, 40.0)
    assert len(emitted) == 2
    assert emitted[1] == (KEY_SPAN, 40.0)
