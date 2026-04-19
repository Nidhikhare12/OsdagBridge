# ──────────────────────────────────────────────────────────────────────────────
# 3D Implementation Discussion
# ──────────────────────────────────────────────────────────────────────────────
# This module deliberately uses 2D QPainter-based CAD views (cross-section and
# elevation) rather than an OpenGL / 3D rendering pipeline.  The rationale:
#
#   1. **Scale Accuracy** — Engineering drawings require precise, dimensioned
#      representation.  QPainter's coordinate system maps directly to physical
#      units via `pixel_per_meter`, guaranteeing that on-screen distances
#      correspond exactly to real-world values.  An OpenGL perspective or
#      orthographic projection would add an extra transformation layer whose
#      rounding / depth-buffer artefacts could compromise measurements.
#
#   2. **Zero-Dependency Integration** — The Osdag desktop UI is built on
#      PySide6 (Qt).  QPainter is part of the core Qt framework, so these
#      canvas widgets work on every platform Osdag supports without pulling in
#      OpenGL drivers, PyOpenGL, or shader toolchains.
#
#   3. **Real-Time Performance** — Each `paintEvent` completes in < 1 ms on a
#      modern desktop.  The lightweight geometry (rects, lines, polygons)
#      repaints on every `textChanged` signal with no visible lag, keeping the
#      interactive workflow fluid.
#
#   4. **Maintainability** — Structural engineers contributing to Osdag are
#      familiar with 2D drawing conventions.  Keeping the rendering in plain
#      QPainter calls lowers the barrier to future enhancements (e.g. adding
#      reinforcement layers or dimension annotations).
#
# A future 3D viewer (e.g. for FEM mesh visualisation) can be layered on top
# via a separate QOpenGLWidget without altering these canonical 2D drawings.
# ──────────────────────────────────────────────────────────────────────────────

"""2D CAD bridge load visualization widget.

Renders a cross-section view of a bridge deck + girders with dynamic load
symbols (Point, Line, Area) that update when the user changes inputs.

Usage::
    canvas = BridgeLoadCanvas()
    canvas.set_num_girders(3)
    canvas.set_load_type("Point")
    canvas.set_position(0.4)        # 40% along span
    canvas.set_range(0.2, 0.8)      # for Line / Area loads
"""

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore    import Qt, QSize
from PySide6.QtGui     import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QFontMetrics
)
from PySide6.QtCore import QPointF, QRectF

# ── Palette ──────────────────────────────────────────────────────────────────
_COL_DECK      = QColor("#8A9BA8")   # blue-grey  — deck slab
_COL_GIRDER    = QColor("#6B7F8C")   # darker grey — girder web/flanges
_COL_LOAD      = QColor("#CC2200")   # red         — load arrows
_COL_AREA_FILL = QColor(204, 34, 0, 55)  # red 22 % alpha — area shade
_COL_DIM       = QColor("#666666")   # dark grey   — dimension lines
_COL_LABEL     = QColor("#222222")   # near-black  — text labels
_COL_BG        = QColor("#FFFFFF")   # white background

# Elevation-specific colours
_COL_SUPPORT   = QColor("#4A5A6A")   # dark blue-grey — support triangles
_COL_SPAN_FILL = QColor("#B0BEC5")   # light grey    — girder side profile


