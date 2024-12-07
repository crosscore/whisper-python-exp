import streamlit as st
import sounddevice as sd
import numpy as np
import wave
from datetime import datetime
import os

# 音声保存用のディレクトリ作成
AUDIO_DIR = "recorded_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def save_audio(recording, filename, samplerate=44100):
    """録音データをWAVファイルとして保存する"""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)  # モノラル
        wf.setsampwidth(2)  # 16ビット
        wf.setframerate(samplerate)
        wf.writeframes(recording.tobytes())

def main():
    st.title("音声録音アプリ")

    # セッション状態の初期化
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None

    # 録音コントロール用のカラム
    col1, col2 = st.columns(2)

    with col1:
        # 録音ボタン
        if not st.session_state.recording:
            if st.button("🎤 録音開始"):
                st.session_state.recording = True
                st.session_state.audio_data = []
                st.experimental_rerun()

    with col2:
        # 停止ボタン
        if st.session_state.recording:
            if st.button("⏹ 録音停止"):
                st.session_state.recording = False
                if st.session_state.audio_data:
                    # 録音データの連結
                    recorded_audio = np.concatenate(st.session_state.audio_data, axis=0)
                    # ファイル名の生成（タイムスタンプ）
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(AUDIO_DIR, f"audio_{timestamp}.wav")
                    # 音声の保存
                    save_audio(recorded_audio, filename)
                    st.success(f"録音を保存しました: {filename}")
                st.experimental_rerun()

    # 録音状態の表示
    if st.session_state.recording:
        st.warning("録音中...")
        # 音声データの取得と保存
        try:
            audio_chunk = sd.rec(int(0.1 * 44100), samplerate=44100, channels=1, dtype='int16')
            sd.wait()
            st.session_state.audio_data.append(audio_chunk)
        except Exception as e:
            st.error(f"録音中にエラーが発生しました: {str(e)}")
            st.session_state.recording = False

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
