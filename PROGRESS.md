## 13-06-2026

### Source:
https://www.startdataengineering.com/post/design-patterns

### What I Learned
- A data pipeline has 2 fundamental components: **source** and **sink**
- Source: the system that provides input data to the pipeline
- Sink: the system where the pipeline stores processed data
- Source replayability: the ability of a source to answer "what did the data look like n periods ago?" — if it cannot answer this, it is non-replayable
- Replayability is critical for backfilling
- Backfilling: the ability to reprocess historical data — e.g. when a business logic change requires recalculating values on past records, you need the original raw data; this is why replayability matters
- Replayable sources: web server logs, database dumps (WAL/CDC), event streams, etc.
- Non-replayable sources: application tables that are constantly modified, APIs that only return current state, etc.
- A non-replayable source can be made replayable by periodically dumping its raw data into a raw/landing area — however, the granularity of replayability is limited to the dump frequency. If we dump every hour, we cannot reconstruct what the data looked like at the minute level.
- Sink overwritability: the ability to update or replace specific rows in the sink — typically requires a unique key on the target table
- There are 4 extraction patterns: time-ranged, full snapshot, lookback, streaming
- Time-ranged: the pipeline pulls data for a fixed, specific time window per run. The time the pipeline runs and the time window of data it pulls are two separate things. Example: pipeline runs at 00:01 Thursday → pulls data from Wednesday 00:00 to Wednesday 23:59
- Full snapshot: pulls all data from the source on every run — simple to build, but slow and storage-heavy for large datasets
- Lookback: used when the end-user wants an aggregate metric for the past n periods — the window always moves relative to the current run time
- Streaming: processes each record in real-time as it arrives
- Data pipelines have 2 behavioral patterns: idempotent and self-healing
- Idempotency: running the pipeline multiple times with the same input always produces the same output — no duplicates, no schema changes
- Structural patterns define how tasks and transformations are organized: multi-hop, conditional/dynamic, disconnected pipelines
- Multi-hop: data passes through multiple layers (e.g. raw → staging → mart), with data quality checks applied at each layer

### Architecture Decision for weather-pipeline
- Full Snapshot → Multi-hop → Append-only sink

### Terms I Don't Understand Yet (to revisit later)
- CDC (Change Data Capture)
- WAL (Write-Ahead Log)
- Source ordering, exponential backoff, watermarking, handling late-arriving events
- SCD2 (Slowly Changing Dimension Type 2)
- Conditional/dynamic pipelines
- Disconnected pipelines
- Self-healing pipelines

## 14-06-2026

### What I worked on
- Explored OpenWeatherMap API response structure — identified available fields,
  data types, and their meanings
- Saved JSON responses from 4 cities: Bekasi, Bandung, Jakarta, and Surabaya
- Designed and created the raw schema and weather_raw table in PostgreSQL:

    CREATE TABLE raw.weather_raw (
        id          SERIAL PRIMARY KEY,
        city        VARCHAR(100)  NOT NULL,
        observed_at TIMESTAMPTZ   NOT NULL,
        payload     JSONB         NOT NULL,
        ingested_at TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
        UNIQUE(city, observed_at)
    );

- Read: Data Pipeline Design Patterns #2 — Coding Patterns in Python
  (startdataengineering.com/post/code-patterns/)

- Built a complete raw ingest pipeline in Python across 4 modules:
  - config.py — loads and exposes environment variables (DB credentials, API key)
  - ingest.py — extract function: calls OpenWeatherMap API, returns JSON response
  - db.py — load function: inserts raw JSON into raw.weather_raw with idempotency
  - main.py — orchestrator: opens one DB connection, loops over cities, calls
    extract then load for each
- Ran pipeline 3+ times consecutively and verified row count stayed identical —
  ON CONFLICT (city, observed_at) DO NOTHING confirmed working

### What I learned

**Database concepts**
- TIMESTAMP vs TIMESTAMPTZ: TIMESTAMP stores date and time with no timezone
  context — the same value can be interpreted differently depending on the server
  location. TIMESTAMPTZ stores the moment in UTC and converts to local timezone
  on display. Always use TIMESTAMPTZ in data engineering.
- JSON vs JSONB: JSON stores raw text as-is. JSONB stores data in a parsed binary
  format — faster to query, supports indexing into nested fields, and is the
  correct choice for pipeline storage even though key ordering is not preserved.
- Database index: a separate lookup structure that lets PostgreSQL jump directly
  to matching rows instead of scanning the entire table — critical for
  performance at scale.
