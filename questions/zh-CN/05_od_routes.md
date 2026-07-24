# 哪些起讫路线最为重要？

按行程所属的 `pickup_borough` 和 `dropoff_borough` 维度观察
`mobility.trip_count`、`mobility.average_fare`、
`mobility.average_trip_duration` 和 `mobility.average_speed_mph`。

使用 `pickup_zone` 和 `dropoff_zone` 深入分析影响最显著的行政区组合。比较机场与
非机场路线，评估记录质量，并避免将路线之间的差异视为因果效应。
