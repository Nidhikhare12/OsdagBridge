import math
from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QDoubleValidator, QPen, QBrush, QColor, QFont, QPainter, QPolygonF
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from osdagbridge.desktop.ui.dialogs.tabs.common import apply_field_style
from osdagbridge.desktop.ui.dialogs.custom_messagebox import CustomMessageBox, MessageBoxType
from osdagbridge.core.bridge_types.plate_girder.ui_fields_additional_input import CUSTOM_LOAD_TAB_SCHEMA


# ═══════════════════════════════════════════════════════════════════════════════
#  CROSS-SECTION VIEW  —  BridgeLoadScene
# ═══════════════════════════════════════════════════════════════════════════════

class BridgeLoadScene(QGraphicsScene):
    """
    2D cross-section of the bridge showing:
      • RC deck slab
      • 3 steel I-girders (G1, G2, G3)
      • Load symbol: Point arrow / Line UDL / Area patch

    Call update_load(load_type, x1, x2, span_m, label) to refresh.
    """

    # ── Layout constants ──────────────────────────────────────────────────────
    W, H      = 460, 280
    DECK_TOP  = 120
    DECK_H    = 22
    GH        = 70        # total girder height
    FLANGE_W  = 48
    FLANGE_H  = 10
    WEB_W     = 10
    N_GIRDERS = 3
    MARGIN    = 44
    ARROW_H   = 38
    ARROW_TIP = 9

    # ── Colours ───────────────────────────────────────────────────────────────
    C_BG      = QColor("#f8f8f8")
    C_DECK    = QColor("#78909c")
    C_GIRDER  = QColor("#546e7a")
    C_OUTLINE = QColor("#37474f")
    C_LOAD    = QColor("#e53935")
    C_AREA    = QColor(229, 57, 53, 45)
    C_DIM     = QColor("#666666")
    C_TITLE   = QColor("#212121")

    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, self.W, self.H)
        self._load_type = "Point"
        self._x1        = 0.40
        self._x2        = 0.70
        self._span_m    = 20.0
        self._label     = ""
        self._redraw()

    # ── Public API ─────────────────────────────────────────────────────────────

    def update_load(self, load_type: str, x1: float, x2: float,
                    span_m: float = 20.0, label: str = ""):
        self._load_type = load_type
        self._x1        = max(0.0, min(1.0, x1))
        self._x2        = max(0.0, min(1.0, x2))
        self._span_m    = span_m if span_m > 0 else 20.0
        self._label     = label
        self._redraw()

    # ── Internal drawing ───────────────────────────────────────────────────────

    def _redraw(self):
        self.clear()
        self._bg()
        self._girders()
        self._deck()
        self._load()
        self._dimension_line()
        self._legend()

    def _pen(self, col, w=1.0, style=Qt.SolidLine):
        p = QPen(col, w, style)
        p.setCosmetic(False)
        return p

    def _bg(self):
        self.addRect(0, 0, self.W, self.H, QPen(Qt.NoPen), QBrush(self.C_BG))

    def _girder_xs(self):
        span = self.W - 2 * self.MARGIN
        step = span / (self.N_GIRDERS - 1)
        return [self.MARGIN + i * step for i in range(self.N_GIRDERS)]

    def _deck(self):
        self.addRect(
            self.MARGIN, self.DECK_TOP,
            self.W - 2 * self.MARGIN, self.DECK_H,
            self._pen(self.C_OUTLINE, 1.2),
            QBrush(self.C_DECK),
        )
        lbl = self.addText("Deck slab")
        lbl.setFont(QFont("Arial", 7))
        lbl.setDefaultTextColor(self.C_DIM)
        lbl.setPos(4, self.DECK_TOP + 4)

    def _girders(self):
        pen   = self._pen(self.C_OUTLINE, 1.0)
        brush = QBrush(self.C_GIRDER)
        y0    = self.DECK_TOP + self.DECK_H

        for i, gx in enumerate(self._girder_xs()):
            self.addRect(gx - self.FLANGE_W / 2, y0,
                         self.FLANGE_W, self.FLANGE_H, pen, brush)
            wy = y0 + self.FLANGE_H
            wh = self.GH - 2 * self.FLANGE_H
            self.addRect(gx - self.WEB_W / 2, wy,
                         self.WEB_W, wh, pen, brush)
            by = y0 + self.GH - self.FLANGE_H
            self.addRect(gx - self.FLANGE_W / 2, by,
                         self.FLANGE_W, self.FLANGE_H, pen, brush)
            g_lbl = self.addText(f"G{i+1}")
            g_lbl.setFont(QFont("Arial", 7))
            g_lbl.setDefaultTextColor(self.C_DIM)
            g_lbl.setPos(gx - g_lbl.boundingRect().width() / 2,
                         y0 + self.GH + 3)

    def _span_x(self, norm: float) -> float:
        return self.MARGIN + norm * (self.W - 2 * self.MARGIN)

    def _arrow(self, x: float, y_top: float):
        pen   = self._pen(self.C_LOAD, 2.0)
        y_tip = self.DECK_TOP
        self.addLine(x, y_top, x, y_tip - self.ARROW_TIP, pen)
        head = QPolygonF([
            QPointF(x,     y_tip),
            QPointF(x - 7, y_tip - self.ARROW_TIP),
            QPointF(x + 7, y_tip - self.ARROW_TIP),
        ])
        self.addPolygon(head, QPen(Qt.NoPen), QBrush(self.C_LOAD))

    def _load(self):
        lt  = self._load_type
        a_y = self.DECK_TOP - self.ARROW_H
        pen = self._pen(self.C_LOAD, 2.0)
        s   = self._span_m

        if lt == "Point":
            sx   = self._span_x(self._x1)
            x_m  = round(self._x1 * s, 2)
            self._arrow(sx, a_y)
            lbl = self.addText(f"x = {x_m} m")
            lbl.setFont(QFont("Arial", 7, QFont.Bold))
            lbl.setDefaultTextColor(self.C_LOAD)
            lbl.setPos(sx - lbl.boundingRect().width() / 2, a_y - 16)

        else:
            x0 = self._span_x(self._x1)
            x1 = self._span_x(self._x2)
            if x1 < x0:
                x0, x1 = x1, x0

            if lt == "Area":
                self.addRect(x0, a_y, x1 - x0, self.DECK_TOP - a_y,
                             self._pen(self.C_LOAD, 1.0, Qt.DashLine),
                             QBrush(self.C_AREA))

            self.addLine(x0, a_y, x1, a_y, pen)

            gap = 40
            n   = max(2, int((x1 - x0) / gap))
            for i in range(n + 1):
                ax = x0 + i * (x1 - x0) / n
                self._arrow(ax, a_y)

            x1_m = round(self._x1 * s, 2)
            x2_m = round(self._x2 * s, 2)
            lbl = self.addText(f"x₁ = {x1_m} m   x₂ = {x2_m} m")
            lbl.setFont(QFont("Arial", 7, QFont.Bold))
            lbl.setDefaultTextColor(self.C_LOAD)
            lbl.setPos((x0 + x1) / 2 - lbl.boundingRect().width() / 2, a_y - 16)

    def _dimension_line(self):
        dim_y = self.DECK_TOP + self.DECK_H + self.GH + 18
        pen   = self._pen(self.C_DIM, 1.0, Qt.DashLine)
        tick  = self._pen(self.C_DIM, 1.0)
        xl    = self.MARGIN
        xr    = self.W - self.MARGIN

        self.addLine(xl, dim_y, xr, dim_y, pen)
        for xx in (xl, xr):
            self.addLine(xx, dim_y - 5, xx, dim_y + 5, tick)

        # Show real span value in metres
        sp = self.addText(f"Span = {self._span_m:.1f} m")
        sp.setFont(QFont("Arial", 8))
        sp.setDefaultTextColor(self.C_DIM)
        sp.setPos(self.W / 2 - sp.boundingRect().width() / 2, dim_y + 4)

    def _legend(self):
        title = self.addText(f"Load Type: {self._load_type}")
        title.setFont(QFont("Arial", 9, QFont.Bold))
        title.setDefaultTextColor(self.C_TITLE)
        title.setPos(self.W / 2 - title.boundingRect().width() / 2, 4)


