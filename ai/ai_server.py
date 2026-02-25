from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import numpy as np
import soundfile as sf
import io
from TTS.api import TTS
from scipy.signal import resample, butter, lfilter
import whisper
import os
model = whisper.load_model("base")
print("READY")  # laat Go weten dat het model geladen is

# ---- Model laden ----
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", gpu=True)
tts.speaker = "p225"

# ---- FastAPI app ----
app = FastAPI(title="TARS TTS API")

# ---- Pydantic request model ----
class TTSRequest(BaseModel):
    sentence: str
class STTRequest(BaseModel):
    audio_path: str

# ---- Audio effect functies ----
def highpass_filter(wav, sr, cutoff=3000):
    b, a = butter(1, cutoff / (sr / 2), btype='high')
    return lfilter(b, a, wav)

def tars_effect(wav: np.ndarray, sr=22050) -> np.ndarray:
    wav = np.array(wav, dtype=np.float32)
    pitch_factor = 0.78
    wav = resample(wav, int(len(wav) / pitch_factor))
    speed_factor = 0.92
    wav = resample(wav, int(len(wav) * speed_factor))
    echo_strength = 0.18
    delay_samples = int(0.02 * sr)
    if len(wav) > delay_samples:
        wav[delay_samples:] += echo_strength * wav[:-delay_samples]
    wav = highpass_filter(wav, sr, cutoff=2500)
    wav = np.sign(wav) * (1 - np.exp(-np.abs(wav) * 3))
    wav *= 0.7
    wav = np.clip(wav, -1.0, 1.0)
    return wav

# ---- Endpoint ----
@app.post("/tts")
def tts_endpoint(request: TTSRequest):
    # Tekst omzetten naar spraak
    wav = tts.tts(request.sentence)
    sr = tts.synthesizer.output_sample_rate
    # TARS-effect toepassen
    wav = tars_effect(wav, sr)

    # Zet om naar in-memory WAV bestand
    buf = io.BytesIO()
    sf.write(buf, wav, sr, format="WAV")
    buf.seek(0)

    return StreamingResponse(buf, media_type="audio/wav")
@app.get("/stt")
def stt_endpoint():
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "received_audio.wav"))
    result = model.transcribe(file_path)
    return result["text"]