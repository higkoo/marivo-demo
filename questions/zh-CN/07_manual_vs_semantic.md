# 手动查询数据和用 Marivo 语义层相比，差在哪？

> **你能学到什么**：先亲手用最简单的命令行手段查一遍原始数据，
> 再对比 Marivo 语义层能帮你省下多少事——从而理解"语义层治理"的真正价值。
> **难度**：对比（建议做完 01–03 后看）

## 背景小知识：从零开始手动查数据

下面所有命令**都基于项目自身的路径约定**：

```
项目根/
├── data/
│   ├── raw/
│   │   ├── yellow_tripdata_2025-01.parquet   ← 每月行程文件
│   │   ├── yellow_tripdata_2025-02.parquet
│   │   ├── ... （01–12，共 12 个）
│   │   └── taxi_zone_lookup.csv              ← 区域对照表
│   └── warehouse.duckdb                      ← make setup 后自动构建
└── ...
```

先跑 `make setup` 把数据下好（约 750 MB，几分钟）：

```bash
make setup
```

---

### 前置：装 DuckDB CLI（一次性）

DuckDB 官方提供预编译的命令行二进制，一行命令就能用：

```bash
wget https://github.com/duckdb/duckdb/releases/download/v1.5.5/duckdb_cli-linux-amd64.zip
unzip duckdb_cli-linux-amd64.zip
chmod +x duckdb
sudo mv duckdb /usr/local/bin/
```

验证：

```bash
duckdb --version   # v1.5.5 (Variegata)
```

不需要 Python、不需要 pip、不需要 `.venv`——**纯 Shell 零依赖**。

---

### 路线 A：纯 Shell + DuckDB CLI（推荐先做）

所有查询都在项目根目录下执行，直接用 `duckdb -c "SQL"`。

#### 1. 看 Parquet 里有哪些列

```bash
duckdb -c "
SELECT name, type
FROM parquet_schema('data/raw/yellow_tripdata_2025-01.parquet')
WHERE name <> 'schema'
ORDER BY name
"
```

#### 2. 看行数

```bash
duckdb -c "
SELECT count(*) AS trips
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
"
```

#### 3. 看前 5 行关键字段

```bash
duckdb -c "
SELECT tpep_pickup_datetime AS pickup,
       trip_distance, fare_amount, tip_amount, total_amount,
       payment_type, PULocationID, DOLocationID
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
LIMIT 5
"
```

#### 4. 基础汇总（行程数、车费、小费率）

```bash
duckdb -c "
SELECT
  count(*) AS trips,
  round(sum(fare_amount), 2) AS total_fare,
  round(sum(tip_amount), 2) AS total_tips,
  round(sum(tip_amount) / nullif(sum(fare_amount), 0), 4) AS tip_rate
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
WHERE trip_distance > 0 AND total_amount >= 0
"
```

#### 5. 按小时看打车热度

```bash
duckdb -c "
SELECT extract(hour FROM tpep_pickup_datetime) AS hour,
       count(*) AS trips
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
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
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
GROUP BY 1 ORDER BY 2 DESC
"
```

#### 7. 关联区域表，看哪个行政区最多

```bash
duckdb -c "
SELECT z.Borough AS pickup_borough,
       count(*) AS trips,
       round(sum(t.total_amount), 0) AS revenue
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet') t
LEFT JOIN read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true) z
  ON t.PULocationID = z.LocationID
GROUP BY 1 ORDER BY 2 DESC LIMIT 5
"
```

#### 8. 数据质量巡检

```bash
duckdb -c "
SELECT
  count(*) FILTER (WHERE fare_amount < 0) AS neg_fare,
  count(*) FILTER (WHERE trip_distance = 0) AS zero_mi,
  count(*) FILTER (WHERE passenger_count IS NULL) AS null_pax,
  count(*) FILTER (WHERE tpep_dropoff_datetime <= tpep_pickup_datetime) AS bad_duration
FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
"
```

#### 9. 读全部 12 个月（跨月分析）

