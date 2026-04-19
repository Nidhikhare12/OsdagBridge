"""
3D View CAD Widget for OsdagBridge
Handles basic 3D isometric rendering of bridge structures
Author: Arushi
"""

import math
from PySide6.QtWidgets import QWidget, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF

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
        self.rotation_x = 0   # degrees (tilt)
        self.rotation_y = 0   # degrees (roll)
        self.rotation_z = 0   # degrees

        # Interactive navigation state
        self._is_rotating = False
        self._is_panning = False
        self._last_mouse_pos = None
        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0

        # 3D orbit center (updated from active bridge geometry)
        self._orbit_center = (0.0, 0.0, 0.0)
        
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
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0
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

    def _to_float(self, value, default):
        try:
            if value is None:
                return float(default)
            if isinstance(value, str) and not value.strip():
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _to_int(self, value, default):
        try:
            if value is None:
                return int(default)
            if isinstance(value, str) and not value.strip():
                return int(default)
            return int(float(value))
        except (TypeError, ValueError):
            return int(default)

    def _compute_deck_total_width(self):
        carriageway = self._to_float(self.params.get('carriageway_width'), 10500.0)
        crash_barrier = self._to_float(self.params.get('crash_barrier_width'), 500.0)
        footpath_width = self._to_float(self.params.get('footpath_width'), 1500.0)
        fp_config = str(self.params.get('footpath_config', 'both')).strip().lower()
        median_present = bool(self.params.get('median_present', False))
        median_width = self._to_float(self.params.get('median_width'), 1200.0)

        if fp_config == 'both':
            num_fp = 2
        elif fp_config in {'left', 'right'}:
            num_fp = 1
        else:
            num_fp = 0

        if median_present:
            return carriageway * 2.0 + median_width + 2.0 * crash_barrier + num_fp * footpath_width
        return carriageway + 2.0 * crash_barrier + num_fp * footpath_width

    def _rotate_point(self, x, y, z):
        """Rotate point around current orbit center using X/Y/Z Euler angles."""
        cx, cy, cz = self._orbit_center
        px = x - cx
        py = y - cy
        pz = z - cz

        rx = math.radians(self.rotation_x)
        ry = math.radians(self.rotation_y)
        rz = math.radians(self.rotation_z)

        # Rotate around X axis
        py, pz = (
            py * math.cos(rx) - pz * math.sin(rx),
            py * math.sin(rx) + pz * math.cos(rx),
        )

        # Rotate around Y axis
        px, pz = (
            px * math.cos(ry) + pz * math.sin(ry),
            -px * math.sin(ry) + pz * math.cos(ry),
        )

        # Rotate around Z axis
        px, py = (
            px * math.cos(rz) - py * math.sin(rz),
            px * math.sin(rz) + py * math.cos(rz),
        )

        return px + cx, py + cy, pz + cz

    def _iso_raw(self, x, y, z):
        x, y, z = self._rotate_point(x, y, z)
        return (
            (x - y) * 0.8660254037844386,
            z - 0.5 * (x + y),
        )

    def _configure_projection(self, points_3d):
        if not points_3d:
            self._iso_scale = 1.0
            self._iso_ref_x = 0.0
            self._iso_ref_y = 0.0
            self._iso_center_x = self.width() * 0.5
            self._iso_center_y = self.height() * 0.5
            return

        raw = [self._iso_raw(x, y, z) for x, y, z in points_3d]
        min_x = min(p[0] for p in raw)
        max_x = max(p[0] for p in raw)
        min_y = min(p[1] for p in raw)
        max_y = max(p[1] for p in raw)

        span_x = max(1.0, max_x - min_x)
        span_y = max(1.0, max_y - min_y)

        padding = 42.0
        avail_w = max(80.0, self.width() - 2.0 * padding)
        avail_h = max(80.0, self.height() - 2.0 * padding)
        fit_scale = min(avail_w / span_x, avail_h / span_y)

        self._iso_scale = max(0.001, fit_scale * self.zoom_level * self.scale_factor)
        self._iso_ref_x = 0.5 * (min_x + max_x)
        self._iso_ref_y = 0.5 * (min_y + max_y)
        self._iso_center_x = self.width() * 0.5
        self._iso_center_y = self.height() * 0.5

    def _poly3d(self, points_3d):
        return QPolygonF([
            QPointF(*self.isometric_project(x, y, z))
            for x, y, z in points_3d
        ])

    def _draw_prism(self, painter, x1, x2, y1, y2, z1, z2, color):
        x_low, x_high = sorted((x1, x2))
        y_low, y_high = sorted((y1, y2))
        z_low, z_high = sorted((z1, z2))

        side_face = [
            (x_high, y_low, z_low),
            (x_high, y_high, z_low),
            (x_high, y_high, z_high),
            (x_high, y_low, z_high),
        ]
        flank_face = [
            (x_low, y_high, z_low),
            (x_high, y_high, z_low),
            (x_high, y_high, z_high),
            (x_low, y_high, z_high),
        ]
        top_face = [
            (x_low, y_low, z_high),
            (x_high, y_low, z_high),
            (x_high, y_high, z_high),
            (x_low, y_high, z_high),
        ]

        painter.save()
        painter.setPen(QPen(QColor(58, 58, 58), 1.0))

        painter.setBrush(QBrush(color.darker(124)))
        painter.drawPolygon(self._poly3d(flank_face))

        painter.setBrush(QBrush(color.darker(110)))
        painter.drawPolygon(self._poly3d(side_face))

        painter.setBrush(QBrush(color.lighter(108)))
        painter.drawPolygon(self._poly3d(top_face))
        painter.restore()
    
    def paintEvent(self, event):
        """Paint the 3D view"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(self.rect(), QColor(240, 245, 250))
            self.draw_3d_view(painter)

            # Quick interaction hint for users.
            painter.setPen(QPen(QColor(90, 90, 90), 1))
            painter.setFont(QFont('Arial', 8))
            painter.drawText(10, 16, "Drag: rotate | Right-drag: pan | Wheel: zoom")
        except Exception as e:
            print(f"3D VIEW PAINT ERROR: {repr(e)}")
        finally:
            painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_rotating = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() in (Qt.RightButton, Qt.MiddleButton):
            self._is_panning = True
            self._last_mouse_pos = event.position()
            self.setCursor(Qt.SizeAllCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._last_mouse_pos is None:
            super().mouseMoveEvent(event)
            return

        if self._is_rotating or self._is_panning:
            pos = event.position()
            dx = pos.x() - self._last_mouse_pos.x()
            dy = pos.y() - self._last_mouse_pos.y()

            if self._is_rotating:
                self.rotation_z += dx * 0.35
                self.rotation_x += dy * 0.35
                self.rotation_x = max(-80.0, min(80.0, self.rotation_x))
                self.update()
            elif self._is_panning:
                self.pan_offset_x += dx
                self.pan_offset_y += dy
                self.update()

            self._last_mouse_pos = pos
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_rotating = False
        elif event.button() in (Qt.RightButton, Qt.MiddleButton):
            self._is_panning = False

        if not self._is_rotating and not self._is_panning:
            self._last_mouse_pos = None
            self.setCursor(Qt.ArrowCursor)

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_in()
        elif delta < 0:
            self.zoom_out()
        event.accept()
    
    def isometric_project(self, x, y, z):
        """Convert 3D coordinates to 2D isometric projection
        x: along span, y: across width, z: vertical
        Returns (screen_x, screen_y)
        """
        raw_x, raw_y = self._iso_raw(x, y, z)
        scale = getattr(self, '_iso_scale', 1.0)
        ref_x = getattr(self, '_iso_ref_x', 0.0)
        ref_y = getattr(self, '_iso_ref_y', 0.0)
        center_x = getattr(self, '_iso_center_x', self.width() * 0.5)
        center_y = getattr(self, '_iso_center_y', self.height() * 0.5)
        return (
            center_x + (raw_x - ref_x) * scale + self.pan_offset_x,
            center_y + (raw_y - ref_y) * scale + self.pan_offset_y,
        )
    
    def draw_3d_view(self, painter):
        """Draw a 3D isometric bridge with connected members."""

        span_length = max(5000.0, self._to_float(self.params.get('span_length'), 35000.0))
        num_girders = max(1, self._to_int(self.params.get('num_girders'), 4))
        carriageway_width = max(4000.0, self._to_float(self.params.get('carriageway_width'), 10500.0))
        deck_thickness = max(120.0, self._to_float(self.params.get('deck_thickness'), 200.0))
        deck_overhang = max(300.0, self._to_float(self.params.get('deck_overhang'), 1000.0))
        cross_bracing_spacing = max(1000.0, self._to_float(self.params.get('cross_bracing_spacing'), 3500.0))

        footpath_width = max(0.0, self._to_float(self.params.get('footpath_width'), 1500.0))
        fp_config = str(self.params.get('footpath_config', 'both')).strip().lower()
        if fp_config == 'both':
            left_fp = footpath_width
            right_fp = footpath_width
        elif fp_config == 'left':
            left_fp = footpath_width
            right_fp = 0.0
        elif fp_config == 'right':
            left_fp = 0.0
            right_fp = footpath_width
        else:
            left_fp = 0.0
            right_fp = 0.0

        crash_barrier_w = max(300.0, self._to_float(self.params.get('crash_barrier_width'), 500.0))
        crash_barrier_h = max(450.0, self._to_float(self.crash_barrier.get('height'), 800.0))
        median_present = bool(self.params.get('median_present', False))
        median_width = max(600.0, self._to_float(self.params.get('median_width'), 1200.0))

        deck_total_width = max(carriageway_width + 2.0 * crash_barrier_w, self._compute_deck_total_width())

        visual = self.girder_visual_scale
        girder_depth = max(450.0, self._to_float(self.girder.get('depth'), 500.0) * visual['depth'])

        if 'top_flange_width' in self.girder and 'bottom_flange_width' in self.girder:
            bf_top = self._to_float(self.girder.get('top_flange_width'), 180.0) * visual['flange_width']
            tf_top = self._to_float(self.girder.get('top_flange_thickness'), 17.2) * visual['flange_thickness']
            bf_bottom = self._to_float(self.girder.get('bottom_flange_width'), 180.0) * visual['flange_width']
            tf_bottom = self._to_float(self.girder.get('bottom_flange_thickness'), 17.2) * visual['flange_thickness']
        else:
            bf_top = bf_bottom = self._to_float(self.girder.get('flange_width'), 180.0) * visual['flange_width']
            tf_top = tf_bottom = self._to_float(self.girder.get('flange_thickness'), 17.2) * visual['flange_thickness']

        tw = self._to_float(self.girder.get('web_thickness'), 10.2) * visual['web_thickness']

        tw = max(25.0, tw)
        tf_top = max(40.0, tf_top)
        tf_bottom = max(40.0, tf_bottom)
        bf_top = max(tw * 3.0, bf_top)
        bf_bottom = max(tw * 3.0, bf_bottom)
        girder_depth = max(girder_depth, tf_top + tf_bottom + 180.0)

        z_girder_bottom = 0.0
        z_girder_top = girder_depth
        z_deck_bottom = z_girder_top
        z_deck_top = z_deck_bottom + deck_thickness
        z_support_bottom = -max(600.0, girder_depth * 0.70)

        # Keep rotations centered around bridge mass rather than world origin.
        self._orbit_center = (
            0.5 * span_length,
            0.5 * deck_total_width,
            0.5 * (z_support_bottom + z_deck_top),
        )

        if num_girders > 1:
            usable_overhang = min(deck_overhang, deck_total_width * 0.35)
            y_first = usable_overhang
            y_last = deck_total_width - usable_overhang
            if y_last <= y_first:
                y_first = deck_total_width * 0.2
                y_last = deck_total_width * 0.8
            spacing = (y_last - y_first) / (num_girders - 1)
            girder_ys = [y_first + i * spacing for i in range(num_girders)]
        else:
            girder_ys = [deck_total_width * 0.5]

        fit_points = [
            (-0.08 * span_length, -0.15 * deck_total_width, z_support_bottom),
            (1.08 * span_length, -0.15 * deck_total_width, z_support_bottom),
            (1.08 * span_length, 1.15 * deck_total_width, z_deck_top + crash_barrier_h),
            (-0.08 * span_length, 1.15 * deck_total_width, z_deck_top + crash_barrier_h),
        ]
        for gy in girder_ys:
            half_w = max(bf_top, bf_bottom) * 0.5
            fit_points.extend([
                (0.0, gy - half_w, z_girder_bottom),
                (span_length, gy + half_w, z_girder_top),
            ])
        self._configure_projection(fit_points)

        ground_color = QColor(210, 210, 192)
        ground_poly = self._poly3d([
            (-0.03 * span_length, -0.08 * deck_total_width, z_support_bottom),
            (1.03 * span_length, -0.08 * deck_total_width, z_support_bottom),
            (1.03 * span_length, 1.08 * deck_total_width, z_support_bottom),
            (-0.03 * span_length, 1.08 * deck_total_width, z_support_bottom),
        ])
        painter.save()
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(ground_color, 1, Qt.DashLine))
        painter.drawPolygon(ground_poly)
        painter.restore()

        girder_color = QColor(179, 180, 160)
        for gy in girder_ys:
            self._draw_prism(
                painter,
                0.0,
                span_length,
                gy - bf_bottom * 0.5,
                gy + bf_bottom * 0.5,
                z_girder_bottom,
                z_girder_bottom + tf_bottom,
                girder_color,
            )
            self._draw_prism(
                painter,
                0.0,
                span_length,
                gy - tw * 0.5,
                gy + tw * 0.5,
                z_girder_bottom + tf_bottom,
                z_girder_top - tf_top,
                girder_color.darker(120),
            )
            self._draw_prism(
                painter,
                0.0,
                span_length,
                gy - bf_top * 0.5,
                gy + bf_top * 0.5,
                z_girder_top - tf_top,
                z_girder_top,
                girder_color,
            )

        if num_girders > 1:
            y_min = min(girder_ys) - bf_bottom * 0.5
            y_max = max(girder_ys) + bf_bottom * 0.5
            dia_thickness = max(80.0, tw * 1.8)
            dia_color = QColor(134, 134, 100)
            for x_anchor in (0.0, span_length):
                self._draw_prism(
                    painter,
                    x_anchor - dia_thickness * 0.5,
                    x_anchor + dia_thickness * 0.5,
                    y_min,
                    y_max,
                    z_girder_bottom + tf_bottom,
                    z_girder_top - tf_top,
                    dia_color,
                )

        deck_color = QColor(225, 225, 225)
        self._draw_prism(
            painter,
            0.0,
            span_length,
            0.0,
            deck_total_width,
            z_deck_bottom,
            z_deck_top,
            deck_color,
        )

        barrier_color = QColor(126, 126, 126)
        left_barrier_start = left_fp
        left_barrier_end = left_barrier_start + crash_barrier_w
        right_barrier_end = deck_total_width - right_fp
        right_barrier_start = right_barrier_end - crash_barrier_w

        if left_barrier_end > left_barrier_start:
            self._draw_prism(
                painter,
                0.0,
                span_length,
                left_barrier_start,
                left_barrier_end,
                z_deck_top,
                z_deck_top + crash_barrier_h,
                barrier_color,
            )

        if right_barrier_end > right_barrier_start:
            self._draw_prism(
                painter,
                0.0,
                span_length,
                right_barrier_start,
                right_barrier_end,
                z_deck_top,
                z_deck_top + crash_barrier_h,
                barrier_color,
            )

        if median_present:
            median_start = left_fp + crash_barrier_w + carriageway_width
            median_end = median_start + median_width
            median_barrier_w = min(crash_barrier_w, max(120.0, (median_end - median_start) * 0.48))
            if median_end > median_start + 2.0 * median_barrier_w:
                self._draw_prism(
                    painter,
                    0.0,
                    span_length,
                    median_start,
                    median_start + median_barrier_w,
                    z_deck_top,
                    z_deck_top + crash_barrier_h,
                    QColor(150, 150, 150),
                )
                self._draw_prism(
                    painter,
                    0.0,
                    span_length,
                    median_end - median_barrier_w,
                    median_end,
                    z_deck_top,
                    z_deck_top + crash_barrier_h,
                    QColor(150, 150, 150),
                )

        if num_girders > 1:
            z_bracing_low = z_girder_bottom + tf_bottom + max(20.0, 0.08 * girder_depth)
            z_bracing_high = z_girder_top - tf_top - max(20.0, 0.08 * girder_depth)
            if z_bracing_high <= z_bracing_low:
                z_mid = 0.5 * (z_bracing_low + z_bracing_high)
                z_bracing_low = z_mid - 20.0
                z_bracing_high = z_mid + 20.0

            bracing_x = []
            x_cursor = cross_bracing_spacing
            while x_cursor < span_length - 0.35 * cross_bracing_spacing and len(bracing_x) < 12:
                bracing_x.append(x_cursor)
                x_cursor += cross_bracing_spacing
            if not bracing_x:
                bracing_x = [span_length * 0.5]

            painter.save()
            painter.setPen(QPen(QColor(235, 236, 211), 1.4))
            for bx in bracing_x:
                for i in range(len(girder_ys) - 1):
                    y1 = girder_ys[i]
                    y2 = girder_ys[i + 1]
                    p1 = self.isometric_project(bx, y1, z_bracing_low)
                    p2 = self.isometric_project(bx, y2, z_bracing_high)
                    p3 = self.isometric_project(bx, y1, z_bracing_high)
                    p4 = self.isometric_project(bx, y2, z_bracing_low)
                    painter.drawLine(QPointF(p1[0], p1[1]), QPointF(p2[0], p2[1]))
                    painter.drawLine(QPointF(p3[0], p3[1]), QPointF(p4[0], p4[1]))
            painter.restore()

        painter.save()
        painter.setPen(QPen(QColor(85, 85, 85), 2.0))
        painter.setBrush(QBrush(QColor(210, 70, 70)))
        bearing_radius = max(2.0, 4.0 * self.zoom_level)
        for x_anchor in (0.0, span_length):
            for gy in girder_ys:
                top = self.isometric_project(x_anchor, gy, z_girder_bottom)
                bottom = self.isometric_project(x_anchor, gy, z_support_bottom)
                painter.drawLine(QPointF(top[0], top[1]), QPointF(bottom[0], bottom[1]))
                painter.drawEllipse(QPointF(top[0], top[1]), bearing_radius, bearing_radius)
        painter.restore()

        axis_length = max(1800.0, min(4200.0, span_length * 0.12))
        self.draw_3d_axes(
            painter,
            origin=(-0.04 * span_length, -0.08 * deck_total_width, z_support_bottom + 80.0),
            axis_length=axis_length,
        )
    
    def draw_3d_axes(self, painter, origin=(0.0, 0.0, 0.0), axis_length=3000.0):
        """Draw 3D coordinate axes for reference."""
        ox, oy, oz = origin
        origin_2d = self.isometric_project(ox, oy, oz)
        x_end = self.isometric_project(ox + axis_length, oy, oz)
        y_end = self.isometric_project(ox, oy + axis_length, oz)
        z_end = self.isometric_project(ox, oy, oz + axis_length)
        
        # X-axis (red)
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(QPointF(origin_2d[0], origin_2d[1]), QPointF(x_end[0], x_end[1]))
        
        # Y-axis (green)
        painter.setPen(QPen(QColor(0, 180, 0), 2))
        painter.drawLine(QPointF(origin_2d[0], origin_2d[1]), QPointF(y_end[0], y_end[1]))
        
        # Z-axis (blue)
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.drawLine(QPointF(origin_2d[0], origin_2d[1]), QPointF(z_end[0], z_end[1]))
        
        # Labels
        font = QFont('Arial', 8)
        painter.setFont(font)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawText(int(x_end[0] + 5), int(x_end[1]), "X")
        painter.drawText(int(y_end[0]), int(y_end[1] + 10), "Y")
        painter.drawText(int(z_end[0] + 5), int(z_end[1] - 5), "Z")