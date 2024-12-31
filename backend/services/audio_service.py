# services/audio_service.py
import sounddevice as sd
import numpy as np
import wave
from pathlib import Path
from datetime import datetime
import queue
from typing import Optional

class AudioService:
    def __init__(self, sample_rate: int = 44100, channels: int = 1):
        """Initialize audio service with recording parameters"""
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_data = []
        self._stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        """Callback function for audio recording"""
        if status:
            print(f'Audio callback error: {status}')
        self.audio_queue.put(indata.copy())

    def start_recording(self) -> bool:
        """Start audio recording"""
        if self.is_recording:
            return False

        try:
            self.audio_data = []
            self.is_recording = True
            self._stream = sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=np.int16,
                callback=self._audio_callback,
                blocksize=1024
            )
            self._stream.start()
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            self.is_recording = False
            return False

    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop recording and return the recorded audio data"""
        if not self.is_recording:
            return None

        try:
            if self._stream:
                self._stream.stop()
                self._stream.close()
            self.is_recording = False

            # Get remaining audio data from queue
            while not self.audio_queue.empty():
                self.audio_data.append(self.audio_queue.get())

            return np.concatenate(self.audio_data) if self.audio_data else None
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return None
        finally:
            self._stream = None

    def save_audio(self, audio_data: np.ndarray, output_dir: Path) -> Optional[Path]:
        """Save audio data to WAV file"""
        if audio_data is None:
            return None

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_dir / f"audio_{timestamp}.wav"

            with wave.open(str(filename), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())

            return filename
        except Exception as e:
            print(f"Error saving audio: {e}")
            return None

    def get_recording_status(self) -> dict:
        """Get current recording status"""
        return {
            "is_recording": self.is_recording,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "queue_size": self.audio_queue.qsize()
        }
