import streamlit as st
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
import os
import threading
import queue

# 音声保存用のディレクトリ作成
AUDIO_DIR = "../recorded_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# 録音設定
SAMPLE_RATE = 44100
CHANNELS = 1

class AudioRecorder:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.audio_data = []

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(f'Audio callback error: {status}')
        self.audio_queue.put(indata.copy())

    def start_recording(self):
        self.audio_data = []
        self.is_recording = True
        self.stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=SAMPLE_RATE,
            dtype=np.int16,
            callback=self.callback
        )
        self.stream.start()

    def stop_recording(self):
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        self.is_recording = False
        # キューに残っているデータを全て取得
        while not self.audio_queue.empty():
            self.audio_data.append(self.audio_queue.get())
        return np.concatenate(self.audio_data) if self.audio_data else None

def save_audio(audio_data, filename):
    """録音データをWAVファイルとして保存する"""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

def main():
    st.title("音声録音アプリ")

    # AudioRecorderのインスタンスをセッション状態に保存
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()

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
                    filename = os.path.join(AUDIO_DIR, f"audio_{timestamp}.wav")
                    # 音声の保存
                    save_audio(recorded_audio, filename)
                    st.success(f"録音を保存しました: {filename}")
                st.rerun()

    # 録音状態の表示
    if st.session_state.audio_recorder.is_recording:
        st.warning("録音中...")
        # 録音中のデータをaudio_dataに追加
        while not st.session_state.audio_recorder.audio_queue.empty():
            chunk = st.session_state.audio_recorder.audio_queue.get()
            st.session_state.audio_recorder.audio_data.append(chunk)

    # 保存された音声ファイルの一覧表示
    st.subheader("録音済みファイル")
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]
    if audio_files:
        for audio_file in sorted(audio_files, reverse=True):
            st.text(audio_file)
    else:
        st.info("録音ファイルはまだありません")

if __name__ == "__main__":
    main()