# ═══════════════════════════════════════════════════════════════════════════════
#  ELEVATION VIEW  —  ElevationScene  (BONUS)
# ═══════════════════════════════════════════════════════════════════════════════

class ElevationScene(QGraphicsScene):
    """
    Side (elevation) view showing the bridge as a simple beam.
    Displays:
      • Beam rectangle with support triangles at both ends
      • Load arrow(s) at the correct position(s) along the span
      • Span dimension line with real span value in metres
      • Position labels in metres

    This is the bonus Elevation View described in the task PDF (section 3.2).
    """

    W, H      = 460, 150
    MARGIN    = 50
    BEAM_Y    = 72
    BEAM_H    = 16
    ARROW_H   = 36

    C_BG   = QColor("#f8f8f8")
    C_BEAM = QColor("#78909c")
    C_OUT  = QColor("#37474f")
    C_SUPP = QColor("#546e7a")
    C_LOAD = QColor("#e53935")
    C_AREA = QColor(229, 57, 53, 45)
    C_DIM  = QColor("#666666")

    def __init__(self):
        super().__init__()
        self.setSceneRect(0, 0, self.W, self.H)
        self._load_type = "Point"
        self._x1        = 0.40
        self._x2        = 0.70
        self._span_m    = 20.0
        self._redraw()

    # ── Public API ─────────────────────────────────────────────────────────────

    def update_load(self, load_type: str, x1: float, x2: float,
                    span_m: float = 20.0):
        self._load_type = load_type
        self._x1        = max(0.0, min(1.0, x1))
        self._x2        = max(0.0, min(1.0, x2))
        self._span_m    = span_m if span_m > 0 else 20.0
        self._redraw()

    # ── Internal drawing ───────────────────────────────────────────────────────

    def _redraw(self):
        self.clear()
        self._bg()
        self._title()
        self._beam()
        self._supports()
        self._load()
        self._dim_line()

    def _pen(self, col, w=1.5, style=Qt.SolidLine):
        p = QPen(col, w, style)
        p.setCosmetic(False)
        return p

    def _bg(self):
        self.addRect(0, 0, self.W, self.H, QPen(Qt.NoPen), QBrush(self.C_BG))

    def _title(self):
        t = self.addText("Elevation View")
        t.setFont(QFont("Arial", 8, QFont.Bold))
        t.setDefaultTextColor(QColor("#333333"))
        t.setPos(self.W / 2 - t.boundingRect().width() / 2, 4)

    def _beam(self):
        bw = self.W - 2 * self.MARGIN
        self.addRect(self.MARGIN, self.BEAM_Y, bw, self.BEAM_H,
                     self._pen(self.C_OUT, 1.2),
                     QBrush(self.C_BEAM))

    def _supports(self):
        """Pinned support triangles at both ends."""
        y_base = self.BEAM_Y + self.BEAM_H
        for sx in [self.MARGIN, self.W - self.MARGIN]:
            tri = QPolygonF([
                QPointF(sx,      y_base),
                QPointF(sx - 10, y_base + 16),
                QPointF(sx + 10, y_base + 16),
            ])
            self.addPolygon(tri,
                            self._pen(self.C_SUPP, 1),
                            QBrush(self.C_SUPP))
            # ground hatch line
            self.addLine(sx - 14, y_base + 17,
                         sx + 14, y_base + 17,
                         self._pen(self.C_SUPP, 1.5))

    def _scene_x(self, norm: float) -> float:
        return self.MARGIN + norm * (self.W - 2 * self.MARGIN)

    def _draw_arrow(self, x: float):
        """Single downward load arrow to top of beam."""
        tip_y = self.BEAM_Y
        top_y = tip_y - self.ARROW_H
        pen   = self._pen(self.C_LOAD, 2.0)
        self.addLine(x, top_y, x, tip_y - 8, pen)
        head = QPolygonF([
            QPointF(x,     tip_y),
            QPointF(x - 6, tip_y - 9),
            QPointF(x + 6, tip_y - 9),
        ])
        self.addPolygon(head, QPen(Qt.NoPen), QBrush(self.C_LOAD))

    def _load(self):
        lt    = self._load_type
        tip_y = self.BEAM_Y
        top_y = tip_y - self.ARROW_H
        s     = self._span_m

        if lt == "Point":
            px  = self._scene_x(self._x1)
            x_m = round(self._x1 * s, 2)
            self._draw_arrow(px)
            # label above arrow
            lbl = self.addText(f"x = {x_m} m")
            lbl.setFont(QFont("Arial", 7, QFont.Bold))
            lbl.setDefaultTextColor(self.C_LOAD)
            lbl.setPos(px - lbl.boundingRect().width() / 2, top_y - 14)

        else:   # Line or Area
            x_start = self._scene_x(self._x1)
            x_end   = self._scene_x(self._x2)
            if x_end < x_start:
                x_start, x_end = x_end, x_start

            if lt == "Area":
                self.addRect(x_start, top_y,
                             x_end - x_start, tip_y - top_y,
                             self._pen(self.C_LOAD, 1, Qt.DashLine),
                             QBrush(self.C_AREA))

            # horizontal bar
            self.addLine(x_start, top_y, x_end, top_y,
                         self._pen(self.C_LOAD, 2.0))

            # evenly spaced arrows
            n = max(2, int((x_end - x_start) / 40))
            for i in range(n + 1):
                ax = x_start + i * (x_end - x_start) / n
                self._draw_arrow(ax)

            x1_m = round(self._x1 * s, 2)
            x2_m = round(self._x2 * s, 2)
            lbl = self.addText(f"x₁ = {x1_m} m   x₂ = {x2_m} m")
            lbl.setFont(QFont("Arial", 7, QFont.Bold))
            lbl.setDefaultTextColor(self.C_LOAD)
            mid  = (x_start + x_end) / 2
            lbl.setPos(mid - lbl.boundingRect().width() / 2, top_y - 14)

    def _dim_line(self):
        dim_y = self.BEAM_Y + self.BEAM_H + 36
        pen   = self._pen(self.C_DIM, 1.0, Qt.DashLine)
        tick  = self._pen(self.C_DIM, 1.0)
        xl    = self.MARGIN
        xr    = self.W - self.MARGIN

        self.addLine(xl, dim_y, xr, dim_y, pen)
        for xx in (xl, xr):
            self.addLine(xx, dim_y - 5, xx, dim_y + 5, tick)

        sp = self.addText(f"Span = {self._span_m:.1f} m")
        sp.setFont(QFont("Arial", 8))
        sp.setDefaultTextColor(self.C_DIM)
        sp.setPos(self.W / 2 - sp.boundingRect().width() / 2, dim_y + 5)


