#!/usr/bin/env bash
PYTHON=python3
if ! command -v "$PYTHON" 2>&1; then PYTHON="python"; fi

set -ex
if ! [ -f courses.json ]; then
	"$PYTHON" get-courses.py
fi

"$PYTHON" main.py

