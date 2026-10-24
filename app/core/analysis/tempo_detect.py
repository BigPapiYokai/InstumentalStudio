import numpy as np
import librosa

def detect_bpm(data: np.ndarray, sample_rate: int) -> float:
    """
    Detect BPM of audio data using librosa beat tracking.
    """
    if data.size == 0:
        return 120.0
    
    mono = np.mean(data, axis=1) if data.ndim == 2 else data
    try:
        tempo, _ = librosa.beat.beat_track(y=mono, sr=sample_rate)
        if isinstance(tempo, np.ndarray):
            tempo = float(tempo[0])
        return float(tempo) if tempo > 0 else 120.0
    except Exception:
        return 120.0
