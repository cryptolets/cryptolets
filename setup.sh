#!/usr/bin/env bash
echo "Creating python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
echo "Installing sympy..."
pip install sympy
deactivate
echo "Finished Setup!"