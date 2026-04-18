"""
3D View CAD Widget for OsdagBridge
Handles basic 3D isometric rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPolygon

class Bridge3DCADWidget(QWidget):
    """Widget for drawing a basic 3D isometric view of the bridge"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # 3D view hover tracking 
        self.view_3d_hover_zones = []
        self.hovered_3d_element = None
        
        # Zoom level for this widget
        self.zoom_level = 1.0
        
        # Scale factor for diagram size
        self.scale_factor = 1.0
        
        # Setup zoom controls
        self.setup_zoom_controls()
        
        # Track scroll area for fixed button positioning
        self.scroll_area = None
        
        # Rotation angles (for interactive rotation - stored for future use)
        self.rotation_x = 25  # degrees
        self.rotation_y = 45  # degrees
        self.rotation_z = 0   # degrees
        
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
    
    def paintEvent(self, event):
        """Paint the 3D view"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(240, 245, 250))
            self.draw_3d_view(painter)
        except Exception as e:
            print(f"3D VIEW PAINT ERROR: {repr(e)}")
        finally:
            painter.end()
    
    def isometric_project(self, x, y, z):
        """Convert 3D coordinates to 2D isometric projection
        x: along span, y: across width, z: vertical
        Returns (screen_x, screen_y)
        """
        # Isometric angles
        iso_scale = 0.3 * self.zoom_level * self.scale_factor
        
        # Isometric projection formulas
        screen_x = (x - y) * iso_scale * 0.866  # cos(30°) for X-axis
        screen_y = z * iso_scale - (x + y) * iso_scale * 0.5  # sin(30°) for Y-axis
        
        # Center on screen
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        return (center_x + screen_x, center_y + screen_y)
    
    def draw_3d_view(self, painter):
        """Draw a 3D isometric view of the bridge"""
        
        span_length = self.params.get('span_length', 35000)  # mm
        num_girders = self.params.get('num_girders', 4)
        girder_spacing = self.params.get('girder_spacing', 2750)  # mm
        carriageway_width = self.params.get('carriageway_width', 10500)  # mm
        girder_depth = self.girder['depth']  # mm
        deck_thickness = self.params.get('deck_thickness', 200)  # mm
        
        # Draw ground plane (reference)
        ground_color = QColor(200, 200, 180)
        painter.setPen(QPen(ground_color, 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        
        # Define 3D corners of the ground plane (in mm)
        ground_points_3d = [
            (-5000, -5000, 0),
            (span_length + 5000, -5000, 0),
            (span_length + 5000, carriageway_width + 5000, 0),
            (-5000, carriageway_width + 5000, 0),
        ]
        
        # Project to 2D
        ground_points_2d = [self.isometric_project(x, y, z) for x, y, z in ground_points_3d]
        
        # Draw ground plane
        if len(ground_points_2d) >= 4:
            painter.setPen(QPen(ground_color, 1, Qt.DashLine))
            for i in range(len(ground_points_2d)):
                p1 = ground_points_2d[i]
                p2 = ground_points_2d[(i + 1) % len(ground_points_2d)]
                painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))
        
        # Draw girders
        girder_color = QColor(179, 180, 160)
        painter.setPen(QPen(QColor(60, 60, 60), 1.5))
        painter.setBrush(QBrush(girder_color))
        
        # Calculate girder positions
        if num_girders > 1:
            first_girder_x = 1000  # mm from start
            last_girder_x = span_length - 1000
            available_span = last_girder_x - first_girder_x
            actual_spacing = available_span / (num_girders - 1)
            positions = [first_girder_x + i * actual_spacing for i in range(num_girders)]
        else:
            positions = [span_length / 2]
        
        # Draw each girder as 3D box
        for gx in positions:
            # Girder bottom left-front
            p1 = self.isometric_project(gx, 500, 0)
            # Girder bottom right-front
            p2 = self.isometric_project(gx, carriageway_width - 500, 0)
            # Girder top right-front (with height)
            p3 = self.isometric_project(gx, carriageway_width - 500, girder_depth)
            # Girder top left-front
            p4 = self.isometric_project(gx, 500, girder_depth)
            
            # Draw front face
            girder_outline = QPolygon([
                QPointF(p1[0], p1[1]),
                QPointF(p2[0], p2[1]),
                QPointF(p3[0], p3[1]),
                QPointF(p4[0], p4[1]),
            ])
            painter.drawPolygon(girder_outline)
            
            # Draw edges from front to back (span direction)
            depth_back = 100
            # Back left edge
            pb1 = self.isometric_project(gx + depth_back, 500, 0)
            pb4 = self.isometric_project(gx + depth_back, 500, girder_depth)
            painter.drawLine(QPointF(p1[0], p1[1]), QPointF(pb1[0], pb1[1]))
            painter.drawLine(QPointF(p4[0], p4[1]), QPointF(pb4[0], pb4[1]))
        
        # Draw deck slab
        deck_color = QColor(225, 225, 225)
        painter.setPen(QPen(QColor(0, 0, 0), 1.5))
        painter.setBrush(QBrush(deck_color))
        
        # Deck top corners
        d_top_1 = self.isometric_project(0, 500, girder_depth + deck_thickness)
        d_top_2 = self.isometric_project(span_length, 500, girder_depth + deck_thickness)
        d_top_3 = self.isometric_project(span_length, carriageway_width - 500, girder_depth + deck_thickness)
        d_top_4 = self.isometric_project(0, carriageway_width - 500, girder_depth + deck_thickness)
        
        # Draw deck top rectangle
        deck_top = QPolygon([
            QPointF(d_top_1[0], d_top_1[1]),
            QPointF(d_top_2[0], d_top_2[1]),
            QPointF(d_top_3[0], d_top_3[1]),
            QPointF(d_top_4[0], d_top_4[1]),
        ])
        painter.drawPolygon(deck_top)
        
        # Draw supports/bearings at ends
        support_color = QColor(200, 50, 50)
        painter.setPen(QPen(QColor(100, 0, 0), 1.5))
        painter.setBrush(QBrush(support_color))
        
        for sx in [500, span_length - 500]:
            # Support column
            sup_top = self.isometric_project(sx, carriageway_width / 2, girder_depth + 50)
            sup_bottom = self.isometric_project(sx, carriageway_width / 2, -200)
            painter.drawLine(QPointF(sup_bottom[0], sup_bottom[1]), QPointF(sup_top[0], sup_top[1]))
            
            # Bearing (circle)
            bearing_center = self.isometric_project(sx, carriageway_width / 2, 0)
            painter.drawEllipse(QPointF(bearing_center[0], bearing_center[1]), 8, 8)
        
        # Draw coordinate axes (for reference)
        self.draw_3d_axes(painter)
    
    def draw_3d_axes(self, painter):
        """Draw 3D coordinate axes for reference"""
        origin = self.isometric_project(0, 0, 0)
        x_end = self.isometric_project(3000, 0, 0)
        y_end = self.isometric_project(0, 3000, 0)
        z_end = self.isometric_project(0, 0, 3000)
        
        # X-axis (red)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(QPointF(origin[0], origin[1]), QPointF(x_end[0], x_end[1]))
        
        # Y-axis (green)
        painter.setPen(QPen(QColor(0, 180, 0), 2))
        painter.drawLine(QPointF(origin[0], origin[1]), QPointF(y_end[0], y_end[1]))
        
        # Z-axis (blue)
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.drawLine(QPointF(origin[0], origin[1]), QPointF(z_end[0], z_end[1]))
        
        # Labels
        font = QFont('Arial', 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawText(int(x_end[0] + 5), int(x_end[1]), "X")
        painter.drawText(int(y_end[0]), int(y_end[1] + 10), "Y")
        painter.drawText(int(z_end[0] + 5), int(z_end[1] - 5), "Z")
