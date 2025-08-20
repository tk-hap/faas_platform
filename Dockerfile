FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install UV
COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/

# Place executable at the front of the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
ENV UV_COMPILE_BYTECODE=1

# UV Cache
ENV UV_LINK_MODE=copy

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

ENV PYTHONPATH=/app

COPY ./pyproject.toml ./uv.lock /app/

COPY ./src /app/src

COPY .env /app/.env

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync


CMD ["fastapi", "run", "src/main.py", "--port", "8080"]