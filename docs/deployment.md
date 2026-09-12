# Enterprise AI Platform: Containerization & Deployment Operations Guide

## 1. ARCHITECTURE OVERVIEW

The Enterprise AI Platform is fully containerized using Docker and Docker Compose, orchestrating 9 dedicated services on an isolated bridge network with healthcheck dependencies and persistent data volumes:

| Service | Image / Build | Port | Purpose | Health Check |
|---|---|---|---|---|
| `postgres` | `postgres:16-alpine` | `5432` | Relational Metadata & DB Store | `pg_isready -U postgres -d enterprise_ai` |
| `redis` | `redis:7-alpine` | `6379` | Celery Broker & Result Cache | `redis-cli ping` |
| `mlflow` | `ghcr.io/mlflow/mlflow:v2.15.0` | `5000` | Experiment Tracking & Artifact Store | HTTP response |
| `backend` | `./backend/Dockerfile` | `8000` | FastAPI Core REST API Server | `curl -f http://localhost:8000/health` |
| `celery_worker` | `./backend/Dockerfile` | - | Distributed Background Task Worker | Celery heartbeat |
| `frontend` | `./frontend/Dockerfile` | `3000` | React + TypeScript + Vite SPA | `wget -q --spider http://localhost:80/healthz` |
| `prometheus` | `prom/prometheus:v2.54.1` | `9090` | Time-series Metrics Scraper & Store | Self-monitoring |
| `grafana` | `grafana/grafana:11.1.0` | `3001` | MLOps Observability & Dashboards | HTTP response |
| `nginx` | `nginx:1.25-alpine` | `80` | Master Ingress Gateway & Reverse Proxy | `curl http://localhost:80/healthz` |

---

## 2. QUICK START (DEVELOPMENT & LOCAL TESTING)

### Prerequisites
- Docker Engine 24.0+
- Docker Compose v2.20+

### Starting the Entire Cluster
```bash
# Clone the repository
cd enterprise-ai-platform

# Spin up all 9 services in detached mode with build
docker compose up --build -d

# Check cluster service status
docker compose ps

# Follow logs across all services
docker compose logs -f

# Follow backend logs specifically
docker compose logs -f backend
```

### Access Points
- **Web Application HUD**: [http://localhost](http://localhost) (or [http://localhost:3000](http://localhost:3000))
- **FastAPI REST API**: [http://localhost/api/v1](http://localhost/api/v1) (or [http://localhost:8000/api/v1](http://localhost:8000/api/v1))
- **Swagger Interactive API Docs**: [http://localhost/docs](http://localhost/docs)
- **MLflow Tracking UI**: [http://localhost/mlflow/](http://localhost/mlflow/) (or [http://localhost:5000](http://localhost:5000))
- **Grafana MLOps Telemetry**: [http://localhost/grafana/](http://localhost/grafana/) (or [http://localhost:3001](http://localhost:3001))
  - *Default Credentials*: `admin` / `admin`
- **Prometheus Raw Metrics**: [http://localhost:9090](http://localhost:9090)
- **Scrapable Platform Metrics**: [http://localhost/metrics](http://localhost/metrics)

---

## 3. PRODUCTION DEPLOYMENT HARDENING

For staging and production deployments, combine the base configuration with `docker-compose.prod.yml`:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### Key Production Enhancements Applied:
1. **CPU & Memory Hard Quotas**:
   - Backend: 2.0 CPUs / 4GB RAM limit
   - Celery Worker: 4.0 CPUs / 8GB RAM limit
   - PostgreSQL: 2.0 CPUs / 2GB RAM limit
   - Redis: 1.0 CPU / 1GB RAM limit
2. **Security Sandboxing**:
   - `security_opt: ["no-new-privileges:true"]` applied to all containers.
   - Non-root user `appuser` (UID 10001) enforced in Python execution.
3. **Log Rotation Drivers**:
   - `json-file` log driver with `max-size: 10m-20m` and `max-file: 3-5` prevents disk saturation.
4. **Horizontal Scaling**:
   - Scaled backend and Celery workers to multiple replicas (`replicas: 2`).

---

## 4. DATABASE MIGRATIONS & SEEDING

Alembic database migrations execute automatically upon container launch in `backend/entrypoint.sh`.

To manually trigger migrations or seed data:
```bash
# Run migrations inside backend container
docker compose exec backend alembic upgrade head

# Open interactive async Python shell
docker compose exec backend python -c "from app.database.database import async_engine; print(async_engine)"
```

---

## 5. PERSISTENT STORAGE VOLUMES

| Volume Name | Target Path | Data Retained |
|---|---|---|
| `postgres_data` | `/var/lib/postgresql/data` | Relational tables, users, jobs, metrics |
| `redis_data` | `/data` | Redis in-memory append-only snapshots |
| `mlflow_data` | `/mlflow` | MLflow model artifacts, experiments, run logs |
| `backend_data` | `/app/data` | Uploaded tabular datasets, serialized models (`.joblib`) |
| `prometheus_data` | `/prometheus` | Time-series metrics TSDB |
| `grafana_data` | `/var/lib/grafana` | Custom Grafana user preferences & dashboard states |

---

## 6. STOPPING & CLEANING UP

```bash
# Stop all containers (preserving persistent volumes)
docker compose down

# Stop all containers and delete all data volumes (FACTORY RESET)
docker compose down -v
```
