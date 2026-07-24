.PHONY: setup data-download data-build data-verify semantic-snapshot semantic-check analysis-smoke test lint typecheck verify clean-warehouse

VENV_PYTHON := .venv/bin/python
TESTS ?= tests

setup:
	bash scripts/setup.sh

data-download:
	$(VENV_PYTHON) -m yellow_taxi_demo.data download

data-build:
	$(VENV_PYTHON) -m yellow_taxi_demo.data build

data-verify:
	$(VENV_PYTHON) -m yellow_taxi_demo.data verify

semantic-snapshot:
	$(VENV_PYTHON) -m yellow_taxi_demo.semantic_snapshot

semantic-check: semantic-snapshot
	$(VENV_PYTHON) -m yellow_taxi_demo.semantic_check
	.venv/bin/marivo doctor --semantic

analysis-smoke:
	$(VENV_PYTHON) -m yellow_taxi_demo.analysis_smoke

test:
	$(VENV_PYTHON) -m pytest $(TESTS)

lint:
	$(VENV_PYTHON) -m ruff check yellow_taxi_demo tests

typecheck:
	$(VENV_PYTHON) -m mypy

verify: data-verify semantic-check analysis-smoke test lint typecheck

clean-warehouse:
	rm -f data/warehouse.duckdb data/warehouse.duckdb.tmp