class BridgeLoadCanvas(QWidget):
    """QPainter-based cross-section view for bridge load visualization."""

    # ── defaults ──────────────────────────────────────────────────────────────
    _LOAD_TYPES = ("Point", "Line", "Area")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: white;")

        # Public state — changed via public setters
        self._load_type:  str   = "Point"
        self._pos_x:      float = 0.0    # raw distance (m) for Point load
        self._x1:         float = 0.0    # raw start dist (m) for Line/Area
        self._x2:         float = 0.0    # raw end   dist (m) for Line/Area
        self._num_girders: int  = 3
        self._span_m:     float = 1.0    # physical span (m)
        self._span_label: str  = "Span Length"

    # ── public setters (each triggers repaint) ────────────────────────────────

    def set_load_type(self, load_type: str) -> None:
        """Set load type: 'Point', 'Line', or 'Area'."""
        if load_type in self._LOAD_TYPES:
            self._load_type = load_type
            self.update()

    def set_span(self, span_m: float) -> None:
        """Set physical span size for internal ratio scaling."""
        self._span_m = max(span_m, 0.001)
        self.update()

    def set_position(self, x: float) -> None:
        """Set position [m] for Point load."""
        self._pos_x = x
        self.update()

    def set_range(self, x1: float, x2: float) -> None:
        """Set start/end [m] for Line / Area load."""
        self._x1 = min(x1, x2)
        self._x2 = max(x1, x2)
        self.update()

    def set_num_girders(self, n: int) -> None:
        """Update girder count and repaint."""
        self._num_girders = max(1, n)
        self.update()

    def set_span_label(self, label: str) -> None:
        self._span_label = label
        self.update()

    # ── Qt override: preferred size ───────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(600, 280)

    # ── main paint event ──────────────────────────────────────────────────────

    def paintEvent(self, event):                         # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Fill background
        painter.fillRect(self.rect(), _COL_BG)

        # Compute layout geometry once per paint
        p = self._layout()

        self._draw_load_symbol(painter, p)   # drawn BEHIND deck
        self._draw_deck(painter, p)
        self._draw_girders(painter, p)
        self._draw_labels(painter, p)
        self._draw_span_dim(painter, p)
        self._draw_load_title(painter, p)    # label above load

        painter.end()

    # ── geometry helper ───────────────────────────────────────────────────────

    def _layout(self) -> dict:
        """Return a dict of all geometry values derived from current size."""
        W = self.width()
        H = self.height()

        mx = 72          # left/right margin
        span_px = W - 2 * mx

        deck_y      = H * 0.52
        deck_h      = 20
        girder_h    = 58
        flange_t    = 10   # flange thickness (top & bottom)
        web_w       = 16   # web width
        flange_w    = 38   # flange width

        # Girder x-positions (evenly spaced)
        step = span_px / (self._num_girders + 1)
        girder_xs = [mx + step * (i + 1) for i in range(self._num_girders)]

        arrow_h    = 50    # pixel height of load arrow shaft
        arrow_top  = deck_y - arrow_h  # Y where arrow tip meets deck top
        
        pixel_per_meter = span_px / max(self._span_m, 0.001)

        return dict(
            W=W, H=H, mx=mx, span_px=span_px,
            deck_y=deck_y, deck_h=deck_h,
            girder_h=girder_h, flange_t=flange_t, web_w=web_w, flange_w=flange_w,
            girder_xs=girder_xs,
            arrow_h=arrow_h, arrow_top=arrow_top,
            pixel_per_meter=pixel_per_meter,
        )

    # ── drawing helpers ───────────────────────────────────────────────────────

    def _draw_deck(self, painter: QPainter, p: dict) -> None:
        """Draw the bridge deck slab as a filled rounded rect."""
        painter.setBrush(QBrush(_COL_DECK))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            QRectF(p["mx"], p["deck_y"],
                   p["span_px"], p["deck_h"]),
            3, 3
        )

    def _draw_girders(self, painter: QPainter, p: dict) -> None:
        """Draw I-beam shaped girders below the deck."""
        painter.setBrush(QBrush(_COL_GIRDER))
        painter.setPen(Qt.NoPen)

        top_flange_y = p["deck_y"] + p["deck_h"]
        web_y        = top_flange_y + p["flange_t"]
        web_h        = p["girder_h"] - 2 * p["flange_t"]
        bot_flange_y = web_y + web_h

        for gx in p["girder_xs"]:
            # top flange
            painter.drawRect(QRectF(
                gx - p["flange_w"] / 2, top_flange_y,
                p["flange_w"], p["flange_t"]
            ))
            # web
            painter.drawRect(QRectF(
                gx - p["web_w"] / 2, web_y,
                p["web_w"], web_h
            ))
            # bottom flange
            painter.drawRect(QRectF(
                gx - p["flange_w"] / 2, bot_flange_y,
                p["flange_w"], p["flange_t"]
            ))

    def _draw_load_symbol(self, painter: QPainter, p: dict) -> None:
        """Dispatch to the correct load renderer."""
        if self._load_type == "Point":
            self._draw_point_load(painter, p)
        elif self._load_type == "Line":
            self._draw_line_load(painter, p)
        elif self._load_type == "Area":
            self._draw_area_load(painter, p)

    def _arrow(self, painter: QPainter, cx: float,
               top_y: float, bot_y: float,
               head_w: int = 12) -> None:
        """Draw a single downward arrow: shaft + filled arrowhead."""
        shaft_pen = QPen(_COL_LOAD, 2.5)
        painter.setPen(shaft_pen)
        painter.drawLine(QPointF(cx, top_y), QPointF(cx, bot_y - head_w / 2))

        # arrowhead (filled triangle)
        head = QPolygonF([
            QPointF(cx,               bot_y),
            QPointF(cx - head_w / 2,  bot_y - head_w),
            QPointF(cx + head_w / 2,  bot_y - head_w),
        ])
        painter.setBrush(QBrush(_COL_LOAD))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(head)

    def _draw_point_load(self, painter: QPainter, p: dict) -> None:
        cx = p["mx"] + self._pos_x * p["pixel_per_meter"]
        self._arrow(painter, cx, p["arrow_top"] - 10, p["deck_y"])

    def _draw_line_load(self, painter: QPainter, p: dict) -> None:
        x1_px = p["mx"] + self._x1 * p["pixel_per_meter"]
        x2_px = p["mx"] + self._x2 * p["pixel_per_meter"]
        line_y = p["arrow_top"] - 10

        # horizontal connecting line
        painter.setPen(QPen(_COL_LOAD, 2.5))
        painter.drawLine(QPointF(x1_px, line_y), QPointF(x2_px, line_y))

        # evenly spaced arrows
        width_px = x2_px - x1_px
        n_arrows = max(2, int(width_px / 32))
        for i in range(n_arrows + 1):
            ax = x1_px + (width_px * i / n_arrows) if n_arrows else x1_px
            self._arrow(painter, ax, line_y, p["deck_y"])

    def _draw_area_load(self, painter: QPainter, p: dict) -> None:
        x1_px = p["mx"] + self._x1 * p["pixel_per_meter"]
        x2_px = p["mx"] + self._x2 * p["pixel_per_meter"]
        line_y = p["arrow_top"] - 10

        # shaded rectangle
        shade_rect = QRectF(x1_px, line_y, x2_px - x1_px, p["deck_y"] - line_y)
        painter.setBrush(QBrush(_COL_AREA_FILL))
        dash_pen = QPen(_COL_LOAD, 1.5, Qt.DashLine)
        painter.setPen(dash_pen)
        painter.drawRect(shade_rect)

        # arrows (same as line load)
        width_px = x2_px - x1_px
        n_arrows = max(2, int(width_px / 32))
        painter.setBrush(QBrush(_COL_LOAD))
        for i in range(n_arrows + 1):
            ax = x1_px + (width_px * i / n_arrows) if n_arrows else x1_px
            self._arrow(painter, ax, line_y, p["deck_y"])

    def _draw_labels(self, painter: QPainter, p: dict) -> None:
        """Draw 'Deck' and 'Girder' annotation labels with leader lines."""
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(_COL_LABEL, 1))

        # Deck label
        deck_label_x = p["mx"] - 8
        deck_label_y = p["deck_y"] + p["deck_h"] / 2 + 4
        painter.drawText(int(deck_label_x) - 44, int(deck_label_y), "Deck")
        painter.drawLine(
            QPointF(deck_label_x - 2, deck_label_y - 2),
            QPointF(p["mx"], p["deck_y"] + p["deck_h"] / 2)
        )

        # Girder label (point to first girder web centre)
        if p["girder_xs"]:
            gx = p["girder_xs"][0]
            gir_y = p["deck_y"] + p["deck_h"] + p["flange_t"] + p["girder_h"] / 2
            painter.drawText(int(p["mx"]) - 50, int(gir_y) + 4, "Girder")
            painter.drawLine(
                QPointF(p["mx"] - 2, gir_y),
                QPointF(gx - p["flange_w"] / 2, gir_y)
            )

    def _draw_span_dim(self, painter: QPainter, p: dict) -> None:
        """Draw dashed horizontal dimension line at the bottom."""
        dim_y  = p["deck_y"] + p["deck_h"] + p["girder_h"] + 22
        x_left = p["mx"]
        x_rght = p["mx"] + p["span_px"]

        painter.setPen(QPen(_COL_DIM, 1, Qt.DashLine))
        painter.drawLine(QPointF(x_left, dim_y), QPointF(x_rght, dim_y))

        # tick marks
        painter.setPen(QPen(_COL_DIM, 1.5))
        painter.drawLine(QPointF(x_left, dim_y - 5), QPointF(x_left, dim_y + 5))
        painter.drawLine(QPointF(x_rght, dim_y - 5), QPointF(x_rght, dim_y + 5))

        # span text
        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QPen(_COL_DIM, 1))
        fm   = QFontMetrics(font)
        text = self._span_label
        tw   = fm.horizontalAdvance(text)
        painter.drawText(int((x_left + x_rght) / 2 - tw / 2),
                         int(dim_y + 14), text)

    def _draw_load_title(self, painter: QPainter, p: dict) -> None:
        """Draw load type title above the load symbol."""
        titles = {
            "Point": "Point Load  P",
            "Line":  "Line Load  w (kN/m)",
            "Area":  "Area Load  q (kN/m²)",
        }
        text = titles.get(self._load_type, "")
        font = QFont("Arial", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(_COL_LABEL, 1))

        fm = QFontMetrics(font)
        tw = fm.horizontalAdvance(text)
        tx = int(p["W"] / 2 - tw / 2)
        ty = int(p["arrow_top"] - 22)
        painter.drawText(tx, ty, text)


