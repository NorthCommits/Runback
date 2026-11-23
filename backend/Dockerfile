ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=60 \
    PIP_RETRIES=5

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y ca-certificates && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --timeout 60 "setuptools>=75"
RUN groupadd --gid 10001 runback && useradd --uid 10001 --gid 10001 --create-home runback

FROM base AS test

COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY tests ./tests

RUN pip install --no-build-isolation ".[dev]"
RUN pytest

FROM base AS runtime

COPY pyproject.toml ./
COPY --chown=runback:runback app ./app
COPY --chown=runback:runback alembic.ini ./
COPY --chown=runback:runback migrations ./migrations

RUN pip install --no-build-isolation .

USER runback

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
