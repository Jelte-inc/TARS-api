import asyncio
import websockets

async def handler(websocket):
    print("Pi connected")
    async for audio_chunk in websocket:
        print(f"Received {len(audio_chunk)} bytes")

async def main():
    # Luister op alle interfaces -> bereikbaar vanaf de Pi
    async with websockets.serve(handler, "0.0.0.0", 8000):
        print("Listening on ws://0.0.0.0:8000")
        await asyncio.Future()  # houdt de server draaiend

asyncio.run(main())
