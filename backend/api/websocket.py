# backend/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
import asyncio
import json
from services.realtime_service import RealtimeTranscriptionService
from services.transcription_service import TranscriptionService

router = APIRouter()

# Initialize services
transcription_service = TranscriptionService(model_name="base")
realtime_service = RealtimeTranscriptionService(transcription_service)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_transcription(self, transcription: Dict, websocket: WebSocket):
        try:
            await websocket.send_json(transcription)
        except Exception as e:
            print(f"Error sending transcription: {e}")
            await self.disconnect(websocket)

manager = ConnectionManager()

@router.websocket("/ws/audio")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # Create a callback for this connection
    async def transcription_callback(result: Dict):
        await manager.send_transcription(result, websocket)

    try:
        # Add callback for transcription results
        realtime_service.add_transcription_callback(transcription_callback)

        # Start processing task
        process_task = asyncio.create_task(realtime_service.process_queue())

        while True:
            # Receive audio data
            audio_data = await websocket.receive_bytes()
            await realtime_service.handle_audio_stream(audio_data)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error in websocket connection: {e}")
    finally:
        # Clean up
        realtime_service.remove_transcription_callback(transcription_callback)
        manager.disconnect(websocket)
        realtime_service.stop()

@router.get("/status")
async def get_status() -> Dict:
    """Get current processing status"""
    return realtime_service.get_status()
