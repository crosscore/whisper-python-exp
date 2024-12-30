# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.audio import router as audio_router

app = FastAPI(title="Audio Recording API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio_router, prefix="/audio", tags=["audio"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
