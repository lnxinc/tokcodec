#!/usr/bin/env bash
# Cold-machine verification in Docker, against the LOCAL source tree (pre-publish)
# or against the registries (post-publish, pass --published).
#   scripts/cold-test.sh              # node:22-slim (no Python!) + python:3.12-slim, from local source
#   scripts/cold-test.sh --published  # same, but installs from npm/PyPI like a real user
set -euo pipefail
cd "$(dirname "$0")/.."
mode="${1:-local}"
if [[ "$mode" == "--published" ]]; then
  echo "== node:22-slim, npx from npm registry (no Python in this image)"
  docker run --rm node:22-slim bash -lc "npx -y tokcodec why /etc/hosts && npx -y tokcodec install --dry-run"
  echo "== python:3.12-slim, uvx from PyPI"
  docker run --rm python:3.12-slim bash -lc "pip install -q uv && uvx tokcodec why /etc/hosts"
else
  echo "== node:22-slim, launcher + uv bootstrap, tokcodec from local source (no Python in this image)"
  docker run --rm -v "$PWD:/src:ro" -e TOKCODEC_PYTHON_SPEC=/src node:22-slim bash -lc \
    "cp -r /src/npm /tmp/npm && cd /tmp && node npm/bin/tokcodec.js why /src/samples/decoder.py && node npm/bin/tokcodec.js install --dry-run"
  echo "== python:3.12-slim, uvx from local source"
  docker run --rm -v "$PWD:/src:ro" python:3.12-slim bash -lc \
    "pip install -q uv && uvx --from /src tokcodec why /src/samples/decoder.py"
fi
echo "cold-test: ok"
