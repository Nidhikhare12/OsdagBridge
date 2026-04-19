"""
Multi-View CAD Widget for OsdagBridge
Combines cross-section, top view, elevation, and 3D view with tabbed interface
Author: Arushi
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QTabWidget, QPushButton, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .cad_cross_section import CrossSectionCADWidget
from .cad_top_view import TopViewCADWidget
from .cad_elevation_view import ElevationViewCADWidget
from .cad_3d_view import Bridge3DCADWidget

class BridgeMultiViewCADWidget(QWidget):
    """Multi-view widget with tabbed interface for all 4 views"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_view = 'cross_section'
        
    def setup_ui(self):
        """Setup the tabbed view layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #000000;
                padding: 5px 15px;
                border: 1px solid #d0d0d0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #000000;
                border-bottom: 2px solid #90AF13;
            }
            QTabBar::tab:hover {
                background-color: #f5f5f5;
            }
        """)
        
        # ============ CROSS-SECTION VIEW ============
        self.cross_section_widget = CrossSectionCADWidget(self)
        self.cross_scroll = QScrollArea()
        self.cross_scroll.setWidget(self.cross_section_widget)
        self.cross_scroll.setWidgetResizable(True)
        self.cross_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.cross_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.cross_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.tab_widget.addTab(self.cross_scroll, "Cross-Section")
        
        # ============ TOP VIEW ============
        self.top_view_widget = TopViewCADWidget(self)
        self.top_scroll = QScrollArea()
        self.top_scroll.setWidget(self.top_view_widget)
        self.top_scroll.setWidgetResizable(True)
        self.top_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.top_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.top_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.tab_widget.addTab(self.top_scroll, "Top View")
        
        # ============ ELEVATION VIEW ============
        self.elevation_widget = ElevationViewCADWidget(self)
        self.elevation_scroll = QScrollArea()
        self.elevation_scroll.setWidget(self.elevation_widget)
        self.elevation_scroll.setWidgetResizable(True)
        self.elevation_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.elevation_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.elevation_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.tab_widget.addTab(self.elevation_scroll, "Elevation")
        
        # ============ 3D VIEW ============
        self.view_3d_widget = Bridge3DCADWidget(self)
        self.view_3d_scroll = QScrollArea()
        self.view_3d_scroll.setWidget(self.view_3d_widget)
        self.view_3d_scroll.setWidgetResizable(True)
        self.view_3d_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view_3d_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.view_3d_scroll.setStyleSheet("QScrollArea { border: none; }")
        self.tab_widget.addTab(self.view_3d_scroll, "3D View")
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        layout.addWidget(self.tab_widget)
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        tab_names = ['cross_section', 'top_view', 'elevation', '3d_view']
        self.current_view = tab_names[index] if index < len(tab_names) else 'cross_section'
    
    def update_from_osdag_inputs(self, input_dict):
        """
        Update all CAD views from OsdagBridge input fields
        """
        from osdagbridge.core.utils.common import (
            KEY_SPAN, KEY_CARRIAGEWAY_WIDTH, KEY_SKEW_ANGLE, KEY_FOOTPATH,
            KEY_NO_OF_GIRDERS, KEY_GIRDER_SPACING, KEY_DECK_OVERHANG,
            KEY_DECK_THICKNESS, KEY_FOOTPATH_WIDTH, KEY_FOOTPATH_THICKNESS,
            KEY_CROSS_BRACING_SPACING, KEY_INCLUDE_MEDIAN
        )
        
        params = {}

        def _to_float(value, default=None):
            try:
                if value is None:
                    return default
                if isinstance(value, str) and not value.strip():
                    return default
                return float(value)
            except (TypeError, ValueError):
                return default

        def _to_int(value, default=None):
            try:
                if value is None:
                    return default
                if isinstance(value, str) and not value.strip():
                    return default
                return int(float(value))
            except (TypeError, ValueError):
                return default

        span_m = _to_float(input_dict.get(KEY_SPAN))
        if span_m is not None:
            params['span_length'] = span_m * 1000

        carriageway_m = _to_float(input_dict.get(KEY_CARRIAGEWAY_WIDTH))
        if carriageway_m is not None:
            params['carriageway_width'] = carriageway_m * 1000

        skew_angle = _to_float(input_dict.get(KEY_SKEW_ANGLE))
        if skew_angle is not None:
            params['skew_angle'] = skew_angle

        num_girders = _to_int(input_dict.get(KEY_NO_OF_GIRDERS))
        if num_girders is not None:
            params['num_girders'] = num_girders

        girder_spacing_m = _to_float(input_dict.get(KEY_GIRDER_SPACING))
        if girder_spacing_m is not None:
            params['girder_spacing'] = girder_spacing_m * 1000

        deck_overhang_m = _to_float(input_dict.get(KEY_DECK_OVERHANG))
        if deck_overhang_m is not None:
            params['deck_overhang'] = deck_overhang_m * 1000

        deck_thickness_mm = _to_float(input_dict.get(KEY_DECK_THICKNESS))
        if deck_thickness_mm is not None:
            params['deck_thickness'] = deck_thickness_mm

        footpath_width_m = _to_float(input_dict.get(KEY_FOOTPATH_WIDTH))
        if footpath_width_m is not None:
            params['footpath_width'] = footpath_width_m * 1000

        footpath_thickness_mm = _to_float(input_dict.get(KEY_FOOTPATH_THICKNESS))
        if footpath_thickness_mm is not None:
            params['footpath_thickness'] = footpath_thickness_mm

        if KEY_FOOTPATH in input_dict:
            footpath_value = str(input_dict.get(KEY_FOOTPATH, '')).strip()
            if footpath_value == "None":
                params['footpath_config'] = 'none'
            elif footpath_value in {"Single Side", "Single Sided", "Left"}:
                params['footpath_config'] = 'left'
            elif footpath_value == "Right":
                params['footpath_config'] = 'right'
            elif footpath_value in {"Both", "Both Sides"}:
                params['footpath_config'] = 'both'

        cross_bracing_spacing_m = _to_float(input_dict.get(KEY_CROSS_BRACING_SPACING))
        if cross_bracing_spacing_m is not None:
            params['cross_bracing_spacing'] = cross_bracing_spacing_m * 1000

        if KEY_INCLUDE_MEDIAN in input_dict:
            raw_median = input_dict.get(KEY_INCLUDE_MEDIAN)
            if isinstance(raw_median, str):
                params['median_present'] = raw_median.strip().lower() in {"yes", "true", "1"}
            else:
                params['median_present'] = bool(raw_median)

        # Custom load values drive load overlays in cross-section and elevation.
        load_case = str(input_dict.get("custom_load_case", "") or "").strip()
        custom_load_case_name = str(input_dict.get("custom_load_case_name", "") or "").strip()
        if not load_case:
            load_case = "LL"
        elif load_case.lower() == "custom":
            load_case = custom_load_case_name or "Custom"

        load_type = str(input_dict.get("custom_load_type", "Point") or "Point").strip().title()
        if load_type not in {"Point", "Line", "Area"}:
            load_type = "Point"

        params['show_live_load'] = True
        params['load_case_label'] = load_case
        params['load_type'] = load_type

        point_left_m = _to_float(input_dict.get("custom_point_left"))
        point_bearing_m = _to_float(input_dict.get("custom_point_bearing"))
        line_left_start_m = _to_float(input_dict.get("custom_line_left_start"))
        line_left_end_m = _to_float(input_dict.get("custom_line_left_end"))
        line_bearing_start_m = _to_float(input_dict.get("custom_line_bearing_start"))
        line_bearing_end_m = _to_float(input_dict.get("custom_line_bearing_end"))

        if point_left_m is not None:
            params['load_transverse_m'] = point_left_m

        if line_left_start_m is not None and line_left_end_m is not None:
            if line_left_end_m < line_left_start_m:
                line_left_start_m, line_left_end_m = line_left_end_m, line_left_start_m
            params['load_transverse_start_m'] = line_left_start_m
            params['load_transverse_end_m'] = line_left_end_m

        if line_bearing_start_m is not None and line_bearing_end_m is not None:
            if line_bearing_end_m < line_bearing_start_m:
                line_bearing_start_m, line_bearing_end_m = line_bearing_end_m, line_bearing_start_m
            params['load_line_start_m'] = line_bearing_start_m
            params['load_line_end_m'] = line_bearing_end_m
            params['load_position_m'] = (line_bearing_start_m + line_bearing_end_m) * 0.5
        elif point_bearing_m is not None:
            params['load_position_m'] = point_bearing_m
        elif span_m is not None and span_m > 0.0:
            params['load_position_m'] = span_m * 0.5

        if span_m and span_m > 0.0 and 'load_position_m' in params:
            params['load_position_ratio'] = max(0.0, min(1.0, params['load_position_m'] / span_m))
        
        # Update all widgets with same parameters
        self.cross_section_widget.update_params(params)
        self.top_view_widget.update_params(params)
        self.elevation_widget.update_params(params)
        self.view_3d_widget.update_params(params)
    
    def update_specific_param(self, param_key, value):
        """
        Update a specific parameter in all views
        Optimized for real-time updates
        """
        params = {param_key: value}
        self.cross_section_widget.update_params(params)
        self.top_view_widget.update_params(params)
        self.elevation_widget.update_params(params)
        self.view_3d_widget.update_params(params)
    
    # Delegation methods for cross-section view
    def set_cross_section_visible(self, visible):
        """Show/hide cross-section tab"""
        if visible:
            if self.tab_widget.indexOf(self.cross_scroll) == -1:
                self.tab_widget.insertTab(0, self.cross_scroll, "Cross-Section")
        else:
            idx = self.tab_widget.indexOf(self.cross_scroll)
            if idx != -1:
                self.tab_widget.removeTab(idx)
    
    def set_top_view_visible(self, visible):
        """Show/hide top view tab"""
        if visible:
            if self.tab_widget.indexOf(self.top_scroll) == -1:
                self.tab_widget.insertTab(1, self.top_scroll, "Top View")
        else:
            idx = self.tab_widget.indexOf(self.top_scroll)
            if idx != -1:
                self.tab_widget.removeTab(idx)
    
    def set_elevation_visible(self, visible):
        """Show/hide elevation tab"""
        if visible:
            if self.tab_widget.indexOf(self.elevation_scroll) == -1:
                self.tab_widget.insertTab(2, self.elevation_scroll, "Elevation")
        else:
            idx = self.tab_widget.indexOf(self.elevation_scroll)
            if idx != -1:
                self.tab_widget.removeTab(idx)
    
    def set_3d_visible(self, visible):
        """Show/hide 3D view tab"""
        if visible:
            if self.tab_widget.indexOf(self.view_3d_scroll) == -1:
                self.tab_widget.insertTab(3, self.view_3d_scroll, "3D View")
        else:
            idx = self.tab_widget.indexOf(self.view_3d_scroll)
            if idx != -1:
                self.tab_widget.removeTab(idx)