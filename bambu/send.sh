#!/usr/bin/env bash
# Wrapper for print_job.py (FTPS upload + MQTT print start). Loads creds from printer.env.
#   ./bambu/send.sh --status                 # show filament/state
#   ./bambu/send.sh path/to.3mf              # upload only (no print)
#   ./bambu/send.sh path/to.3mf --print      # upload AND start print
# Requires `uv` (https://github.com/astral-sh/uv).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$WS/bambu/printer.env" ] && set -a && . "$WS/bambu/printer.env" && set +a
exec uv run "$WS/bambu/print_job.py" "$@"
