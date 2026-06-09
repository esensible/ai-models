#!/usr/bin/env bash
# Wrapper: load printer creds from printer.env (if present), then read LAN status.
#   ./bambu/run.sh            # one-shot status
#   ./bambu/run.sh --watch    # stream until Ctrl-C
# Requires `uv` (https://github.com/astral-sh/uv).
set -euo pipefail
WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "$WS/bambu/printer.env" ] && set -a && . "$WS/bambu/printer.env" && set +a
exec uv run "$WS/bambu/bambu_status.py" "$@"
