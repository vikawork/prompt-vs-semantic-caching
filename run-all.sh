#!/usr/bin/env bash
set -euo pipefail
DEMO_DIR=$(cd "$(dirname "$0")" && pwd)
exec nice -n 10 python "$DEMO_DIR/run_all.py"
