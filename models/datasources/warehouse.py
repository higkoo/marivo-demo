import marivo.datasource as md

md.duckdb(
    name="warehouse",
    path="data/warehouse.duckdb",
    read_only=True,
)
