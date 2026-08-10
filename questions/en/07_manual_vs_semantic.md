# Manual query vs semantic layer — what's the difference?

> **What you will learn**: Run raw queries with minimal tooling, then compare
> with Marivo's governed semantic layer — and understand why semantic
> governance matters.
> **Difficulty**: contrast (recommended after 01–03)

## Background: query raw data from zero (two paths)

Below is a beginner-friendly hands-on guide. Work through it once and you'll
immediately see why a semantic layer is useful.

### Prerequisites (both paths)

```bash
# 1) Make a folder for the data
mkdir -p ~/nyc_taxi && cd ~/nyc_taxi

# 2) Download the zone lookup (do once)
curl -fsSL --retry 5 --progress-bar \
  "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv" \
  -o taxi_zone_lookup.csv

# 3) Download 2025-01 trip data (~57 MB)
curl -fsSL --retry 5 --progress-bar \
  "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet" \
  -o yellow_tripdata_2025-01.parquet
```

---

### Path A: pure Shell (zero Python, try this first)

You only need **one tool**: `duckdb`, a single self-contained CLI binary.

```bash
# Install duckdb CLI (Mac users can also brew install duckdb)
pip install duckdb-cli

# Verify
duckdb --version
```

Every query is a **single-line shell command**. Examples from easy to hard:

#### 1. Inspect Parquet schema

```bash
duckdb -c "SELECT name, type FROM parquet_schema('yellow_tripdata_2025-01.parquet') WHERE name <> 'schema'"
```

#### 2. Row count

```bash
duckdb -c "SELECT count(*) FROM read_parquet('yellow_tripdata_2025-01.parquet')"
```

#### 3. Top 5 rows, key columns

```bash
duckdb -c "
  SELECT tpep_pickup_datetime AS pickup,
         trip_distance, fare_amount, tip_amount, total_amount,
         payment_type, PULocationID, DOLocationID
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  LIMIT 5
"
```

#### 4. Basic summary (trips, fare, tip rate)

```bash
duckdb -c "
  SELECT count(*) AS trips,
         round(sum(fare_amount), 2) AS total_fare,
         round(sum(tip_amount), 2) AS total_tips,
         round(sum(tip_amount)/nullif(sum(fare_amount), 0), 4) AS tip_rate
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  WHERE trip_distance > 0 AND total_amount >= 0
"
```

#### 5. Trips by hour of day

```bash
duckdb -c "
  SELECT extract(hour FROM tpep_pickup_datetime) AS hour,
         count(*) AS trips
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 1
"
```

#### 6. By payment type

```bash
duckdb -c "
  SELECT payment_type,
         count(*) AS trips,
         round(avg(fare_amount), 2) AS avg_fare,
         round(avg(tip_amount), 2) AS avg_tip
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 2 DESC
"
```

#### 7. Join zone table — top pickup boroughs

```bash
duckdb -c "
  SELECT z.Borough AS pickup_borough,
         count(*) AS trips,
         round(sum(t.total_amount), 0) AS revenue
  FROM read_parquet('yellow_tripdata_2025-01.parquet') t
  LEFT JOIN read_csv_auto('taxi_zone_lookup.csv', header=true) z
    ON t.PULocationID = z.LocationID
  GROUP BY 1 ORDER BY 2 DESC LIMIT 5
"
```

#### 8. Data quality inspection

```bash
duckdb -c "
  SELECT
    count(*) FILTER (WHERE fare_amount < 0) AS neg_fare,
    count(*) FILTER (WHERE trip_distance = 0) AS zero_mi,
    count(*) FILTER (WHERE passenger_count IS NULL) AS null_pax,
    count(*) FILTER (WHERE tpep_dropoff_datetime <= tpep_pickup_datetime) AS bad_duration
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
"
```

#### 9. All 12 months at once (cross-month analysis)

DuckDB natively supports glob — one pattern, all files:

```bash
duckdb -c "
  SELECT strftime(tpep_pickup_datetime, '%Y-%m') AS month,
         count(*) AS trips,
         round(sum(fare_amount), 0) AS fare
  FROM read_parquet('yellow_tripdata_2025-*.parquet')
  GROUP BY 1 ORDER BY 1
"
```

#### 10. Build a local DuckDB warehouse

