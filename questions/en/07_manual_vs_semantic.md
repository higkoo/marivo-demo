# Manual query vs semantic layer — what's the difference?

> **What you will learn**: Run raw queries with minimal tooling, then compare
> with Marivo's governed semantic layer — and understand why semantic
> governance matters.
> **Difficulty**: contrast (recommended after 01–03)

## Background: query raw data from zero

All commands below follow the project's own path conventions:

```
project-root/
├── data/
│   ├── raw/
│   │   ├── yellow_tripdata_2025-01.parquet   ← monthly trip files
│   │   ├── yellow_tripdata_2025-02.parquet
│   │   ├── ... (01–12, 12 files total)
│   │   └── taxi_zone_lookup.csv              ← zone lookup table
│   └── warehouse.duckdb                      ← built after `make setup`
└── ...
```

Start with `make setup` to download the data (~750 MB, a few minutes):

```bash
make setup
```

---

### Prerequisite: install DuckDB CLI (one-time)

DuckDB ships a pre-compiled command-line binary. Four lines and you're done:

```bash
wget https://github.com/duckdb/duckdb/releases/download/v1.5.5/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
chmod +x duckdb
sudo mv duckdb /usr/local/bin/
```

Verify:

```bash
duckdb --version   # v1.5.5 (Variegata)
```

No Python, no pip, no virtualenv — **pure Shell, zero dependencies**.

---

### Path A: pure Shell + DuckDB CLI (recommended first)

All queries run from the project root. Just `duckdb -c "SQL"`.

#### 1. Inspect Parquet columns and types

```bash
duckdb -c "
SELECT name, type
FROM parquet_schema('data/raw/yellow_tripdata_2025-01.parquet')
WHERE name <> 'schema'
ORDER BY name
"
```

#### 2. Row count

```bash
duckdb -c "
SELECT count(*) AS trips
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
"
```

#### 3. Top 5 rows, key columns

```bash
duckdb -c "
SELECT tpep_pickup_datetime AS pickup,
       trip_distance, fare_amount, tip_amount, total_amount,
       payment_type, PULocationID, DOLocationID
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
LIMIT 5
"
```

#### 4. Basic summary (trips, fare, tip rate)

```bash
duckdb -c "
SELECT
  count(*) AS trips,
  round(sum(fare_amount), 2) AS total_fare,
  round(sum(tip_amount), 2) AS total_tips,
  round(sum(tip_amount) / nullif(sum(fare_amount), 0), 4) AS tip_rate
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
WHERE trip_distance > 0 AND total_amount >= 0
"
```

#### 5. Trips by hour of day

```bash
duckdb -c "
SELECT extract(hour FROM tpep_pickup_datetime) AS hour,
       count(*) AS trips
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
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
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
GROUP BY 1 ORDER BY 2 DESC
"
```

#### 7. Join zone table — top pickup boroughs

```bash
duckdb -c "
SELECT z.Borough AS pickup_borough,
       count(*) AS trips,
       round(sum(t.total_amount), 0) AS revenue
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet') t
LEFT JOIN read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true) z
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
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
"
```

#### 9. All 12 months at once (cross-month analysis)

```bash
duckdb -c "
SELECT strftime(tpep_pickup_datetime, '%Y-%m') AS month,
       count(*) AS trips,
       round(sum(fare_amount), 0) AS fare
FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet')
GROUP BY 1 ORDER BY 1
"
```

> You will notice this query returns **16 rows**, not 12. It picks up
> stray records from 2007–2009 and 2024-12. The raw data hands
> you everything — no filtering.

#### 10. Build a local DuckDB warehouse

```bash
duckdb data/manual_warehouse.duckdb -c "
CREATE TABLE trips AS
SELECT * FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet', union_by_name=true);
CREATE TABLE zones AS
SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true);
"

# Then:
duckdb data/manual_warehouse.duckdb -c "SELECT count(*) FROM trips"
```

The project's own warehouse is `data/warehouse.duckdb` (built by
`make setup`). Yours lives in `data/manual_warehouse.duckdb` —
no conflicts.

---

### Path B: Python + DuckDB (optional, for data-science workflows)

If you also have Python around, use the duckdb library inside Jupyter:

```bash
pip install duckdb pandas
```

Then a short script:

