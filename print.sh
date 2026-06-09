#!/usr/bin/env bash
# One-command print driver: validate against live printer state -> slice -> print.
#   ./print.sh model.stl              # validate + slice + summary (does NOT print)
#   ./print.sh model.stl --print      # ...and start the print
#   ./print.sh model.stl --material PLA --plate "Cool Plate"
# See bambu/loaded.json (recorded plate/filament) and slice/materials.json (profiles).
# Requires `uv` (https://github.com/astral-sh/uv).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[ -f "$WS/bambu/printer.env" ] && set -a && . "$WS/bambu/printer.env" && set +a
exec uv run "$WS/bambu/printflow.py" "$@"