```bash
duckdb warehouse.duckdb <<'SQL'
CREATE TABLE trips AS SELECT * FROM read_parquet('yellow_tripdata_2025-*.parquet', union_by_name=true);
CREATE TABLE zones AS SELECT * FROM read_csv_auto('taxi_zone_lookup.csv', header=true);
SQL
# After that:
duckdb warehouse.duckdb -c "SELECT count(*) FROM trips"
```

---

### Path B: Python + Pandas/DuckDB

For those who already have Python installed.

```bash
pip install duckdb pandas
```

Script example (`manual_query.py`):

```python
import duckdb

con = duckdb.connect()
con.execute("CREATE TABLE trips AS SELECT * FROM read_parquet('yellow_tripdata_2025-01.parquet')")
con.execute("CREATE TABLE zones AS SELECT * FROM read_csv_auto('taxi_zone_lookup.csv', header=true)")

print(con.execute("""
    SELECT count(*) AS trips,
           round(sum(fare_amount), 2) AS fare_usd,
           round(sum(tip_amount)/nullif(sum(fare_amount),0), 4) AS tip_rate
    FROM trips
    WHERE trip_distance > 0 AND total_amount >= 0
""").fetchdf())

print(con.execute("""
    SELECT extract(hour FROM tpep_pickup_datetime) AS h,
           count(*) AS trips
    FROM trips GROUP BY 1 ORDER BY 1
""").fetchdf())

print(con.execute("""
    SELECT payment_type,
           count(*) AS trips,
           round(sum(tip_amount)/nullif(sum(fare_amount),0), 4) AS tip_rate
    FROM trips WHERE fare_amount > 0 GROUP BY 1 ORDER BY 2 DESC
""").fetchdf())
```

Run with:

```bash
python3 manual_query.py
```

---

### Common pitfalls of manual querying

After running through the steps above you will likely notice:

1. **Every query needs its own WHERE clause** — filter zero-distance?
   Negative fare? Forgetting one gives inconsistent numbers.

2. **TLC code numbers are opaque** — `payment_type = 1` means what?
   `RatecodeID = 2`? You either memorize the data dictionary or write
   CASE WHEN in every SQL.

3. **Tip rate is trivially wrong if you forget payment-type filtering** —
   cash trips record zero tip, so a naive `sum(tip_amount)/sum(fare_amount)`
   is systematically understated. The real rider tip rate needs
   `payment_type = 1`.

4. **Timezone** — the Parquet timestamps are already `America/New_York`.
   If you convert with Python `utcfromtimestamp` you get 5 hours off.

5. **Double JOINs for pickup and dropoff** — easy to mis-write or forget
   the ON condition, producing a Cartesian product silently.

6. **`union_by_name` matters across months** — if one file gains a new column
   later, plain `UNION ALL` breaks.

7. **CBD congestion fee has a start date** — before Jan 5, 2025, zeros are
   normal, not non-compliance.

8. **Every new analysis re-requires 10+ lines of prep SQL** — JOIN zones,
   translate codes, filter implausibles, derive hour/weekday dimensions.
   A simple "trips by hour" query turns into 30 lines of SQL.

## Question to ask the Agent

Suppose you just ran the raw-query guide above. Compare two ways of answering
the same question — *"What is the tip rate among credit-card trips in January
2025, broken down by day of week?"* — using:

1. **Raw Parquet + duckdb SQL** (which you just did)
2. **Marivo semantic layer** (`import marivo.semantic as ms`)

Compare along these dimensions:

- How many lines of SQL / code each approach needs?
- Which filters are "you must remember to add them manually" in raw SQL,
  and which does the semantic layer apply for you?
- Where is it easy to get the numbers wrong in raw SQL
  (cash vs credit, metered fare vs total charged, plausible vs all records)?
- How does each approach handle data quality issues
  (negative fares, zero distance, null `passenger_count`)?
- If the analysis scope expands from January to all 12 months,
  what changes in each approach?

End with a one-sentence summary: **When is raw SQL good enough,
and when does a semantic layer save real time?**

## Tips for beginners

- **Run the commands first.** Don't skip this. You need to write the SQL
  yourself once before the semantic layer's convenience becomes tangible.
- Don't frame this as "one is better than the other." Raw SQL is great for
  quick exploration. A semantic layer shines when multiple people need
  consistent numbers, or when the same analysis pattern repeats.
- After you've run the raw queries, time yourself — then ask the Agent
  the same question through the semantic layer and feel the difference.
