#!/usr/bin/env bash
# Wrapper: load printer creds from printer.env (if present), then read LAN status.
#   ./printer/run.sh            # one-shot status
#   ./printer/run.sh --watch    # stream until Ctrl-C
# Requires `uv` (https://github.com/astral-sh/uv).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BAMBU_ENV_FILE="${BAMBU_ENV_FILE:-$WS/printer/printer.env}"
[ -f "$BAMBU_ENV_FILE" ] && set -a && . "$BAMBU_ENV_FILE" && set +a
exec uv run "$WS/printer/bambu_status.py" "$@"
