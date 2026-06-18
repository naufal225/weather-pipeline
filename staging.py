import psycopg2

def transform_load(conn) -> tuple[int, int]:
    cursor = conn.cursor();
    
    cursor.execute("SELECT * FROM raw.weather_raw");
    rows = cursor.fetchall();
    
    rows_inserted = 0
    rows_skipped = 0
    
    for row in rows:
        payload = row[3]
        
        city = payload["name"]
        observed_at = row[2]
        temp_celsius = payload["main"]["temp"] - 273.15
        humidity = payload["main"]["humidity"]
        weather_main = payload["weather"][0]["main"]
        weather_description = payload["weather"][0]["description"]
        wind_speed = payload["wind"]["speed"]
        
        cursor.execute("""
                       INSERT INTO staging.weather (city, observed_at, temp_celsius, humidity, weather_main, weather_description, wind_speed) 
                       VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (city, observed_at) DO NOTHING
                       """, (city, observed_at, temp_celsius, humidity, weather_main, weather_description, wind_speed))
        
        inserted = cursor.rowcount
        skipped = 1 - inserted
        
        rows_inserted += inserted
        rows_skipped += skipped
        
    return (rows_inserted, rows_skipped)
        
        
        
        