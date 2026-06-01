FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    gcc musl-dev libffi-dev git && \
    pip install --no-cache-dir uv

WORKDIR /app

COPY knowledge_base/pyproject.toml pyproject.toml

RUN uv venv .venv && \
    UV_COMPILE_BYTECODE=1 uv pip install --python .venv -r pyproject.toml

FROM python:3.12-alpine

RUN apk add --no-cache git && \
    git config --global safe.directory '*'

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder /app/.venv .venv

COPY knowledge_base/src/knowledge_base knowledge_base/

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "knowledge_base.main:app", "--host", "0.0.0.0", "--port", "8080"]
