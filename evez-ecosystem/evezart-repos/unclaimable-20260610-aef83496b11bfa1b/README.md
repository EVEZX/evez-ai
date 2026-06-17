# Music Generation Service

This repository provides a simple **MusicGen** based service that can:

- Generate audio from a natural‑language prompt.
- Produce a mel‑spectrogram image of the generated audio.
- Serve a tiny web UI that works on any browser (including your Samsung Galaxy A16).

## Architecture

- **FastAPI** server (`app.py`) – loads the pretrained MusicGen model once and exposes a `/generate` endpoint.
- **Model** – uses the open‑source `facebook/musicgen-medium` checkpoint (requires ~4 GB VRAM for GPU, works on CPU albeit slower).
- **Audio processing** – `librosa` + `matplotlib` to create a spectrogram.
- **Web UI** – static `index.html` that sends a POST request to `/generate` and displays the audio player and spectrogram.

## Setup

1. **Install dependencies**
   ```bash
   cd music_gen_service
   python -m venv venv
   source venv/bin/activate  # on Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

2. **Run the server**
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   The service will be reachable at `http://localhost:8000` (or the host IP if you expose it).

3. **Access from your phone**
   - Ensure the machine running the server is reachable on your local network (e.g., both on same Wi‑Fi).
   - Open the address `http://<host‑ip>:8000` in the browser on your Samsung Galaxy A16.
   - Use the UI to type a prompt, set duration, and click **Generate**.

## API (usable by OpenClaw)

You can call the endpoint directly from the assistant using `exec` (curl) or any HTTP client:
```json
POST /generate
Content-Type: application/json
{
  "prompt": "A calm, relaxing ambient instrumental track",
  "duration": 30
}
```
The response contains two Base64 strings:
- `audio_base64` – a WAV audio file you can stream (`data:audio/wav;base64,...`).
- `spectrogram_base64` – a PNG image of the mel‑spectrogram.

## Docker (optional)

If you prefer containerised deployment, a simple Dockerfile is provided:
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```
Build and run:
```bash
docker build -t music-gen .
 docker run -p 8000:8000 music-gen
```

## Notes & Tips

- **Performance** – GPU dramatically speeds up generation. If you have a CUDA‑compatible GPU, change `model.to("cpu")` to `model.to("cuda")` in `app.py`.
- **Safety** – MusicGen is a general‑purpose model. Avoid prompting for copyrighted or disallowed content.
- **Customization** – You can swap the model checkpoint (`musicgen-small`, `musicgen-large`) by changing the names in the `processor` and `model` loading lines.
- **Mobile friendliness** – The UI uses only standard HTML/JS, so it works on any modern mobile browser without extra plugins.

---

Feel free to adapt the code, add authentication, or integrate it into larger workflows (e.g., OpenClaw can call the service, your phone can use the same endpoint).