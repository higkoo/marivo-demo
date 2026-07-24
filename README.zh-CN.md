# Marivo NYC Yellow Taxi Demo

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个开箱即用的 Marivo 分析项目，数据源为 NYC TLC 官方发布的一整年
Yellow Taxi 行程记录。克隆仓库并完成初始化后，即可在 coding agent 中直接
使用 Marivo 语义层和分析接口。

## 初始化

环境要求：macOS、Linux 或 WSL，已安装 `make`，并能够访问网络。安装程序会
优先使用 Python 3.12 或更高版本；如果本机环境不满足要求，Marivo 安装器会
通过 `uv` 准备运行环境。

```bash
git clone <repository-url>
cd marivo-yellow-taxi-demo
make setup
```

`make setup` 可以重复执行，并会完成全部初始化步骤：

1. 安装 Marivo 并初始化 agent skills；
2. 下载 2025 年 1 月至 12 月的 12 个官方月度 Parquet 文件，支持失败重试和
   断点续传；
3. 下载官方 TLC Taxi Zone 对照表；
4. 构建 `data/warehouse.duckdb`；
5. 获取有界的数据源 evidence，并预览每一个语义对象；
6. 确认语义 catalog 完全 ready，且 doctor 没有 warning；
7. 运行真实的 Marivo observation，覆盖 OD、数据质量、乘客、费用、时间模式、
   速度和打赏分析路径。

默认下载的数据约为 0.7–1 GB。再次执行 setup 时会复用已经完整下载的文件，
仅在需要时重新构建。

## 让 Agent 开始分析

完成 setup 后，在 coding agent 中打开本仓库并提出问题，例如：

> 比较 2025 年 12 月与 1 月的计价器车费收入。收入变化了多少？哪些上车行政区、
> 上车区域、支付方式和费率类别对差异贡献最大？在得出结论前检查数据完整性和
> 异常记录，区分计价器车费与乘客支付总额，并且不要作因果推断。

更多中文示例问题位于 [`questions/zh-CN/`](questions/zh-CN/)，英文版本位于
[`questions/en/`](questions/en/)。

## 常用命令

```bash
make verify
make semantic-snapshot
make semantic-check
make analysis-smoke
make data-verify
```

仅在项目开发和 CI 场景中，可以选择有界的月份子集，而不改变仓库约定的一年
数据范围：

```bash
TAXI_DEMO_MONTHS=2025-11,2025-12 make setup
```

普通使用者应执行不带月份覆盖参数的完整 setup。

## 数据模型

DuckDB 通过下载的 Parquet 文件建立视图，每一行对应一条 2025 年官方发布的
Yellow Taxi 行程记录。项目还提供两个具有明确角色的区域实体。trip 粒度上的
上车和下车角色字段支持无关系歧义的组合 OD 分析：

```text
yellow_trips
  ├── pickup_location_id  -> pickup_zones
  ├── dropoff_location_id -> dropoff_zones
  └── pickup_* + dropoff_* 角色字段，用于 OD 分析
```

受治理的核心指标覆盖：

- 需求量；
- 官方发布的完整费用组成；
- 总体记录打赏和信用卡专用打赏；
- 距离、时长、合理速度和每英里票价；
- 已知乘客数记录的平均乘客数及其覆盖率；
- 拥堵收费；
- 透明的数据质量计数和比率。

上车小时、ISO 星期、周末、Taxi Zone、borough 和 service zone 等维度，可用于
运营模式和时间模式分析。

为了便于审计，官方发布总量会保留修正类和异常记录。常用平均值和效率指标使用
有明确文档约束的 plausible-record 子集：

- pickup 时间与源文件月份一致；
- 行程时长大于 0 且不超过 24 小时；
- 行程距离在 0 至 200 英里之间；
- 推算速度不超过 100 mph；
- fare 和 total amount 非负；
- 上车和下车区域均能解析到官方 Taxi Zone。

## 数据来源与注意事项

- 行程记录和数据字典：
  <https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>
- 官方发布文件：
  <https://d37ci6vzurychx.cloudfront.net/trip-data/>
- Taxi Zone：
  <https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv>

TLC 说明这些记录由授权技术服务商提供，不保证数据的准确性或完整性。本项目
有意保留不合理记录和修正类记录，以便 Marivo 的数据质量分析能够发现这些问题。
支付类型代码 `5` 和 `6` 的标签遵循 TLC 数据字典。
