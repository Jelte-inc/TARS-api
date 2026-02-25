import websocket
import soundfile as sf
import sounddevice as sd
import io

def on_message(ws, message):
    if isinstance(message, bytes):
        print("Ontvangen audio blob:", len(message), "bytes")

        # Lees WAV direct uit geheugen (niet eerst samenvoegen)
        with io.BytesIO(message) as wav_buffer:
            data, samplerate = sf.read(wav_buffer, dtype='float32')
            sd.play(data, samplerate=samplerate, blocking=True)

        print("Audio afgespeeld")

    elif isinstance(message, str) and message.lower() == "end":
        print("TTS volledig ontvangen\n")

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    # Stuur audiobestand naar server
    with open(r"C:\Users\0jrli\TARS-api\test.wav", "rb") as f:
        while chunk := f.read(4096):
            ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)

    ws.send("end")

ws = websocket.WebSocketApp(
    "ws://localhost:56277/ws",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

ws.run_forever()