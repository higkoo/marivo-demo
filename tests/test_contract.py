from __future__ import annotations

from yellow_taxi_demo.periods import DEFAULT_MONTHS


def test_default_period_contract_is_one_complete_calendar_year() -> None:
    assert len(DEFAULT_MONTHS) == 12
    assert DEFAULT_MONTHS[0] == "2025-01"
    assert DEFAULT_MONTHS[-1] == "2025-12"
