import requests
import json
from datetime import datetime
import config

cities = ["Jakarta", "Bekasi", "Surabaya", "Bandung"]

for city in cities:
    url=f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={config.API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    filename = f"sample_{city.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved: {filename}")