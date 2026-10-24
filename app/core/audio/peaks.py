import numpy as np
from typing import Tuple

def compute_peaks(data: np.ndarray, num_points: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute min and max peaks for waveform rendering over time.
    data: shape (samples, channels)
    Returns (mins, maxs) of shape (num_points, channels)
    """
    if data.size == 0:
        return np.zeros((num_points, 2)), np.zeros((num_points, 2))
    
    # Mix down to mono for peak visualization or handle per channel
    if data.ndim == 2:
        mono = np.mean(data, axis=1)
    else:
        mono = data

    samples = len(mono)
    if samples <= num_points:
        return np.column_stack((mono, mono)), np.column_stack((mono, mono))

    chunk_size = samples // num_points
    trimmed = mono[:chunk_size * num_points]
    reshaped = trimmed.reshape((num_points, chunk_size))
    
    mins = np.min(reshaped, axis=1)
    maxs = np.max(reshaped, axis=1)
    
    return mins, maxs
