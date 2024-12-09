# src/app.py
import streamlit as st
import os
from datetime import datetime
from config import AUDIO_DIR, MODEL_DIR, MODEL_NAME
from audio_recorder import AudioRecorder, save_audio, get_audio_duration, RealTimeAudioRecorder, RealTimeTranscriber
from transcription import load_whisper_model, transcribe_audio, save_transcription_to_file

MODEL_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True, parents=True)

def initialize_whisper():
    """Initialize Whisper model"""
    if 'whisper_model' not in st.session_state:
        with st.spinner(f'Loading Whisper "{MODEL_NAME}" model...'):
            st.session_state.whisper_model = load_whisper_model()

def initialize_session_state():
    """Initialize session state"""
    if 'audio_recorder' not in st.session_state:
        st.session_state.audio_recorder = AudioRecorder()
    if 'realtime_recorder' not in st.session_state:
        # Reduce chunk_duration for more frequent updates
        st.session_state.realtime_recorder = RealTimeAudioRecorder(chunk_duration=0.5)
    if 'realtime_transcriber' not in st.session_state:
        st.session_state.realtime_transcriber = RealTimeTranscriber(st.session_state.whisper_model)
    if 'realtime_text' not in st.session_state:
        st.session_state.realtime_text = ""

def update_transcription(audio_data):
    """Update real-time transcription"""
    if audio_data is not None:
        text = st.session_state.realtime_transcriber.transcribe_chunk(audio_data)
        if text:
            st.session_state.realtime_text = st.session_state.realtime_transcriber.get_full_text()
            # Here we can try forcing an update if needed:
            # st.experimental_rerun()

def main():
    st.title("Voice Recorder & Transcription")

    initialize_whisper()
    initialize_session_state()

    # Recording controls
    col1, col2, col3 = st.columns(3)

    with col1:
        if not st.session_state.audio_recorder.is_recording and not st.session_state.realtime_recorder.is_recording:
            if st.button("🎤 Start Recording"):
                st.session_state.audio_recorder.start_recording()
                # Removed st.rerun() to avoid resetting states

    with col2:
        if not st.session_state.audio_recorder.is_recording and not st.session_state.realtime_recorder.is_recording:
            if st.button("🎤 Start Real-time Transcription"):
                st.session_state.realtime_transcriber.clear()
                st.session_state.realtime_text = ""
                st.session_state.realtime_recorder.set_transcription_callback(update_transcription)
                st.session_state.realtime_recorder.start_recording()
                # Removed st.rerun() here as well

    with col3:
        if st.session_state.audio_recorder.is_recording or st.session_state.realtime_recorder.is_recording:
            if st.button("⏹ Stop Recording"):
                if st.session_state.audio_recorder.is_recording:
                    recorded_audio = st.session_state.audio_recorder.stop_recording()
                    if recorded_audio is not None:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = AUDIO_DIR / f"audio_{timestamp}.wav"
                        save_audio(recorded_audio, filename)
                        st.success(f"Recording saved: {filename}")
                if st.session_state.realtime_recorder.is_recording:
                    recorded_audio = st.session_state.realtime_recorder.stop_recording()
                    if recorded_audio is not None:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = AUDIO_DIR / f"audio_realtime_{timestamp}.wav"
                        save_audio(recorded_audio, filename)
                        save_transcription_to_file(filename, st.session_state.realtime_text)
                        st.success(f"Recording saved: {filename}")
                # st.rerun() can remain here to refresh after stopping if desired
                st.rerun()

    # Display recording status and real-time transcription
    if st.session_state.audio_recorder.is_recording:
        st.warning("Recording in progress...")
    elif st.session_state.realtime_recorder.is_recording:
        st.warning("Real-time transcription in progress...")
        st.text_area("Real-time Transcription", st.session_state.realtime_text,
                    height=150, key="realtime_output")

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
