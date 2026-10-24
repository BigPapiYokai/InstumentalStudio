import os
import numpy as np
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QSplitter, QFileDialog, QMessageBox, QProgressBar,
                               QMenuBar, QStatusBar, QLabel, QPushButton, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSettings
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from app.core.audio.loader import load_audio
from app.core.audio.exporter import save_audio
from app.core.audio.peaks import compute_peaks
from app.core.dsp.tempo import time_stretch
from app.core.dsp.equalizer import apply_eq
from app.core.dsp.dynamics import normalize, apply_gain
from app.core.dsp.envelope import apply_envelope
from app.core.dsp.fades import apply_fades
from app.core.analysis.tempo_detect import detect_bpm
from app.core.separation.demucs_backend import DemucsBackend
from app.core.playback.engine import PlaybackEngine
from app.core.project.session import ProjectSession

from app.ui.theme import apply_dark_theme
from app.ui.widgets.waveform_view import WaveformView
from app.ui.widgets.transport_bar import TransportBar
from app.ui.widgets.stem_mixer import StemMixer
from app.ui.widgets.tempo_panel import TempoPanel
from app.ui.widgets.eq_panel import EQPanel
from app.ui.widgets.envelope_editor import EnvelopeEditor
from app.ui.widgets.export_dialog import ExportDialog


class SeparationWorker(QThread):
    progress = Signal(dict)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, backend, audio, sr):
        super().__init__()
        self.backend = backend
        self.audio = audio
        self.sr = sr
        
    def run(self):
        try:
            def cb(info):
                self.progress.emit(info)
            stems = self.backend.separate(self.audio, self.sr, callback=cb)
            self.finished.emit(stems)
        except Exception as e:
            self.error.emit(str(e))


