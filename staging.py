import logging

def safe_get(data: dict, *keys, default=None):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data   
        
def is_valid(*data) -> bool:
    for datum in data:
        if isinstance(datum, str):
            if(datum == ""):
                return False
        if isinstance(datum, int):
            if(datum is None):
                return False
        if isinstance(datum, dict):
            if(datum == {}):
                return False
        if datum is None:
            return False    
        
    return True

def transform_load(conn, log: logging.Logger) -> tuple[int, int]:
    cursor = conn.cursor();
    
    cursor.execute("SELECT id, city, observed_at, payload FROM raw.weather_raw");
    rows = cursor.fetchall();
    
    rows_inserted = 0
    rows_skipped = 0
    
    for row in rows:
        raw_id = row[0]
        payload = row[3]
        
        city = safe_get(payload, "name")
        observed_at = row[2]
        temp_raw = safe_get(payload, "main", "temp")
        humidity = safe_get(payload, "main", "humidity")
        weather_main = payload.get("weather", [{}])[0].get("main")
        weather_description = payload.get("weather", [{}])[0].get("description")
        wind_speed = safe_get(payload, "wind", "speed")
        
        if city is None or observed_at is None or temp_raw is None or humidity is None or weather_main is None or weather_description is None or wind_speed is None:
            log.warning(f"Skipping current weather raw.id={raw_id}: Missing required field - city={city}, observed_at={observed_at}")
            rows_skipped += 1
            continue
        
        temp_celsius = temp_raw - 273.15
        
        if temp_celsius < -90 or temp_celsius > 60:
            log.warning(f"Skipping current weather staging raw.id={raw_id}: Temp range is not valid - city={city}, temp={temp_celsius}")
            rows_skipped += 1
            continue        
        
        
        cursor.execute("""
                       INSERT INTO staging.weather (city, observed_at, temp_celsius, humidity, weather_main, weather_description, wind_speed) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (city, observed_at) DO NOTHING
                       """, (city, observed_at, temp_celsius, humidity, weather_main, weather_description, wind_speed))
        
        inserted = cursor.rowcount
        skipped = 1 - inserted
        
        rows_inserted += inserted
        rows_skipped += skipped
        
    conn.commit()
        
    return (rows_inserted, rows_skipped)
        
def transform_load_forecast(conn, log: logging.Logger) -> tuple[int, int]:
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, city, forecast_for, payload FROM raw.forecast_raw")
    rows = cursor.fetchall()
    
    rows_inserted = 0
    rows_skipped = 0
    
    for row in rows:
        raw_id = row[0]
        city = row[1]
        forecast_for = row[2]
        
        payload = row[3]
        
        temp_raw = safe_get(payload, "main", "temp")
        humidity = safe_get(payload, "main", "humidity")
        weather_main = payload.get("weather", [{}])[0].get("main")
        weather_description = payload.get("weather", [{}])[0].get("description")
        wind_speed = safe_get(payload, "wind", "speed")
        
        if(is_valid(city, forecast_for, temp_raw, humidity, weather_main, weather_description, wind_speed) == False):
            log.warning(f"Skipping forecast weather staging raw.id = {raw_id}")
            rows_skipped += 1
            continue
        
        temp_celsius = temp_raw - 273.15
        
        if temp_celsius < -90 or temp_celsius > 60:
            log.warning(f"Skipping forecast weather staging raw.id={raw_id}: Temp range is not valid - city={city}, temp={temp_celsius}")
            rows_skipped += 1
            continue       
        
        cursor.execute("""
                       INSERT INTO staging.forecast 
                       (city, forecast_for, temp_celsius, humidity, weather_main, weather_description, wind_speed)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (city, forecast_for) DO UPDATE
                        SET temp_celsius = EXCLUDED.temp_celsius,
                        humidity = EXCLUDED.humidity,
                        weather_main = EXCLUDED.weather_main,
                        weather_description = EXCLUDED.weather_description,
                        wind_speed = EXCLUDED.wind_speed,
                        loaded_at = NOW()
                       """, (city, forecast_for, temp_celsius, humidity, weather_main, weather_description, wind_speed))
        
        inserted = cursor.rowcount
        skipped = 1 - inserted
        
        rows_inserted += inserted
        rows_skipped += skipped 
        
    conn.commit()
    
    return (rows_inserted, rows_skipped)