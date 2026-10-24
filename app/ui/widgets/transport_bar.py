from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSlider, QLabel, QStyle
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

class TransportBar(QWidget):
    play_clicked = Signal()
    pause_clicked = Signal()
    stop_clicked = Signal()
    seek_changed = Signal(float)  # 0.0-1.0
    volume_changed = Signal(float)
    loop_toggled = Signal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Rewind / Previous
        self.btn_prev = QPushButton("⏮")
        self.btn_prev.setFixedSize(36, 36)
        layout.addWidget(self.btn_prev)
        
        # Play
        self.btn_play = QPushButton("▶")
        self.btn_play.setFixedSize(44, 44)
        self.btn_play.setStyleSheet("font-size: 18pt; background-color: #0078d4;")
        self.btn_play.clicked.connect(self._on_play)
        layout.addWidget(self.btn_play)
        
        # Pause
        self.btn_pause = QPushButton("⏸")
        self.btn_pause.setFixedSize(36, 36)
        self.btn_pause.clicked.connect(self._on_pause)
        layout.addWidget(self.btn_pause)
        
        # Stop
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setFixedSize(36, 36)
        self.btn_stop.clicked.connect(self._on_stop)
        layout.addWidget(self.btn_stop)
        
        # Forward / Next
        self.btn_next = QPushButton("⏭")
        self.btn_next.setFixedSize(36, 36)
        layout.addWidget(self.btn_next)
        
        # Time display
        self.lbl_time = QLabel("0:00 / 0:00")
        self.lbl_time.setMinimumWidth(100)
        layout.addWidget(self.lbl_time)
        
        # Position slider
        self.slider_pos = QSlider(Qt.Horizontal)
        self.slider_pos.setRange(0, 10000)
        self.slider_pos.setTracking(False)
        self.slider_pos.sliderReleased.connect(self._on_seek)
        layout.addWidget(self.slider_pos, 1)
        
        # Loop
        self.btn_loop = QPushButton("🔁")
        self.btn_loop.setFixedSize(36, 36)
        self.btn_loop.setCheckable(True)
        self.btn_loop.toggled.connect(self.loop_toggled.emit)
        layout.addWidget(self.btn_loop)
        
        # Volume
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.slider_vol.setFixedWidth(100)
        self.slider_vol.valueChanged.connect(lambda v: self.volume_changed.emit(v / 100.0))
        layout.addWidget(self.slider_vol)
        
        self._is_playing = False
        
    def _on_play(self):
        if not self._is_playing:
            self._is_playing = True
            self.btn_play.setText("▶")  # keep as play, we use pause for pause
            self.play_clicked.emit()
            
    def _on_pause(self):
        if self._is_playing:
            self._is_playing = False
            self.btn_play.setText("▶")
            self.pause_clicked.emit()
            
    def _on_stop(self):
        self._is_playing = False
        self.btn_play.setText("▶")
        self.stop_clicked.emit()
        self.slider_pos.setValue(0)
        
    def _on_seek(self):
        self.seek_changed.emit(self.slider_pos.value() / 10000.0)
        
    def set_playing(self, playing: bool):
        self._is_playing = playing
        self.btn_play.setText("⏸" if playing else "▶")
        
    def set_position(self, pos_ratio: float):
        self.slider_pos.blockSignals(True)
        self.slider_pos.setValue(int(pos_ratio * 10000))
        self.slider_pos.blockSignals(False)
        
    def set_time_display(self, current: float, total: float):
        def fmt(t):
            m = int(t // 60)
            s = int(t % 60)
            return f"{m}:{s:02d}"
        self.lbl_time.setText(f"{fmt(current)} / {fmt(total)}")