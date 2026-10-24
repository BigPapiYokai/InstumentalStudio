import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Union

def save_audio(file_path: Union[str, Path], data: np.ndarray, sample_rate: int, subtype: str = 'PCM_16'):
    """
    Save audio numpy array (samples, channels) to file (wav, flac, ogg, etc.).
    """
    path_str = str(file_path)
    sf.write(path_str, data, sample_rate, subtype=subtype)
