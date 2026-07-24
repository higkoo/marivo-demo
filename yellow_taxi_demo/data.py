"""Download, build, and verify the local Yellow Taxi warehouse."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

from yellow_taxi_demo.periods import selected_months

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse.duckdb"
DOWNLOAD_MANIFEST_PATH = PROJECT_ROOT / "data" / "download-manifest.json"
TRIP_BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


@dataclass(frozen=True)
class DownloadRecord:
    """Locally verified identity of one downloaded source file."""

    name: str
    url: str
    bytes: int
    sha256: str


def _trip_path(month: str) -> Path:
    return RAW_DIR / f"yellow_tripdata_{month}.parquet"


def _run_curl(url: str, destination: Path) -> None:
    part = destination.with_suffix(f"{destination.suffix}.part")
    subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--location",
            "--http1.1",
            "--retry",
            "5",
            "--retry-delay",
            "2",
            "--speed-limit",
            "1024",
            "--speed-time",
            "30",
            "--continue-at",
            "-",
            "--output",
            str(part),
            url,
        ],
        check=True,
    )
    part.replace(destination)


def _parquet_is_readable(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    try:
        with duckdb.connect() as connection:
            columns = connection.execute(
                "SELECT name FROM parquet_schema(?) WHERE name <> 'schema'",
                [str(path)],
            ).fetchall()
    except duckdb.Error:
        return False
    names = {str(row[0]) for row in columns}
    return {
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "PULocationID",
        "DOLocationID",
        "total_amount",
    }.issubset(names)


def _ensure_trip_file(month: str) -> Path:
    destination = _trip_path(month)
    if _parquet_is_readable(destination):
        print(f"reuse {destination.name}")
        return destination
    destination.unlink(missing_ok=True)
    url = f"{TRIP_BASE_URL}/{destination.name}"
    print(f"download {destination.name}")
    _run_curl(url, destination)
    if not _parquet_is_readable(destination):
        destination.unlink(missing_ok=True)
        raise RuntimeError(f"downloaded Parquet failed schema validation: {url}")
    return destination


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download() -> None:
    """Download the selected official monthly files and zone lookup."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    months = selected_months()
    workers = max(1, int(os.environ.get("TAXI_DEMO_DOWNLOAD_WORKERS", "4")))
    trip_paths: list[Path] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_ensure_trip_file, month): month for month in months}
        for future in as_completed(futures):
            trip_paths.append(future.result())

    zone_path = RAW_DIR / "taxi_zone_lookup.csv"
    if not zone_path.is_file() or zone_path.stat().st_size == 0:
        print(f"download {zone_path.name}")
        _run_curl(ZONE_URL, zone_path)
    if zone_path.stat().st_size == 0:
        raise RuntimeError("Taxi Zone lookup is empty")

    records = [
        DownloadRecord(
            name=path.name,
            url=(
                ZONE_URL
                if path == zone_path
                else f"{TRIP_BASE_URL}/{path.name}"
            ),
            bytes=path.stat().st_size,
            sha256=_sha256(path),
        )
        for path in sorted([*trip_paths, zone_path])
    ]
    DOWNLOAD_MANIFEST_PATH.write_text(
        json.dumps(
            {
                "schema": "marivo-yellow-taxi-download/v1",
                "months": list(months),
                "files": [asdict(record) for record in records],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    total_bytes = sum(record.bytes for record in records)
    print(f"downloaded {len(records)} files ({total_bytes / 1_000_000_000:.2f} GB)")


def _warehouse_sql() -> str:
    return """
CREATE TABLE pickup_zones AS
SELECT
    LocationID::BIGINT AS location_id,
    Borough::VARCHAR AS borough,
    Zone::VARCHAR AS zone,
    service_zone::VARCHAR AS service_zone
FROM read_csv_auto($zones, header = true);

CREATE TABLE dropoff_zones AS SELECT * FROM pickup_zones;

CREATE VIEW yellow_trips AS
WITH raw AS (
    SELECT
        *,
        filename AS source_file,
        regexp_extract(filename, '(\\d{4}-\\d{2})', 1) AS source_month
    FROM read_parquet($files, union_by_name = true, filename = true)
)
SELECT
    source_month,
    tpep_pickup_datetime AS picked_up_at,
    tpep_dropoff_datetime AS dropped_off_at,
    date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 60.0
        AS trip_duration_minutes,
    date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) / 3600.0
        AS trip_duration_hours,
    extract('hour' FROM tpep_pickup_datetime)::BIGINT AS pickup_hour,
    extract('isodow' FROM tpep_pickup_datetime)::BIGINT AS pickup_weekday_number,
    strftime(tpep_pickup_datetime, '%A') AS pickup_weekday,
    extract('isodow' FROM tpep_pickup_datetime) IN (6, 7) AS pickup_is_weekend,
    VendorID::BIGINT AS vendor_id,
    CASE VendorID
        WHEN 1 THEN 'Creative Mobile Technologies'
        WHEN 2 THEN 'Curb Mobility'
        WHEN 6 THEN 'Myle Technologies'
        WHEN 7 THEN 'Helix'
        ELSE 'Unmapped or not reported'
    END AS vendor,
    passenger_count::DOUBLE AS passenger_count,
    trip_distance::DOUBLE AS trip_distance_miles,
    RatecodeID::BIGINT AS rate_code_id,
    CASE
        WHEN RatecodeID IS NULL THEN 'Not reported'
        WHEN RatecodeID = 1 THEN 'Standard rate'
        WHEN RatecodeID = 2 THEN 'JFK'
        WHEN RatecodeID = 3 THEN 'Newark'
        WHEN RatecodeID = 4 THEN 'Nassau or Westchester'
        WHEN RatecodeID = 5 THEN 'Negotiated fare'
        WHEN RatecodeID = 6 THEN 'Group ride'
        WHEN RatecodeID = 99 THEN 'Null or unknown'
        ELSE 'Unmapped'
    END AS rate_code,
    CASE store_and_fwd_flag::VARCHAR
        WHEN 'Y' THEN 'Stored then forwarded'
        WHEN 'N' THEN 'Sent immediately'
        ELSE 'Not reported'
    END AS store_and_forward,
    PULocationID::BIGINT AS pickup_location_id,
    DOLocationID::BIGINT AS dropoff_location_id,
    pickup.borough AS pickup_borough,
    pickup.zone AS pickup_zone,
    pickup.service_zone AS pickup_service_zone,
    dropoff.borough AS dropoff_borough,
    dropoff.zone AS dropoff_zone,
    dropoff.service_zone AS dropoff_service_zone,
    payment_type::BIGINT AS payment_type_id,
    CASE payment_type
        WHEN 0 THEN 'Flex Fare trip'
        WHEN 1 THEN 'Credit card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No charge'
        WHEN 4 THEN 'Dispute'
        WHEN 5 THEN 'Unknown (code 5)'
        WHEN 6 THEN 'Voided trip'
        ELSE 'Unmapped or not reported'
    END AS payment_type,
    fare_amount::DOUBLE AS fare_amount_usd,
    extra::DOUBLE AS extra_amount_usd,
    mta_tax::DOUBLE AS mta_tax_usd,
    tip_amount::DOUBLE AS tip_amount_usd,
    tolls_amount::DOUBLE AS tolls_amount_usd,
    improvement_surcharge::DOUBLE AS improvement_surcharge_usd,
    total_amount::DOUBLE AS total_amount_usd,
    congestion_surcharge::DOUBLE AS congestion_surcharge_usd,
    Airport_fee::DOUBLE AS airport_fee_usd,
    cbd_congestion_fee::DOUBLE AS cbd_congestion_fee_usd,
    coalesce(
        strftime(tpep_pickup_datetime, '%Y-%m') = source_month,
        false
    ) AS pickup_time_matches_source_month,
    coalesce(tpep_dropoff_datetime > tpep_pickup_datetime, false)
        AS has_positive_duration,
    coalesce(trip_distance >= 0, false) AS has_nonnegative_distance,
    coalesce(trip_distance > 0, false) AS has_positive_distance,
    coalesce(trip_distance BETWEEN 0 AND 200, false) AS has_reasonable_distance,
    coalesce(
        date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)
            BETWEEN 1 AND 86400,
        false
    ) AS has_reasonable_duration,
    coalesce(
        trip_distance = 0
        OR (
            date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) > 0
            AND trip_distance
                / (
                    date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)
                    / 3600.0
                ) <= 100
        ),
        false
    ) AS has_reasonable_speed,
    coalesce(fare_amount >= 0, false) AS has_nonnegative_fare,
    coalesce(total_amount >= 0, false) AS has_nonnegative_total,
    passenger_count IS NOT NULL AS has_known_passenger_count,
    pickup.location_id IS NOT NULL AS has_valid_pickup_zone,
    dropoff.location_id IS NOT NULL AS has_valid_dropoff_zone,
    coalesce((
        strftime(tpep_pickup_datetime, '%Y-%m') = source_month
        AND tpep_dropoff_datetime > tpep_pickup_datetime
        AND date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime) <= 86400
        AND trip_distance BETWEEN 0 AND 200
        AND (
            trip_distance = 0
            OR trip_distance
                / (
                    date_diff('second', tpep_pickup_datetime, tpep_dropoff_datetime)
                    / 3600.0
                ) <= 100
        )
        AND fare_amount >= 0
        AND total_amount >= 0
        AND pickup.location_id IS NOT NULL
        AND dropoff.location_id IS NOT NULL
    ), false) AS is_plausible_record
FROM raw
LEFT JOIN pickup_zones AS pickup ON PULocationID = pickup.location_id
LEFT JOIN dropoff_zones AS dropoff ON DOLocationID = dropoff.location_id;

CREATE TABLE source_months AS
SELECT
    source_month,
    count(*) AS row_count,
    min(picked_up_at) AS minimum_pickup,
    max(picked_up_at) AS maximum_pickup
FROM yellow_trips
GROUP BY source_month
ORDER BY source_month;
"""


def _sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build() -> None:
    """Build a replacement DuckDB warehouse from the selected raw files."""
    months = selected_months()
    files = [_trip_path(month) for month in months]
    missing = [path.name for path in files if not _parquet_is_readable(path)]
    zone_path = RAW_DIR / "taxi_zone_lookup.csv"
    if missing or not zone_path.is_file():
        raise RuntimeError(
            "source files are incomplete; run data download first. "
            f"missing_or_invalid={missing!r}"
        )

    temporary = WAREHOUSE_PATH.with_suffix(".duckdb.tmp")
    temporary.unlink(missing_ok=True)
    connection = duckdb.connect(str(temporary))
    try:
        connection.execute("PRAGMA threads = 4")
        files_sql = "[" + ", ".join(_sql_string(str(path)) for path in files) + "]"
        build_sql = (
            _warehouse_sql()
            .replace("$files", files_sql)
            .replace("$zones", _sql_string(str(zone_path)))
        )
        connection.execute(build_sql)
        connection.execute(
            """
            CREATE TABLE warehouse_metadata AS
            SELECT
                'marivo-yellow-taxi-warehouse/v1' AS schema,
                $months AS source_months,
                current_timestamp AS built_at
            """,
            {"months": ",".join(months)},
        )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()
    temporary.replace(WAREHOUSE_PATH)
    print(f"built {WAREHOUSE_PATH}")


def verify() -> None:
    """Verify source coverage and the materialized warehouse contract."""
    if not WAREHOUSE_PATH.is_file():
        raise RuntimeError("warehouse is missing; run data build")
    months = selected_months()
    connection = duckdb.connect(str(WAREHOUSE_PATH), read_only=True)
    try:
        actual_months = tuple(
            row[0]
            for row in connection.execute(
                "SELECT source_month FROM source_months ORDER BY source_month"
            ).fetchall()
        )
        trip_row = connection.execute("SELECT count(*) FROM yellow_trips").fetchone()
        zone_row = connection.execute("SELECT count(*) FROM pickup_zones").fetchone()
        null_time_row = connection.execute(
            """
            SELECT count(*) FROM yellow_trips
            WHERE picked_up_at IS NULL OR dropped_off_at IS NULL
            """
        ).fetchone()
        if trip_row is None or zone_row is None or null_time_row is None:
            raise RuntimeError("warehouse verification query returned no scalar row")
        trip_count = int(trip_row[0])
        zone_count = int(zone_row[0])
        null_times = int(null_time_row[0])
    finally:
        connection.close()
    if actual_months != months:
        raise RuntimeError(f"warehouse months differ: expected={months!r} actual={actual_months!r}")
    if trip_count <= 0:
        raise RuntimeError("warehouse has no trip rows")
    if zone_count < 260:
        raise RuntimeError(f"Taxi Zone lookup is incomplete: {zone_count}")
    if null_times:
        raise RuntimeError(f"warehouse has {null_times} rows with null trip timestamps")
    print(
        f"verified {len(months)} months, {trip_count:,} trips, "
        f"{zone_count} pickup zones"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("download", "build", "verify", "all"))
    command = parser.parse_args().command
    if command in {"download", "all"}:
        download()
    if command in {"build", "all"}:
        build()
    if command in {"verify", "all"}:
        verify()


if __name__ == "__main__":
    main()
