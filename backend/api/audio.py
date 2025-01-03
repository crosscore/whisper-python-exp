# backend/api/audio.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, List
import os

from services.audio_service import AudioService

router = APIRouter()
audio_service = AudioService()

# Configure output directory
AUDIO_DIR = Path("recorded_audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/start")
async def start_recording() -> Dict[str, bool]:
    """Start audio recording"""
    if audio_service.start_recording():
        return {"success": True}
    raise HTTPException(status_code=500, detail="Failed to start recording")

@router.post("/stop")
async def stop_recording() -> Dict[str, str]:
    """Stop recording and save audio file"""
    audio_data = audio_service.stop_recording()
    if audio_data is None:
        raise HTTPException(status_code=400, detail="No recording in progress")

    filename = audio_service.save_audio(audio_data, AUDIO_DIR)
    if filename is None:
        raise HTTPException(status_code=500, detail="Failed to save recording")

    return {"filename": str(filename)}

@router.get("/status")
async def get_status() -> Dict:
    """Get current recording status"""
    return audio_service.get_recording_status()

@router.get("/recordings")
async def list_recordings() -> List[Dict[str, str]]:
    """List all recorded audio files"""
    recordings = []
    for file in AUDIO_DIR.glob("*.wav"):
        recordings.append({
            "filename": file.name,
            "path": str(file),
            "size": os.path.getsize(file),
            "created": os.path.getctime(file)
        })
    return recordings

@router.get("/download/{filename}")
async def download_recording(filename: str):
    """Download a specific recording"""
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found")
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename=filename
    )
