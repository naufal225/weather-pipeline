## Lessons Learned

### Why idempotency matters

**The problem**
Without idempotency, running the pipeline 5 times with the same input produces
5 copies of the same data in the database. Each run blindly inserts without
checking whether the data already exists.

**Why this is dangerous in production**
Duplicate data silently corrupts every downstream calculation. Total revenue
becomes 5x the real number. Average temperature is distorted. Business reports
can no longer be trusted — and the worst part is the error is not obvious until
someone manually audits the numbers.

**The solution**
Define a natural key that is uniquely meaningful in the real world. For weather
data, the combination of city and observation time (city, observed_at) can never
be duplicated — one city only has one weather condition at any given moment.

Enforce this at the database level with a UNIQUE constraint, then use
ON CONFLICT DO NOTHING in the INSERT statement. PostgreSQL checks the constraint
on every insert — if the combination already exists, the row is silently skipped.
The pipeline can be run any number of times and the result is always identical.

This property — same input always produces same output regardless of how many
times it runs — is called idempotency. It is not optional in production pipelines.

## Pipeline Components

| File | Responsibility |
|------|----------------|
| `config.py` | Loads and exposes required configuration from environment variables (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, API_KEY) |
| `ingest.py` | Provides `extract(city, api_key, log)` — calls the OpenWeatherMap API with a 10-second timeout, retries up to 3 times with exponential backoff on connection/timeout errors, and returns the raw JSON response |
| `db.py` | Provides `load(conn, raw_json)` — validates and inserts raw JSON into `raw.weather_raw`, using `ON CONFLICT DO NOTHING` for idempotency, and returns the count of inserted vs. skipped rows |
| `logger.py` | Provides `get_logger(name)` — builds a logger with a predefined format (timestamp, level, message) that writes to both a daily log file and the console |
| `main.py` | Orchestrates all modules above — opens one database connection, loops through cities calling extract then load, and logs run metrics (rows inserted/skipped, duration) |

## Error Handling & Resilience

This pipeline has been tested against the following failure scenarios:

| Scenario | Behavior |
|----------|----------|
| **Network failure** (internet disconnected mid-run) | The API call raises a `ConnectionError`/`Timeout`. The pipeline retries up to 3 times with exponential backoff (2s, 4s) before logging a clear error and moving to the next city — it does not crash the entire run. |
| **Invalid API credentials** | The API returns HTTP 401. This is not retried (retrying a bad key will never succeed) — the pipeline logs the error immediately and continues with the next city:<br>`ERROR Error: API_Error: 401 - Invalid API key` |
| **Database unavailable** | The connection attempt fails with `psycopg2.OperationalError`, caught by a dedicated try/except around the connection step, and logged clearly instead of crashing with a raw traceback:<br>`ERROR Error: connection to server at "localhost" (::1)... Connection refused`<br>`connection to server at "localhost" (127.0.0.1)... Connection refused`<br><br>Note: two error lines appear because `psycopg2` (via `libpq`) attempts the IPv6 address (`::1`) first, then falls back to IPv4 (`127.0.0.1`) if that fails. |

## Idempotency

The raw layer enforces a natural key — `UNIQUE(city, observed_at)` — since one
city can only have one weather observation at any given timestamp. Every
insert uses `ON CONFLICT (city, observed_at) DO NOTHING`, so PostgreSQL itself
guarantees no duplicates are ever created, regardless of how many times the
pipeline runs with the same input.

Verified by running the pipeline 10 times consecutively: row count in
`raw.weather_raw` remained identical after the first successful run, with
subsequent runs logging `inserted = 0, skipped = 1` for unchanged data.

## Staging Schema Design

| Column | Type | Reasoning |
|--------|------|-----------|
| `id` | `SERIAL` | Auto-incrementing surrogate key — always increases by 1, no business meaning |
| `city` | `VARCHAR(100)` | Stores city name, which is alphabetic text |
| `observed_at` | `TIMESTAMPTZ` | Stores the observation timestamp while preserving timezone information |
| `temp_celsius` | `NUMERIC(5,2)` | Temperature after Kelvin→Celsius conversion is almost always a decimal value |
| `humidity` | `INTEGER` | Humidity is always a whole number (percentage) |
| `weather_main` | `VARCHAR(50)` | Short weather category label (e.g. "Clouds", "Rain") |
| `weather_description` | `VARCHAR(100)` | Longer weather description text (e.g. "scattered clouds") |
| `wind_speed` | `NUMERIC(5,2)` | Wind speed can have decimal values |
| `loaded_at` | `TIMESTAMPTZ` | Records when the row was loaded into staging, with timezone information |