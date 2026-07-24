from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

WAREHOUSE = Path("data/warehouse.duckdb")


@pytest.mark.skipif(not WAREHOUSE.exists(), reason="run make setup first")
def test_warehouse_has_expected_core_tables() -> None:
    connection = duckdb.connect(str(WAREHOUSE), read_only=True)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables"
            ).fetchall()
        }
        columns = {
            row[0]
            for row in connection.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'yellow_trips'
                """
            ).fetchall()
        }
    finally:
        connection.close()
    assert {"yellow_trips", "pickup_zones", "dropoff_zones", "source_months"} <= tables
    assert {
        "pickup_borough",
        "dropoff_borough",
        "pickup_hour",
        "pickup_weekday",
        "extra_amount_usd",
        "mta_tax_usd",
        "improvement_surcharge_usd",
        "congestion_surcharge_usd",
        "airport_fee_usd",
        "has_known_passenger_count",
        "has_reasonable_speed",
        "is_plausible_record",
    } <= columns


@pytest.mark.skipif(not WAREHOUSE.exists(), reason="run make setup first")
def test_analysis_ready_quality_contracts_hold() -> None:
    connection = duckdb.connect(str(WAREHOUSE), read_only=True)
    try:
        row = connection.execute(
            """
            SELECT
                count(*) FILTER (WHERE NOT is_plausible_record) AS implausible_rows,
                avg(passenger_count) FILTER (
                    WHERE is_plausible_record AND has_known_passenger_count
                ) AS known_average_passengers,
                sum(passenger_count) FILTER (
                    WHERE is_plausible_record AND has_known_passenger_count
                ) / count(*) FILTER (
                    WHERE is_plausible_record AND has_known_passenger_count
                ) AS modeled_average_passengers,
                max(
                    trip_distance_miles / nullif(trip_duration_hours, 0)
                ) FILTER (WHERE is_plausible_record) AS maximum_plausible_speed
            FROM yellow_trips
            WHERE source_month = '2025-01'
            """
        ).fetchone()
    finally:
        connection.close()

    assert row is not None
    implausible_rows, known_average, modeled_average, maximum_speed = row
    assert implausible_rows > 0
    assert modeled_average == pytest.approx(known_average)
    assert 0 < maximum_speed <= 100
