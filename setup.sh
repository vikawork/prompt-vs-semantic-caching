#!/usr/bin/env bash
set -euo pipefail
# Downloads only pinned public Hugging Face assets using Python's plain HTTPS client.
DEMO_DIR=$(cd "$(dirname "$0")" && pwd)
nice -n 10 python "$DEMO_DIR/setup.py"
