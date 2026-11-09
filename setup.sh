#!/bin/bash
# Creates the virtual environment and installs dependencies. Run once: ./setup.sh
set -e
cd "$(dirname "$0")"
rm -rf .venv
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q
echo "Done. Activate with: source .venv/bin/activate"
