import whisper
import sys



# Laad model één keer (GPU wordt automatisch gebruikt als beschikbaar)
model = whisper.load_model("base")
print("READY")  # laat Go weten dat het model geladen is
sys.stdout.flush()

# Blijf luisteren naar nieuwe bestandsnamen via stdin
for line in sys.stdin:
    file_path = line.strip()
    if file_path.lower() == "quit":  # stop signaal
        break
    try:
        result = model.transcribe(file_path)
        print(result["text"])
        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.stdout.flush()
