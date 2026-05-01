#!/usr/bin/env bash
echo "Creating python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt
deactivate
echo "Finished Setup!"