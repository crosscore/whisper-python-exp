# services/realtime_service.py
from typing import Optional, Callable, Dict, List
import numpy as np
import asyncio
import queue
from datetime import datetime
from pathlib import Path
import wave
import json

class RealtimeTranscriptionService:
    def __init__(
        self,
        transcription_service,
        sample_rate: int = 16000,
        chunk_duration: float = 2.0,
        max_queue_size: int = 10
    ):
        """Initialize realtime transcription service"""
        self.transcription_service = transcription_service
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)

        # Buffers and queues
        self.audio_buffer = queue.Queue(maxsize=max_queue_size)
        self.current_chunk = []
        self.transcription_callbacks: List[Callable] = []

        # State management
        self.is_processing = False
        self.total_processed = 0
        self.dropped_chunks = 0

    async def process_audio_chunk(self, chunk_data: np.ndarray) -> Optional[Dict]:
        """Process a single chunk of audio data"""
        try:
            # Normalize audio data
            if chunk_data.dtype == np.int16:
                chunk_data = chunk_data.astype(np.float32) / 32768.0

            # Transcribe the chunk
            result = self.transcription_service.transcribe_audio_data(
                chunk_data,
                sample_rate=self.sample_rate
            )

            if result and result.get("text", "").strip():
                return {
                    "text": result["text"],
                    "timestamp": datetime.now().isoformat(),
                    "confidence": result.get("confidence", 1.0)
                }
            return None

        except Exception as e:
            print(f"Error processing audio chunk: {e}")
            return None

    async def handle_audio_stream(self, audio_data: bytes) -> None:
        """Handle incoming audio stream data"""
        try:
            # Convert bytes to numpy array
            chunk = np.frombuffer(audio_data, dtype=np.int16)

            # Add to current chunk buffer
            self.current_chunk.extend(chunk)

            # Process if we have enough data
            if len(self.current_chunk) >= self.chunk_size:
                # Extract chunk for processing
                process_chunk = np.array(self.current_chunk[:self.chunk_size])
                self.current_chunk = self.current_chunk[self.chunk_size:]

                try:
                    # Try to add to processing queue
                    self.audio_buffer.put_nowait(process_chunk)
                    self.total_processed += len(process_chunk)
                except queue.Full:
                    self.dropped_chunks += 1
                    print(f"Warning: Buffer full, dropping chunk. Total dropped: {self.dropped_chunks}")

        except Exception as e:
            print(f"Error handling audio stream: {e}")

    async def process_queue(self) -> None:
        """Process audio chunks from the queue"""
        self.is_processing = True

        try:
            while self.is_processing:
                try:
                    # Get chunk from queue with timeout
                    chunk = self.audio_buffer.get(timeout=0.1)
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                # Process the chunk
                result = await self.process_audio_chunk(chunk)
                if result:
                    # Notify all callbacks with the result
                    for callback in self.transcription_callbacks:
                        try:
                            await callback(result)
                        except Exception as e:
                            print(f"Error in transcription callback: {e}")

        except Exception as e:
            print(f"Error in queue processing: {e}")
        finally:
            self.is_processing = False

    def add_transcription_callback(self, callback: Callable) -> None:
        """Add a callback for transcription results"""
        self.transcription_callbacks.append(callback)

    def remove_transcription_callback(self, callback: Callable) -> None:
        """Remove a transcription callback"""
        if callback in self.transcription_callbacks:
            self.transcription_callbacks.remove(callback)

    def get_status(self) -> Dict:
        """Get current processing status"""
        return {
            "is_processing": self.is_processing,
            "total_processed": self.total_processed,
            "dropped_chunks": self.dropped_chunks,
            "queue_size": self.audio_buffer.qsize(),
            "current_chunk_size": len(self.current_chunk)
        }

    def stop(self) -> None:
        """Stop processing"""
        self.is_processing = False
        # Clear buffers
        self.current_chunk = []
        while not self.audio_buffer.empty():
            try:
                self.audio_buffer.get_nowait()
            except queue.Empty:
                break
