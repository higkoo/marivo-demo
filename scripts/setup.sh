#!/usr/bin/env bash
set -Eeuo pipefail

readonly INSTALLER_URL="${MARIVO_INSTALLER_URL:-https://raw.githubusercontent.com/chengxianglibra/marivo/main/scripts/install-marivo.sh}"
readonly MAKE_BIN="${MAKE:-make}"

stage() {
  printf '\n==> %s\n' "$1"
}

stage "Download upstream Marivo installer"
mkdir -p .cache
curl -fsSL "$INSTALLER_URL" -o .cache/install-marivo.sh

stage "Install and initialize Marivo"
bash .cache/install-marivo.sh --yes

stage "Install Yellow Taxi demo"
.venv/bin/python -m pip install -e ".[dev]"

stage "Download official NYC TLC data"
.venv/bin/python -m yellow_taxi_demo.data download

stage "Build DuckDB warehouse"
.venv/bin/python -m yellow_taxi_demo.data build

stage "Verify project"
"$MAKE_BIN" verify

printf '\nYellow Taxi demo setup completed.\n'
printf 'Open this repository in your agent and start from README.md or questions/.\n'
