#!/usr/bin/env bash
# Smoke-check the toolchain (all baked into the image; nothing installed on the host).
set -euo pipefail
echo "[post-create] toolchain:"
echo "  node    $(node --version)"
echo "  npm     $(npm --version)"
echo "  python  $(python3 --version)"
echo "  uv      $(uv --version)"
echo "  pulumi  $(pulumi version)"
echo "  aws     $(aws --version)"
echo "[post-create] ok — use the Makefile: make build | preview | deploy"
