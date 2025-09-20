# FaaS Platform

Ephemeral Function-as-a-Service platform that lets users submit short function source code snippets, builds a container image on-the-fly with Kaniko, deploys it as a Knative Service, and exposes a temporary HTTPS endpoint. Functions auto‑expire after a configured TTL and their resources are reclaimed.

---

## Key Features

- **Ephemeral Functions**: Each function runs as an independent Knative Service and is garbage‑collected after `FUNCTION_CLEANUP_SECS`.
- **On‑Demand Image Builds**: Build context assembled fully in‑memory and uploaded to S3 / R2. Kaniko pod builds and pushes the image without requiring privileged Docker.
- **Multi‑Language Ready**: Pluggable templates by language (see `src/container/templates/contexts/<language>` and `HandlerFiles` enum).
- **Autoscaling & Scale-to-Zero**: Relies on Knative for request‑driven scaling.
- **Helm Deployable**: Complete chart in `helm/faas-platform` including optional Cilium egress policy, secrets, RBAC, and migration job.
- **Database Persistence**: PostgreSQL (async SQLAlchemy + Alembic) tracks container images and functions (TTL metadata).
- **In‑Cluster & Local Modes**: Kubernetes client auto-detects in-cluster configuration.
- **Static SPA Frontend**: Built with Vite/TypeScript and served by FastAPI from `src/static/dist`.
- **Hardened Baselines**: Non‑root runtime, minimal privileges, optional Cilium egress restrictions.

---

## High-Level Architecture

```
User --> FastAPI API (create function) -->
	1. Persist metadata (DB)
	2. Assemble build context (BytesIO tar.gz) -> S3
	3. Launch Kaniko builder Pod (namespace: kaniko) -> build & push image
	4. Create Knative Service (namespace: functions)
	5. Poll health -> return endpoint URL

Cleanup Scheduler --> scans DB -> delete expired Knative Services + registry images
```

Components:
- **API**: `src/main.py`, routers under `src/function/views.py`.
- **Container Build**: `src/container/service.py` (build context + Kaniko manifest).
- **Function Lifecycle**: `src/function/service.py` (Knative service creation, route fetch, TTL metadata).
- **K8s Helpers**: `src/k8s/service.py` (wait for Kaniko success, route resolution).
- **Scheduler**: `src/scheduler.py` (periodic cleanup – implementation detail if present/not yet shown here).
- **Migrations**: Alembic in `alembic/` and migration Job template in Helm chart.

---

## Tech Stack

| Area | Technology |
|------|------------|
| API | FastAPI + Uvicorn |
| DB Layer | SQLAlchemy (async) |
| Migrations | Alembic |
| Task Scheduling | APScheduler |
| K8s & Knative | Kubernetes Python client + Knative CRDs |
| Image Build | Kaniko (no Docker daemon) |
| Object Storage | S3 compatible (e.g. Cloudflare R2) via `boto3` |
| Frontend | Vite + TypeScript SPA (served statically) |
| Packaging | `uv` (fast dependency resolver) |
| Deployment | Helm chart |

---

## Local Development

### Prerequisites
- Python 3.12+
- `uv` (included by copying binary in Docker, install locally if desired) or fallback to `pip`
- Node 20.x (for frontend builds)
- Docker (for building the runtime image) – not required for Kaniko inside cluster
- A running PostgreSQL (compose file provided)

### Clone & Setup
```bash
git clone <repo-url>
cd faas_platform

# Start Postgres locally
docker compose up -d postgres

# Create and activate venv with uv
uv venv
source .venv/bin/activate

# Install deps
uv sync

# Run Alembic migrations
alembic upgrade head

# Run backend (expects env vars – see below)
uv run fastapi dev src/main.py

# Frontend (development, if you want to modify it before build)
cd src/static && npm install && npm run dev
```

### Environment Variables
Managed via Pydantic `Settings` (`src/config.py`). See .env.example

### Running Tests
```bash
pytest -q
```

Add new tests under `tests/` mirroring module structure.

---

## Build & Run with Docker
The `Dockerfile` performs a multi-stage build (frontend then backend, using `uv`).
```bash
docker build -t faas-platform:dev .
docker run --rm -p 8080:8080 --env-file .env faas-platform:dev
```

Ensure `.env` contains all required variables.

---

## Helm Deployment

Chart: `helm/faas-platform`

Values highlights (`values.yaml`):
- `namespace.*` – logical separation: `app` (API), `functions` (Knative services), `kaniko` (builder pods)
- `secrets` – create or reference existing secret for sensitive env vars
- `ciliumEgress` – optional egress restriction (policy now applied in functions namespace)
- `replicaCount` – API deployment scaling (Knative services scale independently)

### Install / Upgrade
```bash
helm upgrade --install faas-platform ./deploy/helm/faas-platform \
	-n faas-app --create-namespace \
	-f your-values.yaml
```

If using separate namespaces for functions / kaniko, create them ahead or add namespace templates (future enhancement):
```bash
kubectl create namespace functions
kubectl create namespace kaniko
```

### Migrations
If the migration Job is enabled (`migrations.enabled=true`), it will run on install/upgrade.

---

## Security Considerations
- Non-root containers (`runAsUser=1000`) with `fsGroup` for writable ephemeral dirs.
- Build process isolated to Kaniko builder Pod (no Docker socket exposure).
- Optional network egress restriction via Cilium policy.
- Secrets managed by Kubernetes Secret or external store (recommended for production).

---

## Roadmap / Potential Enhancements
- Helm hook for migrations & namespace templating for `functions` / `kaniko`.
- Readiness / liveness probes for API Deployment.
- Garbage collection worker improvements (batch deletes, metrics export).
- Language plugins & sandboxing (Firecracker / gVisor) for untrusted code.
- Web UI for function submission & status (currently SPA placeholder).
- Observability: OpenTelemetry traces, Prometheus metrics, structured logs shipping.
- Rate limiting & auth .

---