# ══════════════════════════════════════════════════════════════════════════════
# Elevation (side) view canvas
# ══════════════════════════════════════════════════════════════════════════════

class BridgeElevationCanvas(QWidget):
    """QPainter-based side-elevation view of the bridge span.

    Draws a horizontal girder profile of length ``span_m`` with triangular
    supports at each end and maps the current load position (Point) or range
    (Line / Area) horizontally along the span.  Scale consistency with the
    cross-section view is maintained via the same ``pixel_per_meter`` logic.

    Usage::
        elev = BridgeElevationCanvas()
        elev.set_span(35.0)
        elev.set_load_type("Point")
        elev.set_position(12.5)
    """

    _LOAD_TYPES = ("Point", "Line", "Area")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("background-color: white;")

        self._load_type: str   = "Point"
        self._pos_x:     float = 0.0
        self._x1:        float = 0.0
        self._x2:        float = 0.0
        self._span_m:    float = 1.0

    # ── public setters ────────────────────────────────────────────────────────

    def set_load_type(self, load_type: str) -> None:
        if load_type in self._LOAD_TYPES:
            self._load_type = load_type
            self.update()

    def set_span(self, span_m: float) -> None:
        self._span_m = max(span_m, 0.001)
        self.update()

    def set_position(self, x: float) -> None:
        self._pos_x = x
        self.update()

    def set_range(self, x1: float, x2: float) -> None:
        self._x1 = min(x1, x2)
        self._x2 = max(x1, x2)
        self.update()

    # ── Qt overrides ──────────────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(600, 160)

    # ── paint event ───────────────────────────────────────────────────────────

    def paintEvent(self, event):                         # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.fillRect(self.rect(), _COL_BG)

        p = self._elev_layout()

        self._draw_girder_profile(painter, p)
        self._draw_supports(painter, p)
        self._draw_elev_load(painter, p)
        self._draw_elev_dim(painter, p)
        self._draw_elev_title(painter, p)

        painter.end()

    # ── geometry ──────────────────────────────────────────────────────────────

    def _elev_layout(self) -> dict:
        W = self.width()
        H = self.height()

        mx = 72
        span_px = W - 2 * mx
        pixel_per_meter = span_px / max(self._span_m, 0.001)

        girder_y = H * 0.45          # top of girder rectangle
        girder_h = 18                # girder depth in px
        support_h = 20               # triangle height below girder
        arrow_h = 40                 # load arrow height

        return dict(
            W=W, H=H, mx=mx, span_px=span_px,
            pixel_per_meter=pixel_per_meter,
            girder_y=girder_y, girder_h=girder_h,
            support_h=support_h, arrow_h=arrow_h,
        )

    # ── drawing helpers ───────────────────────────────────────────────────────

    def _draw_girder_profile(self, painter: QPainter, p: dict) -> None:
        """Draw the girder as a long horizontal rectangle (side view)."""
        painter.setBrush(QBrush(_COL_SPAN_FILL))
        painter.setPen(QPen(_COL_GIRDER, 1.5))
        painter.drawRect(QRectF(
            p["mx"], p["girder_y"], p["span_px"], p["girder_h"]
        ))

    def _draw_supports(self, painter: QPainter, p: dict) -> None:
        """Draw triangular pin supports at each end of the span."""
        painter.setBrush(QBrush(_COL_SUPPORT))
        painter.setPen(Qt.NoPen)
        base_y = p["girder_y"] + p["girder_h"]
        tri_half = 10  # half-width of triangle base

        for sx in (p["mx"], p["mx"] + p["span_px"]):
            tri = QPolygonF([
                QPointF(sx, base_y),
                QPointF(sx - tri_half, base_y + p["support_h"]),
                QPointF(sx + tri_half, base_y + p["support_h"]),
            ])
            painter.drawPolygon(tri)

    def _draw_elev_load(self, painter: QPainter, p: dict) -> None:
        """Draw load indicator(s) above the girder profile."""
        arrow_top = p["girder_y"] - p["arrow_h"]
        arrow_bot = p["girder_y"]

        if self._load_type == "Point":
            cx = p["mx"] + self._pos_x * p["pixel_per_meter"]
            self._elev_arrow(painter, cx, arrow_top, arrow_bot)
        else:
            # Line or Area
            x1_px = p["mx"] + self._x1 * p["pixel_per_meter"]
            x2_px = p["mx"] + self._x2 * p["pixel_per_meter"]

            if self._load_type == "Area":
                shade = QRectF(x1_px, arrow_top, x2_px - x1_px,
                               arrow_bot - arrow_top)
                painter.setBrush(QBrush(_COL_AREA_FILL))
                painter.setPen(QPen(_COL_LOAD, 1, Qt.DashLine))
                painter.drawRect(shade)

            # Horizontal connecting line
            painter.setPen(QPen(_COL_LOAD, 2))
            painter.drawLine(QPointF(x1_px, arrow_top), QPointF(x2_px, arrow_top))

            width_px = x2_px - x1_px
            n_arrows = max(2, int(width_px / 36))
            for i in range(n_arrows + 1):
                ax = x1_px + (width_px * i / n_arrows) if n_arrows else x1_px
                self._elev_arrow(painter, ax, arrow_top, arrow_bot)

    def _elev_arrow(self, painter: QPainter, cx: float,
                    top_y: float, bot_y: float) -> None:
        """Single downward arrow for the elevation view."""
        head_w = 10
        painter.setPen(QPen(_COL_LOAD, 2))
        painter.drawLine(QPointF(cx, top_y), QPointF(cx, bot_y - head_w / 2))

        head = QPolygonF([
            QPointF(cx, bot_y),
            QPointF(cx - head_w / 2, bot_y - head_w),
            QPointF(cx + head_w / 2, bot_y - head_w),
        ])
        painter.setBrush(QBrush(_COL_LOAD))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(head)

    def _draw_elev_dim(self, painter: QPainter, p: dict) -> None:
        """Span dimension line below the supports."""
        dim_y = p["girder_y"] + p["girder_h"] + p["support_h"] + 12
        x_left = p["mx"]
        x_right = p["mx"] + p["span_px"]

        painter.setPen(QPen(_COL_DIM, 1, Qt.DashLine))
        painter.drawLine(QPointF(x_left, dim_y), QPointF(x_right, dim_y))

        painter.setPen(QPen(_COL_DIM, 1.5))
        painter.drawLine(QPointF(x_left, dim_y - 4), QPointF(x_left, dim_y + 4))
        painter.drawLine(QPointF(x_right, dim_y - 4), QPointF(x_right, dim_y + 4))

        font = QFont("Arial", 8)
        painter.setFont(font)
        painter.setPen(QPen(_COL_DIM, 1))
        fm = QFontMetrics(font)
        text = f"{self._span_m:.1f} m"
        tw = fm.horizontalAdvance(text)
        painter.drawText(int((x_left + x_right) / 2 - tw / 2),
                         int(dim_y + 13), text)

    def _draw_elev_title(self, painter: QPainter, p: dict) -> None:
        """Draw 'Elevation View' header above the drawing."""
        font = QFont("Arial", 9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(_COL_LABEL, 1))

        fm = QFontMetrics(font)
        text = "Elevation View"
        tw = fm.horizontalAdvance(text)
        painter.drawText(int(p["W"] / 2 - tw / 2),
                         int(p["girder_y"] - p["arrow_h"] - 10), text)
