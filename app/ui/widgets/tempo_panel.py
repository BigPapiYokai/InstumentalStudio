from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QGroupBox, QDoubleSpinBox
from PySide6.QtCore import Qt, Signal

class TempoPanel(QWidget):
    bpm_changed = Signal(float)  # target BPM
    stretch_changed = Signal(float)  # stretch ratio
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        group = QGroupBox("Tempo & BPM")
        vbox = QVBoxLayout(group)
        
        # Detected BPM display
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Detected BPM:"))
        self.lbl_detected = QLabel("120.0")
        self.lbl_detected.setStyleSheet("font-weight: bold; color: #4ecdc4;")
        h1.addWidget(self.lbl_detected)
        h1.addStretch()
        vbox.addLayout(h1)
        
        # Target BPM slider
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Target BPM:"))
        self.spin_bpm = QDoubleSpinBox()
        self.spin_bpm.setRange(20.0, 300.0)
        self.spin_bpm.setDecimals(1)
        self.spin_bpm.setSingleStep(1.0)
        self.spin_bpm.setValue(120.0)
        self.spin_bpm.valueChanged.connect(self._on_bpm_changed)
        h2.addWidget(self.spin_bpm)
        
        self.lbl_ratio = QLabel("1.00x")
        self.lbl_ratio.setFixedWidth(50)
        self.lbl_ratio.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        h2.addWidget(self.lbl_ratio)
        vbox.addLayout(h2)
        
        # Slider for ratio
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Stretch:"))
        self.slider_stretch = QSlider(Qt.Horizontal)
        self.slider_stretch.setRange(25, 400)  # 0.25x - 4.0x
        self.slider_stretch.setValue(100)
        self.slider_stretch.valueChanged.connect(self._on_stretch_changed)
        h3.addWidget(self.slider_stretch)
        vbox.addLayout(h3)
        
        # Quick ratio buttons
        h4 = QHBoxLayout()
        for ratio, label in [(0.5, "½"), (0.75, "¾"), (1.0, "1×"), (1.5, "1.5×"), (2.0, "2×")]:
            btn = QPushButton(label)
            btn.setFixedSize(40, 30)
            btn.clicked.connect(lambda _, r=ratio: self.set_stretch_ratio(r))
            h4.addWidget(btn)
        h4.addStretch()
        vbox.addLayout(h4)
        
        layout.addWidget(group)
        
    def _on_bpm_changed(self, val):
        self.bpm_changed.emit(val)
        if self.detected_bpm > 0:
            ratio = val / self.detected_bpm
            self.slider_stretch.blockSignals(True)
            self.slider_stretch.setValue(int(ratio * 100))
            self.slider_stretch.blockSignals(False)
            self._update_ratio_label(ratio)
            
    def _on_stretch_changed(self, val):
        ratio = val / 100.0
        self._update_ratio_label(ratio)
        self.stretch_changed.emit(ratio)
        
    def _update_ratio_label(self, ratio):
        self.lbl_ratio.setText(f"{ratio:.2f}x")
        
    def set_detected_bpm(self, bpm: float):
        self.detected_bpm = bpm
        self.lbl_detected.setText(f"{bpm:.1f}")
        if self.spin_bpm.value() == 120.0:  # not user-modified yet
            self.spin_bpm.setValue(bpm)
            
    def set_stretch_ratio(self, ratio: float):
        self.slider_stretch.blockSignals(True)
        self.slider_stretch.setValue(int(ratio * 100))
        self.slider_stretch.blockSignals(False)
        self._update_ratio_label(ratio)
        self.stretch_changed.emit(ratio)