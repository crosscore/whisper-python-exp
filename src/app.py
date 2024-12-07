# app.py
import streamlit as st
import os
from datetime import datetime
from config import AUDIO_DIR, MODEL_DIR
from audio_recorder import AudioRecorder, save_audio, get_audio_duration
from transcription import load_whisper_model, transcribe_audio, save_transcription_to_file

MODEL_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

def initialize_whisper():
    """Whisperモデルの初期化"""
    if 'whisper_model' not in st.session_state:
        with st.spinner('Whisperモデルを読み込んでいます...'):
            st.session_state.whisper_model = load_whisper_model()

def main():
    st.title("音声認識・録音アプリ")

    initialize_whisper()

    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()

    # 録音コントロール用のカラム
    col1, col2 = st.columns(2)

    with col1:
        if not st.session_state.audio_recorder.is_recording:
            if st.button("🎤 録音開始"):
                st.session_state.audio_recorder.start_recording()
                st.rerun()

    with col2:
        if st.session_state.audio_recorder.is_recording:
            if st.button("⏹ 録音停止"):
                recorded_audio = st.session_state.audio_recorder.stop_recording()
                if recorded_audio is not None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = AUDIO_DIR / f"audio_{timestamp}.wav"
                    save_audio(recorded_audio, filename)
                    st.success(f"録音を保存しました: {filename}")
                st.rerun()

    if st.session_state.audio_recorder.is_recording:
        st.warning("録音中...")

    # 録音済みファイルの一覧表示
    st.subheader("録音済みファイル")
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]

    # 文字起こし処理の状態を保持
    if 'transcription_states' not in st.session_state:
        st.session_state.transcription_states = {}

    if audio_files:
        for audio_file in sorted(audio_files, reverse=True):
            file_path = AUDIO_DIR / audio_file
            txt_file_path = file_path.with_suffix(".txt")
            duration = get_audio_duration(file_path)

            # ファイルごとのコンテナを作成
            with st.container():
                # 3列レイアウト: オーディオ(4) | コントロール(2) | 文字起こし結果(6)
                col_audio, col_controls, col_text = st.columns([4, 2, 6])

                with col_audio:
                    st.markdown(f"##### {audio_file} ({duration}秒)")
                    with open(file_path, 'rb') as audio_file_open:
                        st.audio(audio_file_open.read(), format='audio/wav')

                with col_controls:
                    st.markdown("&nbsp;")  # スペーサー
                    col_del, col_trans = st.columns(2)
                    with col_del:
                        if st.button("🗑️", key=f"delete_{audio_file}"):
                            os.remove(file_path)
                            if txt_file_path.exists():
                                os.remove(txt_file_path)
                            if audio_file in st.session_state.transcription_states:
                                del st.session_state.transcription_states[audio_file]
                            st.rerun()

                    with col_trans:
                        transcribe_button = st.button("📝", key=f"transcribe_{audio_file}")

                with col_text:
                    # 文字起こし状態の管理と表示
                    if transcribe_button:
                        st.session_state.transcription_states[audio_file] = "processing"
                        st.rerun()

                    if audio_file in st.session_state.transcription_states and st.session_state.transcription_states[audio_file] == "processing":
                        # 文字起こし処理中の表示
                        st.info("🔄 文字起こし中...")
                        transcription = transcribe_audio(file_path, st.session_state.whisper_model)
                        if transcription:
                            save_transcription_to_file(file_path, transcription)
                            st.session_state.transcription_states[audio_file] = "completed"
                            st.rerun()
                        else:
                            st.session_state.transcription_states[audio_file] = "error"
                            st.error("❌ 文字起こしに失敗しました")
                            st.rerun()
                    elif txt_file_path.exists():
                        # 文字起こし結果の表示
                        with open(txt_file_path, 'r', encoding='utf-8') as f:
                            transcription = f.read()
                            st.text_area("", transcription, height=100, key=f"text_{audio_file}",
                                        label_visibility="collapsed")
                    else:
                        # 未処理の状態表示
                        st.text_area("", "📝 文字起こしボタンを押して処理を開始", height=100,
                                    key=f"placeholder_{audio_file}", label_visibility="collapsed",
                                    disabled=True)
    else:
        st.info("録音ファイルはまだありません")

if __name__ == "__main__":
    main()
