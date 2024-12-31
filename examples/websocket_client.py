# examples/websocket_client.py
import asyncio
import websockets
import json
import sounddevice as sd
import numpy as np

async def record_and_stream():
    # WebSocket connection
    uri = "ws://localhost:8000/ws/audio"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket server")

        # Audio recording parameters
        sample_rate = 16000
        channels = 1
        chunk_duration = 0.1  # seconds
        chunk_size = int(sample_rate * chunk_duration)

        # Callback for audio input
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback error: {status}")

            # Convert to bytes and send
            audio_data = indata.tobytes()
            asyncio.run_coroutine_threadsafe(
                websocket.send(audio_data),
                loop
            )

        # Start recording
        with sd.InputStream(
            channels=channels,
            samplerate=sample_rate,
            dtype=np.int16,
            callback=audio_callback,
            blocksize=chunk_size
        ):
            print("Started recording...")

            # Receive and print transcriptions
            while True:
                try:
                    result = await websocket.recv()
                    transcription = json.loads(result)
                    print(f"Transcription: {transcription['text']}")
                except Exception as e:
                    print(f"Error: {e}")
                    break

async def main():
    try:
        await record_and_stream()
    except KeyboardInterrupt:
        print("\nStopping...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
