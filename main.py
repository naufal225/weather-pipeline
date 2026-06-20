import config
from ingest import extract, extract_forecast
from db import load, load_forecast
import psycopg2
from logger import get_logger
import time
from staging import transform_load, transform_load_forecast

log = get_logger("main")

start = time.perf_counter()
log.info("Pipeline started")

cities = ["Jakarta", "Bekasi", "Bandung", "Surabaya", "Semarang", "Depok", "Boyolali"]
apiKey = config.API_KEY

try:
    log.info("Openning database connection...")
    
    with psycopg2.connect(
        host=config.DB_HOST,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASS,
        port=config.DB_PORT
    ) as conn:
        for city in cities:
            try:
                log.info(f"Fetching {city}...")

                current_weather_data = extract(city, apiKey, log)
                forecast_weather_data = extract_forecast(city, apiKey, log)

                current_inserted, current_skipped = load(conn, current_weather_data)
                log.info(f"Current weather: {city} done, inserted = {current_inserted}, skipped = {current_skipped}")
                
                forecast_inserted, forecast_skipped = load_forecast(conn, forecast_weather_data, log)
                log.info(f"Forecast weather: {city} done, inserted = {forecast_inserted}, skipped = {forecast_skipped}")              
                
            except Exception as err:
                log.error(f"Error: {err}")
         
        current_inserted, current_skipped = transform_load(conn, log)
        
        log.info(f"Insert current weather to staging done, inserted = {current_inserted}, skipped = {current_skipped}")
        
        forecast_inserted, forecast_skipped = transform_load_forecast(conn, log)
               
        log.info(f"Insert forecast weather to staging done, inserted = {forecast_inserted}, skipped = {forecast_skipped}")
    
    log.info("Database connection closed")
except psycopg2.OperationalError as err:
    log.error(f"Error: {err}")


duration = round(time.perf_counter() - start, 2)
log.info(f"Pipeline finished, dur={duration}s")


