import numpy as np

def normalize(data: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    """
    Peak normalize audio data to target dB.
    """
    peak = np.max(np.abs(data))
    if peak == 0:
        return data
    target_linear = 10.0 ** (target_db / 20.0)
    return data * (target_linear / peak)

def apply_gain(data: np.ndarray, gain_db: float) -> np.ndarray:
    if gain_db == 0.0:
        return data
    factor = 10.0 ** (gain_db / 20.0)
    return data * factor
