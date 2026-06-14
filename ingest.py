import requests

def extract(city: str, api_key: str) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)

    if(response.status_code != 200):
        raise Exception(f"API_Error: {response.status_code} - {response.text}")

    data = response.json()

    return data
