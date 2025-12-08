import asyncio
import websockets
import struct
import os

# --- Configuratie ---
HOST = '0.0.0.0'  # Luister op alle beschikbare interfaces
PORT = 8765       # Moet overeenkomen met de poort in het client-script
OUTPUT_DIR = "ontvangen_frames" # Map om beelden op te slaan
# --- Einde Configuratie ---

async def image_receiver(websocket, path):
    """Verwerkt inkomende frames van de Raspberry Pi client."""
    print("Nieuwe client verbonden.")
    
    # Maak de uitvoermap aan als deze niet bestaat
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    frame_count = 0

    try:
        while True:
            # 1. Ontvang de lengte van het volgende frame (4 bytes)
            # De struct.unpack('<L', ...) verwacht 4 bytes
            try:
                # Wacht tot de 4-byte lengte-indicator is ontvangen
                length_bytes = await websocket.recv()
                
                # Controleer of we daadwerkelijk 4 bytes hebben ontvangen
                if len(length_bytes) != 4:
                    print(f"Verwacht 4 bytes voor lengte, maar kreeg {len(length_bytes)}. Verbreken.")
                    break
                    
            except websockets.exceptions.ConnectionClosedOK:
                print("Client heeft de verbinding netjes verbroken.")
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Verbinding gesloten door fout: {e}")
                break
                
            # Pak de binaire lengte uit (kleine endian 'L' = unsigned long)
            frame_length = struct.unpack('<L', length_bytes)[0]
            
            # Controleer op lege frames (kan gebeuren bij beëindiging)
            if frame_length == 0:
                continue

            # 2. Ontvang de daadwerkelijke framegegevens
            # We verwachten nu precies 'frame_length' bytes
            frame_data = await websocket.recv()
            
            if len(frame_data) != frame_length:
                print(f"Fout: Frame lengte komt niet overeen. Verwacht {frame_length}, kreeg {len(frame_data)}")
                continue

            # 3. Verwerk en opslaan van het frame
            frame_count += 1
            filename = os.path.join(OUTPUT_DIR, f"frame_{frame_count}.jpeg")
            
            # Schrijf de binaire gegevens naar een JPEG-bestand
            with open(filename, "wb") as f:
                f.write(frame_data)
                
            print(f"Frame {frame_count} ontvangen en opgeslagen als '{filename}'. Grootte: {frame_length} bytes.")

    except Exception as e:
        print(f"Er is een onverwachte fout opgetreden: {e}")
    finally:
        print("Client verbinding verbroken.")


# Start de server
async def main():
    print(f"Starten van de WebSocket server op ws://{HOST}:{PORT}")
    async with websockets.serve(image_receiver, HOST, PORT):
        # Blijf de server draaien
        await asyncio.Future() 

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer gestopt door gebruiker.")
    except Exception as e:
        print(f"Hoofdproces fout: {e}")