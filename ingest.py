import requests
import time
import logging

MAX_RETRIES = 3

def extract(city: str, api_key: str, log: logging.Logger) -> dict:
   for attempt in range(MAX_RETRIES):
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
            response = requests.get(url, timeout=10)

            if(response.status_code != 200):
                raise Exception(f"API_Error: {response.status_code} - {response.text}")

            data = response.json()

            return data
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as ex:
            if(attempt == MAX_RETRIES - 1):
                raise Exception(ex)
            
            wait = 2 ** (attempt + 1)
            
            log.warning(f"Attempt: {attempt}, try again after: {wait}s")
            
            time.sleep(wait)
