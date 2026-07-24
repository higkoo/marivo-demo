# 哪些需求异常值得进一步调查？

观察 2025 年的日度 `mobility.trip_count`，发现异常点、时段变化、值得关注的时间窗口，
以及上车区域之间的横截面异常值。

在报告异常之前，检查源数据的月份覆盖情况以及
`mobility.implausible_record_rate`、
`mobility.pickup_time_mismatch_rate`、
`mobility.nonpositive_duration_record_rate`、
`mobility.nonpositive_distance_record_rate` 和
`mobility.negative_fare_record_rate`。确定每个可疑分段主要由哪一种质量问题驱动，
并区分已发布记录中的异常与现实世界中的需求事件。
