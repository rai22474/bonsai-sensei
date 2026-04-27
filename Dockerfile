# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory to /app
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml .

RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

RUN uv pip install --system -r pyproject.toml

COPY bonsai_sensei/ bonsai_sensei/
COPY alembic/ alembic/
COPY alembic.ini .
COPY scripts/init_db.py .

EXPOSE 8080

CMD ["sh", "-c", "uvicorn bonsai_sensei.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
