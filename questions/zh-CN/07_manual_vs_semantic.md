# 手动查询数据和用 Marivo 语义层相比，差在哪？

> **你能学到什么**：先亲手用最简单的命令行手段查一遍原始数据，再对比 Marivo 语义层能帮你省下多少事——从而理解"语义层治理"的真正价值。
> **难度**：对比（建议做完 01–03 后看）

## 背景小知识：从零开始手动查数据（两条路线）

下面是一个**完全新手友好**的手动操作流程。你可以先跟着做一遍，
然后就会明白"为啥要有语义层"。

### 前置条件（两条路线都要做）

```bash
# 1) 创建一个目录放数据
mkdir -p ~/nyc_taxi && cd ~/nyc_taxi

# 2) 下载区域对照表（一次就行）
curl -fsSL --retry 5 --progress-bar \
  "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv" \
  -o taxi_zone_lookup.csv

# 3) 下载 2025 年 1 月行程数据（~57 MB）
curl -fsSL --retry 5 --progress-bar \
  "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet" \
  -o yellow_tripdata_2025-01.parquet
```

---

### 路线 A：纯 Shell（零 Python 依赖，推荐先做）

只需要装 **一个工具** `duckdb`，它是个独立的命令行程序，
不会影响你系统里的其他东西：

```bash
# 安装 duckdb CLI（Mac 用户也可以用 brew install duckdb）
pip install duckdb-cli      # 或者 brew install duckdb

# 验证一下
duckdb --version
```

装好之后，**所有查询都是一行命令**。下面从易到难列出来。

#### 1. 查看 Parquet schema

```bash
duckdb -c "SELECT name, type FROM parquet_schema('yellow_tripdata_2025-01.parquet') WHERE name <> 'schema'"
```

#### 2. 看一眼行数

```bash
duckdb -c "SELECT count(*) FROM read_parquet('yellow_tripdata_2025-01.parquet')"
```

#### 3. 看前 5 行关键字段

```bash
duckdb -c "
  SELECT tpep_pickup_datetime AS pickup,
         trip_distance, fare_amount, tip_amount, total_amount,
         payment_type, PULocationID, DOLocationID
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  LIMIT 5
"
```

#### 4. 基础汇总（行程数、车费、小费率）

```bash
duckdb -c "
  SELECT count(*) AS trips,
         round(sum(fare_amount), 2) AS total_fare,
         round(sum(tip_amount), 2) AS total_tips,
         round(sum(tip_amount)/nullif(sum(fare_amount), 0), 4) AS tip_rate
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  WHERE trip_distance > 0 AND total_amount >= 0
"
```

#### 5. 按小时看打车热度

```bash
duckdb -c "
  SELECT extract(hour FROM tpep_pickup_datetime) AS hour,
         count(*) AS trips
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 1
"
```

#### 6. 按支付方式看差异

```bash
duckdb -c "
  SELECT payment_type,
         count(*) AS trips,
         round(avg(fare_amount), 2) AS avg_fare,
         round(avg(tip_amount), 2) AS avg_tip
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 2 DESC
"
```

#### 7. 关联区域表，看哪个行政区最多

```bash
duckdb -c "
  SELECT z.Borough AS pickup_borough,
         count(*) AS trips,
         round(sum(t.total_amount), 0) AS revenue
  FROM read_parquet('yellow_tripdata_2025-01.parquet') t
  LEFT JOIN read_csv_auto('taxi_zone_lookup.csv', header=true) z
    ON t.PULocationID = z.LocationID
  GROUP BY 1 ORDER BY 2 DESC LIMIT 5
"
```

#### 8. 数据质量巡检（你会第一次看到"脏数据"）

```bash
duckdb -c "
  SELECT
    count(*) FILTER (WHERE fare_amount < 0) AS neg_fare,
    count(*) FILTER (WHERE trip_distance = 0) AS zero_mi,
    count(*) FILTER (WHERE passenger_count IS NULL) AS null_pax,
    count(*) FILTER (WHERE tpep_dropoff_datetime <= tpep_pickup_datetime) AS bad_duration
  FROM read_parquet('yellow_tripdata_2025-01.parquet')
"
```

#### 9. 读全部 12 个月（跨月分析）

DuckDB 原生支持 glob，直接一个 pattern 全读进来：

```bash
# 先把剩下 11 个月也下载一下（略，URL 里月份改一下就行）
# 然后一行查全年
duckdb -c "
  SELECT strftime(tpep_pickup_datetime, '%Y-%m') AS month,
         count(*) AS trips,
         round(sum(fare_amount), 0) AS fare
  FROM read_parquet('yellow_tripdata_2025-*.parquet')
  GROUP BY 1 ORDER BY 1
"
```

#### 10. 建成一个本地仓库（后续查询超快）

```bash
duckdb warehouse.duckdb <<'SQL'
CREATE TABLE trips AS SELECT * FROM read_parquet('yellow_tripdata_2025-*.parquet', union_by_name=true);
CREATE TABLE zones AS SELECT * FROM read_csv_auto('taxi_zone_lookup.csv', header=true);
SQL
# 之后就可以直接：
duckdb warehouse.duckdb -c "SELECT count(*) FROM trips"
```

