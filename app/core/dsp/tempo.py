import numpy as np
import librosa

def time_stretch(data: np.ndarray, rate: float) -> np.ndarray:
    """
    Stretch audio time by 'rate' (e.g. 1.1 = 10% faster, 0.9 = 10% slower)
    preserving pitch using phase vocoder.
    data: shape (samples, channels)
    """
    if rate == 1.0 or data.size == 0:
        return data
    
    stretched_channels = []
    for ch in range(data.shape[1]):
        # librosa time_stretch expects 1D mono
        stretched = librosa.effects.time_stretch(data[:, ch], rate=rate)
        stretched_channels.append(stretched)
    
    # Ensure equal length across channels
    min_len = min(len(c) for c in stretched_channels)
    aligned = np.stack([c[:min_len] for c in stretched_channels], axis=-1)
    return aligned
