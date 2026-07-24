# 记录的小费率在哪里发生了变化？

分析 `mobility.credit_card_tip_rate` 在 2025 年上半年和下半年之间的变化。
将其与 `mobility.credit_card_trip_share` 以及口径更广的 `mobility.tip_rate`
进行比较。由于数据源通常不记录现金小费，不要把现金支付记录中的零值解读为乘客行为。

找出值得关注的上车区域和费率代码，检查结果在按周分桶后是否稳定，并说明所使用的分母。
