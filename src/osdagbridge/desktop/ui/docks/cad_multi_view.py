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
        
        # Map span (meters to mm)
        if KEY_SPAN in input_dict:
            params['span_length'] = float(input_dict[KEY_SPAN]) * 1000
        
        # Map carriageway width (meters to mm)
        if KEY_CARRIAGEWAY_WIDTH in input_dict:
            params['carriageway_width'] = float(input_dict[KEY_CARRIAGEWAY_WIDTH]) * 1000
        
        # Map skew angle (degrees)
        if KEY_SKEW_ANGLE in input_dict:
            params['skew_angle'] = float(input_dict[KEY_SKEW_ANGLE])
        
        # Map number of girders
        if KEY_NO_OF_GIRDERS in input_dict:
            params['num_girders'] = int(input_dict[KEY_NO_OF_GIRDERS])
        
        # Map girder spacing (meters to mm)
        if KEY_GIRDER_SPACING in input_dict:
            params['girder_spacing'] = float(input_dict[KEY_GIRDER_SPACING]) * 1000
        
        # Map deck overhang (meters to mm)
        if KEY_DECK_OVERHANG in input_dict:
            params['deck_overhang'] = float(input_dict[KEY_DECK_OVERHANG]) * 1000
        
        # Map deck thickness (mm)
        if KEY_DECK_THICKNESS in input_dict:
            params['deck_thickness'] = float(input_dict[KEY_DECK_THICKNESS])
        
        # Map footpath width (meters to mm)
        if KEY_FOOTPATH_WIDTH in input_dict:
            params['footpath_width'] = float(input_dict[KEY_FOOTPATH_WIDTH]) * 1000
        
        # Map footpath thickness (mm)
        if KEY_FOOTPATH_THICKNESS in input_dict:
            params['footpath_thickness'] = float(input_dict[KEY_FOOTPATH_THICKNESS])
        
        # Map footpath configuration
        if KEY_FOOTPATH in input_dict:
            footpath_value = input_dict[KEY_FOOTPATH]
            if footpath_value == "None":
                params['footpath_config'] = 'none'
            elif footpath_value == "Single Sided":
                params['footpath_config'] = 'left'
            elif footpath_value == "Both":
                params['footpath_config'] = 'both'
        
        # Map cross bracing spacing (meters to mm)
        if KEY_CROSS_BRACING_SPACING in input_dict:
            params['cross_bracing_spacing'] = float(input_dict[KEY_CROSS_BRACING_SPACING]) * 1000
        
        # Map median present
        if KEY_INCLUDE_MEDIAN in input_dict:
            params['median_present'] = bool(input_dict[KEY_INCLUDE_MEDIAN])
        
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
