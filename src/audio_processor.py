import numpy as np
import queue
from pathlib import Path
import sounddevice as sd
import threading
import time
from datetime import datetime
import wave

class BufferedAudioProcessor:
    def __init__(self, model, sample_rate=44100, chunk_duration=2.0, channels=1):
        self.model = model
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_samples = int(sample_rate * chunk_duration)

        self.audio_buffer = queue.Queue()
        self.text_buffer = queue.Queue()
        self.is_running = False
        self.current_audio_chunk = []

        # Create processing thread
        self.processing_thread = None
        self.last_process_time = 0
        self.min_process_interval = 0.5  # Minimum time between processing in seconds

    def audio_callback(self, indata, frames, time, status):
        """Callback for audio input"""
        if status:
            print(f'Audio callback error: {status}')
            return

        # Add new audio data to the buffer
        self.audio_buffer.put(indata.copy())
        self.current_audio_chunk.extend(indata.flatten())

        # Process when enough data is collected
        if len(self.current_audio_chunk) >= self.chunk_samples:
            current_time = time.time()
            if current_time - self.last_process_time >= self.min_process_interval:
                chunk_data = np.array(self.current_audio_chunk[:self.chunk_samples])
                self.audio_buffer.put(chunk_data)
                self.current_audio_chunk = self.current_audio_chunk[self.chunk_samples:]
                self.last_process_time = current_time

    def process_audio(self):
        """Process audio chunks in a separate thread"""
        while self.is_running:
            try:
                # Get accumulated audio data
                audio_data = []
                while not self.audio_buffer.empty():
                    chunk = self.audio_buffer.get_nowait()
                    audio_data.append(chunk)

                if audio_data:
                    # Concatenate audio chunks
                    combined_audio = np.concatenate(audio_data)

                    # Convert to appropriate format for whisper
                    audio_float32 = combined_audio.astype(np.float32) / 32768.0

                    # Process with whisper
                    result = self.model.transcribe(
                        audio_float32,
                        language='ja',
                        fp16=False,
                        initial_prompt="",
                    )

                    if result["text"].strip():
                        self.text_buffer.put(result["text"])

                time.sleep(0.1)  # Prevent excessive CPU usage

            except Exception as e:
                print(f"Error processing audio: {e}")
                continue

    def start(self):
        """Start audio processing"""
        self.is_running = True
        self.stream = sd.InputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=self.audio_callback,
            dtype=np.int16,
            blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
        )

        self.processing_thread = threading.Thread(target=self.process_audio)
        self.processing_thread.start()
        self.stream.start()

    def stop(self):
        """Stop audio processing"""
        self.is_running = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        if self.processing_thread:
            self.processing_thread.join()

    def get_text(self):
        """Get accumulated text from the buffer"""
        text_pieces = []
        while not self.text_buffer.empty():
            text_pieces.append(self.text_buffer.get())
        return " ".join(text_pieces) if text_pieces else ""
