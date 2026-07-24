"""Static semantic-layer verification used by setup."""

from __future__ import annotations

import marivo.semantic as ms


def main() -> None:
    catalog = ms.load()
    required = [
        ms.ref.metric("mobility.trip_count"),
        ms.ref.metric("mobility.fare_revenue"),
        ms.ref.metric("mobility.total_surcharges"),
        ms.ref.metric("mobility.tip_rate"),
        ms.ref.metric("mobility.credit_card_tip_rate"),
        ms.ref.metric("mobility.average_passengers"),
        ms.ref.metric("mobility.passenger_count_coverage"),
        ms.ref.metric("mobility.plausible_passenger_count_coverage"),
        ms.ref.metric("mobility.average_speed_mph"),
        ms.ref.metric("mobility.implausible_record_rate"),
        ms.ref.metric("mobility.negative_fare_record_rate"),
        ms.ref.dimension("mobility.pickup_zones.borough"),
        ms.ref.dimension("mobility.dropoff_zones.borough"),
        ms.ref.dimension("mobility.yellow_trips.pickup_borough"),
        ms.ref.dimension("mobility.yellow_trips.dropoff_borough"),
        ms.ref.dimension("mobility.yellow_trips.pickup_hour"),
        ms.ref.dimension("mobility.yellow_trips.pickup_weekday"),
    ]
    for ref in required:
        catalog.require(ref)
    metrics = [ref for ref in required if ref.kind == "metric"]
    report = catalog.readiness(refs=metrics)
    if report.status != "ready":
        report.show()
        raise RuntimeError(
            "required Yellow Taxi metrics are not fully ready; "
            "run make semantic-snapshot and inspect the report"
        )
    print(
        f"semantic catalog verified: {len(required)} required refs, "
        f"readiness={report.status}"
    )


if __name__ == "__main__":
    main()