---

### 路线 B：Python + Pandas/DuckDB

适合已经装了 Python 的同学。先装依赖：

```bash
pip install duckdb pandas
```

然后写一个脚本（比如叫 `manual_query.py`）：

```python
import duckdb

con = duckdb.connect()
con.execute("CREATE TABLE trips AS SELECT * FROM read_parquet('yellow_tripdata_2025-01.parquet')")
con.execute("CREATE TABLE zones AS SELECT * FROM read_csv_auto('taxi_zone_lookup.csv', header=true)")

# 查询 1：基础汇总
print(con.execute("""
    SELECT count(*) AS trips,
           round(sum(fare_amount), 2) AS fare_usd,
           round(sum(tip_amount)/nullif(sum(fare_amount),0), 4) AS tip_rate
    FROM trips
    WHERE trip_distance > 0 AND total_amount >= 0
""").fetchdf())

# 查询 2：按小时分布
print(con.execute("""
    SELECT extract(hour FROM tpep_pickup_datetime) AS h,
           count(*) AS trips
    FROM trips GROUP BY 1 ORDER BY 1
""").fetchdf())

# 查询 3：按支付方式 + 小费率
print(con.execute("""
    SELECT payment_type,
           count(*) AS trips,
           round(sum(tip_amount)/nullif(sum(fare_amount),0), 4) AS tip_rate
    FROM trips WHERE fare_amount > 0 GROUP BY 1 ORDER BY 2 DESC
""").fetchdf())
```

运行：

```bash
python3 manual_query.py
```

---

### 手动查询会遇到的坑（提前预警）

做完上面的练习，你大概率会注意到这些问题：

1. **每个查询都要自己写 WHERE 条件**：要不要过滤零里程？要不要过滤负车费？
   不同查询可能忘写，结果口径不一致。

2. **支付方式、费率的数字代码看不懂**：`payment_type = 1` 是什么？`RatecodeID = 2`？
   每次都得查数据字典，或者在 SQL 里写 CASE WHEN。

3. **现金和信用卡的小费口径混淆**：直接 `sum(tip_amount)` 算出来的"小费率"
   其实是**被现金记录严重拉低**的（现金不记录小费，值是 0），真正的骑手小费率
   应该只算 `payment_type = 1` 的信用卡行程。这个过滤条件很容易忘。

4. **时间戳的时区问题**：Parquet 里的时间是 America/New_York 本地时间，
   如果你自己用 Python `datetime.utcfromtimestamp` 转换，会差 5 小时。

5. **区域 JOIN 容易写出笛卡尔积**：PULocationID 和 DOLocationID 都要
   JOIN 区域表，忘了加 ON 条件或者写错关联字段就出大问题。

6. **多月份 union_by_name 忘了加**：12 个文件列如果有一点点不一样（比如
   新增了字段），直接 `UNION ALL` 会报错，得加 `union_by_name=true`。

7. **CBD 拥堵费字段**：2025 年 1 月 5 日才生效，之前的零值不代表违规，
   分析时自己得记得这个时间点。

8. **每次分析都要先写 10 行预处理 SQL**：JOIN 区域表、翻译代码、过滤
   不合理记录、派生小时/星期维度……一个简单的"按小时看需求"查询
   实际要写 30 行 SQL。

## 提问给 Agent

假设你刚刚按上面的流程手动查了一遍数据，请对比两种方式：

1. **直接用原始 Parquet + duckdb SQL 查询**（你刚刚做的）
2. **用 Marivo 语义层（`import marivo.semantic as ms`）查询**

分别用两种方式回答同一个问题——"2025 年 1 月信用卡支付的记录，
小费率是多少？分星期几看有什么差异？"——然后从以下维度对比：

- 需要写多少行代码/SQL？
- 哪些过滤条件是"必须记得手动加"的，哪些是语义层已经帮你加好的？
- 口径是否容易写错？（比如现金 vs 信用卡、计价器车费 vs 支付总额、合理记录 vs 全部记录）
- 遇到数据质量问题（负车费、零里程、passenger_count 为空）时，手动查和用语义层分别怎么处理？
- 想把分析范围从 1 月扩大到全年 12 月，两种方式各自需要改什么？

最终用一句话总结：**在什么场景下手动查够用，在什么场景下语义层能帮你省很多事。**

## 小白提示

- 先真的动手跑一遍上面的 Shell 或 Python 命令，**不要跳过**。
  只有亲自写过 SQL，才会觉得语义层的"傻瓜式"指标是真的省心。
- 对比的时候别纠结谁"更高级"——手动查在快速探索阶段就很好用，
  语义层在反复做、多人协作、要保证口径一致时才体现价值。
- 跑完手动查询后，看看你花了多少分钟，再让 Agent 用语义层答同一个问题，
  感受一下差距。
