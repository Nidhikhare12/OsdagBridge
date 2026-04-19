import math
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
    QGraphicsLineItem,
    QGraphicsSimpleTextItem,
)
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QPainter, QFont
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer


class CustomLoadCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self._first_render = True

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.load_data = None
        self.bridge_width = 10.0
        self.span_length = 20.0
        self._view = "cross_section"
        self._last_bw = 0.0  # help with zoom stability

        self.setStyleSheet("background-color: transparent; border: none;")
        self.setAlignment(Qt.AlignCenter)
        self._updating = False

    def set_load_data(self, data, bridge_width=10.0, span_length=20.0):
        self.load_data = data
        self.bridge_width = bridge_width if bridge_width > 0 else 10.0
        self.span_length = span_length if span_length > 0 else 20.0
        
        # get dimensions based on current view mode
        phys_len = self.bridge_width if self._view == "cross_section" else self.span_length
        bw = max(phys_len, 1.0)
        
        # only zoom out if the size changes a lot (to stay stable while typing)
        significant_change = abs(bw - self._last_bw) / bw > 0.01 if self._last_bw > 0 else True
        
        self.draw_scene(fit_view=(self._first_render or significant_change))
        
        self._first_render = False
        self._last_bw = bw

    def set_view(self, view_mode):
        # if mode is different, we definitely want a fresh view
        mode_changed = (self._view != view_mode)
        self._view = view_mode
        self.draw_scene(fit_view=mode_changed)

    def showEvent(self, event):
        super().showEvent(event)
        # give it a moment to show up then fit the view
        QTimer.singleShot(50, lambda: self.draw_scene(fit_view=True))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.draw_scene()

    def zoom_in(self):
        self.scale(1.5, 1.5)

    def zoom_out(self):
        self.scale(1 / 1.5, 1 / 1.5)

    def reset_view(self):
        self.draw_scene(fit_view=True)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()
        event.accept()


    def draw_dimension_line(self, px1, px2, text, y_pos):
        pen_dash = QPen(Qt.black, 3, Qt.DashLine)
        pen_solid = QPen(Qt.black, 3, Qt.SolidLine)

        # Main dashed line
        line = QGraphicsLineItem(px1, y_pos, px2, y_pos)
        line.setPen(pen_dash)
        self.scene.addItem(line)

        # End ticks
        for px in (px1, px2):
            tick = QGraphicsLineItem(px, y_pos - 10, px, y_pos + 10)
            tick.setPen(pen_solid)
            self.scene.addItem(tick)

        if text:
            # Text with white background to break the dashed line
            font = QFont("Arial", 18)
            txt = QGraphicsSimpleTextItem(text)
            txt.setFont(font)
            txt.setBrush(QBrush(QColor("#1a1a1a")))

            txt_w = txt.boundingRect().width()
            txt_h = txt.boundingRect().height()
            cx = (px1 + px2) / 2

            bg_rect = QGraphicsRectItem(cx - txt_w / 2 - 8, y_pos - txt_h / 2 - 4, txt_w + 16, txt_h + 8)
            bg_rect.setBrush(QBrush(QColor("#ffffff")))
            bg_rect.setPen(QPen(Qt.NoPen))
            bg_rect.setZValue(1)
            self.scene.addItem(bg_rect)

            txt.setPos(cx - txt_w / 2, y_pos - txt_h / 2)
            txt.setZValue(2)
            self.scene.addItem(txt)



    def draw_scene(self, fit_view=False):
        if getattr(self, "_updating", False):
            return
        self._updating = True

        try:
            self.scene.clear()
            self.scene.setBackgroundBrush(QColor("#f5f7f9"))

            w, h = 1000.0, 400.0

            if not self.load_data:
                self._zoom_empty(w, h)
                return

            load_type = self.load_data.get("type", "").lower()
            if load_type not in ("point", "line", "area"):
                self._zoom_empty(w, h)
                return

            phys_len = (
                self.bridge_width if self._view == "cross_section" else self.span_length
            )
            bw = max(phys_len, 1.0)

            if self._view == "cross_section":
                x1 = self.load_data.get("dist_left_start", 0.0)
                x2 = self.load_data.get("dist_left_end", 0.0)
            else:
                x1 = self.load_data.get("dist_bear_start", 0.0)
                x2 = self.load_data.get("dist_bear_end", 0.0)

            x1 = max(0.0, min(x1, bw))
            x2 = max(0.0, min(x2, bw))
            if x1 > x2:
                x1, x2 = x2, x1

            if load_type == "area" and abs(x2 - x1) < 0.1:
                x2 = x1 + 0.1

            deck_top = h / 2.0
            deck_thick = 40.0
            deck_bot = deck_top + deck_thick

            margin = 150.0
            scale_x = (w - 2 * margin) / bw

            def map_x(x):
                return margin + x * scale_x

            px_left = map_x(0)
            px_right = map_x(bw)
            deck_w = px_right - px_left

            # Grid overlay with markers
            self._draw_grid(w, h, bw, margin, scale_x, deck_bot + 60.0)

            deck_color = QColor(175, 175, 175)
            deck_pen = QColor(60, 60, 60)

            # Arrows are red (#D32F2F)
            load_color = QColor("#D32F2F")

            # Draw Base Bridge
            deck_rect = QGraphicsRectItem(px_left, deck_top, deck_w, deck_thick)
            deck_rect.setBrush(QBrush(deck_color))
            deck_rect.setPen(QPen(deck_pen, 2))
            deck_rect.setZValue(0)
            self.scene.addItem(deck_rect)

            if self._view == "cross_section":
                # Girders across cross-section
                g_w = max(20.0, deck_w * 0.04)
                g_h = deck_thick * 1.5
                girder_positions = [0.2, 0.5, 0.8]
                girder_labels = ["G1", "G2", "G3"]
                for i, label in zip(girder_positions, girder_labels):
                    gx = px_left + deck_w * i - g_w / 2.0
                    g_rect = QGraphicsRectItem(gx, deck_bot, g_w, g_h)
                    g_rect.setBrush(QBrush(deck_color))
                    g_rect.setPen(QPen(deck_pen, 2))
                    g_rect.setZValue(0)
                    self.scene.addItem(g_rect)

                    lbl = QGraphicsSimpleTextItem(label)
                    lbl.setFont(QFont("Arial", 14, QFont.Bold))
                    lbl.setBrush(QBrush(QColor("#1a1a1a")))
                    lbl.setZValue(1)
                    lbl_h = lbl.boundingRect().height()
                    lbl.setPos(gx + g_w / 2 - lbl.boundingRect().width() / 2,
                                deck_bot + g_h / 2 - lbl_h / 2)
                    self.scene.addItem(lbl)
            else:
                # Supports at bearing ends
                sup_w = 40.0
                sup_h = 40.0
                for px in (px_left, px_right):
                    poly = QPolygonF(
                        [
                            QPointF(px, deck_bot),
                            QPointF(px - sup_w / 2, deck_bot + sup_h),
                            QPointF(px + sup_w / 2, deck_bot + sup_h),
                        ]
                    )
                    sup = QGraphicsPolygonItem(poly)
                    sup.setBrush(QBrush(QColor(150, 150, 150)))
                    sup.setPen(QPen(deck_pen, 2))
                    sup.setZValue(0)
                    self.scene.addItem(sup)


            title_text = {"point": "Point Load", "line": "Line Load", "area": "Area Load"}.get(load_type, "Load")
            title_item = QGraphicsSimpleTextItem(title_text)
            title_item.setFont(QFont("Arial", 20, QFont.Bold))
            title_item.setBrush(QBrush(QColor("#1e293b")))
            title_item.setZValue(2)
            title_item.setPos(w / 2.0 - title_item.boundingRect().width() / 2.0, 50)
            self.scene.addItem(title_item)

            # load positioning
            y_end = deck_top
            y_start = y_end - 80.0

            mag = self.load_data.get("magnitude", "")
            unit = {"line": "kN/m", "area": "kN/m²"}.get(load_type, "kN")
            mag_txt = f"{mag} {unit}" if mag else ""

            def draw_arrow(x):
                line = QGraphicsLineItem(x, y_start, x, y_end)
                line.setPen(QPen(load_color, 6))
                line.setZValue(1)
                self.scene.addItem(line)

                head = QGraphicsPolygonItem(
                    QPolygonF(
                        [
                            QPointF(x, y_end),
                            QPointF(x - 12, y_end - 18),
                            QPointF(x + 12, y_end - 18),
                        ]
                    )
                )
                head.setBrush(QBrush(load_color))
                head.setPen(QPen(Qt.NoPen))
                head.setZValue(1)
                self.scene.addItem(head)

            def add_small_label(t, mag_text, cx):
                combined = f"{t} = {mag_text}" if mag_text else t
                txt = QGraphicsSimpleTextItem(combined)
                txt.setFont(QFont("Arial", 16, QFont.Bold))
                txt.setBrush(QBrush(load_color))
                txt.setZValue(2)
                txt.setPos(cx - txt.boundingRect().width() / 2, y_start - 35)
                self.scene.addItem(txt)

            px1 = map_x(x1)
            px2 = map_x(x2)

            if load_type == "point":
                draw_arrow(px1)
                add_small_label("P", mag_txt, px1)
                self.draw_dimension_line(px_left, px1, f"x = {x1:.1f} m", deck_bot + 120.0)

            elif load_type == "line":
                dist = px2 - px1
                if dist < 40:
                    draw_arrow((px1 + px2) / 2.0)
                else:
                    num_arrows = max(2, int(dist / 60.0) + 1)
                    for i in range(num_arrows):
                        draw_arrow(px1 + dist * (i / (num_arrows - 1)))

                    horiz = QGraphicsLineItem(px1, y_start, px2, y_start)
                    horiz.setPen(QPen(load_color, 4))
                    horiz.setZValue(1)
                    self.scene.addItem(horiz)
                add_small_label("w", mag_txt, (px1 + px2) / 2)
                self.draw_dimension_line(px1, px2, f"x₁ = {x1:.1f} m to x₂ = {x2:.1f} m", deck_bot + 120.0)

            elif load_type == "area":
                dist = px2 - px1
                w_rect = max(dist, 2.0)
                area = QGraphicsRectItem(px1, y_start, w_rect, y_end - y_start)
                col = QColor(load_color)
                col.setAlpha(80)
                area.setBrush(QBrush(col))
                if dist < 40:
                    area.setPen(QPen(Qt.NoPen))
                else:
                    area.setPen(QPen(load_color, 2, Qt.DashLine))
                area.setZValue(1)
                self.scene.addItem(area)

                if dist < 40:
                    draw_arrow((px1 + px2) / 2.0)
                else:
                    num_arrows = max(2, int(dist / 60.0) + 1)
                    for i in range(num_arrows):
                        draw_arrow(px1 + dist * (i / (num_arrows - 1)))
                add_small_label("q", mag_txt, px1 + w_rect / 2.0)
                self.draw_dimension_line(px1, px2, f"A = {x1:.1f} m – {x2:.1f} m", deck_bot + 120.0)

            rect = QRectF(0, 0, w, h)
            self.scene.setSceneRect(rect)
            if fit_view:
                self.fitInView(rect, Qt.KeepAspectRatio)

        finally:
            self._updating = False

    def _draw_grid(self, logical_w, logical_h, bw, margin, scale_x, axis_y):
        grid_pen = QPen(QColor(210, 215, 220), 1, Qt.SolidLine)
        grid_step_m = bw / 10.0
        if grid_step_m < 0.1:
            grid_step_m = 0.1

        px_left = margin + 0 * scale_x
        px_right = margin + bw * scale_x

        # Grid lines (vertical)
        for i in range(11):
            x_m = i * grid_step_m
            px = margin + x_m * scale_x
            line = self.scene.addLine(px, axis_y - 200, px, axis_y + 50, grid_pen)
            line.setZValue(-1)

        axis_line = QGraphicsLineItem(px_left, axis_y, px_right, axis_y)
        axis_line.setPen(QPen(Qt.black, 2))
        axis_line.setZValue(0)
        self.scene.addItem(axis_line)

        tick_font = QFont("Arial", 14, QFont.Bold)
        for i in range(11):
            if i % 2 != 0 and i != 10:
                continue  # fewer labels
            x_m = i * grid_step_m
            px = margin + x_m * scale_x
            tick = QGraphicsLineItem(px, axis_y - 6, px, axis_y + 6)
            tick.setPen(QPen(Qt.black, 2))
            tick.setZValue(0)
            self.scene.addItem(tick)

            lbl_text = f"{x_m:g} m"
            # Switch to SimpleTextItem to avoid setPointSize warnings in some Qt versions
            txt = QGraphicsSimpleTextItem(lbl_text)
            txt.setFont(tick_font)
            txt.setBrush(QBrush(Qt.black))
            txt.setPos(px - txt.boundingRect().width() / 2, axis_y + 10)
            self.scene.addItem(txt)

    def _zoom_empty(self, logical_w, logical_h):
        rect = QRectF(0, 0, logical_w, logical_h)
        self.scene.setSceneRect(rect)
        self.fitInView(rect, Qt.KeepAspectRatio)
