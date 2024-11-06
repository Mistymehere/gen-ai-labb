import os
import hashlib
import hmac
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
import openai

from functions.transcribe import transcribe_with_whisper_openai
from functions.split_audio import split_audio_to_chunks
from functions.menu import menu  # Assuming this function is defined elsewhere

### Custom CSS for Styling
def custom_css():
    st.markdown("""
        <style>
            .main-title { 
                font-size: 32px;
                color: #4a4a4a;
                font-weight: bold;
            }
            .sub-title { 
                font-size: 20px; 
                color: #4a4a4a; 
                margin-bottom: 10px;
            }
            .sidebar .sidebar-content { 
                background-color: #f5f5f5; 
                padding: 20px; 
                border-radius: 10px; 
            }
            .css-1aumxhk {
                padding-top: 0;
                padding-bottom: 0;
            }
            .uploaded-file, .recorded-audio {
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                padding: 10px;
                background-color: #f1f1f1;
                width: 100%;
                height: 250px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
        </style>
    """, unsafe_allow_html=True)
custom_css()

### Sidebar with Menu
st.sidebar.title("Settings")
st.sidebar.markdown("🔊 **Audio Options**")
st.sidebar.markdown("📝 **Transcription Settings**")
st.sidebar.markdown("🌐 **Language**")
menu()  # Assuming this sets up additional menu elements

### Authentication (Password Check)
if st.secrets.pwd_on == "true":

    def check_password():
        passwd = st.secrets["password"]
        
        def password_entered():
            if hmac.compare_digest(st.session_state["password"], passwd):
                st.session_state["password_correct"] = True
                del st.session_state["password"]  # Don't store the password.
            else:
                st.session_state["password_correct"] = False

        if st.session_state.get("password_correct", False):
            return True

        st.text_input("Lösenord", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("😕 Ooops. Fel lösenord.")
        return False

    if not check_password():
        st.stop()

### Translation
if 'language' not in st.session_state:
    st.session_state['language'] = "Svenska"  # Default language

if st.session_state['language'] == "Svenska":
    page_name = "Transkribering"
    upload_text = "Ladda upp"
    rec_text = "Spela in"
    record_text = "Klicka på mikrofonikonen för att spela in"
    splitting_audio_text = "Delar upp ljudfilen i mindre bitar..."
    transcribing_text = "Transkriberar alla ljudbitar. Det här kan ta ett tag beroende på hur lång inspelningen är..."
    transcription_done_text = "Transkribering klar!"
    record_stop = "Stoppa inspelning"
    choose_file_text = "Välj en fil"
    max_size_help = "Max 10GB"
    main_title_text = "Transkriberingstjänst"
    sub_title_text = "Ladda upp eller spela in ljud"
elif st.session_state['language'] == "English":
    page_name = "Transcribe"
    upload_text = "Upload"
    rec_text = "Record"
    record_text = "Click on the microphone icon to record"
    splitting_audio_text = "Splitting the audio file into smaller pieces..."
    transcribing_text = "Transcribing all audio pieces. This may take a while depending on how long the recording is..."
    transcription_done_text = "Transcription done!"
    record_stop = "Stop recording"
    choose_file_text = "Choose a file"
    max_size_help = "Max 10GB"
    main_title_text = "Transcription Service"
    sub_title_text = "Upload or Record Audio"
else:
    # Default to English if language not recognized
    page_name = "Transcribe"
    upload_text = "Upload"
    rec_text = "Record"
    record_text = "Click on the microphone icon to record"
    splitting_audio_text = "Splitting the audio file into smaller pieces..."
    transcribing_text = "Transcribing all audio pieces. This may take a while depending on how long the recording is..."
    transcription_done_text = "Transcription done!"
    record_stop = "Stop recording"
    choose_file_text = "Choose a file"
    max_size_help = "Max 10GB"
    main_title_text = "Transcription Service"
    sub_title_text = "Upload or Record Audio"

# Setting up storage directories
os.makedirs("data/audio", exist_ok=True)  # Audio files for transcription
os.makedirs("data/audio_chunks", exist_ok=True)  # Audio chunks
os.makedirs("data/text", exist_ok=True)  # Transcribed documents

### Main Layout
st.markdown(f"<div class='main-title'>{main_title_text}</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>{sub_title_text}</div>", unsafe_allow_html=True)

# Adjust column widths: make the second column wider
col1, col2 = st.columns([1, 2])  # Second column is larger

# File Upload Section
with col1:
    st.markdown(f"### {upload_text}")
    with st.container():
        st.markdown(f"<div class='uploaded-file'>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            choose_file_text,
            type=["mp3", "wav", "flac", "mp4", "m4a", "aifc"],
            help=max_size_help
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file:
        current_file_hash = hashlib.md5(uploaded_file.read()).hexdigest()
        uploaded_file.seek(0)  # Reset the file pointer

        if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
            st.session_state.file_hash = current_file_hash
            if "transcribed" in st.session_state:
                del st.session_state.transcribed

        if "transcribed" not in st.session_state:
            with st.spinner(splitting_audio_text):
                chunk_paths = split_audio_to_chunks(uploaded_file)

            with st.spinner(transcribing_text):
                with ThreadPoolExecutor() as executor:
                    transcriptions = list(executor.map(
                        lambda chunk: transcribe_with_whisper_openai(open(chunk, "rb"), os.path.basename(chunk)), 
                        chunk_paths
                    ))

            st.session_state.transcribed = "\n".join(transcriptions)
            st.success(transcription_done_text)

# Audio Recorder Section
with col2:
    st.markdown(f"### {rec_text}")
    with st.container():
        st.markdown(f"<div class='recorded-audio'>", unsafe_allow_html=True)
        audio = st.experimental_audio_input(record_text)
        st.markdown("</div>", unsafe_allow_html=True)
    
    if audio:
        current_file_hash = hashlib.md5(audio.read()).hexdigest()
        audio.seek(0)

        if "file_hash" not in st.session_state or st.session_state.file_hash != current_file_hash:
            st.session_state.file_hash = current_file_hash
            if "transcribed" in st.session_state:
                del st.session_state.transcribed

        if "transcribed" not in st.session_state:
            with st.spinner(splitting_audio_text):
                chunk_paths = split_audio_to_chunks(audio)

            with st.spinner(transcribing_text):
                with ThreadPoolExecutor() as executor:
                    transcriptions = list(executor.map(
                        lambda chunk: transcribe_with_whisper_openai(open(chunk, "rb"), os.path.basename(chunk)), 
                        chunk_paths
                    ))

            st.session_state.transcribed = "\n".join(transcriptions)
            st.success(transcription_done_text)

# Display Transcription
if "transcribed" in st.session_state:
    st.markdown(f"#### {page_name}")
    st.markdown(st.session_state.transcribed)

### Footer
def add_footer():
    st.markdown("""
        <style>
            footer {visibility: hidden;}
            .footer {
                position: fixed;
                bottom: 0;
                width: 100%;
                color: #4a4a4a;
                text-align: center;
                padding: 10px;
                font-size: 12px;
            }
        </style>
        <div class="footer">
            Developed by Mistymehere | Powered by OpenAI Whisper API
        </div>
    """, unsafe_allow_html=True)

add_footer()
