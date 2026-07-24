# Repository Guide

This is a Marivo-first analytical project over the 2025 NYC TLC Yellow Taxi dataset.

- Run `make setup` before analysis. It installs Marivo, downloads the fixed
  2025 dataset, builds DuckDB, and verifies the semantic layer.
- Never use bare `python`, `pip`, `pytest`, `mypy`, or `ruff`. Use the Make
  targets or `.venv/bin/...`.
- Start analysis from the governed objects under `models/`; do not replace
  semantic metrics with ad-hoc SQL.
- Use `import marivo.semantic as ms` for exact refs and
  `import marivo.analysis as mv` for analysis.
- Prefer the progressive artifact read path:
  `repr -> show() -> contract() -> to_pandas()`.
- Treat TLC timestamps as local `America/New_York` wall-clock timestamps.
- Treat policy and weather explanations as observational. Marivo does not make
  causal claims from before/after comparisons or correlations.
- Raw SQL is a diagnostic escape hatch only. If used, reconcile the result to
  the semantic metric before reporting it.
- Do not modify, delete, or silently filter raw source files during analysis.
- Put local analysis scripts under `analysis/` and keep generated session state
  under `.marivo/` out of Git.
