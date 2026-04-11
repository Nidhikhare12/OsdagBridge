from __future__ import annotations

import math
import numpy as np

# check for opengl support early on
try:
    import pyqtgraph.opengl as gl
    _HAS_GL = True
except Exception:
    _HAS_GL = False

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor


_DECK_RGBA     = (0.678, 0.769, 0.784, 0.95)
_GIRDER_RGBA   = (0.467, 0.533, 0.600, 1.00)
_LOAD_RGBA     = (0.827, 0.184, 0.184, 0.85)
_AREA_RGBA     = (0.827, 0.184, 0.184, 0.35)
_CONTACT_RGBA  = (0.1,   0.1,   0.1,   0.40)
_CONCRETE_RGBA = (0.749, 0.780, 0.796, 1.00)
_SUPPORT_RGBA  = (0.337, 0.420, 0.420, 1.00)
_EDGE_DARK     = (0.1,   0.1,   0.1,   1.0)
_EDGE_MID      = (0.2,   0.2,   0.2,   1.0)


# helpers to build basic 3d shapes
def _solid_box(x0, x1, y0, y1, z0, z1, color):
    verts = np.array([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ], dtype=np.float32)
    faces = np.array([
        [0,1,2],[0,2,3], [4,5,6],[4,6,7],
        [0,1,5],[0,5,4], [2,3,7],[2,7,6],
        [0,3,7],[0,7,4], [1,2,6],[1,6,5],
    ])
    colors = np.tile(color, (len(faces), 1)).astype(np.float32)
    return gl.GLMeshItem(
        vertexes=verts, faces=faces, faceColors=colors,
        smooth=False, drawEdges=True, edgeColor=_EDGE_DARK,
    )


def _cone(x, y, tip_z, height, radius, color, segments=20):
    base_z = tip_z + height
    angles = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    ring = np.column_stack([
        x + radius * np.cos(angles),
        y + radius * np.sin(angles),
        np.full(segments, base_z),
    ])
    tip_pt  = np.array([[x, y, tip_z]], dtype=np.float32)
    cap_ctr = np.array([[x, y, base_z]], dtype=np.float32)
    verts   = np.vstack([tip_pt, ring, cap_ctr]).astype(np.float32)
    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces.append([0, i + 1, nxt + 1])
        faces.append([segments + 1, nxt + 1, i + 1])
    clr = np.tile(color, (len(faces), 1)).astype(np.float32)
    return gl.GLMeshItem(vertexes=verts, faces=np.array(faces), faceColors=clr, smooth=True)


def _cylinder(x, y, z0, z1, radius, color, segments=12):
    angles  = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    cos_a   = np.cos(angles)
    sin_a   = np.sin(angles)
    bot_ring = np.column_stack([x + radius * cos_a, y + radius * sin_a, np.full(segments, z0)])
    top_ring = np.column_stack([x + radius * cos_a, y + radius * sin_a, np.full(segments, z1)])
    bot_ctr  = np.array([[x, y, z0]])
    top_ctr  = np.array([[x, y, z1]])
    verts    = np.vstack([bot_ring, top_ring, bot_ctr, top_ctr]).astype(np.float32)
    bc = segments * 2
    tc = segments * 2 + 1
    faces = []
    for i in range(segments):
        nxt = (i + 1) % segments
        faces += [
            [i, nxt, nxt + segments],
            [i, nxt + segments, i + segments],
            [bc, nxt, i],
            [tc, i + segments, nxt + segments],
        ]
    clr = np.tile(color, (len(faces), 1)).astype(np.float32)
    return gl.GLMeshItem(vertexes=verts, faces=np.array(faces), faceColors=clr, smooth=True)


def _line(pts, color, width=2.5):
    return gl.GLLinePlotItem(
        pos=np.array(pts, dtype=np.float32),
        color=color, width=width, antialias=True,
    )


def _contact_plate(x, y, r, color):
    angles = np.linspace(0, 2 * math.pi, 8, endpoint=False)
    verts  = np.column_stack([
        x + r * np.cos(angles),
        y + r * np.sin(angles),
        np.zeros(8),
    ])
    faces = [[0, i, i + 1] for i in range(1, 7)]
    clr   = np.tile(color, (len(faces), 1)).astype(np.float32)
    return gl.GLMeshItem(vertexes=verts.astype(np.float32), faces=np.array(faces), faceColors=clr, smooth=False)