```python
import duckdb

con = duckdb.connect()
con.execute("""
    CREATE TABLE trips AS
    SELECT * FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet',
                                union_by_name=true)
""")
con.execute("""
    CREATE TABLE zones AS
    SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true)
""")

print(con.execute("""
    SELECT extract(hour FROM tpep_pickup_datetime) AS h,
           count(*) AS trips
    FROM trips
    GROUP BY 1 ORDER BY 1
""").fetchall())
```

---

### Common pitfalls of manual querying

After running through the steps above you will likely notice:

1. **Every query needs its own WHERE clause** — filter zero-distance?
   Negative fare? Stray records from 2007? Forgetting one gives
   inconsistent numbers.

2. **TLC code numbers are opaque** — `payment_type = 1` is credit card,
   `payment_type = 2` is cash, `RatecodeID = 2` is JFK. Either
   memorize the data dictionary or write CASE WHEN in every SQL.

3. **Tip rate is trivially wrong if you forget payment-type filtering** —
   cash trips record zero tip, so a naive `sum(tip_amount)/sum(fare_amount)`
   is systematically understated. The real rider tip rate needs
   `payment_type = 1`.

4. **Timezone** — the Parquet timestamps are already `America/New_York`.
   If you convert with Python `utcfromtimestamp` you get 5 hours off.

5. **Double JOINs for pickup and dropoff** — easy to mis-write or forget
   the ON condition, producing a Cartesian product silently.

6. **Glob pattern needs care** — `read_parquet('data/raw/*.parquet')`
   grabs `.part` temp files too. Use the exact
   `yellow_tripdata_2025-*.parquet` pattern.

7. **CBD congestion fee has a start date** — before Jan 5, 2025, zeros are
   normal, not non-compliance.

8. **Every new analysis re-requires 10+ lines of prep SQL** — JOIN zones,
   translate codes, filter implausibles, derive hour/weekday dimensions.
   A simple "trips by hour" query turns into 30 lines of SQL.

## Question to ask the Agent

Suppose you just ran the raw-query guide above. Compare two ways of
answering the same question — *"What is the tip rate among credit-card
trips in January 2025, broken down by day of week?"* — using:

1. **Raw Parquet + duckdb SQL** (which you just did)
2. **Marivo semantic layer** (`import marivo.semantic as ms`)

Compare along these dimensions:

- How many lines of SQL / code each approach needs?
- Which filters are "you must remember to add them manually" in raw SQL,
  and which does the semantic layer apply for you?
- Where is it easy to get the numbers wrong in raw SQL
  (cash vs credit, metered fare vs total charged, plausible vs all records)?
- How does each approach handle data quality issues
  (negative fares, zero distance, null `passenger_count`, stray 2007 records)?
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
- Try deliberately **skipping all WHERE filters** on the full-year glob
  query. Notice that "44.47 million trips, ~$9.2B fare" includes a single
  $17 trip from 2007 and a single $70 trip from 2008 — does that change
  your conclusion? Probably not, but you should know they are there.

---

## Appendix: the DuckDB warehouse built by `make setup`

In addition to downloading raw Parquet files into `data/raw/`,
`make setup` also builds a local DuckDB warehouse at
`data/warehouse.duckdb` (~1.3 MB).

The warehouse combines the 12 monthly Parquet files + the zone lookup
table, and derives 30+ convenience columns on top of the raw fields.
**Raw data files are never modified** — everything lives as views and
dimension tables inside DuckDB.

### Inspect what's in the warehouse

```bash
duckdb data/warehouse.duckdb -c "
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_type, table_name
"
```

### The 5 objects, at a glance

| Object | Type | Description |
|--------|------|-------------|
| `yellow_trips` | **VIEW** | The core: one row per TLC trip record, with 30+ derived convenience columns on top of raw fields |
| `pickup_zones` | TABLE | Taxi Zone lookup, **pickup-role** version (265 zones) |
| `dropoff_zones` | TABLE | Same zone table, **dropoff-role** copy (identical columns, kept separate so you can JOIN without aliasing) |
| `source_months` | TABLE | Row count, min/max pickup time per source month (12 rows) |
| `warehouse_metadata` | TABLE | Warehouse version, build timestamp, data provenance |

### The 49 columns of `yellow_trips`, grouped

**Time & duration (9 columns)**

