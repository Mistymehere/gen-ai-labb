import streamlit as st
from concurrent.futures import ThreadPoolExecutor
from functions.transcribe import transcribe_with_whisper_openai
from functions.split_audio import split_audio_to_chunks
from functions.styling import page_config, styling
import os
import tiktoken

# Initialization
if 'language' not in st.session_state:
    st.session_state['language'] = "Svenska"

page_config()
styling()

# Translations
translations = {
    "Svenska": {
        "title": "Transkribering",
        "instruction": "Ladda upp en ljudfil eller spela in direkt",
        "upload": "Ladda upp ljudfil",
        "record": "Spela in ljud",
        "transcribing": "Transkriberar...",
        "done": "Transkribering klar!",
    },
    "English": {
        "title": "Transcription",
        "instruction": "Upload an audio file or record directly",
        "upload": "Upload audio file",
        "record": "Record audio",
        "transcribing": "Transcribing...",
        "done": "Transcription complete!",
    }
}

lang = st.session_state['language']
t = translations[lang]

st.title(t["title"])
st.write(t["instruction"])

# File uploader and audio recorder in a single column
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader(t["upload"], type=["mp3", "wav", "flac", "mp4", "m4a", "aifc"], label_visibility="collapsed")
with col2:
    audio = st.experimental_audio_input(t["record"])

# Function to process audio (either uploaded or recorded)
def process_audio(audio_file):
    if "transcribed" not in st.session_state:
        with st.spinner(t["transcribing"]):
            chunk_paths = split_audio_to_chunks(audio_file)
            with ThreadPoolExecutor() as executor:
                transcriptions = list(executor.map(
                    lambda chunk: transcribe_with_whisper_openai(open(chunk, "rb"), os.path.basename(chunk)), 
                    chunk_paths
                ))
            st.session_state.transcribed = "\n".join(transcriptions)
        st.success(t["done"])
    
    st.subheader(t["title"])
    st.write(st.session_state.transcribed)

# Process the audio file (either uploaded or recorded)
if uploaded_file:
    process_audio(uploaded_file)
elif audio:
    process_audio(audio)

# Display token count if transcription is available
if "transcribed" in st.session_state:
    token_count = len(tiktoken.get_encoding("o200k_base").encode(st.session_state.transcribed))
    st.info(f"Antal tokens: {token_count}")
