#!/usr/bin/env bash
# Wrapper for print_job.py (FTPS upload + MQTT print start). Loads creds from printer.env.
#   ./printer/send.sh --status                 # show filament/state
#   ./printer/send.sh path/to.3mf              # upload only (no print)
#   ./printer/send.sh path/to.3mf --print      # upload AND start print
# Requires `uv` (https://github.com/astral-sh/uv).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BAMBU_ENV_FILE="${BAMBU_ENV_FILE:-$WS/printer/printer.env}"
[ -f "$BAMBU_ENV_FILE" ] && set -a && . "$BAMBU_ENV_FILE" && set +a
exec uv run "$WS/printer/print_job.py" "$@"
