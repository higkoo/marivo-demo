# Marivo NYC Yellow Taxi Demo

[English](README.md) | [简体中文（小白入门推荐）](README.zh-CN.md)

> New here? The [beginner-friendly Chinese guide](README.zh-CN.md) walks through
> what this project is, why to use it, and how to run it step by step.

A clone-and-analyze Marivo project backed by one complete year of official NYC
TLC Yellow Taxi trip records.

## Setup

Requirements: macOS, Linux, or WSL; `make`; and network access. Python 3.12+ is
used when available, otherwise Marivo's installer provisions it with `uv`.

```bash
git clone <repository-url>
cd marivo-yellow-taxi-demo
make setup
```

`make setup` is idempotent and performs the complete bootstrap:

1. installs Marivo and initializes its agent skills;
2. downloads the 12 official monthly Parquet files from January through
   December 2025, with retry and resume support;
3. downloads the official TLC Taxi Zone lookup;
4. builds `data/warehouse.duckdb`;
5. acquires bounded datasource evidence and previews every semantic object;
6. requires a fully ready semantic catalog with no doctor warnings;
7. runs real Marivo observations across OD, quality, passenger, fee, temporal,
   speed, and tip-analysis paths.

The default source download is approximately 0.7-1 GB. Re-running setup reuses
complete files and rebuilds only when requested.

## Ask an agent

After setup, open this repository in a coding agent and ask:

> Compare December 2025 with January 2025. How much did metered fare revenue
> change, and which pickup boroughs, pickup zones, payment methods, and rate
> categories accounted for most of the difference? Check data completeness and
> unusual records before drawing conclusions, distinguish metered fares from
> total passenger charges, and do not make causal claims.

More prompts live under [`questions/en/`](questions/en/). A Chinese version is
available under [`questions/zh-CN/`](questions/zh-CN/).

## Useful commands

```bash
make verify
make semantic-snapshot
make semantic-check
make analysis-smoke
make data-verify
```

For development only, a bounded subset can be selected without changing the
committed one-year contract:

```bash
TAXI_DEMO_MONTHS=2025-11,2025-12 make setup
```

This override is intended for repository development and CI. A normal user
should run the default full setup.

## Data model

The warehouse exposes one row per published 2025 Yellow Taxi trip record through
a DuckDB view over the downloaded Parquet files, plus two role-specific zone
dimensions. Trip-owned pickup and drop-off role fields support combined OD
analysis without relationship ambiguity:

```text
yellow_trips
  ├── pickup_location_id  -> pickup_zones
  ├── dropoff_location_id -> dropoff_zones
  └── pickup_* + dropoff_* role fields for OD analysis
```

Core governed metrics include demand; the complete published fare-component
family; recorded and credit-card-specific tips; distance, duration, plausible
speed, and fare per mile; known-record passenger averages and coverage;
congestion-pricing fees; and transparent record-quality counts and rates.
Pickup hour, ISO weekday, weekend, zone, borough, and service-zone dimensions
support operational and temporal pattern analysis.

Published totals retain correction-like records for auditability. Common
averages and efficiency metrics use a documented plausible-record subset:
source-month alignment, positive duration up to 24 hours, distance from 0 to
200 miles, implied speed no more than 100 mph, nonnegative fare and total, and
resolvable pickup and drop-off zones.

## Source and caveats

- Trip records and data dictionaries:
  <https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>
- Published files:
  <https://d37ci6vzurychx.cloudfront.net/trip-data/>
- Taxi zones:
  <https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv>

The TLC states that the records are supplied by authorized technology providers
and does not guarantee their accuracy or completeness. This project deliberately
retains implausible and correction-like rows so Marivo quality analysis can
surface them. Payment type `5` and `6` labels follow the TLC data dictionary.
