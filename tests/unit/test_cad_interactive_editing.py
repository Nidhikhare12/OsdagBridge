import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_GIRDER_SPACING,
    KEY_CARRIAGEWAY_WIDTH,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_DECK_OVERHANG,
    KEY_TS_OVERALL_WIDTH,
)
from osdagbridge.desktop.ui.docks.cad_top_view import TopViewCADWidget
from osdagbridge.desktop.ui.docks.cad_cross_section import CrossSectionCADWidget
from osdagbridge.desktop.ui.docks.cad_dual_view import BridgeDualCADWidget

app = QApplication.instance() or QApplication([])


def test_top_view_dimension_callouts():
    widget = TopViewCADWidget()
    widget.resize(800, 600)
    pixmap = QPixmap(800, 600)
    painter = QPainter(pixmap)
    widget.dimension_callouts = []
    widget.draw_top_view(painter)
    painter.end()

    callouts = widget.dimension_callouts
    assert len(callouts) > 0

    span_callout = next((c for c in callouts if c.get("param_key") == KEY_SPAN), None)
    assert span_callout is not None
    assert span_callout["is_editable"] is True
    assert span_callout["display_name"] == "Span Length"

    gs_callout = next((c for c in callouts if c.get("param_key") == KEY_TS_GIRDER_SPACING), None)
    assert gs_callout is not None
    assert gs_callout["is_editable"] is True
    assert gs_callout["display_name"] == "Girder Spacing"

    bracing_callout = next((c for c in callouts if c.get("display_name") == "Bracing Spacing"), None)
    if bracing_callout:
        assert bracing_callout["is_editable"] is False


def test_cross_section_dimension_callouts():
    widget = CrossSectionCADWidget()
    widget.resize(800, 600)
    pixmap = QPixmap(800, 600)
    painter = QPainter(pixmap)
    widget.dimension_callouts = []
    widget.draw_cross_section(painter)
    painter.end()

    callouts = widget.dimension_callouts
    assert len(callouts) > 0

    cw_callout = next((c for c in callouts if c.get("param_key") == KEY_CARRIAGEWAY_WIDTH), None)
    assert cw_callout is not None
    assert cw_callout["is_editable"] is True
    assert cw_callout["display_name"] == "Carriageway Width"

    deck_t_callout = next((c for c in callouts if c.get("param_key") == KEY_TS_DECK_THICKNESS), None)
    assert deck_t_callout is not None
    assert deck_t_callout["is_editable"] is True
    assert deck_t_callout["display_name"] == "Deck Thickness"

    overhang_callout = next((c for c in callouts if c.get("param_key") == KEY_TS_DECK_OVERHANG), None)
    assert overhang_callout is not None
    assert overhang_callout["is_editable"] is False

    overall_callout = next((c for c in callouts if c.get("param_key") == KEY_TS_OVERALL_WIDTH), None)
    assert overall_callout is not None
    assert overall_callout["is_editable"] is False


def test_dual_view_signal_forwarding():
    dual_widget = BridgeDualCADWidget()
    emitted = []

    def on_edited(key, val):
        emitted.append((key, val))

    dual_widget.cad_parameter_edited.connect(on_edited)

    # Emit from top view
    dual_widget.top_view_widget.cad_parameter_edited.emit(KEY_SPAN, 35.0)
    assert (KEY_SPAN, 35.0) in emitted
    assert dual_widget.top_view_widget.params['span_length'] == 35000.0

    # Emit from cross section
    dual_widget.cross_section_widget.cad_parameter_edited.emit(KEY_CARRIAGEWAY_WIDTH, 7.5)
    assert (KEY_CARRIAGEWAY_WIDTH, 7.5) in emitted
    assert dual_widget.top_view_widget.params['carriageway_width'] == 7500.0
    assert dual_widget.cross_section_widget.params['carriageway_width'] == 7500.0
