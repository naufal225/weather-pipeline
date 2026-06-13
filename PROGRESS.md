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