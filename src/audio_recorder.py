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

class RealTimeAudioRecorder(AudioRecorder):
    def __init__(self, chunk_duration=3):
        super().__init__()
        self.chunk_duration = chunk_duration  # Chunk duration (seconds)
        self.chunk_samples = int(SAMPLE_RATE * chunk_duration)
        self.current_chunk = []
        self.transcription_callback = None

    def set_transcription_callback(self, callback):
        """Set transcription callback function"""
        self.transcription_callback = callback

    def callback(self, indata, frames, time, status):
        """Processing callback for audio data"""
        if status:
            print(f'Audio callback error: {status}')

        # Add audio data to queue and chunk
        self.audio_queue.put(indata.copy())
        self.current_chunk.extend(indata.flatten())

        # If chunk size is exceeded, perform transcription
        if len(self.current_chunk) >= self.chunk_samples:
            chunk_data = np.array(self.current_chunk[:self.chunk_samples])
            self.current_chunk = self.current_chunk[self.chunk_samples:]

            # Create a temporary WAV file and transcribe
            if self.transcription_callback:
                temp_filename = AUDIO_DIR / f"temp_chunk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                save_audio(chunk_data, temp_filename)
                self.transcription_callback(temp_filename)

    def stop_recording(self):
        """Recording stop process"""
        audio_data = super().stop_recording()
        self.current_chunk = []
        return audio_data

class RealTimeTranscriber:
    def __init__(self, model):
        self.model = model
        self.full_text = []

    def transcribe_chunk(self, audio_file):
        """Transcription of audio chunks"""
        try:
            result = transcribe_audio(audio_file, self.model)
            if result:
                self.full_text.append(result)
                return result
        finally:
            # Delete temporary files
            if audio_file.exists():
                audio_file.unlink()
        return None

    def get_full_text(self):
        """Get the full transcript"""
        return " ".join(self.full_text)

    def clear(self):
        """Clear the transcript"""
        self.full_text = []
