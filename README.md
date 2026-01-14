# Bonsai Sensei

A FastAPI application managed by `uv` and Dockerized.

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Docker (optional, for containerization)

## Installation

1.  Clone the repository.
2.  Install dependencies:

    ```bash
    uv sync
    ```

## Running Locally

Run the server with:

```bash
uv run uvicorn bonsai_sensei.main:app --reload
```

Open http://127.0.0.1:8000/docs to see the Swagger UI.

## Docker

Build the image:

```bash
docker build -t bonsai-sensei .
```

Run the container:

```bash
docker run -p 8000:8000 bonsai-sensei
```

Open http://127.0.0.1:8000/docs.
