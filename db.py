from datetime import datetime, timezone
import json

def load(conn, raw_json: dict) -> None:
    city = raw_json["name"]
    observed_at = datetime.fromtimestamp(raw_json["dt"], tz=timezone.utc)
    payload = json.dumps(raw_json)
    
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO raw.weather_raw (city, observed_at, payload)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (city, observed_at) DO NOTHING
                   """, (city, observed_at, payload))
    
    conn.commit()