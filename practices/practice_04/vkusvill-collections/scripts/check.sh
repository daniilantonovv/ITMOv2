#!/bin/sh
# Single trusted runner: used by people, the agent and the hook.
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python
[ -x "$PY" ] || { echo "No .venv. Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"; exit 1; }
"$PY" -m compileall -q app tests
"$PY" -m pytest -q
