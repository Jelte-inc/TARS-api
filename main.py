
from ai.ai_chat_model import ai
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio

app = FastAPI()

# Voorbeeld input-model
class InputData(BaseModel):
    name: str
    number: int

# Root endpoint (GET)
@app.get("/")
def get(message: str):
    return ai(message)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        ai(data, websocket)

        # Simuleer een antwoord dat per letter wordt gestuurd
        response = "Dit is een simulatie van het antwoord."

        for letter in response:
            await websocket.send_text(letter)
            await asyncio.sleep(0.1)  # delay per letter

        # Optioneel: sluiten of wachten op client disconnect
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=56277) 