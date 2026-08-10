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
├── .venv/bin/python                          ← 自带 duckdb 库
└── ...
```

如果你已经跑过 `make setup`，那这些文件**应该已经存在了**。
如果没有，先跑一遍：

```bash
make setup
```

它会自动下载全部 12 个 Parquet 文件 + 区域表到 `data/raw/`，
并构建 `data/warehouse.duckdb`。这个过程需要几分钟（总共约 750 MB）。

---

### 路线 A：纯 Shell 一行命令（推荐先做）

**前提**：已经 `make setup`。项目自带的 `.venv/bin/python` 里装了 DuckDB，
不需要额外装任何东西。

#### 查看 Parquet schema

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"SELECT name, type FROM parquet_schema('data/raw/yellow_tripdata_2025-01.parquet') WHERE name <> 'schema'\").show()
"
```

#### 看行数

```bash
.venv/bin/python -c "
import duckdb; print(duckdb.sql(\"SELECT count(*) FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')\").fetchone()[0])
"
```

#### 看前 5 行关键字段

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT tpep_pickup_datetime AS pickup,
         trip_distance, fare_amount, tip_amount, total_amount,
         payment_type, PULocationID, DOLocationID
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
  LIMIT 5
\"\"\").show()
"
```

#### 基础汇总（行程数、车费、小费率）

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT count(*) AS trips,
         round(sum(fare_amount), 2) AS total_fare,
         round(sum(tip_amount), 2) AS total_tips,
         round(sum(tip_amount)/nullif(sum(fare_amount), 0), 4) AS tip_rate
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
  WHERE trip_distance > 0 AND total_amount >= 0
\"\"\").show()
"
```

#### 按小时看打车热度

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT extract(hour FROM tpep_pickup_datetime) AS hour,
         count(*) AS trips
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 1
\"\"\").show()
"
```

#### 按支付方式看差异

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT payment_type,
         count(*) AS trips,
         round(avg(fare_amount), 2) AS avg_fare,
         round(avg(tip_amount), 2) AS avg_tip
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 2 DESC
\"\"\").show()
"
```

#### 关联区域表，看哪个行政区最多

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT z.Borough AS pickup_borough,
         count(*) AS trips,
         round(sum(t.total_amount), 0) AS revenue
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet') t
  LEFT JOIN read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true) z
    ON t.PULocationID = z.LocationID
  GROUP BY 1 ORDER BY 2 DESC LIMIT 5
\"\"\").show()
"
```

#### 数据质量巡检

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT
    count(*) FILTER (WHERE fare_amount < 0) AS neg_fare,
    count(*) FILTER (WHERE trip_distance = 0) AS zero_mi,
    count(*) FILTER (WHERE passenger_count IS NULL) AS null_pax,
    count(*) FILTER (WHERE tpep_dropoff_datetime <= tpep_pickup_datetime) AS bad_duration
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
\"\"\").show()
"
```

#### 读全部 12 个月（跨月分析）

```bash
.venv/bin/python -c "
import duckdb; duckdb.sql(\"\"\"
  SELECT strftime(tpep_pickup_datetime, '%Y-%m') AS month,
         count(*) AS trips,
         round(sum(fare_amount), 0) AS fare
  FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet')
  GROUP BY 1 ORDER BY 1
\"\"\").show()
"
```

> 你注意到什么了吗？上面这个查询会出来 16 行，
> 其中有 2007-12、2008-12、2009-01 的零星记录，
> 还有 2024-12 的 21 条——这些就是"脏数据"。
> 原始数据**不帮你过滤**，全给你看。

#### 建成一个本地 DuckDB 仓库（后续查询超快）

```bash
.venv/bin/python -c "
import duckdb
con = duckdb.connect('data/manual_warehouse.duckdb')
con.execute(\"CREATE TABLE trips AS SELECT * FROM read_parquet('data/raw/yellow_tripdata_2025-*.parquet', union_by_name=true)\")
con.execute(\"CREATE TABLE zones AS SELECT * FROM read_csv_auto('data/raw/taxi_zone_lookup.csv', header=true)\")
print('rows =', con.execute('SELECT count(*) FROM trips').fetchone()[0])
con.close()
"
# 之后直接：
.venv/bin/python -c "
import duckdb
con = duckdb.connect('data/manual_warehouse.duckdb')
duckdb.sql('SELECT count(*) FROM trips').show()
"
```

项目自己的仓库是 `data/warehouse.duckdb`（`make setup` 构建的），
你自己建的这个叫 `data/manual_warehouse.duckdb`，
两者互不冲突。

---

### 路线 B：装个 duckdb CLI，更简洁

如果你嫌上面的 `python -c` 太长，可以装 DuckDB 命令行工具，
然后就可以直接写 SQL：

```bash
# 安装到项目的 .venv 里
.venv/bin/pip install duckdb-cli

# 验证
.venv/bin/duckdb --version

# 然后直接一行：
.venv/bin/duckdb -c "SELECT count(*) FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')"

.venv/bin/duckdb -c "
  SELECT extract(hour FROM tpep_pickup_datetime) AS h, count(*) AS trips
  FROM read_parquet('data/raw/yellow_tripdata_2025-01.parquet')
  GROUP BY 1 ORDER BY 1
"
```

CLI 模式适合临时探索、写长 SQL、或者配 `.sql` 文件。

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
