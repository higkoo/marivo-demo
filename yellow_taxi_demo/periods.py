"""Pinned source-period contract for the demo."""

from __future__ import annotations

import os

DEFAULT_MONTHS: tuple[str, ...] = tuple(f"2025-{month:02d}" for month in range(1, 13))


def selected_months() -> tuple[str, ...]:
    """Return the committed period set or an explicit development override."""
    raw = os.environ.get("TAXI_DEMO_MONTHS")
    if raw is None:
        return DEFAULT_MONTHS
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    invalid = tuple(item for item in values if len(item) != 7 or item[4] != "-")
    if not values or invalid:
        raise ValueError(
            "TAXI_DEMO_MONTHS must be a comma-separated non-empty YYYY-MM list; "
            f"received {raw!r}"
        )
    return values
