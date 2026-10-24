from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox, QGroupBox, QFileDialog
from PySide6.QtCore import Qt

class ExportDialog(QDialog):
    def __init__(self, parent=None, duration: float = 0):
        super().__init__(parent)
        self.setWindowTitle("Export Audio")
        self.setModal(True)
        self.resize(400, 350)
        
        layout = QVBoxLayout(self)
        
        # Format
        fmt_group = QGroupBox("Format")
        fmt_layout = QVBoxLayout(fmt_group)
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Format:"))
        self.cmb_format = QComboBox()
        self.cmb_format.addItems(["WAV", "FLAC", "MP3", "OGG"])
        h1.addWidget(self.cmb_format)
        fmt_layout.addLayout(h1)
        
        # WAV/FLAC options
        self.chk_float = QCheckBox("32-bit float (WAV only)")
        fmt_layout.addWidget(self.chk_float)
        
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Sample Rate:"))
        self.cmb_sr = QComboBox()
        self.cmb_sr.addItems(["44100", "48000", "96000"])
        self.cmb_sr.setCurrentText("44100")
        h2.addWidget(self.cmb_sr)
        fmt_layout.addLayout(h2)
        
        # MP3 options
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("MP3 Bitrate:"))
        self.cmb_bitrate = QComboBox()
        self.cmb_bitrate.addItems(["128", "192", "256", "320"])
        self.cmb_bitrate.setCurrentText("320")
        h3.addWidget(self.cmb_bitrate)
        fmt_layout.addLayout(h3)
        
        layout.addWidget(fmt_group)
        
        # Range
        range_group = QGroupBox("Range")
        range_layout = QVBoxLayout(range_group)
        
        self.chk_full = QCheckBox("Export full track")
        self.chk_full.setChecked(True)
        self.chk_full.toggled.connect(self._toggle_range)
        range_layout.addWidget(self.chk_full)
        
        h4 = QHBoxLayout()
        h4.addWidget(QLabel("Start:"))
        self.spin_start = QDoubleSpinBox()
        self.spin_start.setRange(0, max(1, duration))
        self.spin_start.setSuffix(" s")
        self.spin_start.setEnabled(False)
        h4.addWidget(self.spin_start)
        h4.addWidget(QLabel("End:"))
        self.spin_end = QDoubleSpinBox()
        self.spin_end.setRange(0, max(1, duration))
        self.spin_end.setValue(duration)
        self.spin_end.setSuffix(" s")
        self.spin_end.setEnabled(False)
        h4.addWidget(self.spin_end)
        range_layout.addLayout(h4)
        
        layout.addWidget(range_group)
        
        # Output
        h5 = QHBoxLayout()
        h5.addWidget(QLabel("Output:"))
        self.lbl_path = QLabel("...")
        self.lbl_path.setStyleSheet("color: #888;")
        h5.addWidget(self.lbl_path, 1)
        btn_browse = QPushButton("Browse")
        btn_browse.clicked.connect(self._browse)
        h5.addWidget(btn_browse)
        layout.addLayout(h5)
        
        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Export")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)
        
        self._output_path = ""
        
    def _toggle_range(self, checked: bool):
        self.spin_start.setEnabled(not checked)
        self.spin_end.setEnabled(not checked)
        
    def _browse(self):
        fmt = self.cmb_format.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(self, "Save Audio", "", f"{fmt.upper()} (*.{fmt})")
        if path:
            self._output_path = path
            self.lbl_path.setText(path)
            self.lbl_path.setStyleSheet("color: #e0e0e0;")
            
    def get_settings(self) -> dict:
        return {
            "format": self.cmb_format.currentText().lower(),
            "sample_rate": int(self.cmb_sr.currentText()),
            "bitrate": self.cmb_bitrate.currentText() + "k",
            "float32": self.chk_float.isChecked(),
            "full_track": self.chk_full.isChecked(),
            "start_time": self.spin_start.value() if not self.chk_full.isChecked() else 0,
            "end_time": self.spin_end.value() if not self.chk_full.isChecked() else 0,
            "output_path": self._output_path
        }