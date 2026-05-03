FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    gcc musl-dev libffi-dev \
    jpeg-dev zlib-dev freetype-dev libpng-dev && \
    pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml .

RUN uv venv .venv && \
    UV_COMPILE_BYTECODE=1 uv pip install --python .venv -r pyproject.toml

FROM python:3.12-alpine

RUN apk add --no-cache libjpeg libpng freetype ttf-dejavu

WORKDIR /app

COPY --from=builder /app/.venv .venv

COPY bonsai_sensei/ bonsai_sensei/
COPY alembic/ alembic/
COPY alembic.ini .
COPY scripts/init_db.py .

EXPOSE 8080

CMD ["/app/.venv/bin/python", "-m", "uvicorn", "bonsai_sensei.main:app", "--host", "0.0.0.0", "--port", "8080"]