class ExportWorker(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, output_path, audio_data, sample_rate, settings):
        super().__init__()
        self.output_path = output_path
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.settings = settings
        
    def run(self):
        try:
            # Apply all processing
            data = self.audio_data.copy()
            
            # Tempo stretch
            stretch = self.settings.get('stretch_ratio', 1.0)
            if stretch != 1.0:
                data = time_stretch(data, stretch)
                self.progress.emit(20)
            
            # EQ
            eq = self.settings.get('eq', (0,0,0))
            if any(eq):
                data = apply_eq(data, self.sample_rate, eq[0], eq[1], eq[2])
                self.progress.emit(40)
            
            # Master gain
            mg = self.settings.get('master_gain', 0)
            if mg != 0:
                data = apply_gain(data, mg)
                
            # Envelope
            env = self.settings.get('envelope', [])
            if env:
                data = apply_envelope(data, self.sample_rate, env)
                self.progress.emit(60)
                
            # Fades
            fi = self.settings.get('fade_in', 0)
            fo = self.settings.get('fade_out', 0)
            if fi > 0 or fo > 0:
                data = apply_fades(data, self.sample_rate, fi, fo)
                self.progress.emit(80)
            
            # Export
            fmt = self.settings.get('format', 'wav')
            if fmt == 'wav':
                subtype = 'FLOAT' if self.settings.get('float32') else 'PCM_16'
                save_audio(self.output_path, data, self.sample_rate, subtype)
            elif fmt == 'flac':
                save_audio(self.output_path, data, self.sample_rate, 'PCM_16')
            else:
                # mp3/ogg - use soundfile with appropriate subtype or pydub
                save_audio(self.output_path, data, self.sample_rate, 'PCM_16')
                
            self.progress.emit(100)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SonicLoom Studio")
        self.resize(1400, 900)
        
        # State
        self.audio_data = None
        self.sample_rate = 44100
        self.duration = 0
        self.stems = {}
        self.current_stem = None
        self.detected_bpm = 120.0
        self.stretch_ratio = 1.0
        
        # Playback engine
        self.player = PlaybackEngine(self.sample_rate)
        self.player.on_position_changed = self._on_playback_position
        
        # Separation backend
        self.separator = DemucsBackend()
        self.sep_worker = None
        self.export_worker = None
        
        self._setup_ui()
        self._setup_shortcuts()
        self._apply_theme()
        
    def _setup_ui(self):
        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        
        act_open = QAction("&Open Audio...", self)
        act_open.setShortcut(QKeySequence.Open)
        act_open.triggered.connect(self._open_file)
        file_menu.addAction(act_open)
        
        act_save = QAction("&Save Project...", self)
        act_save.setShortcut(QKeySequence.Save)
        act_save.triggered.connect(self._save_project)
        file_menu.addAction(act_save)
        
        act_load = QAction("&Load Project...", self)
        act_load.setShortcut(QKeySequence.Open)
        act_load.triggered.connect(self._load_project)
        file_menu.addAction(act_load)
        
        file_menu.addSeparator()
        
        act_export = QAction("&Export Audio...", self)
        act_export.setShortcut(QKeySequence("Ctrl+E"))
        act_export.triggered.connect(self._export_audio)
        file_menu.addAction(act_export)
        
        file_menu.addSeparator()
        
        act_quit = QAction("&Quit", self)
        act_quit.setShortcut(QKeySequence.Quit)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)
        
        # Central widget with splitter
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - waveform and transport
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(8, 8, 4, 8)
        left_layout.setSpacing(8)
        
        # Drop zone label
        self.drop_label = QLabel("Drag & Drop Audio File Here\nor use File → Open")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #444;
                border-radius: 8px;
                padding: 40px;
                color: #888;
                font-size: 14pt;
            }
        """)
        self.drop_label.setAcceptDrops(True)
        left_layout.addWidget(self.drop_label, 1)
        
        # Waveform view
        self.waveform = WaveformView()
        self.waveform.position_changed.connect(self._on_waveform_seek)
        self.waveform.selection_changed.connect(self._on_selection_changed)
        left_layout.addWidget(self.waveform, 4)
        
        # Transport bar
        self.transport = TransportBar()
        self.transport.play_clicked.connect(self._play)
        self.transport.pause_clicked.connect(self._pause)
        self.transport.stop_clicked.connect(self._stop)
        self.transport.seek_changed.connect(self._on_transport_seek)
        self.transport.volume_changed.connect(self._on_volume_changed)
        self.transport.loop_toggled.connect(self._on_loop_toggled)
        left_layout.addWidget(self.transport)
        
        # Progress bar for separation/export
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # Right panel - controls
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 8, 8, 8)
        right_layout.setSpacing(8)
        
        # Stem Mixer
        self.stem_mixer = StemMixer()
        self.stem_mixer.stem_gain_changed.connect(self._on_stem_gain_changed)
        self.stem_mixer.stem_mute_changed.connect(self._on_stem_mute_changed)
        self.stem_mixer.stem_solo_changed.connect(self._on_stem_solo_changed)
        self.stem_mixer.vocal_removal_changed.connect(self._on_vocal_removal_changed)
        right_layout.addWidget(self.stem_mixer, 3)
        
        # Tempo Panel
        self.tempo_panel = TempoPanel()
        self.tempo_panel.bpm_changed.connect(self._on_target_bpm_changed)
        self.tempo_panel.stretch_changed.connect(self._on_stretch_changed)
        right_layout.addWidget(self.tempo_panel, 1)
        
        # EQ Panel
        self.eq_panel = EQPanel()
        self.eq_panel.eq_changed.connect(self._on_eq_changed)
        self.eq_panel.master_gain_changed.connect(self._on_master_gain_changed)
        right_layout.addWidget(self.eq_panel, 1)
        
        # Envelope Editor
        self.envelope_editor = EnvelopeEditor()
        self.envelope_editor.envelope_changed.connect(self._on_envelope_changed)
        right_layout.addWidget(self.envelope_editor, 1)
        
        # Export button
        btn_export = QPushButton("Export Current Mix")
        btn_export.setFixedHeight(40)
        btn_export.setStyleSheet("font-size: 12pt; background-color: #0078d4; font-weight: bold;")
        btn_export.clicked.connect(self._export_audio)
        right_layout.addWidget(btn_export)
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([900, 500])
        
        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")
        
        # Enable drag & drop
        self.setAcceptDrops(True)
        
    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space), self, self._toggle_play_pause)
        QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self._seek_relative(-5))
        QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self._seek_relative(5))
        
    def _apply_theme(self):
        apply_dark_theme(QApplication.instance())
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet(self.drop_label.styleSheet().replace("#444", "#0078d4"))
            
    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #444;
                border-radius: 8px;
                padding: 40px;
                color: #888;
                font-size: 14pt;
            }
        """)
        
    def dropEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #444;
                border-radius: 8px;
                padding: 40px;
                color: #888;
                font-size: 14pt;
            }
        """)
        urls = event.mimeData().urls()
        if urls:
            self._load_audio_file(urls[0].toLocalFile())
            
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.aiff *.wma *.opus)"
        )
        if path:
            self._load_audio_file(path)
            
    def _load_audio_file(self, path: str):
        self.status.showMessage(f"Loading {os.path.basename(path)}...")
        QApplication.processEvents()
        
        try:
            data, sr = load_audio(path)
            self.audio_data = data
            self.sample_rate = sr
            self.duration = len(data) / sr
            
            # Compute peaks for waveform
            mins, maxs = compute_peaks(data)
            self.waveform.set_audio_data(mins, maxs, sr)
            
            # Set player audio
            self.player.set_audio(data, sr)
            
            # Detect BPM
            self.detected_bpm = detect_bpm(data, sr)
            self.tempo_panel.set_detected_bpm(self.detected_bpm)
            
            # Reset stems
            self.stems = {}
            self.stem_mixer.set_stems([])
            self.envelope_editor.set_duration(self.duration)
            self.envelope_editor.set_points([(0.0, 1.0), (self.duration, 1.0)])
            
            # Update UI
            self.drop_label.hide()
            self.waveform.show()
            self.transport.set_time_display(0, self.duration)
            self.status.showMessage(f"Loaded: {os.path.basename(path)} | {sr}Hz | {self.duration:.1f}s | BPM: {self.detected_bpm:.1f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audio:\n{e}")
            self.status.showMessage("Error loading file")
            
    def _play(self):
        self.player.play()
        self.transport.set_playing(True)
        self.status.showMessage("Playing...")
        
    def _pause(self):
        self.player.pause()
        self.transport.set_playing(False)
        self.status.showMessage("Paused")
        
    def _stop(self):
        self.player.stop()
        self.transport.set_playing(False)
        self.transport.set_position(0)
        self.waveform.set_position(0)
        self.status.showMessage("Stopped")
        
    def _toggle_play_pause(self):
        if self.player.is_playing:
            self._pause()
        else:
            self._play()
            
    def _seek_relative(self, seconds: float):
        new_pos = self.player.position + int(seconds * self.sample_rate)
        self.player.seek(new_pos)
        self.transport.set_position(self.player.position / max(1, len(self.player.audio_data or [1])))
        self.waveform.set_position(self.player.position)
        
    def _on_waveform_seek(self, time_sec: float):
        sample_pos = int(time_sec * self.sample_rate)
        self.player.seek(sample_pos)
        self.transport.set_position(sample_pos / max(1, len(self.player.audio_data or [1])))
        
    def _on_transport_seek(self, ratio: float):
        if self.player.audio_data is not None:
            sample_pos = int(ratio * len(self.player.audio_data))
            self.player.seek(sample_pos)
            self.waveform.set_position(sample_pos)
            
    def _on_playback_position(self, sample_pos: int):
        if self.player.audio_data is not None:
            ratio = sample_pos / len(self.player.audio_data)
            self.transport.set_position(ratio)
            self.waveform.set_position(sample_pos)
            self.transport.set_time_display(sample_pos / self.sample_rate, self.duration)
            
    def _on_volume_changed(self, vol: float):
        self.player.set_volume(vol)
        
    def _on_loop_toggled(self, enabled: bool):
        self.player.loop = enabled
        
    def _on_selection_changed(self, start: float, end: float):
        self.player.loop_start = int(start * self.sample_rate)
        self.player.loop_end = int(end * self.sample_rate)
        
    # Separation
    def _on_vocal_removal_changed(self, strength: float):
        # Blend between original and instrumental
        pass
        
    def _on_stem_gain_changed(self, stem: str, gain: float):
        # Apply stem gain to playback mix
        pass
        
    def _on_stem_mute_changed(self, stem: str, muted: bool):
        pass
        
    def _on_stem_solo_changed(self, stem: str, solo: bool):
        pass
        
    # Tempo
    def _on_target_bpm_changed(self, bpm: float):
        if self.detected_bpm > 0:
            self.stretch_ratio = bpm / self.detected_bpm
            self.tempo_panel.set_stretch_ratio(self.stretch_ratio)
            
    def _on_stretch_changed(self, ratio: float):
        self.stretch_ratio = ratio
        
    # EQ
    def _on_eq_changed(self, low: float, mid: float, high: float):
        pass
        
    def _on_master_gain_changed(self, gain: float):
        pass
        
    def _on_envelope_changed(self, points: list):
        pass
        
    # Separation action
    def _separate_vocals(self):
        if self.audio_data is None:
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.sep_worker = SeparationWorker(self.separator, self.audio_data, self.sample_rate)
        self.sep_worker.progress.connect(self._on_sep_progress)
        self.sep_worker.finished.connect(self._on_sep_finished)
        self.sep_worker.error.connect(self._on_sep_error)
        self.sep_worker.start()
        
    def _on_sep_progress(self, info: dict):
        if 'segment_offset' in info and 'audio_length' in info:
            pct = int(100 * info['segment_offset'] / max(1, info['audio_length']))
            self.progress_bar.setValue(pct)
            
    def _on_sep_finished(self, stems: dict):
        self.stems = stems
        stem_names = list(stems.keys())
        self.stem_mixer.set_stems(stem_names)
        
        # Default: full vocal removal (instrumental)
        self.stem_mixer.slider_vocal.setValue(100)
        
        self.progress_bar.setVisible(False)
        self.status.showMessage(f"Separation complete: {', '.join(stem_names)}")
        
    def _on_sep_error(self, err: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Separation Error", err)
        self.status.showMessage("Separation failed")
        
    # Export
    def _export_audio(self):
        if self.audio_data is None:
            return
            
        dialog = ExportDialog(self, self.duration)
        if dialog.exec() == QDialog.Accepted:
            settings = dialog.get_settings()
            if not settings['output_path']:
                return
                
            # Prepare final mix settings
            export_settings = {
                'format': settings['format'],
                'sample_rate': settings['sample_rate'],
                'stretch_ratio': self.stretch_ratio,
                'eq': (self.eq_panel.slider_low.value(), self.eq_panel.slider_mid.value(), self.eq_panel.slider_high.value()),
                'master_gain': self.eq_panel.slider_master.value(),
                'envelope': self.envelope_editor.get_points(),
                'fade_in': 0,  # TODO: add fade controls
                'fade_out': 0,
                'float32': settings['float32']
            }
            
            # Get current playback mix (original or stems)
            # For now export the main audio with processing
            output_audio = self._render_current_mix()
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.export_worker = ExportWorker(settings['output_path'], output_audio, self.sample_rate, export_settings)
            self.export_worker.progress.connect(self.progress_bar.setValue)
            self.export_worker.finished.connect(self._on_export_finished)
            self.export_worker.error.connect(self._on_export_error)
            self.export_worker.start()
            
    def _render_current_mix(self) -> np.ndarray:
        """Render the current mix with all processing applied."""
        # Use stems if available, otherwise original
        if self.stems and self.stem_mixer.slider_vocal.value() > 0:
            # Mix stems with gains
            # For simplicity, mix all stems with their gains
            mix = None
            for name, data in self.stems.items():
                gain = 1.0
                if name == 'vocals':
                    gain = 1.0 - self.stem_mixer.slider_vocal.value() / 100.0
                # TODO: get individual stem gains from stem_mixer
                if mix is None:
                    mix = data * gain
                else:
                    # Align lengths
                    min_len = min(len(mix), len(data))
                    mix = mix[:min_len] + data[:min_len] * gain
            if mix is not None:
                return mix
        return self.audio_data
        
    def _on_export_finished(self, path: str):
        self.progress_bar.setVisible(False)
        self.status.showMessage(f"Exported: {os.path.basename(path)}")
        QMessageBox.information(self, "Export Complete", f"Audio exported to:\n{path}")
        
    def _on_export_error(self, err: str):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Export Error", err)
        
    def _save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "SonicLoom Project (*.slproj)")
        if path:
            session = ProjectSession(path)
            session.sample_rate = self.sample_rate
            session.audio_data = self.audio_data
            session.stems = self.stems
            session.bpm = self.detected_bpm
            session.target_bpm = self.detected_bpm * self.stretch_ratio
            session.eq_settings = {
                "low": self.eq_panel.slider_low.value(),
                "mid": self.eq_panel.slider_mid.value(),
                "high": self.eq_panel.slider_high.value()
            }
            session.envelope_points = self.envelope_editor.get_points()
            session.master_gain = self.eq_panel.slider_master.value()
            session.current_stem_mix = {}  # TODO
            session.save()
            self.status.showMessage(f"Project saved: {os.path.basename(path)}")
            
    def _load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "SonicLoom Project (*.slproj)")
        if path:
            try:
                session = ProjectSession.load(path)
                self.audio_data = session.audio_data
                self.sample_rate = session.sample_rate
                self.stems = session.stems
                self.duration = len(self.audio_data) / self.sample_rate if self.audio_data is not None else 0
                
                if self.audio_data is not None:
                    mins, maxs = compute_peaks(self.audio_data)
                    self.waveform.set_audio_data(mins, maxs, self.sample_rate)
                    self.player.set_audio(self.audio_data, self.sample_rate)
                    
                self.detected_bpm = session.bpm
                self.tempo_panel.set_detected_bpm(self.detected_bpm)
                self.stretch_ratio = session.target_bpm / self.detected_bpm if self.detected_bpm > 0 else 1.0
                self.tempo_panel.set_stretch_ratio(self.stretch_ratio)
                
                self.eq_panel.set_eq(
                    session.eq_settings.get("low", 0),
                    session.eq_settings.get("mid", 0),
                    session.eq_settings.get("high", 0)
                )
                self.eq_panel.slider_master.setValue(int(session.master_gain))
                
                self.envelope_editor.set_duration(self.duration)
                self.envelope_editor.set_points(session.envelope_points)
                
                if self.stems:
                    self.stem_mixer.set_stems(list(self.stems.keys()))
                    
                self.drop_label.hide()
                self.waveform.show()
                self.status.showMessage(f"Project loaded: {os.path.basename(path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")

    def closeEvent(self, event):
        self.player.stop()
        event.accept()