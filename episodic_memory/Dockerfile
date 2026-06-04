FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir uv

WORKDIR /app

COPY episodic_memory/pyproject.toml pyproject.toml

RUN uv venv .venv && \
    UV_COMPILE_BYTECODE=1 uv pip install --python .venv -r pyproject.toml

FROM python:3.12-alpine

RUN apk add --no-cache libffi openssl

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv .venv

COPY episodic_memory/src/episodic_memory episodic_memory/

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "episodic_memory.main:app", "--host", "0.0.0.0", "--port", "8080"]
