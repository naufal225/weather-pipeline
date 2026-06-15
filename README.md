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