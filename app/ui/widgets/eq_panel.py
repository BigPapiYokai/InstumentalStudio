from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QGroupBox
from PySide6.QtCore import Qt, Signal

class EQPanel(QWidget):
    eq_changed = Signal(float, float, float)  # low, mid, high in dB
    master_gain_changed = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        group = QGroupBox("Equalizer & Dynamics")
        vbox = QVBoxLayout(group)
        
        # Master gain
        h0 = QHBoxLayout()
        h0.addWidget(QLabel("Master Gain:"))
        self.slider_master = QSlider(Qt.Horizontal)
        self.slider_master.setRange(-24, 24)
        self.slider_master.setValue(0)
        self.slider_master.valueChanged.connect(lambda v: self.master_gain_changed.emit(float(v)))
        self.lbl_master = QLabel("0 dB")
        self.lbl_master.setFixedWidth(45)
        self.slider_master.valueChanged.connect(lambda v: self.lbl_master.setText(f"{v:+d} dB"))
        h0.addWidget(self.slider_master)
        h0.addWidget(self.lbl_master)
        vbox.addLayout(h0)
        
        # 3-band EQ
        for band_name, band_key, default_db in [
            ("Bass", "low", 0),
            ("Mid", "mid", 0),
            ("Treble", "high", 0),
        ]:
            h = QHBoxLayout()
            h.addWidget(QLabel(f"{band_name}:"))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(-12, 12)
            slider.setValue(default_db)
            slider.setFixedHeight(24)
            lbl = QLabel(f"{default_db:+d} dB")
            lbl.setFixedWidth(50)
            slider.valueChanged.connect(lambda v, l=lbl: l.setText(f"{v:+d} dB"))
            setattr(self, f"slider_{band_key}", slider)
            setattr(self, f"lbl_{band_key}", lbl)
            h.addWidget(slider)
            h.addWidget(lbl)
            vbox.addLayout(h)
            
        # Connect all sliders
        self.slider_low.valueChanged.connect(self._emit_eq)
        self.slider_mid.valueChanged.connect(self._emit_eq)
        self.slider_high.valueChanged.connect(self._emit_eq)
        
        layout.addWidget(group)
        
    def _emit_eq(self):
        self.eq_changed.emit(
            float(self.slider_low.value()),
            float(self.slider_mid.value()),
            float(self.slider_high.value())
        )
        
    def set_eq(self, low: float, mid: float, high: float):
        for key, val in [("low", low), ("mid", mid), ("high", high)]:
            slider = getattr(self, f"slider_{key}")
            lbl = getattr(self, f"lbl_{key}")
            slider.blockSignals(True)
            slider.setValue(int(val))
            lbl.setText(f"{int(val):+d} dB")
            slider.blockSignals(False)