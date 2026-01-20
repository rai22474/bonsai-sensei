#!/bin/bash
set -e

echo "Running data population script..."
uv run python scripts/populate_db.py
echo "Done."
