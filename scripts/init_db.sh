#!/bin/bash
set -e

# Run the database initialization via uv
# This connects to localhost:5432 by default (as per session.py defaults),
# which matches the docker-compose forwarded port.
echo "Running database initialization..."
uv run python scripts/init_db.py
echo "Done."
