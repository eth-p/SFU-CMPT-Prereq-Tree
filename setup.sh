#!/usr/bin/env bash
PIP=pip3
if ! command -v "$PIP" 2>&1; then PIP="pip"; fi

set -x
"$PIP" install -r requirements.txt

