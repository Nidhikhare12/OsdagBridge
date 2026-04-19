"""
Cross-Section CAD Widget for OsdagBridge
Handles cross-sectional view rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from PySide6.QtGui import QPixmap
import random

class CrossSectionCADWidget(QWidget):
    """Widget for drawing bridge cross-section view"""
    # ===== SHARED CAD COLORS =====
    GIRDER_COLOR = QColor(179, 180, 160)
    STIFFENER_COLOR = QColor(79, 78, 70)
    CROSS_BRACING_COLOR = QColor(235, 236, 211)
    END_DIAPHRAGM_COLOR = QColor(134, 134, 100)

    CONCRETE_COLOR = QColor(225, 225, 225)
    BARRIER_COLOR = QColor(126, 126, 126)
    MEDIAN_COLOR = QColor(221, 221, 221)
    RAILING_COLOR = QColor(126, 126, 126)

    BEARING_COLOR = QColor(255, 0, 0)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # enable mouse tracking for hover
        self.concrete_brush = self.create_concrete_brush()
        # hover label regions: list of (QRectF, text, bg_color, text_color)
        self.hover_labels = []
        self.hovered_label_index = -1
        self.hovered_element = None  # Track hovered element for highlighting
        self.cross_section_hover_zones = []  # Store hover zones as (QRectF, element_type)
        
        # Scale factor for diagram size (1.0 = normal, <1.0 = smaller)
        self.scale_factor = 1.0
        
        # Zoom level for this widget
        self.zoom_level = 1.0
        
        # Setup zoom controls inside this widget (but not for previews inside scroll areas)
        # Will be called after widget is fully initialized
        self._zoom_controls_setup = False
        
        # bridge parameters with default values (all in mm)
        self.params = {
            'span_length': 35000,
            'num_girders': 4,
            'girder_spacing': 2750,
            'cross_bracing_spacing': 3500,
            'carriageway_width': 10500,
            'skew_angle': 0,
            'deck_thickness': 200,
            'footpath_width': 1500,
            'footpath_thickness': 200,
            'crash_barrier_width': 500,
            'railing_height': 1000,
            'footpath_config': 'both',
            'deck_overhang': 1000,
            'railing_width': 100,
            'median_present': False,
            'median_width': 1200,
            'show_live_load': True,
            'load_case_label': 'LL',
            'load_type': 'Point',
            'load_position_m': 17.5,
            'load_transverse_m': None,
            'load_transverse_start_m': None,
            'load_transverse_end_m': None,
            'load_line_start_m': None,
            'load_line_end_m': None,
        }
        
        # girder dimensions (mm)
        self.girder = {
            'depth': 500,
            'top_flange_width': 180,
            'top_flange_thickness': 17.2,
            'bottom_flange_width': 180,
            'bottom_flange_thickness': 17.2,
            'web_thickness': 10.2,
            # Legacy support for symmetric sections
            'flange_width': 180,
            'flange_thickness': 17.2,
        }
        
        # stiffener dimensions
        self.stiffener = {
            'width': 84.9,
            'height': 465.6,
        }

        self.girder_visual_scale = {
            'depth': 3.0,
            'flange_width': 3.75,
            'flange_thickness': 4.05,
            'web_thickness': 3.75,
        }
        
        # crash barrier dimensions (mm) 
        self.crash_barrier = {
            'width': 500,
            'height': 800,
            'base_width': 300,
        }
        
        # railing dimensions
        self.railing = {
            'post_dia': 50,
            'height': 1000,
            'rail_count': 3,
            'width': 100,
        }
        
        # Setup zoom controls (buttons will be hidden initially)
        self.setup_zoom_controls()
        
        # Track scroll area for fixed button positioning
        self.scroll_area = None

    def setup_zoom_controls(self):
        """Create zoom controls inside the widget"""
        self.zoom_in_btn = QPushButton("+", self)
        self.zoom_in_btn.setFixedSize(25, 25)
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #999;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(144, 175, 19, 200);
                color: white;
            }
        """)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_in_btn.hide()  # Hide initially, show in showEvent for non-previews
        
        self.zoom_out_btn = QPushButton("-", self)
        self.zoom_out_btn.setFixedSize(25, 25)
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #999;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(144, 175, 19, 200);
                color: white;
            }
        """)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_out_btn.hide()  # Hide initially
        
        self.zoom_reset_btn = QPushButton("Reset", self)
        self.zoom_reset_btn.setFixedSize(45, 25)
        self.zoom_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 200);
                border: 1px solid #999;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: rgba(144, 175, 19, 200);
                color: white;
            }
        """)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        self.zoom_reset_btn.hide()  # Hide initially
        
        # Set minimum size for visibility
        self.setMinimumSize(400, 300)
    
    def _position_zoom_buttons(self):
        """Lock zoom buttons to fixed viewport position - improved version"""
        if not hasattr(self, 'zoom_in_btn'):
            return

        # Find scroll area once
        if self.scroll_area is None:
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    self.scroll_area = parent
                    # Install event filter on viewport to catch resize events
                    if self.scroll_area.viewport():
                        self.scroll_area.viewport().installEventFilter(self)
                    break
                parent = parent.parent()

        # Return early if scroll area not found yet
        if not self.scroll_area:
            return

        viewport = self.scroll_area.viewport()
        
        # Check if viewport is valid
        if not viewport or viewport.width() == 0:
            return
        
        # Re-parent buttons to viewport if not already
        if self.zoom_in_btn.parent() != viewport:
            self.zoom_in_btn.setParent(viewport)
            self.zoom_out_btn.setParent(viewport)
            self.zoom_reset_btn.setParent(viewport)

        # Position in top-right corner of VIEWPORT
        margin = 10
        x = viewport.width() - 50
        y = margin

        self.zoom_in_btn.move(x + 10, y)
        self.zoom_out_btn.move(x + 10, y + 30)
        self.zoom_reset_btn.move(x, y + 60)

        # Ensure buttons are visible and on top
        self.zoom_in_btn.show()
        self.zoom_out_btn.show()
        self.zoom_reset_btn.show()
        self.zoom_in_btn.raise_()
        self.zoom_out_btn.raise_()
        self.zoom_reset_btn.raise_()


    def eventFilter(self, obj, event):
        """Filter events to catch viewport resize"""
        if obj == (self.scroll_area.viewport() if self.scroll_area else None):
            if event.type() == event.Type.Resize:
                # Viewport resized - reposition buttons
                self._position_zoom_buttons()
        return super().eventFilter(obj, event)


    def showEvent(self, event):
        """Setup zoom controls on first show"""
        super().showEvent(event)
        if not self._zoom_controls_setup:
            self._zoom_controls_setup = True
            # Check if this is a preview
            is_preview = self.scale_factor < 1.0 if hasattr(self, 'scale_factor') else False
            # Only show zoom buttons if NOT a preview
            if not is_preview and hasattr(self, 'zoom_in_btn'):
                # Position buttons immediately
                self._position_zoom_buttons()
    
    def zoom_in(self):
        """Zoom in while keeping view centered"""
        # Store old center position before zoom
        old_center = self._get_scroll_center()
        
        # Apply zoom
        self.zoom_level *= 1.1
        self._update_widget_size()
        self.update()
        
        # Restore center position after zoom
        self._set_scroll_center(old_center, 1.1)

    def zoom_out(self):
        """Zoom out while keeping view centered"""
        # Store old center position before zoom
        old_center = self._get_scroll_center()
        
        # Apply zoom
        self.zoom_level /= 1.1
        self._update_widget_size()
        self.update()
        
        # Restore center position after zoom
        self._set_scroll_center(old_center, 1/1.1)

    def zoom_reset(self):
        """Reset zoom to 1.0 while keeping view centered"""
        # Store old center position before zoom
        old_center = self._get_scroll_center()
        zoom_ratio = 1.0 / self.zoom_level
        
        # Apply zoom
        self.zoom_level = 1.0
        self._update_widget_size()
        self.update()
        
        # Restore center position after zoom
        self._set_scroll_center(old_center, zoom_ratio)

    def _get_scroll_center(self):
        """Get the current center point of the visible viewport in widget coordinates"""
        if not self.scroll_area:
            return (0.5, 0.5)  # Default to center
        
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        v_scrollbar = self.scroll_area.verticalScrollBar()
        viewport = self.scroll_area.viewport()
        
        # Get current scroll position
        h_value = h_scrollbar.value()
        v_value = v_scrollbar.value()
        
        # Get viewport dimensions
        viewport_width = viewport.width()
        viewport_height = viewport.height()
        
        # Calculate center point in widget coordinates
        center_x = h_value + viewport_width / 2
        center_y = v_value + viewport_height / 2
        
        # Get widget dimensions
        widget_width = self.width()
        widget_height = self.height()
        
        # Return normalized center position (0.0 to 1.0)
        if widget_width > 0 and widget_height > 0:
            return (center_x / widget_width, center_y / widget_height)
        else:
            return (0.5, 0.5)

    def _set_scroll_center(self, old_center, zoom_ratio):
        """Set scroll position to keep the same center point visible after zoom"""
        if not self.scroll_area:
            return
        
        h_scrollbar = self.scroll_area.horizontalScrollBar()
        v_scrollbar = self.scroll_area.verticalScrollBar()
        viewport = self.scroll_area.viewport()
        
        # Get new widget dimensions after zoom
        new_width = self.width()
        new_height = self.height()
        
        # Calculate new center position in pixels
        new_center_x = old_center[0] * new_width
        new_center_y = old_center[1] * new_height
        
        # Calculate new scroll positions to center on the same point
        viewport_width = viewport.width()
        viewport_height = viewport.height()
        
        new_h_value = int(new_center_x - viewport_width / 2)
        new_v_value = int(new_center_y - viewport_height / 2)
        
        # Clamp to valid range
        new_h_value = max(0, min(new_h_value, h_scrollbar.maximum()))
        new_v_value = max(0, min(new_v_value, v_scrollbar.maximum()))
        
        # Apply new scroll positions
        h_scrollbar.setValue(new_h_value)
        v_scrollbar.setValue(new_v_value)
    
    def _update_widget_size(self):
        """Update widget size based on zoom level for proper scrolling"""
        base_width = 800
        base_height = 600
        # Add extra padding (20%) to ensure scrollbar reaches beyond content
        padding_factor = 1.2
        new_width = int(base_width * self.zoom_level * padding_factor)
        new_height = int(base_height * self.zoom_level)
        self.setMinimumSize(new_width, new_height)
        self.resize(new_width, new_height)
    
    def resizeEvent(self, event):
        """Position zoom controls in top-right corner"""
        super().resizeEvent(event)
        self._position_zoom_buttons()
    
    def update_params(self, params):
        self.params.update(params)
        self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse hover for both labels and structural elements"""
        pos = event.position() if hasattr(event, 'position') else event.pos()
        
        # Check label hover first
        new_hovered = -1
        for i, (rect, text, bg_color, text_color) in enumerate(self.hover_labels):
            if rect.contains(pos):
                new_hovered = i
                break
        
        if new_hovered != self.hovered_label_index:
            self.hovered_label_index = new_hovered
            self.update()
        
        # Check element hover
        new_hovered_element = None
        for rect, element_type in self.cross_section_hover_zones:
            if rect.contains(pos):
                new_hovered_element = element_type
                break
        
        if new_hovered_element != self.hovered_element:
            self.hovered_element = new_hovered_element
            self.update()

    def register_hover_label(self, x, y, text, bg_color, text_color, font_size=9):
        """lables for catching hover hovering"""
        font = QFont('Arial', font_size, QFont.Bold)
        metrics = self.fontMetrics()
        text_rect = metrics.boundingRect(text)
        
        padding = 5
        hover_rect = QRectF(x - padding, y - text_rect.height() - padding,
                            text_rect.width() + 2*padding + 20, text_rect.height() + 2*padding + 10)
        
        self.hover_labels.append((hover_rect, text, bg_color, text_color))
        return len(self.hover_labels) - 1

    def draw_hover_label_if_active(self, painter, label_index, x, y, text, bg_color, text_color, font_size=9):
        """label only if its being hovered"""
        if self.hovered_label_index == label_index:
            self.draw_text_with_background(painter, x, y, text, bg_color, text_color, font_size, True)
        
    def paintEvent(self, event):
        # Position buttons on first paint if not done yet
        if hasattr(self, 'zoom_in_btn') and not hasattr(self, '_buttons_positioned'):
            self._position_zoom_buttons()
            self._buttons_positioned = True
        # clear hover labels and zones at start of each paint
        self.hover_labels = []
        self.cross_section_hover_zones = []
        
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            self.draw_cross_section(painter)
        except Exception as e:
            print(" PAINT ERROR:", repr(e))
        finally:
            painter.end() 
    def draw_text_with_background(self, painter, x, y, text,
                              bg_color=QColor(255, 255, 255, 230), 
                              text_color=QColor(0, 0, 0), font_size=9, bold=False):

        font_weight = QFont.Bold if bold else QFont.Normal
        font = QFont('Arial', font_size, font_weight)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        # breaking text in 2 to space be space
        lines = text.split("\n")

        line_height = metrics.height()
        max_width = max(metrics.boundingRect(line).width() for line in lines)
        total_height = line_height * len(lines)

        padding = 2

        # background rectangle
        bg_rect = QRectF(
            x - padding,
            y - total_height - padding,
            max_width + 2 * padding,
            total_height + 2 * padding
        )

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(bg_rect)

        # Draw each text line
        painter.setPen(QPen(text_color, 0.8))
        first_line_y = y - total_height + metrics.ascent()

        for i, line in enumerate(lines):
            painter.drawText(int(x), int(first_line_y + i * line_height), line)

    
    def draw_dimension_arrow(self, painter, x1, y1, x2, y2, text, horizontal=True, offset=0, text_offset=0, draw_extensions=True, extension_direction='down', extension_end_y=None):
        """dimension line with arrows and text with extension lines"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        
        ext_len = 6
        if horizontal:
            painter.drawLine(QPointF(x1, y1 - ext_len), QPointF(x1, y1 + ext_len))
            painter.drawLine(QPointF(x2, y2 - ext_len), QPointF(x2, y2 + ext_len))
        else:
            painter.drawLine(QPointF(x1 - ext_len, y1), QPointF(x1 + ext_len, y1))
            painter.drawLine(QPointF(x2 - ext_len, y2), QPointF(x2 + ext_len, y2))
        
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        if horizontal:
            left_arrow = [
                QPointF(x1, y1),
                QPointF(x1 + arrow_size, y1 - arrow_size/2),
                QPointF(x1 + arrow_size, y1 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(left_arrow))
            
            right_arrow = [
                QPointF(x2, y2),
                QPointF(x2 - arrow_size, y2 - arrow_size/2),
                QPointF(x2 - arrow_size, y2 + arrow_size/2)
            ]
            painter.drawPolygon(QPolygonF(right_arrow))
            
            if draw_extensions:
                painter.setPen(QPen(QColor(100, 100, 100), 0.8, Qt.DotLine))
                
                if extension_end_y is not None:
                    # Draw extension lines to specified y coordinate
                    if extension_direction == 'up':
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, extension_end_y))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, extension_end_y))
                    else:
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, extension_end_y))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, extension_end_y))
                else:
                    extension_length = 40
                    if extension_direction == 'up':
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 - extension_length))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 - extension_length))
                    else:
                        painter.drawLine(QPointF(x1, y1), QPointF(x1, y1 + extension_length))
                        painter.drawLine(QPointF(x2, y2), QPointF(x2, y2 + extension_length))