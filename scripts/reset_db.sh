#!/bin/bash
set -e

echo "Resetting database (irreversible)..."
uv run python scripts/reset_db.py
echo "Done."
