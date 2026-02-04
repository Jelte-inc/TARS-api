import asyncio
import websockets
import json
import ollama
from concurrent.futures import ThreadPoolExecutor

# Settings
# PI_URI = "ws://10.80.178.250:8765"
PI_URI = "ws://192.168.2.43:8765"
MODEL_NAME = "tars"

# Executer fixes error where the script will freeze and cause websocket problems
executor = ThreadPoolExecutor(max_workers=1)

# Inject prompt into ollama model
def call_ollama(prompt):
    return ollama.chat(
        model=MODEL_NAME,
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )

async def run_controller():
    print(f"Verbinden met TARS op {PI_URI}...")
    
    try:
        # ping_interval=None fixes issues with timeouts
        #TODO: check if this is an error in golang
        async with websockets.connect(PI_URI, ping_interval=None) as websocket:
            print("Connected! Tars is online.")
            
            loop = asyncio.get_running_loop()
            
            while True:
                prompt = await loop.run_in_executor(None, input, "\nCommando for TARS: ")
                
                if prompt.lower() in ['exit', 'quit']:
                    break

                print("TARS is thinking...")
                
                # Call ollama without blocking the websocket
                try:
                    response = await loop.run_in_executor(executor, call_ollama, prompt)
                    raw_json = response['message']['content']
                    
                    # Validate json and send through websocket
                    valid_data = json.loads(raw_json)
                    await websocket.send(json.dumps(valid_data))
                    print(f"Send: {raw_json}")
                    
                except Exception as e:
                    print(f"Error while running Ollama: {e}")

    except Exception as e:
        print(f"Connection closed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_controller())
    except KeyboardInterrupt:
        print("\nClosed by user.")