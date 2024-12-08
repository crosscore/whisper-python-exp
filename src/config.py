# src/config.py
from pathlib import Path

# PROJECT DIRECTORY SETTINGS
ROOT_DIR = Path(__file__).parent.parent
MODEL_DIR = ROOT_DIR / "model"
AUDIO_DIR = ROOT_DIR / "recorded_audio"

# MODEL SETTINGS
MODEL_NAME = "turbo"

# RECORD SETTINGS
SAMPLE_RATE = 44100
CHANNELS = 1