# ═══════════════════════════════════════════════════════════════════════════════
#  CustomLoadTab
# ═══════════════════════════════════════════════════════════════════════════════

class CustomLoadTab(QWidget):

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.custom_load_items = getattr(owner, "custom_load_items", [])
        owner.custom_load_items = self.custom_load_items
        self.schema = CUSTOM_LOAD_TAB_SCHEMA
        self._build_ui()

    # ── Read real span from any available source ───────────────────────────────

    def _get_span(self) -> float:
        """
        Try multiple places where the span value might live in the app,
        falling back to 20.0 m if none are found.
        Priority:
          1. owner._main_window.span_input  (Basic Inputs QLineEdit)
          2. owner._main_window.cad_state dict
          3. owner itself has span_input
          4. Default 20.0
        """
        try:
            mw = self.owner._main_window
            val = float(mw.span_input.text())
            if val > 0:
                return val
        except Exception:
            pass
        try:
            mw  = self.owner._main_window
            val = float(mw.cad_state.get("span", 0))
            if val > 0:
                return val
        except Exception:
            pass
        try:
            val = float(self.owner.span_input.text())
            if val > 0:
                return val
        except Exception:
            pass
        return 20.0

    def _build_ui(self):
        owner  = self.owner
        schema = self.schema

        self.setStyleSheet("background-color: #f0f0f0;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f0f0f0; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #f0f0f0;")

        page_layout = QVBoxLayout(scroll_content)
        page_layout.setContentsMargins(8, 8, 8, 8)
        page_layout.setSpacing(8)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(12)

        label_style   = "font-size: 11px; color: #2a2a2a; background: transparent; border: none;"
        heading_style = "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"

        label_width = schema.get("label_width", 280)
        field_width = schema.get("field_width", 140)

        # ── LEFT COLUMN ──────────────────────────────────────────────────────

        left_column = QVBoxLayout()
        left_column.setContentsMargins(0, 0, 0, 0)
        left_column.setSpacing(8)

        # Bridge geometry placeholder
        diagram = QFrame()
        diagram.setMinimumSize(QSize(380, 130))
        diagram.setMaximumHeight(130)
        diagram.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #d0d0d0; }"
        )
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(8, 8, 8, 8)
        diagram_label = QLabel("Bridge Geometry\nDiagram")
        diagram_label.setAlignment(Qt.AlignCenter)
        diagram_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #2a2a2a; background: transparent; border: none;"
        )
        diagram_layout.addWidget(diagram_label, 1)
        left_column.addWidget(diagram)

        # ── Input card ──────────────────────────────────────────────────────
        input_card = owner._create_card()
        input_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(8)

        title = QLabel("Custom Load Input Add/Edit:")
        title.setStyleSheet(heading_style)
        input_layout.addWidget(title)

        all_fields_layout = QVBoxLayout()
        all_fields_layout.setContentsMargins(0, 0, 0, 0)
        all_fields_layout.setSpacing(10)

        # Load case
        load_case_field = schema["fields"]["load_case"]
        load_case_row   = QHBoxLayout()
        load_case_row.setSpacing(8)
        lbl = QLabel(load_case_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        owner.custom_load_case_combo = QComboBox()
        owner.custom_load_case_combo.addItems(schema["load_case_choices"])
        owner.custom_load_case_combo.setFixedWidth(field_width)
        apply_field_style(owner.custom_load_case_combo)
        load_case_row.addWidget(lbl)
        load_case_row.addWidget(owner.custom_load_case_combo)
        custom_name_field = schema["fields"]["custom_load_case_name"]
        owner.custom_load_case_name_input = QLineEdit()
        owner.custom_load_case_name_input.setPlaceholderText(custom_name_field["placeholder"])
        owner.custom_load_case_name_input.setFixedWidth(field_width)
        owner.custom_load_case_name_input.setEnabled(custom_name_field["enabled"])
        apply_field_style(owner.custom_load_case_name_input)
        load_case_row.addWidget(owner.custom_load_case_name_input)
        load_case_row.addStretch()
        all_fields_layout.addLayout(load_case_row)

        # Load type
        load_type_field = schema["fields"]["load_type"]
        load_type_row   = QHBoxLayout()
        load_type_row.setSpacing(8)
        lbl = QLabel(load_type_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        owner.custom_load_type_combo = QComboBox()
        owner.custom_load_type_combo.addItems(schema["load_type_choices"])
        owner.custom_load_type_combo.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_load_type_combo)
        load_type_row.addWidget(lbl)
        load_type_row.addWidget(owner.custom_load_type_combo)
        load_type_row.addStretch()
        all_fields_layout.addLayout(load_type_row)

        input_layout.addLayout(all_fields_layout)

        # Stacked widget (Point / Line)
        self.custom_load_stack = QStackedWidget()
        self.custom_load_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.custom_load_stack.setStyleSheet(
            "QStackedWidget { border: none; background: transparent; }"
            "QWidget#customPointWidget, QWidget#customLineWidget { background: transparent; }"
        )

        # ── Point page ──
        point_widget = QWidget()
        point_widget.setObjectName("customPointWidget")
        point_layout = QVBoxLayout(point_widget)
        point_layout.setContentsMargins(0, 0, 0, 0)
        point_layout.setSpacing(10)

        point_left_field = schema["fields"]["point_left"]
        point_left_row   = QHBoxLayout()
        point_left_row.setSpacing(8)
        lbl = QLabel(point_left_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        owner.custom_point_left_input = QLineEdit()
        owner.custom_point_left_input.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_point_left_input)
        self._apply_validator(owner.custom_point_left_input, point_left_field.get("validator"))
        point_left_row.addWidget(lbl)
        point_left_row.addWidget(owner.custom_point_left_input)
        point_left_row.addStretch()
        point_layout.addLayout(point_left_row)

        point_bearing_field = schema["fields"]["point_bearing"]
        point_bearing_row   = QHBoxLayout()
        point_bearing_row.setSpacing(8)
        lbl = QLabel(point_bearing_field["label"])
        lbl.setStyleSheet(label_style)
        lbl.setFixedWidth(label_width)
        owner.custom_point_bearing_input = QLineEdit()
        owner.custom_point_bearing_input.setFixedWidth(field_width * 2 + 8)
        apply_field_style(owner.custom_point_bearing_input)
        self._apply_validator(owner.custom_point_bearing_input, point_bearing_field.get("validator"))
        point_bearing_row.addWidget(lbl)
        point_bearing_row.addWidget(owner.custom_point_bearing_input)
        point_bearing_row.addStretch()
        point_layout.addLayout(point_bearing_row)

        self.custom_load_stack.addWidget(point_widget)

        # ── Line/Area page ──
        line_widget = QWidget()
        line_widget.setObjectName("customLineWidget")
        line_layout = QVBoxLayout(line_widget)
        line_layout.setContentsMargins(0, 0, 0, 0)
        line_layout.setSpacing(10)

        line_left_start_field = schema["fields"]["line_left_start"]
        line_left_end_field   = schema["fields"]["line_left_end"]
        left_edge_row = QHBoxLayout()
        left_edge_row.setSpacing(4)
        left_label = QLabel(line_left_start_field["label"])
        left_label.setStyleSheet(label_style)
        left_label.setFixedWidth(label_width)
        left_start_container = QVBoxLayout()
        left_start_container.setSpacing(4)
        left_start_lbl = QLabel(line_left_start_field["sub_label"])
        left_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_start = QLineEdit()
        owner.custom_line_left_start.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_left_start)
        self._apply_validator(owner.custom_line_left_start, line_left_start_field.get("validator"))
        left_start_container.addWidget(left_start_lbl)
        left_start_container.addWidget(owner.custom_line_left_start)
        left_end_container = QVBoxLayout()
        left_end_container.setSpacing(4)
        left_end_lbl = QLabel(line_left_end_field["sub_label"])
        left_end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        left_end_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_left_end = QLineEdit()
        owner.custom_line_left_end.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_left_end)
        self._apply_validator(owner.custom_line_left_end, line_left_end_field.get("validator"))
        left_end_container.addWidget(left_end_lbl)
        left_end_container.addWidget(owner.custom_line_left_end)
        left_edge_row.addWidget(left_label)
        left_edge_row.addLayout(left_start_container)
        left_edge_row.addLayout(left_end_container)
        left_edge_row.addStretch()
        line_layout.addLayout(left_edge_row)

        line_bearing_start_field = schema["fields"]["line_bearing_start"]
        line_bearing_end_field   = schema["fields"]["line_bearing_end"]
        bearing_row = QHBoxLayout()
        bearing_row.setSpacing(4)
        bearing_label = QLabel(line_bearing_start_field["label"])
        bearing_label.setStyleSheet(label_style)
        bearing_label.setFixedWidth(label_width)
        bearing_start_container = QVBoxLayout()
        bearing_start_container.setSpacing(4)
        bearing_start_lbl = QLabel(line_bearing_start_field["sub_label"])
        bearing_start_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_start_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_start = QLineEdit()
        owner.custom_line_bearing_start.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_bearing_start)
        self._apply_validator(owner.custom_line_bearing_start, line_bearing_start_field.get("validator"))
        bearing_start_container.addWidget(bearing_start_lbl)
        bearing_start_container.addWidget(owner.custom_line_bearing_start)
        bearing_end_container = QVBoxLayout()
        bearing_end_container.setSpacing(4)
        bearing_end_lbl = QLabel(line_bearing_end_field["sub_label"])
        bearing_end_lbl.setStyleSheet("font-size: 9px; color: #505050;")
        bearing_end_lbl.setAlignment(Qt.AlignCenter)
        owner.custom_line_bearing_end = QLineEdit()
        owner.custom_line_bearing_end.setFixedWidth(field_width + 2)
        apply_field_style(owner.custom_line_bearing_end)
        self._apply_validator(owner.custom_line_bearing_end, line_bearing_end_field.get("validator"))
        bearing_end_container.addWidget(bearing_end_lbl)
        bearing_end_container.addWidget(owner.custom_line_bearing_end)
        bearing_row.addWidget(bearing_label)
        bearing_row.addLayout(bearing_start_container)
        bearing_row.addLayout(bearing_end_container)
        bearing_row.addStretch()
        line_layout.addLayout(bearing_row)

        self.custom_load_stack.addWidget(line_widget)

        input_layout.addWidget(self.custom_load_stack)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setMinimumWidth(120)
        save_btn.setFixedHeight(28)
        save_btn.setStyleSheet(
            "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px;"
            "  padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
            "QPushButton:hover { background: #f0f0f0; }"
            "QPushButton:pressed { background: #e0e0e0; }"
        )
        save_row = QHBoxLayout()
        save_row.setContentsMargins(0, 12, 0, 0)
        save_row.addStretch()
        save_row.addWidget(save_btn)
        save_row.addStretch()
        input_layout.addLayout(save_row)

        left_column.addWidget(input_card)

        # ── Table card ──
        list_card = owner._create_card()
        list_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        list_card.setMinimumHeight(250)
        list_layout = QVBoxLayout(list_card)
        list_layout.setContentsMargins(4, 10, 10, 10)
        list_layout.setSpacing(8)

        list_title = QLabel("Custom Load Name")
        list_title.setStyleSheet(heading_style)
        list_layout.addWidget(list_title)

        controls_row = QHBoxLayout()
        controls_row.setSpacing(6)
        owner.custom_edit_btn   = QPushButton("Edit")
        owner.custom_delete_btn = QPushButton("Delete")
        for btn in (owner.custom_edit_btn, owner.custom_delete_btn):
            btn.setFixedWidth(55)
            btn.setStyleSheet(
                "QPushButton { background: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px;"
                "  padding: 3px 8px; font-size: 11px; color: #2a2a2a; }"
                "QPushButton:hover { background: #f0f0f0; }"
                "QPushButton:pressed { background: #e0e0e0; }"
            )
            controls_row.addWidget(btn)
        controls_row.addStretch()
        list_layout.addLayout(controls_row)

        table_frame = QFrame()
        table_frame.setStyleSheet("QFrame { border: none; background: #ffffff; }")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.custom_load_table = QTableWidget(0, 4)
        self.custom_load_table.setFrameStyle(QFrame.NoFrame)
        self.custom_load_table.setContentsMargins(0, 0, 0, 0)
        self.custom_load_table.viewport().setContentsMargins(0, 0, 0, 0)
        self.custom_load_table.setShowGrid(True)
        self.custom_load_table.setHorizontalHeaderLabels([
            "Load Case", "Load Type",
            "Distance from Left (m)", "Distance from Bearing (m)",
        ])
        for col in range(4):
            self.custom_load_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        self.custom_load_table.verticalHeader().setVisible(False)
        self.custom_load_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.custom_load_table.setSelectionMode(QTableWidget.SingleSelection)
        self.custom_load_table.setCornerButtonEnabled(False)
        self.custom_load_table.setStyleSheet("""
            QTableWidget { background: #ffffff; border: 1px solid #a0a0a0; gridline-color: #d0d0d0; }
            QTableWidget::item { padding: 4px; font-size: 10px; color: #3a3a3a; border-bottom: 1px solid #c0c0c0; }
            QTableWidget::item:selected { background: #d0e8ff; }
            QHeaderView::section { color: #2a2a2a; background: #f0f0f0; font-size: 10px; font-weight: 600;
                padding: 5px; border: none; border-right: 1px solid #d0d0d0; border-bottom: 1px solid #d0d0d0; }
        """)
        self.custom_load_table.setMinimumHeight(180)
        table_layout.addWidget(self.custom_load_table)
        list_layout.addWidget(table_frame)
        left_column.addWidget(list_card)

        # ── RIGHT COLUMN — 2D Load Visualisation ─────────────────────────────
        right_card = owner._create_card()
        right_card.setStyleSheet(
            "QFrame { border: 1px solid #a0a0a0; border-radius: 4px; background-color: #ffffff; }"
        )
        right_card.setMinimumWidth(260)
        right_card.setMinimumHeight(560)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(6)

        # ── Cross-section title ──
        viz_title = QLabel("Load Visualisation")
        viz_title.setAlignment(Qt.AlignCenter)
        viz_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        )
        right_layout.addWidget(viz_title)

        # ── Cross-section scene + view ──
        self._load_scene = BridgeLoadScene()
        self._load_view  = QGraphicsView(self._load_scene)
        self._load_view.setRenderHint(QPainter.Antialiasing)
        self._load_view.setRenderHint(QPainter.TextAntialiasing)
        self._load_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._load_view.setStyleSheet(
            "background: #f8f8f8; border: 1px solid #cccccc; border-radius: 4px;"
        )
        self._load_view.setMinimumHeight(240)
        right_layout.addWidget(self._load_view, stretch=3)

        # ── Legend ──
        legend_lbl = QLabel(
            "<span style='color:#e53935;'>▼</span>  Red arrows = applied load &nbsp;&nbsp;"
            "<span style='color:#546e7a;'>■</span>  Blue-grey = steel girders"
        )
        legend_lbl.setStyleSheet(
            "font-size: 9px; color: #555555; background: transparent; border: none;"
        )
        legend_lbl.setWordWrap(True)
        right_layout.addWidget(legend_lbl)

        # ── Divider ──
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #cccccc;")
        right_layout.addWidget(divider)

        # ── Elevation view title ──
        elev_title = QLabel("Elevation View  (Bonus)")
        elev_title.setAlignment(Qt.AlignCenter)
        elev_title.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #1a1a1a; background: transparent; border: none;"
        )
        right_layout.addWidget(elev_title)

        # ── Elevation scene + view ──
        self._elev_scene = ElevationScene()
        self._elev_view  = QGraphicsView(self._elev_scene)
        self._elev_view.setRenderHint(QPainter.Antialiasing)
        self._elev_view.setRenderHint(QPainter.TextAntialiasing)
        self._elev_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._elev_view.setFixedHeight(165)
        self._elev_view.setStyleSheet(
            "background: #f8f8f8; border: 1px solid #cccccc; border-radius: 4px;"
        )
        right_layout.addWidget(self._elev_view, stretch=2)

        # ── Assemble row ──────────────────────────────────────────────────────
        content_row.addLayout(left_column, 3)
        content_row.addWidget(right_card, 2)
        page_layout.addLayout(content_row)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # ── Connect signals ───────────────────────────────────────────────────
        owner.custom_load_type_combo.currentTextChanged.connect(self._on_custom_load_type_changed)
        self._on_custom_load_type_changed(owner.custom_load_type_combo.currentText())

        save_btn.clicked.connect(self._on_save_custom_load)
        owner.custom_delete_btn.clicked.connect(self._on_delete_custom_load)
        owner.custom_edit_btn.clicked.connect(self._on_edit_custom_load)
        owner.custom_load_case_combo.currentTextChanged.connect(self._on_load_case_changed)

        # Live diagram updates — fire on every keystroke
        owner.custom_load_type_combo.currentTextChanged.connect(self._refresh_diagram)
        owner.custom_point_left_input.textChanged.connect(self._refresh_diagram)
        owner.custom_line_left_start.textChanged.connect(self._refresh_diagram)
        owner.custom_line_left_end.textChanged.connect(self._refresh_diagram)

        self._refresh_custom_load_table()
        self._refresh_diagram()

    # ── Diagram refresh — updates BOTH cross-section AND elevation ─────────────

    def _refresh_diagram(self, *_):
        owner    = self.owner
        lt       = owner.custom_load_type_combo.currentText()   # "Point" / "Line/Area"
        span     = self._get_span()

        x1 = x2 = 0.4

        if lt == "Point":
            try:
                raw = float(owner.custom_point_left_input.text())
                x1  = max(0.0, min(1.0, raw / span))
            except ValueError:
                x1 = 0.4
            x2 = x1

        else:   # Line / Area
            try:
                x1 = max(0.0, min(1.0, float(owner.custom_line_left_start.text()) / span))
            except ValueError:
                x1 = 0.3
            try:
                x2 = max(0.0, min(1.0, float(owner.custom_line_left_end.text()) / span))
            except ValueError:
                x2 = 0.7

        # Map combo text → scene load type string
        scene_lt = "Point" if lt == "Point" else ("Area" if "Area" in lt else "Line")

        # ── Update cross-section view ──
        self._load_scene.update_load(scene_lt, x1, x2, span_m=span)
        self._load_view.fitInView(self._load_scene.sceneRect(), Qt.KeepAspectRatio)

        # ── Update elevation view ──
        self._elev_scene.update_load(scene_lt, x1, x2, span_m=span)
        self._elev_view.fitInView(self._elev_scene.sceneRect(), Qt.KeepAspectRatio)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_view.fitInView(self._load_scene.sceneRect(), Qt.KeepAspectRatio)
        self._elev_view.fitInView(self._elev_scene.sceneRect(), Qt.KeepAspectRatio)

    # ── Unchanged helpers ─────────────────────────────────────────────────────

    def _apply_validator(self, widget, validator_config):
        if not validator_config:
            return
        if validator_config["type"] == "double_range":
            validator = QDoubleValidator(
                validator_config["bottom"],
                validator_config["top"],
                validator_config.get("decimals", 2),
                widget,
            )
            validator.setNotation(QDoubleValidator.StandardNotation)
            widget.setValidator(validator)

    def _on_custom_load_type_changed(self, text):
        if text == "Point":
            self.custom_load_stack.setCurrentIndex(0)
        else:
            self.custom_load_stack.setCurrentIndex(1)
        self._refresh_diagram()

    def _on_load_case_changed(self, text):
        is_custom = (text == "Custom")
        self.owner.custom_load_case_name_input.setEnabled(is_custom)
        if not is_custom:
            self.owner.custom_load_case_name_input.clear()

    def _refresh_custom_load_table(self):
        self.custom_load_table.setRowCount(0)
        for row_idx, load_data in enumerate(self.custom_load_items):
            self.custom_load_table.insertRow(row_idx)
            load_case = load_data.get("load_case", "")
            if load_case == "Custom":
                load_case_display = load_data.get("custom_load_case_name", "custom")
            else:
                load_case_display = load_case
            item = QTableWidgetItem(load_case_display)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 0, item)
            load_type = load_data.get("load_type", "")
            item = QTableWidgetItem(load_type)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 1, item)
            if load_type == "Point":
                dist_left = load_data.get("point_left", "")
            else:
                start = load_data.get("line_left_start", "")
                end   = load_data.get("line_left_end", "")
                dist_left = f"{start} - {end}"
            item = QTableWidgetItem(dist_left)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 2, item)
            if load_type == "Point":
                dist_bearing = load_data.get("point_bearing", "")
            else:
                start = load_data.get("line_bearing_start", "")
                end   = load_data.get("line_bearing_end", "")
                dist_bearing = f"{start} - {end}"
            item = QTableWidgetItem(dist_bearing)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.custom_load_table.setItem(row_idx, 3, item)

    def _on_save_custom_load(self):
        owner = self.owner
        load_data = {
            "load_case": owner.custom_load_case_combo.currentText(),
            "load_type": owner.custom_load_type_combo.currentText(),
        }
        if owner.custom_load_case_combo.currentText() == "Custom":
            custom_name = owner.custom_load_case_name_input.text().strip()
            if not custom_name:
                CustomMessageBox(title="Invalid Input", text="Please provide a name for the Custom load case.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            load_data["custom_load_case_name"] = custom_name
        if owner.custom_load_type_combo.currentText() == "Point":
            point_l = owner.custom_point_left_input.text().strip()
            point_b = owner.custom_point_bearing_input.text().strip()
            if not point_l or not point_b:
                CustomMessageBox(title="Invalid Input", text="Please fill in all distance fields for the Point load.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            load_data["point_left"]    = point_l
            load_data["point_bearing"] = point_b
        else:
            line_l_start = owner.custom_line_left_start.text().strip()
            line_l_end   = owner.custom_line_left_end.text().strip()
            line_b_start = owner.custom_line_bearing_start.text().strip()
            line_b_end   = owner.custom_line_bearing_end.text().strip()
            if not line_l_start or not line_l_end or not line_b_start or not line_b_end:
                CustomMessageBox(title="Invalid Input", text="Please fill in all distance fields for the Line/Area load.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            try:
                if float(line_l_start) > float(line_l_end):
                    CustomMessageBox(title="Invalid Input", text="Distance from Left Edge Start cannot be greater than End.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                    return
                if float(line_b_start) > float(line_b_end):
                    CustomMessageBox(title="Invalid Input", text="Distance from Bearing Start cannot be greater than End.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                    return
            except ValueError:
                CustomMessageBox(title="Invalid Input", text="Distance fields must be numeric.", buttons=["OK"], dialogType=MessageBoxType.Warning).exec()
                return
            load_data["line_left_start"]    = line_l_start
            load_data["line_left_end"]      = line_l_end
            load_data["line_bearing_start"] = line_b_start
            load_data["line_bearing_end"]   = line_b_end
        if hasattr(self, "_editing_load_data") and self._editing_load_data:
            for i, item in enumerate(self.custom_load_items):
                if item == self._editing_load_data:
                    self.custom_load_items[i] = load_data
                    break
            self._editing_load_data = None
        else:
            self.custom_load_items.append(load_data)
        self._clear_inputs()
        self._refresh_custom_load_table()
        # Refresh diagram after save so it reflects the saved position
        self._refresh_diagram()
        CustomMessageBox(title="Saved", text="Custom load has been saved.", buttons=["OK"], dialogType=MessageBoxType.Success).exec()

    def _on_edit_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            CustomMessageBox(title="Edit", text="Please select one custom load to edit.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()
            return
        if len(selected_rows) > 1:
            CustomMessageBox(title="Edit", text="Please select only one custom load to edit.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()
            return
        row_idx   = selected_rows[0].row()
        load_data = self.custom_load_items[row_idx]
        self._editing_load_data = load_data
        owner = self.owner
        index = owner.custom_load_case_combo.findText(load_data.get("load_case", "DL"))
        if index >= 0:
            owner.custom_load_case_combo.setCurrentIndex(index)
        if load_data.get("load_case") == "Custom":
            owner.custom_load_case_name_input.setText(load_data.get("custom_load_case_name", ""))
        index = owner.custom_load_type_combo.findText(load_data.get("load_type", "Point"))
        if index >= 0:
            owner.custom_load_type_combo.setCurrentIndex(index)
        if load_data.get("load_type") == "Point":
            owner.custom_point_left_input.setText(load_data.get("point_left", ""))
            owner.custom_point_bearing_input.setText(load_data.get("point_bearing", ""))
        else:
            owner.custom_line_left_start.setText(load_data.get("line_left_start", ""))
            owner.custom_line_left_end.setText(load_data.get("line_left_end", ""))
            owner.custom_line_bearing_start.setText(load_data.get("line_bearing_start", ""))
            owner.custom_line_bearing_end.setText(load_data.get("line_bearing_end", ""))

    def _on_delete_custom_load(self):
        selected_rows = self.custom_load_table.selectionModel().selectedRows()
        if len(selected_rows) == 0:
            CustomMessageBox(title="Delete", text="Please select at least one custom load to delete.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()
            return
        rows_to_delete = sorted([row.row() for row in selected_rows], reverse=True)
        for row_idx in rows_to_delete:
            if 0 <= row_idx < len(self.custom_load_items):
                del self.custom_load_items[row_idx]
        self._refresh_custom_load_table()
        CustomMessageBox(title="Deleted", text=f"{len(rows_to_delete)} custom load(s) deleted.", buttons=["OK"], dialogType=MessageBoxType.Information).exec()

    def _clear_inputs(self):
        owner = self.owner
        owner.custom_load_case_combo.setCurrentIndex(0)
        owner.custom_load_case_name_input.clear()
        owner.custom_load_type_combo.setCurrentIndex(0)
        owner.custom_point_left_input.clear()
        owner.custom_point_bearing_input.clear()
        owner.custom_line_left_start.clear()
        owner.custom_line_left_end.clear()
        owner.custom_line_bearing_start.clear()
        owner.custom_line_bearing_end.clear()

    def reset_defaults(self):
        self._clear_inputs()
        self.owner.custom_load_case_name_input.setEnabled(False)
        self.custom_load_items.clear()
        self._refresh_custom_load_table()
        if hasattr(self, "_editing_load_data"):
            self._editing_load_data = None