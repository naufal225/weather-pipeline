import config
from ingest import extract
from db import load
import psycopg2

cities = ["Jakarta", "Bekasi", "Bandung", "Surabaya", "Semarang"]

with psycopg2.connect(
    host=config.DB_HOST,
    dbname=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASS,
    port=config.DB_PORT
) as conn:
    for city in cities:

        data = extract(city, config.API_KEY)

        load(conn, data)



