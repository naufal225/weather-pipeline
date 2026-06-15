from datetime import datetime, timezone
import json

def load(conn, raw_json: dict) -> tuple[int,int]:
    if not raw_json or "name" not in raw_json or "dt" not in raw_json:
        raise ValueError("Raw JSON kosong atau korup")
    
    city = raw_json["name"]
    observed_at = datetime.fromtimestamp(raw_json["dt"], tz=timezone.utc)
    payload = json.dumps(raw_json)
    
    cursor = conn.cursor()
    cursor.execute("""
                   INSERT INTO raw.weather_raw (city, observed_at, payload)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (city, observed_at) DO NOTHING
                   """, (city, observed_at, payload))
    
    rows_inserted = cursor.rowcount
    rows_skipped = 1 - rows_inserted
    
    conn.commit()
    
    return (rows_inserted, rows_skipped)