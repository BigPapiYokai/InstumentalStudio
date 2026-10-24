import numpy as np

def apply_fades(data: np.ndarray, sample_rate: int, fade_in_sec: float, fade_out_sec: float) -> np.ndarray:
    """
    Apply linear fade in and fade out.
    """
    out = data.copy()
    total_samples = len(out)
    
    fi_samples = int(fade_in_sec * sample_rate)
    fo_samples = int(fade_out_sec * sample_rate)
    
    if fi_samples > 0 and fi_samples < total_samples:
        fade_in = np.linspace(0.0, 1.0, fi_samples)
        if out.ndim == 2:
            fade_in = fade_in[:, np.newaxis]
        out[:fi_samples] *= fade_in
        
    if fo_samples > 0 and fo_samples < total_samples:
        fade_out = np.linspace(1.0, 0.0, fo_samples)
        if out.ndim == 2:
            fade_out = fade_out[:, np.newaxis]
        out[-fo_samples:] *= fade_out
        
    return out
