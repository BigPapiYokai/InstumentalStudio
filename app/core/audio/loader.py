import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Union, Tuple
from pydub import AudioSegment

def load_audio(file_path: Union[str, Path], target_sr: int = 44100) -> Tuple[np.ndarray, int]:
    """
    Load any popular audio file format into float32 numpy array of shape (samples, channels)
    and target sample rate.
    """
    path_str = str(file_path)
    try:
        # Try soundfile first (fast path for wav, flac, ogg)
        data, sr = sf.read(path_str, always_2d=True, dtype='float32')
        if sr != target_sr:
            import librosa
            resampled = []
            for ch in range(data.shape[1]):
                resampled.append(librosa.resample(data[:, ch], orig_sr=sr, target_sr=target_sr))
            data = np.stack(resampled, axis=-1)
            sr = target_sr
        return data, sr
    except Exception:
        # Fallback to pydub + ffmpeg for m4a, mp3, wma, etc.
        try:
            segment = AudioSegment.from_file(path_str)
            segment = segment.set_frame_rate(target_sr)
            segment = segment.set_channels(2)
            samples = np.array(segment.get_array_of_samples(), dtype=np.float32)
            if segment.channels == 2:
                samples = samples.reshape((-1, 2))
            else:
                samples = np.column_stack((samples, samples))
            samples /= 32768.0
            return samples, target_sr
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file {path_str}: {e}")