```bash
duckdb -c "
SELECT strftime(tpep_pickup_datetime, '%Y-%m') AS month,
       count(*) AS trips,
       round(sum(fare_amount), 0) AS fare
FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet')
GROUP BY 1 ORDER BY 1
"
```

> 你注意到什么了吗？上面这个查询会出来 **16 行**，
> 其中有 2007-12、2008-12、2009-01 的零星记录，
> 还有 2024-12 的 21 条——这些就是"脏数据"。
> 原始数据**不帮你过滤**，全给你看。

#### 10. 建成一个本地 DuckDB 仓库（后续查询超快）

```bash
duckdb data/manual_warehouse.duckdb -c "
CREATE TABLE trips AS
SELECT * FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet', union_by_name=true);
CREATE TABLE zones AS
SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true);
"

# 之后直接：
duckdb data/manual_warehouse.duckdb -c "SELECT count(*) FROM trips"
```

项目自己的仓库是 `data/warehouse.duckdb`（`make setup` 构建的），
你自己建的这个叫 `data/manual_warehouse.duckdb`，
两者互不冲突。

---

### 路线 B：Python + DuckDB（可选，适合数据科学场景）

如果你同时装了 Python，可以用 duckdb 库在 Jupyter 里分析：

```bash
pip install duckdb pandas
```

然后写脚本：

```python
import duckdb

# 一次性注册（12 个文件）
con = duckdb.connect()
con.execute("""
    CREATE TABLE trips AS
    SELECT * FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet',
                                union_by_name=true)
""")
con.execute("""
    CREATE TABLE zones AS
    SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true)
""")

# 直接查
print(con.execute("""
    SELECT extract(hour FROM tpep_pickup_datetime) AS h,
           count(*) AS trips
    FROM trips
    GROUP BY 1 ORDER BY 1
""").fetchall())
```

---

### 手动查询会遇到的坑（提前预警）

做完上面的练习，你大概率会注意到这些问题：

1. **每个查询都要自己写 WHERE 条件**：要不要过滤零里程？
   要不要过滤负车费？要不要排除 2007 年那几条脏数据？
   不同查询可能忘写，结果口径不一致。

2. **支付方式、费率的数字代码看不懂**：`payment_type = 1` 是信用卡、
   `payment_type = 2` 是现金、`RatecodeID = 2` 是 JFK……
   每次都得查数据字典，或者在 SQL 里写 CASE WHEN 翻译。

3. **现金和信用卡的小费口径混淆**：直接 `sum(tip_amount)` 算出来的
   小费率会被现金记录严重拉低（现金不记录小费，值是 0）。
   正确的骑手小费率应该只算 `payment_type = 1` 的信用卡行程。
   这个过滤条件特别容易忘，结果差了 5 个百分点。

4. **时间戳的时区问题**：Parquet 里的时间已经是 `America/New_York`
   本地时间，如果你自己用 Python `utcfromtimestamp` 转换会差 5 小时。

5. **区域 JOIN 容易写出笛卡尔积**：PULocationID 和 DOLocationID 都要
   JOIN 区域表，忘了加 ON 条件或者写错关联字段就出大问题。

6. **多月份 glob 有小陷阱**：`read_parquet('data/raw/*.parquet')` 会把
   `.part`（还没下完的临时文件）也当 Parquet 读，得用精确的
   `yellow_tripdata_2025-*.parquet` 模式。

7. **CBD 拥堵费字段**：2025 年 1 月 5 日才生效，之前的零值不代表违规，
   分析时自己得记得这个时间点。

8. **每次分析都要先写 10 行预处理 SQL**：JOIN 区域表、翻译代码、
   过滤不合理记录、派生小时/星期维度……一个简单的"按小时看需求"
   实际要写 30 行 SQL。

## 提问给 Agent

假设你刚刚按上面的流程手动查了一遍数据。请对比两种方式，
回答同一个问题——**"2025 年 1 月信用卡支付的记录，小费率是多少？
分星期几看有什么差异？"**

