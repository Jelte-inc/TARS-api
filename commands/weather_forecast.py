import requests
import os
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


def weather_forecast(user_input:str):
    url = "http://api.weatherapi.com/v1/forecast.json"  
    load_dotenv()
    key = os.getenv("API_KEY")

    if key is None:
        print("Api key is missing")
    print(user_input)
    parts = user_input[1:].strip().split(maxsplit=1)
    if len(parts) == 2:
        days, location = parts
        print("Day:", days)
        print("Location:", location)
    params = {
        "key": key,
        "days": days,
        "q":location
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        temp = data['current']['temp_c']  
        precip = data['current']['precip_mm']  
        print(f"Temperature: {temp}°C")
        print(f"Rain: {precip} mm")
    else:
        print(f"Fout: {response.status_code}, {response.json().get('error', {}).get('message', 'Unknown error')}")
    return f"Temperature: {temp} Rain: {precip}"