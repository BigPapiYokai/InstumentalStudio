import numpy as np
from typing import List, Tuple

def apply_envelope(data: np.ndarray, sample_rate: int, points: List[Tuple[float, float]]) -> np.ndarray:
    """
    Apply a time-varying gain envelope specified by control points (time_in_seconds, gain_linear or dB).
    points: sorted list of (time, gain_factor) e.g. [(0.0, 1.0), (5.0, 0.5)]
    """
    if not points or data.size == 0:
        return data
    
    total_samples = len(data)
    time_axis = np.arange(total_samples) / sample_rate
    
    # Sort points by time
    sorted_pts = sorted(points, key=lambda x: x[0])
    times = [p[0] for p in sorted_pts]
    gains = [p[1] for p in sorted_pts]
    
    # Interpolate gain curve across all samples
    env = np.interp(time_axis, times, gains, left=gains[0], right=gains[-1])
    
    if data.ndim == 2:
        env = env[:, np.newaxis]
        
    return data * env
