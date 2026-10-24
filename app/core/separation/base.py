from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Callable, Optional

class SeparationBackend(ABC):
    @abstractmethod
    def separate(self, audio: np.ndarray, sample_rate: int, callback: Optional[Callable[[dict], None]] = None) -> Dict[str, np.ndarray]:
        """
        Separate audio into stems (e.g. 'vocals', 'drums', 'bass', 'other').
        Returns dict mapping stem_name -> numpy array (samples, channels).
        """
        pass
