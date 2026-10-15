import io
import os
import tempfile
from pathlib import Path

import streamlit as st
from pydub import AudioSegment
from df.enhance import enhance, init_df, load_audio, save_audio

st.set_page_config(
    page_title="Tilawat Voice Cleaner",
    page_icon="🎙️",
    layout="centered",
)

st.title("🎙️ Tilawat Voice Cleaner")
st.write("Apni tilawat upload karein, ek click mein clean karein, phir sunein aur download karein.")
st.info(
    "Yeh app noise kam karne aur awaaz ko saaf karne ki koshish karti hai. "
    "Aapki awaaz convert nahi hoti, lekin har recording par result mukhtalif ho sakta hai. "
    "Download se pehle tajweed, makharij aur madd zaroor sun kar check karein."
)

@st.cache_resource(show_spinner="Audio enhancement model load ho raha hai...")
def get_model():
    model, df_state, _ = init_df()
    return model, df_state

def to_wav_bytes(uploaded_file):
    audio = AudioSegment.from_file(uploaded_file)
    # Mono is suitable for this enhancement model; keep the original sample rate conversion safe.
    audio = audio.set_channels(1).set_frame_rate(48000)
    buffer = io.BytesIO()
    audio.export(buffer, format="wav")
    buffer.seek(0)
    return buffer.getvalue()

def enhance_audio(wav_bytes):
    with tempfile.TemporaryDirectory() as tmp:
        input_path = os.path.join(tmp, "input.wav")
        output_path = os.path.join(tmp, "enhanced.wav")
        with open(input_path, "wb") as f:
            f.write(wav_bytes)

        model, df_state = get_model()
        audio, _ = load_audio(input_path, sr=df_state.sr())
        cleaned = enhance(model, df_state, audio)
        save_audio(output_path, cleaned, df_state.sr())

        with open(output_path, "rb") as f:
            return f.read()

def wav_to_mp3_bytes(wav_bytes):
    audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
    buffer = io.BytesIO()
    audio.export(buffer, format="mp3", bitrate="192k")
    buffer.seek(0)
    return buffer.getvalue()

uploaded = st.file_uploader(
    "Apni tilawat ki audio upload karein",
    type=["wav", "mp3", "m4a", "ogg", "flac"],
    help="Behtar result ke liye saaf recording karein aur clipping se bachein.",
)

if uploaded:
    st.subheader("Original tilawat")
    st.audio(uploaded)

    if st.button("✨ Clean My Tilawat", type="primary", use_container_width=True):
        try:
            with st.spinner("Tilawat clean ho rahi hai. File ke size ke mutabiq kuch waqt lag sakta hai..."):
                original_wav = to_wav_bytes(uploaded)
                cleaned_wav = enhance_audio(original_wav)
                cleaned_mp3 = wav_to_mp3_bytes(cleaned_wav)
                st.session_state["cleaned_wav"] = cleaned_wav
                st.session_state["cleaned_mp3"] = cleaned_mp3
                st.session_state["cleaned_name"] = Path(uploaded.name).stem
            st.success("Audio tayyar hai! Ab sunein aur download karein.")
        except Exception as e:
            st.error("Audio process nahi ho saki. WAV ya MP3 file ke saath dobara try karein.")
            st.caption("Technical detail: " + str(e))

if "cleaned_wav" in st.session_state:
    st.subheader("Saaf ki hui tilawat")
    st.audio(st.session_state["cleaned_wav"], format="audio/wav")
    left, right = st.columns(2)
    with left:
        st.download_button(
            "⬇️ Download WAV",
            data=st.session_state["cleaned_wav"],
            file_name=f"{st.session_state['cleaned_name']}_cleaned.wav",
            mime="audio/wav",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "⬇️ Download MP3",
            data=st.session_state["cleaned_mp3"],
            file_name=f"{st.session_state['cleaned_name']}_cleaned.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

st.divider()
st.caption("Tip: Original aur cleaned audio ko headphones par compare karein. Agar koi harf, madd ya tajweed badli hui lage, original recording use karein ya kam processing wali recording banayein.")
