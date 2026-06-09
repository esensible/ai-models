#!/usr/bin/env bash
# cad/setup.sh — (re)build the build123d headless CAD venv from requirements.txt.
#
# Requires `uv`. If the venv's pinned Python interpreter disappears (e.g. after a
# host/OS upgrade) the venv is dead; this detects that and rebuilds. Idempotent.
set -euo pipefail

CAD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$CAD/.venv"
REQ="$CAD/requirements.txt"
log() { printf '\033[0;35m[cad]\033[0m %s\n' "$*"; }

# Is the existing venv usable (python present and runnable)?
venv_ok() { [[ -x "$VENV/bin/python" ]] && "$VENV/bin/python" -c 'import sys' 2>/dev/null; }

if venv_ok; then
  log "venv healthy ($("$VENV/bin/python" --version 2>&1)) — syncing deps"
else
  if [[ -e "$VENV" ]]; then
    log "venv broken (interpreter missing/incompatible) — recreating"
    rm -rf "$VENV"
  fi
  log "creating venv with $(uv python find 2>/dev/null || echo system python)"
  uv venv "$VENV"
fi

log "installing requirements (this pulls large OCP wheels on first run) ..."
VIRTUAL_ENV="$VENV" uv pip install -r "$REQ"

# pyrender pins pyopengl==3.1.0, which lacks OSMesaCreateContextAttribs needed for
# headless osmesa rendering. Force a newer PyOpenGL over it (second pass on purpose).
PYOPENGL_OVERRIDE="PyOpenGL>=3.1.7"
log "overriding $PYOPENGL_OVERRIDE (pyrender's 3.1.0 pin lacks OSMesa attribs) ..."
VIRTUAL_ENV="$VENV" uv pip install --upgrade "$PYOPENGL_OVERRIDE"

log "verifying imports ..."
"$VENV/bin/python" - <<'PY'
import importlib
for m in ("build123d", "OCP", "trimesh", "ezdxf"):
    importlib.import_module(m)
    print(f"  ok  {m}")
try:
    import pyrender, OpenGL  # noqa
    print("  ok  pyrender + PyOpenGL")
except Exception as e:
    print(f"  warn pyrender import: {e}")
PY
log "done ✔"
