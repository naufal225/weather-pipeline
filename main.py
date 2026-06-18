import config
from ingest import extract
from db import load
import psycopg2
from logger import get_logger
import time

log = get_logger("main")

start = time.perf_counter()
log.info("Pipeline started")

cities = ["Jakarta", "Bekasi", "Bandung", "Surabaya", "Semarang"]

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

                data = extract(city, config.API_KEY, log)

                inserted, skipped = load(conn, data)
                
                log.info(f"{city} done, inserted = {inserted}, skipped = {skipped}")
            except Exception as err:
                log.error(f"Error: {err}")
                
    log.info("Database connection closed")
except psycopg2.OperationalError as err:
    log.error(f"Error: {err}")


duration = round(time.perf_counter() - start, 2)
log.info(f"Pipeline finished, dur={duration}s")


