# src/audio_recorder.py
import sounddevice as sd
import numpy as np
import wave
import queue
from datetime import datetime
from pathlib import Path
from config import SAMPLE_RATE, CHANNELS, AUDIO_DIR

class AudioRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_data = []

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(f'Audio callback error: {status}')
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        """Start recording"""
        self.audio_data = []
        self.is_recording = True
        self.stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=np.int16,
            callback=self.callback
        )
        self.stream.start()

    def stop_recording(self):
        """Stop recording and return the recorded data"""
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.is_recording = False

        while not self.audio_queue.empty():
            self.audio_data.append(self.audio_queue.get())

        return np.concatenate(self.audio_data) if self.audio_data else None

def save_audio(audio_data, filename):
    """Save recorded data as a WAV file"""
    if isinstance(filename, Path):
        filename = str(filename)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

def get_audio_duration(file_path):
    """Get the duration of a WAV file"""
    with wave.open(str(file_path), 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
        return round(duration, 1)
