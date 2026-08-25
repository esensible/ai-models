#!/usr/bin/env bash
# One-command print driver: validate against live printer state -> slice -> print.
#   ./print.sh model.stl              # validate + slice + summary (does NOT print)
#   ./print.sh model.stl --print      # ...and start the print
#   ./print.sh model.stl --material PLA --plate "Cool Plate"
# See printer/loaded.json (user-declared filament/plate/nozzle) and
# slice/filaments/ (per-filament profiles + overrides).
# Requires `uv` (https://github.com/astral-sh/uv).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BAMBU_ENV_FILE="${BAMBU_ENV_FILE:-$WS/printer/printer.env}"
[ -f "$BAMBU_ENV_FILE" ] && set -a && . "$BAMBU_ENV_FILE" && set +a
exec uv run "$WS/printer/printflow.py" "$@"
