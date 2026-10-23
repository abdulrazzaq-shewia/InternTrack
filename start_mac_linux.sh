#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/python -m pip install -r requirements.txt
printf '\nOpen http://127.0.0.1:5000 in your browser. Press Ctrl+C to stop.\n'
.venv/bin/python run.py
