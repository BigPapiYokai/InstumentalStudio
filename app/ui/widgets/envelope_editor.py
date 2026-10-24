from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent, QPolygonF

class EnvelopeEditor(QWidget):
    """Interactive gain envelope editor - draw volume curves over time."""
    envelope_changed = Signal(list)  # list of (time_sec, gain)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.points = [(0.0, 1.0), (1.0, 1.0)]  # (normalized_time, gain_0_to_2)
        self.duration = 1.0
        self._dragging_idx = -1
        self._hover_idx = -1
        
    def set_duration(self, duration: float):
        self.duration = max(0.1, duration)
        self.update()
        
    def set_points(self, points: list):
        # points: list of (time_sec, gain)
        self.points = [(t / self.duration if self.duration > 0 else 0, g) for t, g in points]
        # Ensure start and end exist
        if not any(abs(p[0]) < 0.001 for p in self.points):
            self.points.insert(0, (0.0, 1.0))
        if not any(abs(p[0] - 1.0) < 0.001 for p in self.points):
            self.points.append((1.0, 1.0))
        self.update()
        
    def get_points(self) -> list:
        return [(t * self.duration, g) for t, g in self.points]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        draw_rect = (margin, margin, w - 2*margin, h - 2*margin)
        
        # Background
        painter.fillRect(self.rect(), QColor("#1e1e1e"))
        painter.setPen(QPen(QColor("#333"), 1))
        painter.drawRect(*draw_rect)
        
        # Grid lines
        painter.setPen(QPen(QColor("#2a2a2a"), 1))
        for i in range(1, 4):
            y = margin + (h - 2*margin) * i / 4
            painter.drawLine(margin, y, w - margin, y)
        for i in range(1, 10):
            x = margin + (w - 2*margin) * i / 10
            painter.drawLine(x, margin, x, h - margin)
            
        # Draw envelope curve
        if len(self.points) >= 2:
            # Sort by time
            sorted_pts = sorted(self.points, key=lambda p: p[0])
            
            # Create path
            path_points = []
            for t, g in sorted_pts:
                x = margin + t * (w - 2*margin)
                # Gain 0-2 maps to full height, 1.0 = center
                y = margin + (h - 2*margin) * (1.0 - min(2.0, max(0.0, g)) / 2.0)
                path_points.append((x, y))
                
            # Draw filled area under curve
            painter.setBrush(QBrush(QColor(0, 120, 215, 40)))
            painter.setPen(Qt.NoPen)
            
            poly = QPolygonF()
            poly.append(QPointF(path_points[-1][0], h - margin))
            poly.append(QPointF(path_points[0][0], h - margin))
            for x, y in path_points:
                poly.append(QPointF(x, y))
            painter.drawPolygon(poly)
            
            # Draw curve line
            painter.setPen(QPen(QColor("#0078d4"), 2))
            for i in range(len(path_points) - 1):
                painter.drawLine(int(path_points[i][0]), int(path_points[i][1]),
                               int(path_points[i+1][0]), int(path_points[i+1][1]))
                               
            # Draw control points
            for i, (x, y) in enumerate(path_points):
                if i == self._dragging_idx:
                    painter.setBrush(QBrush(QColor("#ff4444")))
                    painter.setPen(QPen(QColor("#ff8888"), 2))
                elif i == self._hover_idx:
                    painter.setBrush(QBrush(QColor("#00aaff")))
                    painter.setPen(QPen(QColor("#0078d4"), 2))
                else:
                    painter.setBrush(QBrush(QColor("#0078d4")))
                    painter.setPen(QPen(QColor("#0078d4"), 2))
                painter.drawEllipse(int(x - 6), int(y - 6), 12, 12)
                
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            x = event.position().x()
            w = self.width()
            margin = 10
            t = (x - margin) / (w - 2*margin) if w > 2*margin else 0
            t = max(0.0, min(1.0, t))
            
            # Check if clicking near existing point
            for i, (pt, _) in enumerate(self.points):
                px = margin + pt * (w - 2*margin)
                if abs(px - x) < 10:
                    self._dragging_idx = i
                    return
                    
            # Add new point
            # Find insert position
            insert_idx = 0
            for i, (pt, _) in enumerate(self.points):
                if pt > t:
                    insert_idx = i
                    break
            else:
                insert_idx = len(self.points)
                
            # Interpolate gain at this time
            gain = self._interpolate_gain(t)
            self.points.insert(insert_idx, (t, gain))
            self._dragging_idx = insert_idx
            self.update()
            self._emit_changed()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        x = event.position().x()
        w = self.width()
        margin = 10
        
        # Update hover
        self._hover_idx = -1
        for i, (pt, _) in enumerate(self.points):
            px = margin + pt * (w - 2*margin)
            if abs(px - x) < 10:
                self._hover_idx = i
                break
                
        if self._dragging_idx >= 0:
            t = (x - margin) / (w - 2*margin) if w > 2*margin else 0
            t = max(0.0, min(1.0, t))
            
            # Keep start/end fixed in time
            if self._dragging_idx == 0:
                t = 0.0
            elif self._dragging_idx == len(self.points) - 1:
                t = 1.0
            else:
                # Ensure ordering
                prev_t = self.points[self._dragging_idx - 1][0]
                next_t = self.points[self._dragging_idx + 1][0] if self._dragging_idx + 1 < len(self.points) else 1.0
                t = max(prev_t + 0.001, min(next_t - 0.001, t))
                
            y = event.position().y()
            h = self.height()
            gain = 2.0 * (1.0 - (y - margin) / (h - 2*margin))
            gain = max(0.0, min(2.0, gain))
            
            self.points[self._dragging_idx] = (t, gain)
            self.update()
            self._emit_changed()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging_idx = -1
        self.update()
        
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        # Delete point on double-click (except first/last)
        if event.button() == Qt.LeftButton:
            if self._hover_idx > 0 and self._hover_idx < len(self.points) - 1:
                self.points.pop(self._hover_idx)
                self._hover_idx = -1
                self.update()
                self._emit_changed()
                
    def _interpolate_gain(self, t: float) -> float:
        sorted_pts = sorted(self.points, key=lambda p: p[0])
        for i in range(len(sorted_pts) - 1):
            t1, g1 = sorted_pts[i]
            t2, g2 = sorted_pts[i + 1]
            if t1 <= t <= t2:
                if t2 == t1:
                    return g1
                alpha = (t - t1) / (t2 - t1)
                return g1 + alpha * (g2 - g1)
        return 1.0
        
    def _emit_changed(self):
        self.envelope_changed.emit(self.get_points())
        
    def leaveEvent(self, event):
        self._hover_idx = -1
        self.update()