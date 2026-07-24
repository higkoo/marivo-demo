# Which demand anomalies deserve investigation?

Observe daily `mobility.trip_count` during 2025 and discover unusual points,
period shifts, interesting windows, and cross-sectional pickup-zone outliers.

Check source-month coverage, `mobility.implausible_record_rate`,
`mobility.pickup_time_mismatch_rate`,
`mobility.nonpositive_duration_record_rate`,
`mobility.nonpositive_distance_record_rate`, and
`mobility.negative_fare_record_rate` before reporting anomalies. Determine
which quality reason drives each suspicious segment and separate
published-record anomalies from real-world demand events.
