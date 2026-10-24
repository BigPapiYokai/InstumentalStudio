import json
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
import soundfile as sf

class ProjectSession:
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.sample_rate = 44100
        self.audio_data: Optional[np.ndarray] = None  # original mix
        self.stems: Dict[str, np.ndarray] = {}  # stem_name -> audio
        self.current_stem_mix: Dict[str, float] = {}  # stem -> gain (0.0-1.0 for vocals, etc.)
        self.bpm = 120.0
        self.target_bpm = 120.0
        self.eq_settings = {"low": 0.0, "mid": 0.0, "high": 0.0}
        self.envelope_points: List[tuple] = []  # (time, gain)
        self.fade_in = 0.0
        self.fade_out = 0.0
        self.master_gain = 0.0

    def save(self, path: Optional[str] = None):
        if path is None:
            path = self.project_path
        if path is None:
            raise ValueError("No project path specified")
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save metadata JSON
        meta = {
            "sample_rate": self.sample_rate,
            "bpm": self.bpm,
            "target_bpm": self.target_bpm,
            "eq_settings": self.eq_settings,
            "envelope_points": self.envelope_points,
            "fade_in": self.fade_in,
            "fade_out": self.fade_out,
            "master_gain": self.master_gain,
            "stem_mix": self.current_stem_mix,
            "stems_list": list(self.stems.keys()),
            "version": 1
        }
        
        with open(path, 'w') as f:
            json.dump(meta, f, indent=2)
        
        # Save audio files alongside
        audio_dir = path.parent / (path.stem + "_audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        if self.audio_data is not None:
            sf.write(str(audio_dir / "original.wav"), self.audio_data, self.sample_rate)
        
        for name, data in self.stems.items():
            safe_name = name.replace('/', '_')
            sf.write(str(audio_dir / f"{safe_name}.wav"), data, self.sample_rate)

    @classmethod
    def load(cls, path: str) -> 'ProjectSession':
        with open(path, 'r') as f:
            meta = json.load(f)
        
        session = cls(project_path=path)
        session.sample_rate = meta.get("sample_rate", 44100)
        session.bpm = meta.get("bpm", 120.0)
        session.target_bpm = meta.get("target_bpm", 120.0)
        session.eq_settings = meta.get("eq_settings", {"low": 0.0, "mid": 0.0, "high": 0.0})
        session.envelope_points = meta.get("envelope_points", [])
        session.fade_in = meta.get("fade_in", 0.0)
        session.fade_out = meta.get("fade_out", 0.0)
        session.master_gain = meta.get("master_gain", 0.0)
        session.current_stem_mix = meta.get("stem_mix", {})
        
        audio_dir = Path(path).parent / (Path(path).stem + "_audio")
        
        # Load original
        original_path = audio_dir / "original.wav"
        if original_path.exists():
            session.audio_data, _ = sf.read(str(original_path), always_2d=True, dtype='float32')
        
        # Load stems
        for name in meta.get("stems_list", []):
            safe_name = name.replace('/', '_')
            stem_path = audio_dir / f"{safe_name}.wav"
            if stem_path.exists():
                session.stems[name], _ = sf.read(str(stem_path), always_2d=True, dtype='float32')
        
        return session