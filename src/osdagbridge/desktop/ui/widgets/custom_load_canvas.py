import math
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsSimpleTextItem
from PySide6.QtGui import QPen, QBrush, QColor, QPolygonF, QPainter, QFont
from PySide6.QtCore import Qt, QPointF, QRectF

class CustomLoadCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.load_data = None
        self.bridge_width = 10.0
        
        self.setStyleSheet("background-color: transparent; border: none;")
        self._updating = False

    def set_load_data(self, data, bridge_width=10.0):
        self.load_data = data
        self.bridge_width = bridge_width if bridge_width > 0 else 10.0
        self.draw_scene()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.draw_scene()

    def draw_scene(self):
        if getattr(self, "_updating", False):
            return
        self._updating = True
        
        try:
            self.scene.clear()
            self.scene.setBackgroundBrush(QColor("#f5f5f5"))
            
            w, h = 1000.0, 400.0
            self._draw_grid(w, h)
            
            if not self.load_data:
                self._zoom_empty(w, h)
                return
            
            load_type = self.load_data.get("type", "").lower()
            if load_type not in ("point", "line", "area"):
                self._zoom_empty(w, h)
                return
                
            bw = max(self.bridge_width, 1.0)
            x1 = max(0.0, min(self.load_data.get("x_start", 0.0), bw))
            x2 = max(0.0, min(self.load_data.get("x_end", 0.0), bw))
            
            if x1 > x2:
                x1, x2 = x2, x1
                
            # force a small width for area loads so they don't collapse
            if load_type == "area" and abs(x2 - x1) < 0.1:
                x2 = x1 + 0.1
                
            deck_top = h / 2.0
            deck_thick = 40.0
            deck_bot = deck_top + deck_thick
            
            margin = 100.0
            scale_x = (w - 2 * margin) / bw
            
            def map_x(x): return margin + x * scale_x
                
            px_left = map_x(0)
            px_right = map_x(bw)
            deck_w = px_right - px_left
            
            deck_color = QColor(210, 210, 210)
            deck_pen = QColor(80, 80, 80)
            load_color = QColor(220, 0, 0)
            
            # deck
            deck_rect = QGraphicsRectItem(px_left, deck_top, deck_w, deck_thick)
            deck_rect.setBrush(QBrush(deck_color))
            deck_rect.setPen(QPen(deck_pen, 1))
            deck_rect.setZValue(0)
            self.scene.addItem(deck_rect)
            
            # clear axis line under deck
            axis_y = deck_bot + 60.0
            axis_line = QGraphicsLineItem(px_left, axis_y, px_right, axis_y)
            axis_line.setPen(QPen(Qt.black, 2))
            axis_line.setZValue(0)
            self.scene.addItem(axis_line)
            
            tick_font = QFont("Arial", 14, QFont.Bold)
            
            for ratio in (0.0, 0.5, 1.0):
                tx = map_x(ratio * bw)
                tick = QGraphicsLineItem(tx, axis_y - 8, tx, axis_y + 8)
                tick.setPen(QPen(Qt.black, 2))
                tick.setZValue(0)
                self.scene.addItem(tick)
                
                lbl = "0 m" if ratio == 0.0 else f"{ratio * bw:g} m"
                txt = self.scene.addText(lbl, tick_font)
                txt.setDefaultTextColor(QColor(0, 0, 0))
                txt.setPos(tx - txt.boundingRect().width() / 2, axis_y + 10)
            
            # girders (approximate visual)
            g_w = max(20.0, deck_w * 0.04)
            g_h = deck_thick * 1.5
            for i in (0.2, 0.5, 0.8):
                gx = px_left + deck_w * i - g_w / 2.0
                g_rect = QGraphicsRectItem(gx, deck_bot, g_w, g_h)
                g_rect.setBrush(QBrush(deck_color))
                g_rect.setPen(QPen(deck_pen, 1))
                g_rect.setZValue(0)
                self.scene.addItem(g_rect)
                
            # load positioning
            y_end = deck_top
            y_start = y_end - 60.0
            
            # magnitude text
            name = self.load_data.get("name", "Load")
            mag = self.load_data.get("magnitude", "")
            
            unit = {"line": "kN/m", "area": "kN/m²"}.get(load_type, "kN")
            mag_txt = f"{name} = {mag} {unit}" if mag else name
            
            font = QFont("Arial", 16, QFont.Bold)
            
            def draw_arrow(x):
                line = QGraphicsLineItem(x, y_start, x, y_end)
                line.setPen(QPen(load_color, 6))
                line.setZValue(1)
                self.scene.addItem(line)
                
                head = QGraphicsPolygonItem(QPolygonF([
                    QPointF(x, y_end),
                    QPointF(x - 10, y_end - 20),
                    QPointF(x + 10, y_end - 20)
                ]))
                head.setBrush(QBrush(load_color))
                head.setPen(QPen(Qt.NoPen))
                head.setZValue(1)
                self.scene.addItem(head)
                
            def add_label(t, cx):
                txt = QGraphicsSimpleTextItem(t)
                txt.setFont(font)
                txt.setBrush(QBrush(Qt.black))
                txt.setZValue(2)
                txt.setPos(cx - txt.boundingRect().width() / 2, y_start - 30)
                self.scene.addItem(txt)
                
            px1 = map_x(x1)
            px2 = map_x(x2)
            
            if load_type == "point":
                draw_arrow(px1)
                add_label(mag_txt, px1)
                
            elif load_type == "line":
                dist = px2 - px1
                if dist < 1:
                    draw_arrow(px1)
                else:
                    num_arrows = max(2, int(dist / 50.0) + 1)
                    for i in range(num_arrows):
                        draw_arrow(px1 + dist * (i / (num_arrows - 1)))
                        
                    horiz = QGraphicsLineItem(px1, y_start, px2, y_start)
                    horiz.setPen(QPen(load_color, 6))
                    horiz.setZValue(1)
                    self.scene.addItem(horiz)
                    
                add_label(mag_txt, (px1 + px2) / 2)
                
            elif load_type == "area":
                w_rect = max(px2 - px1, 2.0)
                area = QGraphicsRectItem(px1, y_start, w_rect, y_end - y_start)
                area.setBrush(QBrush(QColor(220, 0, 0, 50)))
                area.setPen(QPen(load_color, 1, Qt.DashLine))
                area.setZValue(1)
                self.scene.addItem(area)
                
                dist = px2 - px1
                if dist < 1:
                    draw_arrow(px1)
                else:
                    num_arrows = max(2, int(dist / 50.0) + 1)
                    for i in range(num_arrows):
                        draw_arrow(px1 + dist * (i / (num_arrows - 1)))
                
                add_label(mag_txt, px1 + w_rect / 2.0)
                
            rect = self.scene.itemsBoundingRect()
            rect.adjust(-20, -20, 20, 20)
            self.scene.setSceneRect(rect)
            self.fitInView(rect, Qt.KeepAspectRatio)

        finally:
            self._updating = False

    def _draw_grid(self, logical_w, logical_h):
        # Light grid lines to guide proportions
        grid_pen = QPen(QColor(225, 225, 225), 1, Qt.DashLine)
        grid_step = 50.0
        
        # Draw wider than basic frame to ensure coverage
        extend_w = int(logical_w) + 200
        extend_h = int(logical_h) + 200
        
        for y in range(-200, extend_h, int(grid_step)):
            line = self.scene.addLine(-200, y, extend_w, y, grid_pen)
            line.setZValue(-1)
            
        for x in range(-200, extend_w, int(grid_step)):
            line = self.scene.addLine(x, -200, x, extend_h, grid_pen)
            line.setZValue(-1)

    def _zoom_empty(self, logical_w, logical_h):
        rect = QRectF(0, 0, logical_w, logical_h)
        self.scene.setSceneRect(rect)
        self.fitInView(rect, Qt.KeepAspectRatio)
