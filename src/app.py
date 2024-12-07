import streamlit as st
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
import os
import threading
import queue
import whisper
import torch
import tempfile
from pathlib import Path

# プロジェクトのルートディレクトリを取得
ROOT_DIR = Path(__file__).parent.parent
MODEL_DIR = ROOT_DIR / "model"
AUDIO_DIR = ROOT_DIR / "recorded_audio"

# ディレクトリの作成
MODEL_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# 録音設定
SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK_DURATION = 3  # チャンクの長さ（秒）
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)

def download_whisper_model():
    """Whisperモデルをダウンロードし、指定のディレクトリに保存する"""
    model_path = MODEL_DIR / "model.pt"
    if not model_path.exists():
        print("Downloading Whisper model...")
        # モデルをダウンロード
        model = whisper.load_model("base")
        # モデルの状態を保存
        torch.save(model.state_dict(), str(model_path))
        print(f"Model saved to {model_path}")
    return model_path

def load_whisper_model():
    """保存されたモデルを読み込む"""
    model_path = MODEL_DIR / "model.pt"
    if not model_path.exists():
        model_path = download_whisper_model()

    # モデルのインスタンスを作成
    model = whisper.load_model("base")
    # 保存された重みを読み込む
    state_dict = torch.load(str(model_path))
    model.load_state_dict(state_dict)
    return model

class AudioRecorder:
    def __init__(self, model):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_data = []
        self.recognition_queue = queue.Queue()
        self.recognition_thread = None
        self.current_chunk = []
        self.samples_collected = 0
        self.whisper_model = model  # モデルをインスタンス変数として保持
        self.recognition_results = []  # 認識結果を保持

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(f'Audio callback error: {status}')
        self.audio_queue.put(indata.copy())

        # チャンク処理のための音声データ収集
        self.current_chunk.extend(indata.flatten())
        self.samples_collected += len(indata.flatten())

        # チャンクが完成したら認識キューに追加
        if self.samples_collected >= CHUNK_SAMPLES:
            chunk_data = np.array(self.current_chunk[:CHUNK_SAMPLES], dtype=np.int16)
            self.recognition_queue.put(chunk_data)
            # 残りのサンプルを次のチャンクの開始点とする
            self.current_chunk = self.current_chunk[CHUNK_SAMPLES:]
            self.samples_collected -= CHUNK_SAMPLES

    def start_recording(self):
        self.audio_data = []
        self.current_chunk = []
        self.samples_collected = 0
        self.is_recording = True
        self.recognition_results = []  # 認識結果をリセット
        self.stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=np.int16,
            callback=self.callback
        )
        self.stream.start()

        # 認識スレッドの開始
        self.recognition_thread = threading.Thread(target=self.recognition_worker)
        self.recognition_thread.start()

    def stop_recording(self):
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.is_recording = False

        # 残りのデータを処理
        while not self.audio_queue.empty():
            self.audio_data.append(self.audio_queue.get())

        # 認識スレッドの終了待ち
        if self.recognition_thread:
            self.recognition_queue.put(None)  # 終了シグナル
            self.recognition_thread.join()

        return np.concatenate(self.audio_data) if self.audio_data else None

    def recognition_worker(self):
        """音声認識ワーカースレッド"""
        try:
            while True:
                chunk = self.recognition_queue.get()
                if chunk is None:  # 終了シグナル
                    break

                # 一時ファイルに音声データを保存
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=True) as temp_file:
                    save_audio(chunk, temp_file.name)
                    # Whisperで認識
                    try:
                        result = self.whisper_model.transcribe(
                            temp_file.name,
                            language='ja',
                            fp16=False
                        )
                        if result["text"].strip():  # 空でない結果のみを追加
                            self.recognition_results.append(result["text"])
                    except Exception as e:
                        print(f"Recognition error: {e}")
        except Exception as e:
            print(f"Worker thread error: {e}")

def save_audio(audio_data, filename):
    """録音データをWAVファイルとして保存する"""
    if isinstance(filename, Path):
        filename = str(filename)
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

def get_audio_duration(file_path):
    """WAVファイルの再生時間を取得する"""
    with wave.open(str(file_path), 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
        return round(duration, 1)

def initialize_whisper():
    """Whisperモデルの初期化"""
    if 'whisper_model' not in st.session_state:
        with st.spinner('Whisperモデルを読み込んでいます...'):
            st.session_state.whisper_model = load_whisper_model()
            st.session_state.recognition_results = []

def main():
    st.title("音声録音・認識アプリ")

    # Whisperモデルの初期化
    initialize_whisper()

    # AudioRecorderのインスタンスをセッション状態に保存
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder(st.session_state.whisper_model)

    # 録音コントロール用のカラム
    col1, col2 = st.columns(2)

    with col1:
        # 録音ボタン
        if not st.session_state.audio_recorder.is_recording:
            if st.button("🎤 録音開始"):
                st.session_state.audio_recorder.start_recording()
                st.rerun()

    with col2:
        # 停止ボタン
        if st.session_state.audio_recorder.is_recording:
            if st.button("⏹ 録音停止"):
                recorded_audio = st.session_state.audio_recorder.stop_recording()
                if recorded_audio is not None:
                    # ファイル名の生成（タイムスタンプ）
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = AUDIO_DIR / f"audio_{timestamp}.wav"
                    # 音声の保存
                    save_audio(recorded_audio, filename)
                    st.success(f"録音を保存しました: {filename}")
                st.rerun()

    # 録音状態と認識結果の表示
    if st.session_state.audio_recorder.is_recording:
        st.warning("録音中...")

        # 認識結果の表示エリア
        recognition_area = st.empty()
        recognition_text = "\n".join(st.session_state.audio_recorder.recognition_results)
        recognition_area.markdown(f"**認識結果:**\n{recognition_text}")

    # 保存された音声ファイルの一覧表示と再生機能
    st.subheader("録音済みファイル")
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
    if audio_files:
        for audio_file in sorted(audio_files, reverse=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                # 音声ファイルの情報表示
                file_path = AUDIO_DIR / audio_file
                duration = get_audio_duration(file_path)
                st.text(f"{audio_file} (録音時間: {duration}秒)")

                # 音声再生用のプレイヤー
                with open(file_path, 'rb') as audio_file:
                    st.audio(audio_file.read(), format='audio/wav')

            with col2:
                # 削除ボタン
                if st.button("🗑️ 削除", key=f"delete_{audio_file}"):
                    os.remove(file_path)
                    st.success("ファイルを削除しました")
                    st.rerun()
    else:
        st.info("録音ファイルはまだありません")

if __name__ == "__main__":
    main()
