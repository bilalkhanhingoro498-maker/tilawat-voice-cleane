import io
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import noisereduce as nr
import soundfile as sf
import streamlit as st
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Tilawat Voice Cleaner", page_icon="🎙️", layout="centered")
st.title("🎙️ Tilawat Voice Cleaner")
st.write("Microphone se seedha tilawat record karein ya audio upload karein, phir clean karke download karein.")
st.info(
    "Yeh app background noise kam karti hai aur volume ko halka sa balance karti hai. "
    "Aapki awaaz convert nahi hoti. Processing se tajweed, madd ya makharij mutasir ho sakte hain; "
    "is liye final audio zaroor sun kar check karein."
)

SUPPORTED = ["wav", "mp3", "m4a", "ogg", "flac"]

def decode_audio(data: bytes, suffix: str):
    # Use FFmpeg directly rather than pydub/audioop.
    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / f"input.{suffix}"
        output_path = Path(tmp) / "decoded.wav"
        input_path.write_bytes(data)
        cmd = [
            "ffmpeg", "-nostdin", "-y", "-i", str(input_path),
            "-vn", "-ac", "1", "-ar", "44100", "-f", "wav", str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not output_path.exists():
            raise RuntimeError("FFmpeg audio decode failed: " + result.stderr[-1200:])
        samples, sr = sf.read(output_path, dtype="float32")
        if samples.ndim > 1:
            samples = np.mean(samples, axis=1)
        return samples, sr

def clean_audio(samples, sample_rate):
    cleaned = nr.reduce_noise(
        y=samples,
        sr=sample_rate,
        stationary=False,
        prop_decrease=0.55,
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
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "cleaned.wav"
        mp3_path = Path(tmp) / "cleaned.mp3"
        wav_path.write_bytes(wav_bytes)
        result = subprocess.run([
            "ffmpeg", "-nostdin", "-y", "-i", str(wav_path),
            "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_path)
        ], capture_output=True, text=True)
        if result.returncode != 0 or not mp3_path.exists():
            raise RuntimeError("MP3 conversion failed: " + result.stderr[-1200:])
        return mp3_path.read_bytes()

st.subheader("🎙️ Online recording")
st.caption("Start Recording dabayein, microphone permission allow karein, phir Stop Recording dabayein.")
recorded = mic_recorder(
    start_prompt="🔴 Start Recording",
    stop_prompt="⏹️ Stop Recording",
    just_once=True,
    use_container_width=True,
    key="tilawat_recorder",
)

if recorded and recorded.get("bytes"):
    st.session_state["source_audio"] = recorded["bytes"]
    st.session_state["source_name"] = "recorded_tilawat"
    st.session_state["source_suffix"] = "wav"

if "source_audio" in st.session_state:
    st.success("Recording/audio ready hai.")
    st.audio(st.session_state["source_audio"], format="audio/wav")
    if st.button("🗑️ Remove recording / choose another", use_container_width=True):
        for key in ("source_audio", "source_name", "source_suffix", "cleaned_wav", "cleaned_mp3", "cleaned_name"):
            st.session_state.pop(key, None)
        st.rerun()

st.markdown("**Ya apni pehle se mojood audio upload karein**")
uploaded = st.file_uploader("Audio file upload karein", type=SUPPORTED)
if uploaded:
    st.session_state["source_audio"] = uploaded.getvalue()
    st.session_state["source_name"] = Path(uploaded.name).stem
    st.session_state["source_suffix"] = Path(uploaded.name).suffix.lower().lstrip(".")
    st.audio(uploaded.getvalue())

if "source_audio" in st.session_state:
    if st.button("✨ Clean My Tilawat", type="primary", use_container_width=True):
        try:
            with st.spinner("Audio clean ho rahi hai..."):
                data = st.session_state["source_audio"]
                suffix = st.session_state.get("source_suffix", "wav")
                samples, sr = decode_audio(data, suffix)
                cleaned_wav = clean_audio(samples, sr)
                cleaned_mp3 = wav_to_mp3(cleaned_wav)
                st.session_state["cleaned_wav"] = cleaned_wav
                st.session_state["cleaned_mp3"] = cleaned_mp3
                st.session_state["cleaned_name"] = st.session_state.get("source_name", "tilawat")
            st.success("Audio tayyar hai! Sunein aur download karein.")
        except Exception as exc:
            st.error("Audio process nahi ho saki.")
            st.code(str(exc))

if "cleaned_wav" in st.session_state:
    st.subheader("Saaf ki hui tilawat")
    st.audio(st.session_state["cleaned_wav"], format="audio/wav")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Download WAV",
            st.session_state["cleaned_wav"],
            file_name=f"{st.session_state['cleaned_name']}_cleaned.wav",
            mime="audio/wav",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Download MP3",
            st.session_state["cleaned_mp3"],
            file_name=f"{st.session_state['cleaned_name']}_cleaned.mp3",
            mime="audio/mpeg",
            use_container_width=True,
        )

st.divider()
st.caption("Pehle 10–20 second ki recording test karein. Agar makharij, madd ya tajweed badli hui lage, original recording use karein.")
