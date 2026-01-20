# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set the working directory to /app
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

COPY pyproject.toml .

RUN uv pip install --system -r pyproject.toml

COPY bonsai_sensei/ bonsai_sensei/
COPY scripts/init_db.py .

EXPOSE 8000

CMD ["uvicorn", "bonsai_sensei.main:app", "--host", "0.0.0.0", "--port", "8000"]
