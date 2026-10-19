# Tilawat Voice Cleaner v2

This version removes `pydub` and `deepfilternet`; it uses FFmpeg directly for decoding and MP3 conversion, and `noisereduce` for conservative noise reduction.

Upload all files at the root of the GitHub repository and set `app.py` as the Streamlit main file. Check the Python version in Streamlit Cloud app settings; use Python 3.11 if available.

Always listen carefully to the result for any effect on tajweed, makharij, or madd.
