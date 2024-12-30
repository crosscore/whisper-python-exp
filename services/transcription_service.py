# services/transcription_service.py
import whisper
import torch
from pathlib import Path
from typing import Optional, Dict
import numpy as np

class TranscriptionService:
    def __init__(
        self,
        model_name: str = "base",
        model_dir: Optional[Path] = None,
        language: str = "ja",
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """Initialize transcription service with Whisper model"""
        self.model_name = model_name
        self.model_dir = model_dir or Path("models")
        self.language = language
        self.device = device
        self.model = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize and load Whisper model"""
        try:
            self.model_dir.mkdir(parents=True, exist_ok=True)
            model_path = self.model_dir / f"whisper-{self.model_name}.pt"

            # Load or download model
            if model_path.exists():
                print(f"Loading existing model from {model_path}")
                self.model = whisper.load_model(self.model_name, device=self.device)
                state_dict = torch.load(str(model_path), map_location=self.device)
                self.model.load_state_dict(state_dict)
            else:
                print(f"Downloading Whisper {self.model_name} model...")
                self.model = whisper.load_model(self.model_name, device=self.device)
                # Save model for future use
                torch.save(self.model.state_dict(), str(model_path))

        except Exception as e:
            print(f"Error initializing Whisper model: {e}")
            raise

    def transcribe_file(self, audio_path: Path) -> Optional[Dict]:
        """Transcribe audio file"""
        if not self.model:
            raise RuntimeError("Model not initialized")

        try:
            result = self.model.transcribe(
                str(audio_path),
                language=self.language,
                fp16=False,
                task="transcribe"
            )
            return {
                "text": result["text"],
                "language": result.get("language", self.language),
                "segments": result.get("segments", [])
            }
        except Exception as e:
            print(f"Error transcribing file: {e}")
            return None

    def transcribe_audio_data(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[Dict]:
        """Transcribe audio data directly from numpy array"""
        if not self.model:
            raise RuntimeError("Model not initialized")

        try:
            # Normalize audio data if needed
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0

            result = self.model.transcribe(
                audio_data,
                language=self.language,
                fp16=False,
                task="transcribe"
            )
            return {
                "text": result["text"],
                "language": result.get("language", self.language),
                "segments": result.get("segments", [])
            }
        except Exception as e:
            print(f"Error transcribing audio data: {e}")
            return None

    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "language": self.language,
            "device": self.device,
            "model_path": str(self.model_dir / f"whisper-{self.model_name}.pt")
        }