| Column | Type | Description |
|--------|------|-------------|
| `source_month` | VARCHAR | Source file month (`2025-01` … `2025-12`) |
| `picked_up_at` | TIMESTAMP | Pickup time (America/New_York) |
| `dropped_off_at` | TIMESTAMP | Dropoff time |
| `trip_duration_minutes` | DOUBLE | Duration in minutes |
| `trip_duration_hours` | DOUBLE | Duration in hours |
| `pickup_hour` | BIGINT | Pickup hour 0–23 |
| `pickup_weekday_number` | BIGINT | ISO weekday (1=Monday … 7=Sunday) |
| `pickup_weekday` | VARCHAR | Weekday name (`Monday` … `Sunday`) |
| `pickup_is_weekend` | BOOLEAN | Whether the trip started on Saturday or Sunday |

**Trip attributes (8 columns)**

| Column | Type | Description |
|--------|------|-------------|
| `vendor_id` / `vendor` | BIGINT / VARCHAR | TPEP vendor code + translated name |
| `passenger_count` | DOUBLE | Number of passengers (driver-entered, can be null) |
| `trip_distance_miles` | DOUBLE | Trip distance in miles |
| `rate_code_id` / `rate_code` | BIGINT / VARCHAR | Rate code + translation (`Standard` / `JFK` / `Newark` …) |
| `store_and_forward` | VARCHAR | Whether the trip was "stored and forwarded" |

**Zone (6 columns, two roles each)**

| Column | Type | Description |
|--------|------|-------------|
| `pickup_location_id` / `dropoff_location_id` | BIGINT | Pickup / dropoff zone ID |
| `pickup_borough` / `dropoff_borough` | VARCHAR | Borough (Manhattan / Queens / Brooklyn / Bronx / Staten Island / EWR / Unknown) |
| `pickup_zone` / `dropoff_zone` | VARCHAR | Zone name (e.g. `Midtown East`) |
| `pickup_service_zone` / `dropoff_service_zone` | VARCHAR | Service zone category (`Yellow Zone` / `Boro Zone` / `EWR`) |

**Payment (2 columns)**

| Column | Type | Description |
|--------|------|-------------|
| `payment_type_id` | BIGINT | Payment-type code |
| `payment_type` | VARCHAR | Translation: `Credit card` / `Cash` / `No charge` / `Dispute` / `Unknown` |

**Amounts (10 columns, all with `_usd` suffix)**

| Column | Description |
|--------|-------------|
| `fare_amount_usd` | Metered fare |
| `extra_amount_usd` | Extra surcharge |
| `mta_tax_usd` | MTA tax |
| `tip_amount_usd` | Tip (mostly credit-card tips; cash tips are not recorded) |
| `tolls_amount_usd` | Tolls |
| `improvement_surcharge_usd` | TLC improvement surcharge |
| `total_amount_usd` | Total charged to passenger (excludes cash tips) |
| `congestion_surcharge_usd` | NY state congestion surcharge |
| `airport_fee_usd` | Airport fee |
| `cbd_congestion_fee_usd` | CBD congestion fee (effective Jan 5, 2025) |

**Data-quality flags (12 columns, all BOOLEAN)**

| Column | Check |
|--------|-------|
| `pickup_time_matches_source_month` | Pickup month matches the source file's month |
| `has_positive_duration` | Duration > 0 |
| `has_nonnegative_distance` | Distance ≥ 0 |
| `has_positive_distance` | Distance > 0 |
| `has_reasonable_distance` | Distance between 0 and 200 miles |
| `has_reasonable_duration` | Duration between 0 and 24 hours |
| `has_reasonable_speed` | Implied speed ≤ 100 mph |
| `has_nonnegative_fare` | Fare ≥ 0 |
| `has_nonnegative_total` | Total charged ≥ 0 |
| `has_known_passenger_count` | Passenger count is not null |
| `has_valid_pickup_zone` | Pickup zone ID resolves to the official lookup |
| `has_valid_dropoff_zone` | Dropoff zone ID resolves to the official lookup |
| **`is_plausible_record`** | **Composite "reasonable record" flag combining all of the above** |

### A few queries to try

```bash
# Inspect the schema
duckdb data/warehouse.duckdb -c "DESCRIBE yellow_trips"

# Plausible vs implausible share
duckdb data/warehouse.duckdb -c "
SELECT
  is_plausible_record,
  count(*) AS trips
FROM yellow_trips
GROUP BY 1
ORDER BY 1 DESC
"

# Raw Parquet row count vs warehouse view — should match exactly
# Note: we must connect to warehouse.duckdb because yellow_trips lives there
duckdb data/warehouse.duckdb -c "
SELECT 'raw' AS source, count(*) FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet')
UNION ALL
SELECT 'warehouse', count(*) FROM yellow_trips
"
```
