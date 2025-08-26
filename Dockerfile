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

# ---------- Python runtime stage ----------
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# uv binary
COPY --from=ghcr.io/astral-sh/uv:0.7.3 /uv /uvx /bin/

# Dependency resolution (no source yet, for cache efficiency)
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy backend source
COPY src ./src

# Copy built frontend assets
COPY --from=frontend-build /frontend/dist ./src/static/dist

# Install the project itself (places code into venv)
RUN --mount=type=cache,target=/root/.cache/uv uv sync

# Ensure dist exists (fail fast if frontend missed)
RUN test -d ./src/static/dist || (echo "Missing static dist" && exit 1)

# Put venv first
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

EXPOSE 8080

# Prefer uvicorn directly (fastapi run wraps uvicorn, but explicit is clearer)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]