# src/app.py
import streamlit as st
import os
from datetime import datetime
from config import AUDIO_DIR, MODEL_DIR, MODEL_NAME, SAMPLE_RATE, CHANNELS
from audio_recorder import AudioRecorder, save_audio, get_audio_duration
from transcription import load_whisper_model, transcribe_audio, save_transcription_to_file
import time
import threading
from audio_processor import BufferedAudioProcessor

# Directory initialization
MODEL_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True, parents=True)

def initialize_whisper():
    """Initialize Whisper model"""
    if 'whisper_model' not in st.session_state:
        with st.spinner(f'Loading Whisper "{MODEL_NAME}" model...'):
            st.session_state.whisper_model = load_whisper_model()

def initialize_session_state():
    """Initialize session state with improved real-time processing"""
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()
    if 'buffered_processor' not in st.session_state:
        st.session_state.buffered_processor = BufferedAudioProcessor(
            model=st.session_state.whisper_model,
            sample_rate=SAMPLE_RATE,
            channels=CHANNELS,
            max_queue_size=10  # バッファサイズの制限を追加
        )
    if 'realtime_text' not in st.session_state:
        st.session_state.realtime_text = []
    if 'is_transcribing' not in st.session_state:
        st.session_state.is_transcribing = False
    if 'transcription_placeholder' not in st.session_state:
        st.session_state.transcription_placeholder = None
    if 'update_thread' not in st.session_state:
        st.session_state.update_thread = None

def clean_up_resources():
    """Clean up resources when stopping recording"""
    if st.session_state.is_transcribing:
        st.session_state.is_transcribing = False
        if st.session_state.buffered_processor:
            st.session_state.buffered_processor.stop()
        if st.session_state.update_thread and st.session_state.update_thread.is_alive():
            st.session_state.update_thread.join(timeout=2.0)
        st.session_state.update_thread = None

def update_transcription():
    """Update transcription text in the UI"""
    try:
        while st.session_state.is_transcribing:
            new_text = st.session_state.buffered_processor.get_text()
            if new_text:
                st.session_state.realtime_text.append(new_text)
                # 現在のテキストを更新
                current_text = " ".join(st.session_state.realtime_text)
                if st.session_state.transcription_placeholder is not None:
                    st.session_state.transcription_placeholder.text_area(
                        "Real-time Transcription",
                        current_text,
                        height=150,
                        key=f"realtime_output_{time.time()}"  # ユニークなキーを生成
                    )
            time.sleep(0.1)
    except Exception as e:
        print(f"Error in update_transcription: {e}")
        st.session_state.is_transcribing = False

def main():
    st.title("Voice Recorder & Transcription")

    initialize_whisper()
    initialize_session_state()

    # Recording controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if not st.session_state.audio_recorder.is_recording and not st.session_state.is_transcribing:
            if st.button("🎤 Start Recording"):
                st.session_state.audio_recorder.start_recording()
                st.rerun()

    with col2:
        if not st.session_state.audio_recorder.is_recording and not st.session_state.is_transcribing:
            if st.button("🎤 Start Real-time Transcription"):
                clean_up_resources()  # 既存のリソースをクリーンアップ
                st.session_state.realtime_text = []
                st.session_state.is_transcribing = True
                st.session_state.buffered_processor.start()
                st.session_state.update_thread = threading.Thread(
                    target=update_transcription,
                    daemon=True
                )
                st.session_state.update_thread.start()
                st.rerun()

    with col3:
        if st.session_state.audio_recorder.is_recording or st.session_state.is_transcribing:
            if st.button("⏹ Stop Recording"):
                if st.session_state.audio_recorder.is_recording:
                    recorded_audio = st.session_state.audio_recorder.stop_recording()
                    if recorded_audio is not None:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = AUDIO_DIR / f"audio_{timestamp}.wav"
                        save_audio(recorded_audio, filename)
                        st.success(f"Recording saved: {filename}")
                if st.session_state.is_transcribing:
                    clean_up_resources()
                    # Save the transcription
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = AUDIO_DIR / f"audio_realtime_{timestamp}.wav"
                    transcription_text = " ".join(st.session_state.realtime_text)
                    save_transcription_to_file(filename, transcription_text)
                    st.success(f"Transcription saved: {filename}")
                st.rerun()

    # Display recording status and real-time transcription
    if st.session_state.audio_recorder.is_recording:
        st.warning("Recording in progress...")
    elif st.session_state.is_transcribing:
        st.warning("Real-time transcription in progress...")

        # Create a placeholder for real-time updates
        st.session_state.transcription_placeholder = st.empty()

        # Display current transcription
        current_text = " ".join(st.session_state.realtime_text)
        st.session_state.transcription_placeholder.text_area(
            "Real-time Transcription",
            current_text,
            height=150,
            key="realtime_output"
        )

    # Display recorded files
    st.subheader("Recorded Files")
    audio_files = [f for f in os.listdir(AUDIO_DIR) if f.endswith('.wav')]

    if 'transcription_states' not in st.session_state:
        st.session_state.transcription_states = {}

    if audio_files:
        for audio_file in sorted(audio_files, reverse=True):
            if audio_file.startswith('temp_chunk_'):  # Skip temporary chunk files
                continue
            file_path = AUDIO_DIR / audio_file
            txt_file_path = file_path.with_suffix(".txt")
            duration = get_audio_duration(file_path)

            with st.container():
                col_audio, col_controls, col_text = st.columns([4, 2, 6])

                with col_audio:
                    st.markdown(f"##### {audio_file} ({duration}s)")
                    with open(file_path, 'rb') as audio_file_open:
                        st.audio(audio_file_open.read(), format='audio/wav')

                with col_controls:
                    st.markdown(" ")
                    col_del, col_trans = st.columns(2)
                    with col_del:
                        if st.button("🗑️", key=f"delete_{audio_file}",
                                    help="Delete this recording"):
                            os.remove(file_path)
                            if txt_file_path.exists():
                                os.remove(txt_file_path)
                            if audio_file in st.session_state.transcription_states:
                                del st.session_state.transcription_states[audio_file]
                            st.rerun()

                    with col_trans:
                        transcribe_button = st.button("📝", key=f"transcribe_{audio_file}",
                                                        help="Transcribe this recording")

                with col_text:
                    if transcribe_button:
                        st.session_state.transcription_states[audio_file] = "processing"
                        st.rerun()

                    if audio_file in st.session_state.transcription_states and st.session_state.transcription_states[audio_file] == "processing":
                        st.info("🔄 Transcribing...")
                        transcription = transcribe_audio(file_path, st.session_state.whisper_model)
                        if transcription:
                            save_transcription_to_file(file_path, transcription)
                            st.session_state.transcription_states[audio_file] = "completed"
                            st.rerun()
                        else:
                            st.session_state.transcription_states[audio_file] = "error"
                            st.error("❌ Transcription failed")
                            st.rerun()
                    elif txt_file_path.exists():
                        with open(txt_file_path, 'r', encoding='utf-8') as f:
                            transcription = f.read()
                            st.text_area("", transcription, height=100, key=f"text_{audio_file}",
                                        label_visibility="collapsed")
                    else:
                        st.text_area("", "📝 Click the transcribe button to start", height=100,
                                    key=f"placeholder_{audio_file}",
                                    label_visibility="collapsed",
                                    disabled=True)
    else:
        st.info("No recordings available yet")

if __name__ == "__main__":
    main()
