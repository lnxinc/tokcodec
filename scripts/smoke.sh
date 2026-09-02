#!/usr/bin/env bash
# Smoke test for a clean machine: the CLI runs, prints a before->after pair, exits 0.
set -euo pipefail
cd "$(dirname "$0")/.."
out=$(tokcodec why samples/decoder.py)
echo "$out" | grep -q "tokcodec L3" || { echo "smoke: missing L3 row"; exit 1; }
tokcodec samples/pytest_run.log -l 3 -s 2>&1 >/dev/null | grep -Eq '[0-9]+→[0-9]+ tok' || { echo "smoke: no before→after stats"; exit 1; }
tokcodec langs >/dev/null
tokcodec install --dry-run >/dev/null
echo "smoke: ok"
