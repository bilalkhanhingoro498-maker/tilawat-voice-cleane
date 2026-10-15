# Tilawat Voice Cleaner (Streamlit)

## What it does
- Upload an audio file
- One-click noise reduction / speech enhancement using DeepFilterNet
- Listen to the original and processed audio
- Download the processed audio as WAV or MP3

## Run locally
Python 3.10 or 3.11 is a sensible starting point for ML package compatibility.

1. Install FFmpeg on your computer (needed by pydub for MP3/M4A conversion).
2. In a terminal in this folder, run:
   ```bash
   python -m venv .venv
   ```
   Activate the environment, then:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

## Notes
- The first processing run downloads/loads the enhancement model and may take time.
- This is enhancement, not voice conversion; it does not intentionally replace the speaker's voice.
- Noise reduction can still affect subtle recitation details. Always listen carefully to tajweed, makharij, and madd before publishing.
- For a first test, use a short 10–20 second recording.
- For deployment, a Linux host with enough RAM and FFmpeg is recommended. Cloud free tiers may run out of memory or time on long audio.
