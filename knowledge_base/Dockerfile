FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

WORKDIR /app

COPY knowledge_base/pyproject.toml pyproject.toml

RUN uv venv .venv && \
    UV_COMPILE_BYTECODE=1 uv pip install --python .venv -r pyproject.toml

ENV FASTEMBED_CACHE_PATH=/app/model_cache

RUN .venv/bin/python -c "\
from fastembed import TextEmbedding; \
TextEmbedding('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git wget \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global safe.directory '*'

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV FASTEMBED_CACHE_PATH=/app/model_cache

COPY --from=builder /app/.venv .venv
COPY --from=builder /app/model_cache /app/model_cache

COPY knowledge_base/src/knowledge_base knowledge_base/

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "knowledge_base.main:app", "--host", "0.0.0.0", "--port", "8080"]
