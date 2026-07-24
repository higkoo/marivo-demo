# Which origin-destination routes matter most?

Observe `mobility.trip_count`, `mobility.average_fare`,
`mobility.average_trip_duration`, and `mobility.average_speed_mph` by the
trip-owned `pickup_borough` and `dropoff_borough` dimensions.

Drill into the most material borough pairs using `pickup_zone` and
`dropoff_zone`. Compare airport and non-airport routes, assess record quality,
and avoid treating route differences as causal effects.
