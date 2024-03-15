# syntax=docker/dockerfile:1

FROM python:3.12-bookworm as build

ARG POETRY_VERSION="1.7.0"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONDONTWRITEBYTECODE=1

RUN pip3 install poetry==${POETRY_VERSION}

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install dependencies with BuildKit caching
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --without=dev --without=ci --no-root --no-interaction --no-ansi

FROM python:3.12-slim-bookworm

LABEL org.opencontainers.image.source https://github.com/Sparta142/Celebi

USER nobody

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/app/.venv

# "Activate" the virtual environment
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

WORKDIR /app

COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY celebi ./celebi

ENTRYPOINT ["python3", "-m", "celebi"]