class CustomLoadCanvas3D(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.load_data     = None
        self.bridge_width  = 10.0
        self.span_length   = 20.0
        self._items        = []
        self._needs_update = True
        self._fail_count   = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._fallback_lbl = QLabel("3D Acceleration Unavailable\nRestoring stability...")
        self._fallback_lbl.setAlignment(Qt.AlignCenter)
        self._fallback_lbl.setWordWrap(True)
        self._fallback_lbl.setStyleSheet(
            "color:#d32f2f;font-weight:bold;background:#ffebee;"
            "border:1px solid #ffcdd2;border-radius:4px;padding:10px;"
        )
        self._fallback_lbl.setVisible(False)
        layout.addWidget(self._fallback_lbl)

        if not _HAS_GL:
            self._fallback_lbl.setText("3D view unavailable.\nInstall pyqtgraph and PyOpenGL.")
            self._fallback_lbl.setVisible(True)
            self._view = None
            return

        self._view = None
        self._build_view()

    # create the actual gl surface
    def _build_view(self):
        self._view = gl.GLViewWidget()
        self._view.setBackgroundColor("#f5f5f5")
        self._view.setCameraPosition(distance=45, elevation=28, azimuth=220)
        self._view.opts["fov"] = 55
        self._items = []
        self.layout().addWidget(self._view)

    def _destroy_view(self):
        if self._view is None:
            return
        self._items.clear()
        self.layout().removeWidget(self._view)
        self._view.hide()
        self._view.deleteLater()
        self._view = None

    def showEvent(self, event):
        super().showEvent(event)
        if not _HAS_GL or self._fail_count >= 3:
            return
        self._destroy_view()
        self._build_view()
        if self.load_data or self._needs_update:
            # give it a tiny bit of time to settle before drawing
            QTimer.singleShot(100, self._render_safe)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._clear()

    def zoom(self, factor):
        if self._view:
            self._view.opts["distance"] *= factor
            self._view.update()

    def reset_camera(self):
        if self._view:
            self._view.setCameraPosition(distance=45, elevation=28, azimuth=220)

    def set_camera_view(self, mode):
        if not self._view:
            return
        presets = {
            "top":  dict(distance=40, elevation=90,  azimuth=270),
            "side": dict(distance=40, elevation=0,   azimuth=270),
            "iso":  dict(distance=45, elevation=28,  azimuth=220),
        }
        if mode in presets:
            self._view.setCameraPosition(**presets[mode])

    def set_load_data(self, data, bridge_width=10.0, span_length=20.0):
        self.load_data     = data
        self.bridge_width  = max(bridge_width, 1.0)
        self.span_length   = max(span_length, 1.0)
        self._needs_update = True
        if self.isVisible():
            self._render_safe()

    def _render_safe(self):
        if not self.isVisible() or self._fail_count >= 3:
            return
        self._render()

    def _handle_fallback(self):
        self._destroy_view()
        self._fallback_lbl.setVisible(True)

    def _add_safe(self, item_func, *args, **kwargs):
        if self._view is None:
            return
        try:
            self._view.makeCurrent()
            item = item_func(*args, **kwargs)
            self._view.addItem(item)
            self._items.append(item)
        except Exception as e:
            print(f"3D item error: {e}")
            self._fail_count += 1
            if self._fail_count >= 3:
                self._handle_fallback()

    def _add(self, item):
        if self._view:
            self._view.addItem(item)
            self._items.append(item)

    def _clear(self):
        if self._view is None:
            return
        for item in self._items:
            self._view.removeItem(item)
        self._items.clear()

    # main logic to rebuild the 3d scene
    def _render(self):
        if self._view is None or not self.load_data or not self.isVisible():
            return
        if self._fail_count >= 3:
            self._handle_fallback()
            return

        try:
            self._view.makeCurrent()
        except Exception:
            pass

        self._clear()
        self._needs_update = False

        bw = self.bridge_width
        sp = self.span_length

        # figure out deck and girder dimensions
        deck_thick = max(bw * 0.05, 0.35)
        barrier_h  = deck_thick * 0.9
        barrier_w  = max(bw * 0.025, 0.18)
        g_w        = max(bw * 0.045, 0.32)
        flange_w   = g_w * 2.8
        flange_h   = deck_thick * 0.28
        web_h      = deck_thick * 2.2
        g_total_h  = flange_h * 2 + web_h

        deck_z0       = 0.0
        deck_z1       = deck_thick
        g_bot_flg_z   = deck_z0 - g_total_h
        g_top_flg_z   = deck_z0 - flange_h
        g_web_z0      = deck_z0 - flange_h - web_h
        foundation_z  = g_bot_flg_z - 0.5

        try:
            self._draw_ground(bw, sp, foundation_z)
            self._draw_deck(bw, sp, deck_z0, deck_z1, barrier_h, barrier_w)
            self._draw_girders(bw, sp, flange_w, g_w, flange_h, web_h, deck_z0, g_bot_flg_z, g_top_flg_z, g_web_z0)

            load_type = self.load_data.get("type", "").lower()
            x1 = float(self.load_data.get("dist_left_start", bw * 0.5))
            x2 = float(self.load_data.get("dist_left_end",   x1))
            y1 = float(self.load_data.get("dist_bear_start", 0.0))
            y2 = float(self.load_data.get("dist_bear_end",   sp))
            mag = self.load_data.get("magnitude", "?")

            arrow_tip_z  = deck_z1 + 0.02
            arrow_stem_h = max(bw * 0.22, 1.4)
            cone_h       = max(bw * 0.11, 0.75)
            cone_r       = max(bw * 0.035, 0.3)
            stem_r       = cone_r * 0.4

            if load_type == "point":
                self._draw_point_load(x1, y1, arrow_tip_z, arrow_stem_h, cone_h, cone_r, stem_r, mag)
            elif load_type == "line":
                self._draw_line_load(x1, x2, y1, y2, arrow_tip_z, arrow_stem_h, cone_h, cone_r, stem_r, mag, bw, sp)
            elif load_type == "area":
                self._draw_area_load(x1, x2, y1, y2, arrow_tip_z, arrow_stem_h, cone_h, cone_r, stem_r, mag, bw, sp)

            self._view.update()
        except Exception as e:
            print(f"3D render error: {e}")
            self._fail_count += 1
            if self._fail_count >= 3:
                self._handle_fallback()

    def _draw_ground(self, bw, sp, z):
        grid = gl.GLGridItem()
        grid.setSize(x=bw * 2.5, y=sp * 1.8)
        grid.setSpacing(x=max(bw / 10, 1.0), y=max(sp / 10, 2.0))
        grid.translate(bw / 2, sp / 2, z)
        grid.setColor((0.6, 0.65, 0.7, 0.25))
        self._add(grid)

        try:
            for i in range(0, int(bw) + 1, 2):
                self._add(gl.GLTextItem(pos=np.array([i, -1.0, z], dtype=np.float32), text=f"{i}m", color=(0.4, 0.4, 0.4, 1.0)))
            for i in range(0, int(sp) + 1, 5):
                self._add(gl.GLTextItem(pos=np.array([-1.5, i, z], dtype=np.float32), text=f"{i}m", color=(0.4, 0.4, 0.4, 1.0)))
        except Exception:
            pass

    def _draw_deck(self, bw, sp, z0, z1, barrier_h, barrier_w):
        self._add(_solid_box(0, bw, 0, sp, z0, z1, _CONCRETE_RGBA))
        for bx in (0.0, bw - barrier_w):
            self._add(_solid_box(bx, bx + barrier_w, 0, sp, z1, z1 + barrier_h, _GIRDER_RGBA))

    def _draw_girders(self, bw, sp, flange_w, g_w, flange_h, web_h, deck_z0, bot_z, top_z, web_z0):
        for frac in (0.2, 0.5, 0.8):
            cx = bw * frac
            hw = flange_w / 2
            self._add(_solid_box(cx - hw, cx + hw, 0, sp, top_z,  deck_z0,  _GIRDER_RGBA))
            self._add(_solid_box(cx - g_w / 2, cx + g_w / 2, 0, sp, web_z0, top_z, _GIRDER_RGBA))
            self._add(_solid_box(cx - hw, cx + hw, 0, sp, bot_z,  web_z0,  _GIRDER_RGBA))

    def _draw_load_arrow(self, x, y, tip_z, stem_h, cone_h, cone_r, stem_r, draw_plate=True):
        stem_top = tip_z + stem_h + cone_h
        self._add(_cylinder(x, y, tip_z + cone_h, stem_top, stem_r, _LOAD_RGBA))
        self._add(_cone(x, y, tip_z, cone_h, cone_r, _LOAD_RGBA))
        if draw_plate:
            plate = _contact_plate(x, y, cone_r * 1.1, _CONTACT_RGBA)
            plate.translate(0, 0, tip_z - 0.01)
            self._add(plate)

    def _draw_point_load(self, x, y, tip_z, stem_h, cone_h, cone_r, stem_r, mag):
        self._draw_load_arrow(x, y, tip_z, stem_h, cone_h, cone_r, stem_r)
        self._try_label(x, y, tip_z + stem_h + cone_h + 0.5, f"P = {mag} kN")

    def _draw_line_load(self, x1, x2, y1, y2, tip_z, stem_h, cone_h, cone_r, stem_r, mag, bw, sp):
        mid_y  = (y1 + y2) / 2
        span_x = x2 - x1
        count  = max(3, int(abs(span_x) / max(bw / 8, 0.5)) + 1) if abs(span_x) > 0.1 else 1

        tops = []
        for i in range(count):
            t  = i / max(count - 1, 1)
            xi = x1 + t * span_x
            self._draw_load_arrow(xi, mid_y, tip_z, stem_h, cone_h, cone_r, stem_r)
            tops.append([xi, mid_y, tip_z + stem_h + cone_h])

        if len(tops) >= 2:
            self._add(_line(tops, _LOAD_RGBA, width=3.5))

        self._try_label((x1 + x2) / 2, mid_y, tip_z + stem_h + cone_h + 0.5, f"w = {mag} kN/m")

    def _draw_area_load(self, x1, x2, y1, y2, tip_z, stem_h, cone_h, cone_r, stem_r, mag, bw, sp):
        vol_h = stem_h * 0.7
        pad_x = max(x2 - x1, 0.3)
        pad_y = max(y2 - y1, 0.3)

        area_verts = np.array([
            [x1,         y1,         tip_z        ],
            [x1 + pad_x, y1,         tip_z        ],
            [x1 + pad_x, y1 + pad_y, tip_z        ],
            [x1,         y1 + pad_y, tip_z        ],
            [x1,         y1,         tip_z + vol_h],
            [x1 + pad_x, y1,         tip_z + vol_h],
            [x1 + pad_x, y1 + pad_y, tip_z + vol_h],
            [x1,         y1 + pad_y, tip_z + vol_h],
        ], dtype=np.float32)
        area_faces = np.array([
            [0,1,2],[0,2,3],[4,5,6],[4,6,7],
            [0,1,5],[0,5,4],[2,3,7],[2,7,6],
            [0,3,7],[0,7,4],[1,2,6],[1,6,5],
        ])
        area_clr = np.tile(_AREA_RGBA, (len(area_faces), 1)).astype(np.float32)
        self._add(gl.GLMeshItem(
            vertexes=area_verts, faces=area_faces, faceColors=area_clr,
            smooth=False, drawEdges=True, edgeColor=_EDGE_DARK,
        ))

        plate_verts = np.array([
            [x1,         y1,         tip_z - 0.01],
            [x1 + pad_x, y1,         tip_z - 0.01],
            [x1 + pad_x, y1 + pad_y, tip_z - 0.01],
            [x1,         y1 + pad_y, tip_z - 0.01],
        ], dtype=np.float32)
        plate_faces = np.array([[0,1,2],[0,2,3]])
        plate_clr   = np.tile(_CONTACT_RGBA, (len(plate_faces), 1)).astype(np.float32)
        self._add(gl.GLMeshItem(vertexes=plate_verts, faces=plate_faces, faceColors=plate_clr, smooth=False))

        nx = max(2, int(pad_x / max(bw / 6, 0.5)) + 1)
        ny = max(2, int(pad_y / max(sp / 6, 0.5)) + 1)
        for ix in range(nx):
            for iy in range(ny):
                xi = x1 + (pad_x * ix / max(nx - 1, 1))
                yi = y1 + (pad_y * iy / max(ny - 1, 1))
                self._draw_load_arrow(xi, yi, tip_z, stem_h * 0.55, cone_h * 0.75, cone_r * 0.72, stem_r * 0.72)

        self._try_label(x1 + pad_x / 2, y1 + pad_y / 2, tip_z + vol_h + 0.5, f"q = {mag} kN/m²")

    def _try_label(self, x, y, z, text):
        try:
            self._add(gl.GLTextItem(
                pos=np.array([x, y, z], dtype=np.float32),
                text=text,
                color=(*_LOAD_RGBA[:3], 1.0),
            ))
        except Exception:
            pass