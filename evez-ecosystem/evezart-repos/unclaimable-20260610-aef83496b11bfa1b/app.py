import base64
import os
from io import BytesIO
from tempfile import NamedTemporaryFile

import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import MusicgenForConditionalGeneration, MusicgenProcessor

app = FastAPI()
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="static", html=True), name="static")

class GenerateRequest(BaseModel):
    prompt: str
    duration: int = 30  # duration in seconds

# Load model globally (use CPU; change to 'cuda' if GPU is available)
processor = MusicgenProcessor.from_pretrained("facebook/musicgen-medium")
model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-medium")
model = model.to("cpu")

@app.post("/generate")
def generate(request: GenerateRequest):
    # Process text prompt
    inputs = processor(text=[request.prompt], padding=True, return_tensors="pt")
    # Estimate number of tokens based on duration and model's audio config
    # MusicGen's default sample rate is 24kHz and chunk length is 1024 samples per token
    # Approx tokens = duration * sample_rate / chunk_length
    sample_rate = model.config.audio_encoder.sr  # 24000
    chunk_len = model.config.audio_encoder.chunk_length  # 1024
    max_new_tokens = int(request.duration * sample_rate / chunk_len)
    # Generate audio waveform
    with torch.no_grad():
        audio = model.generate(**inputs, max_new_tokens=max_new_tokens)
    # audio shape: (batch, seq_len)
    audio = audio.squeeze().cpu().numpy()
    # Save audio to a temporary WAV file
    with NamedTemporaryFile(suffix=".wav", delete=False) as wav_file:
        sf.write(wav_file.name, audio, samplerate=sample_rate)
        wav_path = wav_file.name
    # Generate mel spectrogram image
    S = librosa.feature.melspectrogram(y=audio, sr=sample_rate, n_mels=128)
    S_dB = librosa.power_to_db(S, ref=np.max)
    fig, ax = plt.subplots(figsize=(8, 4))
    img = librosa.display.specshow(S_dB, sr=sample_rate, x_axis="time", y_axis="mel", ax=ax)
    ax.set(title="Mel Spectrogram")
    fig.colorbar(img, ax=ax, format="%+2.0f dB")
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    spectrogram_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    # Read audio file and encode as base64
    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    # Cleanup temporary wav file
    try:
        os.remove(wav_path)
    except Exception:
        pass
    return {"audio_base64": audio_b64, "spectrogram_base64": spectrogram_b64}