分别用：

1. **原始 Parquet + duckdb SQL**（你刚刚跑的）
2. **Marivo 语义层**（`import marivo.semantic as ms`）

然后从以下维度对比：

- 需要写多少行代码/SQL？
- 哪些过滤条件是"必须记得手动加"的，哪些是语义层已经帮你加好的？
- 口径是否容易写错？（现金 vs 信用卡、计价器车费 vs 支付总额、合理记录 vs 全部记录）
- 遇到数据质量问题（负车费、零里程、脏数据）时，手动查和用语义层分别怎么处理？
- 想把分析范围从 1 月扩大到全年 12 月，两种方式各自需要改什么？

最终用一句话总结：**在什么场景下手动查够用，在什么场景下语义层能帮你省很多事。**

## 小白提示

- **先真的动手跑一遍命令**，不要跳过。
  只有亲自写过 SQL，才会觉得语义层的"傻瓜式"指标是真的省心。
- 对比的时候别纠结谁"更高级"——手动查在快速探索阶段就很好用，
  语义层在反复做、多人协作、要保证口径一致时才体现价值。
- 跑完手动查询后，看看你花了多少分钟，再让 Agent 用语义层答同一个问题，
  感受一下差距。
- 试试故意**不加任何过滤条件**跑一次全年查询，然后想想：
  你得到的那个"全年总共 4447 万条、车费约 92 亿美元"的数字，
  里面混了 2007 年的一条 17 美元记录和 2008 年的一条 70 美元记录——
  对你的结论有影响吗？（答案是：看情况，但你得先**知道它们存在**。）

---

## 附录：`make setup` 构建的 DuckDB 仓库

`make setup` 除了下载原始文件到 `data/raw/`，还会自动构建一个
**本地 DuckDB 仓库**：`data/warehouse.duckdb`（约 1.3 MB）。

这个仓库把 12 个 Parquet 文件 + 区域表整合在了一起，
并在原始字段之上派生了大量便捷字段。**不修改原始数据文件**，
只是在 DuckDB 里建了一个视图和几张维表。

### 查看仓库里有什么

```bash
duckdb data/warehouse.duckdb -c "
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'main'
ORDER BY table_type, table_name
"
```

### 5 个库对象一览

| 对象 | 类型 | 说明 |
|------|------|------|
| `yellow_trips` | **视图（VIEW）** | 核心：一行 = 一条官方发布的行程，在原始字段上派生了 30+ 个便捷列 |
| `pickup_zones` | 表 | Taxi Zone 区域表，**上车角色**的 265 个区域 |
| `dropoff_zones` | 表 | 同样的区域表，**下车角色**版本（字段相同，独立一份方便 JOIN） |
| `source_months` | 表 | 每月的行数、最早/最晚上车时间（12 行） |
| `warehouse_metadata` | 表 | 仓库版本、构建时间、数据来源等元信息 |

### `yellow_trips` 视图的 49 列分组

**时间 & 时长（9 列）**

| 列名 | 类型 | 说明 |
|------|------|------|
| `source_month` | VARCHAR | 来源文件月份（`2025-01` … `2025-12`） |
| `picked_up_at` | TIMESTAMP | 上车时间（America/New_York） |
| `dropped_off_at` | TIMESTAMP | 下车时间 |
| `trip_duration_minutes` | DOUBLE | 行程时长（分钟） |
| `trip_duration_hours` | DOUBLE | 行程时长（小时） |
| `pickup_hour` | BIGINT | 上车小时 0–23 |
| `pickup_weekday_number` | BIGINT | ISO 星期（1=周一 … 7=周日） |
| `pickup_weekday` | VARCHAR | 星期名称（`Monday` … `Sunday`） |
| `pickup_is_weekend` | BOOLEAN | 是否周末 |

**行程属性（8 列）**

