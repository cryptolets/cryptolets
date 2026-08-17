#!/usr/bin/env bash
# Create the virtual environment the flow runs in.
set -e

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

echo "Setup done."