- SERIAL: shorthand for an auto-incrementing integer backed by a PostgreSQL
  sequence (nextval). Not magic — just a sequence called automatically on INSERT.
- Natural key: a combination of columns that are already meaningful in the
  real world and are naturally unique per row — e.g. (city, observed_at) for
  weather data. Different from a surrogate key (like id SERIAL) which is an
  artificial number with no business meaning.
- OpenWeatherMap returns temperature in Kelvin. Conversion to Celsius
  (value - 273.15) happens in the staging layer, not in raw.
- Unix timestamp: integer representing seconds elapsed since 1970-01-01 00:00:00
  UTC. Field dt in the API response is a Unix timestamp — must be converted to
  TIMESTAMPTZ before storing in observed_at.

**Code design patterns (from article #2)**
- Functional design principles:
  - Atomicity: one function does exactly one task — nothing more
  - Idempotency: same input always produces same output regardless of how many
    times the function is called — no duplicates, no side effects on state
  - No side effects: a function must not modify anything outside its own scope —
    no global variables, no external state changes beyond its return value

- Factory pattern: when multiple pipelines share the same structure (e.g.
  LinkedIn, Reddit pipelines), define a common interface (AbstractPipeline) and
  implement it as separate concrete classes per source. A factory then maps a
  string key to the correct class — eliminates complex if/else chains and makes
  adding new sources easy without touching existing code.

- Singleton pattern: ensures only one instance of a class exists throughout the
  entire runtime — commonly used for database connections and loggers. However,
  it is considered an anti-pattern for testing because it makes it impossible to
  isolate state between test cases.

- Python helpers relevant to DE:
  - typing: provides type hints and type checking — makes function signatures
    explicit about what goes in and what comes out, catches bugs early
  - dataclass: a clean way to define classes that primarily hold data — less
    boilerplate than regular classes
  - context managers (with keyword): automatically handles setup and teardown
    of external connections (database, files) — guarantees close() is called
    even if an error occurs, preventing memory leaks
  - pytest: testing framework
  - decorators: functions that wrap other functions to add behavior

  **From practice**
- DB connection must be opened once outside the loop — opening a new connection
  per city is wasteful and slow (one trip to the post office per letter vs. one
  trip for all letters)
- ON CONFLICT DO NOTHING works because PostgreSQL checks the UNIQUE(city,
  observed_at) constraint on every INSERT — if the combination already exists,
  the row is silently skipped, no error, no duplicate
- Separating concerns across files (config / ingest / db / main) means each file
  has exactly one reason to change — if the API changes, only ingest.py is
  touched; if the DB changes, only db.py

### What I don't understand yet
- Strategy pattern — mentioned in the article but not fully clear
- Callable type hint with nested generics:

    from typing import Callable, List

    def transformation_factory(value: str) -> Callable[[List[SocialMediaData]], List[SocialMediaData]]:
        factory = {
            'sd': standard_deviation_outlier_filter,
            'no_tx': no_transformation,
            'rand': random_choice_filter,
        }
        return factory[value]

  Callable[[input_types], output_type] means the function returns another
  function — but the nested List syntax is still confusing.


## 15-06-2026

### What I worked on
- Added raw JSON validation in db.py before processing
- Modified load() to return (inserted, skipped) row counts
- Built logger.py — logging module with file and console handlers
- Integrated logger into main.py — every run now produces a structured log
- Added pipeline duration tracking using time.perf_counter()

### What I learned
- Logging is not optional in production pipelines — without it, if something
  breaks at 3am you have no way to know what happened, when it happened, or
  which city caused the failure. print() disappears when the terminal closes;
  log files persist.
- Tracking inserted vs skipped rows per run makes idempotency observable —
  you can see exactly whether data was new or a duplicate, not just assume
  the pipeline worked correctly.
- Defensive validation in db.py (checking that required keys exist in raw_json
  before touching the database) prevents silent partial failures — the pipeline
  fails loudly with a clear message instead of crashing with a cryptic KeyError
  deep in the stack.
- time.perf_counter() is more accurate than time.time() for measuring duration
  because it is not affected by system clock changes or NTP sync. Use
  time.time() for timestamps (when something happened), perf_counter() for
  duration (how long something took).

### What the log looks like now
  2026-06-15 17:34:30 INFO     Pipeline started
  2026-06-15 17:34:31 INFO     Jakarta done, inserted = 0, skipped = 1
  2026-06-15 17:34:31 INFO     Bandung done, inserted = 1, skipped = 0
  2026-06-15 17:34:32 INFO     Pipeline finished, dur=1.19s