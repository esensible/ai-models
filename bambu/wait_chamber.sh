#!/usr/bin/env bash
# Poll the (unpowered) nozzle temp as a chamber proxy; exit 0 when it reaches
# the target, exit 2 on timeout. Logs each reading to cad/out/preheat.log.
set -uo pipefail
WS=/home/node/.openclaw/workspace
cd "$WS"
set -a && . bambu/printer.env && set +a
export PATH="$WS/.bin:$PATH" XDG_CACHE_HOME="$WS/.cache" XDG_DATA_HOME="$WS/.local/share" UV_PYTHON_INSTALL_DIR="$WS/.local/share/uv/python"

TARGET=${1:-30}
MAX_MIN=${2:-45}
LOG=cad/out/preheat.log
deadline=$(( $(date +%s) + MAX_MIN*60 ))

while :; do
  json=$(uv run bambu/nozzle_temp.py 2>/dev/null | tail -1)
  noz=$(printf '%s' "$json" | sed -n 's/.*"nozzle": \([0-9.]*\).*/\1/p')
  ts=$(date -u +%H:%M:%S)
  echo "$ts nozzle=$noz $json" >> "$LOG"
  if [ -n "$noz" ]; then
    reached=$(awk -v n="$noz" -v t="$TARGET" 'BEGIN{print (n>=t)?1:0}')
    if [ "$reached" = "1" ]; then
      echo "REACHED nozzle=$noz at $ts"
      exit 0
    fi
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "TIMEOUT after ${MAX_MIN}min, last nozzle=$noz"
    exit 2
  fi
  sleep 45
done
