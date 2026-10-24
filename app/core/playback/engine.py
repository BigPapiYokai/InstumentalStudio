import numpy as np
import sounddevice as sd
from typing import Optional, Callable

class PlaybackEngine:
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.audio_data: Optional[np.ndarray] = None # shape (samples, channels)
        self.position = 0 # current sample index
        self.is_playing = False
        self.volume = 1.0
        self.loop = False
        self.loop_start = 0
        self.loop_end = 0
        self.stream: Optional[sd.OutputStream] = None
        self.on_position_changed: Optional[Callable[[int], None]] = None

    def set_audio(self, data: np.ndarray, sr: int):
        self.stop()
        self.audio_data = data
        self.sample_rate = sr
        self.position = 0
        self.loop_start = 0
        self.loop_end = len(data) if data is not None else 0

    def play(self):
        if self.audio_data is None or self.is_playing:
            return
        
        self.is_playing = True
        
        def callback(outdata, frames, time_info, status):
            if not self.is_playing or self.audio_data is None:
                outdata.fill(0)
                return
            
            end_pos = self.position + frames
            if end_pos >= len(self.audio_data):
                if self.loop and self.loop_end > self.loop_start:
                    self.position = self.loop_start
                    end_pos = self.position + frames
                else:
                    end_pos = len(self.audio_data)
                    self.is_playing = False
            
            chunk = self.audio_data[self.position:end_pos] * self.volume
            
            if len(chunk) < frames:
                pad = frames - len(chunk)
                chunk = np.pad(chunk, ((0, pad), (0, 0)), 'constant')
                
            outdata[:] = chunk
            self.position = end_pos
            
            if self.on_position_changed:
                try:
                    self.on_position_changed(self.position)
                except Exception:
                    pass
                    
            if not self.is_playing:
                raise sd.CallbackStop()

        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                callback=callback,
                finished_callback=lambda: setattr(self, 'is_playing', False)
            )
            self.stream.start()
        except Exception as e:
            self.is_playing = False
            raise RuntimeError(f"Audio playback error: {e}")

    def pause(self):
        self.is_playing = False
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def stop(self):
        self.pause()
        self.position = 0

    def seek(self, sample_idx: int):
        if self.audio_data is not None:
            self.position = max(0, min(sample_idx, len(self.audio_data) - 1))

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(vol, 2.0))
