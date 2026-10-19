import io
from pathlib import Path

import numpy as np
import noisereduce as nr
import soundfile as sf
import streamlit as st
from pydub import AudioSegment

st.set_page_config(page_title="Tilawat Voice Cleaner", page_icon="🎙️", layout="centered")
st.title("🎙️ Tilawat Voice Cleaner")
st.write("Upload karein, ek click mein awaaz saaf karein, phir sunein aur download karein.")
st.info(
    "Yeh version background noise ko kam karta hai aur volume ko balance karta hai. "
    "Aapki awaaz convert nahi hoti. Noise reduction tajweed, madd ya makharij ko bhi affect kar sakti hai, "
    "is liye publish karne se pehle audio zaroor sun kar check karein."
)

def decode_audio(uploaded_file):
    audio = AudioSegment.from_file(uploaded_file)
    audio = audio.set_channels(1).set_frame_rate(44100)
    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)
    samples, sample_rate = sf.read(wav_buffer, dtype="float32")
    if samples.ndim > 1:
        samples = np.mean(samples, axis=1)
    return samples, sample_rate

def clean_audio(samples, sample_rate):
    cleaned = nr.reduce_noise(
        y=samples,
        sr=sample_rate,
        stationary=False,
        prop_decrease=0.60,
        n_fft=1024,
    )
    peak = float(np.max(np.abs(cleaned))) if cleaned.size else 0.0
    if peak > 0:
        target_peak = 10 ** (-1.5 / 20)
        cleaned = cleaned * min(target_peak / peak, 4.0)
    cleaned = np.clip(cleaned, -0.999, 0.999)
    output = io.BytesIO()
    sf.write(output, cleaned, sample_rate, format="WAV", subtype="PCM_16")
    return output.getvalue()

def wav_to_mp3(wav_bytes):
    audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
    output = io.BytesIO()
    audio.export(output, format="mp3", bitrate="192k")
    output.seek(0)
    return output.getvalue()

uploaded = st.file_uploader("Apni tilawat ki audio upload karein", type=["wav", "mp3", "m4a", "ogg", "flac"])

if uploaded:
    st.subheader("Original tilawat")
    st.audio(uploaded)

    if st.button("✨ Clean My Tilawat", type="primary", use_container_width=True):
        try:
            with st.spinner("Audio clean ho rahi hai... file ke size ke mutabiq waqt lag sakta hai."):
                samples, sample_rate = decode_audio(uploaded)
                cleaned_wav = clean_audio(samples, sample_rate)
                cleaned_mp3 = wav_to_mp3(cleaned_wav)
                st.session_state["cleaned_wav"] = cleaned_wav
                st.session_state["cleaned_mp3"] = cleaned_mp3
                st.session_state["cleaned_name"] = Path(uploaded.name).stem
            st.success("Audio tayyar hai. Ab sunein aur download karein.")
        except Exception as exc:
            st.error("Audio process nahi ho saki. Chhoti WAV ya MP3 file se dobara try karein.")
            st.caption(f"Technical detail: {exc}")

if "cleaned_wav" in st.session_state:
    st.subheader("Saaf ki hui tilawat")
    st.audio(st.session_state["cleaned_wav"], format="audio/wav")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download WAV",
            data=st.session_state["cleaned_wav"],
            file_name=f"{st.session_state['cleaned_name']}_cleaned.wav",
            mime="audio/wav",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "⬇️ Download MP3",
            data=st.session_state["cleaned_mp3"],
            file_name=f"{st.session_state['cleaned_name']}_cleaned.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

st.divider()
st.caption("Tip: Pehle 10–20 second ki recording test karein. Agar koi harf, madd ya tajweed badli hui lage, original audio use karein.")
