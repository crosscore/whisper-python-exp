# config.py
from pathlib import Path

# プロジェクトのディレクトリ設定
ROOT_DIR = Path(__file__).parent.parent
MODEL_DIR = ROOT_DIR / "model"
AUDIO_DIR = ROOT_DIR / "recorded_audio"

# 録音設定
SAMPLE_RATE = 44100
CHANNELS = 1
