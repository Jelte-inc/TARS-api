import ollama
from commands.weather_forecast import weather_forecast
import datetime
from fastapi import WebSocket
import asyncio


# Functie om modeloutput te verwerken
def execute_model_output(model_output: str) -> str:
    return weather_forecast(model_output)    

async def ai(user_input:str, websocket:WebSocket):
    message_content = user_input
    if user_input == "bye bye":
      return
    message = {'role': 'user', 'content': message_content + str(datetime.datetime.today())}
    try:
        full_response = ""
        hoi = False
        i = 0
        for part in ollama.chat(model='tars', messages=[message], stream=True):
          if "@" in full_response:
             hoi = True
          elif len(full_response) > 1 and not hoi:
            if i == 0:
              await websocket.send_text(full_response)
              i += 1
            await websocket.send_text(part['message']['content'])
            await asyncio.sleep(0)
          full_response += part['message']['content']
        if hoi:
          await ai(execute_model_output(full_response), websocket)

             
    except Exception as e:
        print("Something went wrong:", e)
    print(full_response)