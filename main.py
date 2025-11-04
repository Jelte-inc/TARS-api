
from ai.ai_chat_model import ai
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # of specifiek: ["http://localhost"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        await ai(data, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=56277) 