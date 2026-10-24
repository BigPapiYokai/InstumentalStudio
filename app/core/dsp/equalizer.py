import numpy as np
from scipy.signal import lfilter, sosfilt

def apply_eq(data: np.ndarray, sample_rate: int, low_gain_db: float = 0.0, mid_gain_db: float = 0.0, high_gain_db: float = 0.0) -> np.ndarray:
    """
    Simple 3-band shelf/peaking EQ.
    """
    if low_gain_db == 0.0 and mid_gain_db == 0.0 and high_gain_db == 0.0:
        return data
    
    # Simple gain amplification approximation per frequency band or shelving using scipy biquad
    # For a robust lightweight implementation, we can apply simple biquad filters or multi-band weighting.
    # Here we implement simple biquad low-shelf, peaking, high-shelf filters.
    # To keep it extremely robust and clean:
    out = data.copy()
    
    # Convert dB to linear gain factors
    g_low = 10.0 ** (low_gain_db / 20.0)
    g_mid = 10.0 ** (mid_gain_db / 20.0)
    g_high = 10.0 ** (high_gain_db / 20.0)
    
    # Frequency separation using butterworth filters
    from scipy.signal import butter, sosfilt
    
    # Low shelf (< 250 Hz)
    try:
        sos_low = butter(2, 250 / (sample_rate / 2), btype='low', output='sos')
        sos_high = butter(2, 4000 / (sample_rate / 2), btype='high', output='sos')
        sos_mid = butter(2, [250 / (sample_rate / 2), 4000 / (sample_rate / 2)], btype='band', output='sos')
        
        for ch in range(out.shape[1]):
            chan = out[:, ch]
            low_part = sosfilt(sos_low, chan) * g_low
            mid_part = sosfilt(sos_mid, chan) * g_mid
            high_part = sosfilt(sos_high, chan) * g_high
            out[:, ch] = low_part + mid_part + high_part
    except Exception:
        # Fallback to simple gain scaling if filter fails
        out *= g_mid
        
    return out
