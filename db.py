from datetime import datetime, timezone
import json
import logging

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

def load_forecast(conn, raw_json: dict, log: logging.Logger) -> tuple[int, int]:
    if "list" not in raw_json or "city" not in raw_json:
        raise ValueError("Unexpected forecast response structure")
    
    if len(raw_json["list"]) == 0:
        return (0,0)
    
    rows_inserted = 0
    rows_skipped = 0
    
    cursor = conn.cursor()
    city = raw_json.get("city", {}).get("name")
    
    for item in raw_json["list"]:
        forecast_for_raw = item.get("dt", None)
        
        if city is None or forecast_for_raw is None:
            log.warning("Skipped missing required field")
            rows_skipped += 1
            continue
        
        forecast_for = datetime.fromtimestamp(forecast_for_raw, tz=timezone.utc)
        payload = json.dumps(item)
        
        cursor.execute("""
                       INSERT INTO raw.forecast_raw (city, forecast_for, payload)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (city, forecast_for, ingested_at) DO NOTHING
                       """, (city, forecast_for, payload))
        
        inserted = cursor.rowcount
        skipped = 1 - inserted
        
        rows_inserted += inserted
        rows_skipped += skipped
        
    conn.commit()
    
    return (rows_inserted, rows_skipped)