# ---------- Frontend build stage ----------
FROM node:20-alpine AS frontend-build
WORKDIR /frontend

# Install only what we need first for better layer caching
COPY src/static/package.json src/static/package-lock.json* ./ 
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy the remaining frontend source (vite config, ts, public, etc.)
COPY src/static/ ./

# Build (Vite outputs to ./dist by default)
RUN npm run build

# ---------- Python base stage ----------
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

COPY ./src /src

# Copy built frontend assets from stage into the backend tree
# Resulting runtime path: /app/src/static/dist
COPY --from=frontend-build /frontend/dist /src/static/dist

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync

EXPOSE 8080

CMD ["fastapi", "run", "src/main.py", "--port", "8080"]