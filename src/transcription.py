# transcription.py
import whisper
import torch
from pathlib import Path
from config import MODEL_DIR

def download_whisper_model():
    """Whisperモデルをダウンロードし、指定のディレクトリに保存する"""
    model_path = MODEL_DIR / "model.pt"
    if not model_path.exists():
        print("Downloading Whisper model...")
        model = whisper.load_model("turbo")
        torch.save(model.state_dict(), str(model_path))
        print(f"Model saved to {model_path}")
    return model_path

def load_whisper_model():
    """保存されたモデルを読み込む"""
    model_path = MODEL_DIR / "model.pt"
    if not model_path.exists():
        model_path = download_whisper_model()

    model = whisper.load_model("turbo")
    state_dict = torch.load(str(model_path))
    model.load_state_dict(state_dict)
    return model

def transcribe_audio(file_path, whisper_model):
    """音声ファイルを文字起こしする"""
    try:
        result = whisper_model.transcribe(str(file_path), language='ja', fp16=False)
        return result["text"]
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def save_transcription_to_file(file_path, transcription):
    """文字起こし結果をテキストファイルに保存する"""
    txt_file_path = file_path.with_suffix(".txt")
    with open(txt_file_path, "w", encoding="utf-8") as f:
        f.write(transcription)
