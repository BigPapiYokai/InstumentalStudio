import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, QRectF

pg.setConfigOptions(antialias=True)

class WaveformView(QWidget):
    position_changed = Signal(float)  # time in seconds
    selection_changed = Signal(float, float)  # start, end seconds
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setMouseEnabled(x=True, y=False)
        self.plot_widget.getPlotItem().getAxis('left').setStyle(showValues=False)
        self.plot_widget.getPlotItem().getAxis('bottom').setStyle(showValues=True)
        
        layout.addWidget(self.plot_widget)
        
        self.mins = None
        self.maxs = None
        self.sample_rate = 44100
        self.duration = 0.0
        
        # Playhead line
        self.playhead = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#ff4444', width=2))
        self.plot_widget.addItem(self.playhead)
        
        # Selection region
        self.region = pg.LinearRegionItem(values=(0, 0), movable=True, 
                                           brush=pg.mkBrush(0, 120, 215, 50),
                                           pen=pg.mkPen('#0078d4', width=1))
        self.region.setZValue(10)
        self.region.sigRegionChanged.connect(self._on_region_changed)
        self.plot_widget.addItem(self.region)
        self.region.setVisible(False)
        
        self._dragging_playhead = False
        
        self.plot_widget.scene().sigMouseClicked.connect(self._on_click)
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)
        
    def set_audio_data(self, mins: np.ndarray, maxs: np.ndarray, sample_rate: int):
        self.mins = mins
        self.maxs = maxs
        self.sample_rate = sample_rate
        self.duration = len(mins) / (len(mins) / self.duration) if self.duration > 0 else len(mins) * 512 / sample_rate
        # Actually compute duration from data size
        total_samples = len(mins) * 512  # approximate, we'll recalc properly
        self.duration = total_samples / sample_rate if sample_rate > 0 else 0
        
        self._update_plot()
        
    def _update_plot(self):
        self.plot_widget.clear()
        self.plot_widget.addItem(self.playhead)
        self.plot_widget.addItem(self.region)
        
        if self.mins is None:
            return
            
        # Plot filled waveform
        n = len(self.mins)
        x = np.linspace(0, self.duration, n)
        
        # Create fill between min and max
        fill = pg.FillBetweenItem(
            pg.PlotCurveItem(x, self.mins, pen=None),
            pg.PlotCurveItem(x, self.maxs, pen=None),
            brush=pg.mkBrush(0, 120, 215, 80)
        )
        self.plot_widget.addItem(fill)
        
        # Center line
        self.plot_widget.plot(x, np.zeros_like(x), pen=pg.mkPen('#444', width=1))
        
        self.plot_widget.setXRange(0, self.duration, padding=0)
        self.plot_widget.setYRange(-1.1, 1.1, padding=0)
        
    def set_position(self, sample_pos: int):
        if self.duration > 0:
            t = sample_pos / self.sample_rate
            self.playhead.setValue(t)
            
    def _on_click(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.plot_widget.getPlotItem().vb.mapSceneToView(event.scenePos())
            t = pos.x()
            t = max(0, min(t, self.duration))
            self.position_changed.emit(t)
            
    def _on_mouse_move(self, event):
        if self._dragging_playhead:
            pos = self.plot_widget.getPlotItem().vb.mapSceneToView(event)
            t = max(0, min(pos.x(), self.duration))
            self.position_changed.emit(t)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.plot_widget.getPlotItem().vb.mapSceneToView(event.position())
            if abs(pos.x() - self.playhead.value()) < 0.05 * self.duration:
                self._dragging_playhead = True
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self._dragging_playhead = False
        super().mouseReleaseEvent(event)
        
    def _on_region_changed(self):
        start, end = self.region.getRegion()
        self.selection_changed.emit(start, end)
        
    def set_selection(self, start: float, end: float):
        self.region.setRegion([start, end])
        self.region.setVisible(True)
        
    def clear_selection(self):
        self.region.setVisible(False)