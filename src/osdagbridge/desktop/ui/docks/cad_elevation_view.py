"""
Elevation View CAD Widget for OsdagBridge
Handles elevation (side) view rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF
from PySide6.QtGui import QPixmap
import random

class ElevationViewCADWidget(QWidget):
    """Widget for drawing bridge elevation (side) view"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # enable mouse tracking for hover
        
        # elevation view hover tracking 
        self.elevation_hover_zones = []  # list of (QRectF, element_type)
        self.hovered_elevation_element = None
        
        # Zoom level for this widget
        self.zoom_level = 1.0
        
        # Scale factor for diagram size
        self.scale_factor = 1.0
        
        # Setup zoom controls inside this widget
        self.setup_zoom_controls()
        
        # Track scroll area for fixed button positioning
        self.scroll_area = None
        
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
            'load_position_ratio': 0.5,
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

        self.setMinimumSize(400, 300)
    
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
        self.zoom_in_btn.hide()
        
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
        self.zoom_out_btn.hide()
        
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
        self.zoom_reset_btn.hide()
        
        self.setMinimumSize(400, 300)
    
    def _position_zoom_buttons(self):
        """Lock zoom buttons to fixed viewport position"""
        if not hasattr(self, 'zoom_in_btn'):
            return

        if self.scroll_area is None:
            parent = self.parent()
            while parent:
                if isinstance(parent, QScrollArea):
                    self.scroll_area = parent
                    break
                parent = parent.parent()

        if not self.scroll_area:
            return

        viewport = self.scroll_area.viewport()
        
        if not viewport or viewport.width() == 0:
            return
        
        if self.zoom_in_btn.parent() != viewport:
            self.zoom_in_btn.setParent(viewport)
            self.zoom_out_btn.setParent(viewport)
            self.zoom_reset_btn.setParent(viewport)

        margin = 10
        x = viewport.width() - 50
        y = margin

        self.zoom_in_btn.move(x + 10, y)
        self.zoom_out_btn.move(x + 10, y + 30)
        self.zoom_reset_btn.move(x, y + 60)

        self.zoom_in_btn.show()
        self.zoom_out_btn.show()
        self.zoom_reset_btn.show()
        self.zoom_in_btn.raise_()
        self.zoom_out_btn.raise_()
        self.zoom_reset_btn.raise_()

    def zoom_in(self):
        self.zoom_level *= 1.1
        self._update_widget_size()
        self.update()

    def zoom_out(self):
        self.zoom_level /= 1.1
        self._update_widget_size()
        self.update()

    def zoom_reset(self):
        self.zoom_level = 1.0
        self._update_widget_size()
        self.update()

    def _update_widget_size(self):
        """Update widget size based on zoom level"""
        base_width = 800
        base_height = 600
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
        """Update parameters from the model"""
        self.params.update(params)
        self.update()

    def _to_float(self, value, default=None):
        try:
            if value is None:
                return default
            if isinstance(value, str) and not value.strip():
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _draw_downward_load_arrow(self, painter, x, y_top, y_bottom, color):
        painter.setPen(QPen(color, 1.6))
        painter.drawLine(QPointF(x, y_top), QPointF(x, y_bottom))
        arrow_size = 5
        painter.setBrush(QBrush(color))
        arrow = [
            QPointF(x, y_bottom),
            QPointF(x - arrow_size / 2, y_bottom - arrow_size),
            QPointF(x + arrow_size / 2, y_bottom - arrow_size),
        ]
        painter.drawPolygon(QPolygonF(arrow))

    def _draw_label_with_bg(self, painter, x, y, text,
                            bg_color=QColor(232, 241, 255, 230),
                            text_color=QColor(45, 92, 170)):
        font = QFont('Arial', 9, QFont.Bold)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(text)
        pad = 3

        bg_rect = QRectF(
            x - pad,
            y - text_rect.height() - pad,
            text_rect.width() + 2 * pad,
            text_rect.height() + 2 * pad,
        )

        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(bg_color))
        painter.drawRect(bg_rect)
        painter.setPen(QPen(text_color, 1.0))
        painter.drawText(int(x), int(y), text)
        painter.restore()

    def draw_elevation_live_load(self, painter, start_x, span_px, deck_top_y, base_y, span_length_m):
        """Draw live-load position over the elevation view span."""
        if not self.params.get('show_live_load', True):
            return

        if span_length_m <= 0:
            return

        load_case = str(self.params.get('load_case_label', 'LL')).strip() or 'LL'
        load_type = str(self.params.get('load_type', 'Point')).strip().lower()
        load_color = QColor(45, 92, 170)

        arrow_top_y = deck_top_y - 48
        arrow_bottom_y = deck_top_y + 2
        reference_line_y = base_y + 28

        painter.save()
        painter.setPen(QPen(load_color, 1.5))
        painter.setBrush(QBrush(load_color))

        if load_type in {'line', 'area'}:
            start_m = self._to_float(self.params.get('load_line_start_m'))
            end_m = self._to_float(self.params.get('load_line_end_m'))

            if start_m is None or end_m is None:
                center_m = self._to_float(self.params.get('load_position_m'), span_length_m * 0.5)
                half_window = max(0.1, span_length_m * 0.1)
                start_m = center_m - half_window
                end_m = center_m + half_window

            start_m = max(0.0, min(span_length_m, start_m))
            end_m = max(0.0, min(span_length_m, end_m))
            if end_m < start_m:
                start_m, end_m = end_m, start_m

            load_start_x = start_x + (start_m / span_length_m) * span_px
            load_end_x = start_x + (end_m / span_length_m) * span_px

            if abs(load_end_x - load_start_x) < 8:
                load_end_x = min(start_x + span_px, load_start_x + 8)

            painter.drawLine(QPointF(load_start_x, arrow_top_y), QPointF(load_end_x, arrow_top_y))

            arrow_count = max(3, min(8, int(abs(load_end_x - load_start_x) / 80.0) + 1))
            if arrow_count == 1:
                x_positions = [(load_start_x + load_end_x) * 0.5]
            else:
                x_positions = [
                    load_start_x + (load_end_x - load_start_x) * i / (arrow_count - 1)
                    for i in range(arrow_count)
                ]

            for x_pos in x_positions:
                self._draw_downward_load_arrow(painter, x_pos, arrow_top_y, arrow_bottom_y, load_color)

            mid_x = (load_start_x + load_end_x) * 0.5
            painter.setPen(QPen(load_color, 1.0, Qt.DashLine))
            painter.drawLine(QPointF(mid_x, deck_top_y + 2), QPointF(mid_x, reference_line_y))
            self._draw_label_with_bg(
                painter,
                mid_x - 80,
                arrow_top_y - 10,
                f"{load_case} {load_type.title()}: {start_m:.2f} m to {end_m:.2f} m",
            )
        else:
            load_position_m = self._to_float(self.params.get('load_position_m'))
            if load_position_m is None:
                ratio = self._to_float(self.params.get('load_position_ratio'), 0.5)
                ratio = max(0.0, min(1.0, ratio))
                load_position_m = span_length_m * ratio

            load_position_m = max(0.0, min(span_length_m, load_position_m))
            load_x = start_x + (load_position_m / span_length_m) * span_px

            self._draw_downward_load_arrow(painter, load_x, arrow_top_y, arrow_bottom_y, load_color)
            painter.setPen(QPen(load_color, 1.0, Qt.DashLine))
            painter.drawLine(QPointF(load_x, deck_top_y + 2), QPointF(load_x, reference_line_y))
            self._draw_label_with_bg(
                painter,
                load_x - 58,
                arrow_top_y - 10,
                f"{load_case} @ {load_position_m:.2f} m",
            )

        painter.restore()
    
    def paintEvent(self, event):
        """Paint the elevation view"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(255, 255, 255))
            self.draw_elevation(painter)
        except Exception as e:
            print(f"ELEVATION VIEW PAINT ERROR: {repr(e)}")
        finally:
            painter.end()
    
    def draw_elevation(self, painter):
        """Draw the elevation (side) view of the bridge"""
        
        span_length = self.params.get('span_length', 35000)  # mm
        num_girders = self.params.get('num_girders', 4)
        girder_depth = self.girder['depth']
        deck_thickness = self.params.get('deck_thickness', 200)
        footpath_thickness = self.params.get('footpath_thickness', 200)
        railing_height = self.params.get('railing_height', 1000)
        crash_barrier_height = self.crash_barrier['height']
        
        # Dimensions
        base_width = 800 * self.zoom_level * self.scale_factor
        base_height = 600 * self.zoom_level * self.scale_factor
        
        margin = 50
        span_px = (span_length / 1000.0) * (base_width - 2*margin) / (span_length / 1000.0)  # span in pixels
        
        # Scale span to fit
        available_width = base_width - 2*margin
        if span_length > 0:
            span_scale = available_width / (span_length / 1000.0)  # pixels per meter
        else:
            span_scale = 100
        
        # Calculate heights in pixels
        girder_depth_px = girder_depth * 0.15  # visual scale
        deck_thick_px = deck_thickness * 0.2
        railing_height_px = railing_height * 0.08
        
        # Position bridge in center
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        span_length_m = span_length / 1000.0
        span_px = span_length_m * span_scale
        
        # Base line (ground/support level)
        base_y = center_y + 50
        
        # Girder top level
        girder_top_y = base_y - girder_depth_px
        
        # Deck bottom (just above girder)
        deck_bottom_y = girder_top_y
        
        # Deck top
        deck_top_y = deck_bottom_y - deck_thick_px
        
        # Start x position (left end)
        start_x = center_x - span_px / 2
        
        # Draw supports (bearings) at ends and middle
        support_diameter = 15
        num_supports = min(3, num_girders)  # Supports at ends and optionally middle
        support_positions = []
        
        if num_supports == 2:
            support_positions = [start_x, start_x + span_px]
        elif num_supports >= 3:
            support_positions = [start_x, center_x, start_x + span_px]
        
        # Draw supports
        for sup_x in support_positions:
            # Bearing (red circle)
            painter.setBrush(QBrush(QColor(200, 50, 50)))
            painter.setPen(QPen(QColor(100, 0, 0), 1.5))
            painter.drawEllipse(QPointF(sup_x, base_y), support_diameter, support_diameter)
            
            # Support column
            painter.setPen(QPen(QColor(80, 80, 80), 2))
            painter.drawLine(QPointF(sup_x, base_y), QPointF(sup_x, base_y + 30))
        
        # Draw girders (side elevation - shown as rectangles)
        girder_color = QColor(179, 180, 160)
        painter.setBrush(QBrush(girder_color))
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        
        # Main girder outline
        painter.drawRect(QRectF(start_x, girder_top_y, span_px, girder_depth_px))
        
        # Draw parabolic curve for bridge sagging (if tension)
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        
        # Optional: draw cable or sag pattern
        path_points = []
        sag = girder_depth_px * 0.1  # Small sag
        for i in range(int(span_px) + 1):
            x = start_x + i
            # Parabolic equation
            t = i / span_px if span_px > 0 else 0
            y = girder_top_y - sag * 4 * t * (1 - t)
            path_points.append(QPointF(x, y))
        
        # Draw deck slab
        deck_color = QColor(225, 225, 225)
        painter.setBrush(QBrush(deck_color))
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        painter.drawRect(QRectF(start_x, deck_top_y, span_px, deck_thick_px))
        
        # Draw railing
        railing_color = QColor(126, 126, 126)
        painter.setBrush(QBrush(railing_color))
        painter.setPen(QPen(QColor(50, 50, 50), 1.5))
        
        # Left railing
        painter.drawRect(QRectF(start_x - 10, deck_top_y - railing_height_px, 10, railing_height_px))
        
        # Right railing
        painter.drawRect(QRectF(start_x + span_px, deck_top_y - railing_height_px, 10, railing_height_px))

        self.draw_elevation_live_load(
            painter,
            start_x,
            span_px,
            deck_top_y,
            base_y,
            span_length_m,
        )
        
        # Draw dimensions
        self.draw_elevation_dimensions(painter, start_x, span_px, base_y, deck_top_y, 
                                      girder_top_y, railing_height_px, girder_depth_px, span_length_m)
    
    def draw_elevation_dimensions(self, painter, start_x, span_px, base_y, deck_top_y, 
                                girder_top_y, railing_height_px, girder_depth_px, span_length_m):
        """Draw dimensions for the elevation view"""
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        
        # Span dimension
        dim_y = base_y + 40
        painter.drawLine(QPointF(start_x, dim_y), QPointF(start_x + span_px, dim_y))
        
        # Arrow heads
        arrow_size = 4
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        left_arrow = [QPointF(start_x, dim_y), QPointF(start_x + arrow_size, dim_y - arrow_size/2),
                     QPointF(start_x + arrow_size, dim_y + arrow_size/2)]
        painter.drawPolygon(QPolygonF(left_arrow))
        
        right_arrow = [QPointF(start_x + span_px, dim_y), 
                      QPointF(start_x + span_px - arrow_size, dim_y - arrow_size/2),
                      QPointF(start_x + span_px - arrow_size, dim_y + arrow_size/2)]
        painter.drawPolygon(QPolygonF(right_arrow))
        
        # Dimension text
        font = QFont('Arial', 10, QFont.Bold)
        painter.setFont(font)
        text = f"Span = {span_length_m:.2f} m"
        painter.drawText(int(start_x + span_px/2 - 30), int(dim_y + 20), text)
        
        # Girder height dimension
        painter.setPen(QPen(QColor(0, 0, 0), 0.8))
        dim_x = start_x - 35
        painter.drawLine(QPointF(dim_x, girder_top_y), QPointF(dim_x, base_y))
        
        # Height dimension text
        girder_height_mm = self.girder['depth']
        text = f"h = {girder_height_mm:.0f} mm"
        painter.drawText(int(dim_x - 50), int(girder_top_y + girder_depth_px/2), text)