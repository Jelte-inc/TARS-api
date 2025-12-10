import websocket
import io
import soundfile as sf
import sounddevice as sd


audio_buffer = bytearray()

def on_message(ws, message):
    global audio_buffer
    if isinstance(message, bytes):
        audio_buffer.extend(message)
    elif isinstance(message, str) and message.lower() == "end":
        print("Length of audio_buffer:", len(audio_buffer))
        if len(audio_buffer) == 0:
            print("Geen audio ontvangen!")
            return
        with open("debug.wav", "wb") as f:
            f.write(audio_buffer)
        import soundfile as sf
        import sounddevice as sd
        data, samplerate = sf.read("debug.wav", dtype='float32')
        sd.play(data, samplerate=samplerate, blocking=True)
        print("Audio volledig afgespeeld")
        audio_buffer = bytearray()  # reset voor volgende zin


def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    # Stuur audiobestand naar server
    with open(r"C:\Users\0jrli\Downloads\Record (online-voice-recorder.com) (1).mp3", "rb") as f:
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
