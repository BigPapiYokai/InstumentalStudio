from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QGroupBox
from PySide6.QtCore import Qt, Signal

class StemMixer(QWidget):
    stem_gain_changed = Signal(str, float)  # stem_name, gain (0.0-1.0)
    stem_mute_changed = Signal(str, bool)
    stem_solo_changed = Signal(str, bool)
    vocal_removal_changed = Signal(float)  # 0.0 = original, 1.0 = full instrumental
    
    STEM_COLORS = {
        'vocals': '#ff6b6b',
        'drums': '#4ecdc4',
        'bass': '#ffe66d',
        'other': '#a8e6cf',
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Vocal removal strength slider
        vr_layout = QHBoxLayout()
        vr_layout.addWidget(QLabel("Vocal Removal:"))
        self.slider_vocal = QSlider(Qt.Horizontal)
        self.slider_vocal.setRange(0, 100)
        self.slider_vocal.setValue(100)
        self.slider_vocal.valueChanged.connect(lambda v: self.vocal_removal_changed.emit(v / 100.0))
        vr_layout.addWidget(self.slider_vocal)
        self.lbl_vocal = QLabel("100%")
        self.lbl_vocal.setFixedWidth(40)
        self.slider_vocal.valueChanged.connect(lambda v: self.lbl_vocal.setText(f"{v}%"))
        vr_layout.addWidget(self.lbl_vocal)
        layout.addLayout(vr_layout)
        
        # Stem faders container
        self.faders_container = QWidget()
        self.faders_layout = QHBoxLayout(self.faders_container)
        self.faders_layout.setSpacing(16)
        layout.addWidget(self.faders_container)
        
        self.stem_faders = {}
        
    def set_stems(self, stem_names: list):
        # Clear existing
        for widget in self.stem_faders.values():
            widget.setParent(None)
        self.stem_faders.clear()
        
        for name in stem_names:
            fader = self._create_fader(name)
            self.stem_faders[name] = fader
            self.faders_layout.addWidget(fader)
            
    def _create_fader(self, name: str) -> QWidget:
        color = self.STEM_COLORS.get(name, '#888888')
        
        box = QGroupBox(name.capitalize())
        box.setStyleSheet(f"QGroupBox {{ border: 1px solid {color}; color: {color}; }}")
        vbox = QVBoxLayout(box)
        
        # Gain slider (vertical)
        slider = QSlider(Qt.Vertical)
        slider.setRange(0, 200)  # 0-200% (0.0-2.0)
        slider.setValue(100)
        slider.setInvertedAppearance(True)
        slider.setFixedWidth(40)
        slider.valueChanged.connect(lambda v, n=name: self.stem_gain_changed.emit(n, v / 100.0))
        
        # Value label
        lbl_val = QLabel("100%")
        lbl_val.setAlignment(Qt.AlignCenter)
        slider.valueChanged.connect(lambda v, l=lbl_val: l.setText(f"{v}%"))
        
        # Mute / Solo
        hbox = QHBoxLayout()
        btn_mute = QPushButton("M")
        btn_mute.setCheckable(True)
        btn_mute.setFixedSize(30, 30)
        btn_mute.toggled.connect(lambda checked, n=name: self.stem_mute_changed.emit(n, checked))
        btn_mute.setStyleSheet("QPushButton:checked { background-color: #ff4444; }")
        
        btn_solo = QPushButton("S")
        btn_solo.setCheckable(True)
        btn_solo.setFixedSize(30, 30)
        btn_solo.toggled.connect(lambda checked, n=name: self.stem_solo_changed.emit(n, checked))
        btn_solo.setStyleSheet("QPushButton:checked { background-color: #ffaa00; }")
        
        hbox.addWidget(btn_mute)
        hbox.addWidget(btn_solo)
        hbox.addStretch()
        
        vbox.addWidget(slider, 1)
        vbox.addWidget(lbl_val)
        vbox.addLayout(hbox)
        
        return box
    
    def set_stem_gain(self, name: str, gain: float):
        if name in self.stem_faders:
            # Find the slider in the group box
            for child in self.stem_faders[name].findChildren(QSlider):
                if child.orientation() == Qt.Vertical:
                    child.blockSignals(True)
                    child.setValue(int(gain * 100))
                    child.blockSignals(False)
                    break