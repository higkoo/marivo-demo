"""Acquire bounded datasource evidence and preview representative semantic metrics."""

from __future__ import annotations

import marivo.datasource as md
import marivo.semantic as ms

TRIP_COLUMNS = (
    "source_month",
    "picked_up_at",
    "dropped_off_at",
    "pickup_hour",
    "pickup_weekday_number",
    "pickup_weekday",
    "pickup_is_weekend",
    "vendor_id",
    "vendor",
    "payment_type_id",
    "payment_type",
    "rate_code_id",
    "rate_code",
    "store_and_forward",
    "pickup_location_id",
    "dropoff_location_id",
    "pickup_borough",
    "pickup_zone",
    "pickup_service_zone",
    "dropoff_borough",
    "dropoff_zone",
    "dropoff_service_zone",
    "fare_amount_usd",
    "extra_amount_usd",
    "mta_tax_usd",
    "tip_amount_usd",
    "tolls_amount_usd",
    "improvement_surcharge_usd",
    "total_amount_usd",
    "congestion_surcharge_usd",
    "airport_fee_usd",
    "cbd_congestion_fee_usd",
    "trip_distance_miles",
    "trip_duration_minutes",
    "trip_duration_hours",
    "passenger_count",
    "pickup_time_matches_source_month",
    "has_positive_duration",
    "has_nonnegative_distance",
    "has_positive_distance",
    "has_reasonable_distance",
    "has_reasonable_duration",
    "has_reasonable_speed",
    "has_nonnegative_fare",
    "has_nonnegative_total",
    "has_known_passenger_count",
    "has_valid_pickup_zone",
    "has_valid_dropoff_zone",
    "is_plausible_record",
)
ZONE_COLUMNS = ("location_id", "borough", "zone", "service_zone")


def _sample(source_name: str, columns: tuple[str, ...]) -> md.DiscoverySnapshot:
    inspection = md.inspect(ms.ref.datasource("warehouse"), md.table(source_name))
    return inspection.sample(
        scope=md.unpruned(max_rows=1000, timeout_seconds=30),
        columns=columns,
        persist_values=False,
        refresh=False,
    )


def main() -> None:
    trip_snapshot = _sample("yellow_trips", TRIP_COLUMNS)
    pickup_snapshot = _sample("pickup_zones", ZONE_COLUMNS)
    dropoff_snapshot = _sample("dropoff_zones", ZONE_COLUMNS)

    catalog = ms.load()
    refs_and_snapshots: list[tuple[ms.Ref, md.DiscoverySnapshot]] = []
    for collection in (
        catalog.entities,
        catalog.dimensions,
        catalog.time_dimensions,
        catalog.measures,
        catalog.metrics,
    ):
        for item in collection:
            ref_id = str(item.ref)
            if "mobility.pickup_zones" in ref_id:
                snapshot = pickup_snapshot
            elif "mobility.dropoff_zones" in ref_id:
                snapshot = dropoff_snapshot
            else:
                snapshot = trip_snapshot
            refs_and_snapshots.append((item.ref, snapshot))

    failed: list[str] = []
    for ref, snapshot in refs_and_snapshots:
        result = catalog.preview(ref, using=snapshot, limit=10)
        if result.status != "passed":
            failed.append(str(ref))
    for relationship in catalog.relationships:
        if "pickup" in relationship.ref.name:
            zone_ref = ms.ref.entity("mobility.pickup_zones")
            zone_snapshot = pickup_snapshot
        else:
            zone_ref = ms.ref.entity("mobility.dropoff_zones")
            zone_snapshot = dropoff_snapshot
        relationship_snapshots = {
            ms.ref.entity("mobility.yellow_trips"): trip_snapshot,
            zone_ref: zone_snapshot,
        }
        result = catalog.preview(
            relationship.ref,
            using=relationship_snapshots,
            limit=10,
        )
        if result.status != "passed":
            failed.append(str(relationship.ref))
    if failed:
        raise RuntimeError(f"semantic previews failed: {failed!r}")
    print(
        f"semantic evidence acquired: 3 sources, "
        f"{len(refs_and_snapshots) + len(catalog.relationships)} semantic previews"
    )


if __name__ == "__main__":
    main()
