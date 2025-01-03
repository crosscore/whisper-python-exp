# backend/api/transcription.py
from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
from typing import Dict, Optional
import tempfile
import shutil

from services.transcription_service import TranscriptionService

router = APIRouter()
transcription_service = TranscriptionService(model_name="base")

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None
) -> Dict:
    """Transcribe uploaded audio file"""
    if not file.filename.endswith(('.wav', '.mp3', '.m4a')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload WAV, MP3, or M4A file."
        )

    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        try:
            # Save uploaded file to temporary file
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = Path(tmp_file.name)

            # Update language if specified
            if language:
                transcription_service.language = language

            # Transcribe the audio file
            result = transcription_service.transcribe_file(tmp_path)
            if result is None:
                raise HTTPException(
                    status_code=500,
                    detail="Transcription failed"
                )

            return result

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing file: {str(e)}"
            )
        finally:
            # Clean up temporary file
            tmp_path = Path(tmp_file.name)
            if tmp_path.exists():
                tmp_path.unlink()

@router.get("/model-info")
async def get_model_info() -> Dict:
    """Get information about the current transcription model"""
    return transcription_service.get_model_info()

@router.post("/transcribe/{recording_id}")
async def transcribe_recording(recording_id: str) -> Dict:
    """Transcribe an existing recording"""
    recording_path = Path("recorded_audio") / f"{recording_id}.wav"

    if not recording_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Recording {recording_id} not found"
        )

    result = transcription_service.transcribe_file(recording_path)
    if result is None:
        raise HTTPException(
            status_code=500,
            detail="Transcription failed"
        )

    # Save transcription result
    transcription_path = recording_path.with_suffix(".txt")
    try:
        with open(transcription_path, "w", encoding="utf-8") as f:
            f.write(result["text"])
    except Exception as e:
        print(f"Error saving transcription: {e}")

    return result
