# src/audio_processor.pyimport numpy as np
import queue
from pathlib import Path
import sounddevice as sd
import threading
import time
from datetime import datetime
import wave

class BufferedAudioProcessor:
    def __init__(self, model, sample_rate=44100, chunk_duration=2.0, channels=1, max_queue_size=10):
        self.model = model
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_samples = int(sample_rate * chunk_duration)

        # バッファサイズの制限を追加
        self.audio_buffer = queue.Queue(maxsize=max_queue_size)
        self.text_buffer = queue.Queue()
        self.is_running = False
        self.current_audio_chunk = []

        self.processing_thread = None
        self.last_process_time = time.time()
        self.min_process_interval = 0.5  # Minimum time between processing in seconds

        # 音声データの統計情報
        self.total_processed_samples = 0
        self.dropped_samples = 0

    def audio_callback(self, indata, frames, callback_time, status):
        """Callback for audio input"""
        if status:
            print(f'Audio callback error: {status}')
            return

        try:
            # 新しい音声データを現在のチャンクに追加
            self.current_audio_chunk.extend(indata.flatten())

            # 十分なデータが集まった場合の処理
            current_time = time.time()
            while len(self.current_audio_chunk) >= self.chunk_samples:
                if current_time - self.last_process_time >= self.min_process_interval:
                    # チャンクを切り出し
                    chunk_data = np.array(self.current_audio_chunk[:self.chunk_samples])
                    self.current_audio_chunk = self.current_audio_chunk[self.chunk_samples:]

                    # バッファが一杯の場合は古いデータを破棄
                    try:
                        self.audio_buffer.put_nowait(chunk_data)
                        self.total_processed_samples += len(chunk_data)
                    except queue.Full:
                        self.dropped_samples += len(chunk_data)
                        print(f"Warning: Buffer full, dropping audio chunk. Dropped samples: {self.dropped_samples}")

                    self.last_process_time = current_time
                else:
                    break

            # メモリ使用量の制限
            if len(self.current_audio_chunk) > self.chunk_samples * 2:
                self.current_audio_chunk = self.current_audio_chunk[-self.chunk_samples:]

        except Exception as e:
            print(f"Error in audio callback: {e}")

    def process_audio(self):
        """Process audio chunks in a separate thread"""
        while self.is_running:
            try:
                # 音声データの取得（タイムアウト付き）
                try:
                    audio_data = self.audio_buffer.get(timeout=0.5)
                except queue.Empty:
                    continue

                # Convert to appropriate format for whisper
                audio_float32 = audio_data.astype(np.float32) / 32768.0

                # Process with whisper
                result = self.model.transcribe(
                    audio_float32,
                    language='ja',
                    fp16=False,
                    initial_prompt="",
                )

                if result["text"].strip():
                    self.text_buffer.put(result["text"])

            except Exception as e:
                print(f"Error processing audio: {e}")
                time.sleep(0.1)  # エラー時は少し待機

    def start(self):
        """Start audio processing"""
        if self.is_running:
            return

        self.is_running = True
        self.total_processed_samples = 0
        self.dropped_samples = 0

        # Initialize audio stream
        self.stream = sd.InputStream(
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=self.audio_callback,
            dtype=np.int16,
            blocksize=int(self.sample_rate * 0.1)  # 100ms blocks
        )

        # Start processing thread
        self.processing_thread = threading.Thread(target=self.process_audio, daemon=True)
        self.processing_thread.start()
        self.stream.start()

    def stop(self):
        """Stop audio processing"""
        if not self.is_running:
            return

        self.is_running = False

        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)  # タイムアウト付きの終了待機

        # 統計情報の表示
        total_samples = self.total_processed_samples + self.dropped_samples
        if total_samples > 0:
            drop_rate = (self.dropped_samples / total_samples) * 100
            print(f"Audio processing statistics:")
            print(f"Total processed samples: {self.total_processed_samples}")
            print(f"Dropped samples: {self.dropped_samples}")
            print(f"Drop rate: {drop_rate:.2f}%")

    def get_text(self):
        """Get accumulated text from the buffer"""
        text_pieces = []
        while not self.text_buffer.empty():
            text_pieces.append(self.text_buffer.get())
        return " ".join(text_pieces) if text_pieces else ""
