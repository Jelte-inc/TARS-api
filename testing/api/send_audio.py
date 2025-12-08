import requests
import os

def file_stream(path, chunk_size=1024*64):
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data

url = "http://10.80.178.250:8000/upload-audio"
audio_file = "/home/jelte/Downloads/luvvoice.com-20251204-JJohNo.mp3"

# Zelf multipart bouwen is lastiger omdat requests anders alles buffert.
# Je kunt beter een raw streaming request gebruiken:
headers = {
    "Content-Type": "application/octet-stream",
    "X-Filename": os.path.basename(audio_file),
}

r = requests.post(url, data=file_stream(audio_file), headers=headers)

print(r.json())
