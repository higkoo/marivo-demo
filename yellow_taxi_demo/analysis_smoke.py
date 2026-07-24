"""End-to-end Marivo observations proving the main demo analysis families."""

from __future__ import annotations

from datetime import date, timedelta

import marivo.analysis as mv
import marivo.semantic as ms
import pandas as pd

from yellow_taxi_demo.periods import selected_months


def _month_window(month: str) -> tuple[str, str]:
    year, month_number = (int(value) for value in month.split("-"))
    start = date(year, month_number, 1)
    end = date(year + (month_number == 12), (month_number % 12) + 1, 1)
    return start.isoformat(), end.isoformat()


def _dimension(name: str) -> ms.Ref:
    return ms.ref.dimension(f"mobility.yellow_trips.{name}")


def _observe(
    session: mv.Session,
    metric: str,
    *,
    start: str,
    end: str,
    dimensions: tuple[str, ...] = (),
) -> pd.DataFrame:
    frame = session.observe(
        ms.ref.metric(f"mobility.{metric}"),
        time_scope={"start": start, "end": end},
        dimensions=[_dimension(name) for name in dimensions],
        analysis_purpose=f"verify setup runtime for {metric}",
    )
    rows: pd.DataFrame = frame.to_pandas()
    if rows.empty:
        raise RuntimeError(f"Marivo setup smoke returned no rows for {metric}")
    return rows


def main() -> None:
    source_month = selected_months()[0]
    month_start, _ = _month_window(source_month)
    start = month_start
    end = (date.fromisoformat(start) + timedelta(days=1)).isoformat()
    session = mv.session.get_or_create(
        name="setup-smoke",
        question="Can the Yellow Taxi semantic layer execute its main analysis families?",
    )

    pickup = session.observe(
        ms.ref.metric("mobility.trip_count"),
        time_scope={"start": start, "end": end},
        dimensions=[ms.ref.dimension("mobility.pickup_zones.borough")],
        analysis_purpose="verify pickup-zone relationship execution",
    ).to_pandas()
    od = _observe(
        session,
        "trip_count",
        start=start,
        end=end,
        dimensions=("pickup_borough", "dropoff_borough"),
    )
    quality = _observe(
        session,
        "implausible_record_rate",
        start=start,
        end=end,
        dimensions=("payment_type",),
    )
    passengers = _observe(session, "average_passengers", start=start, end=end)
    coverage = _observe(
        session,
        "plausible_passenger_count_coverage",
        start=start,
        end=end,
    )
    fees = _observe(
        session,
        "total_surcharges",
        start=start,
        end=end,
        dimensions=("rate_code",),
    )
    time_pattern = _observe(
        session,
        "trip_count",
        start=start,
        end=end,
        dimensions=("pickup_weekday", "pickup_hour"),
    )
    speed = _observe(
        session,
        "average_speed_mph",
        start=start,
        end=end,
        dimensions=("pickup_borough",),
    )
    credit_tip = _observe(
        session,
        "credit_card_tip_rate",
        start=start,
        end=end,
        dimensions=("pickup_borough",),
    )

    if pickup.empty or pickup["trip_count"].sum() <= 0:
        raise RuntimeError("pickup relationship smoke returned no trips")
    if od["trip_count"].sum() != pickup["trip_count"].sum():
        raise RuntimeError("OD smoke does not reconcile to pickup trip count")
    if not quality["implausible_record_rate"].between(0, 1).all():
        raise RuntimeError("quality smoke returned a rate outside [0, 1]")
    average_passengers = float(passengers["average_passengers"].iloc[0])
    passenger_coverage = float(coverage["plausible_passenger_count_coverage"].iloc[0])
    if not 0 < average_passengers <= 10:
        raise RuntimeError("average passenger smoke returned an implausible value")
    if not 0 < passenger_coverage <= 1:
        raise RuntimeError("passenger coverage smoke returned a rate outside (0, 1]")
    if fees["total_surcharges"].sum() <= 0:
        raise RuntimeError("fee-component smoke returned no surcharges")
    if time_pattern["trip_count"].sum() <= 0:
        raise RuntimeError("time-pattern smoke returned no trips")
    if not speed["average_speed_mph"].dropna().between(0, 100).all():
        raise RuntimeError("speed smoke returned a value outside [0, 100] mph")
    if not credit_tip["credit_card_tip_rate"].dropna().between(0, 1).all():
        raise RuntimeError("credit-card tip smoke returned a rate outside [0, 1]")

    print(
        "analysis smoke verified: pickup relationship, OD, quality, passengers, "
        "fees, time patterns, speed, and credit-card tips "
        f"for {start}"
    )


if __name__ == "__main__":
    main()
