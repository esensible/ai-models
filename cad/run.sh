#!/usr/bin/env bash
# Run a build123d model script in the headless CAD env.
#   ./cad/run.sh cad/models/<model>.py [args...]
#
# Uses the venv built by cad/setup.sh and the SYSTEM GL/OSMesa libraries
# (install libosmesa6 / libgl1 / libglu1-mesa via your package manager).
set -euo pipefail
CAD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYOPENGL_PLATFORM=osmesa        # off-screen software GL (no display needed)
export HOME="$CAD/.home"               # writable HOME for ezdxf/fontconfig caches
export XDG_CACHE_HOME="$CAD/.home/.cache"
mkdir -p "$HOME" "$XDG_CACHE_HOME"
exec "$CAD/.venv/bin/python" "$@"