| 列名 | 类型 | 说明 |
|------|------|------|
| `vendor_id` / `vendor` | BIGINT / VARCHAR | TPEP 服务商编码 + 翻译名 |
| `passenger_count` | DOUBLE | 乘客数（可为空） |
| `trip_distance_miles` | DOUBLE | 里程（英里） |
| `rate_code_id` / `rate_code` | BIGINT / VARCHAR | 费率编码 + 翻译（`Standard` / `JFK` / `Newark` …） |
| `store_and_forward` | VARCHAR | 是否先存后发 |

**区域（6 列，上车 + 下车各一套）**

| 列名 | 类型 | 说明 |
|------|------|------|
| `pickup_location_id` / `dropoff_location_id` | BIGINT | 上车 / 下车区域 ID |
| `pickup_borough` / `dropoff_borough` | VARCHAR | 行政区（Manhattan / Queens / Brooklyn / Bronx / Staten Island / EWR / Unknown） |
| `pickup_zone` / `dropoff_zone` | VARCHAR | 区域名称（如 `Midtown East`） |
| `pickup_service_zone` / `dropoff_service_zone` | VARCHAR | 服务区分类（`Yellow Zone` / `Boro Zone` / `EWR`） |

**支付（2 列）**

| 列名 | 类型 | 说明 |
|------|------|------|
| `payment_type_id` | BIGINT | 支付方式编码 |
| `payment_type` | VARCHAR | 翻译：`Credit card` / `Cash` / `No charge` / `Dispute` / `Unknown` |

**金额（10 列，统一加 `_usd` 后缀）**

| 列名 | 说明 |
|------|------|
| `fare_amount_usd` | 计价器车费 |
| `extra_amount_usd` | 附加费 |
| `mta_tax_usd` | MTA 税 |
| `tip_amount_usd` | 小费（基本只有信用卡小费，现金小费不在内） |
| `tolls_amount_usd` | 过路费 |
| `improvement_surcharge_usd` | TLC 改善附加费 |
| `total_amount_usd` | 乘客支付总额（不含现金小费） |
| `congestion_surcharge_usd` | 纽约州拥堵附加费 |
| `airport_fee_usd` | 机场费 |
| `cbd_congestion_fee_usd` | CBD 拥堵费（2025-01-05 起生效） |

**数据质量标记（12 列，全部是 BOOLEAN）**

| 列名 | 检查内容 |
|------|----------|
| `pickup_time_matches_source_month` | 上车月份是否与源文件月份一致 |
| `has_positive_duration` | 时长 > 0 |
| `has_nonnegative_distance` | 里程 ≥ 0 |
| `has_positive_distance` | 里程 > 0 |
| `has_reasonable_distance` | 里程在 0–200 英里 |
| `has_reasonable_duration` | 时长在 0–24 小时 |
| `has_reasonable_speed` | 推算速度 ≤ 100 mph |
| `has_nonnegative_fare` | 车费 ≥ 0 |
| `has_nonnegative_total` | 支付总额 ≥ 0 |
| `has_known_passenger_count` | 乘客数不为空 |
| `has_valid_pickup_zone` | 上车区域 ID 在官方对照表中 |
| `has_valid_dropoff_zone` | 下车区域 ID 在官方对照表中 |
| **`is_plausible_record`** | **综合上面所有条件的"合理记录"标记** |

### 查看示例

```bash
# 看看 yellow_trips 的结构
duckdb data/warehouse.duckdb -c "DESCRIBE yellow_trips"

# 看看合理记录占比
duckdb data/warehouse.duckdb -c "
SELECT
  is_plausible_record,
  count(*) AS trips
FROM yellow_trips
GROUP BY 1
ORDER BY 1 DESC
"

# 对比一下：原始 Parquet vs 仓库视图
# 注意：因为要读 yellow_trips 视图，必须先连上 warehouse.duckdb
duckdb data/warehouse.duckdb -c "
SELECT 'raw' AS src, count(*) FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet')
UNION ALL
SELECT 'warehouse', count(*) FROM yellow_trips
"
# 结果应该一致——仓库视图不增不减，只是加了便捷列
```
