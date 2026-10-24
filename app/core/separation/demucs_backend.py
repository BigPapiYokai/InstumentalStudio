import numpy as np
import torch as th
from typing import Dict, Callable, Optional
from .base import SeparationBackend
from demucs.api import Separator

class DemucsBackend(SeparationBackend):
    def __init__(self, model_name: str = "htdemucs", device: Optional[str] = None):
        self.model_name = model_name
        if device is None:
            self.device = "cuda" if th.cuda.is_available() else "cpu"
        else:
            self.device = device
            
    def separate(self, audio: np.ndarray, sample_rate: int, callback: Optional[Callable[[dict], None]] = None) -> Dict[str, np.ndarray]:
        """
        Separate audio tensor using Demucs.
        audio: shape (samples, channels), float32
        """
        # Demucs expects tensor of shape (channels, samples)
        tensor_in = th.from_numpy(audio.T).float()
        
        separator = Separator(
            model=self.model_name,
            device=self.device,
            progress=True,
            callback=callback
        )
        
        _, separated_dict = separator.separate_tensor(tensor_in, sr=sample_rate)
        
        # Convert back to numpy shape (samples, channels)
        out = {}
        for stem, t in separated_dict.items():
            out[stem] = t.cpu().numpy().T
            
        return out
